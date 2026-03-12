# 代码生成：从结构化意图到 Prompt

> 代码生成是意图编译器的核心环节，将结构化意图转换为 LLM 可理解的 Prompt。

---

## 1. 概述

### 1.1 职责

**代码生成器 (Code Generator)** 的职责是将结构化意图转换为 LLM 可执行的 Prompt：

```
StructuredIntent → CodeGenerator → Prompt
```

### 1.2 输出组成

生成的 Prompt 包含两部分：

| 部分 | 说明 | 示例 |
|------|------|------|
| **System Prompt** | 系统指令，定义角色和任务 | "你是销售分析助手..." |
| **User Prompt** | 用户请求，包含具体参数 | "请分析华东区 Q3 销售数据" |

---

## 2. 模板系统

### 2.1 意图类型模板

不同意图类型使用不同模板：

```python
TEMPLATES = {
    "atomic": """
# 任务执行指令

你是一个 AI 原生助手，需要执行用户的意图。

## 意图信息
- **名称**: {intent_name}
- **类型**: 原子任务
- **目标**: {goal}
- **描述**: {description}

## 可用能力
{capabilities}

## 上下文信息
- **用户**: {user_id}
- **角色**: {user_role}
- **会话**: {session_id}

## 参数
{params}

## 约束条件
{constraints}

请根据以上信息，执行意图并返回结果。
结果格式：JSON 对象，包含 success, result, message 字段。
""",

    "composite": """
# 复合任务执行计划

你是一个 AI 原生助手，需要执行一个多步骤的复合任务。

## 意图信息
- **名称**: {intent_name}
- **类型**: 复合任务
- **目标**: {goal}

## 执行步骤
{steps}

## 上下文信息
- **用户**: {user_id}
- **角色**: {user_role}

## 参数
{params}

请按顺序执行上述步骤，每一步的输出将作为下一步的输入。
最终返回整合后的结果。
""",

    "scenario": """
# 场景化任务

你是一个 AI 原生助手，需要完成一个业务场景任务。

## 场景信息
- **名称**: {intent_name}
- **场景**: {description}
- **目标**: {goal}

## 业务上下文
- **用户角色**: {user_role}
- **相关权限**: {permissions}

## 场景参数
{params}

## 期望输出
根据场景需求，生成结构化的输出结果。
""",

    "meta": """
# 系统管理指令

你是一个 AI 原生系统的元管理器，需要管理系统自身的结构和行为。

## 元意图信息
- **动作**: {action}
- **目标**: {goal}

## 当前系统状态
{system_state}

## 操作参数
{params}

请执行系统管理操作，并返回操作结果。
""",
}
```

### 2.2 模板选择逻辑

```python
def select_template(intent_type: str) -> str:
    """根据意图类型选择模板"""
    template_map = {
        "atomic": "atomic",
        "composite": "composite",
        "scenario": "scenario",
        "meta": "meta",
    }
    template_name = template_map.get(intent_type, "atomic")
    return TEMPLATES[template_name]
```

---

## 3. 填充逻辑

### 3.1 变量替换

```python
class CodeGenerator:
    def generate(self, intent: StructuredIntent) -> GeneratedPrompt:
        # 选择模板
        template = self._select_template(intent.intent_type)
        
        # 收集填充变量
        variables = {
            "intent_name": intent.name,
            "goal": intent.goal,
            "description": intent.description,
            "capabilities": self._format_capabilities(),
            "user_id": intent.context.user_id,
            "user_role": intent.context.user_role,
            "session_id": intent.context.session_id,
            "params": self._format_params(intent.params),
            "constraints": self._format_constraints(intent.constraints),
            "steps": self._format_steps(intent.steps),
            "system_state": self._format_system_state(),
        }
        
        # 填充模板
        system_prompt = template.format(**variables)
        user_prompt = self._generate_user_prompt(intent)
        
        return GeneratedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            intent=intent,
        )
```

### 3.2 能力格式化

```python
def _format_capabilities(self) -> str:
    """格式化能力列表"""
    if not self.registry:
        return "（无可用能力）"
    
    capabilities = self.registry.list_capabilities()
    if not capabilities:
        return "（无可用能力）"
    
    lines = []
    for cap in capabilities:
        lines.append(f"- **{cap.name}**: {cap.description}")
        lines.append(f"  输入：{cap.input_schema}")
        lines.append(f"  输出：{cap.output_schema}")
    
    return "\n".join(lines)
```

### 3.3 步骤格式化

```python
def _format_steps(self, steps: list[IntentStep]) -> str:
    """格式化执行步骤"""
    if not steps:
        return "（无预定义步骤）"
    
    lines = []
    for i, step in enumerate(steps, 1):
        lines.append(f"**步骤 {i}**: 调用 `{step.capability_name}`")
        if step.params:
            lines.append(f"  参数：{step.params}")
        if step.condition:
            lines.append(f"  条件：{step.condition}")
        if step.output_var:
            lines.append(f"  输出绑定：${{{step.output_var}}}")
    
    return "\n".join(lines)
```

---

## 4. 用户 Prompt 生成

### 4.1 基本逻辑

```python
def _generate_user_prompt(self, intent: StructuredIntent) -> str:
    """生成用户 Prompt"""
    base_prompt = f"请执行：{intent.goal}"
    
    if intent.params:
        base_prompt += f"\n\n参数：{intent.params}"
    
    if intent.context.history:
        base_prompt += f"\n\n历史对话：{intent.context.history[-3:]}"
    
    return base_prompt
```

### 4.2 示例

```python
# 输入
intent = StructuredIntent(
    goal="分析华东区 Q3 销售数据",
    params={"region": "华东", "period": "Q3"},
    context=Context(history=["用户：你好", "助手：有什么可以帮助你的？"])
)

# 输出
user_prompt = """
请执行：分析华东区 Q3 销售数据

参数：{'region': '华东', 'period': 'Q3'}

历史对话：['用户：你好', '助手：有什么可以帮助你的？']
"""
```

---

## 5. JSON 格式生成

### 5.1 适用场景

对于支持 Function Calling 的 LLM，可以生成 JSON 格式的 Prompt：

```python
def compile_to_json(self, intent: StructuredIntent) -> str:
    """将意图编译为 JSON 格式"""
    import json
    
    return json.dumps({
        "intent": {
            "name": intent.name,
            "type": intent.intent_type,
            "goal": intent.goal,
            "params": intent.params,
            "constraints": intent.constraints,
        },
        "context": {
            "user_id": intent.context.user_id,
            "user_role": intent.context.user_role,
            "session_id": intent.context.session_id,
        },
        "steps": [
            {
                "capability": step.capability_name,
                "params": step.params,
                "condition": step.condition,
                "output_var": step.output_var,
            }
            for step in intent.steps
        ],
    }, ensure_ascii=False, indent=2)
```

### 5.2 输出示例

```json
{
  "intent": {
    "name": "sales_analysis",
    "type": "composite",
    "goal": "分析华东区 Q3 销售数据",
    "params": {
      "region": "华东",
      "period": "Q3"
    }
  },
  "context": {
    "user_id": "manager_001",
    "user_role": "manager",
    "session_id": "sess_123"
  },
  "steps": [
    {
      "capability": "query_sales",
      "params": {"region": "华东", "period": "Q3"}
    },
    {
      "capability": "analyze_trends",
      "params": {"data": "${sales_data}"}
    }
  ]
}
```

---

## 6. 优化技巧

### 6.1 上下文压缩

当历史对话过长时，进行压缩：

```python
def _compress_history(self, history: list[str], max_tokens: int = 1000) -> str:
    """压缩历史对话"""
    if len(history) <= max_tokens:
        return "\n".join(history)
    
    # 保留最近的对话，压缩早期对话
    recent = history[-5:]  # 保留最近 5 轮
    early_summary = f"[早期对话共{len(history)-5}轮，已省略]"
    
    return early_summary + "\n" + "\n".join(recent)
```

### 6.2 参数验证

```python
def _validate_params(self, params: dict, schema: dict) -> list[str]:
    """验证参数是否符合 Schema"""
    errors = []
    
    for required_field in schema.get("required", []):
        if required_field not in params:
            errors.append(f"缺少必填参数：{required_field}")
    
    for field, value in params.items():
        expected_type = schema.get("properties", {}).get(field, {}).get("type")
        if expected_type and not isinstance(value, eval(expected_type)):
            errors.append(f"参数类型错误：{field}")
    
    return errors
```

### 6.3 缓存优化

```python
class CodeGenerator:
    def __init__(self):
        self._cache = {}  # 缓存已生成的 Prompt
    
    def generate(self, intent: StructuredIntent) -> GeneratedPrompt:
        # 生成缓存键
        cache_key = self._generate_cache_key(intent)
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 生成 Prompt
        prompt = self._generate_impl(intent)
        
        # 缓存
        self._cache[cache_key] = prompt
        
        return prompt
```

---

## 7. 完整示例

### 7.1 代码示例

```python
from intentos import IntentCompiler, StructuredIntent, Context

# 创建编译器
compiler = IntentCompiler()

# 创建结构化意图
intent = StructuredIntent(
    name="sales_analysis",
    intent_type="composite",
    goal="分析华东区 Q3 销售数据，对比去年同期",
    description="销售数据分析任务",
    params={
        "region": "华东",
        "period": "Q3",
        "compare_with": "last_year"
    },
    context=Context(user_id="manager_001", user_role="manager"),
    steps=[
        IntentStep(capability_name="query_sales", params={"region": "华东"}),
        IntentStep(capability_name="analyze_trends", params={"data": "${sales_data}"}),
        IntentStep(capability_name="render_dashboard", params={"style": "executive"}),
    ]
)

# 生成 Prompt
prompt = compiler.generate(intent)

# 查看结果
print("=== System Prompt ===")
print(prompt.system_prompt)
print("\n=== User Prompt ===")
print(prompt.user_prompt)
```

### 7.2 输出示例

```
=== System Prompt ===
# 复合任务执行计划

你是一个 AI 原生助手，需要执行一个多步骤的复合任务。

## 意图信息
- **名称**: sales_analysis
- **类型**: 复合任务
- **目标**: 分析华东区 Q3 销售数据，对比去年同期

## 执行步骤
**步骤 1**: 调用 `query_sales`
  参数：{'region': '华东'}
**步骤 2**: 调用 `analyze_trends`
  参数：{'data': '${sales_data}'}
**步骤 3**: 调用 `render_dashboard`
  参数：{'style': 'executive'}

## 上下文信息
- **用户**: manager_001
- **角色**: manager

## 参数
- region: 华东
- period: Q3
- compare_with: last_year

请按顺序执行上述步骤，每一步的输出将作为下一步的输入。
最终返回整合后的结果。

=== User Prompt ===
请执行：分析华东区 Q3 销售数据，对比去年同期

参数：{'region': '华东', 'period': 'Q3', 'compare_with': 'last_year'}
```

---

## 8. 总结

代码生成器的核心价值：

1. **模板化**: 不同意图类型使用不同模板
2. **结构化**: 将意图信息组织为清晰的格式
3. **可优化**: 支持缓存、压缩、验证等优化
4. **多格式**: 支持文本和 JSON 格式

---

**下一篇**: [链接器](04-linker.md)

**上一篇**: [PEF 规范](02-pef-specification.md)
