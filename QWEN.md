# IntentOS - 分布式 AI 原生操作系统

> **语言即系统 · Prompt 即可执行文件 · 分布式语义 VM**

**文档版本**: 3.1
**创建日期**: 2026-03-12
**最后更新**: 2026-04-03

---

## 项目概述

IntentOS 是一个 **分布式 AI 原生操作系统**, 不是传统的 AI Agent 框架。

核心是**语义虚拟机 (Semantic VM)** —— 将自然语言意图编译为 PEF (Prompt Executable File), 由 LLM 作为处理器执行, 支持 Self-Bootstrap 和跨节点分布式部署。

### 与传统 AI Agent 框架的本质区别

| 传统 AI Agent 框架 | IntentOS |
|-------------------|----------|
| 单节点应用层智能代理 | **分布式操作系统内核** |
| Tool Calling + LLM Loop | **语义 VM + PEF** (Prompt Executable File) |
| Prompt Engineering | **意图编译 → 语义执行** |
| 会话级上下文 | **全局语义地址空间** (跨节点) |

### 核心理念

- **语义 VM**: LLM 作为处理器, PEF 作为机器码, 跨网络组成整体 OS
- **分布式**: 多节点集群, 语义 VM 跨节点执行, Map-Reduce 汇总结果
- **运行时 Agent**: 节点 Daemon, 为本地语义 VM 提供能力, 管理 Skill 缓存
- **接口层**: 对外提供 REST API 和 Chat 访问接口
- **PaaS 服务层**: 多租户、计费、应用市场（独立于 OS 核心层）

### 快速导航

| 文档 | 说明 |
|------|------|
| [架构文档](./docs/ARCHITECTURE.md) | ⭐ **完整架构说明**：分布式语义 VM、运行时 Agent、PaaS 层 |
| [核心原则](./docs/CORE_PRINCIPLES.md) | 语言即系统 · Prompt 即可执行文件 · 语义 VM |
| [AI Native App](./docs/AI_NATIVE_APP.md) | AI Native App 概念、开发指南 |
| [ROADMAP.md](./ROADMAP.md) | 项目路线图 |
| [📋 项目约定](#-项目约定) | 测试路径、代码组织、提交规范 |

---

## 快速开始

### 1. 安装

```bash
# 基础安装
pip install -e .

# 启动 Shell
PYTHONPATH=. python intentos/interface/shell.py

# 启动 API 服务器
PYTHONPATH=. python intentos/interface/api.py
```

### 2. 使用示例

```python
from intentos.compiler import IntentCompiler
from intentos.semantic_vm import SemanticVM
from intentos.agent import AgentContext

# 创建编译器 (加载已注册的能力)
compiler = IntentCompiler()

# 编译用户意图为 PEF (Prompt Executable File)
pef = compiler.compile("分析华东区 Q3 销售数据")

# 创建语义 VM 和执行上下文
vm = SemanticVM()
context = AgentContext(user_id="demo", permissions=["data:read"])

# 执行 PEF
result = await vm.execute(pef, context)

print(result.message)  # 自然语言回复
print(result.data)     # 数据结果
```

### 3. 分布式部署

```python
from intentos.runtime import RuntimeAgent

# 创建运行时 Agent
runtime_agent = RuntimeAgent(
    node_id="node1",
    cluster_nodes=["node2", "node3"],
)

# 启动节点
await runtime_agent.start()

# 分布式执行
pef = compiler.compile("分析销售数据")
result = await runtime_agent.map_reduce(pef, data_partitions)
```

---

## 项目结构

```
IntentOS/
├── intentos/
│   ├── agent/           # 能力注册中心 (系统调用表)
│   ├── runtime/         # 运行时 Agent (分布式节点代理)
│   ├── semantic_vm/     # 语义 VM (OS 内核, 在每个节点运行)
│   ├── compiler/        # 意图编译器 (用户意图 → PEF)
│   ├── interface/       # 接口层 (REST API + Chat)
│   └── paas/            # PaaS 服务层 (多租户、计费、市场)
│
├── docs/                # 文档
├── examples/            # 示例代码
├── tests/               # 测试用例
├── README.md            # 项目说明
├── ROADMAP.md           # 项目路线图
└── QWEN.md              # 本文件 (项目概括)
```

---

## 核心概念（简要）

### 语义 VM (OS 内核)
- **LLM 作为处理器**, PEF (Prompt Executable File) 作为机器码
- 在每个节点上运行, 跨网络组成整体 OS
- 执行流程: 加载 PEF → LLM 处理 → 需要能力时查询注册中心 → 执行 → 生成结果

### 意图编译器
- **用户自然语言意图 → PEF (Prompt Executable File)**
- 编译时将能力描述注入到 Prompt
- PEF 可缓存、可分发、可跨节点执行

### 能力注册中心 (系统调用表)
- 管理所有 OS 级能力 (Shell/FileSystem/Network/自定义)
- 能力声明输入输出 Schema 和所需权限
- 执行前受 Capability Gate (能力门控) 保护

### 运行时 Agent (节点 Daemon)
- **分布式节点代理**, 在每个节点上运行
- 为本地语义 VM 提供能力实现
- 管理 Skill 缓存
- 分布式运行 (Map-Reduce)、结果汇总

### 接口层
- **对外提供 REST API 和 Chat 访问接口**
- REST API: POST /v1/execute, GET /v1/status, GET /v1/nodes
- Chat Interface: Shell TUI, WebSocket, Web UI

### PaaS 服务层
- **独立于 OS 核心层**, 处理业务逻辑
- 多租户管理、计费系统、应用市场、开发者工具

---

## 📋 项目约定

### 测试代码路径

| 测试类型 | 路径 | 说明 |
|----------|------|------|
| **单元测试** | `tests/unit/test_*.py` | 针对模块/函数的测试 |
| **集成测试** | `tests/integration/test_*.py` | 跨模块集成测试 |
| **端到端测试** | `tests/e2e/test_*.py` | 完整流程测试 |

**命名规范**:
- 测试文件：`test_<module>.py`
- 测试函数：`test_<function>_<scenario>()`
- 测试类：`Test<ClassName>`

**运行测试**:
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_prompts.py -v

# 运行并生成覆盖率报告
pytest --cov=intentos --cov-report=html
```

### 代码组织原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个模块/类/函数只完成一个任务 |
| **显式优于隐式** | 依赖、类型、错误应明确声明 |
| **测试驱动** | 新功能先写测试，再实现代码 |
| **文档即代码** | 关键函数必须有 docstring |

### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**type 类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例**:
```
feat(prompts): 添加提示词缓存优化

- 实现静态/动态部分分离
- 使用 Blake2b 哈希计算缓存键
- 集成到 IntentCompiler

Closes #123
```

---

## 参考文档

完整架构说明请参考：[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

其他文档：
- [核心原则](./docs/CORE_PRINCIPLES.md)
- [AI Native App](./docs/AI_NATIVE_APP.md)
- [分层架构](./docs/LAYERED_ARCHITECTURE.md)
- [计费与收益](./docs/BILLING_AND_REVENUE.md)
- [意图包格式规范](./docs/INTENT_PACKAGE_SPEC.md)
- [安全与权限](./docs/SECURITY_AND_PERMISSIONS.md)
- [性能优化策略](./docs/PERFORMANCE_OPTIMIZATION.md)
- [测试与调试指南](./docs/TESTING_AND_DEBUGGING.md)

---

## 📜 代码修复律令（不可违背）

### ⚠️ 铁律：先读后改

**在任何代码修改前，必须先读取文件内容。**

```
❌ 禁止：未读取文件就直接编辑
✅ 必须：read_file → 理解上下文 → edit
```

**违反示例**:
- 不读取文件就假设内容并修改
- 根据猜测的路径直接编辑
- 不看现有代码结构就重构

**正确做法**:
1. 使用 `read_file` 读取目标文件
2. 理解代码结构、风格、依赖
3. 使用 `edit` 进行精准修改
4. 必要时使用 `glob`/`grep` 确认影响范围

---

### 无损修改三原则

1. **永远不要简化代码、回避问题**
   - 必须解决问题的根源，而非表面症状
   - 必须修复 Bug 的完整链条，而非临时绕过
   - 必须进行无损修改，保留原始代码结构和完整功能

2. **只修改导致错误的具体部分**
   - 精准定位问题根源，最小化修改范围
   - 保留未受影响的所有代码和逻辑
   - 禁止因局部问题而重构无关代码

3. **保留原始代码结构和完整功能**
   - 尊重原有设计意图和架构模式
   - 保留所有注释、文档字符串和类型注解
   - 确保修改后功能等价或更强，绝不削弱

### 违反示例

❌ **错误做法**:
- 因为测试失败而删除测试用例
- 因为类型错误而删除类型注解
- 因为功能复杂而简化实现
- 因为文档过长而删除重要内容
- 因为依赖问题而移除功能模块

### 正确做法

✅ **正确做法**:
- 测试失败 → 修复代码使测试通过
- 类型错误 → 修正类型定义或实现
- 功能复杂 → 保持完整，添加注释说明
- 文档过长 → 保留内容，优化组织结构
- 依赖问题 → 解决依赖，保留功能

---

**QWEN.md 说明**: 本文档是项目概括，帮助快速了解 IntentOS。完整架构说明请参考 [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)。
