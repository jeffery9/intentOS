"""
意图编译器 v2.0

支持：
- PEF v2.0 格式（人类可读的 YAML/JSON）
- 向后兼容 PEF v1.0
- 标准 Unix I/O（stdin/stdout）
- 管道操作支持

参考: docs/PEF_FORMAT_SPEC.md
"""

from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path
from typing import Any, Optional

from intentos.compiler.pef_format import (
    PEF,
    CapabilityBinding,
    ContextBinding,
    IntentDeclaration,
)


class IntentCompilerV2:
    """
    意图编译器 v2.0
    
    将自然语言意图编译为人类可读的 PEF v2.0 格式
    """

    def __init__(
        self,
        enable_cache: bool = True,
        enable_optimization: bool = True,
        default_format: str = "yaml",
    ) -> None:
        """
        初始化编译器

        Args:
            enable_cache: 启用缓存
            enable_optimization: 启用优化
            default_format: 默认输出格式（yaml/json）
        """
        self.enable_cache = enable_cache
        self.enable_optimization = enable_optimization
        self.default_format = default_format

        # 缓存（使用 v1 缓存系统，PEF 可转换为 v2）
        from intentos.agent.compiler import PEFCache

        self._cache = PEFCache(max_size=1000, ttl=3600)

        # 统计
        self._stats: dict[str, Any] = {
            "compile_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_compile_time_ms": 0.0,
        }

    def compile(
        self,
        goal: str,
        user_id: str,
        capabilities: list[str] | None = None,
        context: dict[str, Any] | None = None,
        session_id: str | None = None,
        output_format: str = "json",
        constraints: dict[str, Any] | None = None,
    ) -> PEF:
        """
        编译意图为 PEF v2.0

        Args:
            goal: 意图目标（自然语言）
            user_id: 用户 ID
            capabilities: 能力列表
            context: 业务上下文
            session_id: 会话 ID
            output_format: 输出格式（json/markdown/text）
            constraints: 约束条件

        Returns:
            PEF v2.0 实例
        """
        start_time = time.time()
        self._stats["compile_count"] += 1

        # 生成缓存键
        cache_key = self._generate_cache_key(goal, capabilities or [], context or {})

        # 检查缓存
        if self.enable_cache:
            cached = self._cache.get(cache_key)
            if cached:
                self._stats["cache_hits"] += 1
                # 转换为 v2.0 格式
                return cached.to_v2()
            self._stats["cache_misses"] += 1

        # 构建能力绑定
        cap_bindings = [
            CapabilityBinding(name=cap) for cap in (capabilities or [])
        ]

        # 构建上下文
        ctx = ContextBinding(
            user_id=user_id,
            session_id=session_id or "",
            business_context=context or {},
        )

        # 构建意图声明
        intent = IntentDeclaration(
            goal=goal,
            output_format=output_format,
        )

        # 构建约束
        final_constraints = constraints or {}
        if self.enable_optimization:
            final_constraints.setdefault("execution", {})
            final_constraints["execution"].setdefault("temperature", 0.0)
            final_constraints["execution"].setdefault("max_tokens", 4096)

        # 创建 PEF
        pef = PEF(
            intent=intent,
            context=ctx,
            capabilities=cap_bindings,
            constraints=final_constraints,
            metadata={"cache_key": cache_key},
        )

        # 缓存（使用 v1 格式缓存以保持兼容）
        if self.enable_cache:
            v1_pef = pef.to_v1()
            self._cache.set(cache_key, v1_pef)

        # 更新统计
        compile_time_ms = (time.time() - start_time) * 1000
        self._update_stats(compile_time_ms)

        return pef

    def compile_from_file(self, file_path: str | Path) -> PEF:
        """
        从 PEF 文件加载并验证

        Args:
            file_path: PEF 文件路径

        Returns:
            PEF v2.0 实例
        """
        pef = PEF.from_file(file_path)
        
        # 验证
        errors = pef.validate()
        if errors:
            raise ValueError(f"PEF validation failed: {', '.join(errors)}")
        
        return pef

    def compile_from_stdin(self) -> PEF:
        """
        从标准输入读取意图（支持 Unix 管道）

        Returns:
            PEF v2.0 实例
        """
        # 读取所有输入
        input_data = sys.stdin.read().strip()
        
        if not input_data:
            raise ValueError("No input from stdin")

        # 检测输入格式
        if input_data.startswith("{") or input_data.startswith("version:"):
            # JSON 或 YAML 格式，直接解析为 PEF
            if input_data.startswith("{"):
                return PEF.from_json(input_data)
            else:
                return PEF.from_yaml(input_data)
        else:
            # 纯文本，作为意图目标
            return self.compile(
                goal=input_data,
                user_id="stdin_user",
            )

    def save_pef(
        self,
        pef: PEF,
        file_path: str | Path,
        format: str | None = None,
    ) -> None:
        """
        保存 PEF 到文件

        Args:
            pef: PEF 实例
            file_path: 文件路径
            format: 输出格式（yaml/json），默认使用编译器配置
        """
        fmt = format or self.default_format
        pef.to_file(file_path, format=fmt)

    def _generate_cache_key(
        self,
        goal: str,
        capabilities: list[str],
        context: dict[str, Any],
    ) -> str:
        """生成缓存键"""
        key_data = f"{goal}|{','.join(sorted(capabilities))}|{str(sorted(context.items()))}"
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def _update_stats(self, compile_time_ms: float) -> None:
        """更新编译统计"""
        count = self._stats["compile_count"]
        avg = self._stats["avg_compile_time_ms"]
        self._stats["avg_compile_time_ms"] = (avg * (count - 1) + compile_time_ms) / count

    def get_stats(self) -> dict[str, Any]:
        """获取编译统计"""
        return {
            **self._stats,
            "cache": self._cache.stats(),
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()


# =============================================================================
# 便捷函数
# =============================================================================


def compile_intent(
    goal: str,
    user_id: str = "default",
    capabilities: list[str] | None = None,
    **kwargs: Any,
) -> PEF:
    """
    快速编译意图

    Args:
        goal: 意图目标
        user_id: 用户 ID
        capabilities: 能力列表
        **kwargs: 其他参数

    Returns:
        PEF v2.0 实例
    """
    compiler = IntentCompilerV2()
    return compiler.compile(
        goal=goal,
        user_id=user_id,
        capabilities=capabilities,
        **kwargs,
    )
