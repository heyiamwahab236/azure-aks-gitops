terraform {
  required_version = ">= 1.7, < 2.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.52.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "platform" {
  name     = "${var.name}-rg"
  location = var.location
  tags     = { project = "order-platform", environment = "portfolio" }
}

resource "azurerm_virtual_network" "platform" {
  name                = "${var.name}-vnet"
  location            = azurerm_resource_group.platform.location
  resource_group_name = azurerm_resource_group.platform.name
  address_space       = ["10.42.0.0/16"]
}

resource "azurerm_subnet" "aks" {
  name                 = "aks"
  resource_group_name  = azurerm_resource_group.platform.name
  virtual_network_name = azurerm_virtual_network.platform.name
  address_prefixes     = ["10.42.0.0/22"]
}

resource "azurerm_container_registry" "platform" {
  name                = var.acr_name
  location            = azurerm_resource_group.platform.location
  resource_group_name = azurerm_resource_group.platform.name
  sku                 = "Basic"
  admin_enabled       = false
}

resource "azurerm_kubernetes_cluster" "platform" {
  name                      = "${var.name}-aks"
  location                  = azurerm_resource_group.platform.location
  resource_group_name       = azurerm_resource_group.platform.name
  dns_prefix                = var.name
  sku_tier                  = "Free"
  oidc_issuer_enabled       = true
  workload_identity_enabled = true
  local_account_disabled    = true

  default_node_pool {
    name           = "system"
    node_count     = var.node_count
    vm_size        = var.vm_size
    vnet_subnet_id = azurerm_subnet.aks.id
  }
  identity { type = "SystemAssigned" }
  azure_active_directory_role_based_access_control {
    azure_rbac_enabled     = true
    admin_group_object_ids = var.admin_group_object_ids
  }
  api_server_access_profile {
    authorized_ip_ranges = var.authorized_ip_ranges
  }
  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    network_policy      = "azure"
    pod_cidr            = "10.244.0.0/16"
    service_cidr        = "10.43.0.0/16"
    dns_service_ip      = "10.43.0.10"
  }
}

resource "azurerm_role_assignment" "pull_images" {
  scope                            = azurerm_container_registry.platform.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_kubernetes_cluster.platform.kubelet_identity[0].object_id
  skip_service_principal_aad_check = true
}
