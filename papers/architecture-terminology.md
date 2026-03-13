# IntentOS 架构术语规范

## 问题：为什么需要不同术语？

当垂直和水平都用"层"时：
- 垂直三层 vs 水平七层
- 容易混淆，不知道在说哪个维度
- 无法清晰表达架构关系

## 解决方案：使用完全不同的术语

### 新术语体系

```
IntentOS 架构 = 垂直三层 + 水平七级

垂直方向 (调用关系): 使用"层" (Layer)
  - 应用层 (Application Layer)
  - 意图层 (Intent Layer)
  - 模型层 (Model Layer)

水平方向 (处理流程): 使用"级" (Level/Stage)
  - 1 级：意图解析
  - 2 级：任务规划
  - 3 级：上下文收集
  - 4 级：安全验证
  - 5 级：能力绑定
  - 6 级：执行
  - 7 级：改进
```

---

## 完整架构图 (新术语)

```
┌─────────────────────────────────────────────────────────────┐
│  IntentOS 架构                                               │
│                                                              │
│  垂直三层 (调用关系)                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  应用层 (Application Layer)                          │   │
│  │  • 面向用户                                          │   │
│  │  • 接收需求                                          │   │
│  │  • 呈现结果                                          │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │ 调用意图                             │
│                      ↓                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  意图层 (Intent Layer)                               │   │
│  │  • 解析意图                                          │   │
│  │  • 规划执行                                          │   │
│  │  • 管理记忆                                          │   │
│  │                                                      │   │
│  │  水平七级 (处理流程)                                  │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │  1 级：意图解析 → 2 级：任务规划               │  │   │
│  │  │       ↓              ↓                        │  │   │
│  │  │  3 级：上下文收集 → 4 级：安全验证             │  │   │
│  │  │       ↓              ↓                        │  │   │
│  │  │  5 级：能力绑定 → 6 级：执行                   │  │   │
│  │  │       ↓              ↓                        │  │   │
│  │  │  7 级：改进                                    │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │ 执行 Prompt                          │
│                      ↓                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  模型层 (Model Layer)                                │   │
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
| **垂直** | 三层 | **三层** | Three Layers |
| **水平** | 七层 | **七级** | Seven Levels |

### 垂直三层

| 层 | 名称 | 职责 | 英文 |
|----|------|------|------|
| **应用层** | Application Layer | 面向用户，接收需求 | User-Facing |
| **意图层** | Intent Layer | 处理意图，协调资源 | Intent Processing |
| **模型层** | Model Layer | 语义理解，推理生成 | Semantic Understanding |

### 水平七级 (意图层内部)

| 级 | 名称 | 输入 | 输出 | 英文 |
|----|------|------|------|------|
| **1 级** | 意图解析 | 自然语言 | StructuredIntent | Intent Parsing |
| **2 级** | 任务规划 | StructuredIntent | TaskDAG | Task Planning |
| **3 级** | 上下文收集 | TaskDAG | EnrichedContext | Context Collection |
| **4 级** | 安全验证 | EnrichedContext | SecurityClearedContext | Safety Verification |
| **5 级** | 能力绑定 | SecurityClearedContext | BoundCapabilities | Capability Binding |
| **6 级** | 执行 | BoundCapabilities | ExecutionResult | Execution |
| **7 级** | 改进 | ExecutionResult | ImprovementSuggestions | Improvement |

---

## 形象比喻

### 医院比喻

```
垂直三层:
├── 应用层：门诊大厅
│   • 患者挂号
│   • 呈现诊断结果
│
├── 意图层：诊疗流程 (七级)
│   ├── 1 级：问诊 (意图解析)
│   ├── 2 级：制定治疗方案 (任务规划)
│   ├── 3 级：查看病历 (上下文收集)
│   ├── 4 级：过敏检查 (安全验证)
│   ├── 5 级：准备药品/器械 (能力绑定)
│   ├── 6 级：治疗 (执行)
│   └── 7 级：复诊调整 (改进)
│
└── 模型层：检验科/药房
    • 提供检验结果
    • 提供药品
```

### 酒店比喻

```
垂直三层:
├── 应用层：前台
│   • 客人入住
│   • 提供服务
│
├── 意图层：服务流程 (七级)
│   ├── 1 级：理解需求 (意图解析)
│   ├── 2 级：安排服务 (任务规划)
│   ├── 3 级：查看客人偏好 (上下文收集)
│   ├── 4 级：安全检查 (安全验证)
│   ├── 5 级：准备房间/设备 (能力绑定)
│   ├── 6 级：提供服务 (执行)
│   └── 7 级：满意度调查 (改进)
│
└── 模型层：后勤部门
    • 提供基础服务
```

---

## 示例：销售分析意图的处理流程 (新术语)

### 垂直三层处理

```
用户："分析华东区 Q3 销售数据"
    ↓
┌─────────────────────────────────────────┐
│ 应用层                                   │
│ • 接收用户输入                           │
│ • 调用：IntentOS.execute()              │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 意图层                                   │
│ • 解析意图                               │
│ • 规划执行                               │
│ • 调用模型                               │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 模型层                                   │
│ • 理解 Prompt                            │
│ • 生成响应                               │
└─────────────────────────────────────────┘
```

### 水平七级处理 (意图层内部)

```
1 级 意图解析:
  输入："分析华东区 Q3 销售数据"
  输出：StructuredIntent(action="analyze", ...)

2 级 任务规划:
  输入：StructuredIntent
  输出：TaskDAG(tasks=[...])

3 级 上下文收集:
  输入：TaskDAG
  输出：EnrichedContext(user_id="manager_001", ...)

4 级 安全验证:
  输入：EnrichedContext
  输出：SecurityClearedContext(permission_check="passed")

5 级 能力绑定:
  输入：SecurityClearedContext
  输出：BoundCapabilities(capabilities=[...])

6 级 执行:
  输入：BoundCapabilities
  输出：ExecutionResult(success=true, ...)

7 级 改进:
  输入：ExecutionResult
  输出：ImprovementSuggestions(suggestions=[...])
```

---

## 代码示例 (新术语)

### 垂直三层

```python
from intentos import IntentOS

# 应用层
app = create_app(name="SalesApp")

# 意图层
intentos = IntentOS()

# 模型层
llm = create_executor(provider="openai")

# 调用流程 (垂直)
result = await app.execute(user_input)      # 应用层
result = await intentos.execute(user_input) # 意图层
result = await llm.execute(prompt)          # 模型层
```

### 水平七级

```python
from intentos import IntentPipeline

# 创建处理流水线
pipeline = IntentPipeline()

# 添加七级处理
pipeline.add_level(IntentParsingLevel())      # 1 级
pipeline.add_level(TaskPlanningLevel())       # 2 级
pipeline.add_level(ContextCollectionLevel())  # 3 级
pipeline.add_level(SafetyVerificationLevel()) # 4 级
pipeline.add_level(CapabilityBindingLevel())  # 5 级
pipeline.add_level(ExecutionLevel())          # 6 级
pipeline.add_level(ImprovementLevel())        # 7 级

# 执行流水线
result = await pipeline.execute(user_input)
```

---

## 记忆口诀

```
垂直三层：应 - 意 - 模 (应用层、意图层、模型层)
水平七级：解 - 规 - 收 - 验 - 绑 - 执 - 改
         (解析、规划、收集、验证、绑定、执行、改进)
```

---

## 总结

### 新术语体系

```
IntentOS 架构 = 垂直三层 + 水平七级

垂直三层 (调用关系):
  应用层 (Application Layer)
  意图层 (Intent Layer) ← 包含七级
  模型层 (Model Layer)

水平七级 (意图层内部处理流程):
  1 级：意图解析
  2 级：任务规划
  3 级：上下文收集
  4 级：安全验证
  5 级：能力绑定
  6 级：执行
  7 级：改进
```

### 关键要点

1. **垂直用"层"**: 表示调用关系的层级 (Layer)
2. **水平用"级"**: 表示处理流程的步骤 (Level)
3. **七级在意图层内**: 七级是意图层的内部处理流程
4. **术语清晰**: 不再混淆"三层"vs"七层"

### 术语使用示例

✅ 正确说法:
- "垂直三层架构"
- "水平七级处理流程"
- "意图层包含七级处理"
- "从应用层调用到意图层"

❌ 错误说法:
- "三层七层" (混淆)
- "七层架构" (不清楚是垂直还是水平)

---

**文档版本**: 5.0 (最终术语规范版)  
**创建日期**: 2026-03-13  
**最后更新**: 2026-03-13  
**负责人**: IntentOS Team
