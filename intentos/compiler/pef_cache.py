"""
PEF 三段式缓存优化

将 PEF 编译结果分为三层:
1. Static (Global Cache)    - 跨用户/会话不变
2. Memoized (Session Cache) - 会话内只计算一次
3. Volatile (Per-turn)      - 每轮重新计算

参考 Claude Code 的 Prompt 分段缓存设计。
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# =============================================================================
# 三段式数据结构
# =============================================================================


@dataclass
class PEFSection:
    """PEF 段"""
    name: str
    content: str
    cache_scope: str  # "global", "session", "volatile"
    computed_at: float = field(default_factory=time.time)


@dataclass
class CompiledPEF:
    """
    编译后的 PEF (Prompt Executable File)
    
    三段式结构:
    - static_section: 全局缓存, 跨用户/会话不变
    - dynamic_section: 会话缓存, 会话内只计算一次
    - volatile_section: 每轮重新计算
    """
    
    # ① 静态段 - global cache
    static_section: str
    
    # ② 动态段 - session cache
    dynamic_section: str
    
    # ③ 易变段 - per-turn
    volatile_section: str
    
    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_prompt(self) -> str:
        """组合完整 Prompt (用于执行)"""
        return f"{self.static_section}\n\n{self.dynamic_section}\n\n{self.volatile_section}"
    
    @property
    def cache_key(self) -> str:
        """
        缓存键 (只包含静态段和动态段)
        
        用于 LLM API 缓存优化。
        易变段不影响缓存键。
        """
        cache_content = f"{self.static_section}{self.dynamic_section}"
        return hashlib.blake2b(
            cache_content.encode("utf-8"),
            digest_size=16,
        ).hexdigest()


# =============================================================================
# 段注册 API
# =============================================================================


def static_section(name: str, compute: Callable[[], str]) -> PEFSection:
    """
    静态段 - global cache, 跨用户/会话不变
    
    例如: 能力描述、系统规则、行为准则
    """
    return PEFSection(
        name=name,
        content="",  # 延迟计算
        cache_scope="global",
    )


def session_section(name: str, compute: Callable[[], str]) -> PEFSection:
    """
    动态段 - session cache, 会话内只计算一次
    
    例如: 用户上下文、租户配置、环境信息
    """
    return PEFSection(
        name=name,
        content="",  # 延迟计算
        cache_scope="session",
    )


def DANGEROUS_volatile_section(
    name: str,
    compute: Callable[[], str],
    reason: str,
) -> PEFSection:
    """
    易变段 - 每轮重新计算
    
    强制写明为什么需要每轮重算 (代码级 ADR)。
    
    例如: 当前任务参数、用户输入
    """
    return PEFSection(
        name=name,
        content="",  # 延迟计算
        cache_scope="volatile",
    )


# =============================================================================
# 缓存管理
# =============================================================================


class PEFCacheManager:
    """
    PEF 缓存管理器
    
    管理三层缓存:
    - Global cache: 跨用户/会话不变
    - Session cache: 会话内只计算一次
    - No cache for volatile: 每轮重新计算
    """
    
    def __init__(self):
        self._global_cache: dict[str, str] = {}
        self._session_cache: dict[str, str] = {}
        self._stats: dict[str, int] = {
            "global_hits": 0,
            "global_misses": 0,
            "session_hits": 0,
            "session_misses": 0,
        }
    
    def get_or_compute(
        self,
        section: PEFSection,
        compute_fn: Callable[[], str],
        session_id: Optional[str] = None,
    ) -> str:
        """
        获取或计算段内容
        
        Args:
            section: PEF 段定义
            compute_fn: 计算函数
            session_id: 会话 ID (session cache 需要)
        
        Returns:
            段内容
        """
        if section.cache_scope == "global":
            return self._get_or_compute_global(section.name, compute_fn)
        elif section.cache_scope == "session":
            if not session_id:
                raise ValueError("Session cache requires session_id")
            return self._get_or_compute_session(section.name, compute_fn, session_id)
        else:  # volatile
            # 每轮重新计算
            return compute_fn()
    
    def _get_or_compute_global(
        self,
        key: str,
        compute_fn: Callable[[], str],
    ) -> str:
        """全局缓存"""
        if key in self._global_cache:
            self._stats["global_hits"] += 1
            return self._global_cache[key]
        
        self._stats["global_misses"] += 1
        content = compute_fn()
        self._global_cache[key] = content
        return content
    
    def _get_or_compute_session(
        self,
        key: str,
        compute_fn: Callable[[], str],
        session_id: str,
    ) -> str:
        """会话缓存"""
        cache_key = f"{session_id}:{key}"
        if cache_key in self._session_cache:
            self._stats["session_hits"] += 1
            return self._session_cache[cache_key]
        
        self._stats["session_misses"] += 1
        content = compute_fn()
        self._session_cache[cache_key] = content
        return content
    
    def clear_session_cache(self, session_id: Optional[str] = None) -> None:
        """
        清除会话缓存
        
        Args:
            session_id: 如果提供, 只清除特定会话; 否则清除全部
        """
        if session_id:
            keys_to_remove = [
                k for k in self._session_cache
                if k.startswith(f"{session_id}:")
            ]
            for k in keys_to_remove:
                del self._session_cache[k]
        else:
            self._session_cache.clear()
    
    def clear_global_cache(self) -> None:
        """清除全局缓存"""
        self._global_cache.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total_hits = self._stats["global_hits"] + self._stats["session_hits"]
        total_misses = self._stats["global_misses"] + self._stats["session_misses"]
        total = total_hits + total_misses
        
        return {
            **self._stats,
            "global_cache_size": len(self._global_cache),
            "session_cache_size": len(self._session_cache),
            "hit_rate": total_hits / total if total > 0 else 0.0,
        }


# =============================================================================
# 延迟构造工具
# =============================================================================


def lazy_schema(factory: Callable[[], Any]) -> Callable[[], Any]:
    """
    延迟构造器
    
    将构造推迟到第一次访问时, 既节省启动时间, 又保证后续访问零成本。
    
    用法:
        schema = lazy_schema(lambda: build_complex_schema())
        # 首次调用时才计算
        result1 = schema()
        # 后续调用直接返回缓存
        result2 = schema()
    """
    cached: list[Any] = [None]  # 使用列表实现可变闭包
    
    def wrapper() -> Any:
        if cached[0] is None:
            cached[0] = factory()
        return cached[0]
    
    return wrapper


# =============================================================================
# 辅助函数
# =============================================================================


def compile_pef_three_stage(
    static_sections: list[tuple[str, Callable[[], str]]],
    dynamic_sections: list[tuple[str, Callable[[], str], Optional[str]]],
    volatile_sections: list[tuple[str, Callable[[], str], str]],
    cache_manager: PEFCacheManager,
    session_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> CompiledPEF:
    """
    三段式编译 PEF
    
    Args:
        static_sections: [(name, compute_fn), ...] 静态段
        dynamic_sections: [(name, compute_fn, session_id), ...] 动态段
        volatile_sections: [(name, compute_fn, reason), ...] 易变段
        cache_manager: 缓存管理器
        session_id: 会话 ID
        metadata: 元数据
    
    Returns:
        编译后的 PEF
    """
    # ① 编译静态段
    static_parts = []
    for name, compute_fn in static_sections:
        content = cache_manager.get_or_compute(
            PEFSection(name=name, content="", cache_scope="global"),
            compute_fn,
        )
        static_parts.append(content)
    
    # ② 编译动态段
    dynamic_parts = []
    for name, compute_fn, dyn_session_id in dynamic_sections:
        sid = dyn_session_id or session_id
        content = cache_manager.get_or_compute(
            PEFSection(name=name, content="", cache_scope="session"),
            compute_fn,
            session_id=sid,
        )
        dynamic_parts.append(content)
    
    # ③ 编译易变段
    volatile_parts = []
    for name, compute_fn, reason in volatile_sections:
        # 每轮重新计算
        content = compute_fn()
        volatile_parts.append(content)
    
    # 组合三段
    static_section = "\n\n".join(static_parts) if static_parts else ""
    dynamic_section = "\n\n".join(dynamic_parts) if dynamic_parts else ""
    volatile_section = "\n\n".join(volatile_parts) if volatile_parts else ""
    
    return CompiledPEF(
        static_section=static_section,
        dynamic_section=dynamic_section,
        volatile_section=volatile_section,
        metadata=metadata or {},
    )
