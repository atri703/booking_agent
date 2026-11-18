"""Tested database adapter, intentionally NOT imported by the runtime factory.

A single transactional JSON document preserves the exact JSON adapter contract.
This is a migration reference, not a normalized multi-tenant production schema.
"""

import copy
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from booking_agent.storage.json_store import empty_state


class SQLiteStore:
    def __init__(self, path: Path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, body TEXT)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO state VALUES (1, ?)", (json.dumps(empty_state()),)
            )

    def read(self):
        with closing(sqlite3.connect(self.path)) as connection, connection:
            return json.loads(connection.execute("SELECT body FROM state WHERE id=1").fetchone()[0])

    def transact(self, operation):
        with closing(sqlite3.connect(self.path, timeout=10)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            state = json.loads(
                connection.execute("SELECT body FROM state WHERE id=1").fetchone()[0]
            )
            result = operation(state)
            connection.execute(
                "UPDATE state SET body=? WHERE id=1", (json.dumps(state, allow_nan=False),)
            )
            return copy.deepcopy(result)
