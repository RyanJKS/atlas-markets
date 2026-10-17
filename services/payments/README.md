# Payments placeholder

Planned responsibility: create and manage transactions, including their identifiers,
idempotency, state changes, and completion. Payments requests a fraud assessment and
publishes the appropriate completed transaction information for the ledger to account
for. Exact contracts and transaction states will be defined during implementation.

Fraud assesses transactions. The ledger accounts for transactions. Payments owns
the transaction lifecycle and does not implement either service's responsibilities.

Status: documentation only. There is no Python project, HTTP server, Dockerfile,
payment provider, or transaction processing. This directory is excluded from the UV
workspace until implementation starts. See [service boundaries](../README.md).
