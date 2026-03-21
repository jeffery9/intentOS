# IntentOS 架构文档

> **分布式语义 VM · 运行时 Agent · PaaS 服务层**

**文档版本**: 1.1
**创建日期**: 2026-03-21
**最后更新**: 2026-03-21
**状态**: Release Candidate

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│              PaaS 服务层 (intentos/paas/)                   │
│          AI Native App 层（构建在 OS 之上的服务层）           │
│  • 多租户管理 • 计费系统 • 应用市场 • 开发者工具            │
└────────────────────┬────────────────────────────────────────┘
                     │ 使用 OS API
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              接口层 (intentos/interface/)                   │
│              分布式 OS 对外访问入口                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  REST API                                            │   │
│  │  • POST /v1/execute - 执行意图                       │   │
│  │  • GET /v1/status - 查看状态                         │   │
│  │  • GET /v1/nodes - 查看节点                          │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Chat Interface                                      │   │
│  │  • Shell TUI - 命令行聊天界面                        │   │
│  │  • WebSocket - 实时聊天                              │   │
│  │  • Web UI - Web 界面                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│         分布式语义 VM 集群 (跨网络组成整体 OS)                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  节点 1 (容器/主机)                                  │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  语义 VM                                     │   │   │
│  │  │  • 运行 PEF                                  │   │   │
│  │  │  • LLM 执行                                  │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │  AI Agent (智能代理)                │   │   │   │
│  │  │  │  • 基于 LLM                          │   │   │   │
│  │  │  │  • 理解意图、规划任务                │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  运行时 Agent (分布式节点代理)              │   │   │
│  │  │  • 提供本地能力（shell、文件系统）           │   │   │
│  │  │  • 管理 Skill 缓存                           │   │   │
│  │  │  • 分布式运行（Map-Reduce）                  │   │   │
│  │  │  • 结果汇总（LLM 汇总）                       │   │   │
│  │  │  • 跨节点通信                                │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────┼─────────────────────────────┐   │
│  │                        │ 跨网络通信                   │   │
│  └────────────────────────┼─────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │  节点 2 (容器/主机)                                  │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  语义 VM                                     │   │   │
│  │  │  • 运行 PEF                                  │   │   │
│  │  │  • LLM 执行                                  │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  运行时 Agent                                │   │   │
│  │  │  • 提供本地能力                              │   │   │
│  │  │  • 分布式运行                                │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

架构层次:
1. PaaS 服务层 - AI Native App 层（构建在 OS 之上的服务层）
2. 接口层 - 分布式 OS 对外访问入口
3. 分布式语义 VM 集群 - 跨网络组成整体 OS
```

**重要区分**：
- **AI Agent** (`intentos/agent/`) - 智能代理，基于 LLM，在语义 VM 内部
- **运行时 Agent** (`intentos/runtime/`) - 分布式节点代理，在语义 VM 外部，是 OS 基础设施
- **语义 VM** (`intentos/semantic_vm/`) - 在每个节点上运行，跨网络组成整体 OS
- **接口层** (`intentos/interface/`) - 对外提供 REST API 和 Chat 访问接口

---

## 接口层（对外服务）

**接口层** (`intentos/interface/`) 是分布式 OS 对外的统一访问入口：

### REST API

```
┌─────────────────────────────────────────────────────────────┐
│  REST API (intentos/interface/)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  POST /v1/execute       - 执行意图                   │   │
│  │  GET  /v1/status        - 查看状态                   │   │
│  │  GET  /v1/nodes         - 查看节点                   │   │
│  │  GET  /v1/wallet        - 查看钱包                   │   │
│  │  GET  /v1/usage         - 查看用量                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**使用示例**：
```bash
# 执行意图
curl -X POST http://localhost:8080/v1/execute \
     -H "Content-Type: application/json" \
     -d '{"intent": "分析华东区 Q3 销售数据"}'

# 查看状态
curl http://localhost:8080/v1/status

# 查看节点
curl http://localhost:8080/v1/nodes
```

### Chat Interface

```
┌─────────────────────────────────────────────────────────────┐
│  Chat Interface (intentos/interface/)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Shell TUI          - 命令行聊天界面                 │   │
│  │  WebSocket          - 实时聊天                      │   │
│  │  Web UI             - Web 界面                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**使用示例**：
```bash
# 启动 Shell
PYTHONPATH=. python intentos/interface/shell.py

# 启动 WebSocket 服务器
PYTHONPATH=. python intentos/interface/websocket.py

# 启动 Web UI
PYTHONPATH=. python intentos/interface/web.py
```

### 接口层与分布式 OS 的关系

```
┌─────────────────────────────────────────────────────────────┐
│  接口层                                                     │
│  • 统一入口（REST API + Chat）                              │
│  • 负载均衡（分发请求到不同节点）                           │
│  • 认证授权（API Key、OAuth2）                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  分布式语义 VM 集群                                          │
│  • 节点 1 • 节点 2 • ... • 节点 N                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、运行时 Agent（基于第一性原理）

### 2.1 为什么需要运行时 Agent？

**问题**：IntentOS 是分布式 OS，语义 VM 运行在多个节点（容器/主机）上，跨网络组成整体 OS。如何管理每个节点的本地资源和能力？

**基于第一性原理的分析**：

**第一性原理 1：分布式语义 VM**
- 语义 VM 在每个节点上运行
- 多个语义 VM 跨网络通信，组成整体 OS
- 运行时 Agent 在每个节点上，为本地语义 VM 提供能力
- ✅ **结论**：运行时 Agent 是分布式 OS 的节点基础设施，为本地语义 VM 提供服务

**第一性原理 2：能力与执行分离**
- 语义 VM：定义能力（语义描述），执行 PEF
- 运行时 Agent：提供能力的具体实现（本地 shell、文件系统等）
- ✅ **结论**：运行时 Agent 是能力的提供者，语义 VM 是能力的使用者

**第一性原理 3：按需加载**
- 语义 VM：PEF 包含能力引用
- 运行时 Agent：按需下载/缓存 Skill，提供能力实现
- ✅ **结论**：运行时 Agent 管理能力的生命周期（下载、缓存、供应）

### 2.2 运行时 Agent 的职责

**职责 1：为本地语义 VM 提供能力**
```python
class RuntimeAgent:
    def __init__(self, node_id, semantic_vm):
        self.node_id = node_id
        self.semantic_vm = semantic_vm  # 本地语义 VM
        self.local_capabilities = {
            "shell": ShellCapability(),
            "filesystem": FileSystemCapability(),
            "network": NetworkCapability(),
        }
        self.register_capabilities()
    
    def register_capabilities(self):
        for cap_id, cap in self.local_capabilities.items():
            self.semantic_vm.registry.register(
                id=cap_id,
                description=cap.description,
                handler=cap.execute,
            )
```

**职责 2：App 分发和缓存**
```python
class RuntimeAgent:
    def __init__(self, node_id, app_cache_dir):
        self.node_id = node_id
        self.app_cache_dir = app_cache_dir
        self.app_instances = {}  # App 实例缓存
    
    async def on_startup(self):
        # 节点启动时预加载常用 App
        await self.download_apps(["data_analyst", "code_generator"])
    
    async def get_app(self, app_id, version=None):
        """
        获取 App 实例（按需下载和生成）
        
        1. 检查缓存中是否有 App 实例
        2. 如果没有，检查是否有 App 包
        3. 如果没有，从远程仓库下载 App 包
        4. 生成 App 实例并缓存
        """
        cache_key = f"{app_id}:{version or 'latest'}"
        
        # 1. 检查 App 实例缓存
        if cache_key in self.app_instances:
            return self.app_instances[cache_key]
        
        # 2. 检查 App 包缓存
        app_package = await self.get_app_package(app_id, version)
        
        # 3. 生成 App 实例
        app_instance = await self.generate_app_instance(app_package)
        
        # 4. 缓存 App 实例
        self.app_instances[cache_key] = app_instance
        
        return app_instance
    
    async def generate_app_instance(self, app_package):
        """
        根据 App 包生成 App 实例
        
        App 实例包含：
        - 意图定义
        - 能力绑定
        - 配置信息
        """
        # 解析 App 包
        intents = app_package.intents
        capabilities = app_package.capabilities
        
        # 绑定能力
        bound_capabilities = await self.bind_capabilities(capabilities)
        
        # 生成 App 实例
        app_instance = AppInstance(
            app_id=app_package.id,
            intents=intents,
            capabilities=bound_capabilities,
        )
        
        return app_instance
```

**职责 3：Skill 缓存和下载**
```python
class RuntimeAgent:
    async def get_skill(self, skill_id):
        if not self.is_skill_cached(skill_id):
            await self.download_skill(skill_id)
        return self.load_skill(skill_id)
```

**职责 4：分布式运行**
```python
class RuntimeAgent:
    async def execute_distributed(self, pef, target_nodes):
        """在多个节点上分布式执行 PEF"""
        tasks = [
            self.forward_to_node(node_id, {"type": "execute", "pef": pef})
            for node_id in target_nodes
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip(target_nodes, results))
    
    async def map_reduce(self, pef, data_partitions):
        """Map-Reduce 模式执行"""
        map_tasks = [
            self.forward_to_node(node_id, {"type": "execute", "pef": pef, "data": partition})
            for node_id, partition in data_partitions.items()
        ]
        map_results = await asyncio.gather(*map_tasks)
        return await self.reduce_results(map_results)
    
    async def reduce_results(self, results):
        """汇总多个节点的结果（使用 LLM）"""
        summary_prompt = self.build_summary_prompt(results)
        return await self.semantic_vm.execute(summary_prompt)
```

**职责 5：跨节点通信**
```python
class RuntimeAgent:
    async def forward_to_node(self, target_node_id, message):
        target_node = self.cluster_nodes.get(target_node_id)
        return await target_node.send(message)
    
    async def broadcast(self, message):
        await asyncio.gather([
            node.send(message)
            for node in self.cluster_nodes.values()
        ])
```

### 2.3 App 分发和缓存流程

```
1. 用户请求执行 App
   ↓
2. 运行时 Agent 检查 App 实例缓存
   ↓
3. 如果缓存命中 → 直接使用
   ↓
4. 如果缓存未命中 → 检查 App 包缓存
   ↓
5. 如果 App 包未命中 → 从远程仓库下载
   ↓
6. 生成 App 实例
   ↓
7. 缓存 App 实例
   ↓
8. 执行 App
```

### App 实例生成

```python
# App 包（从仓库下载）
app_package = {
    "id": "data_analyst",
    "version": "1.0.0",
    "intents": [...],
    "capabilities": [...],
}

# App 实例（运行时生成）
app_instance = {
    "id": "data_analyst:node1:12345",  # 唯一实例 ID
    "app_id": "data_analyst",
    "node_id": "node1",
    "intents": [...],
    "capabilities": {
        "data_loader": bound_capability_1,
        "analyzer": bound_capability_2,
    },
    "config": {...},
}
```

### 2.4 分布式运行示例

**示例 1：分布式数据分析**
```python
async def distributed_data_analysis():
    pef = compiler.compile("分析销售数据")
    
    data_partitions = {
        "node1": "华东区销售数据",
        "node2": "华南区销售数据",
        "node3": "华北区销售数据",
    }
    
    runtime_agent = RuntimeAgent("node0", cluster_nodes)
    result = await runtime_agent.map_reduce(pef, data_partitions)
    
    # result = """
    # 全国销售分析汇总:
    # - 华东区：$5M (环比 +15%)
    # - 华南区：$3M (环比 +10%)
    # - 华北区：$4M (环比 +12%)
    # 全国总计：$12M (环比 +12.3%)
    # """
    return result
```

**示例 2：分布式技能调用**
```python
async def distributed_skill_execution():
    pef = compiler.compile("查询天气")
    target_nodes = ["beijing_node", "shanghai_node", "guangzhou_node"]
    
    runtime_agent = RuntimeAgent("node0", cluster_nodes)
    results = await runtime_agent.execute_distributed(pef, target_nodes)
    
    # results = {
    #     "beijing_node": "北京：晴，25°C",
    #     "shanghai_node": "上海：多云，28°C",
    #     "guangzhou_node": "广州：小雨，30°C",
    # }
    
    summary = await runtime_agent.reduce_results(list(results.values()))
    # summary = "北京晴朗 25°C，上海多云 28°C，广州小雨 30°C"
    
    return summary
```

### 2.4 运行时 Agent 与 AI Agent 的关系

```
┌─────────────────────────────────────────────────────────────┐
│  节点 1                                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  语义 VM                                             │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  AI Agent (智能代理)                        │   │   │
│  │  │  • 基于 LLM                                  │   │   │
│  │  │  • 理解意图、规划任务                        │   │   │
│  │  │  • 调用工具（通过能力注册中心）              │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │         │                                           │   │
│  │         │ 调用能力                                  │   │
│  │         ▼                                           │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  能力注册中心                                │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │         │                                           │   │
│  │         │ 查找实现                                  │   │
│  │         ▼                                           │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  运行时 Agent                                │   │   │
│  │  │  • 提供能力实现                              │   │   │
│  │  │  • 分布式运行（Map-Reduce）                  │   │   │
│  │  │  • 结果汇总（LLM 汇总）                       │   │   │
│  │  │  • 跨节点通信                                │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 目录结构

```
intentos/
├── agent/                 # AI Agent（智能代理）
│   ├── agent.py           # AIAgent 主实现
│   ├── mcp_integration.py # MCP 集成
│   └── skill_integration.py # Skill 集成
│
├── runtime/               # 运行时 Agent（分布式节点代理）
│   ├── __init__.py
│   ├── agent.py           # RuntimeAgent 主实现
│   ├── capabilities/      # 本地能力
│   │   ├── shell.py       # Shell 能力
│   │   ├── filesystem.py  # 文件系统能力
│   │   └── network.py     # 网络能力
│   ├── skill_cache.py     # Skill 缓存管理
│   └── skill_downloader.py # Skill 下载器
│
├── semantic_vm/           # 语义 VM（在每个节点上运行）
│   ├── __init__.py
│   ├── vm.py              # 语义 VM 主实现
│   ├── compiler.py        # 意图编译器
│   └── executor.py        # 执行引擎
│
└── paas/                  # PaaS 服务层
```

---

## 三、PaaS 层：AI Native App 层

### 3.1 PaaS 层的定位

**PaaS 层是在 OS 之外构建的 AI Native App 层**，构建在分布式 OS 之上的服务层：

```
┌─────────────────────────────────────────────────────────────┐
│  PaaS 服务层 (AI Native App 层)                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  多租户管理                                          │   │
│  │  • 租户隔离 • 资源配置 • 配额管理                    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  计费系统                                            │   │
│  │  • 用量计量 • 账单生成 • 支付网关 • 收益分成         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  应用市场                                            │   │
│  │  • App 发布 • 审核 • 上架 • 评价                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  开发者工具                                          │   │
│  │  • SDK • CLI • 调试器 • 文档                         │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │ 使用 OS API
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  分布式 OS (接口层 + 语义 VM 集群 + 运行时 Agent)             │
└─────────────────────────────────────────────────────────────┘
```

**关键理解**：
- ✅ **PaaS 层在 OS 之外** - 不是 OS 的一部分，是构建在 OS 之上的服务层
- ✅ **AI Native App 层** - 基于 OS API 构建的 AI Native 应用
- ✅ **使用 OS API** - 通过接口层（REST API + Chat）与 OS 交互
- ✅ **业务逻辑层** - 处理多租户、计费、市场等业务逻辑

### 3.2 PaaS 层与 OS 的关系

```python
# PaaS 层使用 OS 的 API
from intentos import Agent, AgentContext

# PaaS 层：多租户管理
class TenantManager:
    def __init__(self):
        # 使用 OS 的 Agent
        self.agent = Agent()
    
    def execute_intent(self, tenant_id, user_id, intent):
        # 创建上下文（租户隔离）
        context = AgentContext(tenant_id=tenant_id, user_id=user_id)
        
        # 调用 OS API 执行意图
        result = await self.agent.execute(intent, context)
        
        # 记录用量（计费）
        self.billing.record_usage(tenant_id, result.usage)
        
        return result
```

### 3.3 PaaS 层的模块

| PaaS 模块 | 功能 | 说明 |
|----------|------|------|
| **多租户管理** | 租户隔离、资源配置 | 业务逻辑：管理租户和资源 |
| **计费系统** | 用量计量、账单生成 | 业务逻辑：计费和收益分成 |
| **应用市场** | App 发布、审核、分发 | 业务逻辑：AI Native App 市场 |
| **开发者工具** | SDK、CLI、文档 | 业务逻辑：帮助开发者构建 AI Native App |

### 3.4 PaaS 层的第一性原理评估

| 第一性原理 | PaaS 层设计 | 符合度 |
|-----------|-----------|--------|
| **语言即系统** | PaaS 层独立于 OS，通过 OS API 交互 | ✅ |
| **Prompt 即可执行文件** | PaaS 层管理 App 生命周期，不修改 PEF | ✅ |
| **语义 VM** | PaaS 层管理资源，不介入语义执行 | ✅ |

**总体评估**：PaaS 层是构建在 OS 之上的 AI Native App 层，通过 OS API 与 OS 交互，处理业务逻辑。

---

## 四、IO 能力说明

**IO 能力层** (`intentos/agent/`) 是语义 VM 内部的高层级组件，在**编译/链接 PEF 过程中**将 IO 能力注入到 prompt：

| IO 能力 | 模块 | 作用 |
|--------|------|------|
| **Shell 能力** | `agent.py` | 提供 shell 命令执行能力 |
| **MCP 集成** | `mcp_integration.py` | 提供 MCP 工具调用能力 |
| **Skills 集成** | `skill_integration.py` | 提供技能调用能力 |
| **能力注册** | `registry.py` | 注册和管理所有 IO 能力 |

**IO 能力的定位**：
- ✅ **属于 OS 内核** - 是语义 VM 的有机组成部分，不是外部工具
- ✅ **处于高层级** - 在语义 VM 内部，为 PEF 编译/链接提供 IO 能力
- ✅ **注入到 Prompt** - 在编译/链接时将 IO 能力注入到 prompt
- ✅ **LLM 驱动调用** - LLM 返回工具调用时触发 IO 能力执行

**IO 能力在 PEF 编译/链接中的作用**：
```
1. 用户意图 → 意图解析 → 任务规划
   ↓
2. 编译/链接 PEF
   ↓
3. 注入 IO 能力**引用**到 Prompt（不是具体实现）
   ↓
4. 生成 PEF（包含能力描述，不包含具体实现）
```

**PEF 执行过程中的 IO 能力调用（Loop 机制）**：
```
1. 执行 PEF
   ↓
2. LLM 处理 Prompt（已包含 IO 能力描述）
   ↓
3. LLM 返回工具调用（包含 IO 能力调用）
   ↓
4. 检测到 IO 能力调用
   ↓
5. 查找能力注册中心，获取具体实现
   ↓
6. 调用 IO 能力获取数据
   ↓
7. 将 IO 结果返回给 LLM
   ↓
8. LLM 再次处理（可能需要再次调用工具）
   ↓
9. 重复步骤 3-8，直到不再需要工具调用 ← Loop
   ↓
10. LLM 生成最终结果
```

**编译/链接时 vs 执行时**：
- **编译/链接时**：注入 IO 能力**引用**到 Prompt → 生成 PEF
- **执行时**：LLM Loop 调用 IO 能力 → 从注册中心获取实现 → 获取数据 → 直到不再需要 Loop → 生成结果

---

## 五、参考文档

| 文档 | 说明 |
|------|------|
| [AI Native App 概述](./AI_NATIVE_APP.md) | AI Native App 概念、架构、开发指南 |
| [核心原则](./CORE_PRINCIPLES.md) | 语言即系统 · Prompt 即可执行文件 · 语义 VM |
| [分层架构](./LAYERED_ARCHITECTURE.md) | IntentOS 核心层 + PaaS 服务层 |
| [计费与收益](./BILLING_AND_REVENUE.md) | 计费模式、收益分成、账单管理 |
| [意图包格式规范](./INTENT_PACKAGE_SPEC.md) | manifest.yaml Schema |
| [安全与权限](./SECURITY_AND_PERMISSIONS.md) | 权限模型、安全策略 |
| [性能优化策略](./PERFORMANCE_OPTIMIZATION.md) | 缓存策略、并行执行 |
| [测试与调试指南](./TESTING_AND_DEBUGGING.md) | 单元测试、集成测试 |

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate
