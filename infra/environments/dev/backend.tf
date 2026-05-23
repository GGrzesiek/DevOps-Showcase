terraform {
  backend "s3" {
    bucket         = "YOUR_BUCKET_NAME"   # replace with output from bootstrap
    key            = "dev/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
