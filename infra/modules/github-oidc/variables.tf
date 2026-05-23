variable "github_org"  { type = string }
variable "github_repo" { type = string }
variable "ecr_arns"    { type = list(string) }
variable "tags"        { type = map(string); default = {} }
