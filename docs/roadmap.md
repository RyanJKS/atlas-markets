# Build roadmap

Only the workspace and two service scaffolds exist today. Build a complete simulated
workflow before expanding the number of services or introducing cluster operations.

## 1. Establish market data

Implement deterministic synthetic prices, instrument identifiers, timestamp handling,
and feed validation in market data. Add its first business contract and persistence
only when needed. Keep fixtures reproducible so downstream tests can replay them.

## 2. Simulate a trade

Add order management, deterministic risk limits, and a paper execution adapter. Record
orders and fills with idempotency keys. Add portfolio accounting for cash, positions,
and profit and loss. Verify a complete order-to-position workflow with integration
tests before adding new domain services.

## 3. Add durable events

Introduce PostgreSQL ownership boundaries and a broker when asynchronous consumers
need them. Publish versioned fills through an outbox. Test duplicate delivery, replay,
failure recovery, and reconciliation. Define dead-letter handling and audit retention.

## 4. Build the fraud baseline

Generate labeled synthetic trades and define time-safe features beside the fraud
service, using a separate training environment when needed.
Train and evaluate a simple baseline. Version artifacts and preprocessing. Add model
loading, readiness, and scoring contracts to fraud detection. Run shadow scoring and
send flagged cases to a review workflow before enabling any blocking decision.

## 5. Add user workflows and operations

Build a trader workstation under `apps/`, integrate an identity provider, and enforce
authorization. Add review tooling, audit history, structured logs, metrics, and traces.
Create per-service deployment and rollback procedures before adding Kubernetes or
GitOps. Add release automation and affected-service checks when justified by use.
