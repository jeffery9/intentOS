#!/bin/bash
# IntentOS 自启动安装脚本
# 用法：sudo ./scripts/install-service.sh

set -e

echo "=========================================="
echo "  IntentOS 自启动服务安装脚本"
echo "=========================================="

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 配置变量
INTENTOS_DIR="${INTENTOS_DIR:-/opt/intentos}"
PYTHON_VENV="${INTENTOS_DIR}/venv"
SERVICE_NAME="intentos"

echo ""
echo "📁 安装目录：$INTENTOS_DIR"
echo ""

# 检查目录是否存在
if [ ! -d "$INTENTOS_DIR" ]; then
    echo "❌ IntentOS 目录不存在：$INTENTOS_DIR"
    exit 1
fi

# 检查 Python 虚拟环境
if [ ! -d "$PYTHON_VENV" ]; then
    echo "⚠️  Python 虚拟环境不存在，正在创建..."
    cd "$INTENTOS_DIR"
    python3 -m venv venv
    source "$PYTHON_VENV/bin/activate"
    pip install -e .
    pip install aiohttp redis
else
    source "$PYTHON_VENV/bin/activate"
fi

# 创建 intentos 用户（如果不存在）
if ! id "intentos" &>/dev/null; then
    echo "👤 创建 intentos 用户..."
    useradd -r -d "$INTENTOS_DIR" -s /bin/false intentos
fi

# 设置权限
echo "🔐 设置文件权限..."
chown -R intentos:intentos "$INTENTOS_DIR"
chmod 755 "$INTENTOS_DIR"

# 创建数据目录
echo "📂 创建数据目录..."
mkdir -p "$INTENTOS_DIR/data"
mkdir -p "$INTENTOS_DIR/logs"
mkdir -p "$INTENTOS_DIR/checkpoints"
chown -R intentos:intentos "$INTENTOS_DIR/data"
chown -R intentos:intentos "$INTENTOS_DIR/logs"
chown -R intentos:intentos "$INTENTOS_DIR/checkpoints"

# 安装 systemd 服务
echo "🔧 安装 systemd 服务..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/intentos.service" /etc/systemd/system/intentos.service

# 重新加载 systemd
echo "🔄 重新加载 systemd 配置..."
systemctl daemon-reload

# 启用服务
echo "✅ 启用开机自启动..."
systemctl enable intentos

# 启动服务
echo "🚀 启动 IntentOS 服务..."
systemctl start intentos

# 检查状态
echo ""
echo "📊 服务状态:"
systemctl status intentos --no-pager -l

echo ""
echo "=========================================="
echo "  ✅ 安装完成!"
echo "=========================================="
echo ""
echo "常用命令:"
echo "  查看状态：sudo systemctl status intentos"
echo "  启动服务：sudo systemctl start intentos"
echo "  停止服务：sudo systemctl stop intentos"
echo "  重启服务：sudo systemctl restart intentos"
echo "  查看日志：sudo journalctl -u intentos -f"
echo "  禁用自启：sudo systemctl disable intentos"
echo ""
echo "API 端点：http://localhost:8080"
echo "健康检查：http://localhost:8080/v1/status"
echo ""
