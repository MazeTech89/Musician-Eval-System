# AWS Terraform Deployment Guide

This directory contains Terraform configuration for deploying the Musician Evaluation System to AWS.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS VPC (10.0.0.0/16)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Public Subnets (2 AZs)                        │  │
│  │    Internet Gateway ← Application Load Balancer          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Private Subnets (2 AZs)                       │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │   ECS Fargate Cluster                          │    │  │
│  │  │  ┌─────────────────┐  ┌──────────────────┐   │    │  │
│  │  │  │ Backend Task    │  │ Frontend Task    │   │    │  │
│  │  │  │ (FastAPI)       │  │ (React)          │   │    │  │
│  │  │  └─────────────────┘  └──────────────────┘   │    │  │
│  │  │                                               │    │  │
│  │  │  Auto-scaling: 1-3 tasks                     │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │   RDS PostgreSQL (Multi-AZ for Prod)           │    │  │
│  │  │   - Automated backups (7 days)                 │    │  │
│  │  │   - Enhanced monitoring                        │    │  │
│  │  │   - Read replicas (optional)                   │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │   ElastiCache Redis                            │    │  │
│  │  │   - Session storage & caching                  │    │  │
│  │  │   - Task queuing (Celery)                      │    │  │
│  │  │   - Automatic failover (Prod)                  │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            S3 Bucket (Audio Uploads)                     │  │
│  │  - KMS encryption at rest                              │  │
│  │  - Versioning enabled                                  │  │
│  │  - Lifecycle policies (archive → Glacier)              │  │
│  │  - Access logging                                       │  │
│  │  - CORS configured                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Secrets Manager & IAM                        │  │
│  │  - Database credentials                                │  │
│  │  - JWT secret key                                       │  │
│  │  - Redis auth token                                     │  │
│  │  - KMS encryption                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            CloudWatch & Monitoring                      │  │
│  │  - ECS container logs                                   │  │
│  │  - RDS performance insights                            │  │
│  │  - SNS alerts for critical events                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.0 installed
3. **AWS CLI** configured with credentials:
   ```bash
   aws configure
   ```
4. **Docker** images pushed to ECR:
   - Backend image URL
   - Frontend image URL

## File Structure

```
terraform/
├── main.tf              # VPC, subnets, security groups, IAM roles
├── rds.tf               # RDS PostgreSQL database
├── s3.tf                # S3 bucket for audio uploads
├── ecs.tf               # ECS Fargate containers and ALB
├── redis.tf             # ElastiCache Redis cluster
├── secrets.tf           # Secrets Manager & IAM policies
├── variables.tf         # Input variables
└── terraform.tfvars     # Environment-specific values (not in git)
```

## Setup Instructions

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Create `terraform.tfvars`

Create a file `terraform/terraform.tfvars` with your environment-specific values:

```hcl
# AWS Configuration
aws_region  = "us-east-1"
environment = "development"  # or "staging", "production"
app_name    = "musician-eval"

# Database
db_username = "musicinadmin"
db_password = "SecurePassword123!"  # Change this!

# Application
secret_key               = "your-jwt-secret-key-here"
backend_docker_image     = "your-ecr-account.dkr.ecr.us-east-1.amazonaws.com/musician-eval-backend:latest"
frontend_docker_image    = "your-ecr-account.dkr.ecr.us-east-1.amazonaws.com/musician-eval-frontend:latest"

# Capacity
desired_task_count = 2
min_task_count     = 1
max_task_count     = 5

# Optional
enable_nat_gateway = true
log_retention_days = 7
```

### 3. Plan Infrastructure

```bash
terraform plan -out=tfplan
```

Review the plan to ensure all resources are correct.

### 4. Apply Infrastructure

```bash
terraform apply tfplan
```

This will create:
- VPC with public/private subnets across 2 AZs
- RDS PostgreSQL database
- ECS Fargate cluster with auto-scaling
- S3 bucket with encryption and versioning
- ElastiCache Redis cluster
- Security groups and IAM roles
- CloudWatch monitoring

### 5. Get Outputs

```bash
terraform output
```

Key outputs:
- `alb_dns_name` - Application endpoint (http://your-alb-dns.amazonaws.com)
- `rds_endpoint` - Database endpoint
- `s3_bucket_name` - S3 bucket for uploads
- `redis_endpoint` - Redis cluster endpoint

## Environment-Specific Configurations

### Development
- Single ECS task
- db.t3.micro RDS instance
- cache.t3.micro Redis node
- No multi-AZ
- 7-day backup retention

### Staging
- 2 ECS tasks with auto-scaling
- db.t3.small RDS instance
- cache.t3.small Redis node (single node)
- Optional multi-AZ
- 7-day backup retention

### Production
- 2-5 ECS tasks with CPU/Memory auto-scaling
- db.t3.medium+ RDS instance
- Multi-AZ RDS enabled
- cache.t3.small Redis with automatic failover
- 5-30 day backup retention
- Enhanced monitoring enabled

## Deployment Checklist

- [ ] AWS account configured with `aws configure`
- [ ] Docker images built and pushed to ECR
- [ ] `terraform.tfvars` created with production values
- [ ] Terraform plan reviewed for correctness
- [ ] Database password is strong (minimum 8 characters)
- [ ] JWT secret key is securely generated
- [ ] S3 bucket name is globally unique
- [ ] Monitoring and alerts configured
- [ ] Backup strategy documented
- [ ] Disaster recovery plan created

## Post-Deployment Steps

### 1. Initialize Database

```bash
# Get database endpoint from terraform output
DB_HOST=$(terraform output rds_address)
DB_USER="musicinadmin"
DB_NAME="musician_eval"

# Connect and initialize schema
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < init_db.sql
```

### 2. Configure Domain (Optional)

Update S3 CORS origins and ALB listener with your domain:

```bash
terraform apply -var="cors_origins=[\"https://yourdomain.com\"]"
```

### 3. Enable HTTPS

Add ACM certificate and update ALB listener:

```bash
# Create certificate in ACM first, then update variables
terraform apply -var="alb_certificate_arn=arn:aws:acm:..."
```

### 4. Configure CloudWatch Alerts

Email subscription for SNS topic:
```bash
aws sns subscribe \
  --topic-arn $(terraform output sns_topic_arn) \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## Monitoring & Maintenance

### CloudWatch Dashboards
Dashboard automatically created for:
- ECS task metrics (CPU, memory, network)
- RDS database metrics (connections, disk, latency)
- S3 bucket metrics (size, requests)
- Redis cluster metrics (CPU, memory, connections)

### Automated Backups
- **RDS**: Daily snapshots, 7-day retention
- **S3**: Versioning enabled (30-day retention for old versions)
- **Redis**: Optional snapshots (configure in redis.tf)

### Scaling Policies
ECS tasks auto-scale based on:
- CPU utilization > 70% → Scale up
- Memory utilization > 80% → Scale up
- Custom scaling policies for specific patterns

## Troubleshooting

### Database Connection Issues
```bash
# Check RDS security group
aws ec2 describe-security-groups \
  --filters Name=group-name,Values="*rds*" \
  --query 'SecurityGroups[0].IpPermissions'

# Verify from ECS container
docker exec <container> psql -h <rds-endpoint> -U musicinadmin -d musician_eval -c "SELECT version();"
```

### ECS Task Failures
```bash
# View task logs
aws logs tail /ecs/musician-eval-backend-<environment> --follow

# Describe failing task
aws ecs describe-tasks \
  --cluster musician-eval-cluster-<environment> \
  --tasks <task-arn>
```

### S3 Upload Issues
```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket <bucket-name>

# Test upload
aws s3 cp test.txt s3://<bucket-name>/test.txt
```

## Cleanup

To destroy all AWS resources:

```bash
terraform destroy
```

**Warning**: This will delete:
- Database (final snapshot created)
- S3 bucket (with all files)
- ECS cluster
- VPC and all associated resources

For safety, perform a final backup:
```bash
aws rds create-db-snapshot \
  --db-instance-identifier musician-eval-db-<environment> \
  --db-snapshot-identifier final-backup-$(date +%s)
```

## Cost Optimization

### Recommendations
1. Use Spot instances for non-production environments
2. Right-size RDS instance type based on workload
3. Enable S3 Intelligent-Tiering for automatic cost optimization
4. Use CloudWatch alarms for budget notifications
5. Consider Reserved Instances for production databases

### Estimated Monthly Costs (Development)
- RDS (db.t3.micro): ~$12/month
- ECS (t3.small): ~$13/month
- S3: ~$1/month (minimal storage)
- Redis (cache.t3.micro): ~$10/month
- **Total**: ~$36/month

## Support & Documentation

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS VPC Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-best-practices.html)
- [ECS Fargate Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Fargate-on-ECS.html)
- [RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)

## Next Steps

1. Build and push Docker images to ECR
2. Update Terraform variables with your ECR image URIs
3. Run `terraform plan` and review
4. Deploy with `terraform apply`
5. Configure DNS and SSL certificates
6. Set up monitoring alerts
7. Test end-to-end deployment
