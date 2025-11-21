# Terraform Infrastructure as Code for ETL System
# This file represents the infrastructure configuration that would be indexed

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "etl_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "etl-vpc"
  }
}

# Public Subnets for Load Balancers
resource "aws_subnet" "public_1" {
  vpc_id            = aws_vpc.etl_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "etl-public-subnet-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id            = aws_vpc.etl_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "etl-public-subnet-2"
  }
}

# Private Subnets for ECS Tasks
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.etl_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "etl-private-subnet-1"
  }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.etl_vpc.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "etl-private-subnet-2"
  }
}

# RDS PostgreSQL Database
resource "aws_db_instance" "etl_postgres" {
  identifier     = "etl-postgres"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  max_allocated_storage = 200
  storage_encrypted     = true

  db_name  = "etldb"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.etl.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "etl-postgres-final-snapshot"

  tags = {
    Name = "etl-postgres-db"
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "etl" {
  name       = "etl-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "etl-db-subnet-group"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "etl_redis" {
  name       = "etl-redis-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

resource "aws_elasticache_cluster" "etl_redis" {
  cluster_id           = "etl-redis"
  engine               = "redis"
  engine_version        = "7.0"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.etl_redis.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = {
    Name = "etl-redis-cache"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "raw_documents" {
  bucket = "etl-raw-documents-${var.environment}"

  tags = {
    Name = "etl-raw-documents"
  }
}

resource "aws_s3_bucket" "processed_artifacts" {
  bucket = "etl-processed-artifacts-${var.environment}"

  tags = {
    Name = "etl-processed-artifacts"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "etl" {
  name = "etl-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "etl-ecs-cluster"
  }
}

# Application Load Balancer
resource "aws_lb" "etl_alb" {
  name               = "etl-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  enable_deletion_protection = false

  tags = {
    Name = "etl-application-load-balancer"
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "etl-alb-sg"
  description = "Security group for ETL Application Load Balancer"
  vpc_id      = aws_vpc.etl_vpc.id

  ingress {
    from_port   = 80
    to_port      = 80
    protocol     = "tcp"
    cidr_blocks  = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port      = 443
    protocol     = "tcp"
    cidr_blocks  = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port      = 0
    protocol     = "-1"
    cidr_blocks  = ["0.0.0.0/0"]
  }

  tags = {
    Name = "etl-alb-security-group"
  }
}

resource "aws_security_group" "ecs" {
  name        = "etl-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.etl_vpc.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port      = 0
    protocol     = "-1"
    cidr_blocks  = ["0.0.0.0/0"]
  }

  tags = {
    Name = "etl-ecs-security-group"
  }
}

resource "aws_security_group" "rds" {
  name        = "etl-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.etl_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port      = 0
    protocol     = "-1"
    cidr_blocks  = ["0.0.0.0/0"]
  }

  tags = {
    Name = "etl-rds-security-group"
  }
}

resource "aws_security_group" "redis" {
  name        = "etl-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.etl_vpc.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port      = 0
    protocol     = "-1"
    cidr_blocks  = ["0.0.0.0/0"]
  }

  tags = {
    Name = "etl-redis-security-group"
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

