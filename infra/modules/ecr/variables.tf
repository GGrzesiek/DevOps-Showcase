variable "name" {
  type = string
}

variable "keep_last_n" {
  type    = number
  default = 10
}

variable "tags" {
  type    = map(string)
  default = {}
}
