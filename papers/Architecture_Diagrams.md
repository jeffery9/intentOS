# IntentOS 架构图集

## 图 1：套娃分层架构总览

```mermaid
flowchart TB
    subgraph L3["Layer 3: Application Layer (应用层)"]
        A1[CRM App]
        A2[Sales App]
        A3[BI App]
    end
    
    subgraph L2["Layer 2: Intent Layer (意图层)"]
        subgraph L7["7 Level 处理流程"]
            direction TB
            L1["[L1] 意图解析<br/>功能意图 + 操作意图"]
            L2_["[L2] 任务规划<br/>任务 DAG + Ops Model"]
            L3_["[L3] 上下文收集<br/>多模态事件图"]
            L4["[L4] 安全验证<br/>权限校验 + HITL"]
            L5["[L5] 能力绑定<br/>Linker 符号链接"]
            L6["[L6] 执行<br/>分布式调度"]
            L7_["[L7] 改进<br/>意图漂移检测 + 自愈"]
        end
    end
    
    subgraph L1["Layer 1: Model Layer (模型层)"]
        M1[OpenAI GPT-4/4o]
        M2[Anthropic Claude 3/3.5]
        M3[Ollama Llama 3.1]
    end
    
    subgraph INFRA["Cloud Infrastructure"]
        K8s[Kubernetes/ECS]
        Redis[Redis: 短期记忆]
        S3[S3: 长期记忆]
        APIGW[API Gateway]
    end
    
    L3 -->|调用意图 | L2
    L2 -->|执行 Prompt| L1
    L1 -->|Token Stream| L2
    L2 --> INFRA

    style L3 fill:#e1f5fe
    style L2 fill:#fff3e0
    style L1 fill:#f3e5f5
    style INFRA fill:#e8f5e9
```

---

## 图 2：PEF 编译与执行流程

```mermaid
flowchart LR
    subgraph Compilation["意图编译阶段"]
        NL[自然语言意图] --> IC[意图编译器]
        IC --> LA[词法分析]
        LA --> PA[语法分析]
        PA --> SA[语义分析]
        SA --> CG[代码生成]
        CG --> LN[链接器 Linker]
        LN --> PEF[PEF 文件]
    end
    
    subgraph Execution["语义执行阶段"]
        PEF --> LOAD[VM 加载]
        LOAD --> BIND[能力绑定]
        BIND --> DAG[DAG 任务分解]
        DAG --> MEM[记忆注入]
        MEM --> LLM[LLM 执行]
        LLM --> RESULT[结果输出]
    end
    
    Compilation --> Execution
    
    style NL fill:#ffecb3
    style PEF fill:#c8e6c9
    style RESULT fill:#bbdefb
```

---

## 图 3：PEF 文件格式结构

```mermaid
flowchart TB
    subgraph PEF["PEF (Prompt Executable File)"]
        direction TB
        H[Header 头部]
        H --> |魔数 0x50454600| V[版本号]
        V --> E[入口点偏移]
        
        E --> ST[Section Table 段表]
        ST --> T1[.text 段：指令代码]
        ST --> T2[.data 段：静态数据]
        ST --> T3[.rodata 段：只读常量]
        ST --> T4[.symtab 段：符号表]
        ST --> T5[.binding 段：能力绑定]
        
        T5 --> CAP[能力注册表引用]
        CAP --> API[外部 API/工具]
    end

    style PEF fill:#ffe0b2
    style H fill:#ffcc80
    style ST fill:#ffcc80
```

---

## 图 4：分布式自举执行流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Monitor as 监控器
    participant Executor as 自举执行器
    participant Node1 as 节点 1
    participant Node2 as 节点 2
    participant Redis as Redis

    User->>Monitor: 提交意图
    Monitor->>Monitor: 检测负载 > 阈值

    alt 需要扩容
        Monitor->>Executor: 触发扩容元意图
        Executor->>Executor: 生成 Meta-Intent

        Executor->>Node1: REPLICATE PROGRAM self
        Node1->>Node1: 打包内核逻辑
        Node1->>Node2: 发送 PEF + 能力定义

        Executor->>Node2: SPAWN NODE
        Node2->>Node2: 加载 PEF
        Node2->>Node2: 注册服务
        Node2->>Node2: 初始化记忆系统

        Executor->>Redis: BROADCAST CONFIG
        Redis->>Node1: 同步配置
        Redis->>Node2: 同步配置

        Node2->>Executor: 就绪确认
        Executor->>User: 返回扩容完成
    else 无需扩容
        Monitor->>User: 直接执行意图
    end
```

---

## 图 5：协议自扩展器工作流程

```mermaid
flowchart TD
    Start([用户意图输入]) --> Detect{边界冲突检测}
    
    Detect -->|能力缺失 | Gap[识别能力缺口]
    Detect -->|约束冲突 | Violation[识别违规]
    Detect -->|无冲突 | Execute[直接执行]
    
    Gap --> Suggest[生长建议生成]
    Violation --> Suggest
    
    Suggest --> Analyze[语义分析缺口]
    Analyze --> Plan[构建扩展计划]
    
    Plan --> Approve{Human-in-the-loop 审批}
    Approve -->|用户批准 | MetaIntent[转化为元意图]
    Approve -->|用户拒绝 | Reject([拒绝并记录])
    
    MetaIntent --> Patch[协议补全<br/>modify_protocol]
    Patch --> Update[更新能力图谱]
    Update --> Recompile[分层重新生成]
    Recompile --> Execute
    
    Execute --> Result([返回结果])

    style Detect fill:#ffcc80
    style Approve fill:#ffcc80
    style MetaIntent fill:#c8e6c9
    style Patch fill:#c8e6c9
```

---

## 图 6：元意图层级结构

```mermaid
flowchart TB
    subgraph L2["L2: 元元意图 (Meta-Meta-Intent)"]
        MM1["修改意图创建策略"]
        MM2["定义安全边界规则"]
        MM3["扩展协议演化算法"]
    end
    
    subgraph L1["L1: 元意图 (Meta-Intent)"]
        M1["创建新意图模板"]
        M2["注册新能力"]
        M3["修改解析规则"]
        M4["生成修复意图"]
    end
    
    subgraph L0["L0: 任务意图 (Task Intent)"]
        T1["分析销售数据"]
        T2["生成周报"]
        T3["对比区域业绩"]
        T4["预测下季度趋势"]
    end
    
    L2 -->|管理 | L1
    L1 -->|管理 | L0
    L0 -->|执行结果反馈 | L1
    L1 -->|演化记录 | L2

    style L2 fill:#f3e5f5
    style L1 fill:#e1f5fe
    style L0 fill:#e8f5e9
```

---

## 图 7：意图漂移检测与自愈

```mermaid
flowchart TD
    Start([执行开始]) --> Monitor[持续监控执行状态]
    
    Monitor --> Compare{与原始意图对比}
    Compare -->|一致 | Continue[继续执行]
    Compare -->|偏离 | Detect[检测意图漂移]
    
    Detect --> Analyze[分析漂移原因]
    Analyze --> Type{漂移类型}
    
    Type -->|性能下降 | Perf[性能类修复]
    Type -->|逻辑错误 | Logic[逻辑类修复]
    Type -->|能力缺失 | Cap[能力类修复]
    
    Perf --> GenIntent[生成修复意图<br/>Refinement Intent]
    Logic --> GenIntent
    Cap --> GenIntent
    
    GenIntent --> Regenerate[分层重新生成]
    Regenerate --> Recompile[重新编译 PEF]
    Recompile --> ReExecute[重新执行]
    
    ReExecute --> Verify{验证修复效果}
    Verify -->|成功 | Log[记录自愈日志]
    Verify -->|失败 | Escalate[升级至人工干预]
    
    Log --> End([执行完成])
    Escalate --> End

    style Detect fill:#ffcc80
    style GenIntent fill:#c8e6c9
    style Verify fill:#ffcc80
```

---

## 图 8：Map/Reduce 分布式语义执行

```mermaid
flowchart TB
    User[用户意图] --> LB[负载均衡器]

    LB -->|分发 | Map1[Map 节点 1]
    LB -->|分发 | Map2[Map 节点 2]
    LB -->|分发 | Map3[Map 节点 3]

    subgraph Map["Map 阶段：数据局部性优化"]
        Map1 --> Mem1[(本地记忆 1)]
        Map2 --> Mem2[(本地记忆 2)]
        Map3 --> Mem3[(本地记忆 3)]

        Map1 --> LLM1[LLM 推理 1]
        Map2 --> LLM2[LLM 推理 2]
        Map3 --> LLM3[LLM 推理 3]
    end

    LLM1 --> ReduceNode[汇总节点]
    LLM2 --> ReduceNode
    LLM3 --> ReduceNode

    subgraph Reduce["Reduce 阶段：结果汇总"]
        ReduceNode --> LLM_Sum[LLM 智能汇总]
    end

    LLM_Sum --> Result[返回用户]

    style Map fill:#e3f2fd
    style Reduce fill:#fff3e0
    style LLM_Sum fill:#f3e5f5
```

---

## 图 9：语义 CPU 执行模型

```mermaid
flowchart LR
    subgraph SVM["语义虚拟机 (SVM)"]
        direction TB
        PC[PC 计数器] --> Fetch[取指]
        Fetch --> Decode[译码：Prompt 组装]
        Decode --> Inject[上下文注入]
        Inject --> Execute[执行：LLM 调用]
        Execute --> Writeback[写回：Token 解析]
        Writeback --> PC
    end
    
    subgraph Memory["记忆系统"]
        WM[工作记忆<br/>进程内]
        SM[短期记忆<br/>Redis]
        LM[长期记忆<br/>Redis/S3]
    end
    
    subgraph LLM["语义 CPU"]
        Model[LLM 后端<br/>GPT-4/Claude/Ollama]
    end
    
    Inject --> Memory
    Memory --> Inject
    Execute --> Model
    Model --> Writeback

    style SVM fill:#ffe0b2
    style Memory fill:#e8f5e9
    style LLM fill:#e1f5fe
```

---

## 图 10：能力注册与链接机制

```mermaid
flowchart TB
    subgraph App["应用层：意图包"]
        Def[能力定义]
        Schema[输入/输出 Schema]
        Impl[实现：HTTP API/Python 函数]
    end

    subgraph Registry["能力注册中心"]
        Cap1[能力 1: query_sales]
        Cap2[能力 2: compare_regions]
        Cap3[能力 3: render_chart]
    end

    subgraph Compiler["意图编译器"]
        Parse[意图解析]
        Linker[链接器 Linker]
    end

    subgraph Runtime["运行时"]
        PEF[PEF 文件]
        VM[语义 VM]
    end

    Def --> Registry
    Schema --> Registry
    Impl --> Registry

    Parse --> Linker
    Linker -->|符号绑定 | Registry
    Linker --> PEF
    PEF --> VM
    VM -->|调用 | Cap1
    VM -->|调用 | Cap2
    VM -->|调用 | Cap3

    style Registry fill:#c8e6c9
    style Linker fill:#ffcc80
```

---

## 图 11：分布式记忆同步架构

```mermaid
flowchart TB
    subgraph Node1["节点 1"]
        LocalMem1[本地记忆后端]
        Pub1[Publisher]
        Sub1[Subscriber]
    end
    
    subgraph Node2["节点 2"]
        LocalMem2[本地记忆后端]
        Pub2[Publisher]
        Sub2[Subscriber]
    end
    
    subgraph Node3["节点 3"]
        LocalMem3[本地记忆后端]
        Pub3[Publisher]
        Sub3[Subscriber]
    end
    
    subgraph Redis["Redis Pub/Sub"]
        Channel[sync 频道]
    end
    
    Pub1 -->|发布更新 | Channel
    Pub2 -->|发布更新 | Channel
    Pub3 -->|发布更新 | Channel
    
    Channel -->|广播 | Sub1
    Channel -->|广播 | Sub2
    Channel -->|广播 | Sub3
    
    Sub1 -->|更新 | LocalMem1
    Sub2 -->|更新 | LocalMem2
    Sub3 -->|更新 | LocalMem3
    
    style Redis fill:#ffcc80
    style Channel fill:#ffe0b2
```

---

## 图 12：Self-Bootstrap 层级实现

```mermaid
flowchart TB
    subgraph Level3["Level 3: 分布式自举"]
        D1[自我复制]
        D2[自动扩缩容]
        D3[跨节点同步]
    end

    subgraph Level2["Level 2: 指令集扩展"]
        I1[扩展指令集]
        I2[修改系统策略]
        I3[注册新能力]
    end

    subgraph Level1["Level 1: 规则修改"]
        R1[修改解析 Prompt]
        R2[修改执行规则]
        R3[更新意图模板]
    end

    subgraph Level0["Level 0: 基础执行"]
        E1[加载 PEF]
        E2[驱动 LLM]
        E3[返回结果]
    end

    Level3 -->|编排 | Level2
    Level2 -->|定义 | Level1
    Level1 -->|控制 | Level0
    Level0 -->|执行反馈 | Level1
    Level1 -->|演化记录 | Level2
    Level2 -->|自举历史 | Level3

    style Level3 fill:#f3e5f5
    style Level2 fill:#e1f5fe
    style Level1 fill:#fff3e0
    style Level0 fill:#e8f5e9
```

---

## 图 13：软件范式演进对比

```mermaid
quadrantChart
    title "软件范式演进矩阵"
    x-axis "低抽象" --> "高抽象"
    y-axis "静态" --> "动态"
    quadrant-1 "AI 原生 (IntentOS)"
    quadrant-2 "低代码/无代码"
    quadrant-3 "传统编程"
    quadrant-4 "脚本/配置驱动"
    
    "传统编程": [0.2, 0.2]
    "脚本驱动": [0.3, 0.4]
    "低代码平台": [0.6, 0.5]
    "IntentOS": [0.9, 0.9]
```

---

## 图 14：意图执行生命周期

```mermaid
stateDiagram-v2
    [*] --> Received: 接收意图
    
    Received --> Parsing: L1 解析
    Parsing --> Planning: L2 规划
    Planning --> Context: L3 上下文注入
    Context --> Security: L4 安全验证
    
    Security --> Approved: 通过
    Security --> Rejected: 拒绝
    Rejected --> [*]: 返回错误
    
    Approved --> Binding: L5 能力绑定
    Binding --> Execution: L6 执行
    Execution --> Monitoring: L7 监控
    
    Monitoring --> DriftDetected: 检测漂移
    Monitoring --> Completed: 无漂移
    
    DriftDetected --> Refinement: 生成修复意图
    Refinement --> Planning: 重新规划
    
    Completed --> Result: 返回结果
    Result --> [*]

    style Parsing fill:#e1f5fe
    style Planning fill:#e1f5fe
    style Context fill:#fff3e0
    style Security fill:#ffcc80
    style Refinement fill:#c8e6c9
```

---

## 图 15：IntentOS 与 Harness 对比

```mermaid
flowchart TB
    subgraph IntentOS["IntentOS (操作系统层)"]
        IO1[语义 VM]
        IO2[意图编译器]
        IO3[Self-Bootstrap]
        IO4[分布式执行]
        IO5[PEF 标准]
    end
    
    subgraph Harness["Agent Harness (支撑层)"]
        H1[工具编排]
        H2[安全护栏 Guardrails]
        H3[记忆管理]
        H4[观测层 Observability]
        H5[配置文件 AGENTS.md]
    end
    
    IntentOS -->|包含 | Harness
    IO5 -->|执行 | H1
    IO3 -->|使用 | H2
    IO1 -->|依赖 | H3
    
    style IntentOS fill:#e1f5fe
    style Harness fill:#f3e5f5
```

---

## 图 16：图灵完备性与停机机制平衡

```mermaid
flowchart LR
    subgraph TC["图灵完备性"]
        TC1[条件分支]
        TC2[无限迭代]
        TC3[数据操纵]
    end

    subgraph Balance["平衡机制"]
        B1[Gas 燃料机制]
        B2[DAG 无环约束]
        B3[有界递归]
        B4[外部监控]
    end

    subgraph Halt["合理停机"]
        H1[正常完成]
        H2[资源耗尽]
        H3[外部干预]
        H4[异常捕获]
    end

    TC --> Balance
    Balance --> Halt

    style TC fill:#ffcc80
    style Balance fill:#c8e6c9
    style Halt fill:#e1f5fe
```
