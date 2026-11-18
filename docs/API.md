# API and protocol examples

The local service uses `http://127.0.0.1:8001`. Add `Authorization: Bearer <token>` when BOOKING_API_TOKEN is configured. All requests in this release use the single demo owner; there is no user-controlled owner field.

| Method/path | Purpose |
|---|---|
| GET `/health` | Health and JSON storage mode |
| GET `/api/policy` | Current time, timezone and resource |
| GET `/api/availability?day=YYYY-MM-DD&duration_minutes=30` | Available slots |
| GET `/api/bookings` | List active bookings |
| GET `/api/bookings/{id}` | Read booking including version |
| POST `/api/proposals` | Prepare create/update/delete |
| GET `/api/proposals?session_id=...` | Unexpired pending proposals |
| POST `/api/proposals/{id}/confirm` | Commit exact proposal after client approval |
| POST `/api/chat` | GPT-5.2 conversation; returns session ID and pending proposals |
| GET `/api/sessions/{id}` | Restore JSON conversation events |
| GET `/.well-known/agent-card.json` | A2A discovery |
| POST `/` | A2A 1.0 JSON-RPC |

## Create

Choose a future weekday and a free slot returned by availability. Example body (replace the date to stay within 90 days):

```json
{
  "action": "create",
  "session_id": "my-demo-session",
  "booking": {
    "customer_name": "Demo Customer",
    "start": "2030-01-08T10:00:00+05:30",
    "duration_minutes": 30,
    "service": "consultation",
    "resource": "advisor"
  }
}
```

POST this to `/api/proposals`, inspect the returned request payload and expiry, then POST `{"accepted": true}` to `/api/proposals/<returned-id>/confirm`. A proposal alone does not reserve a slot. Confirmation can therefore return a conflict if another booking won.

## Update/reschedule

Read the latest booking to get its ID/version. POST to `/api/proposals`:

```json
{
  "action": "update",
  "session_id": "my-demo-session",
  "booking_id": "ID_FROM_READ",
  "expected_version": 1,
  "booking": {
    "customer_name": "Demo Customer",
    "start": "2030-01-08T11:00:00+05:30",
    "duration_minutes": 30,
    "service": "consultation",
    "resource": "advisor"
  }
}
```

Confirm the returned proposal. All editable fields must be supplied. The existing booking remains unchanged if the new slot conflicts.

## Delete/cancel

POST `{"action":"delete","session_id":"my-demo-session","booking_id":"ID_FROM_READ","expected_version":2}` to `/api/proposals`, then confirm. This removes the active booking. Audit/proposal/session history is retained; this is not a data-erasure API.

## Chat

POST `{"message":"Show my appointments","session_id":"my-demo-session"}` to `/api/chat`. Omit session_id to create one. The response contains `message`, `session_id` and `proposals`. Reuse the session ID to restore context. Render proposal details as data, not executable HTML. Confirmation remains a separate client action.

## A2A 1.0

```http
POST / HTTP/1.1
Content-Type: application/json
A2A-Version: 1.0

{
  "jsonrpc": "2.0",
  "id": "request-1",
  "method": "SendMessage",
  "params": {
    "message": {
      "messageId": "message-1",
      "role": "ROLE_USER",
      "parts": [{"text": "What is your booking policy?"}]
    }
  }
}
```

Use the SDK or `scripts/a2a_client.py` and preserve the returned contextId for follow-ups. A2A task cancellation means cancellation of protocol execution, not cancellation of an appointment; appointment cancellation needs its own reviewed proposal. The server's SDK provides task/streaming methods; the smoke suite covers discovery and SendMessage plus the ADK remote client.

## Errors

Malformed bodies return 422. Unknown/inaccessible records return 404. Conflicts, stale versions, expired/superseded proposals return 409 with `error` and `message`. Chat without a key returns 503; model failures return 502 without exposing credentials; chat timeout returns 504. A2A uses its own JSON-RPC error envelope.
