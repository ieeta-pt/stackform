"""Which rows a repository keeps visible: soft deletion and time-to-live expiry."""

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

PURGE_INTERVAL_SECONDS = 60

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Expiry:
    """A row expires `seconds` after the timestamp held in `field`."""

    field: str
    seconds: int

    def cutoff(self) -> datetime:
        """Rows whose timestamp is older than this instant have expired."""
        return datetime.now(UTC) - timedelta(seconds=self.seconds)


@dataclass(frozen=True)
class Lifecycle:
    """`removal` names the timestamp a delete sets instead of erasing the row."""

    removal: str | None = None
    expiry: Expiry | None = None


Rows = Iterable[Mapping[str, Any]]


def releasing(
    purge: Callable[[], Awaitable[Rows]], release: Callable[[Rows], Awaitable[object]]
) -> Callable[[], Awaitable[None]]:
    """`purge`, handing the rows it erases to `release`."""

    async def purged() -> None:
        await release(await purge())

    return purged


class Purger:
    """Erases expired rows at startup and then every `interval` seconds."""

    def __init__(
        self,
        purges: Iterable[Callable[[], Awaitable[object]]],
        interval: float = PURGE_INTERVAL_SECONDS,
    ) -> None:
        self._purges = tuple(purges)
        self._interval = interval
        self._task: asyncio.Task | None = None

    async def run(self) -> None:
        while True:
            for purge in self._purges:
                try:
                    await purge()
                except Exception:
                    logger.exception("Purging expired rows failed")
            await asyncio.sleep(self._interval)

    def start(self) -> None:
        if self._purges:
            self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
