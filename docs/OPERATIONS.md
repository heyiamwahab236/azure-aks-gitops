# Local operations

Always use context/profile `order-platform`. Never run namespace, PVC, database or broker deletion as a routine reset.

## Inspect

```powershell
kubectl --context=order-platform -n order-platform get pods,pvc
kubectl --context=order-platform -n order-platform logs deployment/order-service --tail=50
kubectl --context=order-platform -n order-platform top pods
```

Application event logs include service, order ID, event type and outcome. Prometheus exposes HTTP latency, consumer connectivity, event outcomes and pending outbox counts. Alert rules cover unavailable targets, disconnected consumers, persistent pending events and dead-letter activity. Alerts are visible locally; no email/Slack receiver is configured.

## Dashboard connections (separate terminals)

```powershell
kubectl --context=order-platform -n order-platform port-forward svc/frontend-service 18080:80 --address=127.0.0.1
kubectl --context=order-platform -n order-observability port-forward svc/prometheus 19090:9090 --address=127.0.0.1
kubectl --context=order-platform -n order-observability port-forward svc/grafana 13000:3000 --address=127.0.0.1
```

Grafana grants local anonymous Viewer access. It is a ClusterIP service, not an Internet endpoint. Monitoring data is ephemeral (six-hour Prometheus retention); dashboard configuration is versioned.

## Validation

```powershell
python -m pytest tests/test_reliability.py -q
python tests/local_scenarios.py http://127.0.0.1:18080
Get-Content -Raw tests/live_reliability.py | kubectl --context=order-platform -n order-platform exec -i deployment/order-service -- python -
```

Live reliability tests create a dedicated test product, test orders and one malformed message retained in the inventory dead-letter queue. They do not reset existing stock. Before replaying dead-letter data, inspect the cause and validate the corrected event; blindly republishing malformed JSON repeats the failure. Transient handler failures receive up to three attempts; persistent failures require operator intervention.

## Release and recovery

Before GitOps is connected, deploy-local.ps1 builds, validates and applies local manifests. Once Argo CD owns the application, use `-BuildOnly -Tag <new-tag>`, update the Helm imageTag in a reviewed commit and let Argo reconcile. `-UseExistingImages` explicitly redeploys already-built immutable tags. Do not run direct apply concurrently with GitOps.

A bad application release can be recovered by reverting the Helm image tag/configuration in Git while retaining the old local images. Argo pruning is disabled and storage is outside the chart. This does not roll back database schema or business data. The initial history migration was additive and coordinated with application writers stopped; future schema changes require a separate migration review.
