data "aws_region" "current" {}

output "url" {
  description = "The URL of the function behind the load balancer, for TEST_LAMBDA_URL"
  value       = "http://${aws_lb.this.dns_name}"
}

output "function_name" {
  description = "The name of the function, for aws lambda invoke"
  value       = aws_lambda_function.function.function_name
}

output "log_group" {
  description = "The log group of the function, for aws logs tail"
  value       = aws_cloudwatch_log_group.function.name
}

output "region" {
  description = "The region of the resources, for the commands of the AWS CLI"
  value       = data.aws_region.current.region
}
