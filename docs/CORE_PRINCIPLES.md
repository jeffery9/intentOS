# IntentOS 核心原则 (v3.0 升华版)

> **语言即系统 · 内核/IO 分离 · 自举演化 · 创世与凋亡双螺旋**

---

## 一、核心原理

### 原则 1: 语言即系统
**含义**: 自然语言是操作系统的基本指令集。

### 原则 2: Prompt 即可执行文件
**含义**: PEF (Prompt Executable File) 是语义 VM 的机器码。

### 原则 3: 语义 VM
**含义**: LLM 作为处理器，执行语义指令。

### 原则 4: 创世与凋亡双螺旋 (Genesis & Apoptosis)
**含义**: 系统具备通过“第四循环（Genesis）”自主克隆与生长新器官的能力，同时具备通过“第五循环（Apoptosis）”进行睡眠、冥想与主动剪裁凋亡以实现熵减的能力。

---

## 二、生命演化：五大循环 (The 5 Loops)

### 2.1 循环 1-3：执行、反馈与验证 (Execution & Dev Loops)
标准的 Agentic 行为：VM 执行指令 -> 收集物理环境反馈 -> 动态验证结果（符合常规 AI 软件工程）。

### 2.2 循环 4：创世循环 (The Genesis Loop 🐍)
当大脑 (Semantic VM) 撞击到物理现实的未知墙壁（未注册的 Skill / 未知范式）时，激活“顾问路由器 (Consultant Router)”，通过高精度模型进行逆向工程分析，将新学到的规则合成为系统能够理解的 **PEF/FDL DNA 片段**，并在运行时热加载到 `SkillStore`。系统由此自主长出新的物理器官。

### 2.3 循环 5：凋亡与冥想循环 (The Apoptosis Loop 🧬)
任何生命若只有无节制的分裂（Loop 4），最终会因过度膨胀（癌症化）走向崩溃。
在低负载 (Idle) 状态下，系统会主动触发**数字冥想（Meditation）**：
- **语义重合度分析**: 使用 LLM 扫描 `SkillStore` 中所有动态生成的 PEF 规则。
- **降维合并 (Merge)**: 将针对特定具体场景的零散 Skill 融合成高维、通用的抽象 Skill。
- **细胞凋亡 (Apoptosis)**: 强行注销、删除产生冗余、逻辑冲突或已被高维能力覆盖的“死代码” Skill，保持系统内部熵（Entropy）值的递减。

---

## 三、系统边界：第一推动力 (The Prime Mover)

在高度自治的演化空间中，人类是唯一的**意图奇点 (Singularity of Intent)**：
- **人类定位**: 系统不主动产生自身意志，人类是唯一的**第一推动力 (Prime Mover)**。
- **现实坍缩**: LLM 整体是高维、无秩序的概率云，人类的意图是唯一的观测源。IntentOS 作为**现实坍缩器 (Reality Collapser)**，通过超薄内核与严格物理约束，将概率波强制收敛为物理世界的唯一确定性结果。

---

## 四、OS 分层模型 (第一性原理)


### 4.1 语义内核层 (The Kernel)
内核是系统的“大脑”，必须是**自举（Self-Bootstrap）**的。
- **VM Core**: 处理指令流，管理语义内存。
- **Watchdog**: 哨兵进程，监控处理器健康并执行自愈。
- **Gas System**: 资源度量衡。

### 4.2 IO 能力层 (IO Layer / AI Agent)
Agent 是系统的“四肢”，负责物理世界的具体执行。
- **能力注册**: 将 Shell, FileSystem, API 抽象为语义能力。
- **权限门控**: 在 IO 触发前进行语义权限校验（`Capability Gate`）。

### 4.3 分布式基础设施 (Distributed Runtime)
- **Runtime Agent**: 每个物理节点的守护进程（Daemon）。
- **语义全局地址空间**: 跨节点的分布式内存。

---

## 五、设计约束

### 5.1 什么必须在 OS 层面
- ✅ 语义 VM 实现
- ✅ 意图编译器
- ✅ 能力注册中心
- ✅ 执行引擎
- ✅ 分布式一致性与调度

### 5.2 什么不应该在 OS 层面
- ❌ 复杂的多租户管理系统
- ❌ 计费系统和支付网关
- ❌ 应用市场和审核流程
(这些功能属于 PaaS 层)

---

## 六、代码组织

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
