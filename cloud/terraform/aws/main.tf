# AWS Terraform 配置 for IntentOS

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "ECS Cluster Name"
  type        = string
  default     = "intentos-cluster"
}

variable "instance_type" {
  description = "EC2 Instance Type"
  type        = string
  default     = "t3.medium"
}

variable "min_capacity" {
  description = "Minimum Auto Scaling Capacity"
  type        = number
  default     = 2
}

variable "max_capacity" {
  description = "Maximum Auto Scaling Capacity"
  type        = number
  default     = 10
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "intentos-vpc"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "intentos-public-${count.index + 1}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "intentos-igw"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "intentos-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group
resource "aws_security_group" "intentos" {
  name        = "intentos-sg"
  description = "Security group for IntentOS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "intentos-sg"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = var.cluster_name
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "intentos" {
  family                   = "intentos"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 2048
  memory                   = 4096
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "intentos"
      image = "public.ecr.aws/intentos/intentos:v9.0"
      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "REDIS_URL"
          value = aws_elasticache_cluster.redis.cache_nodes[0].address
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        }
      ]
      secrets = [
        {
          name      = "OPENAI_API_KEY"
          valueFrom = aws_secretsmanager_secret.api_keys.arn + ":OPENAI_API_KEY::"
        },
        {
          name      = "ANTHROPIC_API_KEY"
          valueFrom = aws_secretsmanager_secret.api_keys.arn + ":ANTHROPIC_API_KEY::"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/intentos"
          awslogs-region        = var.region
          awslogs-stream-prefix = "intentos"
        }
      }
      healthCheck = {
        command = ["CMD-SHELL", "curl -f http://localhost:8080/v1/status || exit 1"]
        interval = 30
        timeout  = 10
        retries  = 3
      }
    }
  ])

  tags = {
    Name = "intentos-task"
  }
}

# ECS Service
resource "aws_ecs_service" "intentos" {
  name            = "intentos-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.intentos.arn
  desired_count   = var.min_capacity
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.public[*].id
    security_groups = [aws_security_group.intentos.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.intentos.arn
    container_name   = "intentos"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.intentos]
}

# Auto Scaling
resource "aws_appautoscaling_target" "intentos" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.intentos.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "intentos_cpu" {
  name               = "intentos-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.intentos.resource_id
  scalable_dimension = aws_appautoscaling_target.intentos.scalable_dimension
  service_namespace  = aws_appautoscaling_target.intentos.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "intentos-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.intentos.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "intentos-alb"
  }
}

resource "aws_lb_target_group" "intentos" {
  name     = "intentos-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/v1/status"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "intentos" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.intentos.arn
  }
}

# ElastiCache (Redis)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "intentos-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis6.x"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name

  tags = {
    Name = "intentos-redis"
  }
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "intentos-redis-sg"
  subnet_ids = aws_subnet.public[*].id
}

# Secrets Manager
resource "aws_secretsmanager_secret" "api_keys" {
  name = "intentos-api-keys"
}

# IAM Roles
resource "aws_iam_role" "ecs_execution" {
  name = "intentos-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "intentos-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "intentos" {
  name              = "/ecs/intentos"
  retention_in_days = 30
}

# Data Sources
data "aws_availability_zones" "available" {
  state = "available"
}

# Outputs
output "endpoint" {
  description = "IntentOS Endpoint"
  value       = "http://${aws_lb.main.dns_name}"
}

output "cluster_name" {
  description = "ECS Cluster Name"
  value       = aws_ecs_cluster.main.name
}

output "redis_endpoint" {
  description = "Redis Endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
}
