from __future__ import annotations

import time
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def run_with_retry(
    *,
    operation: Callable[[], T],
    should_retry: Callable[[Exception], bool],
    max_retries: int = 1,
    base_delay_seconds: float = 0.2,
    sleep_fn: Callable[[float], None] = time.sleep,
    on_retry: Callable[[int, float, Exception], None] | None = None,
) -> T:
    attempt = 0
    while True:
        try:
            return operation()
        except Exception as error:  # noqa: BLE001
            if attempt >= max_retries or not should_retry(error):
                raise

            delay = base_delay_seconds * (2**attempt)
            if on_retry is not None:
                on_retry(attempt + 1, delay, error)
            sleep_fn(delay)
            attempt += 1
