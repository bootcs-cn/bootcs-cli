# BootCS CLI 文档索引

## 核心文档

### [语言适配器架构设计](./LANGUAGE-ADAPTER-DESIGN.md)

完整的语言适配器架构设计文档，包括：

- 设计目标和动机
- 系统架构图
- 核心类设计
- 命名约定规范
- 使用示例
- CS50 Problems 覆盖情况
- 性能优化策略
- 扩展性设计

**适合人群**：架构师、核心开发者

### [语言适配器实施方案](./LANGUAGE-ADAPTER-IMPLEMENTATION.md)

详细的实施步骤和代码结构，包括：

- 目录结构规划
- 分阶段实施计划（Phase 1-5）
- 代码实现示例
- 迁移策略和脚本
- 验证和测试方法
- 回滚策略
- 度量指标

**适合人群**：开发者、项目经理

### [语言扩展指南](./LANGUAGE-EXTENSION-GUIDE.md)

如何添加新语言支持的完整指南，包括：

- 快速开始（Go 示例）
- 完整示例（Rust）
- 高级主题（LSP、Docker、跨平台）
- 最佳实践
- 社区贡献流程
- 故障排查

**适合人群**：贡献者、语言维护者

## 快速链接

### 对于用户

- [使用指南](#) - 如何使用 BootCS CLI（待创建）
- [语言支持](./LANGUAGE-EXTENSION-GUIDE.md#支持级别) - 支持的编程语言列表

### 对于开发者

- [架构设计](./LANGUAGE-ADAPTER-DESIGN.md)
- [实施方案](./LANGUAGE-ADAPTER-IMPLEMENTATION.md)
- [API 参考](#) - 完整的 API 文档（待创建）
- [贡献指南](#) - 如何贡献代码（待创建）

### 对于贡献者

- [语言扩展](./LANGUAGE-EXTENSION-GUIDE.md)
- [测试指南](#) - 如何编写和运行测试（待创建）
- [发布流程](#) - 版本发布流程（待创建）

## 文档结构

```
docs/
├── README.md                              # 本文件（索引）
├── LANGUAGE-ADAPTER-DESIGN.md             # 架构设计文档 ✅
├── LANGUAGE-ADAPTER-IMPLEMENTATION.md     # 实施方案文档 ✅
├── LANGUAGE-EXTENSION-GUIDE.md            # 语言扩展指南 ✅
├── user-guide/                            # 用户指南（待创建）
│   ├── getting-started.md
│   ├── check-command.md
│   └── submit-command.md
├── developer-guide/                       # 开发者指南（待创建）
│   ├── architecture.md
│   ├── api-reference.md
│   └── testing.md
└── languages/                             # 语言特定文档（待创建）
    ├── c.md
    ├── java.md
    ├── python.md
    ├── go.md
    └── rust.md
```

## 关键概念

### 语言适配器（Language Adapter）

一个抽象层，隐藏不同编程语言的差异，提供统一的编译和运行接口。

**优势**：

- 消除代码重复（减少 80%+）
- 简化维护（一处修改，多语言生效）
- 易于扩展（添加新语言只需 3-4 小时）

### 命名约定（Naming Conventions）

标准化的文件命名和目录结构规则，实现"约定优于配置"。

**示例**：

- C: `hello.c` → `./hello`
- Java: `Hello.java` → `java Hello`
- Python: `hello.py` → `python3 hello.py`

### 支持级别（Support Tiers）

语言支持的三个级别：

- **Tier 1**：完全支持（C, Java, Python）
- **Tier 2**：实验性支持（Go, Rust, TypeScript）
- **Tier 3**：社区支持（其他语言）

## 实施进度

### Phase 1: 基础架构 ✅

- [x] 设计文档
- [x] 实施方案
- [x] 扩展指南
- [ ] 核心代码实现（进行中）

### Phase 2: Hello 迁移

- [ ] 实现基础适配器类
- [ ] 迁移 hello 检查
- [ ] 测试 C/Java/Python
- [ ] 性能验证

### Phase 3: 批量迁移

- [ ] 迁移标准 I/O 问题
- [ ] 迁移复杂问题
- [ ] 迁移特殊项目

### Phase 4: 扩展支持

- [ ] 添加 Go 支持
- [ ] 添加 Rust 支持
- [ ] 添加 TypeScript 支持

### Phase 5: 优化和完善

- [ ] 性能优化
- [ ] 完善文档
- [ ] 用户反馈

## 度量指标

### 代码质量

- **代码减少**：目标 80%+，当前 0%
- **测试覆盖率**：目标 90%+，当前 N/A
- **性能影响**：目标 <5%，当前 N/A

### 开发效率

- **添加新语言**：目标 3-4 小时
- **迁移一个问题**：目标 30 分钟
- **修复 Bug**：目标减少 67%

### 用户体验

- **学习曲线**：平缓
- **错误消息**：清晰
- **文档完整性**：95%+

## 版本历史

### v0.1.0 (2025-12-21)

- ✅ 初始设计文档
- ✅ 实施方案文档
- ✅ 扩展指南文档

### v0.2.0 (计划中)

- [ ] 核心适配器实现
- [ ] Hello 问题迁移
- [ ] 用户指南

### v1.0.0 (目标)

- [ ] 所有 CS50 问题迁移完成
- [ ] 支持 C, Java, Python
- [ ] 完整文档和测试

## 贡献

我们欢迎社区贡献！主要领域：

- **新语言支持**：按照[扩展指南](./LANGUAGE-EXTENSION-GUIDE.md)添加
- **问题迁移**：将旧格式检查迁移到新架构
- **文档改进**：修正错误、添加示例
- **Bug 修复**：报告和修复问题

详见 [CONTRIBUTING.md](../CONTRIBUTING.md)

## 联系方式

- **GitHub Issues**：报告问题和功能请求
- **GitHub Discussions**：讨论和提问
- **Pull Requests**：代码贡献

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件。

---

**最后更新**：2025-12-21  
**维护者**：BootCS Team
