"""
AWS S3 Bucket Configuration for Audio File Storage
"""

# S3 Bucket for Audio Uploads
resource "aws_s3_bucket" "uploads" {
  bucket = "${var.environment}-${var.app_name}-uploads-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.app_name}-uploads-${var.environment}"
  }
}

# Block Public Access
resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning
resource "aws_s3_bucket_versioning" "uploads" {
  count  = var.s3_enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  count  = var.s3_enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

# KMS Key for S3 Encryption
resource "aws_kms_key" "s3" {
  description             = "KMS key for S3 bucket encryption (${var.app_name}-${var.environment})"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "${var.app_name}-s3-key-${var.environment}"
  }
}

resource "aws_kms_alias" "s3" {
  name          = "alias/${var.app_name}-s3-${var.environment}"
  target_key_id = aws_kms_key.s3.key_id
}

# S3 Access Logging
resource "aws_s3_bucket" "logs" {
  count  = var.s3_enable_logging ? 1 : 0
  bucket = "${var.environment}-${var.app_name}-logs-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.app_name}-logs-${var.environment}"
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  count  = var.s3_enable_logging ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "uploads" {
  count          = var.s3_enable_logging ? 1 : 0
  bucket         = aws_s3_bucket.uploads.id
  target_bucket  = aws_s3_bucket.logs[0].id
  target_prefix  = "uploads/"
}

# CORS Configuration
resource "aws_s3_bucket_cors" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = [
      "http://localhost:5173",
      "http://localhost:3000",
      # Add production domain here when deployed
      # "https://yourdomain.com"
    ]
    expose_headers  = ["ETag", "x-amz-server-side-encryption"]
    max_age_seconds = 3000
  }
}

# Lifecycle Policy for Cost Optimization
resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    id     = "archive-old-files"
    status = "Enabled"

    # Transition to Glacier after specified days
    transition {
      days          = var.s3_lifecycle_transition_days
      storage_class = "GLACIER"
    }

    # Delete old versions after 30 days
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# IAM Policy for S3 Access
data "aws_iam_policy_document" "s3_access" {
  statement {
    sid    = "ListBucket"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketVersioning",
      "s3:GetBucketLocation",
    ]
    resources = [aws_s3_bucket.uploads.arn]

    condition {
      test     = "StringEquals"
      variable = "aws:username"
      values   = ["${var.app_name}-backend"]
    }
  }

  statement {
    sid    = "GetObjectAcl"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:GetObjectAcl",
    ]
    resources = ["${aws_s3_bucket.uploads.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:username"
      values   = ["${var.app_name}-backend"]
    }
  }

  statement {
    sid    = "PutObject"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
    ]
    resources = ["${aws_s3_bucket.uploads.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-server-side-encryption"
      values   = ["aws:kms"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:username"
      values   = ["${var.app_name}-backend"]
    }
  }

  statement {
    sid    = "DeleteObject"
    effect = "Allow"
    actions = [
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
    ]
    resources = ["${aws_s3_bucket.uploads.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:username"
      values   = ["${var.app_name}-backend"]
    }
  }

  statement {
    sid    = "KmsKeyUsage"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = [aws_kms_key.s3.arn]

    condition {
      test     = "StringEquals"
      variable = "aws:username"
      values   = ["${var.app_name}-backend"]
    }
  }
}

# IAM Policy for S3
resource "aws_iam_policy" "s3_access" {
  name        = "${var.app_name}-s3-access-policy-${var.environment}"
  description = "S3 access policy for ${var.app_name} backend"
  policy      = data.aws_iam_policy_document.s3_access.json

  tags = {
    Name = "${var.app_name}-s3-access-policy-${var.environment}"
  }
}

# Outputs
output "s3_bucket_name" {
  description = "S3 bucket name for audio uploads"
  value       = aws_s3_bucket.uploads.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.uploads.arn
}

output "s3_region" {
  description = "S3 bucket region"
  value       = aws_s3_bucket.uploads.region
}

output "s3_logs_bucket" {
  description = "S3 logs bucket name"
  value       = var.s3_enable_logging ? aws_s3_bucket.logs[0].id : null
}

output "kms_key_id" {
  description = "KMS key ID for S3 encryption"
  value       = aws_kms_key.s3.id
}

output "kms_key_arn" {
  description = "KMS key ARN for S3 encryption"
  value       = aws_kms_key.s3.arn
}

output "s3_access_policy_arn" {
  description = "S3 access policy ARN"
  value       = aws_iam_policy.s3_access.arn
}
