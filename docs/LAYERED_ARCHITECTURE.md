# IntentOS 分层架构详解 (v9.5.0 升华版)

> **AI 时代的 UNIX · 极简语义内核 · 全息分布式路由 · 创世与凋亡双螺旋**

**文档版本**: 3.0 (升华版)  
**最后更新**: 2026-07-25  
**状态**: Production Ready

---

## 一、 整体系统架构图 (The Unified Topology)

IntentOS 的架构分为三个清晰的大层次：**最上层是 PaaS 业务与租户计量层**，**中间层是自举的语义虚拟机内核层**，**底层是常驻物理事件与全息 P2P 传染层**。

人类的不可篡改意图（`IntentSingularity`）作为**绝对参照系（第一推动力）**，贯穿所有层次。

```
┌─────────────────────────────────────────────────────────────────┐
│                      人类用户 (The User / Observer)             │
│  • 提供不可篡改的人类意图第一因 (IntentSingularity)               │
│  • 通过自然语言级联语义管道 (Semantic Pipeline: A | B | C)        │
└────────────────────┬────────────────────────────────────────────┘
                     │ 自然语言意图 / 管道激发
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              PaaS 商业计量层 (PaaS Service Layer)               │
│  • 多租户物理隔离 (paas/tenant)    • 用量与 Token 计费 (paas/billing)│
│  • 应用发布与分发 (paas/market)    • 开发者工具链 (paas/tools)      │
└────────────────────┬────────────────────────────────────────────┘
                     │ API 注入 / Gas 额度门控
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              IntentOS 语义内核层 (Semantic Kernel)              │
│  ┌───────────────────────────┐   ┌───────────────────────────┐  │
│  │   意图编译器 (Compiler)   │   │     语义 VM (SemanticVM)  │  │
│  │   • 意图编译 → PEF 可执行 │   │   • 语义 CPU (LLM) 坍缩执行│  │
│  │   • 三级高速编译缓存       │   │   • 内核与用户态特权等级安全  │  │
│  └─────────────┬─────────────┘   └─────────────▲─────────────┘  │
│                │ 产生 PEF                      │ 调用与匹配     │
│                ▼                               │                │
│  ┌─────────────────────────────────────────────┴─────────────┐  │
│  │            万能语义阻抗匹配器 (_match_impedance)           │  │
│  │   • 智能抹平上游 STDOUT 到下游 STDIN 的数据结构和接口不对称   │  │
│  │   • 充当 AI 时代的 sed/awk/cut，彻底消灭物理胶水代码         │  │
│  └─────────────────────────────────────────────┬─────────────┘  │
└────────────────────────────────────────────────┼────────────────┘
                                                 │ 物理/分布式执行
                                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              物理常驻守护与分布式 P2P 传染层                    │
│  ┌───────────────────────────┐   ┌───────────────────────────┐  │
│  │   事件守护 (DaemonRunner)  │   │     分布式网 (SemanticP2P)│  │
│  │   • Webhook 轮询 / Cron   │   │   • 双向动态 Peer 路由注册 │  │
│  │   • 文件 Watcher 物理监控 │   │   • Gossip 社会化技能传染  │  │
│  │   • 捕获现实事件，加签奇点│   │   • relay_intent 跨网接力  │  │
│  └───────────────────────────┘   └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、 内核模块与职责边界

IntentOS 的代码组织高度内聚，核心模块各司其职，互不污染：

| 模块路径 | 逻辑划分 | 核心职责 |
|:---|:---|:---|
| `intentos/core/singularity.py` | **第一推动力** | 代表人类不可篡改、被冻结的原始意图，定义全局一致性断言（assertions）与 GasLimit。 |
| `intentos/semantic_vm/vm.py` | **语义 VM** | LLM 作为“语义 CPU”，安全隔离特权执行，并内置**万能阻抗匹配器（`_match_impedance`）**对齐数据。 |
| `intentos/runtime/daemon.py` | **常驻运行** | 物理事件轮询、Webhook 缓存队列拦截、Cron 定时和文件 Watcher 物理捕捉。 |
| `intentos/distributed/p2p.py` | **分布式传染** | 运行全息 Gossip 认知社会化传染，以及跨网 `relay_intent` 管道弹性委托。 |
| `intentos/meditation/engine.py` | **自举与凋亡** | `SkillApoptosisEngine` 在空闲时运行 Meditation 数字冥想，自发合并重合规则、剪枝并对冗余 Skill 执行细胞凋亡。 |
| `intentos/skill/` | **物理器官** | 本地及 evolved 动态技能物理存储中心。 |

---

## 三、 深度剖析：语义 VM 的双层执行流

### 3.1 意图注入与事件加签 (Event Ingestion)
当现实物理世界发生波动时（例如 Webhook 塞入了一条温度报错报文）：
1.  `DaemonRunner` 捕获事件，将其封装为 `IntentSingularity` 意图奇点。
2.  奇点包含人类初始意图描述和约束条件。
3.  系统将事件 Payload 写入变量空间 `_last_result`，激活语义 VM。

### 3.2 管道级联与阻抗匹配 (Pipeline & Impedance Matching)
在 VM 内执行两级管道时：
1.  系统检测到上游步骤输出的 `_last_result` 自动重命名为下游步骤的 `_stdin`。
2.  在唤醒下游 Skill 物理执行前夜，由于上下游接口不对称（如散装文本 vs 强类型 JSON），VM 动态执行 **`_match_impedance`**（阻抗匹配拦截器）。
3.  大模型充当热胶水层，将上游散装数据完美转换为下游 Skill 强类型参数。

### 3.3 物理执行与 Fallback 回退 (Execution Loop)
1.  **物理能力优先**：VM 检索本地 `SkillStore`。若能匹配到 physical 技能或 MCP，以匹配完的合规 JSON 迅速触发。
2.  **大模型自举兜底**：若物理调用遇到障碍，无缝降级回退到高精度 LLM 模拟（Consultant 路由大模型），保证管道不发生物理崩溃，并在运行中逆向提炼经验。

---

## 四、 代码组织树

系统物理代码结构如下：

```
intentos/
├── core/                    # 核心不可变数据模型
│   ├── __init__.py          # 核心导出
│   ├── models.py            # Context/Capability/Intent 等 Pydantic 基类
│   └── singularity.py       # 意图奇点第一推动力（Prime Mover）不可变模型
│
├── semantic_vm/             # 语义虚拟机
│   ├── __init__.py
│   ├── vm.py                # SemanticVM 核心 & _match_impedance 阻抗匹配器
│   └── safe_eval.py         # 安全沙箱 AST 解析
│
├── runtime/                 # 常驻事件调度运行时
│   ├── __init__.py          # 导出 RuntimeAgent, DaemonRunner
│   └── daemon.py            # DaemonRunner、触发器和 Webhook 轮询器
│
├── distributed/             # 分布式基础设施
│   ├── __init__.py          # 导出 SemanticP2P、P2PNode
│   └── p2p.py               # P2P 邻居动态注册、Gossip 认知传染与 cross-network 意图接力
│
├── meditation/              # 数字自引导演化与熵减层
│   ├── __init__.py          # 导出 SkillApoptosisEngine
│   ├── engine.py            # Skill 凋亡引擎与数字冥想管理
│   ├── merger.py            # 认知记忆合并器
│   └── pruner.py            # 冗余裁剪器
│
├── skill/                   # 物理 Skill 存储中心
│   ├── __init__.py          # 导出 SkillStore
│   └── store.py             # FDL/PEF 规则的物理与 YAML 载入
│
└── paas/                    # PaaS 商业与租户层 (与 VM 内核完全物理隔离)
    ├── tenant.py            # 多租户管理
    ├── billing.py           # 用量计量与账单生成
    └── marketplace.py       # 意图包/应用市场分发
```

---

## 五、 总结：大一统分层的好处

1.  **极简自愈内核**：
    内核层（`semantic_vm/`）只有纯粹的语义指令流转与自举沙箱，不沾染任何业务、计费、多租户等“脏逻辑”。
2.  **物理与认知分流**：
    `DaemonRunner` 负责抓取物理世界的粗糙输入，而 `SemanticP2P` 负责全网节点间精纯智力的社会化 Gossip 传染，物理现实与高维认知在语义管道的捏合下达成极简的大一统。
3.  **万物即插即用**：
    通过 `_match_impedance`，开发者不再需要为各种应用间的接口不对称写厚重的胶水适配层，所有的分布式模块都可以像 UNIX 积木一样自由级联、奔流。

---

**文档版本**: 3.0  
**最后更新**: 2026-07-25  
**状态**: Production Ready
