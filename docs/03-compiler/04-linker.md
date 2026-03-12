# 链接器：Prompt 与能力、记忆绑定

> 链接器将生成的 Prompt 与能力 (Capability) 和记忆 (Memory) 绑定，形成可执行的完整单元。

---

## 1. 概述

### 1.1 职责

**链接器 (Linker)** 的职责是将代码生成器生成的 Prompt 与**能力**和**记忆**绑定，形成可执行的完整单元：

```
Prompt + Capabilities + Memories → Linker → Executable
```

### 1.2 为什么需要记忆链接

意图执行需要上下文信息，这些信息存储在记忆系统中：

| 记忆类型 | 链接内容 | 示例 |
|---------|---------|------|
| **工作记忆** | 当前任务的中间结果 | DAG 执行的变量绑定 |
| **短期记忆** | 用户会话、临时偏好 | "华东"指代范围、对话历史 |
| **长期记忆** | 知识库、历史数据 | 销售最佳实践、客户画像 |

### 1.3 链接流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 收集 Prompt 中引用的能力和记忆                           │
│     • 解析 Prompt 中的能力名称                               │
│     • 解析记忆引用（如 ${memory.user_preference}）          │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  2. 查找能力定义和记忆内容                                   │
│     • 在能力注册表中查找能力                                 │
│     • 在记忆管理器中检索记忆                                 │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  3. 绑定能力和记忆                                           │
│     • 绑定 API 端点、认证信息                                │
│     • 注入记忆内容到 Prompt                                  │
└───────────────┬─────────────────────────────────────────────┘
                ↓
┌───────────────▼─────────────────────────────────────────────┐
│  4. 生成可执行单元                                           │
│     • 包含 Prompt、绑定的能力和记忆                          │
│     • 标记为 executable: true                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 能力匹配

### 2.1 显式匹配

从 Prompt 中直接提取能力名称：

```python
class Linker:
    def _extract_capabilities(self, prompt: GeneratedPrompt) -> list[str]:
        """从 Prompt 中提取能力名称"""
        caps = []
        
        # 从意图参数中提取
        if "capabilities" in prompt.intent.parameters:
            caps.extend(prompt.intent.parameters["capabilities"])
        
        # 从工作流步骤中提取
        for step in prompt.intent.steps:
            if step.capability_name:
                caps.append(step.capability_name)
        
        return list(set(caps))  # 去重
```

### 2.2 隐式推断

根据意图动作推断需要的能力：

```python
ACTION_TO_CAPABILITIES = {
    "analyze": ["data_query", "statistics", "trend_analysis"],
    "query": ["data_query"],
    "generate": ["template_render", "file_export"],
    "create": ["resource_create", "permission_check"],
    "compare": ["data_query", "comparison"],
}

def _infer_capabilities(self, action: str) -> list[str]:
    """根据动作推断需要的能力"""
    return ACTION_TO_CAPABILITIES.get(action, [])
```

---

## 3. 记忆链接

### 3.1 记忆引用语法

在 PEF 中使用记忆引用：

```yaml
# PEF 中的记忆引用
intent:
  goal: "分析${memory.user_preference.region}的销售数据"
  parameters:
    user_id: "${memory.session.user_id}"
    history: "${memory.conversation.last_3_turns}"

# 记忆引用格式
${memory.<memory_type>.<key>}
${memory.short_term.user:123:preference}
${memory.long_term.knowledge:sales_best_practices}
```

### 3.2 记忆检索

```python
class Linker:
    def __init__(self, registry: IntentRegistry, memory_manager: DistributedMemoryManager):
        self.registry = registry
        self.memory_manager = memory_manager
    
    async def _resolve_memory_references(self, prompt: GeneratedPrompt) -> dict[str, Any]:
        """解析 Prompt 中的记忆引用"""
        memories = {}
        
        # 从 Prompt 中提取记忆引用
        references = self._extract_memory_references(prompt)
        
        for ref in references:
            # 解析引用格式 ${memory.type.key}
            memory_type, key = self._parse_memory_reference(ref)
            
            # 检索记忆
            if memory_type == "short_term":
                entry = await self.memory_manager.get_short_term(key)
            elif memory_type == "long_term":
                entry = await self.memory_manager.get_long_term(key)
            else:
                entry = await self.memory_manager.get(key)
            
            if entry:
                memories[ref] = entry.value
            else:
                memories[ref] = None  # 记忆不存在
        
        return memories
    
    def _extract_memory_references(self, prompt: GeneratedPrompt) -> list[str]:
        """提取记忆引用"""
        import re
        pattern = r'\$\{memory\.([^}]+)\}'
        
        references = []
        # 从 System Prompt 中提取
        references.extend(re.findall(pattern, prompt.system_prompt))
        # 从 User Prompt 中提取
        references.extend(re.findall(pattern, prompt.user_prompt))
        # 从参数中提取
        references.extend(re.findall(pattern, str(prompt.intent.params)))
        
        return list(set(references))
```

### 3.3 记忆注入

将检索到的记忆注入到 Prompt 中：

```python
async def inject_memories(self, prompt: GeneratedPrompt, memories: dict[str, Any]) -> GeneratedPrompt:
    """将记忆注入到 Prompt"""
    import re
    
    # 替换 System Prompt 中的记忆引用
    system_prompt = prompt.system_prompt
    for ref, value in memories.items():
        placeholder = f"${{memory.{ref}}}"
        system_prompt = re.sub(re.escape(placeholder), str(value), system_prompt)
    
    # 替换 User Prompt 中的记忆引用
    user_prompt = prompt.user_prompt
    for ref, value in memories.items():
        placeholder = f"${{memory.{ref}}}"
        user_prompt = re.sub(re.escape(placeholder), str(value), user_prompt)
    
    return GeneratedPrompt(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        intent=prompt.intent,
        metadata=prompt.metadata,
    )
```

### 3.4 上下文记忆注入

在 System Prompt 中添加上下文记忆：

```python
async def add_context_memories(self, prompt: GeneratedPrompt, context: Context) -> GeneratedPrompt:
    """添加上下文记忆到 System Prompt"""
    # 获取用户偏好
    user_pref = await self.memory_manager.get_short_term(f"user:{context.user_id}:preference")
    
    # 获取对话历史
    conversation_history = await self.memory_manager.get_short_term(f"session:{context.session_id}:history")
    
    # 获取相关知识
    knowledge = await self.memory_manager.get_by_tag("knowledge")
    
    # 构建上下文部分
    context_section = []
    
    if user_pref:
        context_section.append(f"## 用户偏好\n{user_pref.value}")
    
    if conversation_history:
        context_section.append(f"## 对话历史\n{conversation_history.value}")
    
    if knowledge:
        relevant_knowledge = [k for k in knowledge if self._is_relevant(k, prompt.intent)]
        if relevant_knowledge:
            context_section.append("## 相关知识")
            for k in relevant_knowledge[:3]:  # 最多 3 条
                context_section.append(f"- {k.value}")
    
    # 插入到 System Prompt
    if context_section:
        context_text = "\n\n".join(context_section)
        prompt.system_prompt += f"\n\n## 上下文\n{context_text}"
    
    return prompt
```

---

## 4. 能力绑定

### 4.1 绑定结构

```python
@dataclass
class BoundCapability:
    name: str
    description: str
    endpoint: str
    protocol: str  # http, grpc, websocket, llm
    authentication: dict
    params_schema: dict
    output_schema: dict
    fallback: list[str]
    timeout_ms: int
    retry_count: int
```

### 4.2 绑定逻辑

```python
class Linker:
    def __init__(self, registry: IntentRegistry):
        self.registry = registry
    
    def bind_capabilities(
        self,
        prompt: GeneratedPrompt,
        capability_names: list[str],
    ) -> list[BoundCapability]:
        """绑定能力"""
        bound = []
        
        for name in capability_names:
            cap = self.registry.get_capability(name)
            if not cap:
                # 尝试查找备用能力
                cap = self._find_fallback(name)
                if not cap:
                    raise CapabilityNotFoundError(name)
            
            bound_cap = BoundCapability(
                name=cap.name,
                description=cap.description,
                endpoint=cap.endpoint,
                protocol=cap.protocol,
                authentication=cap.authentication,
                params_schema=cap.input_schema,
                output_schema=cap.output_schema,
                fallback=cap.fallback,
                timeout_ms=cap.timeout_ms,
                retry_count=cap.retry_count,
            )
            bound.append(bound_cap)
        
        return bound
```

---

## 5. 认证绑定

```python
def _bind_authentication(self, cap: BoundCapability, context: Context) -> None:
    """绑定认证信息"""
    auth_type = cap.authentication.get("type")
    
    if auth_type == "bearer":
        token_ref = cap.authentication.get("token_ref")
        cap.authentication["token"] = self._get_secret(token_ref)
    
    elif auth_type == "api_key":
        key_ref = cap.authentication.get("key_ref")
        cap.authentication["api_key"] = self._get_secret(key_ref)
    
    elif auth_type == "oauth2":
        cap.authentication["access_token"] = self._get_oauth_token(context.user_id)
```

---

## 6. 可执行单元

### 6.1 结构定义

```python
@dataclass
class Executable:
    """可执行单元"""
    id: str
    prompt: GeneratedPrompt
    capabilities: list[BoundCapability]
    memories: dict[str, Any]  # 注入的记忆
    context: dict
    params: dict
    executable: bool = True
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prompt": self.prompt.to_dict(),
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "memories": self.memories,
            "context": self.context,
            "params": self.params,
            "executable": self.executable,
            "created_at": self.created_at,
        }
```

### 6.2 链接器输出

```python
class Linker:
    async def link(
        self,
        prompt: GeneratedPrompt,
        context: Context,
    ) -> Executable:
        """链接 Prompt、能力和记忆"""
        # 提取并绑定能力
        cap_names = self._extract_capabilities(prompt)
        inferred_caps = self._infer_capabilities(prompt.intent.action)
        cap_names.extend(inferred_caps)
        
        bound_caps = self.bind_capabilities(prompt, cap_names)
        
        # 解析并注入记忆
        memories = await self._resolve_memory_references(prompt)
        prompt = await self.inject_memories(prompt, memories)
        prompt = await self.add_context_memories(prompt, context)
        
        # 绑定参数
        bound_params = self._bind_params(
            prompt.intent.params,
            context,
            memories,
        )
        
        # 创建可执行单元
        return Executable(
            id=str(uuid.uuid4()),
            prompt=prompt,
            capabilities=bound_caps,
            memories=memories,
            context=context,
            params=bound_params,
            executable=True,
        )
```

---

## 7. 完整示例

### 7.1 链接示例

```python
from intentos import IntentCompiler, Linker, IntentRegistry
from intentos import create_memory_manager, Context

# 创建组件
registry = IntentRegistry()
compiler = IntentCompiler(registry)
memory_manager = await create_memory_manager(
    short_term_max=10000,
    long_term_enabled=True,
    long_term_backend="redis",
)
linker = Linker(registry, memory_manager)

# 注册能力
registry.register_capability(Capability(
    name="query_sales",
    description="查询销售数据",
    endpoint="https://api.sales.com/query",
))

# 设置记忆
await memory_manager.set_short_term(
    key="user:manager_001:preference",
    value={"region": "华东", "format": "dashboard"},
)

# 编译意图（包含记忆引用）
prompt = compiler.compile("""
分析${memory.user:manager_001:preference.region}的销售数据，
使用${memory.user:manager_001:preference.format}格式展示
""")

# 链接
context = Context(user_id="manager_001")
executable = await linker.link(prompt, context)

# 查看结果
print(f"可执行单元 ID: {executable.id}")
print(f"绑定的能力：{[cap.name for cap in executable.capabilities]}")
print(f"注入的记忆：{executable.memories}")
print(f"可执行：{executable.executable}")
```

### 7.2 执行示例

```python
# 执行可执行单元
from intentos import ExecutionEngine

engine = ExecutionEngine(registry)
result = await engine.execute(executable)

print(f"执行结果：{result}")
```

---

## 8. 总结

链接器的核心价值：

1. **能力绑定**: 将 Prompt 与能力关联
2. **记忆链接**: 检索并注入上下文记忆
3. **参数验证**: 确保参数正确性
4. **可执行单元**: 形成完整执行单元

---

**下一篇**: [记忆分层架构](../04-memory/01-memory-layers.md)

**上一篇**: [代码生成](03-code-generation.md)
