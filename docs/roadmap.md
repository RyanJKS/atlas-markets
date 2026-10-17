# Build roadmap

The workspace, three HTTP scaffolds, and shared telemetry exist today. Four additional
service directories contain documentation placeholders only. Build complete simulated
workflows before turning those placeholders into deployments or adding cluster operations.

## 1. Establish market data

Implement deterministic synthetic prices, instrument identifiers, timestamp handling,
and feed validation in market data. Add its first business contract and persistence
only when needed. Keep fixtures reproducible so downstream tests can replay them.

## 2. Simulate a trade

Implement order management and deterministic risk limits in orders. Add reproducible
fills in execution simulator and positions and valuation in portfolio. Record orders
and fills with idempotency keys. Keep authoritative accounting in the ledger. Verify
the complete order-to-position workflow with integration tests.

## 3. Add payments, fraud rules, and accounting

Payments creates and manages the transaction; fraud assesses it; the ledger accounts
for it. Define transaction states and assessment contracts, start fraud with deterministic
rules, and implement balanced, idempotent ledger postings for completed transactions.
Test rejected payments, retries, duplicate posting attempts, and reconciliation.
Machine learning is not required for this workflow.

## 4. Add durable events

Introduce PostgreSQL ownership boundaries and a broker when asynchronous consumers
need them. Publish versioned events through an outbox. Test duplicate delivery, replay,
failure recovery, and reconciliation. Define dead-letter handling and audit retention.

## 5. Optionally add an ML baseline

Once rules-based fraud assessment works, consider a future `atlas-ml` component.
Generate labeled synthetic transactions and define time-safe features using a separate
training project and environment. No ML project is implemented yet. Train and evaluate
a simple baseline, version artifacts and preprocessing, and add model readiness and
scoring contracts. Run shadow scoring and review flagged cases before automated blocking.

## 6. Add user workflows and operations

Build a trader workstation under `apps/`, integrate an identity provider, and enforce
authorization. Add review tooling, audit history, structured logs, metrics, and traces.
Create per-service deployment and rollback procedures before adding Kubernetes or
GitOps. Add release automation and affected-service checks when justified by use.
