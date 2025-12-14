#!/bin/bash
# BootCS CLI 安装脚本
# 用法: 
#   curl -fsSL https://bootcs.cn/install.sh | bash                    # 安装通用版
#   curl -fsSL https://bootcs.cn/install.sh | bash -s -- cs50         # 安装 CS50 课程
#   curl -fsSL https://bootcs.cn/install.sh | bash -s -- python       # 安装 Python 课程

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取课程参数
COURSE="${1:-}"

echo -e "${GREEN}🚀 Installing BootCS CLI...${NC}"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# 确定安装目录
INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

# 可用课程列表（镜像标签）
declare -A COURSES=(
    ["cs50"]="ghcr.io/bootcs-cn/bootcs-cli:cs50"
    ["python"]="ghcr.io/bootcs-cn/bootcs-cli:python"
    ["java"]="ghcr.io/bootcs-cn/bootcs-cli:java"
    # 新课程在这里添加
)

# 创建通用 bootcs 脚本
BOOTCS_SCRIPT="$INSTALL_DIR/bootcs"

cat > "$BOOTCS_SCRIPT" << 'EOF'
#!/bin/bash
# BootCS CLI Wrapper
# https://bootcs.cn

# 从 slug 推断课程（如 cs50/credit -> cs50）
infer_course() {
    local slug="$1"
    echo "${slug%%/*}"
}

# 课程镜像映射
get_image() {
    local course="$1"
    case "$course" in
        cs50)   echo "ghcr.io/bootcs-cn/bootcs-cli:cs50" ;;
        python) echo "ghcr.io/bootcs-cn/bootcs-cli:python" ;;
        java)   echo "ghcr.io/bootcs-cn/bootcs-cli:java" ;;
        *)      echo "ghcr.io/bootcs-cn/bootcs-cli:latest" ;;
    esac
}

# 解析命令
if [[ "$1" == "check" && -n "$2" ]]; then
    COURSE=$(infer_course "$2")
    IMAGE=$(get_image "$COURSE")
elif [[ -n "$BOOTCS_IMAGE" ]]; then
    IMAGE="$BOOTCS_IMAGE"
else
    IMAGE="ghcr.io/bootcs-cn/bootcs-cli:latest"
fi

# 运行容器
docker run --rm -v "$(pwd)":/workspace "$IMAGE" "$@"
EOF

chmod +x "$BOOTCS_SCRIPT"

# 如果指定了课程，预拉取镜像
if [[ -n "$COURSE" && -n "${COURSES[$COURSE]}" ]]; then
    echo -e "${BLUE}📦 Pulling ${COURSE} course image...${NC}"
    docker pull "${COURSES[$COURSE]}" || true
fi

# 检查 PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  Please add $INSTALL_DIR to your PATH:${NC}"
    echo ""
    
    # 检测 shell 类型
    SHELL_NAME=$(basename "$SHELL")
    if [[ "$SHELL_NAME" == "zsh" ]]; then
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
        echo "   source ~/.zshrc"
    elif [[ "$SHELL_NAME" == "bash" ]]; then
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        echo "   source ~/.bashrc"
    else
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
    echo ""
fi

echo -e "${GREEN}✅ BootCS CLI installed successfully!${NC}"
echo ""
echo "Usage:"
echo "   bootcs check cs50/credit     # 自动使用 CS50 镜像"
echo "   bootcs check python/hello    # 自动使用 Python 镜像"
echo "   bootcs --help                # 查看帮助"
echo ""
echo "Available courses: ${!COURSES[*]}"
