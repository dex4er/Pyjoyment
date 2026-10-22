variable "name" {
  description = "The name of the function, of its load balancer and of the other resources"
  type        = string
  default     = "pyjoyment"
}

variable "region" {
  description = "The region, or the one of the default chain of AWS"
  type        = string
  default     = null
}

variable "runtime" {
  description = "The runtime of Python of the function"
  type        = string
  default     = "python3.14"
}

variable "multi_value_headers" {
  description = "Whether the load balancer sends the headers and the parameters of the query with all their values"
  type        = bool
  default     = false
}
