module "network" {
  source   = "./modules/network"
  project  = var.project
  vpc_cidr = var.vpc_cidr
}
module "rds" {
  source             = "./modules/rds"
  project            = var.project
  private_subnet_ids = module.network.private_subnet_ids
  db_sg_id           = module.network.db_sg_id
}
module "s3" {
  source  = "./modules/s3"
  project = var.project
}

module "ecr" {
  source  = "./modules/ecr"
  project = var.project
}

module "ec2" {
  source             = "./modules/ec2"
  project            = var.project
  region             = var.region
  subnet_id          = module.network.public_subnet_ids[0]
  app_sg_id          = module.network.app_sg_id
  db_secret_arn      = module.rds.secret_arn
  bucket_name        = module.s3.bucket_name
  bucket_arn         = module.s3.bucket_arn
  ecr_repository_url = module.ecr.repository_url
  ecr_repository_arn = module.ecr.repository_arn
}
module "lambda" {
  source      = "./modules/lambda"
  project     = var.project
  bucket_name = module.s3.bucket_name
  bucket_arn  = module.s3.bucket_arn
}
module "cicd" {
  source             = "./modules/cicd"
  project            = var.project
  region             = var.region
  github_repo        = var.github_repo
  ecr_repository_arn = module.ecr.repository_arn
  instance_id        = module.ec2.instance_id
}