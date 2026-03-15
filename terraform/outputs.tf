output "vpc_id" {
  description = "VPC ID (for terraform_remote_state from EKS module)"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs (for terraform_remote_state from EKS module)"
  value       = module.vpc.private_subnets
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks --region ${var.region} update-kubeconfig --name ${var.cluster_name}"
}