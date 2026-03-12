# 意图即元语言

> 意图是 AI 原生系统的元语言，系统用意图来描述和管理自身。

---

## 1. 什么是元语言

**元语言 (Metalanguage)** 是用来描述另一种语言的语言。

例如：
- 语法书用自然语言描述自然语言的规则
- BNF 范式描述编程语言的语法
- UML 描述软件系统的结构

在 AI 原生系统中，**意图就是元语言**——系统用意图来描述和管理自身。

---

## 2. 意图的形式化定义

### 2.1 定义

**意图 (Intent)** 是用户目标的结构性表达，包含两个维度：

| 维度 | 说明 | 示例 |
|------|------|------|
| **功能意图** | "做什么" (What) | "分析销售数据" |
| **操作意图** | "做到什么程度" (How Well) | "P99 延迟≤100ms" |

### 2.2 结构化表示

```python
@dataclass
class Intent:
    # 功能意图
    action: str           # 动作：analyze, query, generate...
    target: str           # 目标：sales_data, report...
    parameters: dict      # 参数：region, period...
    
    # 操作意图
    slo: dict            # SLO: latency, availability...
    constraints: dict    # 约束：permission, compliance...
    
    # 上下文
    context: dict        # 上下文：user, session, history...
```

### 2.3 示例

```python
# 用户输入
"分析华东区 Q3 销售数据，对比去年同期，99% 请求延迟≤1 秒"

# 结构化意图
Intent(
    action="analyze",
    target="sales_data",
    parameters={
        "region": "华东",
        "period": "Q3",
        "compare_with": "last_year"
    },
    slo={
        "latency_p99_ms": 1000
    },
    constraints={
        "permission": "read_sales"
    },
    context={
        "user_id": "manager_001",
        "role": "sales_manager"
    }
)
```

---

## 3. 意图的层次

### 3.1 任务意图 (L0)

**任务意图**是用户要完成的具体任务：

```
L0: "分析销售数据"
L0: "生成月度报告"
L0: "对比华东和华南"
```

### 3.2 元意图 (L1)

**元意图**用于管理任务意图：

```
L1: "创建新的分析模板"
L1: "修改意图解析规则"
L1: "注册新的能力"
```

### 3.3 元元意图 (L2)

**元元意图**用于管理元意图：

```
L2: "修改模板创建策略"
L2: "优化能力路由规则"
```

### 3.4 层次关系

```
┌─────────────────────────────────────────┐
│  L2: 元元意图                            │
│  • 修改策略                              │
│  • 优化规则                              │
└───────────────┬─────────────────────────┘
                ↓ 管理
┌───────────────▼─────────────────────────┐
│  L1: 元意图                              │
│  • 创建模板                              │
│  • 注册能力                              │
│  • 修改解析器                            │
└───────────────┬─────────────────────────┘
                ↓ 管理
┌───────────────▼─────────────────────────┐
│  L0: 任务意图                            │
│  • 分析销售                              │
│  • 生成报告                              │
│  • 对比区域                              │
└─────────────────────────────────────────┘
```

---

## 4. Self-Bootstrap（自举）

### 4.1 定义

**Self-Bootstrap** 是指系统能够通过自身的能力来定义、扩展、修正、优化自身的结构与行为规则。

形式化定义：

> 系统 S 是自举的，当且仅当：
> $$\forall s \in States(S), \exists i \in Intents(S) : Apply(i, s) \rightarrow s'$$
> 
> 其中 $Apply$ 是意图执行函数，$s'$ 是演化后的系统状态。

### 4.2 自举的条件

支持 Self-Bootstrap 的系统必须满足三个条件：

| 条件 | 说明 | 示例 |
|------|------|------|
| **意图可自省** | 系统能回答关于自身意图的问题 | "当前有哪些可用模板？" |
| **意图可生成** | 系统能用自然语言指令生成新的 DSL 代码 | "创建一个新意图" |
| **意图语义可演化** | 系统能在运行时修改 DSL 的语义 | "扩展语法支持新关键字" |

### 4.3 自举示例

```python
# 用户说
"创建一个新意图，叫'客户健康度分析'，包含活跃度、投诉率、续约倾向"

# 系统自动生成 DSL 代码并注册
define intent customer_health_score {
  steps: [
    get_activity(),
    get_complaints(),
    predict_churn()
  ]
}

# 系统用意图管理自身
# → Self-Bootstrap 实现
```

---

## 5. 意图即程序

### 5.1 传统程序 vs 意图程序

| 维度 | 传统程序 | 意图程序 |
|------|---------|---------|
| **源代码** | 代码文件 | 自然语言 |
| **编译** | 编译器 | 意图编译器 |
| **执行** | CPU | LLM |
| **库函数** | API/库 | 能力 (Capability) |
| **内存** | RAM/磁盘 | 记忆系统 |

### 5.2 编译过程

```
自然语言意图
    ↓
[词法分析] Token 流
    ↓
[语法分析] AST
    ↓
[语义分析] 结构化意图
    ↓
[代码生成] Prompt
    ↓
[链接] Prompt + 能力绑定
    ↓
可执行 Prompt → LLM → 结果
```

### 5.3 示例

```python
# 自然语言意图
"分析华东区 Q3 销售数据"

# 编译后的 Prompt (简化)
system_prompt = """
# AI 助手指令

## 意图信息
- 动作：analyze
- 目标：sales_data
- 参数：region=华东，period=Q3

## 可用能力
- query_sales: 查询销售数据
- analyze_trends: 分析趋势
- render_dashboard: 渲染仪表盘
"""

user_prompt = "请分析华东区 Q3 销售数据"
```

---

## 6. 意图仓库 (Intent Registry)

### 6.1 职责

意图仓库是**意图的管理中枢**，存储：

1. **意图模板**: 常见意图的定义
2. **能力映射**: 意图到能力的映射规则
3. **策略约束**: 安全策略与合规约束
4. **执行度量**: 成功率、用户满意度等

### 6.2 示例

```yaml
# 意图模板
template: sales_analysis
params:
  - region: string
  - period: string
  - benchmark: optional(string)
steps:
  - query_sales_data(region={{region}}, period={{time_range}})
  - compare_with({{benchmark}})
  - generate_insight_report()
version: 1.2.0
tags: [sales, analysis]
```

### 6.3 意图复用

```python
# 复用方式 1: 模板实例化
template = registry.get_template("sales_analysis")
intent = template.instantiate(region="华东", period="Q3")

# 复用方式 2: 子图调用
main_intent = Intent(name="monthly_review")
main_intent.add_subgraph("sales_analysis")

# 复用方式 3: 继承覆盖
finance_template = standard_template.override(
    add_approval_step=True
)
```

---

## 7. 总结

> **意图是 AI 原生系统的元语言，系统用意图来描述和管理自身。**

意图即元语言的三个推论：

1. **意图可自省**: 系统能回答关于自身的问题
2. **意图可组合**: 复杂意图由原子意图组成
3. **意图可演化**: 系统从使用中生长出新的结构

---

**下一篇**: [Self-Bootstrap](03-self-bootstrap.md)

**上一篇**: [三层七层架构](01-three-layer-model.md)
