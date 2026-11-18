"""Cross-process transactions on one local JSON file.

Never use this adapter on NFS or across hosts. A failed callback never writes.
"""

import copy
import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, TypeVar

from filelock import FileLock

T = TypeVar("T")


def empty_state():
    return {"schema_version": 1, "bookings": {}, "proposals": {}, "audit": []}


class Store(Protocol):
    def read(self) -> dict[str, Any]: ...
    def transact(self, operation: Callable[[dict[str, Any]], T]) -> T: ...


class JsonStore:
    def __init__(self, path: Path, factory: Callable = empty_state):
        self.path = Path(path)
        self.factory = factory
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(self.path) + ".lock", timeout=10)

    def _read(self):
        if not self.path.exists():
            return self.factory()
        # Corruption is an error, never silently reset a real dataset.
        result = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(result, dict) or result.get("schema_version") != 1:
            raise ValueError("Unsupported or corrupt storage document")
        return result

    def read(self):
        with self.lock:
            return self._read()

    def transact(self, operation):
        with self.lock:
            state = self._read()
            result = operation(state)
            fd, name = tempfile.mkstemp(dir=self.path.parent, prefix=".booking-", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as output:
                    json.dump(state, output, indent=2, ensure_ascii=False, allow_nan=False)
                    output.write("\n")
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(name, self.path)
            finally:
                if os.path.exists(name):
                    os.unlink(name)
            return copy.deepcopy(result)
