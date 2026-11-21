data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "attachments" {
  bucket        = "${var.project}-attachments-${data.aws_caller_identity.current.account_id}"
  force_destroy = true # lets terraform destroy remove it even with files inside
  tags          = { Name = "${var.project}-attachments" }
}

resource "aws_s3_bucket_public_access_block" "attachments" {
  bucket                  = aws_s3_bucket.attachments.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
