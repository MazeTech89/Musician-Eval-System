"""
AWS RDS PostgreSQL Database Configuration
"""

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.app_name}-db-subnet-group-${var.environment}"
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "main" {
  identifier             = "${var.app_name}-db-${var.environment}"
  engine                 = "postgres"
  engine_version         = "15.5"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = var.db_max_allocated_storage
  storage_type           = "gp3"
  storage_encrypted      = true
  skip_final_snapshot    = var.environment != "production"
  final_snapshot_identifier = "${var.app_name}-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmmss", timestamp())}"

  # Database Configuration
  db_name  = "musician_eval"
  username = var.db_username
  password = var.db_password
  port     = 5432

  # Network Configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Backup Configuration
  backup_retention_period = var.db_backup_retention_days
  backup_window           = "03:00-04:00"
  copy_tags_to_snapshot   = true
  delete_automated_backups = true

  # Maintenance Configuration
  maintenance_window             = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade     = true
  performance_insights_enabled   = true
  performance_insights_retention_period = 7

  # Enhanced Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql"]
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn

  # High Availability (for production)
  multi_az = var.environment == "production" ? true : false

  tags = {
    Name = "${var.app_name}-db-${var.environment}"
  }

  depends_on = [
    aws_db_subnet_group.main,
    aws_security_group.rds,
    aws_iam_role.rds_monitoring
  ]
}

# IAM Role for RDS Enhanced Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.app_name}-rds-monitoring-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.app_name}-rds-monitoring-role-${var.environment}"
  }
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# DB Parameter Group for Custom Configuration
resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "${var.app_name}-db-params-${var.environment}"

  # Performance and Connection Settings
  parameter {
    name  = "max_connections"
    value = "200"
  }

  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/32768}"
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/2048}"
  }

  # Log Configuration
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries slower than 1 second
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  # Application-specific settings
  parameter {
    name  = "timezone"
    value = "UTC"
  }

  tags = {
    Name = "${var.app_name}-db-params-${var.environment}"
  }
}

# Secrets Manager Secret for Database Credentials
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.app_name}/rds/password-${var.environment}"
  description             = "RDS password for ${var.app_name} in ${var.environment}"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.app_name}-db-password-secret-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    engine   = "postgres"
    host     = aws_db_instance.main.endpoint
    port     = 5432
    dbname   = "musician_eval"
  })
}

# RDS Event Subscription for Notifications
resource "aws_db_event_subscription" "main" {
  name             = "${var.app_name}-db-events-${var.environment}"
  sns_topic_arn    = aws_sns_topic.alerts.arn
  source_type      = "db-instance"
  source_ids       = [aws_db_instance.main.id]
  enabled          = true

  event_categories = [
    "availability",
    "backup",
    "failure",
    "maintenance",
  ]

  tags = {
    Name = "${var.app_name}-db-events-${var.environment}"
  }

  depends_on = [aws_sns_topic.alerts]
}

# SNS Topic for RDS Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.app_name}-alerts-${var.environment}"

  tags = {
    Name = "${var.app_name}-alerts-${var.environment}"
  }
}

# Outputs
output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "rds_address" {
  description = "RDS instance address"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "rds_database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "rds_resource_id" {
  description = "RDS resource ID"
  value       = aws_db_instance.main.resource_id
}

output "db_password_secret_arn" {
  description = "ARN of the Secrets Manager secret for database password"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "sns_topic_arn" {
  description = "SNS topic ARN for RDS alerts"
  value       = aws_sns_topic.alerts.arn
}
