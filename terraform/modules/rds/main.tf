locals {
  db_name  = "ticketdesk"
  username = "ticketdesk"
}

# Alphanumeric only, so the password is safe inside a URL.
resource "random_password" "db" {
  length  = 24
  special = false
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.project}-db-subnets"
  subnet_ids = var.private_subnet_ids
  tags       = { Name = "${var.project}-db-subnets" }
}

resource "aws_db_instance" "this" {
  identifier        = "${var.project}-db"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = local.db_name
  username = local.username
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [var.db_sg_id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period = 1
  skip_final_snapshot     = true
  deletion_protection     = false
  apply_immediately       = true

  tags = { Name = "${var.project}-db" }
}

# Credentials live only in Secrets Manager (the EC2 role will read it).
resource "aws_secretsmanager_secret" "db" {
  name                    = "${var.project}/db"
  description             = "TicketDesk database connection"
  recovery_window_in_days = 0 # delete immediately on destroy so re-apply works
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username     = local.username
    password     = random_password.db.result
    host         = aws_db_instance.this.address
    port         = 5432
    dbname       = local.db_name
    database_url = "postgresql+psycopg2://${local.username}:${random_password.db.result}@${aws_db_instance.this.address}:5432/${local.db_name}"
  })
}
