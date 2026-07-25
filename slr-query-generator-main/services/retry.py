from __future__ import annotations

from time import sleep
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(operation: Callable[[], T], attempts: int = 3, delay_seconds: float = 0.25) -> T:
    """Bounded retry for transient provider failures."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:  # Provider exceptions are normalized at the tool boundary.
            last_error = exc
            if attempt + 1 < attempts:
                sleep(delay_seconds * (2 ** attempt))
    assert last_error is not None
    raise last_error
