variable "cluster_name" { type = string }
variable "cluster_version" { type = string }
variable "use_remote_state" {
  type        = bool
  default     = false
  description = "If true, read VPC from terraform_remote_state (standalone EKS). If false, use vpc_id/subnet_ids."
}
variable "vpc_id" {
  type        = string
  default     = null
  description = "VPC ID (from root module.vpc when use_remote_state = false)"
}
variable "subnet_ids" {
  type        = list(string)
  default     = null
  description = "Subnet IDs for EKS (from root when use_remote_state = false)"
}