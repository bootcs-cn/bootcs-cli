#!/bin/bash
# bootcs-evaluate.sh - 评测入口脚本
# 用于 GitHub Actions 评测 workflow

set -e

# 参数
SLUG="${1:-}"
CHECKS_PATH="${2:-/checks}"
STUDENT_CODE_PATH="${3:-/workspace}"

if [ -z "$SLUG" ]; then
    echo "Usage: bootcs-evaluate.sh <slug> [checks_path] [student_code_path]"
    echo "Example: bootcs-evaluate.sh course-cs50/hello /checks /workspace"
    exit 1
fi

# 解析 slug
COURSE=$(echo "$SLUG" | cut -d'/' -f1)
STAGE=$(echo "$SLUG" | cut -d'/' -f2)

# 检查目录
CHECK_DIR="${CHECKS_PATH}/${STAGE}"
if [ ! -d "$CHECK_DIR" ]; then
    echo "Error: Check directory not found: $CHECK_DIR"
    exit 1
fi

# 切换到学生代码目录
cd "$STUDENT_CODE_PATH"

echo "========================================"
echo "BootCS Evaluation"
echo "========================================"
echo "Slug:        $SLUG"
echo "Check Dir:   $CHECK_DIR"
echo "Working Dir: $(pwd)"
echo "========================================"
echo ""

# 运行检查
python -m bootcs check "$SLUG" --local "$CHECK_DIR" --output json

# 获取退出码
EXIT_CODE=$?

echo ""
echo "========================================"
echo "Evaluation completed with exit code: $EXIT_CODE"
echo "========================================"

exit $EXIT_CODE
