# -*- coding: utf-8 -*-
"""
IntentOS Memory Pruner

记忆剪枝器 - 淘汰过时、低价值的记忆
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from ..memory.models import MemoryEntry, MemoryContentType

logger = logging.getLogger(__name__)


class MemoryPruner:
    """
    记忆剪枝器
    
    淘汰过时记忆的策略：
    1. 时间过期 - 超过保留期的记忆
    2. 重要性不足 - 低于阈值的记忆
    3. 被新信息覆盖 - 有更新版本的旧记忆
    4. 低质量 - 内容空洞、无标签的记忆
    """
    
    def __init__(
        self,
        retention_days: int = 30,
        min_importance: float = 3.0,
    ):
        """
        初始化剪枝器
        
        Args:
            retention_days: 记忆保留天数
            min_importance: 最小重要性评分
        """
        self.retention_days = retention_days
        self.min_importance = min_importance
        
        logger.info(f"记忆剪枝器初始化完成 (retention={retention_days}d, min_importance={min_importance})")
    
    def prune_outdated(
        self,
        memories: list[MemoryEntry],
    ) -> tuple[list[MemoryEntry], int]:
        """
        淘汰过时记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            (剪枝后的记忆列表，淘汰的数量)
        """
        if not memories:
            return memories, 0
        
        pruned = []
        pruned_count = 0
        now = datetime.now()
        cutoff_date = now - timedelta(days=self.retention_days)
        
        for memory in memories:
            should_prune = False
            reason = ""
            
            # 1. 检查时间过期
            if memory.timestamp < cutoff_date:
                # 过期的记忆，但如果重要性高则保留
                if memory.importance < 7.0:
                    should_prune = True
                    reason = "时间过期"
            
            # 2. 检查重要性不足
            if memory.importance < self.min_importance:
                # 重要性不足的记忆，如果是旧的则淘汰
                if memory.timestamp < cutoff_date:
                    should_prune = True
                    reason = "重要性不足"
            
            # 3. 检查低质量
            if self._is_low_quality(memory):
                should_prune = True
                reason = "低质量"
            
            if should_prune:
                pruned_count += 1
                logger.debug(f"淘汰记忆 {memory.id[:8]}: {reason}")
            else:
                pruned.append(memory)
        
        logger.info(f"剪枝完成：淘汰 {pruned_count} 条记忆")
        return pruned, pruned_count
    
    def _is_low_quality(self, memory: MemoryEntry) -> bool:
        """
        检查记忆是否低质量
        
        低质量标准：
        - 内容太短（< 10 字）
        - 无标签
        - 无模式
        - 内容为空或只有占位符
        """
        # 内容为空
        if not memory.content or not memory.content.strip():
            return True
        
        # 内容太短
        if len(memory.content.strip()) < 10:
            return True
        
        # 只有占位符内容
        placeholders = ["过滤", "暂无", "待补充", "test", "placeholder"]
        if any(p in memory.content for p in placeholders):
            return True
        
        # 无标签且无模式且重要性低
        if not memory.tags and not memory.patterns and memory.importance < 5.0:
            return True
        
        return False
    
    def prune_by_topic(
        self,
        memories: list[MemoryEntry],
        topic: str,
        keep_latest: int = 3,
    ) -> tuple[list[MemoryEntry], int]:
        """
        按主题剪枝，只保留最新的 N 条
        
        Args:
            memories: 记忆列表
            topic: 主题（标签）
            keep_latest: 保留最新的数量
            
        Returns:
            (剪枝后的记忆列表，淘汰的数量)
        """
        # 筛选出该主题的记忆
        topic_memories = [m for m in memories if topic in m.tags]
        other_memories = [m for m in memories if topic not in m.tags]
        
        if len(topic_memories) <= keep_latest:
            return memories, 0
        
        # 按时间排序，保留最新的
        topic_memories.sort(key=lambda m: m.timestamp, reverse=True)
        kept = topic_memories[:keep_latest]
        pruned_count = len(topic_memories) - keep_latest
        
        logger.info(f"主题 '{topic}' 剪枝：保留 {len(kept)} 条，淘汰 {pruned_count} 条")
        
        return other_memories + kept, pruned_count
    
    def prune_similar(
        self,
        memories: list[MemoryEntry],
        similarity_threshold: float = 0.9,
    ) -> tuple[list[MemoryEntry], int]:
        """
        剪除过于相似的重复记忆
        
        Args:
            memories: 记忆列表
            similarity_threshold: 相似度阈值
            
        Returns:
            (剪枝后的记忆列表，淘汰的数量)
        """
        if len(memories) < 2:
            return memories, 0
        
        from difflib import SequenceMatcher
        
        pruned = []
        pruned_count = 0
        used = set()
        
        for i, mem1 in enumerate(memories):
            if i in used:
                continue
            
            # 查找与当前记忆过于相似的其他记忆
            similar_indices = [i]
            
            for j, mem2 in enumerate(memories):
                if j <= i or j in used:
                    continue
                
                similarity = SequenceMatcher(
                    None,
                    mem1.content.lower(),
                    mem2.content.lower(),
                ).ratio()
                
                if similarity >= similarity_threshold:
                    similar_indices.append(j)
            
            # 保留最重要的那个
            if len(similar_indices) > 1:
                candidates = [memories[idx] for idx in similar_indices]
                winner = max(candidates, key=lambda m: m.importance)
                pruned.append(winner)
                
                # 标记其他为已使用（淘汰）
                for idx in similar_indices:
                    if memories[idx] != winner:
                        used.add(idx)
                        pruned_count += 1
            else:
                pruned.append(mem1)
        
        logger.info(f"相似记忆剪枝：淘汰 {pruned_count} 条")
        return pruned, pruned_count
    
    def get_prune_candidates(
        self,
        memories: list[MemoryEntry],
    ) -> list[tuple[MemoryEntry, str]]:
        """
        获取可能被淘汰的记忆（不实际淘汰，只列出候选）
        
        Returns:
            [(记忆，原因), ...]
        """
        candidates = []
        now = datetime.now()
        cutoff_date = now - timedelta(days=self.retention_days)
        
        for memory in memories:
            reasons = []
            
            # 检查时间
            if memory.timestamp < cutoff_date:
                days_old = (cutoff_date - memory.timestamp).days
                reasons.append(f"时间过期 ({days_old}天)")
            
            # 检查重要性
            if memory.importance < self.min_importance:
                reasons.append(f"重要性不足 ({memory.importance})")
            
            # 检查质量
            if self._is_low_quality(memory):
                reasons.append("低质量")
            
            if reasons:
                candidates.append((memory, ", ".join(reasons)))
        
        return candidates
    
    def calculate_retention_stats(
        self,
        memories: list[MemoryEntry],
    ) -> dict:
        """计算记忆保留统计"""
        now = datetime.now()
        cutoff_date = now - timedelta(days=self.retention_days)
        
        total = len(memories)
        expired = sum(1 for m in memories if m.timestamp < cutoff_date)
        low_importance = sum(1 for m in memories if m.importance < self.min_importance)
        low_quality = sum(1 for m in memories if self._is_low_quality(m))
        
        # 按类型统计
        by_type = {}
        for m in memories:
            t = m.memory_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total": total,
            "expired": expired,
            "low_importance": low_importance,
            "low_quality": low_quality,
            "by_type": by_type,
            "retention_days": self.retention_days,
            "min_importance": self.min_importance,
        }
