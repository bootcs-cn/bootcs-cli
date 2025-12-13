# bootcs-cli-v2

BootCS 命令行工具 - Python 版本

基于 [check50](https://github.com/cs50/check50) 和 [lib50](https://github.com/cs50/lib50) 扩展开发，用于 BootCS 平台的代码检查和提交。

> **注意**: 本项目与 CS50 课程本身没有直接关系，仅复用了 check50/lib50 的开源代码。

## 许可证

本项目基于 GPL-3.0 许可证发布，遵循 check50/lib50 的许可证要求。

## 安装

```bash
# 开发模式
pip install -e .

# 正式安装
pip install bootcs
```

## 使用

```bash
# 检查代码
bootcs check cs50/hello
bootcs check --dev ./checks/hello  # 开发模式
bootcs check --local cs50/hello    # 本地运行

# 提交代码
bootcs submit cs50/hello

# 登录/登出
bootcs login
bootcs logout
bootcs whoami
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black bootcs/
ruff check bootcs/
```

## 文档

- [设计文档](DESIGN.md)
- [落地路线图](ROADMAP.md)
