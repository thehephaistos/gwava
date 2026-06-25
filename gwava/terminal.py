"""Small terminal user-interface helpers."""

from contextlib import contextmanager
import itertools
import sys
import threading
import time
from collections.abc import Iterator
from typing import TextIO


@contextmanager
def loading_indicator(
    message: str,
    *,
    stream: TextIO = sys.stderr,
    interval: float = 0.1,
) -> Iterator[None]:
    """Display a terminal spinner while a block of work is running.

    The animation is enabled only when the output stream is an interactive
    terminal. This prevents control characters from appearing in redirected
    output, notebooks, logs, and automated tests.
    """
    enabled = bool(getattr(stream, "isatty", lambda: False)())

    if not enabled:
        yield
        return

    stopped = threading.Event()

    def animate() -> None:
        for frame in itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
            if stopped.is_set():
                break
            stream.write(f"\r{frame} {message}")
            stream.flush()
            time.sleep(interval)

    thread = threading.Thread(target=animate, daemon=True)
    thread.start()

    try:
        yield
    except BaseException:
        stopped.set()
        thread.join()
        stream.write(f"\r✗ {message}\n")
        stream.flush()
        raise
    else:
        stopped.set()
        thread.join()
        stream.write(f"\r✓ {message}\n")
        stream.flush()
