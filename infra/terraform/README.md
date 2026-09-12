# Optional Azure infrastructure

Terraform defines a resource group, VNet/subnet, AKS and ACR, managed identity, AcrPull, Entra RBAC, restricted API IP ranges, OIDC and workload identity. Local initialization and validation do not create cloud resources.

```powershell
terraform init -backend=false
terraform fmt -check
terraform validate
```

Before plan/apply, choose the subscription, region, VM size, budget, administrator group and trusted public IP ranges. Configure protected remote state with Azure Blob storage and access controls, then review a concrete plan and cost estimate. No subscription, cloud credentials, Terraform state or tfvars belong in Git.

This module provisions infrastructure only. Database/broker persistence, backups, production secrets, registry publishing, application ingress/TLS and operational availability need an explicit Azure deployment design. Local RabbitMQ has not been replaced with Azure Service Bus; these are different integrations. The existing application remains on Minikube.
