data "terraform_remote_state" "vpc" {
  count = var.use_remote_state ? 1 : 0

  backend = "s3"
  config = {
    bucket = "amzn-mlops-vl-nomad-tf-storage"
    key    = "root/terraform.tfstate"
    region = "us-east-1"
  }
}

locals {
  vpc_id     = var.use_remote_state ? data.terraform_remote_state.vpc[0].outputs.vpc_id : var.vpc_id
  subnet_ids = var.use_remote_state ? data.terraform_remote_state.vpc[0].outputs.private_subnets : var.subnet_ids
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access = true

  vpc_id     = local.vpc_id
  subnet_ids = local.subnet_ids

  eks_managed_node_groups = {
    cpu_nodes = {
      min_size     = 1
      max_size     = 5
      desired_size = 4

      instance_types = ["t3.small"]
      labels = {
        workload = "cpu-tasks"
      }
      tags = {
        ExtraTag = "CPU-Node"
      }
    }

    gpu_nodes = {
      min_size     = 1
      max_size     = 1
      desired_size = 1

      instance_types = ["t3.small"]
      labels = {
        workload = "gpu-tasks"
      }
      tags = {
        ExtraTag = "GPU-Node"
      }
    }
  }

  enable_cluster_creator_admin_permissions = true
}