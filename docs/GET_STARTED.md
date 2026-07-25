# IntentOS 快速开始指南 (v9.5.0 升华版)

> **AI 时代的 UNIX · 语言即系统 · 隐式管道阻抗匹配 · 创世与凋亡双螺旋**

欢迎来到 **IntentOS**！这是一个 **AI 原生分布式操作系统**，将大语言模型（LLM）视为系统的“语义 CPU”，将高维语义流视为系统的“最小通用介质”。

本指南将帮助你在 5 分钟内掌握安装部署、常驻启动、万能管道级联、以及节点自举去熵的全新范式。

---

## 目录

- [🚀 5 分钟极速上手](#-5-分钟极速上手)
- [🧠 核心理念：AI 时代的 UNIX](#-核心理念ai-时代的-unix)
- [📦 安装指南](#-安装指南)
- [🛠️ 核心示例与进阶玩法](#️-核心示例与进阶玩法)
- [🧩 故障排查](#-故障排查)
- [🌌 下一步](#-下一步)

---

## 🚀 5 分钟极速上手

### 步骤 1: 安装

```bash
# 克隆仓库
git clone https://github.com/jeffery9/intentOS.git
cd intentOS

# 安装内核及高并发 AnyIO 运行时环境
pip install -e .
```

### 步骤 2: 启动你的第一个“语义常驻守护进程 (DaemonRunner)”

在 IntentOS 中，你可以像配置 UNIX 的 crontab 或监听物理网络端口一样，运行常驻进程来捕捉现实事件，并自动级联为语义流水线：

```python
# run_daemon.py
import anyio
from intentos.semantic_vm import SemanticVM
from intentos.runtime import DaemonRunner
from intentos.llm import create_executor

async def main():
    # 1. 创建并初始化语义 VM 核心
    # 我们这里使用 Mock 大脑执行器来进行极速免 API 体验
    llm_executor = create_executor(provider="mock")
    vm = SemanticVM(llm_executor=llm_executor)
    await vm.initialize()
    
    # 2. 组装一个两阶段语义流水线 (Telemetry Pipeline)
    # 步骤一：提取物理遥测并清洗
    # 步骤二：总结系统当前状态健康度
    from intentos.semantic_vm import SemanticProgram, SemanticInstruction, SemanticOpcode
    program = SemanticProgram(name="telem_pipeline_program")
    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE,
        parameters={"intent": "解析原始报文并提取数值"}
    ))
    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE,
        parameters={"intent": "总结管道上下文并输出最终健康度报告"}
    ))
    await vm.load_program(program)
    
    # 3. 注册常驻守护 Daemon，配置 Webhook 模拟网卡触发器
    daemon = DaemonRunner(vm)
    mock_webhook_queue = []
    
    daemon.register_trigger(
        trigger_id="webhook_telemetry_event",
        trigger_type="webhook",
        config={
            "interval_seconds": 1,
            "_mock_webhook_queue": mock_webhook_queue,
            "gas_limit": 500,
            "assertions": ["output_must_be_positive"]
        },
        target_program="telem_pipeline_program"
    )
    
    # 4. 模拟外部物理网卡突然塞入一个遥测事件数据包
    mock_webhook_queue.append({
        "timestamp": 1721865600,
        "raw_payload": "ERR_TEMP_92_DEGREES_STATUS_CRITICAL",
        "reason": "机房温度传感器报警"
    })
    
    # 5. 激发常驻轮询
    print("[Get-Started] 🚀 启动 DaemonRunner 监听现实事件...")
    async with anyio.create_task_group() as tg:
        tg.start_soon(daemon.start)
        
        # 观察 1.5 秒后安全下线
        await anyio.sleep(1.5)
        await daemon.stop()
        print("[Get-Started] ✓ 轮询观察完毕。")

if __name__ == "__main__":
    anyio.run(main)
```

运行：
```bash
python run_daemon.py
```

---

## 🧠 核心理念：AI 时代的 UNIX

```
                    UNIX (1969)                  │               IntentOS (2026)
────────────────────────────────────────────────┼────────────────────────────────────────────────
 最小通用介质 │  Bytes / Text (字节/纯文本)      │  Semantics / Intent (高维语义/意图)
 核心管道连接 │  cat data.txt | grep "error"    │  Read Watcher | Analyze Log | Apoptosis Skill
 阻抗对齐方式 │  手动编写 sed/awk/cut 胶水代码   │  _match_impedance (大模型动态热阻抗转换)
 通信与分发   │  TCP Sockets / IPC 进程间通信   │  SemanticP2P (社会化认知 Gossip / 意图 Relay)
```

### 1. 意图奇点第一推动力 (IntentSingularity)
系统绝不主动产生自我意识，人类意图是唯一的**绝对参照系（Prime Mover）**。在分布式接力流转中，`IntentSingularity` 对象被只读且冻结，包含强制断言（assertions），在每一次管道执行时发挥强制安全审计作用。

### 2. 万能语义阻抗匹配器 (`_match_impedance`)
当上游输出 STDOUT 流往下游 STDIN 时，如果存在接口字段或数据协议格式不对称，虚拟机将在执行前夜自动调用 **阻抗匹配器**（LLM），将散装非结构化文本动态转换、映射为下游 Skill 强类型 JSON 参数字典。**彻底消灭手写胶水代码**。

### 3. Loop 5 细胞自发凋亡 (SkillApoptosisEngine)
为了防止系统因无限自我进化克隆（Loop 4: Genesis）而导致技能和规则臃肿崩溃，系统提供 **数字冥想 (Meditation)** 机制。系统在低负载时段自动扫描、分析技能重合度，融合成更高维的通用技能，并将冲突和冗余技能执行物理注销与凋亡（Apoptosis），达成系统的极简熵减。

---

## 📦 安装指南

### 系统要求
- **Python 3.10+** (推荐 **Python 3.14+** 黄金极客版，测试已完美通过)
- **pip 21.0+**
- 支持的底层大模型后端：OpenAI, Anthropic (Claude), Ollama (本地 Llama 3) 以及 Mock 执行器。

### 生产级安装
```bash
# 从仓库源码本地可编辑模式安装
pip install -e .
```

---

## 🛠️ 核心示例与进阶玩法

### 示例 1: 跨机器分布式意图接力 (SemanticP2P)

多个物理节点可通过 `SemanticP2P` 协议拼装为一整台高维超级操作系统，实现“社会化认知传染”与“意图跨物理网接力执行”：

```python
import anyio
from intentos.distributed import SemanticP2P, P2PNodeManager
from intentos.semantic_vm import SemanticVM, SemanticProgram, SemanticInstruction, SemanticOpcode
from intentos.llm import create_executor

async def p2p_cluster_demo():
    # 1. 组建物理隔离的两个脑节点 Node_A 与 Node_B
    executor_a = create_executor(provider="mock")
    executor_b = create_executor(provider="mock")
    
    vm_a = SemanticVM(llm_executor=executor_a)
    vm_b = SemanticVM(llm_executor=executor_b)
    await vm_a.initialize()
    await vm_b.initialize()
    
    # 2. 组装 P2P 传染网络
    p2p_a = SemanticP2P(node_id="Node_A", vm=vm_a)
    p2p_b = SemanticP2P(node_id="Node_B", vm=vm_b)
    
    await p2p_a.start()
    await p2p_b.start()
    
    # 3. 双向自发节点注册与发现 (Gossip Baseline)
    p2p_a.register_peer("Node_B", p2p_b)
    p2p_b.register_peer("Node_A", p2p_a)
    
    # 4. 在 Node_A 上编写一节意图管道，并委托 P2P 路由跨网接力到 Node_B 执行
    program = SemanticProgram(name="cross_network_pipeline")
    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE,
        parameters={"intent": "对远程网络执行高带宽安全审计清洗"}
    ))
    
    print("[P2P] Node_A 正在将高带宽安全审计意图跨物理网络 Relay 给 Node_B...")
    result = await p2p_a.relay_intent(target_node="Node_B", program=program)
    print(f"[P2P] Node_B 接力执行成功！返回结果内容: {result.get('content')}")
    
    await p2p_a.stop()
    await p2p_b.stop()

if __name__ == "__main__":
    anyio.run(p2p_cluster_demo)
```

---

## 🧩 故障排查

### 问题 1: 导入 `anyio` 报错
*   **症状**：`ModuleNotFoundError: No module named 'anyio'`
*   **解决**：本系统深度基于 anyio 实现高并发的底层 IO 异步网络。请确保执行了 `pip install anyio`。

### 问题 2: 阻抗匹配抛出异常，降级回退
*   **症状**：日志显示 `[VM] 阻抗匹配抛出异常，降级回退至默认参数...`
*   **解决**：大模型对输入数据的 JSON 转换发生了格式错位。如果是生产模型，请推荐配置高精度大模型（如 `gpt-4o` 或 `claude-3-5-sonnet`），并通过在触发器中加签严密的 Schema 解决。

### 问题 3: 动态技能无法删除/凋亡
*   **症状**：在运行数字冥想时，部分 Skill 报错 `属于内核基石，免疫凋亡`。
*   **解决**：IntentOS 内核包含防御保护机制。任何打上 `builtin` 标签或系统内核自带的基础技能（即基石能力）均自动处于免疫（Immune）保护状态，只有处于 `user` 等级的动态进化技能才会被合并和凋亡。

---

## 🌌 下一步

恭喜你！你已经触碰到了 AI 原生分布式操作系统的最前沿阵地。

*   📖 [架构总览](./ARCHITECTURE.md) - 深入理解 P2P 社会化技能传染和事件驱动网关。
*   📖 [分层架构详解](./LAYERED_ARCHITECTURE.md) - 学习从意图编译 PEF 到底层虚拟机坍缩执行的完整 7 级处理原理。
*   📖 [多模态语义管道 I/O 指南](./UNIX_IO_GUIDE.md) - 全面学习如何使用管道符级联任意不对称的输入输出。

**用高维语义，重塑分布式数字世界的秩序吧！** 🚀🌌

---

**最后更新**: 2026-07-25  
**操作系统当前物理版本**: v9.5.0 (I/O & P2P 级联升华版)
