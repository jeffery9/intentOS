# IntentOS 云上 Self-Bootstrap 完整指南

## 概述

IntentOS 的 **云上 Self-Bootstrap** 不仅仅是启动服务，更重要的是：

1. **自动开通云资源** - 在有凭证的情况下自动创建所需资源
2. **引导人类授权** - 在需要时引导人类完成开通/授权
3. **自我配置** - 根据环境自动调整配置
4. **持续演化** - 根据使用情况优化资源

---

## Self-Bootstrap 流程

```
┌─────────────────────────────────────────────────────────────┐
│  阶段 1: 资源定义                                            │
│  - 定义所需云资源（VPC、ECS、Redis 等）                       │
│  - 指定资源依赖关系                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 2: 资源检查                                            │
│  - 检查资源是否已存在                                        │
│  - 检查凭证是否有效                                          │
│  - 识别需要人类介入的资源                                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 3: 创建计划                                            │
│  - 生成资源创建计划                                          │
│  - 估算成本                                                  │
│  - 识别人类介入点                                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 4: 执行 Bootstrap                                      │
│  ├─ 自动模式：有凭证 → 自动创建资源                          │
│  └─ 交互模式：无凭证 → 引导人类开通/授权                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 5: 验证与配置                                          │
│  - 验证资源创建成功                                          │
│  - 自动配置应用连接                                          │
│  - 启动监控和备份                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 使用方式

### 模式 1: 全自动（有凭证）

```bash
# 配置凭证
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# 自动部署（无需交互）
./cloud/bootstrap.sh --provider aws --region us-east-1 --auto
```

**系统行为**:
1. ✅ 自动检查凭证有效性
2. ✅ 自动创建 VPC、ECS、ElastiCache
3. ✅ 自动配置负载均衡
4. ✅ 自动部署应用
5. ✅ 自动启动监控

### 模式 2: 交互式（无凭证）

```bash
# 不配置凭证，直接运行
./cloud/bootstrap.sh --provider aws --region us-east-1
```

**系统行为**:
1. ⚠️ 检测到无凭证
2. 📖 显示凭证配置指南
3. 🎯 提供多种开通方式（控制台/CLI/Terraform）
4. ⏸️ 等待人类完成开通
5. ✅ 验证资源创建成功

### 模式 3: 混合模式

```bash
# 部分资源自动，部分需要人类
./cloud/bootstrap.sh --provider aws --region us-east-1
```

**系统行为**:
1. ✅ 自动创建简单资源（VPC、安全组）
2. ⚠️ 需要人类授权复杂资源（ECS、Redis）
3. 📖 显示每个资源的创建指南
4. 🔍 验证人类创建的资源

---

## 资源开通方式

### 方式 1: 自动开通（推荐）

**前提**: 有效的云凭证

```bash
# AWS
export AWS_ACCESS_KEY_ID="xxx"
export AWS_SECRET_ACCESS_KEY="xxx"
./cloud/bootstrap.sh --provider aws

# GCP
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
./cloud/bootstrap.sh --provider gcp

# Azure
export ARM_CLIENT_ID="xxx"
export ARM_CLIENT_SECRET="xxx"
./cloud/bootstrap.sh --provider azure
```

### 方式 2: 控制台引导

系统会显示类似输出：

```
============================================================
⚠️  需要人类介入：intentos-vpc (vpc)
============================================================

📋 资源信息:
  名称：intentos-vpc
  类型：vpc
  提供商：aws

📖 创建方式:

  【方式 1】AWS 控制台:
  1. 访问：https://console.aws.amazon.com/vpc/home?#VPCs:
  2. 点击"创建 Vpc"
  3. 配置参数:
     - CIDR: 10.0.0.0/16
     - 名称：intentos-vpc
  4. 点击"创建"

  【方式 2】AWS CLI:
  运行以下命令:
  ```bash
  aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=intentos-vpc}]"
  ```

  【方式 3】Terraform:
  添加以下配置到 main.tf:
  ```hcl
  resource "aws_vpc" "intentos-vpc" {
    cidr_block = "10.0.0.0/16"
    tags = {
      Name = "intentos-vpc"
    }
  }
  ```

============================================================

请选择操作:
  [1] 我已创建资源
  [2] 显示指南
  [3] 跳过此资源
  选择：
```

### 方式 3: CLI 命令引导

系统生成可直接运行的 CLI 命令：

```bash
# VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=intentos-vpc}]"

# ECS Cluster
aws ecs create-cluster --cluster-name intentos-ecs-cluster

# ElastiCache (Redis)
aws elasticache create-cache-cluster \
  --cache-cluster-id intentos-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1

# Secrets Manager
aws secretsmanager create-secret --name intentos-secrets
```

### 方式 4: Terraform 引导

系统生成 Terraform 配置：

```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "intentos-vpc" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "intentos-vpc"
    managed-by = "intentos"
  }
}

resource "aws_ecs_cluster" "intentos-ecs-cluster" {
  name = "intentos-ecs-cluster"
  tags = {
    managed-by = "intentos"
  }
}

resource "aws_elasticache_cluster" "intentos-redis" {
  cluster_id           = "intentos-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  tags = {
    managed-by = "intentos"
  }
}
```

运行：
```bash
terraform init
terraform plan
terraform apply
```

---

## 资源类型与支持

### AWS 资源

| 资源类型 | 自动开通 | 引导方式 | 说明 |
|---------|---------|---------|------|
| **VPC** | ✅ | 控制台/CLI/Terraform | 虚拟私有云 |
| **ECS Cluster** | ✅ | 控制台/CLI/Terraform | 容器服务集群 |
| **ElastiCache** | ✅ | 控制台/CLI/Terraform | Redis 缓存 |
| **ALB** | ✅ | 控制台/CLI/Terraform | 应用负载均衡 |
| **Secrets Manager** | ✅ | 控制台/CLI/Terraform | 密钥管理 |
| **IAM Role** | ⚠️ | 控制台/CLI | 需要人工审核 |
| **RDS** | ⚠️ | 控制台/CLI | 需要人工审核 |

### GCP 资源

| 资源类型 | 自动开通 | 引导方式 | 说明 |
|---------|---------|---------|------|
| **VPC Network** | ✅ | 控制台/CLI/Terraform | 虚拟私有云 |
| **Cloud Run** | ✅ | 控制台/CLI/Terraform | 无服务器容器 |
| **Memorystore** | ✅ | 控制台/CLI/Terraform | Redis 缓存 |
| **Secret Manager** | ✅ | 控制台/CLI/Terraform | 密钥管理 |

### Azure 资源

| 资源类型 | 自动开通 | 引导方式 | 说明 |
|---------|---------|---------|------|
| **VNet** | ✅ | 控制台/CLI/Terraform | 虚拟网络 |
| **AKS** | ✅ | 控制台/CLI/Terraform | Kubernetes 服务 |
| **Cache for Redis** | ✅ | 控制台/CLI/Terraform | Redis 缓存 |
| **Key Vault** | ⚠️ | 控制台/CLI | 需要人工审核 |

### Docker 资源

| 资源类型 | 自动开通 | 引导方式 | 说明 |
|---------|---------|---------|------|
| **Docker Network** | ✅ | 自动 | Docker 网络 |
| **Redis Container** | ✅ | 自动 | Redis 容器 |
| **Volume** | ✅ | 自动 | 数据卷 |

---

## 安全与权限

### 最小权限原则

自动开通需要的最小权限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:CreateTags",
        "ecs:CreateCluster",
        "elasticache:CreateCacheCluster",
        "secretsmanager:CreateSecret"
      ],
      "Resource": "*"
    }
  ]
}
```

### 人类审核点

以下操作需要人类审核：

1. **IAM 角色创建** - 涉及权限策略
2. **生产数据库** - 涉及数据安全
3. **跨区域复制** - 涉及成本
4. **公网访问配置** - 涉及网络安全

---

## 成本估算

### 自动显示成本

```
📊 Bootstrap 计划:

资源状态:
  ✓ intentos-vpc (vpc): active
  ○ intentos-ecs-cluster (ecs_cluster): not_exists → 将自动创建
  ○ intentos-redis (elasticache): not_exists → 将自动创建
  ○ intentos-alb (alb): not_exists → 将自动创建

💰 预估成本:
  月度：$38.00
  年度：$456.00
  
  明细:
  - VPC: $0.00 (免费)
  - ECS Cluster: $0.00 (免费)
  - ElastiCache: $15.00/月 (cache.t3.micro)
  - ALB: $22.00/月
  - Secrets Manager: $1.00/月

是否继续执行？(y/n): 
```

### 成本优化建议

系统会根据使用情况提供优化建议：

```
💡 成本优化建议:

1. 使用 Spot 实例可节省 70%
   当前：$100/月 → 优化后：$30/月

2. 购买预留实例可节省 40%
   当前：$100/月 → 优化后：$60/月

3. 非高峰期缩容到 1 实例
   当前：$100/月 → 优化后：$50/月

是否应用优化？(y/n): 
```

---

## 故障排查

### 凭证问题

```bash
# 检查凭证
aws sts get-caller-identity

# 如果失败，重新配置
aws configure
```

### 权限问题

```bash
# 检查权限
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:user/USERNAME \
  --action-names ec2:CreateVpc
```

### 资源配额

```bash
# 检查配额
aws service-quotas list-service-quotas --service-code ec2

# 申请提升配额
# 访问：https://console.aws.amazon.com/servicequotas/
```

---

## 最佳实践

### 1. 使用环境变量管理凭证

```bash
# ~/.bashrc 或 ~/.zshrc
export AWS_PROFILE=intentos
export AWS_REGION=us-east-1
```

### 2. 使用 AWS Secrets Manager

```bash
# 存储敏感信息
aws secretsmanager create-secret \
  --name intentos/api-keys \
  --secret-string '{"openai":"sk-xxx","anthropic":"sk-ant-xxx"}'
```

### 3. 启用 CloudTrail 审计

```bash
# 记录所有 API 调用
aws cloudtrail create-trail \
  --name intentos-trail \
  --s3-bucket-name intentos-audit-logs
```

### 4. 设置预算告警

```bash
# 创建预算
aws budgets create-budget \
  --account-id ACCOUNT_ID \
  --budget file://budget.json \
  --notifications-with-subscriptions file://notifications.json
```

---

## 总结

IntentOS 云上 Self-Bootstrap 提供三种模式：

| 模式 | 凭证 | 人类介入 | 适用场景 |
|------|------|---------|---------|
| **全自动** | ✅ 有效 | ❌ 无 | CI/CD、自动化部署 |
| **交互式** | ❌ 无效 | ✅ 引导 | 首次部署、学习 |
| **混合** | ⚠️ 部分 | ✅ 部分 | 生产环境、审核需求 |

**核心理念**: 
- 能自动的自动
- 需要人类的引导人类
- 所有操作可审计、可追溯

**IntentOS 在云上真正自我演化！** 🚀☁️✨
