# -*- coding: utf-8 -*-
"""
IntentOS Meditation Engine

冥想引擎 - 定期整理记忆，防止膨胀
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from ..memory.models import MemoryEntry, MemoryContentType, SessionMemory
from .merger import MemoryMerger
from .conflict_resolver import ConflictResolver
from .pruner import MemoryPruner

logger = logging.getLogger(__name__)


@dataclass
class MeditationConfig:
    """冥想配置"""
    # 触发冥想的 session 数量阈值
    session_threshold: int = 5
    # 记忆保留天数（超过此天数的可能被淘汰）
    retention_days: int = 30
    # 最小重要性评分（低于此值的记忆可能被清理）
    min_importance: float = 3.0
    # 是否自动合并重复
    auto_merge: bool = True
    # 是否自动解决矛盾
    auto_resolve_conflicts: bool = True
    # 是否自动淘汰过时记忆
    auto_prune: bool = True
    # 相似度阈值（用于检测重复）
    similarity_threshold: float = 0.8


@dataclass
class MeditationResult:
    """冥想结果"""
    # 冥想时间
    timestamp: datetime = field(default_factory=datetime.now)
    # 处理的 session 数量
    sessions_processed: int = 0
    # 处理的记忆数量
    memories_processed: int = 0
    # 合并的记忆数量
    memories_merged: int = 0
    # 解决的矛盾数量
    conflicts_resolved: int = 0
    # 淘汰的记忆数量
    memories_pruned: int = 0
    # 生成的新记忆（提炼的核心原则）
    new_memories: list[MemoryEntry] = field(default_factory=list)
    # 详细报告
    report: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "sessions_processed": self.sessions_processed,
            "memories_processed": self.memories_processed,
            "memories_merged": self.memories_merged,
            "conflicts_resolved": self.conflicts_resolved,
            "memories_pruned": self.memories_pruned,
            "new_memories_count": len(self.new_memories),
            "report": self.report,
        }


class MeditationEngine:
    """
    冥想引擎
    
    定期整理记忆：
    1. 合并重复 - 识别并合并相似的记忆条目
    2. 删除矛盾 - 识别并解决冲突的记忆
    3. 淘汰过时 - 移除被新信息覆盖的旧记忆
    4. 提炼核心 - 从大量记忆中提炼核心原则
    """
    
    def __init__(self, config: Optional[MeditationConfig] = None):
        self.config = config or MeditationConfig()
        self.pending_sessions: list[SessionMemory] = []
        
        # 子组件
        self.merger = MemoryMerger(similarity_threshold=self.config.similarity_threshold)
        self.conflict_resolver = ConflictResolver()
        self.pruner = MemoryPruner(
            retention_days=self.config.retention_days,
            min_importance=self.config.min_importance,
        )
        
        logger.info("冥想引擎初始化完成")
    
    def add_session(self, session: SessionMemory) -> bool:
        """
        添加会话，检查是否触发冥想
        
        Returns:
            是否触发了冥想
        """
        self.pending_sessions.append(session)
        
        if len(self.pending_sessions) >= self.config.session_threshold:
            logger.info(f"已达到冥想阈值 ({self.config.session_threshold} 个 session)")
            return True
        
        return False
    
    async def meditate(self) -> MeditationResult:
        """
        执行冥想
        
        Returns:
            冥想结果
        """
        logger.info(f"开始冥想，处理 {len(self.pending_sessions)} 个会话")
        
        result = MeditationResult(
            sessions_processed=len(self.pending_sessions),
        )
        
        # 收集所有记忆
        all_memories: list[MemoryEntry] = []
        for session in self.pending_sessions:
            all_memories.extend(session.memory_entries)
        
        result.memories_processed = len(all_memories)
        logger.info(f"共 {len(all_memories)} 条记忆待处理")
        
        # 1. 合并重复
        if self.config.auto_merge:
            logger.info("步骤 1: 合并重复记忆")
            merged_memories, merge_count = self.merger.merge_duplicates(all_memories)
            result.memories_merged = merge_count
            all_memories = merged_memories
            logger.info(f"合并了 {merge_count} 条重复记忆")
        
        # 2. 解决矛盾
        if self.config.auto_resolve_conflicts:
            logger.info("步骤 2: 解决矛盾")
            resolved_memories, conflict_count = self.conflict_resolver.resolve_conflicts(all_memories)
            result.conflicts_resolved = conflict_count
            all_memories = resolved_memories
            logger.info(f"解决了 {conflict_count} 个矛盾")
        
        # 3. 淘汰过时
        if self.config.auto_prune:
            logger.info("步骤 3: 淘汰过时记忆")
            pruned_memories, prune_count = self.pruner.prune_outdated(all_memories)
            result.memories_pruned = prune_count
            all_memories = pruned_memories
            logger.info(f"淘汰了 {prune_count} 条过时记忆")
        
        # 4. 提炼核心原则
        logger.info("步骤 4: 提炼核心原则")
        new_memories = self._distill_principles(all_memories)
        result.new_memories = new_memories
        logger.info(f"提炼了 {len(new_memories)} 条核心原则")
        
        # 生成报告
        result.report = self._generate_report(all_memories, new_memories)
        
        # 清空待处理队列
        self.pending_sessions.clear()
        
        logger.info("冥想完成")
        return result
    
    def _distill_principles(self, memories: list[MemoryEntry]) -> list[MemoryEntry]:
        """
        从记忆中提炼核心原则
        
        通过分析：
        - 重复出现的模式
        - 高重要性的记忆
        - 跨 session 的共性
        """
        principles = []
        
        # 1. 分析模式出现频率
        pattern_counts: dict[str, list[MemoryEntry]] = {}
        for memory in memories:
            for pattern in memory.patterns:
                key = pattern.name
                if key not in pattern_counts:
                    pattern_counts[key] = []
                pattern_counts[key].append(memory)
        
        # 2. 为高频模式生成原则
        for pattern_name, related_memories in pattern_counts.items():
            if len(related_memories) >= 2:  # 至少出现 2 次
                # 计算平均重要性
                avg_importance = sum(m.importance for m in related_memories) / len(related_memories)
                
                # 提炼原则
                principle = MemoryEntry(
                    memory_type=MemoryContentType.PATTERN,
                    content=f"核心原则：{pattern_name}",
                    patterns=[{
                        "name": pattern_name,
                        "description": f"基于 {len(related_memories)} 次经验提炼",
                        "occurrences": len(related_memories),
                    }],
                    importance=min(10.0, avg_importance + 1),  # 提炼后的原则更重要
                    tags=["principle", "distilled"],
                )
                principles.append(principle)
        
        # 3. 从高重要性记忆提炼
        high_importance_memories = [m for m in memories if m.importance >= 8.0]
        if high_importance_memories:
            # 分组提炼
            by_type: dict[MemoryContentType, list[MemoryEntry]] = {}
            for m in high_importance_memories:
                if m.memory_type not in by_type:
                    by_type[m.memory_type] = []
                by_type[m.memory_type].append(m)
            
            for mem_type, type_memories in by_type.items():
                if len(type_memories) >= 2:
                    # 总结共同点
                    common_content = self._find_common_content(type_memories)
                    if common_content:
                        principle = MemoryEntry(
                            memory_type=mem_type,
                            content=f"重要经验：{common_content}",
                            importance=9.0,
                            tags=["principle", "high_importance"],
                        )
                        principles.append(principle)
        
        return principles
    
    def _find_common_content(self, memories: list[MemoryEntry]) -> str:
        """查找记忆的共同内容"""
        if not memories:
            return ""
        
        # 简单实现：取第一条记忆的内容摘要
        first = memories[0]
        content = first.content
        
        # 截取前 200 字
        if len(content) > 200:
            content = content[:200] + "..."
        
        return content
    
    def _generate_report(
        self,
        processed_memories: list[MemoryEntry],
        new_principles: list[MemoryEntry],
    ) -> dict[str, Any]:
        """生成冥想报告"""
        # 按类型统计
        by_type: dict[str, int] = {}
        for m in processed_memories:
            t = m.memory_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        # 按标签统计
        by_tag: dict[str, int] = {}
        for m in processed_memories:
            for tag in m.tags:
                by_tag[tag] = by_tag.get(tag, 0) + 1
        
        # 热门标签
        top_tags = sorted(by_tag.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "processed_memories": len(processed_memories),
            "by_type": by_type,
            "top_tags": top_tags,
            "new_principles": len(new_principles),
            "quality_score": self._calculate_quality_score(processed_memories, new_principles),
        }
    
    def _calculate_quality_score(
        self,
        memories: list[MemoryEntry],
        principles: list[MemoryEntry],
    ) -> float:
        """计算记忆质量评分"""
        if not memories:
            return 0.0
        
        # 平均重要性
        avg_importance = sum(m.importance for m in memories) / len(memories)
        
        # 原则密度（每 10 条记忆有多少原则）
        principle_density = len(principles) / max(1, len(memories)) * 10
        
        # 质量评分 = 平均重要性 * 0.7 + 原则密度 * 3
        quality = avg_importance * 0.7 + principle_density * 3
        
        return min(10.0, quality)
    
    def get_pending_count(self) -> int:
        """获取待处理会话数量"""
        return len(self.pending_sessions)
    
    def clear_pending(self) -> None:
        """清空待处理队列"""
        self.pending_sessions.clear()
        logger.info("已清空待处理会话队列")
