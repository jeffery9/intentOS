# AI Native App 规范 (v3.0)

> **一个 AI Native App 是一个可计量的、可审计的、图灵完备的语义程序，通过对话式生成，并安全地实例化私有资源，运行在分布式语义虚拟机上。**

---

## 1. 核心原则：App 即语义程序

在 IntentOS 中，一个 AI Native App 不是二进制文件或脚本，而是一个 `SemanticProgram`——一个由 `SemanticVM` 执行的结构化 `SemanticInstruction` 序列。这是最基础的第一性原理定义。

- **图灵完备性**: 指令集 (`SemanticOpcode`) 是图灵完备的，不仅支持状态操作 (`CREATE`, `MODIFY`)，还支持完整的控制流 (`IF`, `LOOP`, `WHILE`, `JUMP`) 和分布式计算原语 (`PARALLEL`, `SHARD`, `MIGRATE`)。
- **LLM 即 CPU**: `LLMProcessor` 是 `SemanticVM` 的核心，作为解释和执行这些语义操作码的 CPU。
- **源代码**: App 的“源代码”是其 `logic` 块——在其清单中定义的一系列操作码。

---

## 2. 开发生命周期：对话即 IDE

AI Native App 的整个生命周期通过对话式界面 `AppConversationStudio` 进行管理。

1.  **构思**: 开发者用自然语言描述其应用的功能。
2.  **规格化 (The "App Spec")**: `AppConversationStudio` 使用 LLM 将此想法转化为正式的“App 规格”或清单。该清单包括：
    - `name`, `description`, `category`
    - `intents`: 面向用户的命令模板。
    - `permissions`: 所需的物理访问权限 (例如, `system:shell`)。
    - `logic`: 作为 `SemanticOpcodes` 序列的核心 `SemanticProgram`。
3.  **发布**: 通过一个简单的命令 (`publish`)，生成的规格被提交到 `AppMarketplace`，进行版本控制，并对租户开放。

---

## 3. 实例化模型：逻辑 + 状态 + 安全

当用户运行一个 App 时，它不是传统意义上的“执行”。相反，`AppGenerator` 将其**实例化**，创建一个 `GeneratedApp` 运行时实体。这是一个安全的聚合体，包括：

1.  **逻辑**: App 的核心 `SemanticProgram`。
2.  **状态**: 租户的私有资源 (例如，数据库凭证，API 密钥)，通过 `CapabilityBinder` “嫁接”到 App 的抽象能力上。
3.  **安全上下文**: 一个 `UserContext`，包含一个合成的权限列表，授予实例对租户资源的临时、可撤销的访问权限。

该模型确保了**完美的隔离**，并允许市场上的通用、可重用 App 安全地操作租户的私有数据，而无需暴露这些数据。

---

## 4. 经济模型：Gas 驱动的执行

App 执行的每个方面都通过多维 **Gas** 系统进行计量，确保公平和可审计的资源消耗。

- **计量**: `SemanticVM` 的 `GasTracker` 对每个操作码、每个 LLM Token 和每个 I/O 调用进行核算。
- **配额**: 这种消耗会根据租户的 `TenantQuota` 进行检查，该配额定义了物理 (CPU, 内存) 和语义 (Gas) 的限制。
- **结算**: 执行后，`AppMarketplace.record_usage` 函数将消耗的总 Gas 转化为可计费金额。然后，此金额在开发者和平台之间自动分配，形成一个自我维持的经济循环。

---

## 5. 分布式模型：全球规模

AI Native App 专为分布式世界设计。`DistributedCoordinator` 和 `DistributedSemanticVM` 允许 App 的 `SemanticProgram`：

- **随处运行**: 进程可以在任何节点上启动。
- **按需扩展**: 使用 `PARALLEL` 操作码触发 Map-Reduce 工作流，将任务拆分到多个节点。
- **自由迁移**: 使用 `MIGRATE` 操作码进行实时进程迁移，将正在运行的 App 实例从一个物理节点无缝迁移到另一个。

本规范为新一代软件提供了蓝图——智能、自治，并为 AI 时代而生。

**文档版本**: 3.0  
**最后更新**: 2026-03-21  
**状态**: **v3.0 生产级规范**
