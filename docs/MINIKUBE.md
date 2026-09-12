# Repeatable local deployment

Run from the repository root in PowerShell, with Docker Desktop running and docker, minikube, kubectl and Python 3 on PATH. Builds need access to container and Python package registries. All commands target the order-platform profile, context and namespace.

## Existing lab (normal workflow)

```powershell
minikube start -p order-platform
./scripts/deploy-local.ps1
```

The script checks Docker, cluster, secret names and dependency readiness; records PVC identities; builds five images with a fresh tag; verifies images exist; validates application manifests on the server; applies them and waits for five deployments. It confirms PVC identities and bindings are unchanged. Tags are rendered in memory; source manifests remain unchanged.

For a recorded release, supply a unique tag:

```powershell
./scripts/deploy-local.ps1 -Tag local-my-change-001
```

Existing tags are rejected. After a build failure, correct the error and rerun with a new tag. Nothing is applied until all images build successfully. An apply/rollout failure can leave a partial application deployment: inspect pods and events, fix the problem and rerun. There is no automatic rollback. The script never applies storage manifests or overwrites secrets.

## Exercise the application

Keep this running in a separate terminal:

```powershell
kubectl --context=order-platform -n order-platform port-forward svc/frontend-service 8080:80 --address=127.0.0.1
```

Open http://localhost:8080, then run:

```powershell
python tests/local_scenarios.py http://localhost:8080
```

This checks successful processing, insufficient stock, and invalid quantities/missing items. Run without concurrent orders. It leaves two labelled orders and their records and consumes one stock unit. The no-payment assertion for insufficient stock observes ten seconds after the failure event; it does not prove absence indefinitely. The smaller tests/smoke.py remains available.

## Brand-new disposable lab only

Skip this for the existing lab. Never regenerate credentials for populated volumes: credentials must match the database's existing password.

```powershell
minikube start -p order-platform
kubectl --context=order-platform create namespace order-platform
python scripts/init-local-secrets.py
kubectl --context=order-platform apply -f k8s/config/configmap.yaml -f k8s/postgres -f k8s/rabbitmq
./scripts/deploy-local.ps1
```

Stop if a command fails. The initializer requires an empty namespace (no PVCs, StatefulSets or secrets), generates random credentials and sends them to Kubernetes over stdin. It does not print or save passwords and uses create rather than overwrite. This is local lab secret management. The fresh-lab procedure is documented but has not been executed against a new cluster; the existing lab is the validated path.

## Current limitations

Orders still report created after processing; status propagation is Stage 2. Empty item lists and duplicate events remain known gaps. Payment and notification are simulated records. This uses plain Kubernetes manifests; do not install the legacy Helm chart over it. Helm alignment, security hardening, GitOps and Terraform/Azure follow later.
