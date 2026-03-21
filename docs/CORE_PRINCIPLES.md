# IntentOS 核心原则 (v2.1 融合版)

> **语言即系统 · 内核/IO 分离 · 自举演化**

---

## 一、核心原则

### 原则 1: 语言即系统
**含义**: 自然语言是操作系统的基本指令集。

### 原则 2: Prompt 即可执行文件
**含义**: PEF (Prompt Executable File) 是语义 VM 的机器码。

### 原则 3: 语义 VM
**含义**: LLM 作为处理器，执行语义指令。

---

## 二、OS 分层模型 (第一性原理)

### 2.1 语义内核层 (The Kernel)
内核是系统的“大脑”，必须是**自举（Self-Bootstrap）**的。
- **VM Core**: 处理指令流，管理语义内存。
- **Watchdog**: 哨兵进程，监控处理器健康并执行自愈。
- **Gas System**: 资源度量衡。

### 2.2 IO 能力层 (IO Layer / AI Agent)
Agent 是系统的“四肢”，负责物理世界的具体执行。
- **能力注册**: 将 Shell, FileSystem, API 抽象为语义能力。
- **权限门控**: 在 IO 触发前进行语义权限校验（`Capability Gate`）。

### 2.3 分布式基础设施 (Distributed Runtime)
- **Runtime Agent**: 每个物理节点的守护进程（Daemon）。
- **语义全局地址空间**: 跨节点的分布式内存。

---

## 三、设计约束

### 3.1 什么必须在 OS 层面
- ✅ 语义 VM 实现
- ✅ 意图编译器
- ✅ 能力注册中心
- ✅ 执行引擎
- ✅ 分布式一致性与调度

### 3.2 什么不应该在 OS 层面
- ❌ 复杂的多租户管理系统
- ❌ 计费系统和支付网关
- ❌ 应用市场和审核流程
(这些功能属于 PaaS 层)

---

## 四、代码组织

| 逻辑层 | 代码路径 |
| :--- | :--- |
| **Kernel** | `intentos/semantic_vm/` |
| **Distributed** | `intentos/distributed/` |
| **IO Layer** | `intentos/agent/` |
| **Runtime** | `intentos/runtime/` |
| **PaaS** | `intentos/paas/` |

---

**文档版本**: 2.1 (融合版)  
**最后更新**: 2026-03-21  
**状态**: **IntentOS 核心律令**
