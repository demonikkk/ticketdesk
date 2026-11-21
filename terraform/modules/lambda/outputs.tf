output "function_name" {
  value = aws_lambda_function.processor.function_name
}

output "log_group" {
  value = aws_cloudwatch_log_group.lambda.name
}
