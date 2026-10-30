# AKS architecture

AKS is the target runtime for this project. The diagram below describes the intended Azure deployment, not a recorded live environment. The existing application retains RabbitMQ and PostgreSQL; using AKS does not require rewriting it for Azure Service Bus.

```mermaid
flowchart TD
    TF[Terraform infrastructure] --> Cluster
    CI[CI build and validation] --> ACR[Azure Container Registry]
    Git[Git deployment configuration] --> Argo[Argo CD]
    Argo -->|Helm reconciliation| Cluster
    ACR -->|Container images| Cluster
    Browser[Browser] --> FE
    subgraph Cluster[Azure Kubernetes Service - target]
        FE[Nginx dashboard]
        O[Order API]
        I[Inventory API and consumer]
        P[Payment API and consumer]
        N[Notification API and consumer]
        R[(RabbitMQ)]
        D[(PostgreSQL with persistent storage)]
        FE --> O
        FE --> I
        FE --> P
        FE --> N
        O -->|order.created| R
        R --> I
        I -->|inventory.reserved or inventory.failed| R
        R --> P
        P -->|payment.completed| R
        R --> N
        O --> D
        I --> D
        P --> D
        N --> D
    end
    Cluster --> Metrics[Prometheus metrics and alerts]
    Metrics --> Dashboards[Grafana dashboards]
```

## Delivery responsibilities

- **Terraform:** provision the Azure resource group, networking, AKS, ACR and required identity assignments.
- **CI:** validate changes, build versioned images and publish them to ACR.
- **Helm:** describe the application workloads, configuration, service endpoints and persistent storage.
- **Argo CD:** reconcile reviewed deployment configuration from Git into AKS.
- **Prometheus and Grafana:** collect operational metrics, display dashboards and support alert investigation.

These are design responsibilities. Terraform, CI, Argo CD and monitoring configuration remain pending in the checked-in implementation.

## Application boundaries

The four services share a PostgreSQL database with separate tables. RabbitMQ carries asynchronous business events; HTTP serves the dashboard and API queries. Payments are simulated and notifications are database records.

Managed PostgreSQL, Azure Service Bus, Key Vault and public ingress/TLS are optional future design decisions. They are not prerequisites already implemented in this repository.

## Verification

Record Azure resource identifiers, source revision, rollout results, a successful order workflow, storage checks, GitOps reconciliation and a triggered monitoring alert before marking the AKS architecture as deployed. See [demo evidence](DEMO.md). Earlier local test results remain in [validation](VALIDATION.md).
