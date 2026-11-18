# Data model

Booking: UUID id, owner, version, customer_name, offset-aware start, duration_minutes, service, resource. Editable values are strictly validated. Availability uses half-open UTC intervals and business-zone working hours.

Proposal: UUID id, owner, pending/superseded/committed status, expiry, immutable typed request (action/session/booking ID/expected version/details), and committed result for idempotent replay. Proposal history is retained.

Audit: proposal ID, action, timestamp. Session document: app/user/session identity, event list, state and update revision; application/user scopes are merged on reads, temporary state is not persisted.

Schema version is 1. Corrupt or incompatible JSON is rejected, not overwritten. SQL reference adapter stores this same document transactionally in one row; normalization is future work.
