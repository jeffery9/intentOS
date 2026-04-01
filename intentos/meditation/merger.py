# -*- coding: utf-8 -*-
"""
IntentOS Memory Merger

记忆合并器 - 识别并合并重复的记忆条目
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher
from typing import Optional

from ..memory.models import MemoryEntry, MemoryContentType, Pattern

logger = logging.getLogger(__name__)


class MemoryMerger:
    """
    记忆合并器
    
    识别并合并相似的记忆条目：
    - 内容相似度检测
    - 标签重叠检测
    - 模式合并
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        初始化合并器
        
        Args:
            similarity_threshold: 相似度阈值 (0-1)，高于此值视为重复
        """
        self.similarity_threshold = similarity_threshold
        logger.info(f"记忆合并器初始化完成 (threshold={similarity_threshold})")
    
    def merge_duplicates(
        self,
        memories: list[MemoryEntry],
    ) -> tuple[list[MemoryEntry], int]:
        """
        合并重复记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            (合并后的记忆列表，合并的数量)
        """
        if len(memories) < 2:
            return memories, 0
        
        # 按类型分组
        by_type: dict[MemoryContentType, list[MemoryEntry]] = {}
        for memory in memories:
            if memory.memory_type not in by_type:
                by_type[memory.memory_type] = []
            by_type[memory.memory_type].append(memory)
        
        # 组合并
        merged_all = []
        total_merged = 0
        
        for mem_type, type_memories in by_type.items():
            merged, count = self._merge_by_type(type_memories)
            merged_all.extend(merged)
            total_merged += count
        
        logger.info(f"合并完成：共合并 {total_merged} 条重复记忆")
        return merged_all, total_merged
    
    def _merge_by_type(
        self,
        memories: list[MemoryEntry],
    ) -> tuple[list[MemoryEntry], int]:
        """按类型合并记忆"""
        if len(memories) < 2:
            return memories, 0
        
        merged = []
        merged_count = 0
        used = set()  # 已处理的记忆索引
        
        for i, mem1 in enumerate(memories):
            if i in used:
                continue
            
            # 查找与当前记忆相似的其他记忆
            similar = [mem1]
            similar_indices = {i}
            
            for j, mem2 in enumerate(memories):
                if j <= i or j in used:
                    continue
                
                similarity = self._calculate_similarity(mem1, mem2)
                if similarity >= self.similarity_threshold:
                    similar.append(mem2)
                    similar_indices.add(j)
            
            # 标记为已使用
            used.update(similar_indices)
            
            # 合并相似记忆
            if len(similar) > 1:
                merged_mem = self._merge_memories(similar)
                merged.append(merged_mem)
                merged_count += len(similar) - 1  # 合并减少的数量
                logger.debug(f"合并了 {len(similar)} 条相似记忆")
            else:
                merged.append(mem1)
        
        return merged, merged_count
    
    def _calculate_similarity(
        self,
        mem1: MemoryEntry,
        mem2: MemoryEntry,
    ) -> float:
        """
        计算两个记忆的相似度
        
        考虑因素：
        - 内容相似度
        - 标签重叠度
        - 模式相似度
        """
        # 1. 内容相似度
        content_sim = SequenceMatcher(
            None,
            mem1.content.lower(),
            mem2.content.lower(),
        ).ratio()
        
        # 2. 标签重叠度
        tags1 = set(mem1.tags)
        tags2 = set(mem2.tags)
        if tags1 and tags2:
            tag_overlap = len(tags1 & tags2) / len(tags1 | tags2)
        else:
            tag_overlap = 0.0
        
        # 3. 模式相似度
        pattern_names1 = {p.name for p in mem1.patterns}
        pattern_names2 = {p.name for p in mem2.patterns}
        if pattern_names1 and pattern_names2:
            pattern_sim = len(pattern_names1 & pattern_names2) / len(pattern_names1 | pattern_names2)
        else:
            pattern_sim = 0.0
        
        # 加权平均
        # 内容权重 0.6, 标签权重 0.2, 模式权重 0.2
        similarity = (
            content_sim * 0.6 +
            tag_overlap * 0.2 +
            pattern_sim * 0.2
        )
        
        return similarity
    
    def _merge_memories(self, memories: list[MemoryEntry]) -> MemoryEntry:
        """
        合并多个记忆为一个
        
        策略：
        - 内容：保留最长的，并追加其他内容的关键部分
        - 标签：合并所有标签
        - 模式：合并所有模式
        - 重要性：取平均值 + 额外奖励（因为代表多次经验）
        - 上下文：合并元数据
        """
        if len(memories) == 1:
            return memories[0]
        
        # 1. 内容合并 - 取最长的作为基础
        base = max(memories, key=lambda m: len(m.content))
        other_contents = [m.content for m in memories if m != base and len(m.content) > 20]
        
        if other_contents:
            merged_content = base.content
            # 追加其他内容（限制总长度）
            for content in other_contents[:3]:
                if content not in merged_content:
                    merged_content += f"\n\n相关经验：{content}"
                    if len(merged_content) > 2000:
                        break
        else:
            merged_content = base.content
        
        # 2. 标签合并
        all_tags = set()
        for m in memories:
            all_tags.update(m.tags)
        
        # 3. 模式合并
        all_patterns: dict[str, Pattern] = {}
        for m in memories:
            for p in m.patterns:
                if p.name in all_patterns:
                    # 合并相同模式
                    existing = all_patterns[p.name]
                    existing.occurrences += p.occurrences
                    existing.confidence = max(existing.confidence, p.confidence)
                else:
                    all_patterns[p.name] = p
        
        # 4. 重要性 - 平均值 + 奖励
        avg_importance = sum(m.importance for m in memories) / len(memories)
        bonus = min(2.0, len(memories) * 0.3)  # 最多奖励 2 分
        merged_importance = min(10.0, avg_importance + bonus)
        
        # 5. 上下文合并
        merged_context = {}
        for m in memories:
            for k, v in m.context.items():
                if k not in merged_context:
                    merged_context[k] = v
                elif isinstance(v, (int, float)):
                    # 数值类型累加或平均
                    if "count" in k.lower() or "total" in k.lower():
                        merged_context[k] += v
                    else:
                        merged_context[k] = (merged_context[k] + v) / 2
        
        # 创建合并后的记忆
        merged = MemoryEntry(
            id=base.id,  # 保留第一条的 ID
            session_id=base.session_id,
            memory_type=base.memory_type,
            content=merged_content,
            metadata={
                **base.metadata,
                "merged_from": len(memories),
                "merged_at": base.timestamp.isoformat(),
            },
            patterns=list(all_patterns.values()),
            context=merged_context,
            tags=list(all_tags),
            importance=merged_importance,
        )
        
        return merged
    
    def find_similar(
        self,
        target: MemoryEntry,
        candidates: list[MemoryEntry],
        limit: int = 5,
    ) -> list[tuple[MemoryEntry, float]]:
        """
        查找与目标记忆相似的记忆
        
        Returns:
            [(记忆，相似度), ...] 按相似度降序
        """
        results = []
        
        for candidate in candidates:
            similarity = self._calculate_similarity(target, candidate)
            if similarity > 0.5:  # 只返回有一定相似度的
                results.append((candidate, similarity))
        
        # 按相似度降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
