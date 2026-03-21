# IntentOS v2.1 融合版

> **语言即系统 · 语义内核 · 分布式自举**

**文档版本**: 2.1 (融合版)  
**最后更新**: 2026-03-21  
**状态**: **稳定版 (生产级)**

---

## 核心架构 (v2.1 标准)

IntentOS 实现了计算与物理执行的彻底分离：
1. **语义内核 (The Kernel)**: `SemanticVM` 执行语义 Opcode，由 `Watchdog` 保护，受 `Gas` 约束。
2. **IO 层 (The IO Layer)**: `AIAgent` 作为物理驱动，通过 `Capability Gate` 进行权限准入。
3. **分布式运行时**: `RuntimeAgent` 守护进程将所有节点联合为统一的语义空间。

---

## 关键技术特性

| 特性 | 说明 | 状态 |
|------|------|------|
| **分布式 Map-Reduce** | 跨节点并行执行复杂意图，智能任务拆分与汇总 | ✅ 已实现 |
| **语义安全隔离** | 基于 `tenant:user` 命名空间的数据硬隔离 | ✅ 已实现 |
| **Gas 资源系统** | 对 Token、指令步数、IO 调用进行全维度配额管理 | ✅ 已实现 |
| **进程热迁移** | 运行中 PCB 的跨节点状态同步与转移 | ✅ 已实现 |
| **内核自愈 (Watchdog)** | 实时监控处理器健康，自动修复损坏的 Prompt 逻辑 | ✅ 已实现 |

---

## 快速入口

- **架构详述**: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- **安全规范**: [docs/SECURITY_AND_PERMISSIONS.md](./docs/SECURITY_AND_PERMISSIONS.md)
- **开发指南**: [docs/AI_NATIVE_APP.md](./docs/AI_NATIVE_APP.md)
- **核心原则**: [docs/CORE_PRINCIPLES.md](./docs/CORE_PRINCIPLES.md)

---

## 项目使命

**构建一个自举、演进且分布式的 AGI 运行底座，让自然语言成为操控物理世界的终极媒介。**

---

**QWEN.md 说明**: 本文件是项目核心进度的实时摘要。完整技术细节请参考 `docs/` 目录。
