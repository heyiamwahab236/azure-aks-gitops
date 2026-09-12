# Stage 01 — Repeatable local baseline

Status: complete for the existing Minikube lab, 2026-09-12.

## Changes

- Added scripts/deploy-local.ps1: checks dependencies, builds five locally tagged images, verifies image presence, validates and applies only application manifests, waits for rollouts, and compares PVC identity/binding before and after.
- Added scripts/init-local-secrets.py: generates credentials in memory for an empty lab namespace and refuses populated namespaces. No passwords in arguments, logs or repository files.
- Added tests/local_scenarios.py: exercises happy path, insufficient stock and invalid requests through Nginx.
- Updated MINIKUBE.md with deployment, testing, fresh-lab instructions and failure handling.

## Executed verification

Context, profile and namespace: order-platform. Release tag: stage01-20260912a.

| Check | Observed result |
| --- | --- |
| Docker and Minikube | Docker 29.4.0; cluster running |
| Build and deploy | All five images present, server dry run passed, five deployments rolled out |
| PostgreSQL volume | pvc-da453593-1345-473c-a0cc-5291eea05818 remained Bound |
| RabbitMQ volume | pvc-b2a8e0f9-ecc8-4c9b-b031-c51bb0885c82 remained Bound |
| Happy path | ord-6db9b98f27b1: completed payment and payment.completed notification; stock 45 to 44 |
| Insufficient stock | ord-5af9817aa181: inventory.failed notification; unchanged stock; no payment during subsequent 10-second observation |
| Invalid input | Quantity 0, quantity -1, and missing items each returned HTTP 422; no matching order persisted |
| Order status characterization | Both orders still show created; confirmed Stage 2 gap |
| Reused tag guard | Repeating deployment with stage01-20260912a exited 1 before building/applying |
| Secret initializer guard | Exited 1 with explicit refusal for the populated namespace; no credentials changed |

Commands (from repository root):

```powershell
./scripts/deploy-local.ps1 -Tag stage01-20260912a
kubectl --context=order-platform -n order-platform port-forward svc/frontend-service 18080:80 --address=127.0.0.1
python tests/local_scenarios.py http://localhost:18080
```

The first acceptance run passed its business checks but failed in the final status-reporting line because GET /orders uses id while POST uses order_id. Corrected the test to match the existing API; the full second run exited 0. The two runs leave four test orders and consume two stock units in total. No data cleanup was performed.

## Interview explanation

I made the existing event-driven application repeatably deployable on local Kubernetes. One script builds and verifies the images, validates manifests and checks deployment readiness while preserving the database volumes. I then tested the event flow through the frontend: successful orders create simulated payment and notification records, insufficient stock raises a failure event without payment, and invalid input is rejected before persistence.

## Limits and next stage

This validates the existing local lab, not production readiness or a fresh installation. The fresh-lab credential creation path is documented; only its populated-namespace refusal was exercised. Payment is simulated and notification is a database record. The negative payment assertion has a bounded observation window. Tests require available stock and no concurrent writers. There is no transactional outbox, duplicate-event protection or automatic rollback yet. The next stage adds real order status propagation, an event timeline and clearer failure behavior.
