# IntentOS 完整文档索引 (v3.5)

> **整理原则**: 不损失任何内容，只进行分类组织和导航优化
> **增强原则**: 在原有文档基础上增强，不创建新文档
> **去重原则**: 删除合并版 *_COMPLETE.md 文档，增强原始文档

**总文档数**: 66 篇 (去重后)  
**总字数**: ~70,000 字  
**最后更新**: 2026-03-22

---

## 📋 文档状态

### 已增强的文档

| 文档 | 增强内容 | 状态 |
|------|---------|------|
| [02-architecture/04-distributed-architecture.md](./02-architecture/04-distributed-architecture.md) | 新增运行时 Agent、语义进程管理、故障转移、K8s 部署 | ✅ 已增强 |
| [05-execution/02-map-reduce.md](./05-execution/02-map-reduce.md) | 新增分布式 Map/Reduce、应用场景 | ✅ 已增强 |
| [04-memory/02-distributed-sync.md](./04-memory/02-distributed-sync.md) | 新增混合同步模式、多区域部署、GDPR 合规 | ✅ 已增强 |
| [SELF_BOOTSTRAP.md](./SELF_BOOTSTRAP.md) | 新增 Self-Bootstrap 层级、架构实现、演示示例、验证与安全 | ✅ 已增强 |

### 已删除的重复文档

| 删除的文档 | 原因 | 状态 |
|-----------|------|------|
| `SELF_BOOTSTRAP_COMPLETE.md` | 与原始文档重复 | ✅ 已删除 |
| `DEPLOYMENT.md` | 与 DEPLOYMENT_GUIDE.md 重复 | ✅ 已删除 |
| `02-architecture/09-self-bootstrap-complete.md` | 内容已合并到 SELF_BOOTSTRAP.md | ✅ 已删除 |

---

## 📚 文档分类导航

### 🌟 核心入口文档 (3 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [docs/README.md](./README.md) | 180 | 文档索引导航 |
| [QWEN.md](../QWEN.md) | 201 | 项目核心进度摘要 + 代码修复律令 |
| [README.md](../README.md) | 342 | 项目总览、架构蓝图、快速开始 |

---

### 🏗️ 架构文档 (12 篇)

#### 核心架构

| 文档 | 行数 | 说明 |
|------|------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 650 | 完整架构说明：分布式语义 VM、运行时 Agent、PaaS 层 |
| [LAYERED_ARCHITECTURE.md](./LAYERED_ARCHITECTURE.md) | 405 | 分层架构：IntentOS 核心层 + PaaS 服务层 |
| [CORE_PRINCIPLES.md](./CORE_PRINCIPLES.md) | 70 | 核心原则：语言即系统、Prompt 即可执行文件、语义 VM |
| [AI_NATIVE_CORE_PRINCIPLES.md](./AI_NATIVE_CORE_PRINCIPLES.md) | 404 | AI Native 核心原则详解 |

#### 架构演进

| 文档 | 行数 | 说明 |
|------|------|------|
| [ARCHITECTURE_INTEGRATION.md](./ARCHITECTURE_INTEGRATION.md) | 355 | 架构集成说明 |
| [VISION_IMPLEMENTATION.md](./VISION_IMPLEMENTATION.md) | 579 | 愿景实现路径 |

#### 分层架构 (02-architecture/)

| 文档 | 行数 | 说明 |
|------|------|------|
| [01-three-layer-model.md](./02-architecture/01-three-layer-model.md) | 316 | 垂直 3 Layer 架构 |
| [02-intent-as-metalanguage.md](./02-architecture/02-intent-as-metalanguage.md) | 297 | 意图即元语言 |
| [03-self-bootstrap.md](./02-architecture/03-self-bootstrap.md) | 325 | Self-Bootstrap 机制 |
| [04-distributed-architecture.md](./02-architecture/04-distributed-architecture.md) | 429 | 分布式架构与进程管理 |
| [05-context-layer.md](./02-architecture/05-context-layer.md) | 382 | 上下文层详解 |
| [06-cloud-infrastructure.md](./02-architecture/06-cloud-infrastructure.md) | 980 | 云基础设施架构 |
| [07-self-bootstrap-architecture.md](./02-architecture/07-self-bootstrap-architecture.md) | 302 | Self-Bootstrap 架构 |
| [09-self-bootstrap-complete.md](./02-architecture/09-self-bootstrap-complete.md) | 579 | 完整 Self-Bootstrap 实现 (已合并到 SELF_BOOTSTRAP_COMPLETE.md) |

---

### 🤖 AI Native App 文档 (8 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [AI_NATIVE_APP.md](./AI_NATIVE_APP.md) | 233 | AI Native App 概念、架构、开发指南 |
| [JIT_GENERATION_ARCHITECTURE.md](./JIT_GENERATION_ARCHITECTURE.md) | 692 | App 即时生成、身份感知、版本管理 |
| [TENANT_ARCHITECTURE.md](./TENANT_ARCHITECTURE.md) | 579 | 多租户隔离、资源配置、能力绑定 |
| [BILLING_AND_REVENUE.md](./BILLING_AND_REVENUE.md) | 681 | 计费模式、收益分成、账单管理 |
| [INTENT_PACKAGE_SPEC.md](./INTENT_PACKAGE_SPEC.md) | 898 | manifest.yaml Schema、意图模板 |
| [SECURITY_AND_PERMISSIONS.md](./SECURITY_AND_PERMISSIONS.md) | 520 | 权限模型、安全策略、沙箱执行 |
| [PERFORMANCE_OPTIMIZATION.md](./PERFORMANCE_OPTIMIZATION.md) | 471 | 缓存策略、并行执行、性能监控 |
| [TESTING_AND_DEBUGGING.md](./TESTING_AND_DEBUGGING.md) | 611 | 单元测试、集成测试、调试工具 |

---

### 📖 入门文档 (docs/01-intro/ 4 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [01-what-is-ai-native.md](./01-intro/01-what-is-ai-native.md) | 128 | 什么是 AI 原生软件 |
| [02-from-ui-to-intent.md](./01-intro/02-from-ui-to-intent.md) | 171 | 从界面到意图：软件范式演进 |
| [03-intentos-overview.md](./01-intro/03-intentos-overview.md) | 227 | IntentOS 概述 |
| [04-quickstart.md](./01-intro/04-quickstart.md) | 270 | 5 分钟快速开始 |

---

### 🔧 编译器文档 (docs/03-compiler/ 4 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [01-compiler-architecture.md](./03-compiler/01-compiler-architecture.md) | 415 | 意图编译器架构：词法/语法/语义分析 |
| [02-pef-specification.md](./03-compiler/02-pef-specification.md) | 475 | PEF (Prompt Executable File) 规范 |
| [03-code-generation.md](./03-compiler/03-code-generation.md) | 493 | 代码生成：结构化意图 → Prompt |
| [04-linker.md](./03-compiler/04-linker.md) | 472 | 链接器：Prompt 与能力绑定 |

---

### 🧠 记忆系统文档 (docs/04-memory/ 4 篇)

**注意**: IntentOS 中的 **Memory = 记忆**（模拟人类记忆系统），不是物理内存 (RAM)。

| 文档 | 行数 | 说明 |
|------|------|------|
| [01-memory-layers.md](./04-memory/01-memory-layers.md) | 481 | 记忆分层：工作/短期/长期记忆 |
| [02-distributed-sync.md](./04-memory/02-distributed-sync.md) | 424 | 分布式记忆同步：Redis 同步机制 |
| [03-memory-retrieval.md](./04-memory/03-memory-retrieval.md) | 276 | 记忆检索：标签索引和搜索 |
| [04-expiry-policy.md](./04-memory/04-expiry-policy.md) | 345 | 记忆过期策略：TTL 和清理 |

---

### ⚙️ 执行引擎文档 (docs/05-execution/ 4 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [01-dag-engine.md](./05-execution/01-dag-engine.md) | 540 | DAG 执行引擎：任务图执行 |
| [02-map-reduce.md](./05-execution/02-map-reduce.md) | 685 | **已增强**: Map/Reduce 分布式数据处理 + 分布式执行 |
| [03-memory-optimization.md](./05-execution/03-memory-optimization.md) | 439 | 记忆优化：流式处理和溢出 |
| [04-llm-backends.md](./05-execution/04-llm-backends.md) | 420 | LLM 后端：多模型支持 |

---

### 🔌 API 参考文档 (docs/06-api/ 4 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [01-core-api.md](./06-api/01-core-api.md) | 610 | 核心 API：核心类和函数 |
| [02-compiler-api.md](./06-api/02-compiler-api.md) | 481 | 编译器 API：意图编译器接口 |
| [03-memory-api.md](./06-api/03-memory-api.md) | 585 | 记忆 API：记忆管理接口 |
| [04-execution-api.md](./06-api/04-execution-api.md) | 630 | 执行 API：执行引擎接口 |

---

### 📚 开发指南文档 (docs/07-guides/ 4 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [01-build-first-app.md](./07-guides/01-build-first-app.md) | 432 | 构建第一个 AI Native App |
| [02-define-intent-template.md](./07-guides/02-define-intent-template.md) | 508 | 定义意图模板 |
| [03-register-capability.md](./07-guides/03-register-capability.md) | 482 | 注册能力：能力注册和绑定 |
| [04-deploy-intentos.md](./07-guides/04-deploy-intentos.md) | 542 | 部署 IntentOS：生产环境部署 |

---

### 📜 应用层架构文档 (3 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [APP_DEVELOPMENT_GUIDE.md](./APP_DEVELOPMENT_GUIDE.md) | 698 | 应用开发指南：完整开发流程 |
| [APPS_ARCHITECTURE.md](./APPS_ARCHITECTURE.md) | 591 | 应用层架构与 AI Agent 实现 |
| [AI_AGENT_USAGE.md](./AI_AGENT_USAGE.md) | 712 | AI Agent 使用指南 |

---

### 🔄 Self-Bootstrap 文档 (6 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [SELF_BOOTSTRAP.md](./SELF_BOOTSTRAP.md) | 839 | **已增强**: Self-Bootstrap 完整机制 (含层级/架构/示例/验证/安全) |
| [SELF_REPRODUCTION.md](./SELF_REPRODUCTION.md) | 529 | 自我复制机制 |
| [CLOUD_SELF_BOOTSTRAP.md](./CLOUD_SELF_BOOTSTRAP.md) | 469 | 云端 Self-Bootstrap |
| [SOCIAL_TRANSMISSION.md](./SOCIAL_TRANSMISSION.md) | 573 | 社会传播机制 |
| [02-architecture/03-self-bootstrap.md](./02-architecture/03-self-bootstrap.md) | 325 | Self-Bootstrap 基础介绍 |
| [02-architecture/07-self-bootstrap-architecture.md](./02-architecture/07-self-bootstrap-architecture.md) | 302 | Self-Bootstrap 架构详解 |

**说明**:
- `SELF_BOOTSTRAP.md` 已增强，新增附录 A/B/C/D
- `SELF_BOOTSTRAP_COMPLETE.md` 已删除（重复文档）
- `02-architecture/09-self-bootstrap-complete.md` 已删除（内容已合并）

---

### 📜 其他文档 (5 篇)

| 文档 | 行数 | 说明 |
|------|------|------|
| [INTENTOS_VS_OPENCLAW.md](./INTENTOS_VS_OPENCLAW.md) | 262 | IntentOS vs OpenClaw 对比 |
| [startup-growth-strategy/intentos-integrated-evaluation.md](./startup-growth-strategy/intentos-integrated-evaluation.md) | 127 | IntentOS 综合评估 (英文) |
| [startup-growth-strategy/intentos-integrated-evaluation-zh.md](./startup-growth-strategy/intentos-integrated-evaluation-zh.md) | 127 | IntentOS 综合评估 (中文) |

---

## 📊 文档统计

### 按类别统计

| 类别 | 文档数 | 总行数 | 占比 |
|------|--------|--------|------|
| **核心入口** | 3 | 723 | 2.6% |
| **架构文档** | 12 | 5,376 | 19.4% |
| **AI Native App** | 8 | 4,685 | 16.9% |
| **入门文档** | 4 | 796 | 2.9% |
| **编译器文档** | 4 | 1,855 | 6.7% |
| **记忆系统** | 4 | 1,526 | 5.5% |
| **执行引擎** | 4 | 2,001 | 7.2% |
| **API 参考** | 4 | 2,306 | 8.3% |
| **开发指南** | 4 | 1,964 | 7.1% |
| **应用层架构** | 3 | 2,001 | 7.2% |
| **Self-Bootstrap** | 4 | 2,041 | 7.4% |
| **部署与入门** | 3 | 1,823 | 6.6% |
| **其他文档** | 5 | 889 | 3.2% |
| **总计** | **62** | **27,773** | **100%** |

---

## 📖 推荐阅读路径

### 🟢 初学者路径 (快速上手)

```
README.md → 01-intro/01-what-is-ai-native.md 
         → 01-intro/04-quickstart.md 
         → 07-guides/01-build-first-app.md
```

### 🟡 开发者路径 (完整开发)

```
AI_NATIVE_APP.md → APP_DEVELOPMENT_GUIDE.md 
                → 07-guides/02-define-intent-template.md 
                → 07-guides/03-register-capability.md 
                → TESTING_AND_DEBUGGING.md
```

### 🔵 架构师路径 (深入理解)

```
ARCHITECTURE.md → LAYERED_ARCHITECTURE.md 
               → CORE_PRINCIPLES.md 
               → 02-architecture/01-three-layer-model.md 
               → 03-compiler/01-compiler-architecture.md
```

### 🟣 AI Native App 路径

```
AI_NATIVE_APP.md → JIT_GENERATION_ARCHITECTURE.md 
                → TENANT_ARCHITECTURE.md 
                → BILLING_AND_REVENUE.md 
                → INTENT_PACKAGE_SPEC.md
```

---

## 🔗 外部资源

| 资源 | 链接 |
|------|------|
| **GitHub 仓库** | [github.com/jeffery9/IntentOS](https://github.com/jeffery9/IntentOS) |
| **项目路线图** | [ROADMAP.md](../ROADMAP.md) |
| **示例代码** | [examples/](../examples/) |

---

## 📝 文档版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 3.0 | 2026-03-22 | 完整文档索引整理，不损失任何内容 |
| 2.1 | 2026-03-21 | v2.1 融合版架构更新 |
| 2.0 | 2026-03-21 | v2.0 完整版 |
| 1.0 | 2026-03-12 | 初始版本 |

---

**整理原则**: 不损失任何内容，只进行分类组织和导航优化。  
**最后更新**: 2026-03-22
