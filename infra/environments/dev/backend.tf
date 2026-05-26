terraform {
  backend "s3" {
    bucket         = "execon-tfstate-0852fa70"
    key            = "dev/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
