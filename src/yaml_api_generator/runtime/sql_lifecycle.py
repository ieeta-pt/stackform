"""A repository lifecycle expressed as SQLAlchemy Core clauses and statements, and imposed on declared SQL."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
import sqlglot
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlglot import exp

from .lifecycle import Expiry, Lifecycle

_SQLGLOT_DIALECTS = {"postgresql": "postgres"}
_WRITES = (exp.Insert, exp.Update, exp.Delete)


def _instant(value: datetime) -> sa.BindParameter[datetime]:
    """A timestamp bound as such, whatever type decorates the column it meets."""
    return sa.literal(value, sa.DateTime(timezone=True))


def unique_index(table: str, field: str, removal: str) -> sa.Index:
    """Keeps `field` unique among the rows no delete removed, so a removed row's value can be taken again."""
    kept = sa.column(removal).is_(None)
    return sa.Index(f"uq_{table}_{field}", field, unique=True, postgresql_where=kept, sqlite_where=kept)


class SQLLifecycle:
    def __init__(self, table: sa.Table, lifecycle: Lifecycle = Lifecycle()) -> None:
        self._table = table
        self._lifecycle = lifecycle

    def visible(self) -> tuple[sa.ColumnElement[bool], ...]:
        removal, expiry = self._lifecycle.removal, self._lifecycle.expiry
        removed = (self._table.c[removal].is_(None),) if removal else ()
        if expiry is None:
            return removed
        stamp = self._table.c[expiry.field]
        return (*removed, sa.or_(stamp.is_(None), stamp >= _instant(expiry.cutoff())))

    def remove(self, *criteria: sa.ColumnElement[bool]) -> sa.Executable:
        """Stamps the removal timestamp when soft deletion is on, otherwise erases the row."""
        removal = self._lifecycle.removal
        statement = (
            sa.update(self._table).values({removal: _instant(datetime.now(UTC))})
            if removal
            else sa.delete(self._table)
        )
        return statement.where(*criteria, *self.visible()).returning(self._table)

    def upsert(self, key_field: str, values: Mapping[str, Any], id_field: str) -> sa.Executable:
        """Inserts `values`, or updates the visible row holding their `key_field`; a hidden row is left as it is."""
        removal, visible = self._lifecycle.removal, self.visible()
        statement = pg_insert(self._table).values(**values)
        return statement.on_conflict_do_update(
            index_elements=[key_field],
            index_where=self._table.c[removal].is_(None) if removal else None,
            set_={name: statement.excluded[name] for name in values if name != id_field},
            where=sa.and_(*visible) if visible else None,
        ).returning(self._table)

    async def purge(self, engine: AsyncEngine) -> list[dict[str, Any]]:
        """Erases the expired rows and returns them."""
        expiry = self._lifecycle.expiry
        if expiry is None:
            return []
        expired = self._table.c[expiry.field] < _instant(expiry.cutoff())
        async with engine.begin() as connection:
            result = await connection.execute(sa.delete(self._table).where(expired).returning(self._table))
            return [dict(row._mapping) for row in result]


def _lifecycle(mapping: Mapping[str, Any]) -> Lifecycle:
    expiry = mapping.get("expiry")
    return Lifecycle(mapping.get("removal"), Expiry(**expiry) if expiry else None)


def _written(table: exp.Table) -> exp.Expression | None:
    """The INSERT, UPDATE or DELETE whose target `table` is, if it is one."""
    node = table.parent if isinstance(table.parent, exp.Schema) else table
    statement = node.parent
    return statement if isinstance(statement, _WRITES) and node.arg_key == "this" else None


def _qualified(field: str, qualifier: exp.Identifier) -> exp.Column:
    return exp.Column(this=exp.to_identifier(field, quoted=True), table=qualifier.copy())


def _named(node: exp.Expression) -> exp.Expression:
    """`node` with its placeholder in the `:name` form SQLAlchemy text binds, whatever the dialect renders."""
    return exp.var(f":{node.name}") if isinstance(node, exp.Placeholder) else node


class _ScopedStatement:
    """A declared SQL statement kept to the lifecycle of every table it names.

    It reads visible rows only, unless removed ones are included, and updates or deletes visible rows only;
    deleting from a soft-deleting table stamps the removal timestamp instead of erasing rows.
    """

    def __init__(self, query: Mapping[str, Any], dialect: str) -> None:
        self._sql = query["sql"]
        self._lifecycles = {
            table: _lifecycle(lifecycle)
            for table, lifecycle in (query.get("lifecycles") or {}).items()
            if table.lower() in self._sql.lower()
        }
        self._include_deleted = query.get("includeDeleted", False)
        self._dialect = _SQLGLOT_DIALECTS.get(dialect, dialect)
        self._instants: dict[str, datetime] = {}

    def text(self) -> sa.TextClause:
        if not self._lifecycles:
            return sa.text(self._sql)
        tree = self._soft_deleting(sqlglot.parse_one(self._sql, read=self._dialect))
        for table in [*tree.find_all(exp.Table)]:
            if table.name in self._lifecycles:
                self._confine(table)
        return sa.text(tree.transform(_named).sql(dialect=self._dialect)).bindparams(*(
            sa.bindparam(name, value, type_=sa.DateTime(timezone=True)) for name, value in self._instants.items()
        ))

    def _instant(self, name: str, value: datetime) -> exp.Placeholder:
        self._instants[name] = value
        return exp.Placeholder(this=name)

    def _soft_deleting(self, tree: exp.Expression) -> exp.Expression:
        """`tree`, or the update stamping the removal timestamp when it deletes from a soft-deleting table."""
        if not isinstance(tree, exp.Delete):
            return tree
        removal = self._lifecycles.get(tree.this.name, Lifecycle()).removal
        if removal is None:
            return tree
        head, *rest = tree.args.get("using") or [None]
        if head is not None:
            head.set("joins", [exp.Join(this=table) for table in rest])
        stamp = exp.EQ(
            this=exp.Column(this=exp.to_identifier(removal, quoted=True)),
            expression=self._instant("lifecycle_now", datetime.now(UTC)),
        )
        return exp.Update(
            with_=tree.args.get("with_"),
            this=tree.this,
            expressions=[stamp],
            from_=exp.From(this=head) if head is not None else None,
            where=tree.args.get("where"),
            returning=tree.args.get("returning"),
        )

    def _confine(self, table: exp.Table) -> None:
        written = _written(table)
        qualifier = table.args["alias"].this if table.alias else table.this
        if written is None and not self._include_deleted:
            table.replace(self._visible_rows(table))
        elif isinstance(written, (exp.Update, exp.Delete)):
            written.where(self._visible(table.name, qualifier), copy=False)

    def _visible_rows(self, table: exp.Table) -> exp.Subquery:
        """The rows of `table` in view, standing where `table` stood under the same name."""
        bare = table.copy()
        bare.set("alias", None)
        bare.set("joins", None)
        rows = exp.select("*").from_(bare).where(self._visible(table.name, table.this)).subquery(
            table.args["alias"].this.copy() if table.alias else table.this.copy()
        )
        rows.set("joins", table.args.get("joins"))
        return rows

    def _visible(self, name: str, qualifier: exp.Identifier) -> exp.Condition:
        lifecycle = self._lifecycles[name]
        removal = [_qualified(lifecycle.removal, qualifier).is_(exp.null())] if lifecycle.removal else []
        if lifecycle.expiry is None:
            return exp.and_(*removal)
        stamp = _qualified(lifecycle.expiry.field, qualifier)
        cutoff = self._instant(f"lifecycle_cutoff_{name}", lifecycle.expiry.cutoff())
        return exp.and_(*removal, exp.or_(stamp.is_(exp.null()), exp.GTE(this=stamp.copy(), expression=cutoff)))


def scoped(query: Mapping[str, Any], dialect: str) -> sa.TextClause:
    """`query`'s statement kept to the lifecycle of every table it names, on the SQLAlchemy `dialect`."""
    return _ScopedStatement(query, dialect).text()
