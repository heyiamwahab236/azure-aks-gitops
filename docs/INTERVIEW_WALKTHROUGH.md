# Employer walkthrough: event-driven order platform

## Your 60-second introduction

“I built a local Kubernetes portfolio that demonstrates how an order moves through four Python services using RabbitMQ. I added transactional outbox publishing, duplicate-safe consumers and stock locking, then deployed the application through Helm and Argo CD. Prometheus and Grafana expose operational metrics. I used security scans and JMeter to find and resolve issues, including a database DNS failure under load. The working environment is Minikube; Azure Terraform is prepared and validated but has not been deployed.”

## Ten-minute presentation

| Time | Show | Explain |
| --- | --- | --- |
| 0–1 min | Architecture in README | Browser/Nginx routes to APIs; RabbitMQ carries events; services persist to PostgreSQL. |
| 1–3 min | Application at http://localhost:18080 | Choose a stocked product, order one unit with a unique demo customer, and follow the completed timeline. Payments and notifications are simulated. |
| 3–4 min | Insufficient-stock order | Request more than available stock. Explain failed status and why a payment should not follow this failure. |
| 4–6 min | Argo CD at https://localhost:8081 | Select order-platform. Synced means Git matches managed resources; Healthy reports resource health. Show Deployments, Pods and Services. |
| 6–7 min | Grafana at http://localhost:13000/d/order-platform | Show request rate, latency, consumer connectivity and pending outbox events. Generate traffic by refreshing the application. |
| 7–9 min | PERFORMANCE.md and SECURITY.md | Explain the measured DNS incident, zero-error rerun, remaining notification latency and actual scan results. |
| 9–10 min | Helm chart and Terraform files | Explain release configuration versus infrastructure provisioning, then state current boundaries. |

Open Argo CD in external Chrome: the Codex embedded browser rejects its self-signed certificate. Sign in privately before screen sharing. Do not display password commands, Secrets, or private keys during an interview.

## Explain the order journey

1. The Order API commits an order and an outbox event together in PostgreSQL.
2. The publisher sends the pending event to RabbitMQ with publisher confirmation. If the broker is down, the event stays pending.
3. Inventory consumes order.created, locks stock rows, and either reserves stock or records failure. Its business change and next outbox event commit together.
4. Payment handles inventory.reserved and simulates payment completion.
5. Notification handles the resulting event and writes a local record. The Order service also consumes status events for the frontend timeline.

This is asynchronous processing, not a chain of synchronous API calls. A single PostgreSQL instance is a deliberate lab simplification; service-level database permissions and isolation remain production work.

## Questions and answers to practise

**Why RabbitMQ?** It decouples producers and consumers and buffers asynchronous work. It adds operational complexity and requires retry and duplicate-handling design.

**Why can an event arrive twice?** A consumer can commit its business transaction and lose its connection before acknowledging the message. RabbitMQ may redeliver it. The inbox prevents the same event from repeating the business write.

**Is this exactly-once messaging?** No. Delivery is at-least-once. Database transactions and inbox deduplication protect the recorded business effects. Future external payment calls would need their own provider idempotency guarantees.

**How do you prevent overselling?** Inventory locks the relevant database rows within its transaction and checks stock before deduction. A live concurrent-order test verified that only one buyer obtained the final unit.

**What happens to invalid messages?** Invalid messages go to a dead-letter queue; transient handler failures have bounded retries. An operator must investigate and validate corrections before replaying them.

**What does Argo CD do?** It reads the Helm configuration in Git, compares it with Kubernetes, and reconciles differences. We verified self-healing by manually increasing notification replicas from one to two and observing restoration to one.

**Does Argo CD build images?** No. Our running images were built locally into Minikube. A company pipeline would build and scan images, publish them to a registry, then propose a versioned deployment update in Git.

**How would you roll back?** Revert the application image/configuration in Git while retaining the previous image. This does not undo database migrations or business data; those require separate planning.

**What did load testing show?** An initial 25-user run had 278 errors out of 7,500 requests. Logs identified database DNS resolution failures. Explicit internal service DNS names removed errors in the equivalent final run. Notification p95 remained 1,492 ms, above our 1,000 ms target. Laptop results are not production capacity estimates.

**What security methods did you use?** Bandit for Python source analysis; pip-audit for Python dependency vulnerabilities; Trivy for image vulnerabilities and CycloneDX SBOMs; ZAP for passive web scanning. Final ZAP results were informational only, but vendor-unfixed backend OS findings remain documented.

**Is the CI pipeline proven on GitHub?** No. The workflow exists, but GitHub blocked hosted jobs with an account billing/spending-limit message before execution. Local verification and GitOps reconciliation are separate and were tested successfully. No paid service is required for this demonstration.

**What would change in a workplace?** Reviewed pull requests, registry image publishing, separate environments, release approvals, trusted TLS, authentication, managed secrets, enforced network isolation, backups and restore tests, and actionable alerts. Terraform would provision approved cloud infrastructure; Kubernetes would run the application; Argo CD would reconcile releases.

## Honest boundaries

- Running: Minikube, Python/FastAPI, HTML/CSS/JavaScript frontend, RabbitMQ, PostgreSQL, Helm, Argo CD, Prometheus and Grafana.
- Prepared only: Azure AKS/ACR Terraform. No Azure deployment.
- Not completed: hosted CI execution and automatic registry image promotion.
- Simulated: payments and notifications. No real charges or email delivery.
- Local limitations: single node, shared database credentials, ephemeral monitoring, no public authentication/TLS, notification latency above target.

## Before and after the demo

Follow OPERATIONS.md to start local port forwards. Check stocked products, application health and current Grafana data. Keep the architecture and evidence documents open as a fallback. Avoid broker-outage drills or load tests during the basic demonstration; use recorded results unless a deeper demonstration is requested. Each successful order consumes stock. Close port-forward processes with Ctrl+C when finished; do not delete PVCs or reset the database.
