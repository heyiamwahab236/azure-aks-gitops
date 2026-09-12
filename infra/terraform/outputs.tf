output "cluster_name" { value = azurerm_kubernetes_cluster.platform.name }
output "resource_group" { value = azurerm_resource_group.platform.name }
output "registry" { value = azurerm_container_registry.platform.login_server }
output "oidc_issuer" { value = azurerm_kubernetes_cluster.platform.oidc_issuer_url }
