# IntentOS 自启动与云上永生指南

## 目录

1. [本地自启动](#1-本地自启动)
2. [Docker 容器化](#2-docker 容器化)
3. [Kubernetes 部署](#3-kubernetes 部署)
4. [云服务部署](#4-云服务部署)
5. [健康检查与自愈](#5-健康检查与自愈)
6. [监控与告警](#6-监控与告警)

---

## 1. 本地自启动

### 1.1 systemd 服务（Linux）

创建 systemd 服务文件：

```bash
sudo tee /etc/systemd/system/intentos.service > /dev/null <<'EOF'
[Unit]
Description=IntentOS AI Native Operating System
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=intentos
Group=intentos
WorkingDirectory=/opt/intentos
Environment="PYTHONPATH=/opt/intentos"
Environment="REDIS_URL=redis://localhost:6379"
ExecStart=/opt/intentos/venv/bin/python -m intentos.interface.daemon
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=intentos

# 安全限制
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/intentos/data /opt/intentos/logs

# 资源限制
LimitNOFILE=65535
MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF
```

启用并启动服务：

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启动
sudo systemctl enable intentos

# 启动服务
sudo systemctl start intentos

# 查看状态
sudo systemctl status intentos

# 查看日志
sudo journalctl -u intentos -f
```

### 1.2 Supervisor 配置

```ini
; /etc/supervisor/conf.d/intentos.conf
[program:intentos]
command=/opt/intentos/venv/bin/python -m intentos.interface.daemon
directory=/opt/intentos
user=intentos
autostart=true
autorestart=true
startretries=10
stderr_logfile=/var/log/intentos/err.log
stdout_logfile=/var/log/intentos/out.log
environment=PYTHONPATH="/opt/intentos",REDIS_URL="redis://localhost:6379"
```

### 1.3 macOS LaunchDaemon

```xml
<!-- ~/Library/LaunchAgents/com.intentos.daemon.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.intentos.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/intentos/venv/bin/python</string>
        <string>-m</string>
        <string>intentos.interface.daemon</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/opt/intentos</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>/opt/intentos</string>
        <key>REDIS_URL</key>
        <string>redis://localhost:6379</string>
    </dict>
</dict>
</plist>
```

加载：
```bash
launchctl load ~/Library/LaunchAgents/com.intentos.daemon.plist
```

---

## 2. Docker 容器化

### 2.1 Dockerfile

```dockerfile
# IntentOS Production Dockerfile
FROM python:3.11-slim-bookworm

# 元数据
LABEL maintainer="IntentOS Team"
LABEL version="9.0"
LABEL description="AI Native Operating System"

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    INTENTOS_VERSION=9.0 \
    INTENTOS_ENV=production

# 工作目录
WORKDIR /opt/intentos

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r intentos && useradd -r -g intentos intentos

# 复制依赖文件
COPY pyproject.toml .
COPY README.md .

# 安装 Python 依赖
RUN pip install --no-cache-dir . && \
    pip install --no-cache-dir \
    gunicorn \
    uvicorn \
    aiohttp \
    redis \
    sentry-sdk

# 复制应用代码
COPY intentos/ ./intentos/
COPY examples/ ./examples/

# 创建数据目录
RUN mkdir -p /opt/intentos/data \
    /opt/intentos/logs \
    /opt/intentos/checkpoints \
    && chown -R intentos:intentos /opt/intentos

# 切换到非 root 用户
USER intentos

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/v1/status || exit 1

# 启动命令
ENTRYPOINT ["python", "-m", "intentos.interface.daemon"]
```

### 2.2 Docker Compose（完整栈）

```yaml
# docker-compose.yml
version: '3.8'

services:
  # IntentOS 主服务
  intentos:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: intentos-main
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
      - SENTRY_DSN=${SENTRY_DSN:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
    volumes:
      - intentos-data:/opt/intentos/data
      - intentos-checkpoints:/opt/intentos/checkpoints
      - ./logs:/opt/intentos/logs
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - intentos-net
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G

  # Redis（记忆存储）
  redis:
    image: redis:7-alpine
    container_name: intentos-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - intentos-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx（反向代理）
  nginx:
    image: nginx:alpine
    container_name: intentos-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - intentos
    networks:
      - intentos-net

  # 监控（可选）
  prometheus:
    image: prom/prometheus:latest
    container_name: intentos-prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - intentos-net

  # 日志聚合（可选）
  loki:
    image: grafana/loki:latest
    container_name: intentos-loki
    restart: unless-stopped
    volumes:
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - intentos-net

volumes:
  intentos-data:
  intentos-checkpoints:
  redis-data:
  prometheus-data:
  loki-data:

networks:
  intentos-net:
    driver: bridge
```

### 2.3 Nginx 配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream intentos {
        server intentos-main:8080;
        keepalive 32;
    }

    # 限流
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;

    server {
        listen 80;
        server_name _;

        # 强制 HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name _;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            proxy_pass http://intentos;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;

            # 限流
            limit_req zone=api_limit burst=200 nodelay;
        }

        # 健康检查端点
        location /health {
            proxy_pass http://intentos/v1/status;
            access_log off;
        }
    }
}
```

### 2.4 构建和运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f intentos

# 停止服务
docker-compose down

# 完全清理（包括数据卷）
docker-compose down -v
```

---

## 3. Kubernetes 部署

### 3.1 Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intentos
  namespace: intentos
  labels:
    app: intentos
    version: v9.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: intentos
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: intentos
        version: v9.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      serviceAccountName: intentos-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: intentos
        image: intentos/intentos:v9.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: intentos-secrets
              key: redis-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: intentos-secrets
              key: openai-api-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: intentos-secrets
              key: anthropic-api-key
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /v1/status
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /v1/status
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: data
          mountPath: /opt/intentos/data
        - name: checkpoints
          mountPath: /opt/intentos/checkpoints
        - name: logs
          mountPath: /opt/intentos/logs
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: intentos-data-pvc
      - name: checkpoints
        persistentVolumeClaim:
          claimName: intentos-checkpoints-pvc
      - name: logs
        emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: intentos
              topologyKey: kubernetes.io/hostname
```

### 3.2 HorizontalPodAutoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: intentos-hpa
  namespace: intentos
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: intentos
  minReplicas: 3
  maxReplicas: 20
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
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Max
```

### 3.3 PodDisruptionBudget

```yaml
# k8s/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: intentos-pdb
  namespace: intentos
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: intentos
```

### 3.4 部署命令

```bash
# 创建命名空间
kubectl create namespace intentos

# 创建 Secret
kubectl create secret generic intentos-secrets \
  --from-literal=redis-url=redis://redis-master:6379 \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY \
  -n intentos

# 应用配置
kubectl apply -f k8s/

# 查看状态
kubectl get all -n intentos

# 查看日志
kubectl logs -f deployment/intentos -n intentos

# 扩缩容
kubectl scale deployment intentos --replicas=5 -n intentos
```

---

## 4. 云服务部署

### 4.1 AWS ECS/Fargate

```yaml
# aws/ecs-task-definition.json
{
  "family": "intentos",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "intentos",
      "image": "ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/intentos:v9.0",
      "portMappings": [{"containerPort": 8080}],
      "environment": [
        {"name": "REDIS_URL", "value": "redis://redis-cluster.xxx.amazonaws.com:6379"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:intentos-secrets:OPENAI_API_KEY::"},
        {"name": "ANTHROPIC_API_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:intentos-secrets:ANTHROPIC_API_KEY::"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/intentos",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "intentos"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/v1/status || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3
      }
    }
  ]
}
```

### 4.2 GCP Cloud Run

```yaml
# gcp/cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: intentos
  namespace: default
spec:
  template:
    spec:
      containers:
      - image: gcr.io/PROJECT/intentos:v9.0
        ports:
        - containerPort: 8080
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: intentos-secrets
              key: redis-url
        resources:
          limits:
            cpu: "2"
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /v1/status
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
      maxScale: 10
      minScale: 2
```

### 4.3 阿里云 ACK

```yaml
# aliyun/ack-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intentos
  namespace: default
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
        image: registry.cn-shanghai.aliyuncs.com/intentos/intentos:v9.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /v1/status
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
```

---

## 5. 健康检查与自愈

### 5.1 健康检查端点

IntentOS 已内置健康检查端点 `/v1/status`，返回：

```json
{
  "status": "success",
  "timestamp": "2026-03-15T10:30:00Z",
  "data": {
    "kernel_version": "9.0",
    "uptime": "7d 12h 30m",
    "cluster": {
      "total_nodes": 3,
      "active_nodes": 3
    },
    "memory_state": {...},
    "processes": [...]
  }
}
```

### 5.2 自愈脚本

```bash
#!/bin/bash
# scripts/auto-heal.sh

set -e

INTENTOS_URL="${INTENTOS_URL:-http://localhost:8080}"
HEALTH_ENDPOINT="/v1/status"
MAX_RETRIES=5
RETRY_DELAY=10

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" "${INTENTOS_URL}${HEALTH_ENDPOINT}")
    if [ "$response" -eq 200 ]; then
        return 0
    else
        return 1
    fi
}

restart_service() {
    echo "[$(date)] Health check failed! Attempting restart..."
    
    # systemd
    if command -v systemctl &> /dev/null; then
        sudo systemctl restart intentos
    # Docker
    elif command -v docker &> /dev/null; then
        docker restart intentos-main
    # Kubernetes
    elif command -v kubectl &> /dev/null; then
        kubectl rollout restart deployment/intentos
    fi
    
    echo "[$(date)] Restart initiated. Waiting ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
}

# 主循环
retry_count=0
while true; do
    if ! check_health; then
        retry_count=$((retry_count + 1))
        echo "[$(date)] Health check failed (attempt $retry_count/$MAX_RETRIES)"
        
        if [ $retry_count -ge $MAX_RETRIES ]; then
            echo "[$(date)] Max retries reached! Sending alert..."
            # 发送告警（集成 PagerDuty/Slack/钉钉等）
            # curl -X POST $ALERT_WEBHOOK -d "IntentOS health check failed"
            retry_count=0
        fi
        
        restart_service
    else
        if [ $retry_count -gt 0 ]; then
            echo "[$(date)] Service recovered!"
        fi
        retry_count=0
    fi
    
    sleep 60
done
```

### 5.3 看门狗服务

```bash
# /etc/systemd/system/intentos-watchdog.service
[Unit]
Description=IntentOS Watchdog
After=intentos.service
Wants=intentos.service

[Service]
Type=simple
ExecStart=/opt/intentos/scripts/auto-heal.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 6. 监控与告警

### 6.1 Prometheus 配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'intentos'
    static_configs:
      - targets: ['intentos-main:8080']
    metrics_path: '/metrics'
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### 6.2 Grafana 告警规则

```yaml
# alerting.yaml
groups:
  - name: intentos
    rules:
      - alert: IntentOSDown
        expr: up{job="intentos"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "IntentOS 实例宕机"
          description: "{{ $labels.instance }} 已宕机超过 2 分钟"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="intentos"}[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "IntentOS 响应延迟过高"
          description: "P95 延迟超过 2 秒"
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{job="intentos",status=~"5.."}[5m]) / rate(http_requests_total{job="intentos"}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "IntentOS 错误率过高"
          description: "5xx 错误率超过 5%"
```

### 6.3 告警通知集成

```yaml
# alertmanager.yml
route:
  receiver: 'slack-notifications'
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
        channel: '#intentos-alerts'
        title: '🚨 IntentOS 告警'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
  
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

---

## 7. 备份与恢复

### 7.1 数据备份脚本

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/backup/intentos"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份检查点
echo "[$(date)] Backing up checkpoints..."
tar -czf $BACKUP_DIR/checkpoints_$DATE.tar.gz /opt/intentos/checkpoints/

# 备份 Redis 数据
echo "[$(date)] Backing up Redis..."
redis-cli BGSAVE
sleep 5
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 清理旧备份
echo "[$(date)] Cleaning up old backups..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.rdb" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup completed: $BACKUP_DIR"
```

### 7.2 定时备份（Cron）

```bash
# /etc/cron.d/intentos-backup
0 2 * * * root /opt/intentos/scripts/backup.sh >> /var/log/intentos/backup.log 2>&1
```

---

## 8. 快速启动命令汇总

```bash
# === 本地开发 ===
python -m intentos.interface.daemon

# === Docker ===
docker-compose up -d
docker-compose logs -f

# === Kubernetes ===
kubectl apply -f k8s/
kubectl get pods -n intentos

# === 查看状态 ===
curl http://localhost:8080/v1/status

# === 查看日志 ===
journalctl -u intentos -f
docker logs -f intentos-main
kubectl logs -f deployment/intentos -n intentos

# === 重启服务 ===
sudo systemctl restart intentos
docker restart intentos-main
kubectl rollout restart deployment/intentos -n intentos
```

---

## 总结

通过以上配置，IntentOS 可以实现：

| 特性 | 实现方式 |
|------|---------|
| **开机自启动** | systemd / LaunchDaemon / Supervisor |
| **容器化** | Docker + Docker Compose |
| **编排调度** | Kubernetes Deployment + HPA |
| **云服务** | AWS ECS / GCP Cloud Run / 阿里云 ACK |
| **健康检查** | `/v1/status` 端点 + 看门狗 |
| **自动恢复** | 自愈脚本 + K8s 重启策略 |
| **监控告警** | Prometheus + Grafana + Alertmanager |
| **数据备份** | 定时备份脚本 + 云存储 |

**IntentOS 将在云上获得永生！** 🚀✨
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
