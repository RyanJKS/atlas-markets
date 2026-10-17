# Service boundaries

The service directories describe planned ownership. Only market data, orders, and
fraud currently have runnable HTTP scaffolds. Each exposes process liveness; orders
also has startup readiness and a random telemetry demonstration, without order processing.
The other four directories contain documentation placeholders, not implementations.

```text
services/
├── market-data/
├── orders/
├── execution-simulator/
├── portfolio/
├── ledger/
├── payments/
└── fraud/
```

- **Market data:** owns synthetic price ingestion and normalized market observations.
- **Orders:** owns order requests, validation, lifecycle, and cancellation.
- **Execution simulator:** simulates fills without connecting to a real broker.
- **Portfolio:** derives positions, valuation, and profit and loss from fills and prices.
- **Ledger:** owns balanced accounting entries and the authoritative accounting record.
- **Payments:** creates and manages transactions and their lifecycle.
- **Fraud:** assesses transactions, initially using rules. It can later use model scores.

Payments creates and manages the transaction; fraud assesses it; the ledger accounts
for it. Fraud does not own payment state or ledger entries. Portfolio does not own
the authoritative cash ledger. A future `atlas-ml` component is optional: fraud can
assess transactions with deterministic rules before machine learning exists.

These boundaries are a design, not implemented transaction flows. There are no payment
APIs, fraud decisions, accounting entries, execution simulations, or databases yet.

## Two telemetry approaches

The plan is to compare explicit SDK setup and Operator-injected instrumentation
in the same Kubernetes cluster. Both use OpenTelemetry SDKs; the difference is
whether service code or the Operator initializes and configures the SDK.

| Service | Approach | Current status |
| --- | --- | --- |
| `orders/` | Explicit SDK setup through `atlas-telemetry`; manual business spans and counters. | Implemented, with provider lifecycle and typed application state owned by orders. |
| `market-data/` | Operator-injected Python automatic instrumentation. | Planned Kubernetes example; currently an HTTP scaffold without this injection configured. |
| `fraud/` | To be decided. | HTTP scaffold; no telemetry setup yet. |
| Execution simulator, portfolio, ledger, payments | To be decided when implemented. | Documentation placeholders. |

Both examples can use the same Alloy/OpenTelemetry Collector, trace backend,
Loki, Prometheus, and Grafana. Keep distinct resource names (`service.name=orders`
and `service.name=market-data`). Grafana queries their shared backends; applications
do not send telemetry directly to Grafana.

Orders currently exposes Prometheus metrics at `/metrics/` and writes JSON logs
to stderr. Automatic instrumentation's supported signals depend on the selected
Python distribution and enabled libraries; injection alone does not configure log
collection or a metrics backend. Propagate trace context between services to join
their spans into distributed traces.

Keep one SDK initializer per process: inject only the managed example, and do not
also call orders' provider setup in that service. An automatically instrumented
service can still add manual business spans through the OpenTelemetry API using
the already-initialized providers.

### Operator and Helm references for the managed example

- [Kubernetes Operator overview](https://opentelemetry.io/docs/platforms/kubernetes/operator/): manages Collector resources and automatic instrumentation injection.
- [OpenTelemetry Helm charts](https://opentelemetry.io/docs/platforms/kubernetes/helm/): separate Operator, Collector, and Demo charts; installing all three is not required.
- [Operator chart and prerequisites](https://github.com/open-telemetry/opentelemetry-helm-charts/tree/main/charts/opentelemetry-operator): current Kubernetes/Helm requirements and webhook certificate options.
- [Automatic instrumentation configuration](https://opentelemetry.io/docs/platforms/kubernetes/operator/automatic/): `Instrumentation` resources and language-specific pod annotations.

Reference installation commands, assuming the chart's prerequisites and
`cert-manager` are already installed:

```sh
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
helm upgrade --install opentelemetry-operator open-telemetry/opentelemetry-operator \
  --namespace observability --create-namespace \
  --set manager.collectorImage.repository=ghcr.io/open-telemetry/opentelemetry-collector-releases/opentelemetry-collector-k8s
```

If using another webhook certificate method, follow the chart's certificate
configuration instead of the `cert-manager` assumption above. The Collector image
setting does not deploy a Collector by itself. An existing Alloy receiver can
serve both service examples; the Operator and separate Collector chart are not
required by orders' explicit SDK setup.

After installing the Operator, define an `Instrumentation` resource for market data
and add `instrumentation.opentelemetry.io/inject-python` to the Deployment's **pod
template** annotations. Recreate the pods to apply injection. See the
[managed instrumentation example](../docs/telemetry.md#two-instrumentation-approaches-in-kubernetes).
These are future setup references; this repository does not currently install the
Operator or provide the market-data Kubernetes Deployment.

## Turn a placeholder into a service

Add its own manifest, `src/atlas_<name>/` package, tests, and Dockerfile. Remove the
directory from the root UV workspace `exclude` list, update `uv.lock`, and add a
Compose entry when it can run. Keep the Dockerfile beside the service's manifest.
See the [development guide](../docs/development.md#add-a-service) for the full procedure.
