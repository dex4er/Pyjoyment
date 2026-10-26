# The framework in a layer, the packages Pyjo and Pyjoyment of the checkout, with the static files of their
# resources, which Lambda unpacks in /opt: the names of the root that do not start with "P", which only they do, and
# the hidden ones are left out, but not the root itself, whose name is "."
data "archive_file" "framework" {
  type             = "zip"
  source_dir       = "${path.module}/../.."
  excludes         = ["[^.P]*", ".?*", "**/__pycache__"]
  output_path      = "${path.module}/.terraform/framework.zip"
  output_file_mode = "0644"
}

resource "aws_lambda_layer_version" "framework" {
  layer_name               = var.name
  filename                 = data.archive_file.framework.output_path
  source_code_hash         = data.archive_file.framework.output_base64sha256
  compatible_runtimes      = [var.runtime]
  compatible_architectures = ["arm64"]
}

# The function and the wrapper that runs its runtime client, executable both
data "archive_file" "function" {
  type             = "zip"
  output_path      = "${path.module}/.terraform/function.zip"
  output_file_mode = "0755"

  source {
    content  = file("${path.module}/app.py")
    filename = "app.py"
  }

  source {
    content  = file("${path.module}/wrapper.sh")
    filename = "wrapper.sh"
  }
}

resource "aws_iam_role" "function" {
  name = var.name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "function" {
  role       = aws_iam_role.function.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "function" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = 1
}

resource "aws_lambda_function" "function" {
  function_name    = var.name
  role             = aws_iam_role.function.arn
  runtime          = var.runtime
  architectures    = ["arm64"]
  handler          = "app.handler"
  filename         = data.archive_file.function.output_path
  source_code_hash = data.archive_file.function.output_base64sha256
  layers           = [aws_lambda_layer_version.framework.arn]
  memory_size      = 128
  timeout          = 10

  environment {
    variables = {
      # The runtime client of Pyjo.Server.Lambda in the place of the one of the runtime, which does not stream
      AWS_LAMBDA_EXEC_WRAPPER = "/var/task/wrapper.sh"

      # The invoke mode of the Function URL, which the function does not learn from its invocations
      PYJO_LAMBDA_INVOKE_MODE = "RESPONSE_STREAM"

      PYJO_MODE = "development"

      # The directory of the layer, which the runtime does not put in the path of Python, as it does /opt/python
      PYTHONPATH = "/opt"
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.function.name
  }

  depends_on = [aws_iam_role_policy_attachment.function]
}
