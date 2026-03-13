# IntentOS Self-Bootstrap 架构

> **核心洞察**: 只有 LLM 作为处理器，才能实现真正的 Self-Bootstrap

---

## 1. 为什么硬编码无法实现 Self-Bootstrap

### 原架构 (v2) 的问题

```python
# 硬编码的分词规则
KEYWORDS = {
    "分析": "analyze",
    "查询": "query",
    "生成": "generate",
}

# 硬编码的意图识别
if "华东" in text:
    params["region"] = "华东"
```

**问题**：
1. 规则是硬编码的 Python 代码
2. 要修改规则，需要修改源代码
3. 修改源代码需要重新部署
4. **系统无法自修改**

❌ 这不是 Self-Bootstrap

---

## 2. LLM 作为处理器的架构 (v3)

### 新架构

```python
# 解析规则在 Prompt 中 (可修改)
PARSE_PROMPT = """
你是一个意图解析专家。请将用户的自然语言输入解析为结构化的意图。

## 输出格式
{
    "action": "动作",
    "target": "目标",
    "parameters": {...}
}
"""

# LLM 根据 Prompt 解析
response = await llm.execute([
    {"role": "system", "content": PARSE_PROMPT},
    {"role": "user", "content": user_input},
])
```

**优势**：
1. 规则在 Prompt 中 (数据，非代码)
2. Prompt 可以动态修改
3. **系统可以自修改解析规则**

✅ 这是 Self-Bootstrap

---

## 3. Self-Bootstrap 的三层结构

```
┌─────────────────────────────────────────────────────────────┐
│  L0: 任务意图 (Task Intent)                                 │
│  "分析销售数据"                                             │
│  ↓                                                          │
│  执行分析任务                                               │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ 管理
┌─────────────────────────────────────────────────────────────┐
│  L1: 元意图 (Meta-Intent)                                   │
│  "修改解析规则"                                             │
│  ↓                                                          │
│  修改 PARSE_PROMPT                                          │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ 管理
┌─────────────────────────────────────────────────────────────┐
│  L2: 元元意图 (Meta-Meta-Intent)                            │
│  "修改元意图的处理规则"                                      │
│  ↓                                                          │
│  修改 META_PARSER_PROMPT                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 自修改示例

### 4.1 修改解析规则

```python
# 元意图：修改解析 Prompt
meta = MetaIntent(
    action=MetaAction.MODIFY,
    target_type=TargetType.CONFIG,
    target_id="PARSE_PROMPT",
    parameters={
        "new_value": """
你是一个更强大的意图解析专家。

新增能力:
1. 支持情感分析
2. 支持多轮对话
3. 支持模糊意图识别

## 输出格式
{
    "action": "动作",
    "target": "目标",
    "parameters": {...},
    "sentiment": "positive/neutral/negative",  // 新增
    "follow_up_questions": [...]  // 新增
}
""",
    },
)

# 执行元意图
result = await self_modification.execute_meta(meta)
```

### 4.2 注册新动作

```python
# 元意图：注册新的动作类型
meta = MetaIntent(
    action=MetaAction.CREATE,
    target_type=TargetType.CONFIG,
    parameters={
        "config_id": "ACTION_TYPES",
        "new_actions": ["forecast", "optimize", "simulate"],
    },
)

# 执行后，系统可以识别新的动作
# "预测下季度销售" → action: "forecast"
```

### 4.3 修改验证规则

```python
# 元意图：修改验证规则
meta = MetaIntent(
    action=MetaAction.MODIFY,
    target_type=TargetType.POLICY,
    target_id="VALIDATION_RULES",
    parameters={
        "new_rules": {
            "require_approval_for": ["delete_template", "modify_policy"],
            "max_timeout_seconds": 600,
            "require_confidence_threshold": 0.7,
        },
    },
)
```

---

## 5. 完整的 Self-Bootstrap 流程

```
1. 用户表达元意图
   "修改解析规则，支持情感分析"
   
   ↓
   
2. LLM 解析为 MetaIntent
   MetaIntent(
       action=MODIFY,
       target_type=CONFIG,
       target_id="PARSE_PROMPT",
       parameters={"new_value": "..."},
   )
   
   ↓
   
3. 系统自省 (验证权限)
   if context.has_permission("admin"):
       proceed()
   
   ↓
   
4. 系统自修改 (更新 Prompt)
   CONFIG_STORE["PARSE_PROMPT"] = new_prompt
   
   ↓
   
5. 记录审计日志
   await audit.log(
       action="modify_parse_prompt",
       user=context.user_id,
       details={"old": old_prompt, "new": new_prompt},
   )
   
   ↓
   
6. 创建回滚检查点
   checkpoint = await rollback.create_checkpoint()
   
   ↓
   
7. 系统已演化
   - 新的解析规则已生效
   - 可以处理情感分析
   - 可回滚到修改前状态
```

---

## 6. Self-Bootstrap 的关键要素

| 要素 | 说明 | 是否必需 |
|------|------|---------|
| **LLM 作为处理器** | 解析规则在 Prompt 中 | ✅ 必需 |
| **Prompt 可修改** | 规则是数据，非代码 | ✅ 必需 |
| **元意图 DSL** | 表达自修改意图 | ✅ 必需 |
| **系统自省** | 了解自身状态 | ✅ 必需 |
| **安全边界** | 权限/审计/回滚 | ✅ 必需 |
| **硬编码规则** | Python 代码中的规则 | ❌ 避免 |

---

## 7. 架构对比

| 维度 | 硬编码架构 | LLM 处理器架构 |
|------|-----------|---------------|
| **解析规则位置** | Python 代码 | Prompt (数据) |
| **修改方式** | 修改代码 + 重新部署 | 修改 Prompt |
| **Self-Bootstrap** | ❌ 不可能 | ✅ 可以实现 |
| **演化能力** | 无 | 有 |
| **系统灵活性** | 低 | 高 |

---

## 8. 实现检查清单

### Self-Bootstrap 就绪度

- [ ] 解析规则在 Prompt 中 (非硬编码)
- [ ] Prompt 存储在可修改的配置中
- [ ] 元意图可以修改 Prompt
- [ ] 系统自省 API 完整
- [ ] 权限分级实现
- [ ] 审计日志实现
- [ ] 回滚机制实现

### 当前状态 (v3.0)

- [x] 解析规则在 Prompt 中 (`compiler_v3.py`)
- [x] 元意图 DSL (`self_bootstrap/__init__.py`)
- [x] 元意图解析器 (`self_bootstrap/parser.py`)
- [x] 系统自省 API (`self_bootstrap/introspection.py`)
- [x] 系统自修改 (`self_bootstrap/modifier.py`)
- [ ] 权限分级 (进行中)
- [ ] 审计日志 (进行中)
- [ ] 回滚机制 (待实现)

---

## 9. 下一步

### 阶段 1: 完成安全边界 (Week 5)
- [ ] 权限分级实现
- [ ] 审计日志存储
- [ ] 回滚机制

### 阶段 2: 自修改演示 (Week 6)
- [ ] 演示修改解析规则
- [ ] 演示注册新动作
- [ ] 演示修改验证规则

### 阶段 3: 元元意图 (v0.7.0)
- [ ] 元元意图 DSL
- [ ] 自修改的自修改
- [ ] 完整的自指结构

---

## 10. 总结

> **只有 LLM 作为处理器，Prompt 作为可修改的规则，才能实现真正的 Self-Bootstrap。**

硬编码的规则是**死的**，系统无法修改自身。
Prompt 规则是**活的**，系统可以通过元意图修改自身。

这就是 **Meta** 的本质：**系统用语言描述和管理自身**。

---

**文档版本**: 1.0  
**创建日期**: 2026-03-13  
**最后更新**: 2026-03-13  
**负责人**: IntentOS Team
