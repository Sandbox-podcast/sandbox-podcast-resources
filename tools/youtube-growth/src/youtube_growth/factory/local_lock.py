"""Nonblocking local process locks released by the OS after a worker crash."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def local_lock(directory: Path):
    """Lock a stable inode; never unlink the lock file, even on normal exit.

    Windows locks a byte with msvcrt; POSIX locks the descriptor with flock.
    Kernel ownership disappears when a process closes the handle or terminates.
    This supports one host, matching the factory's local SQLite deployment.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "run.lock"
    stream = lock.open("a+b")
    acquired = False
    try:
        # msvcrt requires a byte to exist. Contents never define ownership.
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except (OSError, BlockingIOError) as error:
            raise RuntimeError(f"Traitement local déjà actif dans {directory}.") from error
        yield
    finally:
        if acquired:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()
