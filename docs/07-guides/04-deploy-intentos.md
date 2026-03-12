# 部署 IntentOS

> 本指南介绍如何在生产环境中部署 IntentOS，包括单机部署、集群部署和云原生部署。

---

## 1. 部署架构

### 1.1 单机部署

适合开发和测试环境：

```
┌─────────────────────────────────────┐
│  IntentOS App                       │
│  ┌─────────────────────────────┐   │
│  │  IntentOS Core              │   │
│  │  - Parser                   │   │
│  │  - Compiler                 │   │
│  │  - Engine                   │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Memory Manager             │   │
│  │  (SQLite/File)              │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  LLM Backend                │   │
│  │  (OpenAI/Ollama)            │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 1.2 集群部署

适合生产环境：

```
                    ┌─────────────┐
                    │  Load       │
                    │  Balancer   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│  IntentOS       │ │  IntentOS   │ │  IntentOS       │
│  Node 1         │ │  Node 2     │ │  Node 3         │
└────────┬────────┘ └──────┬──────┘ └────────┬────────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│  Redis Cluster  │ │  PostgreSQL │ │  LLM Gateway    │
└─────────────────┘ └─────────────┘ └─────────────────┘
```

---

## 2. 单机部署

### 2.1 环境要求

- Python 3.10+
- 4GB+ RAM
- 10GB+ 磁盘空间

### 2.2 安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装 IntentOS
pip install intentos[all]

# 验证安装
python -c "from intentos import IntentOS; print('✅ 安装成功')"
```

### 2.3 配置

```yaml
# config.yaml
intentos:
  # 核心配置
  max_concurrency: 10
  timeout_seconds: 300
  
  # 记忆配置
  memory:
    short_term_max: 10000
    short_term_ttl_seconds: 3600
    long_term_backend: "sqlite"  # 或 "redis"
    sqlite_path: "./data/memory.db"
  
  # LLM 配置
  llm:
    default_provider: "openai"
    providers:
      openai:
        api_key: "${OPENAI_API_KEY}"
        model: "gpt-4o"
      ollama:
        host: "http://localhost:11434"
        model: "llama3.1"
  
  # 日志配置
  logging:
    level: "INFO"
    file: "./logs/intentos.log"
```

### 2.4 启动服务

```python
# server.py
import asyncio
import yaml
from intentos import IntentOS

async def main():
    # 加载配置
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    # 创建 IntentOS 实例
    os = IntentOS()
    os.initialize()
    
    # 注册 App
    from my_app import register
    register(os.registry)
    
    # 启动服务
    print("🚀 IntentOS 已启动")
    
    # 示例：执行意图
    while True:
        user_input = input("用户：")
        if user_input == "exit":
            break
        
        result = await os.execute(user_input)
        print(f"IntentOS: {result}")

asyncio.run(main())
```

```bash
python server.py
```

---

## 3. 集群部署

### 3.1 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制代码
COPY . .

# 启动命令
CMD ["python", "server.py"]
```

```yaml
# docker-compose.yaml
version: '3.8'

services:
  intentos-1:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_HOST=redis
    volumes:
      - ./logs:/app/logs
    depends_on:
      - redis
  
  intentos-2:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_HOST=redis
    volumes:
      - ./logs:/app/logs
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - intentos-1
      - intentos-2

volumes:
  redis_data:
```

### 3.2 Nginx 配置

```nginx
# nginx.conf
upstream intentos {
    least_conn;
    server intentos-1:8000;
    server intentos-2:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://intentos;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }
}
```

### 3.3 启动集群

```bash
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f intentos-1
```

---

## 4. Kubernetes 部署

### 4.1 Helm Chart

```yaml
# Chart.yaml
apiVersion: v2
name: intentos
version: 1.0.0
description: IntentOS Helm Chart

# values.yaml
replicaCount: 3

image:
  repository: intentos/intentos
  tag: latest

config:
  maxConcurrency: 10
  timeoutSeconds: 300

redis:
  enabled: true
  clusterEnabled: true

llm:
  openai:
    apiKeySecret: openai-api-key
```

### 4.2 Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intentos
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
        image: intentos/intentos:latest
        env:
        - name: REDIS_HOST
          value: "redis-master"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-api-key
              key: api-key
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

### 4.3 部署

```bash
# 添加 Helm repo
helm repo add intentos https://charts.intentos.io

# 安装
helm install my-intentos intentos/intentos \
  --set config.openaiApiKey=sk-... \
  --set replicaCount=3

# 升级
helm upgrade my-intentos intentos/intentos \
  --set replicaCount=5

# 卸载
helm uninstall my-intentos
```

---

## 5. 监控和运维

### 5.1 健康检查

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
    }

@app.get("/metrics")
async def metrics():
    return {
        "requests_total": stats.requests_total,
        "errors_total": stats.errors_total,
        "avg_latency_ms": stats.avg_latency_ms,
    }
```

### 5.2 日志收集

```yaml
# logging.yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # 文件日志
  file:
    path: /var/log/intentos/app.log
    max_size: 100MB
    backup_count: 10
  
  # 集中日志（ELK）
  elk:
    enabled: true
    host: elasticsearch
    port: 9200
    index: intentos-logs
```

### 5.3 告警配置

```yaml
# alerting.yaml
alerting:
  rules:
    - name: HighErrorRate
      condition: "error_rate > 0.05"
      duration: "5m"
      severity: "critical"
      notify:
        - slack
        - pagerduty
    
    - name: HighLatency
      condition: "p99_latency_ms > 5000"
      duration: "10m"
      severity: "warning"
      notify:
        - slack
```

---

## 6. 安全配置

### 6.1 API 认证

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader

app = FastAPI()
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != os.environ.get("INTENTOS_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.post("/execute")
async def execute(intent: Intent, api_key: str = Depends(verify_api_key)):
    # 已验证的请求
    ...
```

### 6.2 权限管理

```yaml
# rbac.yaml
roles:
  - name: admin
    permissions:
      - "*"
  
  - name: analyst
    permissions:
      - "read_sales"
      - "generate_report"
  
  - name: viewer
    permissions:
      - "read_sales"

users:
  - name: admin
    role: admin
  
  - name: analyst1
    role: analyst
```

---

## 7. 性能优化

### 7.1 缓存配置

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_capability(name: str):
    return registry.get_capability(name)
```

### 7.2 连接池

```yaml
# database.yaml
database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 3600
```

---

## 8. 故障排查

### 8.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 内存溢出 | 记忆过多 | 增加 TTL，减少 max_size |
| 请求超时 | LLM 响应慢 | 增加 timeout，使用备用模型 |
| 权限错误 | 配置错误 | 检查 RBAC 配置 |

### 8.2 调试模式

```yaml
# config.yaml
debug:
  enabled: true
  verbose_logging: true
  trace_requests: true
```

---

## 9. 总结

部署 IntentOS 的关键步骤：

1. **选择部署架构**: 单机/集群/云原生
2. **配置环境**: Python、Redis、LLM
3. **部署服务**: Docker/Kubernetes
4. **配置监控**: 日志、指标、告警
5. **安全加固**: 认证、授权、加密

---

**上一篇**: [注册能力](03-register-capability.md)
