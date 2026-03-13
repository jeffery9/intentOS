# IntentOS 文档索引

欢迎来到 IntentOS 文档中心。本文档集基于《AI 原生软件范式转变》对话录整理而成，系统阐述了 IntentOS 的设计理念、架构实现和使用指南。

---

## 📚 文档导航

### 第一部分：入门 (Introduction) ✅

| 文档 | 说明 |
|------|------|
| [01-01 什么是 AI 原生软件](01-intro/01-what-is-ai-native.md) | AI 原生软件的定义和核心特征 |
| [01-02 从界面到意图](01-intro/02-from-ui-to-intent.md) | 软件范式的历史演进 |
| [01-03 IntentOS 概述](01-intro/03-intentos-overview.md) | IntentOS 是什么 |
| [01-04 快速开始](01-intro/04-quickstart.md) | 5 分钟上手 IntentOS |

### 第二部分：架构 (Architecture) ✅

| 文档 | 说明 |
|------|------|
| [02-01 三层七层架构](02-architecture/01-three-layer-model.md) | App/IntentOS/LLM 三层模型 |
| [02-02 意图即元语言](02-architecture/02-intent-as-metalanguage.md) | 意图的形式化定义 |
| [02-03 Self-Bootstrap](02-architecture/03-self-bootstrap.md) | 系统自举机制 |
| [02-04 分布式架构](02-architecture/04-distributed-architecture.md) | 分布式执行和记忆同步 |
| [02-05 上下文层](02-architecture/05-context-layer.md) | L3 上下文层详解 |
| [02-06 云基础设施](02-architecture/06-cloud-infrastructure.md) | Cloud 基础设施架构 |
| [02-07 Self-Bootstrap 架构](02-architecture/07-self-bootstrap-architecture.md) | LLM 作为处理器的 Self-Bootstrap |
| [02-08 语义 VM 架构](02-architecture/08-semantic-vm-architecture.md) | 语义 VM = Self-Bootstrap 基础 |
| [02-09 完整 Self-Bootstrap](02-architecture/09-self-bootstrap-complete.md) | 完整的 Self-Bootstrap 实现 |

### 第三部分：编译器 (Compiler) ✅

| 文档 | 说明 |
|------|------|
| [03-01 意图编译器架构](03-compiler/01-compiler-architecture.md) | 词法/语法/语义分析 |
| [03-02 PEF 规范](03-compiler/02-pef-specification.md) | Prompt 可执行文件格式 |
| [03-03 代码生成](03-compiler/03-code-generation.md) | 结构化意图 → Prompt |
| [03-04 链接器](03-compiler/04-linker.md) | Prompt 与能力绑定 |

### 第四部分：记忆 (Memory) ✅

**注意**: IntentOS 中的 **Memory = 记忆**（人类记忆系统），**不是** 传统 OS 的物理内存 (RAM)。

| 文档 | 说明 |
|------|------|
| [04-01 记忆分层架构](04-memory/01-memory-layers.md) | 工作/短期/长期记忆（模拟人类记忆） |
| [04-02 分布式记忆同步](04-memory/02-distributed-sync.md) | Redis 同步机制 |
| [04-03 记忆检索](04-memory/03-memory-retrieval.md) | 标签索引和搜索 |
| [04-04 过期策略](04-memory/04-expiry-policy.md) | TTL 和清理策略 |

### 第五部分：执行 (Execution) ✅

| 文档 | 说明 |
|------|------|
| [05-01 DAG 执行引擎](05-execution/01-dag-engine.md) | 任务图执行 |
| [05-02 Map/Reduce](05-execution/02-map-reduce.md) | 分布式数据处理 |
| [05-03 记忆优化](05-execution/03-memory-optimization.md) | 流式处理和溢出（针对语义记忆） |
| [05-04 LLM 后端](05-execution/04-llm-backends.md) | 多模型支持 |

### 第六部分：API 参考 (API Reference) ✅

| 文档 | 说明 |
|------|------|
| [06-01 核心 API](06-api/01-core-api.md) | 核心类和函数 |
| [06-02 编译器 API](06-api/02-compiler-api.md) | 意图编译器接口 |
| [06-03 记忆 API](06-api/03-memory-api.md) | 记忆管理接口 |
| [06-04 执行 API](06-api/04-execution-api.md) | 执行引擎接口 |

### 第七部分：指南 (Guides) ✅

| 文档 | 说明 |
|------|------|
| [07-01 构建第一个 App](07-guides/01-build-first-app.md) | 创建意图包 |
| [07-02 定义意图模板](07-guides/02-define-intent-template.md) | 意图模板设计 |
| [07-03 注册能力](07-guides/03-register-capability.md) | 能力注册和绑定 |
| [07-04 部署 IntentOS](07-guides/04-deploy-intentos.md) | 生产环境部署 |

---

## 📖 推荐阅读顺序

### 初学者路径

```
01-01 → 01-02 → 01-03 → 01-04 → 07-01 → 07-02
```

### 架构师路径

```
01-01 → 02-01 → 02-02 → 02-03 → 02-04 → 03-01 → 04-01 → 05-01
```

### 开发者路径

```
01-04 → 07-01 → 07-02 → 07-03 → 03-01 → 05-04
```

---

## 🔗 相关资源

- [GitHub 仓库](https://github.com/intentos/intentos)
- [论文：三层七层架构](../paper-three-layer-architecture.md)
- [论文：IntentOS 架构](../paper-intentos-architecture.md)
- [示例代码](../intentos/examples/)

---

## 📝 文档版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-03-12 | 初始版本 |

---

## 📊 完成进度

| 章节 | 已完成 | 总计 | 进度 |
|------|--------|------|------|
| 01-intro | 4 | 4 | 100% ✅ |
| 02-architecture | 9 | 9 | 100% ✅ |
| 03-compiler | 4 | 4 | 100% ✅ |
| 04-memory | 4 | 4 | 100% ✅ |
| 05-execution | 4 | 4 | 100% ✅ |
| 06-api | 4 | 4 | 100% ✅ |
| 07-guides | 4 | 4 | 100% ✅ |
| **总计** | **33** | **33** | **100%** 🎉 |

---

**最后更新**: 2026 年 3 月 12 日
