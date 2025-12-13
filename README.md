# bootcs-cli

BootCS 命令行工具 - 用于代码检查和提交

基于 [check50](https://github.com/cs50/check50) 和 [lib50](https://github.com/cs50/lib50) 扩展开发，用于 BootCS 平台的代码检查和提交。

> **注意**: 本项目与 CS50 课程本身没有直接关系，仅复用了 check50/lib50 的开源代码。

## 功能

- ✅ **代码检查** - 本地运行检查脚本验证代码正确性
- ✅ **GitHub 登录** - 使用 Device Flow 进行 GitHub 认证
- ✅ **代码提交** - 将代码提交到 BootCS 平台进行评测

## 许可证

本项目基于 GPL-3.0 许可证发布，遵循 check50/lib50 的许可证要求。

## 安装

### 方式一：Python 安装

```bash
# 开发模式安装
git clone https://github.com/bootcs-cn/bootcs-cli.git
cd bootcs-cli
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 方式二：Docker 镜像

```bash
# 拉取基础镜像
docker pull ghcr.io/bootcs-cn/bootcs-cli:latest

# 拉取包含 CS50 检查脚本的镜像
docker pull ghcr.io/bootcs-cn/bootcs-cli:cs50
```

## 快速开始

### 1. 登录

```bash
bootcs login
```

按照提示访问 GitHub 并输入验证码完成登录。

### 2. 检查代码

```bash
# 检查当前目录的代码
bootcs check cs50/hello --local /path/to/checks/hello

# 输出 JSON 格式
bootcs check cs50/hello --local /path/to/checks --output json

# 显示详细日志
bootcs check cs50/hello --local /path/to/checks --log
```

### 3. 提交代码

```bash
# 提交代码到 BootCS 平台
bootcs submit cs50/hello --local /path/to/checks/hello

# 跳过确认
bootcs submit cs50/hello --local /path/to/checks/hello -y

# 自定义提交消息
bootcs submit cs50/hello --local /path/to/checks/hello -m "Fix bug"
```

### 4. 账户管理

```bash
# 查看当前登录用户
bootcs whoami

# 登出
bootcs logout
```

## 命令参考

| 命令                   | 说明             |
| ---------------------- | ---------------- |
| `bootcs --version`     | 显示版本号       |
| `bootcs --help`        | 显示帮助信息     |
| `bootcs login`         | 使用 GitHub 登录 |
| `bootcs logout`        | 登出             |
| `bootcs whoami`        | 显示当前登录用户 |
| `bootcs check <slug>`  | 检查代码         |
| `bootcs submit <slug>` | 提交代码         |

### check 命令选项

| 选项                    | 说明                  |
| ----------------------- | --------------------- |
| `--local PATH`          | 指定本地检查脚本目录  |
| `--output [ansi\|json]` | 输出格式 (默认: ansi) |
| `--log`                 | 显示详细日志          |
| `--target NAME`         | 只运行指定的检查      |

### submit 命令选项

| 选项                | 说明                                    |
| ------------------- | --------------------------------------- |
| `--local PATH`      | 指定本地检查脚本目录 (用于获取文件列表) |
| `-m, --message MSG` | 自定义提交消息                          |
| `-y, --yes`         | 跳过确认提示                            |

## Docker 使用

### 本地自测

使用 Docker 镜像可以在本地快速进行代码检查，无需安装 Python 环境：

```bash
# 使用基础镜像检查代码
docker run --rm -v $(pwd):/workspace -v /path/to/checks:/checks \
  ghcr.io/bootcs-cn/bootcs-cli:latest \
  check course-cs50/hello --local /checks/hello

# 使用课程专用镜像（已包含检查脚本）
docker run --rm -v $(pwd):/workspace \
  ghcr.io/bootcs-cn/bootcs-cli:cs50 \
  check course-cs50/hello --local /checks/hello
```

### GitHub Actions 评测

在 GitHub Actions 中使用 Docker 镜像进行自动评测：

```yaml
# .github/workflows/evaluate.yml
name: Evaluate

on:
  push:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/bootcs-cn/bootcs-cli:cs50
    steps:
      - uses: actions/checkout@v4
      - name: Run check
        run: |
          bootcs check course-cs50/hello --local /checks/hello --output json > result.json
      - name: Upload result
        uses: actions/upload-artifact@v4
        with:
          name: result
          path: result.json
```

### 使用评测脚本

镜像中包含 `bootcs-evaluate.sh` 脚本，用于标准化评测：

```bash
# 脚本用法
bootcs-evaluate.sh <slug> <checks_path> <student_code_path>

# 示例
docker run --rm \
  -v $(pwd):/workspace \
  -v /path/to/output:/output \
  ghcr.io/bootcs-cn/bootcs-cli:cs50 \
  bootcs-evaluate.sh course-cs50/hello /checks/hello /workspace

# 结果输出到 /output/result.json
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行单元测试
pytest tests/unit/ -v

# 运行所有测试
pytest

# 代码格式化
black bootcs/
ruff check bootcs/
```

## 项目结构

```
bootcs-cli/
├── bootcs/
│   ├── __init__.py       # 版本信息
│   ├── __main__.py       # CLI 入口
│   ├── auth/             # 认证模块
│   │   ├── credentials.py
│   │   └── device_flow.py
│   ├── api/              # API 客户端
│   │   ├── client.py
│   │   └── submit.py
│   ├── check/            # 检查模块 (基于 check50)
│   │   ├── _api.py
│   │   ├── runner.py
│   │   ├── c.py
│   │   └── ...
│   └── lib50/            # 工具库 (基于 lib50)
│       ├── config.py
│       └── ...
├── tests/
│   ├── unit/             # 单元测试
│   └── check50/          # check50 测试用例
├── pyproject.toml
├── README.md
└── ROADMAP.md
```

## 环境变量

| 变量             | 说明         | 默认值                  |
| ---------------- | ------------ | ----------------------- |
| `BOOTCS_API_URL` | API 服务地址 | `https://api.bootcs.cn` |

## 文档

- [设计文档](DESIGN.md)
- [落地路线图](ROADMAP.md)

## 致谢

本项目基于以下开源项目：

- [check50](https://github.com/cs50/check50) - CS50 代码检查工具
- [lib50](https://github.com/cs50/lib50) - CS50 工具库

感谢 CS50 团队的开源贡献！
