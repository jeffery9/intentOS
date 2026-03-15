# IntentOS Production Dockerfile
FROM python:3.11-slim-bookworm

# 元数据
LABEL maintainer="IntentOS Team"
LABEL version="9.0"
LABEL description="AI Native Operating System - Semantic VM with Self-Bootstrap"

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    INTENTOS_VERSION=9.0 \
    INTENTOS_ENV=production \
    REDIS_URL=redis://localhost:6379 \
    LOG_LEVEL=INFO

# 工作目录
WORKDIR /opt/intentos

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    redis-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r intentos && useradd -r -g intentos -d /opt/intentos intentos

# 复制依赖文件
COPY pyproject.toml .
COPY README.md .

# 安装 Python 依赖
RUN pip install --no-cache-dir . && \
    pip install --no-cache-dir \
    aiohttp \
    redis \
    sentry-sdk

# 复制应用代码
COPY intentos/ ./intentos/

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
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/v1/status || exit 1

# 启动命令（守护进程模式）
CMD ["python", "-m", "intentos.interface.daemon"]
