# IntentOS 文档索引 (v2.1 融合版)

欢迎来到 **IntentOS 企业级 v2.1** 文档中心。本版本确立了“语义解耦”架构，实现了分布式执行、安全隔离与自动化经济结算的完整闭环。

---

## 📚 快速入口

### ⭐ 核心原则 (必读)
| 文档 | 说明 |
|------|------|
| [核心原则](./CORE_PRINCIPLES.md) | **语言即系统 · Prompt 即可执行文件 · 自举演化** (系统灵魂) |

### 🌟 架构核心
| 文档 | 说明 |
|------|------|
| [架构总览](./ARCHITECTURE.md) | ⭐ v2.1 标准：SVM 内核、Watchdog、Gas 机制与分布式 Map-Reduce |
| [分层架构](./LAYERED_ARCHITECTURE.md) | 详解 Kernel -> IO Agent -> PaaS 的语义解耦模型 |
| [租户架构](./TENANT_ARCHITECTURE.md) | 混合配额管理、私有资源嫁接与自动权限合成 |

---

## 🛠️ 关键技术体系

### 1. 语义内核层
- **语义 VM**: 支持 `LOOP`, `SHARD`, `PARALLEL`, `MIGRATE` 指令集的逻辑引擎。
- **Watchdog**: 内核自愈监视器，防止处理器损坏。
- **Gas 系统**: 资源度量衡。

### 2. IO 能力层
- **能力门控**: 权限准入网关。
- **物理映射**: Shell, FileSystem, API 的语义驱动化。

### 3. 分布式运行时
- **Runtime Agent**: 全功能节点守护进程。
- **一致性哈希**: 全局语义存储空间。

### 4. 商业生态 (PaaS)
- **应用市场**: 意图驱动的应用发现与交易。
- **App 生成器**: 结合 `ConversationStudio` 的对话式开发。
- **计费结算**: [计费与商业化规范](./BILLING_AND_REVENUE.md) - 从 Gas 到收益的自动转换。

---

## 📖 参考文档指南

### 开发 AI Native App
1. [AI Native App 规范](./AI_NATIVE_APP.md)
2. [安全与权限规范](./SECURITY_AND_PERMISSIONS.md)
3. [性能优化策略](./PERFORMANCE_OPTIMIZATION.md)

---

**文档版本**: 2.1 (融合版)  
**最后更新**: 2026-03-21  
**状态**: ✅ 稳定版 (企业级)
