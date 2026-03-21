"""
意图编译器（优化版）

支持 PEF 缓存、优化和增量编译
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class PEF:
    """Prompt Executable File"""
    version: str = "1.0"
    id: str = field(default_factory=lambda: f"pef_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    intent: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    capabilities: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # 优化字段
    compiled_at: str = field(default_factory=lambda: datetime.now().isoformat())
    cache_key: str = ""
    token_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "id": self.id,
            "intent": self.intent,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "capabilities": self.capabilities,
            "constraints": self.constraints,
            "metadata": self.metadata,
            "compiled_at": self.compiled_at,
            "cache_key": self.cache_key,
            "token_count": self.token_count,
        }


@dataclass
class PEFCacheEntry:
    """PEF 缓存条目"""
    pef: PEF
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


class PEFCache:
    """PEF 缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size: int = max_size
        self.ttl: int = ttl  # 秒
        self._cache: dict[str, PEFCacheEntry] = {}

    def get(self, cache_key: str) -> Optional[PEF]:
        """获取缓存的 PEF"""
        entry = self._cache.get(cache_key)
        if not entry:
            return None

        # 检查 TTL
        if time.time() - entry.created_at > self.ttl:
            del self._cache[cache_key]
            return None

        # 更新访问统计
        entry.access_count += 1
        entry.last_accessed = time.time()

        return entry.pef

    def set(self, cache_key: str, pef: PEF) -> None:
        """缓存 PEF"""
        # 清理过期缓存
        self._cleanup()

        # 如果缓存已满，删除最少访问的
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        self._cache[cache_key] = PEFCacheEntry(pef=pef)

    def _cleanup(self) -> None:
        """清理过期缓存"""
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v.created_at > self.ttl]
        for k in expired:
            del self._cache[k]

    def _evict_lru(self) -> None:
        """删除最少访问的缓存"""
        if not self._cache:
            return

        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
        del self._cache[lru_key]

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
        }


class IntentCompiler:
    """意图编译器（优化版）"""

    def __init__(self, enable_cache: bool = True, enable_optimization: bool = True) -> None:
        self._prompt_templates: dict[str, str] = {}
        self._register_default_templates()

        # 优化选项
        self.enable_cache: bool = enable_cache
        self.enable_optimization: bool = enable_optimization

        # 缓存
        self._cache: PEFCache = PEFCache(max_size=1000, ttl=3600)

        # 统计
        self._stats: dict[str, Any] = {
            "compile_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_compile_time_ms": 0.0,
        }

    def _register_default_templates(self) -> None:
        """注册默认 Prompt 模板"""
        self._prompt_templates["default"] = """你是一个 AI 智能助理。可用能力：{capabilities}。用户意图：{intent}。"""
        self._prompt_templates["optimized"] = """角色：AI 助理
能力：{capabilities}
任务：{intent}
要求：直接执行，不要多余解释。"""

    def compile(
        self,
        intent: str,
        capabilities: list[str],
        context: Optional[dict[str, Any]] = None,
        optimize: bool = True
    ) -> PEF:
        """编译意图为 PEF"""
        start_time: float = time.time()
        self._stats["compile_count"] += 1

        # 生成缓存键
        cache_key: str = self._generate_cache_key(intent, capabilities, context or {})

        # 检查缓存
        if self.enable_cache:
            cached_pef = self._cache.get(cache_key)
            if cached_pef:
                self._stats["cache_hits"] += 1
                return cached_pef

            self._stats["cache_misses"] += 1

        # 选择模板
        template_name: str = "optimized" if (optimize and self.enable_optimization) else "default"
        template: str = self._prompt_templates.get(template_name, self._prompt_templates["default"])

        # 填充模板
        system_prompt: str = template.format(
            capabilities=", ".join(capabilities),
            intent=intent,
        )

        user_prompt: str = f"请执行：{intent}"

        # 创建 PEF
        pef = PEF(
            intent=intent,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            capabilities=capabilities,
            metadata=context or {},
            cache_key=cache_key,
        )

        # 优化
        if optimize and self.enable_optimization:
            self._optimize_pef(pef)

        # 缓存
        if self.enable_cache:
            self._cache.set(cache_key, pef)

        # 更新统计
        compile_time_ms: float = (time.time() - start_time) * 1000
        self._update_stats(compile_time_ms)

        return pef

    def _generate_cache_key(self, intent: str, capabilities: list[str], context: dict[str, Any]) -> str:
        """生成缓存键"""
        key_data: str = f"{intent}|{','.join(sorted(capabilities))}|{str(sorted(context.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _optimize_pef(self, pef: PEF) -> None:
        """优化 PEF"""
        # 1. 压缩空白字符
        pef.system_prompt = " ".join(pef.system_prompt.split())
        pef.user_prompt = " ".join(pef.user_prompt.split())

        # 2. 估算 Token 数
        pef.token_count = self._estimate_token_count(pef)

        # 3. 添加优化约束
        pef.constraints.update({
            "temperature": 0.0,  # 确定性执行
            "max_tokens": 2048,
            "stream": False,
        })

    def _estimate_token_count(self, pef: PEF) -> int:
        """估算 Token 数"""
        # 简单估算：每 4 个字符约 1 个 token
        total_chars: int = len(pef.system_prompt) + len(pef.user_prompt)
        return total_chars // 4

    def _update_stats(self, compile_time_ms: float) -> None:
        """更新统计"""
        count: int = self._stats["compile_count"]
        avg: float = self._stats["avg_compile_time_ms"]
        self._stats["avg_compile_time_ms"] = (avg * (count - 1) + compile_time_ms) / count

    def get_cache(self) -> PEFCache:
        """获取缓存对象"""
        return self._cache

    def get_stats(self) -> dict[str, Any]:
        """获取编译统计"""
        return {
            **self._stats,
            "cache": self._cache.stats(),
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
