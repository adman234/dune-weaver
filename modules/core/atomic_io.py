"""Crash-safe file writes for the app's JSON data files.

Writing in place (`open(path, "w")`) truncates the file first, so a power cut
or crash mid-write leaves it empty or half-written. These helpers write to a
temp file in the same directory, fsync it, then atomically rename it over the
original, so readers see either the old file or the new one, never a partial one.
"""
import json
import logging
import os
import shutil
import tempfile
import time

logger = logging.getLogger(__name__)


def atomic_write_text(path, text: str, encoding: str = "utf-8") -> None:
    path = os.fspath(path)
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=f".{os.path.basename(path)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        try:
            shutil.copymode(path, tmp)
        except OSError:
            os.chmod(tmp, 0o644)  # New file: mkstemp's default is 0600
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    # Persist the rename itself (POSIX only).
    if hasattr(os, "O_DIRECTORY"):
        try:
            dfd = os.open(directory, os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            pass


def atomic_write_json(path, data, **dump_kwargs) -> None:
    atomic_write_text(path, json.dumps(data, **dump_kwargs))


def preserve_corrupt_file(path) -> str | None:
    """Copy an unreadable data file aside before it gets overwritten with
    defaults, so the user can recover it. Returns the copy's path."""
    path = os.fspath(path)
    if not os.path.exists(path):
        return None
    dest = f"{path}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}"
    try:
        shutil.copy2(path, dest)
        logger.error(f"Unreadable {os.path.basename(path)} saved as {dest}")
        return dest
    except OSError as e:
        logger.error(f"Could not back up unreadable {path}: {e}")
        return None
