# AKS and application diagrams

The infrastructure and delivery diagrams are the target design. The event sequence describes the existing application behavior.

## Azure delivery design

```mermaid
flowchart LR
    Source[Application source] --> CI[CI validation and image build]
    CI --> ACR[Azure Container Registry]
    Config[Reviewed Helm configuration in Git] --> Argo[Argo CD]
    TF[Terraform] --> AKS[Azure Kubernetes Service]
    ACR -->|Pull versioned images| AKS
    Argo -->|Reconcile workloads| AKS
    AKS --> Prometheus[Prometheus]
    Prometheus --> Grafana[Grafana]
```

## Application workflow

```mermaid
sequenceDiagram
    actor User
    participant FE as Nginx dashboard
    participant OS as Order API
    participant MQ as RabbitMQ
    participant IS as Inventory
    participant PS as Payment
    participant NS as Notification
    participant DB as PostgreSQL
    User->>FE: Submit order
    FE->>OS: POST /orders
    OS->>DB: Store order
    OS->>MQ: Publish order.created
    OS-->>FE: Return order ID
    MQ->>IS: Deliver order.created
    IS->>DB: Reserve stock
    IS->>MQ: Publish inventory.reserved
    MQ->>PS: Deliver inventory.reserved
    PS->>DB: Record simulated payment
    PS->>MQ: Publish payment.completed
    MQ->>NS: Deliver workflow events
    NS->>DB: Store notification records
```

Insufficient stock produces `inventory.failed` and does not proceed to payment. This diagram does not imply transactional event publishing, duplicate-event protection or external payment delivery.

## Runtime layout

See the complete [AKS architecture](ARCHITECTURE.md). Local development remains an optional way to exercise the same application; it is not the primary platform in the Azure design.
