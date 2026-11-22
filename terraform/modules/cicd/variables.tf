variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "github_repo" {
  type        = string
  description = "owner/repo that may deploy"
}

variable "ecr_repository_arn" {
  type = string
}

variable "instance_id" {
  type = string
}
