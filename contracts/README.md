# Service contracts

Store reviewed HTTP specifications under `http/<service>/` and event schemas under
`events/<domain>/` when those interfaces exist. The service scaffolds currently expose
only their generated `/openapi.json` documents; no business contract is implemented.

Version event types and include an event ID, producer, occurrence time in UTC,
correlation ID, schema version, and payload. Consumers must tolerate additive fields
and deduplicate deliveries by event ID. Use decimal strings with explicit currency
for money; never use binary floating point for balances or orders.

Breaking changes need a new contract version and a documented migration. Generate
clients from contracts rather than importing another service's source code.
