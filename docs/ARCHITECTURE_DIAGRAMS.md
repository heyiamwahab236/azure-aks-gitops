> Historical baseline document. See README.md and PORTFOLIO_REPORT.md for the current implementation.

# Architecture Diagrams

## Local System Architecture

```mermaid
flowchart LR
    User[User Browser]
    Frontend[Frontend Dashboard<br/>Nginx + HTML/CSS/JS]

    Order[Order Service<br/>FastAPI]
    Inventory[Inventory Service<br/>FastAPI Worker]
    Payment[Payment Service<br/>FastAPI Worker]
    Notification[Notification Service<br/>FastAPI Worker]

    Rabbit[(RabbitMQ<br/>Topic Exchange)]
    Postgres[(PostgreSQL)]

    User --> Frontend

    Frontend -->|POST /api/orders| Order
    Frontend -->|GET /api/inventory| Inventory
    Frontend -->|GET /api/payments| Payment
    Frontend -->|GET /api/notifications| Notification

    Order -->|save order| Postgres
    Inventory -->|save inventory reservation| Postgres
    Payment -->|save payment| Postgres
    Notification -->|save notification| Postgres

    Order -->|publish order.created| Rabbit
    Rabbit -->|consume order.created| Inventory
    Inventory -->|publish inventory.reserved / inventory.failed| Rabbit
    Rabbit -->|consume inventory.reserved| Payment
    Payment -->|publish payment.completed| Rabbit
    Rabbit -->|consume events| Notification
```

## Order Processing Sequence

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant OS as Order Service
    participant MQ as RabbitMQ
    participant IS as Inventory Service
    participant PS as Payment Service
    participant NS as Notification Service
    participant DB as PostgreSQL

    User->>FE: Submit order
    FE->>OS: POST /api/orders
    OS->>DB: Save order
    OS->>MQ: Publish order.created
    OS-->>FE: Return order_id

    MQ->>IS: Deliver order.created
    IS->>DB: Check and update stock
    IS->>MQ: Publish inventory.reserved

    MQ->>PS: Deliver inventory.reserved
    PS->>DB: Save payment
    PS->>MQ: Publish payment.completed

    MQ->>NS: Deliver order/payment events
    NS->>DB: Save notification records

    FE->>OS: GET /api/orders
    FE->>IS: GET /api/inventory
    FE->>PS: GET /api/payments
    FE->>NS: GET /api/notifications
```

## Deployment Progression

```mermaid
flowchart TD
    Code[Source Code]
    Compose[Docker Compose<br/>local development]
    Images[Docker Images]
    Minikube[Minikube<br/>local Kubernetes]
    Helm[Helm Chart]
    ACR[Azure Container Registry]
    AKS[Azure Kubernetes Service]
    AzureServices[Azure Service Bus<br/>Azure PostgreSQL<br/>Key Vault<br/>Monitor]

    Code --> Compose
    Code --> Images
    Images --> Minikube
    Helm --> Minikube
    Images --> ACR
    ACR --> AKS
    Helm --> AKS
    AKS --> AzureServices
```

## Production Target Architecture

```mermaid
flowchart LR
    User[User]
    Ingress[AKS Ingress<br/>TLS + Routing]
    Frontend[Frontend Pod]

    Order[Order Service Pod]
    Inventory[Inventory Service Pod]
    Payment[Payment Service Pod]
    Notification[Notification Service Pod]

    ASB[(Azure Service Bus<br/>Topics + Subscriptions)]
    PG[(Azure PostgreSQL<br/>Flexible Server)]
    KV[(Azure Key Vault)]
    Monitor[(Azure Monitor<br/>App Insights + Logs)]
    ACR[(Azure Container Registry)]

    User --> Ingress
    Ingress --> Frontend
    Frontend --> Order
    Frontend --> Inventory
    Frontend --> Payment
    Frontend --> Notification

    ACR --> Order
    ACR --> Inventory
    ACR --> Payment
    ACR --> Notification
    ACR --> Frontend

    Order --> ASB
    ASB --> Inventory
    Inventory --> ASB
    ASB --> Payment
    Payment --> ASB
    ASB --> Notification

    Order --> PG
    Inventory --> PG
    Payment --> PG
    Notification --> PG

    Order --> KV
    Inventory --> KV
    Payment --> KV
    Notification --> KV

    Order --> Monitor
    Inventory --> Monitor
    Payment --> Monitor
    Notification --> Monitor
```
