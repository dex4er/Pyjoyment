# A Function URL of the public, without an authorization, with the invoke mode of the function, which needs the
# permissions of both actions
resource "aws_lambda_function_url" "function" {
  function_name      = aws_lambda_function.function.function_name
  authorization_type = "NONE"
  invoke_mode        = var.invoke_mode
}

resource "aws_lambda_permission" "url" {
  statement_id           = "AllowFunctionURL"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.function.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "url_invoke" {
  statement_id             = "AllowInvokeFromFunctionURL"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.function.function_name
  principal                = "*"
  invoked_via_function_url = true
}
