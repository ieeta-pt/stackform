"""A repository lifecycle expressed as MongoDB filters, pipelines, writes and indexes.

A lifecycle is the mapping ``{"removal": field | None, "expiry": {"field", "seconds"} | None}``.
Writes store the expiry field as a BSON date, the only type a TTL index erases rows by.
"""

from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from pymongo import ReturnDocument

EXPIRY_INDEX = "lifecycle_expiry"
# The TTL index lags the application purge, which also discards the files of the rows it erases.
EXPIRY_INDEX_LAG_SECONDS = 120

_NON_NULL_BSON_TYPES = [
    "double", "string", "object", "array", "binData", "objectId", "bool", "date", "regex",
    "javascript", "int", "timestamp", "long", "decimal", "minKey", "maxKey",
]
_DELETES = frozenset({"deleteOne", "findOneAndDelete", "deleteMany"})
_READS = frozenset({"find", "findOne", "countDocuments", "distinct"})
_WRITES = frozenset({
    "updateOne", "findOneAndUpdate", "updateMany", "replaceOne", "findOneAndReplace", *_DELETES,
})
_WRITE_OPERATORS = ("$set", "$setOnInsert")


def _instant(value: Any) -> Any:
    """`value` as an aware datetime when it denotes an instant, otherwise unchanged."""
    if isinstance(value, str):
        with suppress(ValueError):
            return _instant(datetime.fromisoformat(value))
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _clock(field: str) -> dict[str, Any]:
    """The instant `field` holds, server side: BSON dates and ISO 8601 strings alike, null otherwise."""
    return {"$convert": {"input": f"${field}", "to": "date", "onError": None, "onNull": None}}


def _expired(expiry: Mapping[str, Any]) -> dict[str, Any]:
    instant = _clock(expiry["field"])
    cutoff = {"$subtract": ["$$NOW", expiry["seconds"] * 1000]}
    return {"$and": [{"$ne": [instant, None]}, {"$lt": [instant, cutoff]}]}


class MongoLifecycle:
    def __init__(
        self,
        lifecycle: Mapping[str, Any] | None = None,
        include_deleted: bool = False,
        joined: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        """`include_deleted` keeps removed and expired rows in view of reads; writes still keep to the lifecycle.

        `joined` maps every other collection a pipeline may read to its lifecycle.
        """
        self._removal = (lifecycle or {}).get("removal")
        self._expiry = (lifecycle or {}).get("expiry")
        removal = [{self._removal: None}] if self._removal else []
        expiry = [{"$expr": {"$not": [_expired(self._expiry)]}}] if self._expiry else []
        self._conditions = (*removal, *expiry)
        self._include_deleted = include_deleted
        self._joined = joined or {}

    def visible(self, criteria: Mapping[str, Any] | None = None) -> dict[str, Any]:
        clauses = [dict(clause) for clause in (criteria, *self._conditions) if clause]
        return {"$and": clauses} if len(clauses) > 1 else next(iter(clauses), {})

    def readable(self, criteria: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """`criteria` as a read applies it: confined to visible rows unless removed ones are included."""
        return dict(criteria or {}) if self._include_deleted else self.visible(criteria)

    def pipeline(self, stages: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        """`stages` reading visible rows only, of this collection and of every collection they join."""
        head = [{"$match": match}] if (match := self.readable()) else []
        return [*head, *self._joining(stages)]

    def _joining(self, stages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """`stages` with every stage reading other rows confined to the rows its source keeps in view."""
        joins: dict[str, Callable[[Any], Any]] = {
            "$lookup": self._lookup, "$unionWith": self._union, "$graphLookup": self._graph_lookup, "$facet": self._facet,
        }
        return [
            {operator: joins[operator](spec) if operator in joins else spec for operator, spec in stage.items()}
            for stage in stages
        ]

    def _of(self, collection: str | None) -> "MongoLifecycle":
        return MongoLifecycle(self._joined.get(collection or ""), self._include_deleted, self._joined)

    def _lookup(self, spec: Mapping[str, Any]) -> dict[str, Any]:
        return {**spec, "pipeline": self._of(spec.get("from")).pipeline(spec.get("pipeline") or [])}

    def _union(self, spec: Mapping[str, Any] | str) -> dict[str, Any]:
        union = spec if isinstance(spec, Mapping) else {"coll": spec}
        return {**union, "pipeline": self._of(union["coll"]).pipeline(union.get("pipeline") or [])}

    def _graph_lookup(self, spec: Mapping[str, Any]) -> dict[str, Any]:
        return {**spec, "restrictSearchWithMatch": self._of(spec["from"]).readable(spec.get("restrictSearchWithMatch"))}

    def _facet(self, spec: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
        return {name: self._joining(stages) for name, stages in spec.items()}

    def stored(self, document: Mapping[str, Any]) -> dict[str, Any]:
        """`document` as written: its expiry timestamp as a BSON date."""
        return {**document, **self._dated(document)}

    def stored_update(self, update: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> Any:
        """`update` as applied: setting the expiry timestamp as a BSON date."""
        if self._expiry is None:
            return update
        if not isinstance(update, Mapping):
            field = self._expiry["field"]
            return [*update, {"$set": {field: _clock(field)}}]
        return {**update, **{
            operator: {**changes, **self._dated(changes)}
            for operator, changes in update.items()
            if operator in _WRITE_OPERATORS
        }}

    def _dated(self, values: Mapping[str, Any]) -> dict[str, Any]:
        field = (self._expiry or {}).get("field")
        return {field: _instant(values[field])} if field in values else {}

    def removal(self) -> dict[str, Any] | None:
        """The update a delete applies in place of erasing rows, when soft deletion is on."""
        return {"$set": {self._removal: datetime.now(UTC).isoformat()}} if self._removal else None

    async def remove(self, collection: Any, criteria: Mapping[str, Any]) -> dict[str, Any] | None:
        removal = self.removal()
        if removal is None:
            return await collection.find_one_and_delete(self.visible(criteria))
        return await collection.find_one_and_update(self.visible(criteria), removal, return_document=ReturnDocument.AFTER)

    def unique(self, field: str) -> dict[str, Any]:
        """The rows a unique index on `field` holds: those with a value that no delete removed."""
        return {field: {"$type": _NON_NULL_BSON_TYPES}, **({self._removal: None} if self._removal else {})}

    async def keep_unique(self, collection: Any, field: str) -> None:
        """Keeps `field` unique among the rows `unique` selects, replacing an index that selects others."""
        name, rows = f"{field}_1", self.unique(field)
        index = (await collection.index_information()).get(name)
        if index is not None and index.get("partialFilterExpression") != rows:
            await collection.drop_index(name)
        await collection.create_index(field, name=name, unique=True, partialFilterExpression=rows)

    async def purge(self, collection: Any) -> list[dict[str, Any]]:
        """Erases the expired rows and returns them, keeping the TTL index that backs this purge."""
        if self._expiry is None:
            return []
        await self._expire(collection)
        rows = await collection.find({"$expr": _expired(self._expiry)}).to_list(length=None)
        await collection.delete_many({"_id": {"$in": [row["_id"] for row in rows]}})
        return rows

    async def _expire(self, collection: Any) -> None:
        """Keeps the TTL index that erases rows the purge missed in step with the configured expiry."""
        if self._expiry is None:
            return
        field, seconds = self._expiry["field"], self._expiry["seconds"] + EXPIRY_INDEX_LAG_SECONDS
        index = (await collection.index_information()).get(EXPIRY_INDEX)
        if index is not None and index["key"] != [(field, 1)]:
            await collection.drop_index(EXPIRY_INDEX)
            index = None
        if index is None:
            await collection.create_index(field, name=EXPIRY_INDEX, expireAfterSeconds=seconds)
        elif index.get("expireAfterSeconds") != seconds:
            await collection.database.command(
                "collMod", collection.name, index={"name": EXPIRY_INDEX, "expireAfterSeconds": seconds}
            )

    def scoped(self, query: Mapping[str, Any]) -> dict[str, Any]:
        """A declared operation's `query` confined to visible rows, writing as `stored` does.

        An estimated count, which no filter narrows, becomes an exact count of the rows in view.
        """
        counted = query["command"] == "estimatedDocumentCount" and bool(self.readable())
        return self._confined({**query, **({"command": "countDocuments", "filter": {}} if counted else {})})

    def _confined(self, spec: Mapping[str, Any], command: str | None = None) -> dict[str, Any]:
        command = command or spec["command"]
        return {
            **spec,
            **({"filter": self.readable(spec.get("filter"))} if command in _READS else {}),
            **({"filter": self.visible(spec.get("filter"))} if command in _WRITES else {}),
            **({"pipeline": self.pipeline(spec.get("pipeline") or [])} if command == "aggregate" else {}),
            **({"document": self.stored(spec["document"])} if "document" in spec else {}),
            **({"documents": [*map(self.stored, spec["documents"])]} if "documents" in spec else {}),
            **({"replacement": self.stored(spec["replacement"])} if "replacement" in spec else {}),
            **({"update": self.stored_update(spec["update"])} if "update" in spec else {}),
            **({"removal": self.removal()} if command in _DELETES and self._removal else {}),
            **({"requests": [
                {kind: self._confined(request_spec, kind) for kind, request_spec in request.items()}
                for request in spec["requests"]
            ]} if "requests" in spec else {}),
        }


def scoped(query: Mapping[str, Any], lifecycle: Mapping[str, Any]) -> dict[str, Any]:
    """`query` scoped to the lifecycle it carries, a target collection's, or else to `lifecycle`."""
    scope = MongoLifecycle(
        query.get("lifecycle", lifecycle), query.get("includeDeleted", False), query.get("lifecycles")
    )
    return scope.scoped(query)
