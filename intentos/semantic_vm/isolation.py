"""
PEF 执行隔离 - 分布式进程隔离机制

参考 Claude Code 的 Agent 隔离设计 (Context Clone + Shared Infrastructure),
适配到 IntentOS 的 PEF 执行场景。

核心原则:
- 默认全隔离 (防止互相干扰)
- 显式 opt-in 共享 (最小权限原则)
- 基础设施穿透 (资源管理必须到达根级别)

使用场景:
- 子 PEF 执行 (类似子进程)
- 分布式 Map-Reduce 节点隔离
- 多租户执行环境隔离
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# =============================================================================
# 执行上下文
# =============================================================================


@dataclass
class AbortController:
    """
    中止控制器
    
    支持链接模式: 子控制器可以链接到父控制器,
    父控制器中止时自动触发所有子控制器中止。
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _aborted: bool = False
    _on_abort: Optional[Callable[[], None]] = None
    _children: list["AbortController"] = field(default_factory=list)
    _parent: Optional["AbortController"] = None
    
    @property
    def is_aborted(self) -> bool:
        """检查是否已中止"""
        return self._aborted
    
    def abort(self, reason: str = "Aborted") -> None:
        """中止执行"""
        if self._aborted:
            return
        
        self._aborted = True
        
        # 触发回调
        if self._on_abort:
            self._on_abort()
        
        # 传播到所有子控制器
        for child in self._children:
            child.abort(f"Parent aborted: {reason}")
    
    def on_abort(self, callback: Callable[[], None]) -> None:
        """注册中止回调"""
        self._on_abort = callback
    
    def link_to_parent(self, parent: "AbortController") -> None:
        """链接到父控制器"""
        self._parent = parent
        parent._children.append(self)
        
        # 如果父控制器已中止, 立即中止
        if parent.is_aborted:
            self.abort("Parent already aborted")


@dataclass
class ResourceTracker:
    """
    资源追踪器
    
    追踪:
    - CPU 时间
    - 内存使用
    - 网络请求
    - 能力调用
    
    基础设施穿透: 即使状态隔离, 资源追踪必须到达根级别。
    """
    
    cpu_time_ms: float = 0.0
    memory_mb: float = 0.0
    network_requests: int = 0
    capability_calls: int = 0
    start_time: float = field(default_factory=time.time)
    
    def record_cpu_time(self, ms: float) -> None:
        """记录 CPU 时间"""
        self.cpu_time_ms += ms
    
    def record_memory(self, mb: float) -> None:
        """记录内存使用"""
        self.memory_mb += mb
    
    def record_network_request(self) -> None:
        """记录网络请求"""
        self.network_requests += 1
    
    def record_capability_call(self) -> None:
        """记录能力调用"""
        self.capability_calls += 1
    
    def get_stats(self) -> dict[str, Any]:
        """获取资源使用统计"""
        return {
            "cpu_time_ms": self.cpu_time_ms,
            "memory_mb": self.memory_mb,
            "network_requests": self.network_requests,
            "capability_calls": self.capability_calls,
            "elapsed_ms": (time.time() - self.start_time) * 1000,
        }


@dataclass
class ExecutionContext:
    """
    PEF 执行上下文
    
    隔离策略:
    - 默认全隔离 (状态、权限、资源)
    - 显式 opt-in 共享 (基础设施穿透)
    """
    
    # ① 可变状态 - 克隆隔离
    state: dict[str, Any] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    
    # ② AbortController - 链接而非共享
    abort_controller: Optional[AbortController] = None
    
    # ③ 基础设施 - 始终穿透到根
    resource_tracker: Optional[ResourceTracker] = None
    metering: Optional[Any] = None  # 计量器 (必须到达根)
    
    # ④ UI 回调 - 子 PEF 不控制父 UI
    ui_callbacks: Optional[dict[str, Any]] = None
    
    # ⑤ 元数据
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_execution_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def clone(self) -> "ExecutionContext":
        """克隆执行上下文 (用于隔离)"""
        return ExecutionContext(
            # 克隆状态 (深拷贝)
            state={k: v.copy() if isinstance(v, dict) else v for k, v in self.state.items()},
            permissions=self.permissions.copy(),
            
            # 新的 AbortController (不共享)
            abort_controller=AbortController(),
            
            # 基础设施穿透 (共享根级别)
            resource_tracker=self.resource_tracker,
            metering=self.metering,
            
            # UI 回调隔离 (子 PEF 不控制父 UI)
            ui_callbacks=None,
            
            # 元数据
            parent_execution_id=self.execution_id,
        )


# =============================================================================
# 隔离上下文创建器
# =============================================================================


@dataclass
class IsolationOverrides:
    """
    隔离覆盖选项
    
    用于显式 opt-in 共享特定资源。
    """
    
    # 共享状态 (默认克隆)
    share_state: bool = False
    
    # 共享权限 (默认克隆)
    share_permissions: bool = False
    
    # 共享 AbortController (默认创建新的并链接到父)
    share_abort_controller: bool = False
    
    # 共享资源追踪器 (默认穿透到根)
    share_resource_tracker: bool = True  # 默认共享 (基础设施)
    
    # 共享计量器 (默认穿透到根)
    share_metering: bool = True  # 默认共享 (基础设施)
    
    # 共享 UI 回调 (默认隔离)
    share_ui_callbacks: bool = False


def create_isolated_context(
    parent_context: ExecutionContext,
    overrides: Optional[IsolationOverrides] = None,
) -> ExecutionContext:
    """
    创建隔离的 PEF 执行上下文
    
    设计原则:
    - 默认全隔离 (防止互相干扰)
    - 显式 opt-in 共享 (最小权限原则)
    - 基础设施穿透 (资源管理必须到达根级别)
    
    Args:
        parent_context: 父执行上下文
        overrides: 覆盖选项
    
    Returns:
        隔离的执行上下文
    """
    overrides = overrides or IsolationOverrides()
    
    # ① 可变状态 - 默认克隆隔离
    if overrides.share_state:
        state = parent_context.state
    else:
        # 深拷贝状态
        state = {
            k: v.copy() if isinstance(v, dict) else v
            for k, v in parent_context.state.items()
        }
    
    # ② 权限 - 默认克隆
    if overrides.share_permissions:
        permissions = parent_context.permissions
    else:
        permissions = parent_context.permissions.copy()
    
    # ③ AbortController - 默认创建新的并链接到父
    if overrides.share_abort_controller:
        abort_controller = parent_context.abort_controller
    else:
        # 创建新的控制器并链接到父
        abort_controller = AbortController()
        if parent_context.abort_controller:
            abort_controller.link_to_parent(parent_context.abort_controller)
    
    # ④ 基础设施 - 始终穿透到根 (默认共享)
    resource_tracker = parent_context.resource_tracker if overrides.share_resource_tracker else ResourceTracker()
    metering = parent_context.metering if overrides.share_metering else None
    
    # ⑤ UI 回调 - 子 PEF 不控制父 UI (默认隔离)
    ui_callbacks = parent_context.ui_callbacks if overrides.share_ui_callbacks else None
    
    return ExecutionContext(
        state=state,
        permissions=permissions,
        abort_controller=abort_controller,
        resource_tracker=resource_tracker,
        metering=metering,
        ui_callbacks=ui_callbacks,
        parent_execution_id=parent_context.execution_id,
    )


# =============================================================================
# 隔离管理器
# =============================================================================


class IsolationManager:
    """
    隔离管理器
    
    管理多个隔离的执行上下文, 支持:
    - 创建隔离上下文
    - 追踪资源使用
    - 中止执行
    - 汇总统计
    """
    
    def __init__(self, root_resource_tracker: Optional[ResourceTracker] = None):
        """
        初始化隔离管理器
        
        Args:
            root_resource_tracker: 根资源追踪器 (所有子上下文共享)
        """
        self.root_resource_tracker = root_resource_tracker or ResourceTracker()
        self._contexts: dict[str, ExecutionContext] = {}
    
    def create_context(
        self,
        parent_context: Optional[ExecutionContext] = None,
        overrides: Optional[IsolationOverrides] = None,
    ) -> ExecutionContext:
        """
        创建隔离上下文
        
        Args:
            parent_context: 父上下文 (如果为 None, 创建根上下文)
            overrides: 覆盖选项
        
        Returns:
            隔离上下文
        """
        if parent_context is None:
            # 创建根上下文
            context = ExecutionContext(
                resource_tracker=self.root_resource_tracker,
            )
        else:
            # 创建隔离子上下文
            context = create_isolated_context(parent_context, overrides)
            # 确保资源追踪器穿透到根
            context.resource_tracker = self.root_resource_tracker
        
        self._contexts[context.execution_id] = context
        return context
    
    def get_context(self, execution_id: str) -> Optional[ExecutionContext]:
        """获取执行上下文"""
        return self._contexts.get(execution_id)
    
    def abort_context(self, execution_id: str, reason: str = "Aborted") -> bool:
        """中止执行上下文"""
        context = self._contexts.get(execution_id)
        if context and context.abort_controller:
            context.abort_controller.abort(reason)
            return True
        return False
    
    def abort_all(self, reason: str = "All aborted") -> None:
        """中止所有执行上下文"""
        for context in self._contexts.values():
            if context.abort_controller:
                context.abort_controller.abort(reason)
    
    def get_stats(self) -> dict[str, Any]:
        """获取所有上下文的统计信息"""
        return {
            "context_count": len(self._contexts),
            "resource_usage": self.root_resource_tracker.get_stats(),
            "contexts": {
                ctx.execution_id: {
                    "parent_id": ctx.parent_execution_id,
                    "permissions": len(ctx.permissions),
                    "state_keys": len(ctx.state),
                    "is_aborted": ctx.abort_controller.is_aborted if ctx.abort_controller else False,
                }
                for ctx in self._contexts.values()
            },
        }
    
    def cleanup(self) -> None:
        """清理所有上下文"""
        self._contexts.clear()


# =============================================================================
# 辅助函数
# =============================================================================


def clone_state(state: dict[str, Any]) -> dict[str, Any]:
    """克隆状态 (浅拷贝)"""
    return {
        k: v.copy() if isinstance(v, dict) else v
        for k, v in state.items()
    }


def link_abort_controller(
    parent: AbortController,
    child: Optional[AbortController] = None,
) -> AbortController:
    """
    创建链接到父控制器的子控制器
    
    父控制器中止时自动触发子控制器中止。
    """
    if child is None:
        child = AbortController()
    
    child.link_to_parent(parent)
    return child


def filter_permissions(
    permissions: list[str],
    allowed: Optional[set[str]] = None,
    denied: Optional[set[str]] = None,
) -> list[str]:
    """
    过滤权限
    
    Args:
        permissions: 原始权限列表
        allowed: 允许白名单 (如果提供, 只保留这些权限)
        denied: 拒绝黑名单 (如果提供, 移除这些权限)
    
    Returns:
        过滤后的权限列表
    """
    result = permissions
    
    if allowed is not None:
        result = [p for p in result if p in allowed]
    
    if denied is not None:
        result = [p for p in result if p not in denied]
    
    return result
