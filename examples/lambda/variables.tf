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
  description = "The runtime of Python of the function, python3.15 in its preview or python3.14"
  type        = string
  default     = "python3.15"
}

variable "multi_value_headers" {
  description = "Whether the load balancer sends the headers and the parameters of the query with all their values"
  type        = bool
  default     = false
}

variable "alb" {
  description = "Whether the function is behind an Application Load Balancer too, which costs for each hour it runs"
  type        = bool
  default     = false
}

variable "layers" {
  description = "More layers of the function, after the one of the framework"
  type        = list(string)
  default = [
    # PHP 8.5 of Bref, https://bref.sh, whose php-fpm app.py starts, with phpinfo.php under /php, in eu-central-1
    # "arn:aws:lambda:eu-central-1:873528684822:layer:arm-php-85:21",
  ]
}
