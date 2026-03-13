# IntentOS 架构术语规范

## 问题：为什么"层"容易混淆？

当垂直和水平都用"层"时：
- 垂直三层 vs 水平七层
- 容易混淆，不知道在说哪个维度
- 无法清晰表达架构关系

## 解决方案：使用不同术语

### 新术语体系

```
IntentOS 架构 = 垂直三阶 + 水平七阶段

垂直方向 (调用关系): 使用"阶" (Tier)
  - 第一阶：应用阶 (Application Tier)
  - 第二阶：意图阶 (Intent Tier)
  - 第三阶：模型阶 (Model Tier)

水平方向 (处理流程): 使用"阶段" (Stage/Phase)
  - 阶段 1：意图解析阶段
  - 阶段 2：任务规划阶段
  - 阶段 3：上下文收集阶段
  - 阶段 4：安全验证阶段
  - 阶段 5：能力绑定阶段
  - 阶段 6：执行阶段
  - 阶段 7：改进阶段
```

---

## 完整架构图 (新术语)

```
┌─────────────────────────────────────────────────────────────┐
│  IntentOS 架构                                               │
│                                                              │
│  垂直三阶 (调用关系)                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  第一阶：应用阶 (Application Tier)                   │   │
│  │  • 面向用户                                          │   │
│  │  • 接收需求                                          │   │
│  │  • 呈现结果                                          │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │ 调用意图                             │
│                      ↓                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  第二阶：意图阶 (Intent Tier)                        │   │
│  │  • 解析意图                                          │   │
│  │  • 规划执行                                          │   │
│  │  • 管理记忆                                          │   │
│  │                                                      │   │
│  │  水平七阶段 (处理流程)                                │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │  阶段 1: 意图解析 → 阶段 2: 任务规划            │  │   │
│  │  │       ↓              ↓                        │  │   │
│  │  │  阶段 3: 上下文收集 → 阶段 4: 安全验证          │  │   │
│  │  │       ↓              ↓                        │  │   │
│  │  │  阶段 5: 能力绑定 → 阶段 6: 执行               │  │   │
│  │  │       ↓              ↓                        │  │   │
│  │  │  阶段 7: 改进                                  │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │ 执行 Prompt                          │
│                      ↓                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  第三阶：模型阶 (Model Tier)                         │   │
│  │  • 语义理解                                          │   │
│  │  • 推理生成                                          │   │
│  │  • Tool Calling                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 术语对比表

| 维度 | 旧术语 | 新术语 | 英文 |
|------|--------|--------|------|
| **垂直** | 三层 | 三阶 | Three Tiers |
| **水平** | 七层 | 七阶段 | Seven Stages |

### 垂直三阶

| 阶 | 名称 | 职责 | 英文 |
|----|------|------|------|
| **第一阶** | 应用阶 | 面向用户，接收需求 | Application Tier |
| **第二阶** | 意图阶 | 处理意图，协调资源 | Intent Tier |
| **第三阶** | 模型阶 | 语义理解，推理生成 | Model Tier |

### 水平七阶段 (意图阶内部)

| 阶段 | 名称 | 输入 | 输出 | 英文 |
|------|------|------|------|------|
| **阶段 1** | 意图解析 | 自然语言 | StructuredIntent | Intent Parsing |
| **阶段 2** | 任务规划 | StructuredIntent | TaskDAG | Task Planning |
| **阶段 3** | 上下文收集 | TaskDAG | EnrichedContext | Context Collection |
| **阶段 4** | 安全验证 | EnrichedContext | SecurityClearedContext | Safety Verification |
| **阶段 5** | 能力绑定 | SecurityClearedContext | BoundCapabilities | Capability Binding |
| **阶段 6** | 执行 | BoundCapabilities | ExecutionResult | Execution |
| **阶段 7** | 改进 | ExecutionResult | ImprovementSuggestions | Improvement |

---

## 形象比喻 (新术语)

### 餐厅比喻

```
垂直三阶:
├── 第一阶：点餐区 (应用阶)
│   • 顾客点餐
│   • 呈现菜品
│
├── 第二阶：厨房 (意图阶)
│   ├── 阶段 1: 理解订单 (意图解析)
│   ├── 阶段 2: 准备食材 (任务规划)
│   ├── 阶段 3: 查找食谱 (上下文收集)
│   ├── 阶段 4: 检查过敏 (安全验证)
│   ├── 阶段 5: 准备厨具 (能力绑定)
│   ├── 阶段 6: 烹饪 (执行)
│   └── 阶段 7: 品尝调整 (改进)
│
└── 第三阶：供应商 (模型阶)
    • 提供食材
    • 基础能力
```

### 工厂比喻

```
垂直三阶:
├── 第一阶：销售阶 (应用阶)
│   • 接收订单
│   • 交付产品
│
├── 第二阶：生产阶 (意图阶)
│   ├── 阶段 1: 订单解析
│   ├── 阶段 2: 生产计划
│   ├── 阶段 3: 物料准备
│   ├── 阶段 4: 质量检查
│   ├── 阶段 5: 设备准备
│   ├── 阶段 6: 生产制造
│   └── 阶段 7: 工艺改进
│
└── 第三阶：供应链阶 (模型阶)
    • 原材料供应
    • 基础资源
```

---

## 示例：销售分析意图的处理流程 (新术语)

### 垂直三阶处理

```
用户："分析华东区 Q3 销售数据"
    ↓
┌─────────────────────────────────────────┐
│ 第一阶：应用阶                           │
│ • 接收用户输入                           │
│ • 调用：IntentOS.execute()              │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 第二阶：意图阶                           │
│ • 解析意图                               │
│ • 规划执行                               │
│ • 调用模型                               │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 第三阶：模型阶                           │
│ • 理解 Prompt                            │
│ • 生成响应                               │
└─────────────────────────────────────────┘
```

### 水平七阶段处理 (意图阶内部)

```
阶段 1 意图解析:
  输入："分析华东区 Q3 销售数据"
  输出：StructuredIntent(action="analyze", ...)

阶段 2 任务规划:
  输入：StructuredIntent
  输出：TaskDAG(tasks=[...])

阶段 3 上下文收集:
  输入：TaskDAG
  输出：EnrichedContext(user_id="manager_001", ...)

阶段 4 安全验证:
  输入：EnrichedContext
  输出：SecurityClearedContext(permission_check="passed")

阶段 5 能力绑定:
  输入：SecurityClearedContext
  输出：BoundCapabilities(capabilities=[...])

阶段 6 执行:
  输入：BoundCapabilities
  输出：ExecutionResult(success=true, ...)

阶段 7 改进:
  输入：ExecutionResult
  输出：ImprovementSuggestions(suggestions=[...])
```

---

## 代码示例 (新术语)

### 垂直三阶

```python
from intentos import IntentOS

# 第一阶：应用阶
app = create_app(name="SalesApp")

# 第二阶：意图阶
intentos = IntentOS()

# 第三阶：模型阶
llm = create_executor(provider="openai")

# 调用流程 (垂直)
result = await app.execute(user_input)      # 第一阶
result = await intentos.execute(user_input) # 第二阶
result = await llm.execute(prompt)          # 第三阶
```

### 水平七阶段

```python
from intentos import IntentPipeline

# 创建处理流水线
pipeline = IntentPipeline()

# 添加七个阶段
pipeline.add_stage(IntentParsingStage())     # 阶段 1
pipeline.add_stage(TaskPlanningStage())      # 阶段 2
pipeline.add_stage(ContextCollectionStage()) # 阶段 3
pipeline.add_stage(SafetyVerificationStage())# 阶段 4
pipeline.add_stage(CapabilityBindingStage()) # 阶段 5
pipeline.add_stage(ExecutionStage())         # 阶段 6
pipeline.add_stage(ImprovementStage())       # 阶段 7

# 执行流水线
result = await pipeline.execute(user_input)
```

---

## 总结

### 新术语体系

```
IntentOS 架构 = 垂直三阶 + 水平七阶段

垂直三阶 (调用关系):
  第一阶：应用阶 (Application Tier)
  第二阶：意图阶 (Intent Tier) ← 包含七阶段
  第三阶：模型阶 (Model Tier)

水平七阶段 (意图阶内部处理流程):
  阶段 1: 意图解析
  阶段 2: 任务规划
  阶段 3: 上下文收集
  阶段 4: 安全验证
  阶段 5: 能力绑定
  阶段 6: 执行
  阶段 7: 改进
```

### 关键要点

1. **垂直用"阶"**: 表示调用关系的层级
2. **水平用"阶段"**: 表示处理流程的步骤
3. **七阶段在第二阶内**: 七阶段是意图阶的内部处理流程
4. **术语清晰**: 不再混淆"三层"vs"七层"

---

**文档版本**: 4.0 (术语规范版)  
**创建日期**: 2026-03-13  
**最后更新**: 2026-03-13  
**负责人**: IntentOS Team
