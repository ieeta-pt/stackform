"""SQLAlchemy column types for field types whose stored form differs from their JSON form."""

from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa

from .fields import iso_utc


class IsoDateTime(sa.TypeDecorator):
    """A timestamp column read and written as the canonical ISO 8601 UTC string."""

    impl = sa.DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: sa.Dialect) -> datetime | None:
        return None if value is None else datetime.fromisoformat(value)

    def process_result_value(self, value: datetime | None, dialect: sa.Dialect) -> str | None:
        return None if value is None else iso_utc(value)


def json_number(value: Any) -> Any:
    """A NUMERIC value as the JSON number it denotes: integral ones as int, others as float."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


class JsonNumber(sa.TypeDecorator):
    """A ``number`` column read back as the JSON number it holds: 5 as 5, 5.5 as 5.5."""

    impl = sa.Numeric(asdecimal=True)
    cache_ok = True

    def process_result_value(self, value: Decimal | None, dialect: sa.Dialect) -> int | float | None:
        return json_number(value)
