# Local GitOps

Argo CD v3.5.2 was installed from its official release into namespace argocd on the order-platform Minikube profile. application.yaml restricts this project to this repository and namespace and permits only Deployments, Services and ConfigMaps. Pruning is off; self-healing is on.

The private GitHub repository requires read-only authentication. A repository deploy key must be approved and registered with GitHub, then its private half stored only in an Argo CD repository Secret. Neither half needs to be committed. See PORTFOLIO_REPORT.md for connection and reconciliation status.

Once credentials are installed:

```powershell
kubectl --context=order-platform apply -f deploy/argocd/application.yaml
kubectl --context=order-platform -n argocd get application order-platform
```

Images in this local lab are prebuilt in Minikube. GitOps reconciles the Helm-declared tag and configuration; it does not build source code. GitHub CI builds and validates a separate disposable stack. A remote registry promotion flow (ACR/GHCR) is future Azure integration work.

References: [private repository authentication](https://argo-cd.readthedocs.io/en/stable/user-guide/private-repositories/), [declarative configuration](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/).
