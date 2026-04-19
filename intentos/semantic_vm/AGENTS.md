# Agent 架构与语义执行 (AGENTS.md)

> **哲学核心**: 在 IntentOS 中，Agent 不是一个外部工具或聊天机器人，而是一个运行在语义虚拟机 (SVM) 上的**进程**。

---

## 1. Agent 即进程 (Agent-as-a-Process)

IntentOS 颠覆了传统 AI 框架的“Agent-as-a-Wrapper”模式，将其沉淀为操作系统内核调度的基本单元：

- **处理器 (CPU)**: LLM (GPT-4o, Claude 3.5, etc.)
- **指令集 (ISA)**: 语义操作码 (Semantic Opcode: CREATE, MODIFY, EXECUTE...)
- **可执行文件**: PEF (Prompt Executable Format)
- **进程实体**: `SemanticProgram` 的执行实例

### 1.1 执行模型

1. **加载**: 内核将 PEF 加载到 `SemanticMemory`。
2. **调度**: `SemanticVM` 通过程序计数器 (PC) 逐条提取语义指令。
3. **解码**: `LLMProcessor` 将语义指令转化为面向 LLM 的具体 Prompt。
4. **执行**: LLM 返回执行结果，VM 更新内存状态或触发 IO 系统调用。

---

## 2. 语义指令集接口

Agent 通过 `SemanticOpcode` 与操作系统交互，实现状态持久化和逻辑控制：

| 指令类别 | 操作码 | 描述 |
| :--- | :--- | :--- |
| **基础操作** | `CREATE`, `MODIFY`, `QUERY` | 对语义组件 (Template, Policy) 的增删改查 |
| **逻辑控制** | `IF`, `LOOP`, `WHILE`, `JUMP` | 提供图灵完备的语义逻辑控制 |
| **物理 IO** | `EXECUTE` | **关键**: 调用物理世界的 Skill 或 MCP 工具 |
| **程序协作** | `CALL` | 实现 Agent 之间的嵌套与子程序协作 |
| **顾问策略** | `CONSULTANT` | **常规优先**: 遇难自动转向高精度专家模型 |
| **元编程** | `DEFINE_INSTRUCTION` | Agent 自我演化的核心，动态扩展指令集 |

---

## 3. 物理世界集成 (IO 层)

Agent 通过 `IOCapabilityIntegration` 接口突破语义黑盒，与物理世界交互。这是通过类似 Unix “系统调用” 的机制实现的：

### 3.1 Skill 调用 (Internal)
Agent 发出 `EXECUTE` 指令，VM 内核通过 `skill_io` 匹配并执行本地或远程 Skill（如文件读写、代码执行）。

### 3.2 MCP 集成 (External)
通过 `mcp_io` 接口，Agent 可以透明地访问所有符合 Model Context Protocol 规范的外部服务。

---

## 4. 权限与隔离 (Security)

为了防止 Agent “越狱” 或破坏内核，SVM 实施了双层隔离：

- **PrivilegeLevel.USER**: 普通 Agent 模式，禁止执行 `MODIFY_PROCESSOR` 或修改系统级 `POLICY`。
- **PrivilegeLevel.KERNEL**: 自举执行模式，允许修改指令集定义和处理器 Prompt。
- **Gas 机制**: 每条语义指令消耗 Gas，防止死循环导致 LLM 资源耗尽。

---

## 5. 自举演化路径 (Self-Bootstrap)

Agent 具备修改自身代码的能力：

1. **观察**: 通过 `QUERY` 指令分析当前的执行瓶颈或 SLO 违约。
2. **决策**: 生成新的优化策略或改进的语义指令。
3. **修改**: 使用 `MODIFY` 指令更新自身的 `SemanticProgram`。
4. **验证**: 通过 `EXECUTE` 执行新版本，并在失败时自动回滚（Transaction 机制）。

---

## 6. 未来演进

- [ ] **寄存器机制**: 引入语义寄存器以加速频繁状态的访问。
- [ ] **中断处理**: 实现基于事件触发的语义中断（Interrupt Handling）。
- [ ] **分布式上下文**: 支持 Agent 进程在多节点间的无损迁移（Checkpointing）。
