"""
AWS Secrets Manager Configuration for Application Secrets
"""

# Application Secret Key
resource "aws_secretsmanager_secret" "app_secret" {
  name                    = "${var.app_name}/app/secret-key-${var.environment}"
  description             = "Application secret key for ${var.app_name} in ${var.environment}"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.app_name}-app-secret-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "app_secret" {
  secret_id = aws_secretsmanager_secret.app_secret.id
  secret_string = jsonencode({
    secret_key = var.secret_key
  })
}

# IAM Policy for ECS to access Secrets Manager
data "aws_iam_policy_document" "ecs_secrets_access" {
  statement {
    sid    = "GetSecret"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = [
      aws_secretsmanager_secret.app_secret.arn,
      aws_secretsmanager_secret.db_password.arn,
      aws_secretsmanager_secret.redis.arn,
    ]
  }

  statement {
    sid    = "DecryptSecret"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
    ]
    resources = [aws_kms_key.s3.arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values = [
        "secretsmanager.${var.aws_region}.amazonaws.com",
        "s3.${var.aws_region}.amazonaws.com",
      ]
    }
  }
}

# Attach policy to ECS task execution role
resource "aws_iam_role_policy" "ecs_secrets_access" {
  name   = "${var.app_name}-ecs-secrets-access-${var.environment}"
  role   = aws_iam_role.ecs_task_execution_role.id
  policy = data.aws_iam_policy_document.ecs_secrets_access.json
}

# Attach policy to ECS task role (for runtime S3 access)
resource "aws_iam_role_policy" "ecs_task_s3_access" {
  name   = "${var.app_name}-ecs-task-s3-access-${var.environment}"
  role   = aws_iam_role.ecs_task_role.id
  policy = data.aws_iam_policy_document.s3_access.json
}

# Outputs
output "app_secret_arn" {
  description = "ARN of application secret"
  value       = aws_secretsmanager_secret.app_secret.arn
}
