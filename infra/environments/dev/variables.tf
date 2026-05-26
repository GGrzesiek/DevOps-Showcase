variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "state_bucket_name" {
  type        = string
  description = "Name of the S3 bucket created by bootstrap (used for Terraform plan IAM policy)"
}

variable "github_org" {
  type = string
}

variable "github_repo" {
  type = string
}
