"""
AWS ElastiCache Redis Configuration for Caching and Task Queuing
"""

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.app_name}-redis-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.app_name}-redis-subnet-group-${var.environment}"
  }
}

# Security Group for ElastiCache
resource "aws_security_group" "redis" {
  name        = "${var.app_name}-redis-sg-${var.environment}"
  description = "Security group for Redis ElastiCache"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-redis-sg-${var.environment}"
  }
}

# ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.app_name}-redis-${var.environment}"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.environment == "production" ? "cache.t3.small" : "cache.t3.micro"
  num_cache_nodes      = var.environment == "production" ? 2 : 1
  parameter_group_name = aws_elasticache_parameter_group.main.name
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  # Backup Configuration
  snapshot_retention_limit = var.environment == "production" ? 5 : 0
  snapshot_window          = var.environment == "production" ? "03:00-05:00" : null

  # Maintenance
  maintenance_window = var.environment == "production" ? "sun:05:00-sun:07:00" : null
  notification_topic_arn = aws_sns_topic.alerts.arn

  # Automatic Failover
  automatic_failover_enabled = var.environment == "production" ? true : false

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = var.environment == "production" ? true : false
  auth_token                 = var.environment == "production" ? random_password.redis_auth_token[0].result : null

  tags = {
    Name = "${var.app_name}-redis-${var.environment}"
  }

  depends_on = [
    aws_elasticache_subnet_group.main,
    aws_security_group.redis
  ]
}

# Redis Auth Token for Production
resource "random_password" "redis_auth_token" {
  count   = var.environment == "production" ? 1 : 0
  length  = 32
  special = true
}

# ElastiCache Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  name        = "${var.app_name}-redis-params-${var.environment}"
  family      = "redis7"
  description = "Parameter group for Redis cluster"

  # Performance tuning
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  parameter {
    name  = "tcp-keepalive"
    value = "300"
  }

  tags = {
    Name = "${var.app_name}-redis-params-${var.environment}"
  }
}

# Redis Secrets in Secrets Manager
resource "aws_secretsmanager_secret" "redis" {
  name                    = "${var.app_name}/redis/connection-${var.environment}"
  description             = "Redis connection details for ${var.app_name} in ${var.environment}"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.app_name}-redis-secret-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    host       = aws_elasticache_cluster.redis.cache_nodes[0].address
    port       = aws_elasticache_cluster.redis.port
    auth_token = var.environment == "production" ? random_password.redis_auth_token[0].result : ""
    url        = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}"
  })
}

# CloudWatch Alarms for Redis
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${var.app_name}-redis-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "EngineCPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "Redis CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis.cluster_id
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${var.app_name}-redis-memory-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "90"
  alarm_description   = "Redis memory usage is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis.cluster_id
  }
}

# Outputs
output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_cluster.redis.port
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}"
}

output "redis_secret_arn" {
  description = "ARN of Redis connection secret"
  value       = aws_secretsmanager_secret.redis.arn
}
