"""Run a resolved SQL operation query on an open SQLAlchemy async connection."""

from typing import Any

from .sql_lifecycle import scoped
from .sql_types import json_number


async def run_sql(connection: Any, query: dict[str, Any]) -> Any:
    result = await connection.execute(scoped(query, connection.dialect.name), query.get("params") or {})
    if result.returns_rows:
        return [{key: json_number(value) for key, value in row._mapping.items()} for row in result]
    return {"rowcount": result.rowcount}
