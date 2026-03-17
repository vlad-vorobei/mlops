variable "aws_region" {
  description = "AWS region for Lambda and Step Functions"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "mlops-train"
}
