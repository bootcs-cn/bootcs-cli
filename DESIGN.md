# bootcs-cli-v2 设计文档

> **版本**: v2.0  
> **语言**: Python 3.9+  
> **创建日期**: 2025-12-13

## 1. 项目概述

bootcs-cli-v2 是 bootcs 平台的命令行工具，基于 Python 重写，整合 CS50 的 check50/lib50 成熟代码，同时适配 bootcs API 进行代码提交。

### 1.1 设计目标

1. **复用成熟代码**: 直接复用 check50/lib50 约 3500 行经过验证的代码
2. **统一入口**: 整合 check、submit、login 等功能到单一 CLI
3. **适配 bootcs API**: submit 功能调用 bootcs API，不依赖 GitHub 个人仓库
4. **保持兼容**: 检查脚本格式与 CS50 原版完全兼容

### 1.2 与 TypeScript 版本对比

| 方面      | TypeScript (v1)            | Python (v2)        |
| --------- | -------------------------- | ------------------ |
| 进程控制  | child_process (有兼容问题) | pexpect (成熟稳定) |
| 代码复用  | 从零实现                   | 复用 check50/lib50 |
| CS50 兼容 | 部分兼容                   | 完全兼容           |
| 维护成本  | 较高                       | 较低               |

---

## 2. 架构设计

### 2.1 项目结构

```
bootcs-cli-v2/
├── pyproject.toml           # 项目配置
├── README.md
├── DESIGN.md                # 本文档
├── ROADMAP.md               # 落地路线图
├── bootcs/
│   ├── __init__.py          # 版本、导出
│   ├── __main__.py          # CLI 入口
│   │
│   ├── cli/                 # CLI 命令
│   │   ├── __init__.py
│   │   ├── check.py         # bootcs check
│   │   ├── submit.py        # bootcs submit
│   │   ├── login.py         # bootcs login
│   │   └── logout.py        # bootcs logout
│   │
│   ├── check/               # 检查引擎 (来自 check50)
│   │   ├── __init__.py      # 导出 run, exists, Failure 等
│   │   ├── _api.py          # 核心 API: run(), exists(), include()
│   │   ├── _exceptions.py   # Failure, Mismatch, Missing
│   │   ├── internal.py      # 内部辅助
│   │   ├── runner.py        # 检查运行器
│   │   ├── c.py             # C 语言支持
│   │   ├── py.py            # Python 支持
│   │   ├── regex.py         # 正则辅助
│   │   └── renderer/        # 结果渲染
│   │
│   ├── lib/                 # 基础库 (来自 lib50)
│   │   ├── __init__.py
│   │   ├── config.py        # YAML 配置加载
│   │   ├── _errors.py       # 错误定义
│   │   └── crypto.py        # 签名验证
│   │
│   ├── api/                 # bootcs API 客户端
│   │   ├── __init__.py
│   │   ├── client.py        # HTTP 客户端
│   │   └── submit.py        # 提交 API
│   │
│   └── auth/                # 认证模块
│       ├── __init__.py
│       ├── credentials.py   # 凭证存储
│       └── device_flow.py   # GitHub Device Flow
│
└── tests/                   # 测试
    ├── __init__.py
    ├── test_check.py
    └── test_submit.py
```

### 2.2 模块职责

| 模块           | 来源              | 职责                            |
| -------------- | ----------------- | ------------------------------- |
| `bootcs.check` | check50           | 检查 API (run, exists, Failure) |
| `bootcs.lib`   | lib50             | 配置加载、签名验证              |
| `bootcs.cli`   | 新写              | 命令行接口                      |
| `bootcs.api`   | 新写              | bootcs API 客户端               |
| `bootcs.auth`  | 部分 lib50 + 新写 | 认证管理                        |

---

## 3. 核心流程

### 3.1 bootcs check 流程

```
用户执行: bootcs check cs50/hello

1. 解析 slug → course=cs50, stage=hello
2. 获取检查脚本
   - --dev: 使用本地路径
   - --local: 使用缓存
   - 默认: 从 GitHub 下载
3. 复制学生代码到临时目录
4. 加载并执行检查脚本
5. 收集结果并渲染输出
```

```python
# 检查脚本示例 (Python, 来自 check50)
import check50

@check50.check()
def exists():
    """hello.c exists"""
    check50.exists("hello.c")

@check50.check(exists)
def compiles():
    """hello.c compiles"""
    check50.c.compile("hello.c")

@check50.check(compiles)
def hello():
    """prints "hello, world\\n" """
    check50.run("./hello").stdout("hello, world\n").exit(0)
```

### 3.2 bootcs submit 流程

```
用户执行: bootcs submit cs50/hello

1. 检查登录状态
2. 读取 .bootcs.yaml 配置
3. 收集要提交的文件
4. 显示文件列表，确认提交
5. Base64 编码文件内容
6. POST /api/submit 到 bootcs API
7. 轮询 GET /api/submissions/:id
8. 显示评测结果
```

```python
# submit 核心实现
async def submit(slug: str, directory: str) -> SubmitResult:
    # 1. 读取凭证
    token = credentials.get_token()

    # 2. 收集文件
    config = load_config(directory)
    files = collect_files(directory, config)

    # 3. 编码并提交
    encoded = [{"path": f.path, "content": base64_encode(f)} for f in files]
    response = api.post("/api/submit", {"slug": slug, "files": encoded})

    # 4. 轮询结果
    return await poll_result(response["submissionId"])
```

### 3.3 bootcs login 流程

```
用户执行: bootcs login

1. POST /api/auth/device/code
2. 获取 user_code, verification_uri
3. 提示用户访问 GitHub 授权页面
4. 轮询 POST /api/auth/device/token
5. 收到 token 后保存到 ~/.bootcs/credentials.yaml
```

---

## 4. 代码复用计划

### 4.1 从 check50 复用

| 文件             | 行数      | 复用方式              |
| ---------------- | --------- | --------------------- |
| `_api.py`        | 520       | 直接复制，调整 import |
| `runner.py`      | 407       | 直接复制              |
| `c.py`           | 140       | 直接复制              |
| `py.py`          | 60        | 直接复制              |
| `internal.py`    | ~200      | 直接复制              |
| `_exceptions.py` | ~100      | 直接复制              |
| `regex.py`       | ~50       | 直接复制              |
| `renderer/`      | ~300      | 直接复制              |
| **小计**         | **~1800** |                       |

### 4.2 从 lib50 复用

| 文件         | 行数     | 复用方式 |
| ------------ | -------- | -------- |
| `config.py`  | ~400     | 直接复制 |
| `_errors.py` | ~100     | 直接复制 |
| `crypto.py`  | ~150     | 直接复制 |
| **小计**     | **~650** |          |

### 4.3 需要新写

| 模块          | 预估行数 | 说明              |
| ------------- | -------- | ----------------- |
| `cli/*.py`    | ~400     | CLI 命令实现      |
| `api/*.py`    | ~200     | bootcs API 客户端 |
| `auth/*.py`   | ~150     | 认证管理          |
| `__main__.py` | ~100     | 入口              |
| **小计**      | **~850** |                   |

**总计**: 复用 ~2450 行 + 新写 ~850 行 = ~3300 行

---

## 5. 配置文件

### 5.1 用户配置 (~/.bootcs/config.yaml)

```yaml
api_url: https://api.bootcs.cn
```

### 5.2 凭证文件 (~/.bootcs/credentials.yaml)

```yaml
token: "eyJhbGciOiJIUzI1NiIs..."
username: "boboweike"
expires_at: "2025-12-20T00:00:00Z"
```

### 5.3 项目配置 (.bootcs.yaml)

```yaml
# 在学生代码目录中
slug: cs50/hello
files:
  include:
    - "*.c"
    - "*.h"
  exclude:
    - "test_*"
```

---

## 6. 依赖

```toml
[project]
dependencies = [
    "pexpect>=4.8",       # 进程控制
    "termcolor>=2.0",     # 终端着色
    "requests>=2.31",     # HTTP 客户端
    "pyyaml>=6.0",        # YAML 解析
    "attrs>=23.0",        # 数据类
    "jellyfish>=1.0",     # 字符串相似度
    "packaging>=23.0",    # 版本比较
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1",
]
```

---

## 7. 命令行接口

```bash
# 检查
bootcs check <slug>              # 远程检查
bootcs check --local <slug>      # 本地检查
bootcs check --dev <path>        # 开发模式
bootcs check --output json       # JSON 输出

# 提交
bootcs submit <slug>             # 提交代码
bootcs submit                    # 从 .bootcs.yaml 读取 slug

# 认证
bootcs login                     # 登录
bootcs logout                    # 登出
bootcs whoami                    # 显示当前用户

# 通用选项
--log-level [warning|info|debug]
--version
--help
```

---

## 8. 与 bootcs API 对接

### 8.1 认证端点

| 端点                     | 方法 | 用途             |
| ------------------------ | ---- | ---------------- |
| `/api/auth/device/code`  | POST | 启动 Device Flow |
| `/api/auth/device/token` | POST | 轮询获取 token   |
| `/api/auth/logout`       | POST | 登出             |

### 8.2 提交端点

| 端点                   | 方法 | 用途         |
| ---------------------- | ---- | ------------ |
| `/api/submit`          | POST | 提交代码     |
| `/api/submissions/:id` | GET  | 获取提交状态 |

---

## 9. 测试策略

### 9.1 单元测试

- check 模块: 使用 check50 原有测试
- submit 模块: mock API 响应
- auth 模块: mock 凭证存储

### 9.2 集成测试

- 实际运行 hello、mario-less、cash 检查
- Docker 环境测试

---

## 10. 发布计划

1. **开发阶段**: `pip install -e .` 本地安装
2. **测试阶段**: 内部 PyPI 或 TestPyPI
3. **正式发布**: PyPI `pip install bootcs`
4. **Docker**: 内置到 bootcs-ide 镜像
