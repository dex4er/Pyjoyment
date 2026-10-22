# The default VPC of the region and its default subnets, one in each zone, as a load balancer needs two zones and
# the function needs no VPC, only with the load balancer
data "aws_vpc" "default" {
  count = var.alb ? 1 : 0

  default = true
}

data "aws_subnets" "default" {
  count = var.alb ? 1 : 0

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}
