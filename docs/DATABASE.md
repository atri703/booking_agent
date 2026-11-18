# Dormant database implementation

`SQLiteStore` implements `read()` and `transact(callback)` just like `JsonStore`. It creates one SQL table containing the versioned JSON domain document. `BEGIN IMMEDIATE` serializes mutation transactions, parameterized SQL writes the document, and a raised callback rolls back. Every parametrized domain test runs against both adapters, including concurrency and rollback.

The runtime factory in `booking_agent/server.py` and the ADK agent factory always use `JsonStore`. No database is opened by the web app, and no configuration flag enables the adapter. SQLite files appear only in temporary parity tests or when a developer explicitly instantiates the class:

```python
from pathlib import Path
from booking_agent.config import Settings
from booking_agent.service import BookingService
from booking_agent.storage.sqlite_store import SQLiteStore

reference_service = BookingService(SQLiteStore(Path('/tmp/booking-reference.sqlite')), Settings())
```

This reference is useful for testing transactions and a later migration, but whole-document SQLite is not a normalized scalable booking database. For production PostgreSQL: create separate bookings, proposals, idempotency and audit tables; enforce tenant ownership and overlap constraints in transactions; add schema migrations and database-backed session/task stores. Preserve the current proposal ID, version and confirmation semantics.

A future migration must stop writes, validate the source schema, back up the JSON, import into the new database, compare records and version counts, run the parity tests, then switch the application deliberately. Do not implement a hidden auto-migration on startup.
