variable "subscription_id" {
  type        = string
  description = "Explicitly approved Azure subscription. No resources are created by validation."
}
variable "location" {
  type        = string
  description = "User-selected Azure region after quota and cost review."
}
variable "name" {
  type    = string
  default = "order-portfolio"
}
variable "acr_name" {
  type        = string
  description = "Globally unique alphanumeric ACR name."
}
variable "node_count" {
  type    = number
  default = 1
  validation {
    condition     = var.node_count >= 1 && var.node_count <= 3
    error_message = "Portfolio node count must be between 1 and 3."
  }
}
variable "vm_size" {
  type        = string
  description = "Choose after confirming regional quota and budget."
}
variable "admin_group_object_ids" {
  type        = list(string)
  description = "Entra ID groups authorized to administer the cluster."
  validation {
    condition     = length(var.admin_group_object_ids) > 0
    error_message = "Provide an administrator group before deployment."
  }
}
variable "authorized_ip_ranges" {
  type        = set(string)
  description = "Trusted public IP CIDRs allowed to reach the AKS API."
  validation {
    condition     = length(var.authorized_ip_ranges) > 0 && !contains(var.authorized_ip_ranges, "0.0.0.0/0")
    error_message = "Provide restricted administrator IP ranges, not the entire Internet."
  }
}
