terraform {
  backend "s3" {
    bucket  = "amzn-mlops-vl-nomad-tf-storage"
    key     = "vpc/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
