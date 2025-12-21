# 语言适配器实施方案

## 实施概述

本文档描述语言适配器的具体实施步骤、代码结构、迁移策略和最佳实践。

## MVP 设计原则

### 简化优先

1. **统一 Slug 格式**：只支持 `{courseSlug}/{stageSlug}`
2. **一致的目录结构**：一个问题一个目录
3. **无过渡期**：直接使用新架构
4. **自动化优先**：语言自动检测

### Slug 格式

```bash
# ✅ 唯一支持
bootcs check cs50/hello
bootcs check cs50/mario-less

# ❌ 不支持
bootcs check cs50/c/hello     # 废弃
bootcs check cs50/java/hello  # 废弃
```

### Checks 目录结构

```
bootcs-checks/
├── cs50/
│   ├── hello/                # 统一目录
│   │   ├── __init__.py       # 多语言支持
│   │   └── .bootcs.yml
│   └── mario-less/
│       ├── __init__.py
│       ├── .bootcs.yml
│       └── data/             # 共享数据
```

## 目录结构

```
bootcs-cli/
├── bootcs/
│   ├── check/
│   │   ├── __init__.py
│   │   ├── _api.py                    # 现有 API（run, exists 等）
│   │   ├── runner.py                  # 检查运行器
│   │   ├── internal.py                # 内部状态管理
│   │   ├── c.py                       # C 语言支持
│   │   ├── java.py                    # Java 语言支持
│   │   └── adapters/                  # 新增：适配器模块
│   │       ├── __init__.py            # 导出公共接口
│   │       ├── base.py                # 基础适配器类
│   │       ├── conventions.py         # 命名约定定义
│   │       ├── compiled.py            # 编译型语言适配器
│   │       ├── interpreted.py         # 解释型语言适配器
│   │       ├── multi_file.py          # 多文件项目适配器
│   │       ├── web.py                 # Web 应用适配器
│   │       ├── sql.py                 # SQL 数据库适配器
│   │       └── factory.py             # 工厂函数
│   └── __main__.py                    # CLI 入口
├── tests/
│   └── adapters/                      # 适配器测试
│       ├── test_base.py
│       ├── test_compiled.py
│       ├── test_interpreted.py
│       └── test_integration.py
└── docs/
    ├── LANGUAGE-ADAPTER-DESIGN.md     # 设计文档
    ├── LANGUAGE-ADAPTER-IMPLEMENTATION.md  # 本文档
    └── LANGUAGE-EXTENSION-GUIDE.md    # 扩展指南

bootcs-checks/
├── cs50/
│   ├── hello/                         # 迁移后的结构
│   │   ├── __init__.py                # 统一的检查（支持多语言）
│   │   └── .bootcs.yml                # 配置文件
│   ├── mario-less/
│   │   ├── __init__.py
│   │   ├── .bootcs.yml
│   │   └── data/                      # 共享测试数据
│   │       ├── 1.txt
│   │       ├── 2.txt
│   │       └── 8.txt
│   └── ... (其他问题)
└── shared/                            # 共享资源
    ├── helpers.py                     # 共享辅助函数
    └── validators.py                  # 共享验证器
```

## Phase 1: 基础架构（第 1-2 周）

### 1.1 创建基础适配器类

**文件：`bootcs/check/adapters/base.py`**

```python
"""
语言适配器基类
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any
from pathlib import Path
from .. import internal


class LanguageAdapter(ABC):
    """
    语言适配器基类

    所有语言适配器的抽象基类，定义了统一的接口。
    """

    # 支持的语言列表
    SUPPORTED_LANGUAGES = {
        'c', 'cpp', 'java', 'python',
        'javascript', 'typescript', 'go', 'rust'
    }

    def __init__(self, problem: str = None):
        """
        初始化适配器

        Args:
            problem: 问题名称（如 "hello", "mario"）
                    如果不提供，从 internal 上下文自动获取
        """
        self.lang = internal.get_current_language()
        self.problem = problem or internal.get_problem_name()

        # 验证语言支持
        if self.lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {self.lang}")

        # 内部状态
        self._compiled = False
        self._compile_cache = {}

    # ============ 抽象方法（子类必须实现） ============

    @abstractmethod
    def get_source_file(self) -> str:
        """
        返回源文件名

        Returns:
            源文件名（如 "hello.c", "Hello.java", "hello.py"）
        """
        pass

    @abstractmethod
    def get_compile_command(self) -> Optional[List[str]]:
        """
        返回编译命令

        Returns:
            编译命令列表，None 表示不需要编译
        """
        pass

    @abstractmethod
    def get_run_command(self, *args: str) -> List[str]:
        """
        返回运行命令

        Args:
            *args: 传递给程序的命令行参数

        Returns:
            运行命令列表
        """
        pass

    # ============ 通用方法 ============

    def needs_compile(self) -> bool:
        """
        判断是否需要编译

        Returns:
            True 表示需要编译
        """
        return self.lang in ('c', 'cpp', 'java', 'rust', 'go')

    def compile(self) -> None:
        """
        编译源代码

        - 如果语言不需要编译，直接返回
        - 使用缓存避免重复编译
        - 调用语言特定的编译逻辑

        Raises:
            CompilationError: 编译失败
        """
        if not self.needs_compile():
            return

        # 如果已经编译过，直接返回
        if self._compiled:
            return

        # 执行编译
        self._do_compile()
        self._compiled = True

    def _do_compile(self) -> None:
        """执行实际的编译（子类可以重写）"""
        cmd = self.get_compile_command()
        if not cmd:
            return

        import subprocess
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            internal.log(f"Compilation successful: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            raise CompilationError(
                f"Compilation failed for {self.get_source_file()}",
                e.stderr,
                e.returncode
            )

    def run(self, *args: str):
        """
        运行程序

        Args:
            *args: 传递给程序的命令行参数

        Returns:
            RunResult 对象（来自 bootcs.check.run）
        """
        from .._api import run as run_impl

        cmd = self.get_run_command(*args)
        return run_impl(*cmd)

    # ============ 便捷属性 ============

    @property
    def file(self) -> str:
        """源文件名（快捷方式）"""
        return self.get_source_file()

    @property
    def executable(self) -> str:
        """可执行文件路径"""
        if self.lang == 'c' or self.lang == 'cpp':
            return f"./{self.problem}"
        elif self.lang == 'java':
            return self.problem.capitalize()
        elif self.lang in ('go', 'rust'):
            return f"./{self.problem}"
        return ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(problem={self.problem!r}, lang={self.lang!r})"


class CompilationError(Exception):
    """编译错误异常"""

    def __init__(self, message: str, stderr: str, exitcode: int):
        self.message = message
        self.stderr = stderr
        self.exitcode = exitcode
        super().__init__(message)
```

### 1.2 定义命名约定

**文件：`bootcs/check/adapters/conventions.py`**

```python
"""
命名约定定义
"""

from typing import Dict, Any


class NamingConventions:
    """命名约定配置"""

    # 文件名模板
    FILENAME_PATTERNS = {
        'c': '{problem}.c',
        'cpp': '{problem}.cpp',
        'java': '{Problem}.java',        # 首字母大写
        'python': '{problem}.py',
        'javascript': '{problem}.js',
        'typescript': '{problem}.ts',
        'go': '{problem}.go',
        'rust': '{problem}.rs',
        'sql': '{problem}.sql'
    }

    # 编译配置
    COMPILE_CONFIG = {
        'c': {
            'compiler': 'gcc',
            'flags': ['-lcs50', '-o', '{problem}'],
            'output': '{problem}'
        },
        'cpp': {
            'compiler': 'g++',
            'flags': ['-std=c++17', '-o', '{problem}'],
            'output': '{problem}'
        },
        'java': {
            'compiler': 'javac',
            'flags': [],
            'output': None  # Java 自动生成 .class 文件
        },
        'go': {
            'compiler': 'go',
            'subcommand': 'build',
            'flags': ['-o', '{problem}'],
            'output': '{problem}'
        },
        'rust': {
            'compiler': 'rustc',
            'flags': ['-o', '{problem}'],
            'output': '{problem}'
        },
        'python': None,      # 不需要编译
        'javascript': None,  # 不需要编译
        'typescript': {      # TypeScript 可选编译
            'compiler': 'tsc',
            'flags': [],
            'output': None
        }
    }

    # 运行配置
    RUN_CONFIG = {
        'c': ['./{problem}'],
        'cpp': ['./{problem}'],
        'java': ['java', '{Problem}'],
        'python': ['python3', '{problem}.py'],
        'javascript': ['node', '{problem}.js'],
        'typescript': ['ts-node', '{problem}.ts'],
        'go': ['./{problem}'],
        'rust': ['./{problem}']
    }

    @classmethod
    def get_filename(cls, lang: str, problem: str) -> str:
        """
        获取源文件名

        Args:
            lang: 语言名称
            problem: 问题名称

        Returns:
            源文件名
        """
        pattern = cls.FILENAME_PATTERNS.get(lang)
        if not pattern:
            raise ValueError(f"No filename pattern for language: {lang}")

        return pattern.format(
            problem=problem,
            Problem=problem.capitalize()
        )

    @classmethod
    def get_compile_command(cls, lang: str, problem: str) -> list:
        """
        获取编译命令

        Args:
            lang: 语言名称
            problem: 问题名称

        Returns:
            编译命令列表
        """
        config = cls.COMPILE_CONFIG.get(lang)
        if not config:
            return None

        cmd = [config['compiler']]
        if 'subcommand' in config:
            cmd.append(config['subcommand'])

        # 添加源文件
        cmd.append(cls.get_filename(lang, problem))

        # 添加编译标志
        flags = [
            flag.format(problem=problem, Problem=problem.capitalize())
            for flag in config.get('flags', [])
        ]
        cmd.extend(flags)

        return cmd

    @classmethod
    def get_run_command(cls, lang: str, problem: str, *args: str) -> list:
        """
        获取运行命令

        Args:
            lang: 语言名称
            problem: 问题名称
            *args: 命令行参数

        Returns:
            运行命令列表
        """
        config = cls.RUN_CONFIG.get(lang)
        if not config:
            raise ValueError(f"No run config for language: {lang}")

        cmd = [
            part.format(
                problem=problem,
                Problem=problem.capitalize()
            )
            for part in config
        ]
        cmd.extend(args)

        return cmd
```

### 1.3 实现约定式适配器

**文件：`bootcs/check/adapters/compiled.py`**

```python
"""
编译型语言适配器
"""

from typing import Optional, List
from .base import LanguageAdapter
from .conventions import NamingConventions


class ConventionBasedAdapter(LanguageAdapter):
    """
    基于约定的适配器

    使用标准命名约定，适用于大多数简单项目。
    零配置，开箱即用。
    """

    def get_source_file(self) -> str:
        """根据约定返回源文件名"""
        return NamingConventions.get_filename(self.lang, self.problem)

    def get_compile_command(self) -> Optional[List[str]]:
        """根据约定返回编译命令"""
        return NamingConventions.get_compile_command(self.lang, self.problem)

    def get_run_command(self, *args: str) -> List[str]:
        """根据约定返回运行命令"""
        return NamingConventions.get_run_command(self.lang, self.problem, *args)


class CompiledLanguageAdapter(ConventionBasedAdapter):
    """
    编译型语言适配器

    支持 C, C++, Java, Go, Rust 等编译型语言。
    提供特定语言的优化编译逻辑。
    """

    def _do_compile(self) -> None:
        """使用语言特定的编译器"""
        if self.lang == 'c':
            self._compile_c()
        elif self.lang == 'cpp':
            self._compile_cpp()
        elif self.lang == 'java':
            self._compile_java()
        elif self.lang == 'go':
            self._compile_go()
        elif self.lang == 'rust':
            self._compile_rust()
        else:
            # 回退到通用编译
            super()._do_compile()

    def _compile_c(self) -> None:
        """C 语言编译（使用 bootcs 内置支持）"""
        from .. import c
        source = self.get_source_file()
        c.compile(source, lcs50=True)

    def _compile_cpp(self) -> None:
        """C++ 编译"""
        import subprocess
        cmd = self.get_compile_command()
        subprocess.run(cmd, check=True)

    def _compile_java(self) -> None:
        """Java 编译（使用 bootcs 内置支持）"""
        from .. import java
        source = self.get_source_file()
        java.compile(source)

    def _compile_go(self) -> None:
        """Go 编译"""
        import subprocess
        subprocess.run(['go', 'build', '-o', self.problem], check=True)

    def _compile_rust(self) -> None:
        """Rust 编译"""
        import subprocess
        source = self.get_source_file()
        subprocess.run(['rustc', source, '-o', self.problem], check=True)
```

### 1.4 实现工厂函数

**文件：`bootcs/check/adapters/factory.py`**

```python
"""
适配器工厂函数
"""

from typing import Optional
from .base import LanguageAdapter
from .compiled import CompiledLanguageAdapter
from .interpreted import InterpretedLanguageAdapter
from .. import internal


def create_adapter(
    problem: str = None,
    adapter_type: str = 'auto',
    **kwargs
) -> LanguageAdapter:
    """
    智能创建语言适配器

    Args:
        problem: 问题名称（如 "hello", "mario"）
                如果不提供，从上下文自动获取
        adapter_type: 适配器类型
            - 'auto': 自动检测（默认）
            - 'compiled': 编译型语言
            - 'interpreted': 解释型语言
            - 'multi': 多文件项目
            - 'web': Web 应用
            - 'sql': SQL 数据库
        **kwargs: 传递给适配器构造函数的额外参数

    Returns:
        适合的适配器实例

    Examples:
        >>> # 零配置，自动检测
        >>> lang = create_adapter("hello")

        >>> # 指定适配器类型
        >>> lang = create_adapter("speller", adapter_type='multi',
        ...                       source_files=['speller.c', 'dictionary.c'])
    """
    lang = internal.get_current_language()

    # 自动检测适配器类型
    if adapter_type == 'auto':
        adapter_type = _detect_adapter_type(lang)

    # 创建对应的适配器
    adapters = {
        'compiled': CompiledLanguageAdapter,
        'interpreted': InterpretedLanguageAdapter,
        'multi': MultiFileAdapter,
        'web': WebAppAdapter,
        'sql': SQLAdapter,
    }

    adapter_class = adapters.get(adapter_type)
    if not adapter_class:
        raise ValueError(f"Unknown adapter type: {adapter_type}")

    return adapter_class(problem, **kwargs)


def _detect_adapter_type(lang: str) -> str:
    """
    自动检测适配器类型

    Args:
        lang: 语言名称

    Returns:
        适配器类型字符串
    """
    if lang in ('c', 'cpp', 'java', 'go', 'rust'):
        return 'compiled'
    elif lang in ('python', 'javascript', 'typescript'):
        return 'interpreted'
    elif lang == 'sql':
        return 'sql'
    else:
        # 默认使用编译型适配器
        return 'compiled'
```

### 1.5 导出公共接口

**文件：`bootcs/check/adapters/__init__.py`**

```python
"""
语言适配器模块

提供统一的多语言支持接口。
"""

from .base import LanguageAdapter, CompilationError
from .compiled import CompiledLanguageAdapter, ConventionBasedAdapter
from .interpreted import InterpretedLanguageAdapter
from .factory import create_adapter

__all__ = [
    # 基础类
    'LanguageAdapter',
    'CompilationError',

    # 具体适配器
    'CompiledLanguageAdapter',
    'InterpretedLanguageAdapter',
    'ConventionBasedAdapter',

    # 工厂函数
    'create_adapter',
]
```

### 1.6 集成到 check 模块

**文件：`bootcs/check/__init__.py`（修改）**

```python
"""
BootCS Check API
"""

# 现有导出
from ._api import (
    check,
    exists,
    run,
    include,
    log,
    data,
    hash,
    # ... 其他现有函数
)

# 新增：语言适配器
from .adapters import (
    create_adapter,
    LanguageAdapter,
    CompilationError,
)

__all__ = [
    # 现有 API
    'check',
    'exists',
    'run',
    'include',
    'log',
    'data',
    'hash',

    # 新增：适配器
    'create_adapter',
    'LanguageAdapter',
    'CompilationError',
]
```

## Phase 2: 迁移 Hello 示例（第 3 周）

### 2.1 新的目录结构

```bash
# 旧结构（废弃）
bootcs-checks/
├── cs50/
│   ├── c/
│   │   └── hello/__init__.py
│   ├── java/
│   │   └── hello/__init__.py
│   └── python/
│       └── hello/__init__.py

# ✅ 新结构（MVP）
bootcs-checks/
├── cs50/
│   └── hello/
│       ├── __init__.py       # 统一检查
│       └── .bootcs.yml
```

### 2.2 创建统一的 Hello 检查

**文件：`bootcs-checks/cs50/hello/__init__.py`（新）**

```python
"""
Hello check - 支持 C, Java, Python

零配置示例，展示语言适配器的基本用法。
"""

from bootcs.check import check, exists, create_adapter

# 创建语言适配器（零配置）
lang = create_adapter("hello")

@check()
def file_exists():
    """source file exists"""
    exists(lang.file)


@check(file_exists)
def compiles():
    """compiles"""
    lang.compile()


@check(compiles)
def emma():
    """responds to name Emma"""
    lang.run().stdin("Emma").stdout("Emma").exit(0)


@check(compiles)
def rodrigo():
    """responds to name Rodrigo"""
    lang.run().stdin("Rodrigo").stdout("Rodrigo").exit(0)
```

### 2.3 测试所有语言

```bash
# 测试 C（自动检测 hello.c）
cd /path/to/student/hello-c
bootcs check cs50/hello

# 测试 Java（自动检测 Hello.java）
cd /path/to/student/hello-java
bootcs check cs50/hello

# 或显式指定语言
bootcs check cs50/hello -L java

# 测试 Python（自动检测 hello.py）
cd /path/to/student/hello-python
bootcs check cs50/hello
```

### 2.3 性能对比

| 指标     | 旧方案     | 新方案    | 改进   |
| -------- | ---------- | --------- | ------ |
| 文件数   | 3 个       | 1 个      | ↓ 67%  |
| 代码行数 | 90 行      | 20 行     | ↓ 78%  |
| 维护成本 | 修改 3 处  | 修改 1 处 | ↓ 67%  |
| 添加语言 | 复制 30 行 | 0 行      | ↓ 100% |

## Phase 3: 批量迁移（第 4-7 周）

### 3.1 迁移优先级

**Week 4：标准 I/O 问题**

- hello ✅（已完成）
- cash
- credit
- readability
- scrabble

**Week 5：Mario 系列**

- mario-less
- mario-more
- 共享 pyramid 验证器

**Week 6：复杂问题**

- caesar
- substitution
- bulbs
- wordle

**Week 7：特殊项目**

- speller（多文件 + Makefile）
- filter（图像处理）
- recover（文件 I/O）

### 3.2 迁移脚本

**文件：`scripts/migrate_check.py`**

```python
#!/usr/bin/env python3
"""
检查迁移脚本

自动将旧格式的检查迁移到新的语言适配器格式。
"""

import sys
import re
from pathlib import Path


def migrate_check(old_dir: Path, new_dir: Path, problem: str):
    """迁移一个检查"""

    # 读取 C 版本作为模板（最完整）
    c_file = old_dir / 'c' / problem / '__init__.py'
    if not c_file.exists():
        print(f"Error: {c_file} not found")
        return

    content = c_file.read_text()

    # 替换导入
    content = re.sub(
        r'from check50 import \*',
        'from bootcs.check import check, exists, create_adapter',
        content
    )

    # 添加适配器创建
    adapter_line = f'\nlang = create_adapter("{problem}")\n\n'
    content = content.replace(
        '@check50.check()',
        adapter_line + '@check()',
        1  # 只替换第一个
    )

    # 替换语言特定的编译/运行
    content = re.sub(
        r'check50\.c\.compile\([^)]+\)',
        'lang.compile()',
        content
    )

    content = re.sub(
        r'check50\.run\("\./' + problem + r'"\)',
        'lang.run()',
        content
    )

    # 创建新目录
    new_check_dir = new_dir / problem
    new_check_dir.mkdir(parents=True, exist_ok=True)

    # 写入新文件
    new_file = new_check_dir / '__init__.py'
    new_file.write_text(content)

    print(f"✓ Migrated {problem}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: migrate_check.py <problem>")
        sys.exit(1)

    problem = sys.argv[1]
    old_dir = Path('bootcs-checks/cs50')
    new_dir = Path('bootcs-checks-new/cs50')

    migrate_check(old_dir, new_dir, problem)
```

### 3.3 验证脚本

**文件：`scripts/verify_migration.py`**

```python
#!/usr/bin/env python3
"""
验证迁移正确性

对比旧版和新版检查的输出是否一致。
"""

import subprocess
import sys
from pathlib import Path


def run_check(check_path: str, student_dir: Path, lang: str) -> dict:
    """运行检查并返回结果"""
    result = subprocess.run(
        ['bootcs', 'check', check_path, '-L', lang, '-o', 'json'],
        cwd=student_dir,
        capture_output=True,
        text=True
    )

    import json
    return json.loads(result.stdout)


def compare_results(old_result: dict, new_result: dict) -> bool:
    """比较两个结果是否一致"""
    # 比较通过的检查数量
    old_passed = sum(1 for r in old_result if r['passed'])
    new_passed = sum(1 for r in new_result if r['passed'])

    if old_passed != new_passed:
        print(f"✗ Passed count mismatch: {old_passed} vs {new_passed}")
        return False

    # 比较每个检查的结果
    for old, new in zip(old_result, new_result):
        if old['name'] != new['name']:
            print(f"✗ Check name mismatch: {old['name']} vs {new['name']}")
            return False

        if old['passed'] != new['passed']:
            print(f"✗ Check {old['name']} result mismatch")
            return False

    return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: verify_migration.py <problem> <student_dir>")
        sys.exit(1)

    problem = sys.argv[1]
    student_dir = Path(sys.argv[2])

    for lang in ['c', 'java', 'python']:
        print(f"Testing {problem} with {lang}...")

        old = run_check(f'cs50/{lang}/{problem}', student_dir, lang)
        new = run_check(f'cs50/{problem}', student_dir, lang)

        if compare_results(old, new):
            print(f"✓ {lang} passed")
        else:
            print(f"✗ {lang} failed")
            sys.exit(1)

    print(f"\n✓ All languages passed for {problem}")
```

## Phase 4: 扩展支持（第 8-9 周）

### 4.1 添加 Go 支持

```python
# 在 conventions.py 中添加
FILENAME_PATTERNS['go'] = '{problem}.go'
COMPILE_CONFIG['go'] = {
    'compiler': 'go',
    'subcommand': 'build',
    'flags': ['-o', '{problem}'],
    'output': '{problem}'
}
RUN_CONFIG['go'] = ['./{problem}']

# 在 compiled.py 中添加
def _compile_go(self) -> None:
    """Go 编译"""
    import subprocess
    subprocess.run(['go', 'build', '-o', self.problem], check=True)
```

### 4.2 添加 TypeScript 支持

```python
# 创建 interpreted.py
class InterpretedLanguageAdapter(ConventionBasedAdapter):
    """解释型语言适配器"""

    def compile(self) -> None:
        """TypeScript 需要可选编译"""
        if self.lang == 'typescript':
            import subprocess
            subprocess.run(['tsc', self.get_source_file()], check=True)
```

## Phase 5: 优化和文档（第 10-11 周）

### 5.1 性能优化

**编译缓存：**

```python
class LanguageAdapter:
    def _get_source_hash(self) -> str:
        """计算源文件哈希"""
        import hashlib
        content = Path(self.get_source_file()).read_bytes()
        return hashlib.sha256(content).hexdigest()

    def compile(self) -> None:
        """带缓存的编译"""
        if not self.needs_compile():
            return

        source_hash = self._get_source_hash()
        cache_file = Path('.bootcs_cache') / f'{source_hash}.compiled'

        if cache_file.exists():
            internal.log("Using cached compilation")
            return

        self._do_compile()
        cache_file.parent.mkdir(exist_ok=True)
        cache_file.touch()
```

### 5.2 完善文档

- API 文档（Sphinx）
- 使用指南
- 迁移指南
- 最佳实践

### 5.3 编写测试

```python
# tests/adapters/test_integration.py
def test_hello_all_languages():
    """测试 hello 检查在所有语言上工作"""
    for lang in ['c', 'java', 'python']:
        with setup_test_env(lang):
            adapter = create_adapter("hello")
            adapter.compile()
            result = adapter.run().stdin("World")
            assert "World" in result.stdout
```

## 回滚策略

如果遇到问题，可以快速回滚：

1. **保留旧代码**：不删除原有的语言特定检查
2. **渐进式迁移**：一次只迁移一个问题
3. **A/B 测试**：同时运行新旧两种检查对比
4. **备份数据**：Git 标签和分支管理

## 度量指标

跟踪以下指标评估迁移效果：

| 指标       | 目标  | 当前 |
| ---------- | ----- | ---- |
| 代码行数   | ↓ 80% | -    |
| 文件数量   | ↓ 67% | -    |
| 测试覆盖率 | > 90% | -    |
| 迁移进度   | 100%  | 0%   |
| 性能影响   | < 5%  | -    |
| Bug 数量   | 0     | -    |

## 总结

通过系统化的实施方案，我们可以：

1. **降低维护成本** - 代码量减少 80%+
2. **提升扩展性** - 添加新语言只需数小时
3. **保证质量** - 完整的测试和验证流程
4. **平滑过渡** - 渐进式迁移，风险可控

语言适配器将成为 BootCS 项目的核心基础设施，支撑未来的长期发展。
