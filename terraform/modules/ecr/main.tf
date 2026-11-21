resource "aws_ecr_repository" "app" {
  name         = var.project
  force_delete = true # lets terraform destroy remove it with images inside

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = { Name = "${var.project}-ecr" }
}

