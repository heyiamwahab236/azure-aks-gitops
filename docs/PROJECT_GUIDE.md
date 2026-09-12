# Event-Driven Order Processing Platform Guide

## 1. Project Goal

This project is a local-first version of a production-style microservices platform.

It simulates an order processing system where one service accepts an order, then other services react to events asynchronously.

The main goal is to learn and demonstrate:

- Python FastAPI microservices
- Event-driven architecture
- Docker containerization
- Kubernetes deployment with Minikube
- Helm-based deployment packaging
- A path toward Azure Container Registry and later AKS/production

## 2. Current Local Architecture

The project currently runs locally with Docker Compose.

```text
Browser
  |
  v
Frontend Dashboard
  |
  v
Nginx reverse proxy
  |
  +--> Order Service
  +--> Inventory Service
  +--> Payment Service
  +--> Notification Service

Order Service
  |
  v
RabbitMQ topic exchange
  |
  +--> Inventory Service
  +--> Payment Service
  +--> Notification Service

All services use PostgreSQL for persistence.
```

## 3. Services

### Frontend

Location:

```text
frontend/
```

Purpose:

- Provides a browser dashboard
- Lets the user create orders
- Shows orders, inventory, payments, and notifications
- Uses Nginx to proxy API requests to backend services

Local URL:

```text
http://localhost:8080
```

Important files:

```text
frontend/index.html
frontend/styles.css
frontend/app.js
frontend/nginx.conf
frontend/Dockerfile
```

The frontend does not talk directly to every backend using different ports. Instead, it calls paths like:

```text
/api/orders
/api/inventory
/api/payments
/api/notifications
```

Nginx then forwards those requests to the correct backend service.

### Order Service

Location:

```text
services/order-service/
```

Purpose:

- Accepts new orders through REST API
- Stores order records in PostgreSQL
- Publishes an `order.created` event to RabbitMQ

Main endpoints:

```text
POST /orders
GET /orders
GET /health
```

When an order is created, this service publishes an event like:

```json
{
  "event_type": "order.created",
  "order_id": "ord-abc123",
  "customer_id": "cust-1",
  "items": [
    {
      "product_id": "sku-1",
      "quantity": 2
    }
  ],
  "created_at": "2026-07-17T10:00:00Z"
}
```

### Inventory Service

Location:

```text
services/inventory-service/
```

Purpose:

- Listens for `order.created`
- Checks if requested products have enough stock
- Reduces inventory when stock is available
- Publishes either `inventory.reserved` or `inventory.failed`

Main endpoints:

```text
GET /inventory
GET /health
```

Current seeded products:

```text
sku-1: 100 units
sku-2: 50 units
```

### Payment Service

Location:

```text
services/payment-service/
```

Purpose:

- Listens for `inventory.reserved`
- Simulates a successful payment
- Stores payment records
- Publishes `payment.completed`

Main endpoints:

```text
GET /payments
GET /health
```

### Notification Service

Location:

```text
services/notification-service/
```

Purpose:

- Listens for important events
- Stores notification records
- Simulates sending notifications

Main endpoints:

```text
GET /notifications
GET /health
```

Events consumed:

```text
order.created
inventory.reserved
inventory.failed
payment.completed
payment.failed
```

## 4. How The Services Are Connected

There are two kinds of communication in this project.

### Synchronous HTTP Communication

The frontend uses HTTP to fetch data from backend services.

```text
Frontend -> Nginx -> Order Service
Frontend -> Nginx -> Inventory Service
Frontend -> Nginx -> Payment Service
Frontend -> Nginx -> Notification Service
```

This is used when the browser needs current data.

Example:

```text
Browser requests /api/orders
Nginx forwards to order-service:8000/orders
Order Service returns order list
```

### Asynchronous Event Communication

Backend services use RabbitMQ events to communicate with each other.

```text
Order Service -> RabbitMQ -> Inventory Service
Inventory Service -> RabbitMQ -> Payment Service
Payment Service -> RabbitMQ -> Notification Service
```

This is used for business workflow.

The services do not need to know each other's direct API addresses for the order workflow. They only publish and consume events.

## 5. Order Flow

Full flow:

```text
1. User opens frontend dashboard.
2. User submits an order.
3. Frontend sends POST /api/orders.
4. Nginx forwards request to Order Service.
5. Order Service saves order in PostgreSQL.
6. Order Service publishes order.created to RabbitMQ.
7. Inventory Service consumes order.created.
8. Inventory Service checks stock.
9. Inventory Service publishes inventory.reserved.
10. Payment Service consumes inventory.reserved.
11. Payment Service stores payment record.
12. Payment Service publishes payment.completed.
13. Notification Service consumes events and stores notification records.
14. Frontend refreshes data and shows updated status.
```

## 6. Local Docker Compose Setup

Docker Compose is used for quick local development.

Main file:

```text
docker-compose.yml
```

It starts:

```text
postgres
rabbitmq
order-service
inventory-service
payment-service
notification-service
frontend
```

Run:

```bash
docker compose up --build
```

Open frontend:

```text
http://localhost:8080
```

Open Order API docs:

```text
http://localhost:8001/docs
```

Open RabbitMQ UI:

```text
http://localhost:15672
```

RabbitMQ login:

```text
guest / guest
```

## 7. Moving From Docker Compose To Minikube

Docker Compose is good for local development, but Minikube is closer to real Kubernetes.

Minikube lets you run Kubernetes locally before deploying to AKS.

### Step 1: Start Docker Desktop

Docker Desktop must be running because Minikube needs a container runtime.

### Step 2: Start Minikube

```bash
minikube start
```

Optional:

```bash
minikube status
```

### Step 3: Install Helm

Helm is needed because this project includes a Helm chart.

Check if Helm exists:

```bash
helm version
```

If Helm is not installed, install it first.

On Windows, common options are:

```bash
winget install Helm.Helm
```

or:

```bash
choco install kubernetes-helm
```

### Step 4: Build Images Inside Minikube

Minikube has its own image environment. Build images directly into Minikube:

```bash
minikube image build -t order-service:local ./services/order-service
minikube image build -t inventory-service:local ./services/inventory-service
minikube image build -t payment-service:local ./services/payment-service
minikube image build -t notification-service:local ./services/notification-service
minikube image build -t order-platform-frontend:local ./frontend
```

### Step 5: Deploy With Helm

```bash
helm upgrade --install order-platform ./helm/order-platform
```

### Step 6: Check Pods

```bash
kubectl get pods
```

You should see pods for:

```text
postgres
rabbitmq
order-service
inventory-service
payment-service
notification-service
frontend-service
```

### Step 7: Check Services

```bash
kubectl get svc
```

### Step 8: Port-Forward Frontend

```bash
kubectl port-forward svc/frontend-service 8080:80
```

Open:

```text
http://localhost:8080
```

### Step 9: Port-Forward Order API

In another terminal:

```bash
kubectl port-forward svc/order-service 8001:8000
```

Open:

```text
http://localhost:8001/docs
```

### Step 10: View Logs

```bash
kubectl logs deploy/order-service
kubectl logs deploy/inventory-service
kubectl logs deploy/payment-service
kubectl logs deploy/notification-service
```

Follow logs:

```bash
kubectl logs -f deploy/inventory-service
```

## 8. Minikube Troubleshooting

If pods are not ready:

```bash
kubectl describe pod <pod-name>
```

If a service cannot connect to RabbitMQ or Postgres:

```bash
kubectl logs deploy/<service-name>
```

If the frontend opens but API calls fail:

```bash
kubectl logs deploy/frontend-service
```

If images are not found:

```bash
minikube image ls
```

Then rebuild missing images:

```bash
minikube image build -t order-service:local ./services/order-service
```

## 9. Moving From Minikube To Azure Container Registry

After the project works on Minikube, the next step is pushing images to Azure Container Registry.

ACR is where production images are stored before AKS pulls them.

### Step 1: Login To Azure

```bash
az login
```

### Step 2: Create Resource Group

Example:

```bash
az group create \
  --name rg-order-platform-dev \
  --location eastus
```

### Step 3: Create Azure Container Registry

ACR names must be globally unique and use only letters and numbers.

Example:

```bash
az acr create \
  --resource-group rg-order-platform-dev \
  --name orderplatformacr123 \
  --sku Basic
```

### Step 4: Login To ACR

```bash
az acr login --name orderplatformacr123
```

### Step 5: Build And Tag Images

Replace `orderplatformacr123.azurecr.io` with your ACR login server.

```bash
docker build -t orderplatformacr123.azurecr.io/order-service:v1 ./services/order-service
docker build -t orderplatformacr123.azurecr.io/inventory-service:v1 ./services/inventory-service
docker build -t orderplatformacr123.azurecr.io/payment-service:v1 ./services/payment-service
docker build -t orderplatformacr123.azurecr.io/notification-service:v1 ./services/notification-service
docker build -t orderplatformacr123.azurecr.io/order-platform-frontend:v1 ./frontend
```

### Step 6: Push Images To ACR

```bash
docker push orderplatformacr123.azurecr.io/order-service:v1
docker push orderplatformacr123.azurecr.io/inventory-service:v1
docker push orderplatformacr123.azurecr.io/payment-service:v1
docker push orderplatformacr123.azurecr.io/notification-service:v1
docker push orderplatformacr123.azurecr.io/order-platform-frontend:v1
```

### Step 7: Update Helm Values

For ACR-based deployment, update:

```text
helm/order-platform/values.yaml
```

Change:

```yaml
order:
  image: order-service:local
```

to:

```yaml
order:
  image: orderplatformacr123.azurecr.io/order-service:v1
```

Do this for every service.

### Step 8: Test ACR Images Locally If Needed

You can run an image directly:

```bash
docker run --rm -p 8001:8000 orderplatformacr123.azurecr.io/order-service:v1
```

For the full system, Docker Compose or Kubernetes is better because services depend on PostgreSQL and RabbitMQ.

## 10. After ACR: Moving To AKS

Once images are in ACR, the next production step is AKS.

High-level process:

```text
1. Create AKS cluster.
2. Attach ACR to AKS.
3. Replace local images in Helm values with ACR images.
4. Deploy using Helm.
5. Add Ingress controller.
6. Add external DNS and TLS.
7. Replace RabbitMQ with Azure Service Bus.
8. Replace local PostgreSQL with Azure PostgreSQL Flexible Server.
9. Move secrets to Azure Key Vault.
10. Add Azure DevOps pipeline.
11. Add ArgoCD GitOps.
```

Attach ACR to AKS:

```bash
az aks update \
  --resource-group rg-order-platform-dev \
  --name aks-order-platform-dev \
  --attach-acr orderplatformacr123
```

Deploy with Helm:

```bash
helm upgrade --install order-platform ./helm/order-platform
```

## 11. Local Versus Production Components

| Local | Production |
| --- | --- |
| Docker Compose | AKS |
| Minikube | AKS |
| RabbitMQ | Azure Service Bus |
| Local PostgreSQL container | Azure PostgreSQL Flexible Server |
| Local environment variables | Azure Key Vault |
| Local Docker images | Azure Container Registry |
| Manual Helm command | Azure DevOps + ArgoCD |

## 12. Recommended Next Tasks

Build the project in this order:

```text
1. Run with Docker Compose.
2. Test creating orders from the frontend.
3. Confirm events appear in RabbitMQ.
4. Deploy the same system to Minikube.
5. Push images to ACR.
6. Create AKS.
7. Deploy ACR images to AKS with Helm.
8. Replace RabbitMQ with Azure Service Bus.
9. Replace local Postgres with Azure PostgreSQL.
10. Add Terraform.
11. Add Azure DevOps pipeline.
12. Add ArgoCD.
```

This order keeps the project understandable. Each step upgrades one layer without rewriting the whole system.
