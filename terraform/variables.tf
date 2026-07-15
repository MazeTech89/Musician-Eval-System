"""
AWS Terraform Variables
"""

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "musician-eval"
}

variable "project_tag" {
  description = "Project tag for resource identification"
  type        = string
  default     = "musician-eval-system"
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS autoscaling in GB"
  type        = number
  default     = 100
}

variable "db_backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 7
}

variable "db_username" {
  description = "Database master username"
  type        = string
  sensitive   = true
  default     = "musicinadmin"
}

variable "db_password" {
  description = "Database master password (minimum 8 characters)"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters."
  }
}

# ECS Configuration
variable "container_port" {
  description = "Port exposed by container"
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "CPU units for ECS task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Memory for ECS task in MB (512, 1024, 2048, 3072, 4096, 5120, 6144, 7168, 8192)"
  type        = number
  default     = 512
}

variable "desired_task_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "min_task_count" {
  description = "Minimum number of ECS tasks for autoscaling"
  type        = number
  default     = 1
}

variable "max_task_count" {
  description = "Maximum number of ECS tasks for autoscaling"
  type        = number
  default     = 3
}

# S3 Configuration
variable "s3_enable_versioning" {
  description = "Enable versioning on S3 bucket"
  type        = bool
  default     = true
}

variable "s3_enable_encryption" {
  description = "Enable server-side encryption on S3 bucket"
  type        = bool
  default     = true
}

variable "s3_enable_logging" {
  description = "Enable S3 access logging"
  type        = bool
  default     = true
}

variable "s3_lifecycle_transition_days" {
  description = "Days before transitioning objects to Glacier"
  type        = number
  default     = 90
}

# Backend Configuration
variable "backend_docker_image" {
  description = "Docker image for backend (ECR URL)"
  type        = string
}

variable "frontend_docker_image" {
  description = "Docker image for frontend (ECR URL)"
  type        = string
}

variable "secret_key" {
  description = "Application secret key for JWT"
  type        = string
  sensitive   = true
}

variable "jwt_algorithm" {
  description = "JWT signing algorithm"
  type        = string
  default     = "HS256"
}

variable "access_token_expire_minutes" {
  description = "JWT access token expiry in minutes"
  type        = number
  default     = 30
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnet internet access"
  type        = bool
  default     = true
}

variable "enable_vpn_endpoint" {
  description = "Enable VPC endpoint for private S3 access"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "musician-eval-system"
    ManagedBy   = "terraform"
    CreatedDate = "2026-07-08"
  }
}
