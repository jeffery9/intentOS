# IntentOS 云基础设施架构

> IntentOS 运行在云计算基础设施之上，利用 Cloud 的弹性计算、分布式存储和网络能力，实现意图的分布式执行和记忆的持久化同步。

---

## 1. 概述

### 1.1 云基础设施分层

```
┌─────────────────────────────────────────────────────────────┐
│  IntentOS Application Layer                                 │
│  • CRM App / Sales App / BI App                            │
│  • 意图包 + 用户交互                                        │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  IntentOS Runtime Layer                                     │
│  • 意图编译器 / 记忆管理 / DAG 执行                          │
│  • 运行在 Kubernetes / ECS 上                               │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  Cloud Infrastructure Layer                                 │
│  ├─ 计算：Kubernetes / ECS / Lambda                        │
│  ├─ 存储：Redis / S3 / EBS                                 │
│  ├─ 网络：VPC / Load Balancer / API Gateway                │
│  └─ 监控：CloudWatch / Prometheus / Grafana                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 云服务映射

| IntentOS 组件 | 云服务 (AWS) | 云服务 (Azure) | 云服务 (GCP) |
|--------------|-------------|---------------|-------------|
| **意图执行** | ECS / Lambda | Container Apps | Cloud Run |
| **记忆存储** | ElastiCache (Redis) | Azure Cache | Memorystore |
| **长期记忆** | S3 | Blob Storage | Cloud Storage |
| **DAG 执行** | Step Functions | Logic Apps | Workflows |
| **API 网关** | API Gateway | API Management | API Gateway |
| **监控** | CloudWatch | Monitor | Operations |

---

## 2. 计算基础设施

### 2.1 容器化部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intentos-runtime
spec:
  replicas: 3
  selector:
    matchLabels:
      app: intentos
  template:
    metadata:
      labels:
        app: intentos
    spec:
      containers:
      - name: intentos
        image: intentos/runtime:latest
        env:
        - name: REDIS_HOST
          value: "redis-cluster.xxx.cache.amazonaws.com"
        - name: S3_BUCKET
          value: "intentos-memory-bucket"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: intentos-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### 2.2 无服务器部署

```yaml
# serverless.yaml
service: intentos-api

provider:
  name: aws
  runtime: python3.10
  region: us-east-1
  environment:
    REDIS_HOST: ${ssm:/intentos/redis/host}
    S3_BUCKET: intentos-memory-bucket

functions:
  compile:
    handler: intentos.compiler_v2.compile
    events:
      - http:
          path: /compile
          method: post
    memorySize: 1024
    timeout: 30
  
  execute:
    handler: intentos.engine.execute
    events:
      - http:
          path: /execute
          method: post
    memorySize: 2048
    timeout: 300
  
  memory:
    handler: intentos.distributed_memory.handler
    events:
      - http:
          path: /memory/{action}
          method: post
    memorySize: 512
    timeout: 30
```

### 2.3 自动扩缩容

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: intentos-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: intentos-runtime
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

---

## 3. 存储基础设施

### 3.1 Redis 集群（短期记忆）

```python
# redis_config.py
import redis.asyncio as redis
from redis.cluster import RedisCluster

class RedisClusterConfig:
    """Redis 集群配置"""
    
    # AWS ElastiCache
    AWS_CONFIG = {
        "host": "redis-cluster.xxx.cache.amazonaws.com",
        "port": 6379,
        "password": os.environ.get("REDIS_PASSWORD"),
        "ssl": True,
        "decode_responses": False,
    }
    
    # Azure Cache
    AZURE_CONFIG = {
        "host": "intentos.redis.cache.windows.net",
        "port": 6380,
        "password": os.environ.get("REDIS_PASSWORD"),
        "ssl": True,
        "decode_responses": False,
    }
    
    @classmethod
    async def create_client(cls, provider: str = "aws"):
        """创建 Redis 客户端"""
        if provider == "aws":
            config = cls.AWS_CONFIG
        elif provider == "azure":
            config = cls.AZURE_CONFIG
        else:
            config = cls.AWS_CONFIG
        
        # 集群模式
        if config.get("cluster", False):
            from redis.cluster import RedisCluster
            client = RedisCluster(
                host=config["host"],
                port=config["port"],
                password=config["password"],
                ssl=config["ssl"],
                decode_responses=False,
            )
        else:
            # 单机模式
            client = redis.Redis(
                host=config["host"],
                port=config["port"],
                password=config["password"],
                ssl=config["ssl"],
                decode_responses=False,
            )
        
        return client
```

### 3.2 S3（长期记忆）

```python
# s3_storage.py
import boto3
from botocore.exceptions import ClientError
import json

class S3MemoryStorage:
    """S3 长期记忆存储"""
    
    def __init__(self, bucket: str, region: str = "us-east-1"):
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region)
    
    async def store(self, key: str, data: dict, metadata: dict = None) -> str:
        """存储记忆到 S3"""
        object_key = f"memories/{key}.json"
        
        content = {
            "data": data,
            "metadata": metadata or {},
            "version": "1.0",
        }
        
        self.s3.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=json.dumps(content),
            ContentType="application/json",
            Metadata=metadata or {},
        )
        
        return object_key
    
    async def retrieve(self, key: str) -> dict:
        """从 S3 检索记忆"""
        object_key = f"memories/{key}.json"
        
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            
            content = json.loads(response["Body"].read())
            return content["data"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise
    
    async def delete(self, key: str) -> bool:
        """从 S3 删除记忆"""
        object_key = f"memories/{key}.json"
        
        try:
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            return True
        except ClientError:
            return False
```

### 3.3 存储分层策略

```python
# storage_tiering.py
from enum import Enum
from datetime import datetime, timedelta

class StorageTier(Enum):
    """存储层级"""
    HOT = "hot"       # Redis (高频访问)
    WARM = "warm"     # S3 Standard (中频访问)
    COLD = "cold"     # S3 Glacier (低频访问)

class StorageTieringManager:
    """存储分层管理器"""
    
    def __init__(self, redis_client, s3_storage):
        self.redis = redis_client
        self.s3 = s3_storage
    
    async def store(self, key: str, data: dict, tier: StorageTier = StorageTier.HOT):
        """根据层级存储记忆"""
        if tier == StorageTier.HOT:
            # Redis: 短期记忆，TTL 7 天
            await self.redis.setex(
                f"memory:{key}",
                timedelta(days=7),
                pickle.dumps(data),
            )
        elif tier == StorageTier.WARM:
            # S3 Standard: 长期记忆
            await self.s3.store(key, data)
        elif tier == StorageTier.COLD:
            # S3 Glacier: 归档记忆
            await self.s3.store(key, data, storage_class="GLACIER")
    
    async def get(self, key: str) -> Optional[dict]:
        """获取记忆（自动从各层查找）"""
        # 先查 Redis
        data = await self.redis.get(f"memory:{key}")
        if data:
            return pickle.loads(data)
        
        # 再查 S3
        data = await self.s3.retrieve(key)
        if data:
            # 自动升温到 Redis
            await self.store(key, data, StorageTier.HOT)
            return data
        
        return None
    
    async def tiering_job(self):
        """定期分层任务（每天执行）"""
        # 将 7 天未访问的记忆从 HOT 移到 WARM
        # 将 30 天未访问的记忆从 WARM 移到 COLD
        pass
```

---

## 4. 网络基础设施

### 4.1 VPC 架构

```
┌─────────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16                                           │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Public Subnet 1 │  │ Public Subnet 2 │                  │
│  │ 10.0.1.0/24     │  │ 10.0.2.0/24     │                  │
│  │                 │  │                 │                  │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │                  │
│  │ │     NLB     │ │  │ │     NLB     │ │                  │
│  │ └─────────────┘ │  │ └─────────────┘ │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Private Subnet 1│  │ Private Subnet 2│                  │
│  │ 10.0.11.0/24    │  │ 10.0.12.0/24    │                  │
│  │                 │  │                 │                  │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │                  │
│  │ │  IntentOS   │ │  │ │  IntentOS   │ │                  │
│  │ │  Pods       │ │  │ │  Pods       │ │                  │
│  │ └─────────────┘ │  │ └─────────────┘ │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Private Subnet 3│  │ Private Subnet 4│                  │
│  │ 10.0.21.0/24    │  │ 10.0.22.0/24    │                  │
│  │                 │  │                 │                  │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │                  │
│  │ │   Redis     │ │  │ │   Redis     │ │                  │
│  │ │  Cluster    │ │  │ │  Cluster    │ │                  │
│  │ └─────────────┘ │  │ └─────────────┘ │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              NAT Gateway                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 API Gateway 配置

```yaml
# api_gateway.yaml
openapi: "3.0.1"
info:
  title: "IntentOS API"
  version: "1.0.0"

paths:
  /compile:
    post:
      operationId: compileIntent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CompileRequest"
      responses:
        "200":
          description: 编译成功
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CompileResponse"
      security:
        - ApiKeyAuth: []
  
  /execute:
    post:
      operationId: executeIntent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ExecuteRequest"
      responses:
        "200":
          description: 执行成功
        "202":
          description: 异步执行已接受
        "500":
          description: 执行失败
      security:
        - ApiKeyAuth: []
  
  /memory/{action}:
    post:
      operationId: memoryOperation
      parameters:
        - name: action
          in: path
          required: true
          schema:
            type: string
            enum: [get, set, delete, search]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/MemoryRequest"
      responses:
        "200":
          description: 操作成功
      security:
        - ApiKeyAuth: []

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
```

---

## 5. 监控与可观测性

### 5.1 CloudWatch 配置

```yaml
# cloudwatch.yaml
Resources:
  IntentOSDashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: "IntentOS-Dashboard"
      DashboardBody: |
        {
          "widgets": [
            {
              "type": "metric",
              "properties": {
                "title": "意图执行次数",
                "metrics": [
                  ["IntentOS", "ExecuteCount", "Environment", "prod"]
                ],
                "period": 60,
                "stat": "Sum"
              }
            },
            {
              "type": "metric",
              "properties": {
                "title": "编译延迟 (ms)",
                "metrics": [
                  ["IntentOS", "CompileLatency", "Environment", "prod"]
                ],
                "period": 60,
                "stat": "p99"
              }
            },
            {
              "type": "metric",
              "properties": {
                "title": "记忆命中率",
                "metrics": [
                  ["IntentOS", "MemoryHitRate", "Environment", "prod"]
                ],
                "period": 60,
                "stat": "Average"
              }
            },
            {
              "type": "metric",
              "properties": {
                "title": "LLM Token 使用",
                "metrics": [
                  ["IntentOS", "LLMTokens", "Environment", "prod"]
                ],
                "period": 60,
                "stat": "Sum"
              }
            }
          ]
        }
  
  IntentOSAlarms:
    Type: AWS::CloudWatch::CompositeAlarm
    Properties:
      AlarmName: "IntentOS-Critical-Alarm"
      AlarmDescription: "IntentOS 关键告警"
      AlarmRule: !Sub |
        ALARM(IntentOS-HighErrorRate)
        OR ALARM(IntentOS-HighLatency)
        OR ALARM(IntentOS-LowMemoryHitRate)
```

### 5.2 Prometheus 监控

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# 指标定义
INTENT_COMPILE_COUNT = Counter(
    "intentos_compile_total",
    "意图编译总数",
    ["status", "intent_type"],
)

INTENT_EXECUTE_COUNT = Counter(
    "intentos_execute_total",
    "意图执行总数",
    ["status", "intent_type"],
)

COMPILE_LATENCY = Histogram(
    "intentos_compile_latency_seconds",
    "编译延迟",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

EXECUTE_LATENCY = Histogram(
    "intentos_execute_latency_seconds",
    "执行延迟",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

MEMORY_HIT_RATE = Gauge(
    "intentos_memory_hit_rate",
    "记忆命中率",
)

LLM_TOKEN_USAGE = Counter(
    "intentos_llm_tokens_total",
    "LLM Token 使用",
    ["model", "type"],  # type: prompt / completion
)

# 装饰器
def measure_compile_latency(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            INTENT_COMPILE_COUNT.labels(status="success", intent_type="unknown").inc()
            return result
        except Exception as e:
            INTENT_COMPILE_COUNT.labels(status="error", intent_type="unknown").inc()
            raise
        finally:
            COMPILE_LATENCY.observe(time.time() - start)
    return wrapper

def measure_execute_latency(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            INTENT_EXECUTE_COUNT.labels(status="success", intent_type="unknown").inc()
            return result
        except Exception as e:
            INTENT_EXECUTE_COUNT.labels(status="error", intent_type="unknown").inc()
            raise
        finally:
            EXECUTE_LATENCY.observe(time.time() - start)
    return wrapper
```

### 5.3 日志配置

```python
# logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

class CloudWatchLogHandler(logging.Handler):
    """CloudWatch 日志处理器"""
    
    def __init__(self, log_group: str, log_stream: str):
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.client = boto3.client("logs")
    
    def emit(self, record):
        log_entry = {
            "timestamp": record.created,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "levelname",
                          "levelno", "pathname", "filename", "module",
                          "lineno", "funcName", "exc_info", "exc_text"]:
                log_entry[key] = value
        
        try:
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        "timestamp": int(log_entry["timestamp"] * 1000),
                        "message": json.dumps(log_entry),
                    }
                ],
            )
        except Exception:
            pass

# 配置
def setup_logging(environment: str = "prod"):
    logger = logging.getLogger("intentos")
    logger.setLevel(logging.INFO)
    
    # JSON 格式化
    log_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(timestamp)s %(level)s %(name)s %(message)s",
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    
    # CloudWatch
    if environment == "prod":
        cw_handler = CloudWatchLogHandler(
            log_group="/intentos/application",
            log_stream=socket.gethostname(),
        )
        logger.addHandler(cw_handler)
    
    return logger
```

---

## 6. 安全与合规

### 6.1 IAM 角色

```yaml
# iam_role.yaml
Resources:
  IntentOSExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: IntentOS-Execution-Role
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - ecs-tasks.amazonaws.com
                - lambda.amazonaws.com
            Action:
              - sts:AssumeRole
      Policies:
        - PolicyName: IntentOS-Policy
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: "*"
              - Effect: Allow
                Action:
                  - elasticache:*
                Resource:
                  - !Sub "arn:aws:elasticache:${AWS::Region}:${AWS::AccountId}:cluster:*"
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                  - s3:DeleteObject
                Resource:
                  - !Sub "arn:aws:s3:::intentos-memory-bucket/*"
              - Effect: Allow
                Action:
                  - secretsmanager:GetSecretValue
                Resource:
                  - !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:intentos-*"
```

### 6.2 数据加密

```python
# encryption.py
from cryptography.fernet import Fernet
import boto3

class MemoryEncryption:
    """记忆加密"""
    
    def __init__(self, key: bytes = None):
        if key is None:
            # 从 Secrets Manager 获取密钥
            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId="intentos/encryption-key")
            key = response["SecretBinary"]
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data: bytes) -> bytes:
        """加密数据"""
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """解密数据"""
        return self.cipher.decrypt(encrypted_data)

# 使用示例
async def store_encrypted_memory(key: str, data: dict):
    """存储加密记忆"""
    encryption = MemoryEncryption()
    
    # 加密
    encrypted_data = encryption.encrypt(json.dumps(data).encode())
    
    # 存储到 S3
    await s3_storage.store(key, encrypted_data)

async def retrieve_decrypted_memory(key: str) -> dict:
    """检索并解密记忆"""
    encryption = MemoryEncryption()
    
    # 从 S3 检索
    encrypted_data = await s3_storage.retrieve(key)
    
    # 解密
    data = encryption.decrypt(encrypted_data)
    return json.loads(data)
```

---

## 7. 成本优化

### 7.1 预留实例

| 资源 | 按需价格 | 预留 1 年 | 节省 |
|------|---------|---------|------|
| ECS (4 vCPU, 16GB) | $0.384/小时 | $0.240/小时 | 37% |
| Redis (cache.r5.large) | $0.166/小时 | $0.104/小时 | 37% |
| S3 Standard | $0.023/GB | - | - |
| S3 Glacier | - | $0.004/GB | 83% |

### 7.2 自动休眠

```python
# cost_optimizer.py
class CostOptimizer:
    """成本优化器"""
    
    async def scale_down_during_low_traffic(self):
        """低流量时缩容"""
        # 分析 CloudWatch 指标
        # 如果 QPS < 10 持续 30 分钟，缩容到最小副本数
        pass
    
    async def move_old_memories_to_glacier(self):
        """将旧记忆移到 Glacier"""
        # 30 天未访问的记忆移到 S3 Glacier
        # 90 天未访问的记忆移到 S3 Glacier Deep Archive
        pass
    
    async def spot_instances_for_batch_jobs(self):
        """使用 Spot 实例执行批量任务"""
        # Map/Reduce 等批量任务使用 Spot 实例
        # 节省 70-90% 成本
        pass
```

---

## 8. 部署架构

### 8.1 多区域部署

```
┌─────────────────────────────────────────────────────────────┐
│  Global Accelerator                                         │
└───────────────┬─────────────────────────────────────────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│ us-east-1 │  │ eu-west-1 │  │ ap-northeast-1 │
│         │  │         │  │         │
│ ┌─────┐ │  │ ┌─────┐ │  │ ┌─────┐ │
│ │ EKS │ │  │ │ EKS │ │  │ │ EKS │ │
│ └─────┘ │  │ └─────┘ │  │ └─────┘ │
│ ┌─────┐ │  │ ┌─────┐ │  │ ┌─────┐ │
│ │Redis│ │  │ │Redis│ │  │ │Redis│ │
│ │Cluster││  │ │Cluster││  │ │Cluster││
│ └─────┘ │  │ └─────┘ │  │ └─────┘ │
└─────────┘  └─────────┘  └─────────┘
```

### 8.2 Terraform 配置

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
  region = var.aws_region
}

# EKS 集群
resource "aws_eks_cluster" "intentos" {
  name     = "intentos-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids = aws_subnet.private[*].id
  }
}

# EKS 节点组
resource "aws_eks_node_group" "intentos" {
  cluster_name    = aws_eks_cluster.intentos.name
  node_group_name = "intentos-nodes"
  node_role_arn   = aws_iam_role.nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  scaling_config {
    desired_size = 3
    max_size     = 50
    min_size     = 1
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "intentos-redis"
  engine               = "redis"
  node_type            = "cache.r5.large"
  num_cache_nodes      = 3
  parameter_group_name = "default.redis6.x"
  port                 = 6379
}

# S3 存储桶
resource "aws_s3_bucket" "memory" {
  bucket = "intentos-memory-bucket"
}

# 生命周期规则
resource "aws_s3_bucket_lifecycle_configuration" "memory" {
  bucket = aws_s3_bucket.memory.id

  rule {
    id     = "tier-to-glacier"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    transition {
      days          = 90
      storage_class = "DEEP_ARCHIVE"
    }
  }
}
```

---

## 9. 总结

IntentOS 云基础设施的核心要素：

1. **计算**: Kubernetes/ECS 容器化部署，支持自动扩缩容
2. **存储**: Redis（短期记忆）+ S3（长期记忆）分层存储
3. **网络**: VPC 隔离，API Gateway 暴露服务
4. **监控**: CloudWatch + Prometheus 全方位监控
5. **安全**: IAM 角色、数据加密、合规审计
6. **成本**: 预留实例、自动休眠、Spot 实例优化

---

**下一篇**: [部署 IntentOS](../07-guides/04-deploy-intentos.md)

**上一篇**: [分布式架构](../02-architecture/04-distributed-architecture.md)
