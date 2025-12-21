# 语言扩展指南

## 概述

本指南介绍如何为 BootCS 语言适配器添加新的编程语言支持。通过遵循本指南，您可以在几小时内完成一门新语言的集成。

## 支持级别

BootCS 定义了三个语言支持级别：

### Tier 1：完全支持

- **特征**：内置编译/运行支持，完整测试覆盖
- **示例**：C, Java, Python
- **要求**：
  - 核心团队维护
  - 90%+ 问题兼容
  - 完整文档和示例
  - CI/CD 测试

### Tier 2：实验性支持

- **特征**：基本功能可用，部分问题支持
- **示例**：Go, Rust, TypeScript
- **要求**：
  - 社区维护
  - 50%+ 问题兼容
  - 基础文档
  - 手动测试

### Tier 3：社区支持

- **特征**：通过插件或配置支持
- **示例**：Julia, Kotlin, Swift
- **要求**：
  - 第三方维护
  - 按需兼容
  - 社区文档

## 快速开始：添加 Go 支持

让我们通过一个完整的示例来添加 Go 语言支持。

### 步骤 1：定义命名约定

**文件：`bootcs/check/adapters/conventions.py`**

```python
# 添加到 FILENAME_PATTERNS
FILENAME_PATTERNS = {
    # ... 现有语言
    'go': '{problem}.go',  # 新增
}

# 添加到 COMPILE_CONFIG
COMPILE_CONFIG = {
    # ... 现有语言
    'go': {  # 新增
        'compiler': 'go',
        'subcommand': 'build',
        'flags': ['-o', '{problem}'],
        'output': '{problem}'
    },
}

# 添加到 RUN_CONFIG
RUN_CONFIG = {
    # ... 现有语言
    'go': ['./{problem}'],  # 新增
}
```

### 步骤 2：实现编译逻辑

**文件：`bootcs/check/adapters/compiled.py`**

```python
class CompiledLanguageAdapter(ConventionBasedAdapter):
    # ... 现有代码

    def _do_compile(self) -> None:
        """使用语言特定的编译器"""
        # ... 现有代码
        elif self.lang == 'go':
            self._compile_go()  # 新增
        else:
            super()._do_compile()

    def _compile_go(self) -> None:  # 新增方法
        """Go 语言编译"""
        import subprocess
        from .. import internal

        # 构建命令
        cmd = ['go', 'build', '-o', self.problem, self.get_source_file()]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=internal.run_dir
            )
            internal.log(f"Go compilation successful: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            raise CompilationError(
                f"Go compilation failed for {self.get_source_file()}",
                e.stderr,
                e.returncode
            )
```

### 步骤 3：注册语言

**文件：`bootcs/check/adapters/base.py`**

```python
class LanguageAdapter(ABC):
    # 支持的语言列表
    SUPPORTED_LANGUAGES = {
        'c', 'cpp', 'java', 'python',
        'javascript', 'typescript',
        'go',  # 新增
        'rust'
    }
```

### 步骤 4：更新自动检测

**文件：`bootcs/check/adapters/factory.py`**

```python
def _detect_adapter_type(lang: str) -> str:
    """自动检测适配器类型"""
    if lang in ('c', 'cpp', 'java', 'go', 'rust'):  # 添加 'go'
        return 'compiled'
    # ... 其他代码
```

### 步骤 5：添加测试

**文件：`tests/adapters/test_go.py`（新建）**

```python
"""Go 语言适配器测试"""

import unittest
from pathlib import Path
from bootcs.check.adapters import create_adapter
from bootcs.check import internal


class TestGoAdapter(unittest.TestCase):
    """测试 Go 语言适配器"""

    def setUp(self):
        """设置测试环境"""
        internal._current_language = 'go'
        self.adapter = create_adapter('hello')

    def test_source_file(self):
        """测试源文件名"""
        self.assertEqual(self.adapter.get_source_file(), 'hello.go')

    def test_compile_command(self):
        """测试编译命令"""
        cmd = self.adapter.get_compile_command()
        self.assertEqual(cmd[0], 'go')
        self.assertEqual(cmd[1], 'build')
        self.assertIn('hello.go', cmd)

    def test_run_command(self):
        """测试运行命令"""
        cmd = self.adapter.get_run_command('arg1', 'arg2')
        self.assertEqual(cmd[0], './hello')
        self.assertEqual(cmd[1:], ['arg1', 'arg2'])

    def test_needs_compile(self):
        """测试是否需要编译"""
        self.assertTrue(self.adapter.needs_compile())


class TestGoIntegration(unittest.TestCase):
    """Go 语言集成测试"""

    def test_hello_world(self):
        """测试 Hello World 程序"""
        # 创建测试目录
        test_dir = Path('/tmp/test_go_hello')
        test_dir.mkdir(exist_ok=True)

        # 写入 Go 代码
        go_code = '''
package main

import (
    "fmt"
    "bufio"
    "os"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    scanner.Scan()
    name := scanner.Text()
    fmt.Println(name)
}
'''
        (test_dir / 'hello.go').write_text(go_code)

        # 切换到测试目录
        import os
        old_cwd = os.getcwd()
        os.chdir(test_dir)

        try:
            # 创建适配器并编译
            internal._current_language = 'go'
            adapter = create_adapter('hello')
            adapter.compile()

            # 运行程序
            result = adapter.run().stdin('World')
            self.assertEqual(result.stdout.strip(), 'World')
        finally:
            os.chdir(old_cwd)


if __name__ == '__main__':
    unittest.main()
```

### 步骤 6：编写文档

**文件：`docs/languages/go.md`（新建）**

````markdown
# Go 语言支持

## 概述

BootCS 支持 Go 语言进行编程作业的检查和提交。

## 环境要求

- Go 1.16 或更高版本
- 推荐使用 Go 1.21+

## 安装 Go

### macOS

```bash
brew install go
```
````

### Ubuntu/Debian

```bash
sudo apt-get install golang-go
```

### Windows

下载安装包：https://go.dev/dl/

## 命名约定

| 元素     | 约定           | 示例       |
| -------- | -------------- | ---------- |
| 源文件   | `{problem}.go` | `hello.go` |
| 编译产物 | `{problem}`    | `hello`    |
| 运行命令 | `./{problem}`  | `./hello`  |

## 示例：Hello World

**文件：`hello.go`**

```go
package main

import (
    "fmt"
    "bufio"
    "os"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    fmt.Print("What is your name? ")
    scanner.Scan()
    name := scanner.Text()
    fmt.Printf("hello, %s\n", name)
}
```

**运行检查：**

```bash
bootcs check cs50/hello -L go
```

## 编译标志

默认编译命令：

```bash
go build -o {problem} {problem}.go
```

自定义编译标志：

```python
lang = create_adapter(
    "myprogram",
    compile_flags=['-ldflags', '-s -w']  # 减小二进制大小
)
```

## 常见问题

### Q: 如何处理多个 Go 文件？

使用 `MultiFileAdapter`：

```python
lang = create_adapter(
    "myprogram",
    adapter_type='multi',
    source_files=['main.go', 'utils.go']
)
```

### Q: 如何使用 Go modules？

确保项目根目录有 `go.mod` 文件，BootCS 会自动处理依赖。

## 支持的问题

| 问题    | 状态        | 备注           |
| ------- | ----------- | -------------- |
| hello   | ✅ 支持     |                |
| mario   | ✅ 支持     |                |
| cash    | ✅ 支持     |                |
| credit  | ✅ 支持     |                |
| caesar  | ✅ 支持     |                |
| speller | ⚠️ 部分支持 | 需要自定义配置 |

````

### 步骤 7：更新主文档

**文件：`README.md`**

在"支持的语言"部分添加：

```markdown
## 支持的语言

- **C** - 完全支持（Tier 1）
- **Java** - 完全支持（Tier 1）
- **Python** - 完全支持（Tier 1）
- **Go** - 实验性支持（Tier 2）✨ 新增
- **Rust** - 实验性支持（Tier 2）
- **TypeScript** - 实验性支持（Tier 2）
````

### 步骤 8：运行测试

```bash
# 运行单元测试
python -m pytest tests/adapters/test_go.py -v

# 运行集成测试
python -m pytest tests/integration/test_go_hello.py -v

# 运行所有测试
python -m pytest tests/ -v
```

### 步骤 9：提交 PR

创建 Pull Request，包含：

1. 代码变更
2. 测试用例
3. 文档更新
4. CHANGELOG 条目

## 完整示例：添加 Rust 支持

### 代码变更

```python
# conventions.py
FILENAME_PATTERNS['rust'] = '{problem}.rs'
COMPILE_CONFIG['rust'] = {
    'compiler': 'rustc',
    'flags': ['-o', '{problem}'],
    'output': '{problem}'
}
RUN_CONFIG['rust'] = ['./{problem}']

# compiled.py
def _compile_rust(self) -> None:
    """Rust 语言编译"""
    import subprocess
    source = self.get_source_file()
    cmd = ['rustc', source, '-o', self.problem]
    subprocess.run(cmd, check=True)

# base.py
SUPPORTED_LANGUAGES.add('rust')
```

### Rust Hello World 示例

```rust
// hello.rs
use std::io::{self, Write};

fn main() {
    print!("What is your name? ");
    io::stdout().flush().unwrap();

    let mut name = String::new();
    io::stdin().read_line(&mut name).unwrap();

    println!("hello, {}", name.trim());
}
```

## 高级主题

### 1. 添加语言特定的库支持

对于 C 语言的 cs50 库，我们需要特殊处理：

```python
def _compile_c(self) -> None:
    """C 语言编译（支持 cs50 库）"""
    from .. import c
    source = self.get_source_file()

    # 检查是否需要 cs50 库
    content = Path(source).read_text()
    needs_cs50 = '#include <cs50.h>' in content

    c.compile(source, lcs50=needs_cs50)
```

### 2. 处理特殊的构建系统

对于使用 Makefile、Cargo、npm 等构建系统的项目：

```python
class MakefileAdapter(MultiFileAdapter):
    """支持 Makefile 的适配器"""

    def compile(self) -> None:
        """使用 Makefile 编译"""
        import subprocess
        subprocess.run(['make'], check=True)

    def clean(self) -> None:
        """清理构建产物"""
        import subprocess
        subprocess.run(['make', 'clean'], check=True)
```

### 3. 添加语言服务器支持（LSP）

集成语言服务器以提供更好的错误信息：

```python
class GoAdapter(CompiledLanguageAdapter):
    """Go 语言适配器（带 LSP 支持）"""

    def check_syntax(self) -> List[str]:
        """使用 gopls 检查语法"""
        import subprocess
        result = subprocess.run(
            ['gopls', 'check', self.get_source_file()],
            capture_output=True,
            text=True
        )
        return result.stderr.splitlines()
```

### 4. 跨平台支持

处理不同操作系统的差异：

```python
import platform

class CrossPlatformAdapter(LanguageAdapter):
    """跨平台适配器"""

    def get_run_command(self, *args: str) -> List[str]:
        """根据平台返回不同的运行命令"""
        if platform.system() == 'Windows':
            return [f'{self.problem}.exe', *args]
        else:
            return [f'./{self.problem}', *args]
```

### 5. 容器化支持

使用 Docker 容器隔离运行环境：

```python
class DockerAdapter(LanguageAdapter):
    """Docker 容器适配器"""

    def __init__(self, problem: str, image: str = 'gcc:latest'):
        super().__init__(problem)
        self.image = image

    def compile(self) -> None:
        """在 Docker 容器中编译"""
        import subprocess
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{Path.cwd()}:/workspace',
            '-w', '/workspace',
            self.image,
            'gcc', self.get_source_file(), '-o', self.problem
        ]
        subprocess.run(cmd, check=True)

    def run(self, *args: str):
        """在 Docker 容器中运行"""
        import subprocess
        cmd = [
            'docker', 'run', '--rm', '-i',
            '-v', f'{Path.cwd()}:/workspace',
            '-w', '/workspace',
            self.image,
            f'./{self.problem}', *args
        ]
        return subprocess.run(cmd, capture_output=True, text=True)
```

## 最佳实践

### 1. 命名约定

遵循语言社区的命名规范：

- Go: `snake_case.go`
- Rust: `snake_case.rs`
- Java: `PascalCase.java`
- Python: `snake_case.py`

### 2. 错误处理

提供清晰的错误消息：

```python
def _compile_go(self) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # 解析 Go 编译错误
        errors = self._parse_go_errors(e.stderr.decode())
        raise CompilationError(
            f"Go compilation failed:\n" + "\n".join(errors),
            e.stderr.decode(),
            e.returncode
        )

def _parse_go_errors(self, stderr: str) -> List[str]:
    """解析 Go 编译错误，提取关键信息"""
    errors = []
    for line in stderr.splitlines():
        if '.go:' in line:
            errors.append(line)
    return errors
```

### 3. 性能优化

利用增量编译和缓存：

```python
def compile(self) -> None:
    """带增量编译的 Go 编译"""
    # 检查是否需要重新编译
    source = Path(self.get_source_file())
    binary = Path(self.problem)

    if binary.exists():
        if binary.stat().st_mtime > source.stat().st_mtime:
            internal.log("Binary is up-to-date, skipping compilation")
            return

    # 执行编译
    self._do_compile()
```

### 4. 测试覆盖

确保每个语言至少有：

- 单元测试（基本功能）
- 集成测试（Hello World）
- 边界测试（错误处理）
- 性能测试（编译速度）

### 5. 文档完整性

每个新语言需要：

- 安装指南
- 快速开始
- API 参考
- 常见问题
- 迁移指南

## 社区贡献

### 提交语言支持

1. **讨论**：在 GitHub Discussions 中提出
2. **实现**：按照本指南实现
3. **测试**：完整的测试覆盖
4. **文档**：清晰的使用文档
5. **PR**：提交 Pull Request

### PR 检查清单

- [ ] 代码变更（适配器实现）
- [ ] 单元测试（90%+ 覆盖率）
- [ ] 集成测试（至少 Hello World）
- [ ] 文档（语言指南 + API 文档）
- [ ] CHANGELOG 条目
- [ ] CI/CD 配置更新
- [ ] 示例代码
- [ ] 性能基准测试

### 维护责任

根据支持级别，维护责任不同：

| 级别   | 维护者     | 响应时间 | 测试要求       |
| ------ | ---------- | -------- | -------------- |
| Tier 1 | 核心团队   | 24 小时  | CI/CD 必须通过 |
| Tier 2 | 社区志愿者 | 1 周     | 手动测试通过   |
| Tier 3 | 第三方     | 按需     | 自行负责       |

## 故障排查

### 常见问题

**Q: 编译器找不到**

```python
# 解决方案：添加环境检查
def check_environment(self):
    import shutil
    if not shutil.which('go'):
        raise EnvironmentError(
            "Go compiler not found. Install from https://go.dev/dl/"
        )
```

**Q: 路径问题（Windows）**

```python
# 解决方案：使用 pathlib
from pathlib import Path
def get_run_command(self):
    if platform.system() == 'Windows':
        return [str(Path(self.problem).with_suffix('.exe'))]
    return [f'./{self.problem}']
```

**Q: 字符编码问题**

```python
# 解决方案：显式指定编码
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)
```

## 总结

添加新语言支持的步骤：

1. ✅ 定义命名约定（5 分钟）
2. ✅ 实现编译逻辑（30 分钟）
3. ✅ 注册语言（5 分钟）
4. ✅ 添加测试（1 小时）
5. ✅ 编写文档（1 小时）
6. ✅ 提交 PR（30 分钟）

**总计：约 3-4 小时完成一门新语言的完整集成！**

通过遵循本指南，我们可以快速扩展 BootCS 的语言支持，为更多学生提供便利。
