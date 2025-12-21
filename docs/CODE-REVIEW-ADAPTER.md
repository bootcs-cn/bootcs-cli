# 代码审查报告 - 语言适配器实施前评估

## 审查日期

2025-12-21

## 审查范围

- `bootcs/check/__init__.py` - 模块导出接口
- `bootcs/check/_api.py` - 核心 API 实现
- `bootcs/check/internal.py` - 内部状态管理
- `bootcs/check/c.py` 和 `java.py` - 现有语言支持
- `bootcs/check/runner.py` - 检查运行器
- `bootcs/__main__.py` - CLI 入口和语言检测

## 关键发现

### ✅ 正面发现

#### 1. 现有架构良好

```python
# bootcs/check/__init__.py
# 清晰的模块导出，易于扩展
__all__ = ["import_checks", "data", "exists", "hash", "include", "regex",
           "run", "log", "Failure", "Mismatch", "Missing", "check", "EOF",
           "c", "java", "internal", "hidden"]
```

**评估**：✅ 模块结构清晰，添加 `adapters` 模块不会破坏现有结构

#### 2. 语言检测已实现

```python
# bootcs/__main__.py
LANGUAGE_EXTENSIONS = {
    '.c': 'c',
    '.h': 'c',
    '.py': 'python',
    '.java': 'java',
    '.sql': 'sql',
}

def detect_language(directory: Path = None, explicit: str = None) -> str:
    """自动检测语言"""
```

**评估**：✅ 已有完善的语言检测机制，可以直接使用

#### 3. 内部状态管理完善

```python
# bootcs/check/internal.py
check_dir = None        # 检查目录
run_dir = None          # 运行目录
student_dir = None      # 学生代码目录
slug = None             # 问题标识
```

**评估**：✅ 状态管理清晰，便于添加 `current_language` 等新状态

#### 4. 现有 C/Java 支持可复用

```python
# bootcs/check/c.py
def compile(*files, exe_name=None, cc=CC, **cflags):
    """C 语言编译"""

# bootcs/check/java.py
def compile(*files, javac=JAVAC, classpath=None, **options):
    """Java 编译"""
```

**评估**：✅ 现有实现可以直接被适配器调用，无需重写

## MVP 简化决策 🎯

### 统一 Slug 格式

**决定**：MVP 阶段只支持 `{courseSlug}/{stageSlug}` 格式

```bash
# ✅ 唯一支持格式
bootcs check cs50/hello
bootcs check cs50/mario-less

# ❌ 不再支持（简化）
bootcs check cs50/c/hello     # 旧格式废弃
bootcs check cs50/java/hello  # 旧格式废弃
```

**理由**：

1. 更简洁的用户体验
2. 统一的目录结构
3. 降低认知负荷
4. MVP 不需要向后兼容

**影响**：

- ✅ 简化 `parse_slug()` 逻辑
- ✅ 统一 checks 目录结构
- ✅ 去掉语言路径判断代码

### ⚠️ 需要调整的地方

#### 1. **缺少语言上下文管理**

**问题**：`internal.py` 中没有存储当前语言的状态

```python
# 当前代码（internal.py）
check_dir = None
run_dir = None
# ❌ 缺少：current_language = None
```

**影响**：适配器无法获取当前语言

**解决方案**：

```python
# 需要添加到 internal.py
_current_language = None

def get_current_language() -> str:
    """获取当前语言"""
    return _current_language or 'c'  # 默认 C

def set_current_language(lang: str):
    """设置当前语言"""
    global _current_language
    _current_language = lang
```

**优先级**：🔴 高 - 适配器核心依赖

#### 2. **缺少问题名称提取**

**问题**：没有从 slug 提取问题名称的函数

```python
# 当前代码
slug = "cs50/hello"  # 或 "cs50/c/hello"
# ❌ 没有函数提取 "hello"
```

**影响**：适配器无法知道当前问题名称（用于构建文件名）

**解决方案**：

```python
# 需要添加到 internal.py
def get_problem_name() -> str:
    """从 slug 提取问题名称"""
    if not slug:
        return None
    parts = slug.split('/')
    return parts[-1]  # 返回最后一部分
```

**优先级**：🔴 高 - 适配器核心依赖

#### 3. **语言状态注入时机**

**问题**：`CheckRunner` 初始化时没有传递语言参数

```python
# 当前代码（runner.py）
class CheckRunner:
    def __init__(self, checks_path, included_files):
        self.checks_path = checks_path
        self.included_files = included_files
        # ❌ 没有 language 参数
```

**影响**：检查运行时无法知道当前语言

**解决方案**：

```python
# 需要修改 runner.py
class CheckRunner:
    def __init__(self, checks_path, included_files, language=None):
        self.checks_path = checks_path
        self.included_files = included_files
        self.language = language

        # 在导入 checks 前设置语言上下文
        if language:
            internal.set_current_language(language)
```

**优先级**：🟡 中 - 可以后续优化

#### 4. **CLI 传递语言参数**

**问题**：`__main__.py` 中创建 `CheckRunner` 时没有传递语言

```python
# 当前代码（__main__.py）
with CheckRunner(checks_file, list(included)) as runner:
    results = runner.run(targets=targets)
    # ❌ 没有传递 language 参数
```

**影响**：语言信息丢失

**解决方案**：

```python
# 需要修改 __main__.py
with CheckRunner(checks_file, list(included), language=language) as runner:
    results = runner.run(targets=targets)
```

**优先级**：🟡 中 - 配合 CheckRunner 修改

### 📊 兼容性评估

| 组件                       | 兼容性      | 需要修改     | 影响范围 |
| -------------------------- | ----------- | ------------ | -------- |
| `bootcs/check/__init__.py` | ✅ 完全兼容 | 添加导出     | 无破坏   |
| `bootcs/check/_api.py`     | ✅ 完全兼容 | 无需修改     | 无影响   |
| `bootcs/check/internal.py` | ⚠️ 需要扩展 | 添加语言状态 | 无破坏   |
| `bootcs/check/c.py`        | ✅ 完全兼容 | 无需修改     | 无影响   |
| `bootcs/check/java.py`     | ✅ 完全兼容 | 无需修改     | 无影响   |
| `bootcs/check/runner.py`   | ⚠️ 需要修改 | 添加语言参数 | 向后兼容 |
| `bootcs/__main__.py`       | ⚠️ 需要修改 | 传递语言参数 | 无破坏   |

## 实施建议

### 阶段 0：基础准备（新增）⚡️

**时间**：1 天

在开始适配器实施之前，先完成必要的基础改动：

#### 0.1 扩展 internal.py

```python
# bootcs/check/internal.py
# 添加语言状态管理

#: Current programming language
_current_language = None

def get_current_language() -> str:
    """Get current programming language."""
    return _current_language or 'c'

def set_current_language(lang: str):
    """Set current programming language."""
    global _current_language
    _current_language = lang

def get_problem_name() -> str:
    """Extract problem name from slug."""
    if not slug:
        return None
    parts = slug.split('/')
    return parts[-1]
```

#### 0.2 修改 CheckRunner

```python
# bootcs/check/runner.py
class CheckRunner:
    def __init__(self, checks_path, included_files, language=None):
        self.checks_path = checks_path
        self.included_files = included_files
        self.language = language

        # Set language context before loading checks
        if language:
            internal.set_current_language(language)
```

#### 0.3 更新 CLI

```python
# bootcs/__main__.py
def run_check(args):
    # ... 现有代码 ...

    # 传递语言参数给 CheckRunner
    with CheckRunner(checks_file, list(included), language=language) as runner:
        results = runner.run(targets=targets)
```

#### 0.4 添加单元测试

```python
# tests/unit/test_internal.py
def test_language_management():
    from bootcs.check import internal

    # 测试默认值
    assert internal.get_current_language() == 'c'

    # 测试设置
    internal.set_current_language('java')
    assert internal.get_current_language() == 'java'

    # 测试问题名称提取
    internal.slug = 'cs50/hello'
    assert internal.get_problem_name() == 'hello'

    internal.slug = 'cs50/c/mario-less'
    assert internal.get_problem_name() == 'mario-less'
```

**验证标准**：

- ✅ 所有现有测试通过
- ✅ 新的语言管理测试通过
- ✅ 向后兼容（不传 language 参数仍然工作）

### 阶段 1：适配器实施（修订）

**时间**：2 周 → 1.5 周（因为基础已完成）

现在可以按照原计划实施适配器，但更流畅：

#### 1.1 创建适配器模块

```bash
bootcs/check/adapters/
├── __init__.py
├── base.py          # 基础适配器类
├── conventions.py   # 命名约定
├── compiled.py      # 编译型语言
└── factory.py       # 工厂函数
```

#### 1.2 集成到现有模块

```python
# bootcs/check/__init__.py
# 添加导出
from .adapters import create_adapter, LanguageAdapter

__all__ = [..., "create_adapter", "LanguageAdapter"]
```

### 关键改进点

#### 1. 最小化侵入性

- ✅ 仅扩展 `internal.py`，不修改核心逻辑
- ✅ `CheckRunner` 参数向后兼容（language 可选）
- ✅ 现有检查无需修改即可运行

#### 3. **MVP 不考虑过渡期**

```python
# ❌ 不需要支持旧格式
# MVP 直接使用新的适配器设计

# ✅ 所有新检查统一使用适配器
@check()
def compiles():
    lang = create_adapter("hello")
    lang.compile()
```

**简化理由**：

- MVP 阶段可以大胆重构
- 不需要维护旧代码兼容性
- 统一架构，降低复杂度

#### 3. 测试策略

- 阶段 0 完成后运行完整测试套件
- 确保 100% 向后兼容
- 添加新的适配器测试

## 风险评估

### 低风险 ✅

- 添加新模块（`adapters/`）
- 扩展 `internal.py` 状态
- 添加可选参数

### 中风险 ⚠️

- 修改 `CheckRunner` 签名（但向后兼容）
- 修改 CLI 调用（内部实现）

### 高风险 ❌

- 无

## 时间估算更新

| 阶段           | 原计划 | 调整后        | 差异          |
| -------------- | ------ | ------------- | ------------- |
| 阶段 0（新增） | -      | 1 天          | +1 天         |
| 阶段 1         | 2 周   | 1.5 周        | -3 天         |
| 阶段 2         | 1 周   | 1 周          | 无变化        |
| 阶段 3         | 4 周   | 4 周          | 无变化        |
| 总计           | 7 周   | 6.5 周 + 1 天 | **提前 2 天** |

通过前置基础工作，实际上可以**加速**后续开发！

## 推荐实施顺序

### 第 1 天：基础准备

1. ✅ 扩展 `internal.py`（30 分钟）
2. ✅ 修改 `CheckRunner`（30 分钟）
3. ✅ 更新 CLI（30 分钟）
4. ✅ 编写测试（1 小时）
5. ✅ 验证兼容性（2 小时）

### 第 2-10 天：适配器开发

按照原计划的 Phase 1

### 第 11-15 天：Hello 迁移

按照原计划的 Phase 2

## 结论

### ✅ 可以开始实施

现有代码库结构良好，只需少量准备工作即可开始适配器开发。

### 🎯 关键成功因素

1. **先完成阶段 0**（1 天）- 打好基础
2. **保持向后兼容** - 旧检查继续工作
3. **增量测试** - 每个改动都测试
4. **文档同步更新** - 记录所有变更

### 📈 预期效果

- ✅ 零破坏性改动
- ✅ 完全向后兼容
- ✅ 为适配器铺平道路
- ✅ 实际加速开发进度

## 下一步行动

### 立即行动

1. **创建功能分支**：`git checkout -b feature/language-adapter-foundation`
2. **实施阶段 0**：完成基础准备工作
3. **运行测试**：确保 100% 通过
4. **Code Review**：团队审查基础改动
5. **合并主分支**：为适配器开发做好准备

### 准备工作

- [ ] 创建 GitHub Issue 跟踪进度
- [ ] 更新 ROADMAP.md
- [ ] 通知团队成员
- [ ] 准备测试数据

---

**审查人**：AI Assistant  
**批准状态**：✅ 建议开始实施  
**风险等级**：🟢 低  
**预计完成**：7 周内完成所有阶段
