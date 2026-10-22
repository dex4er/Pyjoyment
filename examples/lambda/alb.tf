# An Application Load Balancer on a public address, with the name of AWS, as there is no domain of its own, and so
# HTTP without TLS, with "-var alb=true"
resource "aws_security_group" "alb" {
  count = var.alb ? 1 : 0

  name   = "${var.name}-alb"
  vpc_id = data.aws_vpc.default[0].id
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  count = var.alb ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_lb" "this" {
  count = var.alb ? 1 : 0

  name               = var.name
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = data.aws_subnets.default[0].ids
}

resource "aws_lb_target_group" "function" {
  count = var.alb ? 1 : 0

  name                               = var.name
  target_type                        = "lambda"
  lambda_multi_value_headers_enabled = var.multi_value_headers
}

resource "aws_lambda_permission" "alb" {
  count = var.alb ? 1 : 0

  statement_id  = "AllowExecutionFromALB"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.function.function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.function[0].arn
}

resource "aws_lb_target_group_attachment" "function" {
  count = var.alb ? 1 : 0

  target_group_arn = aws_lb_target_group.function[0].arn
  target_id        = aws_lambda_function.function.arn

  depends_on = [aws_lambda_permission.alb]
}

resource "aws_lb_listener" "http" {
  count = var.alb ? 1 : 0

  load_balancer_arn = aws_lb.this[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.function[0].arn
  }
}
