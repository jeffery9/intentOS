# 上下文层（Context Layer）

> L3 上下文层负责收集和管理多模态上下文信息，包括用户上下文、业务上下文、技术上下文和事件图。

---

## 1. 概述

### 1.1 职责

**上下文层 (Context Layer)** 是 IntentOS 七级架构中的第三层，负责：

| 职责 | 说明 |
|------|------|
| **上下文收集** | 从多种来源收集上下文信息 |
| **上下文传播** | 将上下文传递给下游层 |
| **多模态融合** | 融合指标、日志、文档等多模态信息 |
| **上下文缓存** | 缓存常用上下文以提高性能 |

### 1.2 上下文类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **用户上下文** | 用户身份、角色、权限 | user_id, role, permissions |
| **会话上下文** | 当前会话状态 | session_id, history |
| **业务上下文** | 业务领域信息 | department, fiscal_year |
| **技术上下文** | 技术环境信息 | cluster, namespace, service |
| **事件图** | 多模态事件 | metrics, logs, traces, documents |

---

## 2. 上下文数据结构

### 2.1 ContextBinding

```python
@dataclass
class ContextBinding:
    """上下文绑定段"""
    # 用户上下文
    user_id: str = ""
    user_role: str = ""
    session_id: str = ""

    # 业务上下文
    business_context: dict[str, Any] = field(default_factory=dict)

    # 技术上下文
    technical_context: dict[str, Any] = field(default_factory=dict)

    # 历史上下文 (多模态事件图)
    event_graph: list[dict[str, Any]] = field(default_factory=list)
```

### 2.2 事件图结构

```yaml
event_graph:
  - type: "metric"
    source: "prometheus"
    query: "rate(http_requests_total[5m])"
    value: 100
  
  - type: "log"
    source: "elasticsearch"
    query: "level:ERROR service:order"
    count: 5
  
  - type: "trace"
    source: "jaeger"
    trace_id: "abc123"
    duration_ms: 250
  
  - type: "document"
    source: "confluence"
    page_id: "12345"
    title: "订单系统架构"
```

---

## 3. ContextLayer 实现

### 3.1 类定义

```python
class ContextLayer:
    """
    L3: 上下文层
    多模态事件图（指标/日志/代码/文档）
    """
    
    async def process(
        self,
        prompt: PromptExecutable,
    ) -> LayerResult:
        """处理上下文层"""
        start = datetime.now()
        
        try:
            # 收集多模态上下文
            context_graph = self._collect_context(prompt.context)
            
            duration = int((datetime.now() - start).total_seconds() * 1000)
            
            return LayerResult(
                layer_name="ContextLayer",
                success=True,
                output={"context_graph": context_graph},
                metrics={"duration_ms": duration},
            )
        except Exception as e:
            return LayerResult(
                layer_name="ContextLayer",
                success=False,
                error=str(e),
            )
```

### 3.2 上下文收集

```python
def _collect_context(self, context: ContextBinding) -> dict:
    """收集上下文"""
    return {
        "user_context": {
            "user_id": context.user_id,
            "user_role": context.user_role,
            "session_id": context.session_id,
        },
        "business_context": context.business_context,
        "technical_context": context.technical_context,
        "event_graph": context.event_graph,
    }
```

---

## 4. 上下文注入

### 4.1 注入到 Prompt

上下文层收集的信息会注入到 Prompt 中：

```python
async def _add_context_memories(
    self,
    prompt: GeneratedPrompt,
    context: Context,
) -> GeneratedPrompt:
    """添加上下文记忆到 System Prompt"""
    context_section = []
    
    # 获取用户偏好
    user_pref = await self.memory_manager.get_short_term(
        f"user:{context.user_id}:preference"
    )
    if user_pref:
        context_section.append(f"## 用户偏好\n{user_pref.value}")
    
    # 获取对话历史
    history = await self.memory_manager.get_short_term(
        f"session:{context.session_id}:history"
    )
    if history:
        context_section.append(f"## 对话历史\n{history.value}")
    
    # 获取相关知识
    knowledge = await self.memory_manager.get_by_tag("knowledge")
    if knowledge:
        context_section.append("## 相关知识")
        for k in knowledge[:3]:
            context_section.append(f"- {k.value}")
    
    if context_section:
        context_text = "\n\n".join(context_section)
        prompt.system_prompt += f"\n\n## 上下文\n{context_text}"
    
    return prompt
```

### 4.2 注入示例

**注入前的 System Prompt**:

```
# AI 助手指令

## 意图信息
- 动作：analyze
- 目标：销售数据分析
```

**注入后的 System Prompt**:

```
# AI 助手指令

## 意图信息
- 动作：analyze
- 目标：销售数据分析

## 上下文
## 用户偏好
{'region': '华东', 'format': 'dashboard'}

## 对话历史
用户：分析销售数据
助手：好的，正在分析...

## 相关知识
- {'Q3': '第三季度 (7-9 月)'}
- {'GMV': '商品交易总额'}
```

---

## 5. 上下文传播

### 5.1 层间传播

```
┌─────────────────────────────────────────────────────────────┐
│  L1: 意图层                                                  │
│  ↓ 传递意图                                                  │
├─────────────────────────────────────────────────────────────┤
│  L2: 规划层                                                  │
│  ↓ 传递 DAG                                                  │
├─────────────────────────────────────────────────────────────┤
│  L3: 上下文层 ← 收集上下文                                   │
│  ↓ 传递 enriched DAG + context                               │
├─────────────────────────────────────────────────────────────┤
│  L4: 安全环                                                  │
│  ↓ 传递 cleared DAG + context                                │
├─────────────────────────────────────────────────────────────┤
│  L5: 工具层                                                  │
│  ↓ 传递 bound DAG + context                                  │
├─────────────────────────────────────────────────────────────┤
│  L6: 执行层                                                  │
│  ↓ 传递结果                                                  │
├─────────────────────────────────────────────────────────────┤
│  L7: 改进层                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 跨层共享

```python
@dataclass
class LayerResult:
    """层执行结果"""
    layer_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)  # 共享上下文
```

---

## 6. 使用示例

### 6.1 创建上下文

```python
from intentos import Context

context = Context(
    user_id="manager_001",
    user_role="sales_manager",
    permissions=["read_sales", "create_report"],
)

context.set_variable("region", "华东")
context.set_variable("period", "Q3")
```

### 6.2 在 PEF 中声明上下文

```yaml
context:
  user_id: "manager_001"
  user_role: "manager"
  session_id: "sess_123"
  
  # 业务上下文
  business_context:
    department: "sales"
    fiscal_year: 2024
  
  # 技术上下文
  technical_context:
    cluster: "prod-us-east-1"
    namespace: "default"
  
  # 多模态事件图
  event_graph:
    - type: "metric"
      source: "prometheus"
      query: "rate(http_requests_total[5m])"
    - type: "log"
      source: "elasticsearch"
      query: "level:ERROR service:order"
```

### 6.3 在能力执行中使用上下文

```python
from intentos import Capability, Context

async def query_sales(context: Context, region: str) -> dict:
    """查询销售数据"""
    # 检查权限
    if not context.has_permission("read_sales"):
        raise PermissionError("无权访问销售数据")
    
    # 获取上下文变量
    period = context.get_variable("period", "Q3")
    
    # 执行查询
    return {
        "region": region,
        "period": period,
        "revenue": 1000000,
    }
```

---

## 7. 最佳实践

### 7.1 上下文设计原则

| 原则 | 说明 |
|------|------|
| **最小必要** | 只收集必要的上下文 |
| **及时更新** | 定期更新易变的上下文 |
| **安全存储** | 敏感上下文加密存储 |
| **按需加载** | 延迟加载大型上下文 |

### 7.2 上下文缓存

```python
class ContextCache:
    """上下文缓存"""
    
    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}
        self._ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if time.time() - self._timestamps[key] < self._ttl:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._timestamps[key] = time.time()
```

---

## 8. 总结

上下文层的核心价值：

1. **多模态融合**: 融合指标、日志、文档等多种上下文
2. **上下文传播**: 在七级架构中传递上下文
3. **记忆注入**: 将上下文注入到 Prompt 中
4. **性能优化**: 通过缓存提高上下文访问速度

---

**下一篇**: [Self-Bootstrap](03-self-bootstrap.md)

**上一篇**: [分布式架构](04-distributed-architecture.md)
