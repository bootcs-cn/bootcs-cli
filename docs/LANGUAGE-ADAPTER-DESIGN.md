# 语言适配器架构设计

## 概述

语言适配器（Language Adapter）是 BootCS 检查系统的核心组件，旨在解决多语言支持的代码冗余问题。通过适配器模式，我们可以用一套统一的测试代码支持多种编程语言。

### 问题背景

在当前的 `bootcs-checks` 仓库中，存在严重的代码重复问题：

- **同一问题的不同语言实现重复率高达 90%+**
- **维护成本高**：修改测试逻辑需要同时修改 C/Java/Python 三个版本
- **扩展困难**：添加新语言需要复制大量代码
- **认知负荷重**：开发者需要理解多个几乎相同的文件

### 设计目标

1. **消除重复**：将代码重复率从 90% 降低到 10% 以下
2. **统一接口**：所有语言使用相同的测试代码
3. **易于扩展**：添加新语言支持只需 20-30 行代码
4. **类型安全**：利用 Python 类型注解提供 IDE 支持
5. **向后兼容**：现有检查可以平滑迁移
6. **性能优化**：避免不必要的编译和运行

## 架构设计

### 1. 系统架构图

```
┌─────────────────────────────────────────────────┐
│           Check Test Code (测试逻辑)             │
│  - 业务逻辑：输入/输出验证、错误处理等              │
│  - 语言无关：同样的测试逻辑适用于所有语言           │
└────────────────┬────────────────────────────────┘
                 │ 统一接口
                 ▼
┌─────────────────────────────────────────────────┐
│       Language Adapter (语言适配器)              │
│  - 抽象层：定义统一的编译/运行接口                 │
│  - 约定：默认命名和行为约定                       │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┬─────────┬──────────┐
        ▼                 ▼         ▼          ▼
┌──────────────┐  ┌──────────┐ ┌────────┐ ┌────────┐
│ C Adapter    │  │Java Adapt│ │Python  │ │Go/Rust │
│ - gcc/clang  │  │- javac   │ │- python│ │- 未来  │
│ - cs50 lib   │  │- java    │ │  3     │ │  扩展  │
└──────────────┘  └──────────┘ └────────┘ └────────┘
        │                 │         │          │
        ▼                 ▼         ▼          ▼
┌─────────────────────────────────────────────────┐
│           实际工具链 (Toolchain)                  │
│  gcc, javac, python3, go, rustc, etc.          │
└─────────────────────────────────────────────────┘
```

### 2. 核心类设计

#### 2.1 基础适配器类

```python
class LanguageAdapter(ABC):
    """语言适配器基类"""

    # 属性
    lang: str              # 当前语言 (c, java, python)
    problem: str           # 问题名称 (hello, mario, etc.)

    # 抽象方法（子类必须实现）
    @abstractmethod
    def get_source_file(self) -> str:
        """返回源文件名"""
        pass

    @abstractmethod
    def get_compile_command(self) -> Optional[list]:
        """返回编译命令（None 表示不需要编译）"""
        pass

    @abstractmethod
    def get_run_command(self, *args) -> list:
        """返回运行命令"""
        pass

    # 通用方法
    def needs_compile(self) -> bool:
        """判断是否需要编译"""
        return self.lang in ('c', 'cpp', 'java', 'rust', 'go')

    def compile(self):
        """编译源代码"""
        pass

    def run(self, *args):
        """运行程序"""
        pass
```

#### 2.2 约定式适配器（零配置）

```python
class ConventionBasedAdapter(LanguageAdapter):
    """基于约定的适配器 - 零配置"""

    # 命名约定
    NAMING_CONVENTIONS = {
        'c': '{problem}.c',
        'java': '{Problem}.java',  # 首字母大写
        'python': '{problem}.py'
    }

    # 编译约定
    COMPILE_CONVENTIONS = {
        'c': 'gcc {file} -lcs50 -o {problem}',
        'java': 'javac {file}',
        'python': None
    }

    # 运行约定
    RUN_CONVENTIONS = {
        'c': './{problem}',
        'java': 'java {Problem}',
        'python': 'python3 {file}'
    }
```

#### 2.3 项目类型适配器

```python
# 标准 I/O 项目
class StandardIOAdapter(ConventionBasedAdapter):
    """标准输入输出项目（最常见）"""
    pass

# 多文件项目
class MultiFileAdapter(LanguageAdapter):
    """多文件项目（如 speller）"""
    source_files: List[str]
    use_makefile: bool

# Web 应用项目
class WebAppAdapter(LanguageAdapter):
    """Web 应用（Flask/Express）"""
    framework: str  # 'flask' or 'express'

# SQL 数据库项目
class SQLAdapter(LanguageAdapter):
    """SQL 查询项目"""
    database: str
```

### 3. 命名约定规范

#### 3.1 文件名约定

| 语言       | 源文件           | 可执行文件             | 示例                        |
| ---------- | ---------------- | ---------------------- | --------------------------- |
| C          | `{problem}.c`    | `./{problem}`          | `hello.c` → `./hello`       |
| Java       | `{Problem}.java` | `java {Problem}`       | `Hello.java` → `java Hello` |
| Python     | `{problem}.py`   | `python3 {problem}.py` | `hello.py`                  |
| C++        | `{problem}.cpp`  | `./{problem}`          | `hello.cpp` → `./hello`     |
| Go         | `{problem}.go`   | `./{problem}`          | `hello.go` → `./hello`      |
| Rust       | `{problem}.rs`   | `./{problem}`          | `hello.rs` → `./hello`      |
| JavaScript | `{problem}.js`   | `node {problem}.js`    | `hello.js`                  |
| TypeScript | `{problem}.ts`   | `ts-node {problem}.ts` | `hello.ts`                  |

**约定规则：**

- 小写语言：文件名全小写（C, Python, Go, Rust, JS, TS）
- Java：首字母大写（Java 类名规范）
- 问题名称：使用连字符分隔（如 `mario-less`）

#### 3.2 编译约定

```python
COMPILE_CONVENTIONS = {
    'c': {
        'compiler': 'gcc',
        'flags': ['-lcs50', '-o'],
        'output': '{problem}'
    },
    'cpp': {
        'compiler': 'g++',
        'flags': ['-std=c++17', '-o'],
        'output': '{problem}'
    },
    'java': {
        'compiler': 'javac',
        'flags': [],
        'output': None  # Java 自动生成 .class
    },
    'go': {
        'compiler': 'go',
        'subcommand': 'build',
        'flags': ['-o'],
        'output': '{problem}'
    },
    'rust': {
        'compiler': 'rustc',
        'flags': ['-o'],
        'output': '{problem}'
    }
}
```

#### 3.3 运行约定

```python
RUN_CONVENTIONS = {
    'c': ['./{problem}'],
    'java': ['java', '{Problem}'],
    'python': ['python3', '{problem}.py'],
    'cpp': ['./{problem}'],
    'go': ['./{problem}'],
    'rust': ['./{problem}'],
    'javascript': ['node', '{problem}.js'],
    'typescript': ['ts-node', '{problem}.ts']
}
```

### 4. 工厂模式

```python
def create_adapter(
    problem: str = None,
    adapter_type: str = 'auto',
    **kwargs
) -> LanguageAdapter:
    """
    智能创建适配器

    Args:
        problem: 问题名称
        adapter_type: 适配器类型
            - 'auto': 自动检测（默认）
            - 'standard': 标准 I/O
            - 'multi': 多文件项目
            - 'web': Web 应用
            - 'sql': SQL 数据库
        **kwargs: 额外配置

    Returns:
        适合的适配器实例
    """
    lang = internal.get_current_language()

    # 自动检测逻辑
    if adapter_type == 'auto':
        adapter_type = detect_adapter_type(problem, lang)

    # 创建适配器
    adapters = {
        'standard': StandardIOAdapter,
        'multi': MultiFileAdapter,
        'web': WebAppAdapter,
        'sql': SQLAdapter
    }

    return adapters[adapter_type](problem, **kwargs)
```

## 使用示例

## Slug 格式规范

### 统一格式（MVP）

```bash
# ✅ 唯一支持的格式
bootcs check {courseSlug}/{stageSlug}

# 示例
bootcs check cs50/hello
bootcs check cs50/mario-less
bootcs check cs50/credit
```

**语言指定**：

- 自动检测：根据源文件扩展名（`.c`, `.java`, `.py`）
- 显式指定：`bootcs check cs50/hello -L java`

**目录结构**：

```
bootcs-checks/
├── cs50/
│   ├── hello/              # 一个问题一个目录
│   │   ├── __init__.py     # 统一检查（支持多语言）
│   │   └── .bootcs.yml
│   ├── mario-less/
│   │   ├── __init__.py
│   │   ├── .bootcs.yml
│   │   └── data/           # 共享测试数据
│   └── credit/
│       ├── __init__.py
│       └── .bootcs.yml
```

### 示例 1：Hello World（零配置）

```python
# bootcs-checks/cs50/hello/__init__.py
"""
Hello check - 支持 C, Java, Python
"""

from bootcs.check import check, exists, create_adapter

# 创建适配器（零配置，自动处理所有语言差异）
lang = create_adapter("hello")

@check()
def file_exists():
    """source file exists"""
    exists(lang.file)  # 自动：hello.c / Hello.java / hello.py

@check(file_exists)
def compiles():
    """compiles"""
    lang.compile()  # C/Java 编译，Python 跳过

@check(compiles)
def test_emma():
    """responds to name Emma"""
    lang.run().stdin("Emma").stdout("Emma").exit(0)

@check(compiles)
def test_rodrigo():
    """responds to name Rodrigo"""
    lang.run().stdin("Rodrigo").stdout("Rodrigo").exit(0)
```

**效果：**

- 从 3 个文件（270 行）减少到 1 个文件（20 行）
- 代码减少 **93%**
- 支持 C, Java, Python 三种语言

### 示例 2：Mario（稍复杂）

```python
# bootcs-checks/cs50/mario-less/__init__.py
from bootcs.check import check, create_adapter
from pathlib import Path

lang = create_adapter("mario")
data = Path(__file__).parent / "data"

@check()
def file_exists():
    exists(lang.file)

@check(file_exists)
def compiles():
    lang.compile()

@check(compiles)
def test_reject_negative():
    """rejects a height of -1"""
    lang.run().stdin("-1").reject()

@check(compiles)
def test_height_1():
    """handles a height of 1 correctly"""
    expected = (data / "1.txt").read_text()
    lang.run().stdin("1").stdout(expected).exit(0)

@check(compiles)
def test_height_2():
    """handles a height of 2 correctly"""
    expected = (data / "2.txt").read_text()
    lang.run().stdin("2").stdout(expected).exit(0)
```

**效果：**

- 从 810 行（3 语言 × 270 行）减少到 30 行
- 代码减少 **96%**
- 测试数据统一管理（`data/` 目录）

### 示例 3：Speller（多文件 + Makefile）

```python
# bootcs-checks/cs50/speller/__init__.py
from bootcs.check import check, create_adapter

lang = create_adapter(
    "speller",
    adapter_type='multi',
    source_files=['speller.c', 'dictionary.c'],
    makefile=True
)

@check()
def compiles():
    """speller compiles"""
    lang.compile()  # 自动使用 Makefile

@check(compiles)
def test_basic():
    """handles most basic words properly"""
    lang.run("basic/dict", "basic/text") \
        .stdout(open("basic/out").read()) \
        .exit(0)
```

### 示例 4：Finance（Web 应用）

```python
# bootcs-checks/cs50/finance/__init__.py
from bootcs.check import check, create_adapter

lang = create_adapter("finance", adapter_type='web', framework='flask')

@check()
def startup():
    """application starts up"""
    app = lang.run()
    app.get("/").status(200)

@check()
def register():
    """registration succeeds"""
    app = lang.run()
    app.register("user", "pass", "pass").status(200)
```

### 示例 5：Songs（SQL）

```python
# bootcs-checks/cs50/songs/__init__.py
from bootcs.check import check, create_adapter

lang = create_adapter("songs", adapter_type='sql', database='songs.db')

@check()
def test_query_1():
    """1.sql produces correct result"""
    result = lang.run("1.sql")
    assert len(result) == 58
```

## CS50 Problems 覆盖情况

### 完全支持的问题类型

| 类型       | 数量 | 示例                               | 语言支持                        |
| ---------- | ---- | ---------------------------------- | ------------------------------- |
| 标准 I/O   | ~30  | hello, caesar, cash, credit, mario | C, Java, Python, Go, Rust       |
| 命令行参数 | ~8   | substitution, wordle, bulbs        | C, Java, Python, Go, Rust       |
| 文件操作   | ~5   | filter, recover, volume            | C, Java, Python, Go, Rust       |
| 多文件编译 | ~3   | speller, inheritance               | C, Java, Go, Rust               |
| Web 应用   | ~3   | finance, birthdays, homepage       | Python (Flask), JS/TS (Express) |
| SQL 数据库 | ~4   | songs, movies, fiftyville          | SQL (所有方言)                  |

**总覆盖率：95%+**

### 需要特殊处理的问题

| 问题    | 原因                       | 解决方案          |
| ------- | -------------------------- | ----------------- |
| scratch | Scratch 项目（图形化编程） | 不需要适配器      |
| project | 自由项目                   | 手动评估          |
| tasks   | Python 特定检查            | Python 专用适配器 |

## 性能优化

### 1. 编译缓存

```python
class LanguageAdapter:
    def __init__(self):
        self._compiled = False
        self._compile_cache = {}

    def compile(self):
        """只编译一次"""
        if self._compiled:
            return

        # 检查源文件是否修改
        source_hash = self._hash_source()
        if source_hash in self._compile_cache:
            return

        self._do_compile()
        self._compiled = True
        self._compile_cache[source_hash] = True
```

### 2. 懒加载

```python
class LanguageAdapter:
    def __init__(self):
        self._c_module = None
        self._java_module = None

    @property
    def c(self):
        """懒加载 C 模块"""
        if self._c_module is None:
            from . import c
            self._c_module = c
        return self._c_module
```

### 3. 并行运行

```python
def run_checks_parallel(adapters: List[LanguageAdapter]):
    """并行运行多个语言的检查"""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(adapter.run_all_checks)
            for adapter in adapters
        ]
        results = [f.result() for f in futures]

    return results
```

## 扩展性设计

### 1. 添加新语言

添加新语言只需三步：

**步骤 1：定义约定**

```python
CONVENTIONS['go'] = {
    'extension': '.go',
    'compile': 'go build -o {problem}',
    'run': './{problem}'
}
```

**步骤 2：实现编译方法**

```python
def _compile_go(self):
    """Go 语言编译"""
    import subprocess
    subprocess.run(['go', 'build', '-o', self.problem], check=True)
```

**步骤 3：注册语言**

```python
SUPPORTED_LANGUAGES.add('go')
```

### 2. 添加新项目类型

```python
class DockerAdapter(LanguageAdapter):
    """Docker 容器项目适配器"""

    def __init__(self, problem: str, dockerfile: str = 'Dockerfile'):
        super().__init__(problem)
        self.dockerfile = dockerfile

    def compile(self):
        """构建 Docker 镜像"""
        subprocess.run(['docker', 'build', '-t', self.problem, '.'])

    def run(self, *args):
        """运行 Docker 容器"""
        return subprocess.run(['docker', 'run', self.problem, *args])
```

### 3. 插件系统

```python
class AdapterPlugin(ABC):
    """适配器插件基类"""

    @abstractmethod
    def supports(self, lang: str) -> bool:
        """是否支持该语言"""
        pass

    @abstractmethod
    def create_adapter(self, problem: str) -> LanguageAdapter:
        """创建适配器"""
        pass

# 注册插件
registry = AdapterPluginRegistry()
registry.register(GoAdapterPlugin())
registry.register(RustAdapterPlugin())
```

## 类型安全

### 1. 类型注解

```python
from typing import Optional, List, Callable

class LanguageAdapter:
    def get_source_file(self) -> str:
        """返回源文件名"""
        ...

    def compile(self) -> None:
        """编译源代码"""
        ...

    def run(self, *args: str) -> 'RunResult':
        """运行程序并返回结果"""
        ...
```

### 2. Protocol（Python 3.8+）

```python
from typing import Protocol

class Compilable(Protocol):
    """可编译的接口"""
    def compile(self) -> None: ...

class Runnable(Protocol):
    """可运行的接口"""
    def run(self, *args: str) -> 'RunResult': ...

def check_program(adapter: Compilable & Runnable):
    """检查程序（类型安全）"""
    adapter.compile()
    adapter.run()
```

### 3. 运行时类型检查

```python
from typing import get_type_hints

def validate_adapter(adapter: LanguageAdapter):
    """验证适配器实现"""
    required_methods = ['get_source_file', 'compile', 'run']

    for method in required_methods:
        if not hasattr(adapter, method):
            raise TypeError(f"Adapter missing method: {method}")
```

## 错误处理

### 1. 编译错误

```python
class CompilationError(Exception):
    """编译错误"""
    def __init__(self, message: str, stderr: str, exitcode: int):
        self.message = message
        self.stderr = stderr
        self.exitcode = exitcode
        super().__init__(message)

def compile(self):
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        raise CompilationError(
            f"Compilation failed for {self.get_source_file()}",
            e.stderr.decode(),
            e.returncode
        )
```

### 2. 运行时错误

```python
class RuntimeError(Exception):
    """运行时错误"""
    def __init__(self, message: str, stdout: str, stderr: str):
        self.message = message
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(message)
```

### 3. 环境检查

```python
def check_environment(self):
    """检查编译器/解释器是否可用"""
    import shutil

    tools = {
        'c': 'gcc',
        'java': 'javac',
        'python': 'python3',
        'go': 'go',
        'rust': 'rustc'
    }

    tool = tools.get(self.lang)
    if tool and not shutil.which(tool):
        raise EnvironmentError(
            f"{tool} not found. Please install {self.lang} toolchain."
        )
```

## 测试策略

### 1. 单元测试

```python
class TestLanguageAdapter(unittest.TestCase):
    def test_c_adapter(self):
        adapter = create_adapter("hello", lang='c')
        self.assertEqual(adapter.get_source_file(), "hello.c")
        self.assertEqual(adapter.get_run_command(), ["./hello"])

    def test_java_adapter(self):
        adapter = create_adapter("hello", lang='java')
        self.assertEqual(adapter.get_source_file(), "Hello.java")
        self.assertEqual(adapter.get_run_command(), ["java", "Hello"])
```

### 2. 集成测试

```python
def test_hello_check():
    """测试 hello 检查在所有语言上运行"""
    for lang in ['c', 'java', 'python']:
        with setup_language(lang):
            adapter = create_adapter("hello")
            adapter.compile()
            result = adapter.run().stdin("World")
            assert "World" in result.stdout
```

### 3. 性能测试

```python
def test_compilation_cache():
    """测试编译缓存"""
    adapter = create_adapter("mario")

    start = time.time()
    adapter.compile()
    first_time = time.time() - start

    start = time.time()
    adapter.compile()  # 应该使用缓存
    second_time = time.time() - start

    assert second_time < first_time * 0.1  # 缓存应该快 10 倍以上
```

## 文档和示例

### 1. API 文档

使用 Sphinx 生成完整的 API 文档：

- 每个适配器类的详细说明
- 方法参数和返回值
- 使用示例和最佳实践

### 2. 迁移指南

提供从旧代码迁移到语言适配器的指南：

- 逐步迁移步骤
- 常见问题和解决方案
- 迁移工具脚本

### 3. 语言扩展指南

详细说明如何添加新语言支持：

- 必要的步骤
- 代码模板
- 测试要求

## 未来规划

### Phase 1: 基础架构（2 周）

- [ ] 实现基础适配器类
- [ ] 实现 C/Java/Python 支持
- [ ] 单元测试覆盖 90%+

### Phase 2: 迁移 Hello（1 周）

- [ ] 迁移 hello 检查
- [ ] 测试所有语言
- [ ] 验证性能

### Phase 3: 批量迁移（4 周）

- [ ] 迁移所有标准 I/O 问题
- [ ] 迁移多文件问题
- [ ] 迁移 Web 和 SQL 问题

### Phase 4: 扩展支持（2 周）

- [ ] 添加 Go 支持
- [ ] 添加 Rust 支持
- [ ] 添加 TypeScript 支持

### Phase 5: 优化和文档（2 周）

- [ ] 性能优化
- [ ] 完善文档
- [ ] 编写迁移工具

## 总结

语言适配器架构提供了：

1. **高度抽象**：统一的接口隐藏语言差异
2. **零配置启动**：约定优于配置，开箱即用
3. **渐进式复杂度**：从简单到复杂平滑过渡
4. **强类型支持**：利用 Python 类型系统
5. **易于扩展**：添加新语言非常简单
6. **性能优化**：编译缓存和懒加载

这是一个**面向未来、可持续发展**的架构设计，将大幅降低维护成本，提升开发效率。
