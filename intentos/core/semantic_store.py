"""
语义内存 Store - 分布式状态管理

管理分布式语义状态:
- 用户意图上下文
- 能力执行结果缓存
- 节点间共享状态

参考 Claude Code 的极简 Store 设计 (35 行核心代码), 适配到分布式 OS 场景。

核心特性:
- 零依赖 (不依赖框架)
- Object.is 相等性检查
- onChange 回调 (集中式副作用)
- subscribe 返回取消函数 (兼容 useSyncExternalStore)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar, Generic


# =============================================================================
# 类型定义
# =============================================================================


T = TypeVar('T')


@dataclass
class Store(Generic[T]):
    """
    极简 Store - 桥接 React 与非 React 世界
    
    核心接口:
    - getState: 获取状态
    - setState: 更新状态 (updater 模式)
    - subscribe: 订阅变化
    
    与 React 18 useSyncExternalStore 天然兼容。
    """
    
    _state: T
    _listeners: set[Callable[[], None]] = field(default_factory=set)
    _on_change: Optional[Callable[[dict[str, Any]], None]] = None
    
    def get_state(self) -> T:
        """获取当前状态"""
        return self._state
    
    def set_state(self, updater: Callable[[T], T]) -> None:
        """
        更新状态
        
        Args:
            updater: 状态更新函数 (prev -> next)
        """
        prev = self._state
        next_state = updater(prev)
        
        # Object.is 相等性检查 (与 React 行为一致)
        if next_state is prev or next_state == prev:
            return
        
        self._state = next_state
        
        # 集中式副作用
        if self._on_change:
            self._on_change({
                "new_state": next_state,
                "old_state": prev,
            })
        
        # 通知所有监听器
        for listener in self._listeners:
            listener()
    
    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        """
        订阅状态变化

        Args:
            listener: 监听函数

        Returns:
            取消订阅函数
        """
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)


def create_store(
    initial_state: T,
    on_change: Optional[Callable[[dict[str, Any]], None]] = None,
) -> Store[T]:
    """
    创建 Store 实例
    
    Args:
        initial_state: 初始状态
        on_change: 状态变化回调 (用于副作用: 日志、持久化、同步等)
    
    Returns:
        Store 实例
    """
    return Store(
        _state=initial_state,
        _on_change=on_change,
    )


# =============================================================================
# 语义内存 Store
# =============================================================================


@dataclass
class SemanticState:
    """
    语义状态
    
    管理:
    - 用户意图上下文
    - 能力执行结果缓存
    - 节点间共享状态
    """
    
    # 用户意图上下文
    user_context: dict[str, Any] = field(default_factory=dict)
    
    # 能力执行结果缓存
    capability_cache: dict[str, Any] = field(default_factory=dict)
    
    # 节点间共享状态
    shared_state: dict[str, Any] = field(default_factory=dict)
    
    # 会话状态
    session_state: dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    metadata: dict[str, Any] = field(default_factory=lambda: {
        "created_at": time.time(),
        "updated_at": time.time(),
        "version": 0,
    })
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.metadata["updated_at"] = time.time()
        self.metadata["version"] = self.metadata.get("version", 0) + 1


class SemanticMemoryStore:
    """
    语义内存 Store - 分布式状态管理
    
    封装 Store[T], 提供语义状态的高级操作。
    
    使用示例:
        store = SemanticMemoryStore(node_id="node1")
        
        # 设置状态
        store.set_user_context("user_id", {"name": "Alice"})
        
        # 获取状态
        context = store.get_user_context("user_id")
        
        # 订阅变化
        unsubscribe = store.subscribe(lambda: print("State changed"))
    """
    
    def __init__(
        self,
        node_id: str,
        cluster_nodes: Optional[list[str]] = None,
    ):
        """
        初始化语义内存 Store
        
        Args:
            node_id: 当前节点 ID
            cluster_nodes: 集群节点列表 (用于分布式同步)
        """
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes or []
        
        # 创建核心 Store
        self._store = create_store(
            initial_state=SemanticState(),
            on_change=self._on_state_change,
        )
        
        # 分布式同步相关
        self._sync_queue: list[dict[str, Any]] = []
        self._last_sync_time: float = 0.0
    
    # =====================================================================
    # 状态访问
    # =====================================================================
    
    def get_state(self) -> SemanticState:
        """获取语义状态"""
        return self._store.get_state()
    
    def set_state(self, updater: Callable[[SemanticState], SemanticState]) -> None:
        """
        更新语义状态
        
        Args:
            updater: 状态更新函数
        """
        def wrapped(prev: SemanticState) -> SemanticState:
            next_state = updater(prev)
            next_state.update_timestamp()
            return next_state
        
        self._store.set_state(wrapped)
    
    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        """订阅状态变化"""
        return self._store.subscribe(listener)
    
    # =====================================================================
    # 高级操作
    # =====================================================================
    
    def set_user_context(self, user_id: str, context: dict[str, Any]) -> None:
        """设置用户上下文"""
        def updater(state: SemanticState) -> SemanticState:
            state.user_context[user_id] = context
            return state
        
        self.set_state(updater)
    
    def get_user_context(self, user_id: str) -> Optional[dict[str, Any]]:
        """获取用户上下文"""
        return self.get_state().user_context.get(user_id)
    
    def set_capability_cache(self, key: str, value: Any) -> None:
        """设置能力缓存"""
        def updater(state: SemanticState) -> SemanticState:
            state.capability_cache[key] = value
            return state
        
        self.set_state(updater)
    
    def get_capability_cache(self, key: str) -> Optional[Any]:
        """获取能力缓存"""
        return self.get_state().capability_cache.get(key)
    
    def set_shared_state(self, key: str, value: Any) -> None:
        """设置共享状态"""
        def updater(state: SemanticState) -> SemanticState:
            state.shared_state[key] = value
            return state
        
        self.set_state(updater)
    
    def get_shared_state(self, key: str) -> Optional[Any]:
        """获取共享状态"""
        return self.get_state().shared_state.get(key)
    
    def set_session_state(self, session_id: str, state: dict[str, Any]) -> None:
        """设置会话状态"""
        def updater(current: SemanticState) -> SemanticState:
            current.session_state[session_id] = state
            return current
        
        self.set_state(updater)
    
    def get_session_state(self, session_id: str) -> Optional[dict[str, Any]]:
        """获取会话状态"""
        return self.get_state().session_state.get(session_id)
    
    # =====================================================================
    # 分布式同步
    # =====================================================================
    
    def _on_state_change(self, args: dict[str, Any]) -> None:
        """
        状态变化回调 (集中式副作用)
        
        用于:
        - 日志记录
        - 持久化
        - 分布式同步
        """
        new_state = args["new_state"]
        old_state = args["old_state"]
        
        # 记录到同步队列
        self._sync_queue.append({
            "node_id": self.node_id,
            "timestamp": time.time(),
            "version": new_state.metadata["version"],
            "changes": self._compute_diff(old_state, new_state),
        })
        
        # 触发分布式同步 (如果配置了集群节点)
        if self.cluster_nodes:
            self._sync_to_cluster()
    
    def _compute_diff(
        self,
        old_state: SemanticState,
        new_state: SemanticState,
    ) -> dict[str, Any]:
        """计算状态差异"""
        diff = {}
        
        # 比较用户上下文
        if old_state.user_context != new_state.user_context:
            diff["user_context"] = new_state.user_context
        
        # 比较能力缓存
        if old_state.capability_cache != new_state.capability_cache:
            diff["capability_cache"] = new_state.capability_cache
        
        # 比较共享状态
        if old_state.shared_state != new_state.shared_state:
            diff["shared_state"] = new_state.shared_state
        
        # 比较会话状态
        if old_state.session_state != new_state.session_state:
            diff["session_state"] = new_state.session_state
        
        return diff
    
    def _sync_to_cluster(self) -> None:
        """
        同步到集群
        
        TODO: 实现分布式同步协议
        - 使用 Gossip 协议传播状态变更
        - 或使用 Raft 协议保证强一致性
        """
        # 频率限制 (最多每秒同步一次)
        now = time.time()
        if now - self._last_sync_time < 1.0:
            return
        
        self._last_sync_time = now
        
        # TODO: 实际同步逻辑
        # for node_id in self.cluster_nodes:
        #     if node_id != self.node_id:
        #         self._send_sync(node_id, self._sync_queue[-1])
    
    def get_sync_stats(self) -> dict[str, Any]:
        """获取同步统计"""
        return {
            "node_id": self.node_id,
            "cluster_nodes": self.cluster_nodes,
            "sync_queue_size": len(self._sync_queue),
            "last_sync_time": self._last_sync_time,
            "current_version": self.get_state().metadata.get("version", 0),
        }
    
    # =====================================================================
    # 工具方法
    # =====================================================================
    
    def clear(self) -> None:
        """清空所有状态"""
        def updater(state: SemanticState) -> SemanticState:
            return SemanticState()
        
        self.set_state(updater)
    
    def get_stats(self) -> dict[str, Any]:
        """获取 Store 统计"""
        state = self.get_state()
        return {
            "node_id": self.node_id,
            "user_context_size": len(state.user_context),
            "capability_cache_size": len(state.capability_cache),
            "shared_state_size": len(state.shared_state),
            "session_state_size": len(state.session_state),
            "version": state.metadata.get("version", 0),
            "sync_stats": self.get_sync_stats(),
        }
