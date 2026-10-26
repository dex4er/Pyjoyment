terraform {
  required_version = "~> 1.13.0"

  # The providers are not locked, so that they are the newest of their versions
  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# The credentials and the region of the default chain of AWS: the variables of the environment, the profile and the
# role of the machine
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Name = var.name
    }
  }
}
