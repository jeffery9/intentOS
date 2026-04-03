# 架构模式迁移方案 - Claude Code 7 个模式适配到 IntentOS

> **分布式 AI 原生 OS 视角**
> 
> 本文档记录从 Claude Code 源码分析中提炼的 7 个架构模式, 以及如何适配到 IntentOS 分布式 OS 架构中。

**文档版本**: 1.0  
**创建日期**: 2026-04-03  
**状态**: Draft - 待讨论

---

## 目录

- [模式适用性评估](#模式适用性评估)
- [P0 模式详细方案](#p0-模式详细方案)
- [P1 模式适配方案](#p1-模式适配方案)
- [P2/P3 模式简述](#p2p3-模式简述)
- [实施计划](#实施计划)

---

## 模式适用性评估

### 全景评估矩阵

| 模式 | 原始含义 | IntentOS 映射点 | 适用性 | 优先级 | 预期收益 |
|------|---------|----------------|--------|--------|---------|
| **1. 编译期 DCE** | JS bundler 裁剪代码 | ❌ Python 运行时, 不适用 | 🟡 低 | P3 | - |
| **2. 极简 Store** | React 状态管理 | 🔄 **语义内存 Store** (分布式状态) | 🟢 高 | P1 | 统一状态管理 |
| **3. 工具注册表** | 工具注册+三层过滤 | ✅ **能力注册中心** (系统调用表) | 🟢 极高 | P0 | 集中管理+安全默认值 |
| **4. Prompt 分段缓存** | System Prompt 缓存 | ✅ **PEF 编译缓存** | 🟢 极高 | P0 | Token 降本 30-50% |
| **5. 多层配置合并** | 用户/项目/企业配置 | 🔄 **意图配置层** | 🟡 中 | P2 | 企业级配置 |
| **6. Agent 隔离** | 多 Agent 状态隔离 | 🔄 **PEF 执行隔离** | 🟢 高 | P1 | 多进程安全 |
| **7. 安全防线** | 权限决策管线 | ✅ **Capability Gate** | 🟢 极高 | P0 | OS 安全基石 |

### 核心区别: IntentOS vs Claude Code

| 维度 | Claude Code (AI Agent 框架) | IntentOS (分布式 OS) |
|------|---------------------------|---------------------|
| **定位** | 单节点 AI 编码助手 | 分布式 AI 原生操作系统 |
| **核心抽象** | Tool Calling + LLM Loop | 语义 VM + PEF (Prompt Executable File) |
| **状态管理** | React UI 状态 | 分布式语义内存 |
| **权限模型** | 工具级权限 | OS 级 Capability Gate |
| **执行模型** | 单进程 Agent | 跨节点 Map-Reduce |
| **缓存目标** | Prompt 缓存 | PEF 编译缓存 |

---

## P0 模式详细方案

### 模式 4: PEF 编译缓存优化

#### 问题分析

**IntentOS 现状**:
- 已有基础缓存 (`_prompt_cache` in `IntentCompiler`)
- 但只是简单的 key-value 缓存, 没有分层
- 每次编译都重新计算所有 section

**Claude Code 的三层结构**:
```
1. Static (Global Cache)    - 跨用户/会话不变
2. Memoized (Session Cache) - 会话内只计算一次
3. Volatile (Per-turn)      - 每轮重新计算
```

#### 适配方案

**PEF 三段式结构**:

```python
@dataclass
class CompiledPEF:
    """编译后的 PEF (Prompt Executable File)"""
    
    # ① 静态段 - global cache, 跨用户/会话不变
    static_section: str  # 能力描述、系统规则、行为准则
    
    # ② 动态段 - session cache, 会话内只计算一次
    dynamic_section: str  # 用户上下文、租户配置、环境信息
    
    # ③ 易变段 - per-turn, 每轮重新计算
    volatile_section: str  # 当前任务参数、用户输入
    
    # 元数据
    metadata: dict[str, Any]
    
    @property
    def full_prompt(self) -> str:
        """组合完整 Prompt (用于执行)"""
        return f"{self.static_section}\n{self.dynamic_section}\n{self.volatile_section}"
    
    @property
    def cache_key(self) -> str:
        """缓存键 (只包含静态段和动态段)"""
        return blake2b(f"{self.static_section}{self.dynamic_section}".encode()).hexdigest()
```

**编译流程改造**:

```python
class IntentCompiler:
    def compile(self, intent: str, context: AgentContext) -> CompiledPEF:
        # ① 静态段 - global cache
        static_section = self._get_or_compute_static(context)
        
        # ② 动态段 - session cache (session 内只计算一次)
        dynamic_section = self._get_or_compute_dynamic(context)
        
        # ③ 易变段 - 每轮重新计算
        volatile_section = self._compute_volatile(intent, context)
        
        return CompiledPEF(
            static_section=static_section,
            dynamic_section=dynamic_section,
            volatile_section=volatile_section,
            metadata={"intent": intent, "context": context},
        )
    
    def _get_or_compute_static(self, context: AgentContext) -> str:
        """静态段 - global cache"""
        cache_key = "static:capabilities"
        if cache_key in self._global_cache:
            return self._global_cache[cache_key]
        
        # 计算能力描述 (不变的部分)
        capabilities = self._format_capabilities()
        self._global_cache[cache_key] = capabilities
        return capabilities
    
    def _get_or_compute_dynamic(self, context: AgentContext) -> str:
        """动态段 - session cache"""
        cache_key = f"dynamic:{context.session_id}"
        if cache_key in self._session_cache:
            return self._session_cache[cache_key]
        
        # 计算用户上下文 (session 内不变)
        user_context = self._format_user_context(context)
        self._session_cache[cache_key] = user_context
        return user_context
    
    def _compute_volatile(self, intent: str, context: AgentContext) -> str:
        """易变段 - 每轮重新计算"""
        return self._format_intent(intent, context)
```

**缓存 API 设计** (参考 Claude Code):

```python
# 注册 API
def static_section(name: str, compute: Callable) -> Section:
    """静态段 - global cache, 跨用户/会话不变"""
    return Section(name=name, compute=compute, cache_scope="global")

def session_section(name: str, compute: Callable) -> Section:
    """动态段 - session cache, 会话内只计算一次"""
    return Section(name=name, compute=compute, cache_scope="session")

def DANGEROUS_volatile_section(name: str, compute: Callable, reason: str) -> Section:
    """易变段 - 每轮重新计算 (强制写明为什么需要)"""
    return Section(name=name, compute=compute, cache_scope="volatile", reason=reason)
```

**预期收益**:
- Token 成本降低 30-50%
- 缓存命中率提升至 90%+
- 编译时间减少 (缓存命中时跳过计算)

**分布式场景考虑**:
- Global cache 需要在节点间同步 (使用 Redis 或分布式缓存)
- Session cache 本地即可 (会话绑定)
- 缓存失效策略: TTL + 主动失效 (能力注册变化时)

---

### 模式 7: Capability Gate 管线化

#### 问题分析

**IntentOS 现状**:
- 简单权限检查 (`required_permissions` in `Capability`)
- 缺少多步决策管线
- 没有熔断器机制

**Claude Code 的 7 步管线**:
```
1a. 整工具 deny 规则 → 匹配则拒绝 (最高优先级)
1b. 整工具 ask 规则 → 匹配则需要人工确认
1c. tool.checkPermissions() → 工具自身的权限逻辑
1d. 工具返回 deny → 拒绝
1e. requiresUserInteraction + ask → 即使 bypass 也需要确认
1f. 内容级 ask 规则 → bypass 也绕不过
1g. safety check → bypass 也绕不过
2. bypass 模式 → 以上全部通过后, 才允许跳过
3. passthrough → 转为用户确认
```

#### 适配方案

**Capability Gate 管线**:

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class GateDecision(Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"
    PASSTHROUGH = "passthrough"

@dataclass
class GateResult:
    decision: GateDecision
    reason: str
    requires_confirmation: bool = False
    circuit_broken: bool = False

class CapabilityGate:
    """
    Capability Gate - 能力门控管线
    
    决策流程 (deny 优先, bypass-immune 层):
    1. 全局 deny 规则
    2. 权限检查
    3. 安全标注检查
    4. 熔断器检查
    5. 内容级规则
    6. 安全检查 (敏感路径等)
    """
    
    def __init__(self):
        self.deny_rules: set[str] = set()  # 全局禁止的能力
        self.ask_rules: set[str] = set()   # 需要确认的能力
        self.denial_tracker = DenialTracker()
    
    async def evaluate(
        self,
        capability_id: str,
        context: AgentContext,
        input_data: dict,
    ) -> GateResult:
        """执行管线评估"""
        
        # Step 1a: 全局 deny 规则 (最高优先级)
        if capability_id in self.deny_rules:
            return GateResult(GateDecision.DENY, "全局禁止")
        
        # Step 1b: ask 规则 (需要确认)
        if capability_id in self.ask_rules:
            return GateResult(
                GateDecision.ASK,
                "需要用户确认",
                requires_confirmation=True
            )
        
        # Step 1c: 权限检查
        capability = self.registry.get_capability(capability_id)
        if capability and capability.required_permissions:
            if not self._has_permissions(context, capability):
                return GateResult(GateDecision.ASK, "权限不足", requires_confirmation=True)
        
        # Step 1d: 安全标注检查
        if capability:
            if capability.is_destructive(input_data):
                return GateResult(
                    GateDecision.ASK,
                    "破坏性操作",
                    requires_confirmation=True
                )
        
        # Step 1e: 熔断器检查
        if self.denial_tracker.is_circuit_open(capability_id):
            return GateResult(
                GateDecision.DENY,
                "熔断器触发",
                circuit_broken=True
            )
        
        # Step 1f: 内容级规则 (bypass-immune)
        if self._matches_content_rule(capability_id, input_data):
            return GateResult(
                GateDecision.ASK,
                "内容级规则",
                requires_confirmation=True
            )
        
        # Step 1g: 安全检查 (bypass-immune)
        if self._safety_check(input_data):
            return GateResult(
                GateDecision.ASK,
                "安全检查未通过",
                requires_confirmation=True
            )
        
        # 全部通过
        return GateResult(GateDecision.ALLOW, "允许执行")
    
    def _has_permissions(self, context: AgentContext, capability) -> bool:
        """检查权限"""
        user_perms = set(context.permissions)
        required_perms = set(capability.required_permissions)
        return required_perms.issubset(user_perms)
    
    def _matches_content_rule(self, capability_id: str, input_data: dict) -> bool:
        """内容级规则匹配 (bypass-immune)"""
        # 例如: Bash(npm publish:*) 即使 bypass 也需要确认
        return False
    
    def _safety_check(self, input_data: dict) -> bool:
        """安全检查 (bypass-immune)"""
        # 例如: 敏感路径检查 (.git/, .claude/ 等)
        return False
```

**熔断器实现**:

```python
class DenialTracker:
    """
    熔断器 - 防止无限重试
    
    连续 3 次拒绝 或 总计 20 次拒绝 → 熔断
    """
    
    def __init__(self):
        self.consecutive_denials: dict[str, int] = {}
        self.total_denials: dict[str, int] = {}
        self.circuit_open_until: dict[str, float] = {}
    
    def record_denial(self, capability_id: str) -> None:
        """记录拒绝"""
        self.consecutive_denials[capability_id] = \
            self.consecutive_denials.get(capability_id, 0) + 1
        self.total_denials[capability_id] = \
            self.total_denials.get(capability_id, 0) + 1
        
        # 连续 3 次或总计 20 次 → 熔断
        if (self.consecutive_denials[capability_id] >= 3 or
            self.total_denials[capability_id] >= 20):
            self.circuit_open_until[capability_id] = time.time() + 300  # 5 分钟
    
    def is_circuit_open(self, capability_id: str) -> bool:
        """检查熔断器是否开启"""
        if capability_id not in self.circuit_open_until:
            return False
        
        if time.time() < self.circuit_open_until[capability_id]:
            return True
        
        # 熔断器过期, 重置
        del self.circuit_open_until[capability_id]
        self.consecutive_denials[capability_id] = 0
        return False
    
    def record_allow(self, capability_id: str) -> None:
        """记录允许 (重置连续计数)"""
        self.consecutive_denials[capability_id] = 0
```

**模式级变换** (dontAsk/auto/headless):

```python
class PermissionMode(Enum):
    INTERACTIVE = "interactive"  # 正常模式, 可以询问用户
    DONT_ASK = "dont_ask"        # 不询问, 直接拒绝
    AUTO = "auto"                # 自动模式, 使用分类器
    HEADLESS = "headless"        # 无头模式, 使用 Hook

def transform_gate_result(
    result: GateResult,
    mode: PermissionMode,
) -> GateResult:
    """根据权限模式变换管线结果"""
    
    if mode == PermissionMode.DONT_ASK:
        # 不能问用户就直接拒绝
        if result.decision in (GateDecision.ASK, GateDecision.PASSTHROUGH):
            return GateResult(GateDecision.DENY, "dontAsk 模式")
    
    elif mode == PermissionMode.AUTO:
        # 使用分类器 API 评估
        if result.decision == GateDecision.PASSTHROUGH:
            return classify_with_api(result)
    
    elif mode == PermissionMode.HEADLESS:
        # 使用 Hook 系统处理
        if result.decision == GateDecision.PASSTHROUGH:
            return handle_with_hook(result)
    
    return result
```

**集成到能力注册中心**:

```python
class CapabilityRegistry:
    def __init__(self):
        self.gate = CapabilityGate()
        self._capabilities: dict[str, Capability] = {}
    
    async def execute_capability(
        self,
        capability_id: str,
        context: AgentContext,
        **kwargs,
    ) -> Any:
        """执行能力 (带 Capability Gate)"""
        
        capability = self.get_capability(capability_id)
        if not capability:
            raise ValueError(f"能力不存在: {capability_id}")
        
        # ① Capability Gate 检查
        gate_result = await self.gate.evaluate(
            capability_id,
            context,
            kwargs,
        )
        
        # ② 根据决策执行
        if gate_result.decision == GateDecision.DENY:
            if gate_result.circuit_broken:
                raise CircuitBreakerError(
                    f"能力 {capability_id} 熔断器触发"
                )
            raise PermissionError(f"能力 {capability_id} 被拒绝: {gate_result.reason}")
        
        elif gate_result.decision == GateDecision.ASK:
            if gate_result.requires_confirmation:
                # 需要用户确认
                confirmed = await self._ask_user(gate_result)
                if not confirmed:
                    self.gate.denial_tracker.record_denial(capability_id)
                    raise PermissionError("用户拒绝确认")
        
        # ③ 执行能力
        try:
            result = await capability.handler(**kwargs)
            self.gate.denial_tracker.record_allow(capability_id)
            return result
        except Exception as e:
            self.gate.denial_tracker.record_denial(capability_id)
            raise
```

**预期收益**:
- 安全边界清晰, 防止权限绕过
- 熔断器避免无限重试
- bypass-immune 层确保关键安全约束不被覆盖

---

### 模式 3: 能力注册中心增强

#### 问题分析

**IntentOS 现状**:
- 已有 `CapabilityRegistry` (单例, 基础注册/查询/执行)
- 缺少三层条件过滤
- 缺少安全默认值

**Claude Code 的三层过滤**:
```
编译期 DCE → 模块加载期 (环境变量) → 运行时 (isEnabled)
```

#### 适配方案

**三层过滤** (适配 Python 运行时):

```python
class CapabilityRegistry:
    """能力注册中心 (增强版)"""
    
    def __init__(self):
        self._capabilities: dict[str, Capability] = {}
        self._load_conditions: dict[str, Callable] = {}  # 加载期条件
        self._runtime_conditions: dict[str, Callable] = {}  # 运行时条件
    
    def register(
        self,
        id: str,
        name: str,
        description: str,
        handler: Callable,
        input_schema: dict = None,
        output_schema: dict = None,
        required_permissions: list[str] = None,
        source: str = "builtin",
        # 三层过滤
        load_condition: Callable = None,  # 加载期条件 (环境变量/配置)
        runtime_condition: Callable = None,  # 运行时条件 (isEnabled)
        # 安全标注
        is_read_only: bool = False,
        is_concurrency_safe: bool = False,
        is_destructive: Callable = None,
    ) -> Capability:
        """注册能力 (带三层过滤和安全标注)"""
        
        # ① 加载期过滤
        if load_condition and not load_condition():
            return None  # 不注册
        
        # ② 构建能力对象
        capability = Capability(
            id=id,
            name=name,
            description=description,
            handler=handler,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            required_permissions=required_permissions or [],
            source=source,
            # 安全标注
            is_read_only=is_read_only,
            is_concurrency_safe=is_concurrency_safe,
            is_destructive=is_destructive or (lambda: False),
        )
        
        # ③ 注册
        self._capabilities[id] = capability
        self._runtime_conditions[id] = runtime_condition
        
        return capability
    
    def get_enabled_capabilities(self, context: AgentContext) -> list[Capability]:
        """获取已启用的能力 (应用运行时过滤)"""
        enabled = []
        for cap_id, capability in self._capabilities.items():
            # 运行时条件检查
            condition = self._runtime_conditions.get(cap_id)
            if condition and not condition(context):
                continue
            enabled.append(capability)
        return enabled
```

**安全默认值模式**:

```python
# 能力默认值
CAPABILITY_DEFAULTS = {
    "is_read_only": False,           # 默认非只读
    "is_concurrency_safe": False,    # 默认不允许并发
    "is_destructive": lambda: False, # 默认非破坏性
    "check_permissions": lambda: GateDecision.ALLOW,  # 默认允许 (由外层管线兜底)
}

def build_capability(definition: dict) -> Capability:
    """构建能力 (带安全默认值)"""
    return Capability(
        **CAPABILITY_DEFAULTS,
        **definition,  # 显式覆盖默认值
    )
```

**使用示例**:

```python
registry = CapabilityRegistry()

# ① 始终注册 (基础能力)
registry.register(
    id="shell",
    name="Shell",
    description="执行 Shell 命令",
    handler=shell_handler,
    is_concurrency_safe=False,  # 显式标注: 不允许并发
)

# ② 加载期条件 (环境变量控制)
registry.register(
    id="debug_tool",
    name="Debug",
    description="调试工具",
    handler=debug_handler,
    load_condition=lambda: os.getenv("INTENTOS_DEBUG") == "1",
)

# ③ 运行时条件 (动态启用)
registry.register(
    id="experimental_feature",
    name="Experimental",
    description="实验性功能",
    handler=experimental_handler,
    runtime_condition=lambda ctx: ctx.user_id in EXPERIMENTAL_USERS,
)
```

**预期收益**:
- 注册逻辑集中可控
- 安全默认值降低出错风险
- 三层过滤支持灵活的能力管理

---

## P1 模式适配方案

### 模式 2: 语义内存 Store

#### 关键区别

| Claude Code | IntentOS |
|-------------|----------|
| React 状态管理 (UI 层) | **分布式语义内存** (OS 层) |
| 单进程状态 | **跨节点状态同步** |
| `useSyncExternalStore` | **分布式订阅/发布** |

#### 适配方案

```python
class SemanticStore:
    """
    语义内存 Store - 分布式状态管理
    
    管理:
    - 用户意图上下文
    - 能力执行结果缓存
    - 节点间共享状态
    """
    
    def __init__(self, node_id: str, cluster_nodes: list[str] = None):
        self.node_id = node_id
        self._state: dict[str, Any] = {}
        self._listeners: dict[str, set[Callable]] = {}
        self._cluster_nodes = cluster_nodes or []
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """获取语义状态"""
        return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """设置状态 (自动同步到集群)"""
        prev = self._state.get(key)
        
        # 相等性检查 (避免无效更新)
        if prev == value:
            return
        
        self._state[key] = value
        
        # 通知本地监听器
        for listener in self._listeners.get(key, set()):
            listener(key, prev, value)
        
        # 同步到集群 (最终一致性)
        if self._cluster_nodes:
            self._sync_to_cluster(key, value)
    
    def subscribe(self, key: str, callback: Callable) -> Callable:
        """订阅状态变化"""
        if key not in self._listeners:
            self._listeners[key] = set()
        self._listeners[key].add(callback)
        
        # 返回取消订阅函数
        return lambda: self._listeners[key].discard(callback)
    
    def _sync_to_cluster(self, key: str, value: Any) -> None:
        """同步到集群 (使用 Gossip 或 Raft)"""
        # TODO: 实现分布式同步
        pass
```

**问题**:
1. 分布式场景下, 状态一致性如何保证? (最终一致性 vs 强一致性)
2. 是否需要 CRDT (无冲突复制数据类型) 支持?

---

### 模式 6: PEF 执行隔离

#### 关键区别

| Claude Code | IntentOS |
|-------------|----------|
| 多 Agent 状态隔离 | **PEF 执行隔离** (类似进程隔离) |
| 共享父 Agent 状态 | **共享基础设施** (资源追踪器) |

#### 适配方案

```python
def create_pef_execution_context(
    parent_context: ExecutionContext,
    overrides: dict = None,
) -> ExecutionContext:
    """
    创建隔离的 PEF 执行上下文
    
    默认全隔离 + 显式 opt-in 共享 + 基础设施穿透
    """
    overrides = overrides or {}
    
    return ExecutionContext(
        # ① 可变状态 - 克隆隔离
        state=clone_state(overrides.get("state", parent_context.state)),
        permissions=filter_permissions(
            overrides.get("permissions", parent_context.permissions)
        ),
        
        # ② AbortController - 链接而非共享
        abort_controller=overrides.get(
            "abort_controller",
            link_abort_controller(parent_context.abort_controller)
        ),
        
        # ③ 基础设施 - 始终穿透到根
        resource_tracker=parent_context.resource_tracker,  # 必须到达根
        metering=parent_context.metering,  # 计量必须到达根
        
        # ④ UI 回调 - 子 PEF 不控制父 UI
        ui_callbacks=None,
    )
```

---

## P2/P3 模式简述

### 模式 5: 意图配置层 (P2)

**6 层配置优先级**:
```
1. plugin_settings    - 插件基座配置
2. user_settings      - 用户全局偏好 (~/.intentos/settings.json)
3. project_settings   - 项目配置 (.intentos/settings.json, git 提交)
4. local_settings     - 本地配置 (.intentos/settings.local.json, gitignore)
5. flag_settings      - CLI 参数 (--setting key=value)
6. policy_settings    - 企业管理策略 (MDM/remote API)
```

**合并语义**:
- 标量字段: 后来源覆盖先来源
- 数组字段: 拼接后去重

**信任边界**:
- project_settings 和 local_settings 对高风险操作 (env 注入) 不可信
- 只允许白名单内的安全变量

---

### 模式 1: 编译期 DCE (P3)

**不适用原因**:
- IntentOS 是 Python 项目, 非 JS bundler
- 运行时动态加载能力, 非构建期裁剪
- 未来 Web UI 打包时可能用到

**预留方案**:
- 为未来 Web UI 打包预留 feature flag 机制
- 当前优先级最低, 可暂缓

---

## 实施计划

### 阶段 1: P0 模式实现 (立即执行)

| 模式 | 文件 | 预计工作量 |
|------|------|-----------|
| **4. PEF 编译缓存** | `intentos/compiler/cache.py` | 2-3 天 |
| **7. Capability Gate** | `intentos/security/gate.py` | 2-3 天 |
| **3. 能力注册表** | `intentos/agent/registry.py` | 1-2 天 |

### 阶段 2: P1 模式适配 (短期执行)

| 模式 | 文件 | 预计工作量 |
|------|------|-----------|
| **2. 语义内存 Store** | `intentos/core/store.py` | 3-5 天 |
| **6. PEF 执行隔离** | `intentos/semantic_vm/isolation.py` | 2-3 天 |

### 阶段 3: P2 模式 (中期执行)

| 模式 | 文件 | 预计工作量 |
|------|------|-----------|
| **5. 意图配置层** | `intentos/config/settings.py` | 3-5 天 |

### 阶段 4: P3 模式 (长期考虑)

| 模式 | 状态 |
|------|------|
| **1. 编译期 DCE** | 暂缓, 为未来 Web UI 预留 |

---

## 参考文档

- [Claude Code 架构模式总结](/Users/jeffery/Downloads/25-架构模式总结.md)
- [IntentOS 架构文档](./ARCHITECTURE.md)
- [IntentOS 核心原则](./CORE_PRINCIPLES.md)
- [IntentOS 安全与权限](./SECURITY_AND_PERMISSIONS.md)

---

**文档版本**: 1.0  
**创建日期**: 2026-04-03  
**状态**: Draft - 待讨论
