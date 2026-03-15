#!/bin/bash
# IntentOS Cloud Self-Bootstrap 启动脚本
# 用法：./cloud/bootstrap.sh --provider aws --region us-east-1

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
PROVIDER="docker"
REGION=""
PROJECT_ID=""
MIN_INSTANCES=2
MAX_INSTANCES=10
INTENTOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 帮助信息
show_help() {
    cat << EOF
${BLUE}IntentOS Cloud Self-Bootstrap${NC}

用法：$0 [选项]

选项:
  --provider <name>     云提供商 (aws|gcp|azure|docker) [默认：docker]
  --region <region>     云区域 (如 us-east-1)
  --project-id <id>     GCP 项目 ID
  --min-instances <n>   最小实例数 [默认：2]
  --max-instances <n>   最大实例数 [默认：10]
  --help                显示此帮助信息

示例:
  # Docker 本地部署
  $0 --provider docker

  # AWS 部署
  $0 --provider aws --region us-east-1

  # GCP 部署
  $0 --provider gcp --region us-central1 --project-id my-project

  # Azure 部署
  $0 --provider azure --location eastus

EOF
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --min-instances)
            MIN_INSTANCES="$2"
            shift 2
            ;;
        --max-instances)
            MAX_INSTANCES="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项：$1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 打印横幅
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     IntentOS Cloud Self-Bootstrap                      ║${NC}"
echo -e "${BLUE}║     AI Native Operating System                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查 Python 环境
echo -e "${YELLOW}📦 检查环境...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

# 安装依赖
echo -e "📦 安装依赖..."
cd "$INTENTOS_DIR"
pip install -q -e .
pip install -q aiohttp redis

# 设置环境变量
export INTENTOS_PROVIDER="$PROVIDER"
export INTENTOS_REGION="$REGION"
export INTENTOS_PROJECT_ID="$PROJECT_ID"
export INTENTOS_MIN_INSTANCES="$MIN_INSTANCES"
export INTENTOS_MAX_INSTANCES="$MAX_INSTANCES"

# 构建命令
PYTHON_CMD="python3 -m intentos.bootstrap.cloud_bootstrap"
PYTHON_CMD+=" --provider $PROVIDER"

if [ -n "$REGION" ]; then
    PYTHON_CMD+=" --region $REGION"
fi

if [ -n "$PROJECT_ID" ]; then
    PYTHON_CMD+=" --project-id $PROJECT_ID"
fi

PYTHON_CMD+=" --min-instances $MIN_INSTANCES"
PYTHON_CMD+=" --max-instances $MAX_INSTANCES"

# 打印配置
echo ""
echo -e "${BLUE}配置:${NC}"
echo -e "  云提供商：${GREEN}$PROVIDER${NC}"
echo -e "  区域：${GREEN}${REGION:-default}${NC}"
echo -e "  项目 ID: ${GREEN}${PROJECT_ID:-N/A}${NC}"
echo -e "  实例数：${GREEN}$MIN_INSTANCES - $MAX_INSTANCES${NC}"
echo ""

# 确认
if [ "$PROVIDER" != "docker" ]; then
    echo -e "${YELLOW}⚠️  注意：云部署将产生费用！${NC}"
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 部署已取消${NC}"
        exit 1
    fi
fi

# 执行 Bootstrap
echo ""
echo -e "${GREEN}🚀 开始 Self-Bootstrap...${NC}"
echo ""

eval "$PYTHON_CMD"

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     ✅ 部署成功！                                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}下一步:${NC}"
    echo "  1. 访问 API 端点查看状态"
    echo "  2. 配置 LLM API 密钥"
    echo "  3. 开始使用 IntentOS!"
    echo ""
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║     ❌ 部署失败                                       ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}故障排查:${NC}"
    echo "  1. 检查云凭证配置"
    echo "  2. 查看日志输出"
    echo "  3. 运行 terraform validate"
    echo ""
    exit 1
fi
