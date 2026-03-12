# Self-Bootstrap：系统自举机制

> 真正的 AI-Native 系统应能通过语言自我定义、自我演化、自我修复。

---

## 1. 什么是 Self-Bootstrap

**Self-Bootstrap (自举)** 是指系统能够通过自身的能力来定义、扩展、修正、优化自身的结构与行为规则。

### 1.1 类比

| 系统 | 自举方式 |
|------|---------|
| **Lisp 机器** | 用 Lisp 实现操作系统 |
| **Smalltalk** | 一切都是对象，包括系统自身 |
| **生物体** | DNA 复制和修复 |
| **IntentOS** | 用意图管理意图 |

### 1.2 核心思想

> **系统用自己能理解的语言来描述和管理自身。**

在 IntentOS 中：
- 系统用**意图**来管理**意图**
- 系统用**意图**来修改**系统自身**

---

## 2. 自举的层次

### 2.1 三层自举结构

```
┌─────────────────────────────────────────┐
│  L2: 元元意图 (Meta-Meta-Intent)        │
│  • 修改系统策略                          │
│  • 优化执行规则                          │
│  • 定义元意图语法                        │
└───────────────┬─────────────────────────┘
                ↓ 管理
┌───────────────▼─────────────────────────┐
│  L1: 元意图 (Meta-Intent)               │
│  • 创建意图模板                          │
│  • 注册能力                              │
│  • 修改解析器                            │
└───────────────┬─────────────────────────┘
                ↓ 管理
┌───────────────▼─────────────────────────┐
│  L0: 任务意图 (Task-Intent)             │
│  • 分析销售                              │
│  • 生成报告                              │
│  • 查询数据                              │
└─────────────────────────────────────────┘
```

### 2.2 各层职责

| 层级 | 职责 | 示例 |
|------|------|------|
| **L0** | 执行用户任务 | "分析销售数据" |
| **L1** | 管理 L0 意图 | "创建分析模板" |
| **L2** | 管理 L1 意图 | "修改模板创建策略" |

---

## 3. 自举的四个机制

### 3.1 意图可自省 (Introspection)

系统能回答关于自身的问题：

```python
# 用户问
"当前有哪些可用意图模板？"
"这个意图的执行步骤是什么？"
"谁定义了它？何时被调用过？"

# 系统回答
"""
当前可用模板:
1. sales_analysis - 销售分析
2. customer_report - 客户报告
3. pipeline_review - 漏斗复盘

sales_analysis 的定义:
- 创建者：admin
- 创建时间：2024-01-01
- 调用次数：156
- 成功率：98%
"""
```

### 3.2 意图可编程 (Intent Programming)

用户能用声明式语言定义、修改意图模板：

```python
# 用户说
"创建一个新意图，叫'客户健康度分析'"

# 系统生成 DSL 代码
define intent customer_health_score {
  requires capability: [
    get_activity,
    get_complaints,
    predict_churn
  ]
  output: interactive_dashboard
  policy: data_owner_only
  steps:
    - fetch_activity()
    - fetch_complaints()
    - calculate_score()
    - render_dashboard()
}

# 系统自动注册并验证
```

### 3.3 意图可学习 (Intent Learning)

系统通过观察用户行为，自动提炼新意图模板：

```python
# 观察
用户多次说：
- "对比华东和华南的 Q3 销售"
- "对比华北和华西的 Q4 销售"
- "对比华东和华北的上半年销售"

# 归纳
系统自动创建模板：
define intent compare_regions {
  params: [region_a, region_b, period]
  steps:
    - query_region(region_a, period)
    - query_region(region_b, period)
    - compare_results()
}

# 建议
系统问用户：
"我注意到你经常对比区域销售，
  要我创建一个快捷指令吗？"
```

### 3.4 意图可治理 (Intent Governance)

用策略性元意图管理安全与合规：

```python
# 用户说
"财务数据的意图需要 CFO 审批"

# 系统创建策略
apply policy "finance_data" to intent "*":
  condition: intent.domain == "finance"
  action: require_approval(role="CFO")
  audit: log_all_executions

# 策略本身也是意图
# 可被审计、修改、撤销
```

---

## 4. 自举的实现

### 4.1 意图仓库 (Intent Registry)

意图仓库是**自举的核心基础设施**：

```python
class IntentRegistry:
    def __init__(self):
        self._templates = {}      # 意图模板
        self._capabilities = {}   # 能力注册
        self._policies = {}       # 策略规则
        self._metrics = {}        # 执行度量
    
    # 自省
    def introspect(self) -> dict:
        return {
            "templates": self._templates,
            "capabilities": self._capabilities,
            "policies": self._policies,
        }
    
    # 注册
    def register_template(self, template: IntentTemplate):
        self._templates[template.name] = template
    
    # 查询
    def search(self, query: str) -> list:
        # 语义匹配
        ...
```

### 4.2 元意图执行器

元意图的执行需要特殊处理：

```python
async def execute_meta_intent(intent: MetaIntent):
    if intent.action == "register_template":
        # 注册新模板
        registry.register_template(intent.template)
        return {"status": "registered"}
    
    elif intent.action == "modify_policy":
        # 修改策略
        registry.update_policy(intent.policy)
        return {"status": "updated"}
    
    elif intent.action == "introspect":
        # 系统自省
        return registry.introspect()
```

### 4.3 自举循环

```
┌─────────────────────────────────────────┐
│  1. 用户表达元意图                       │
│  "创建一个新意图模板"                    │
└───────────────┬─────────────────────────┘
                ↓
┌───────────────▼─────────────────────────┐
│  2. 系统解析为结构化元意图               │
│  MetaIntent(action="create_template",...)│
└───────────────┬─────────────────────────┘
                ↓
┌───────────────▼─────────────────────────┐
│  3. 执行元意图，修改系统状态             │
│  registry.register_template(template)    │
└───────────────┬─────────────────────────┘
                ↓
┌───────────────▼─────────────────────────┐
│  4. 系统状态演化                         │
│  新模板可用，系统能力增强                │
└───────────────┬─────────────────────────┘
                ↓
┌───────────────▼─────────────────────────┐
│  5. 用户可使用新模板                     │
│  回到步骤 1，继续演化                    │
└─────────────────────────────────────────┘
```

---

## 5. 自举的收敛性

### 5.1 无限递归问题

一个关键问题是：**如果 L2 管理 L1，那谁来管理 L2？L3 吗？**

这会导致无限递归：
```
L0 ← L1 ← L2 ← L3 ← L4 ← ...
```

### 5.2 收敛策略

IntentOS 采用**策略空间收敛**：

```
L2 的策略变更 → 收敛到预定义的策略空间
                (有限的策略原语组合)
```

例如：
- L2 可以修改"模板创建策略"
- 但只能在预定义的策略原语范围内组合
- 不能创建"删除所有数据"这样的危险策略

### 5.3 安全边界

```python
# 预定义策略原语
POLICY_PRIMITIVES = {
    "require_approval": require_approval,
    "log_execution": log_execution,
    "restrict_role": restrict_role,
    "set_timeout": set_timeout,
    # ... 有限的安全原语
}

# L2 只能组合这些原语
# 不能创建新的危险原语
```

---

## 6. 自举的演进阶段

| 阶段 | 特征 | 技术支撑 |
|------|------|---------|
| **1. Prompt + 函数调用** | 用 LLM 调用预定义工具 | Function Calling |
| **2. 意图模板化** | 将高频任务固化为模板 | 意图 DSL |
| **3. 意图仓库** | 集中管理、版本化 | Registry + 策略引擎 |
| **4. 元意图层** | 系统支持"定义意图的意图" | 自省 API |
| **5. 自引导系统** | 系统可学习、演化、修复 | 程序合成 + 学习 |

当前（2025）我们处于**阶段 2→3**。

---

## 7. 总结

> **Self-Bootstrap 的本质是：系统用自身能理解的语言来描述和管理自身。**

IntentOS 通过以下机制实现自举：

1. **意图分层**: L0/L1/L2 三层结构
2. **意图自省**: 系统能回答关于自身的问题
3. **意图可编程**: 用 DSL 定义和修改意图
4. **意图可学习**: 从使用中自动归纳新模板
5. **策略收敛**: 限制在安全原语范围内组合

---

**下一篇**: [分布式架构](04-distributed-architecture.md)

**上一篇**: [意图即元语言](02-intent-as-metalanguage.md)
