variable "name" {
  description = "The name of the function and of the other resources"
  type        = string
  default     = "pyjoyment-stream"
}

variable "region" {
  description = "The region, or the one of the default chain of AWS"
  type        = string
  default     = null
}

variable "runtime" {
  description = "The runtime of Python of the function, python3.15 in its preview or python3.14"
  type        = string
  default     = "python3.15"
}
