output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_ids" {
  value = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.network.private_subnet_ids
}

output "app_security_group_id" {
  value = module.network.app_sg_id
}

output "db_security_group_id" {
  value = module.network.db_sg_id
}
output "db_endpoint" {
  value = module.rds.endpoint
}
output "db_secret_arn" {
  value = module.rds.secret_arn
}
output "app_url" {
  value = "http://${module.ec2.public_ip}"
}

output "instance_id" {
  value = module.ec2.instance_id
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "bucket_name" {
  value = module.s3.bucket_name
}

output "log_group" {
  value = module.ec2.log_group
}
output "lambda_function" {
  value = module.lambda.function_name
}

output "lambda_log_group" {
  value = module.lambda.log_group
}