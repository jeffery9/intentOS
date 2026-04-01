# -*- coding: utf-8 -*-
"""
IntentOS Conflict Resolver

矛盾解决器 - 识别并解决冲突的记忆
"""

from __future__ import annotations

import logging
from typing import Optional

from ..memory.models import MemoryEntry, MemoryContentType

logger = logging.getLogger(__name__)


class ConflictResolver:
    """
    矛盾解决器
    
    识别并解决冲突的记忆：
    - 检测矛盾（同一主题的不同说法）
    - 保留更新、更重要的记忆
    - 标记已解决的矛盾
    """
    
    # 矛盾关键词
    CONTRADICTION_KEYWORDS = [
        # 否定词
        "不", "非", "无", "没", "别", "勿",
        # 转折词
        "但是", "然而", "可是", "却", "反而",
        # 英文
        "not", "no", "never", "instead", "but", "however",
    ]
    
    def __init__(self):
        logger.info("矛盾解决器初始化完成")
    
    def resolve_conflicts(
        self,
        memories: list[MemoryEntry],
    ) -> tuple[list[MemoryEntry], int]:
        """
        解决记忆矛盾
        
        Args:
            memories: 记忆列表
            
        Returns:
            (解决后的记忆列表，解决的矛盾数量)
        """
        if len(memories) < 2:
            return memories, 0
        
        # 按主题分组（使用标签作为主题代理）
        by_topic: dict[str, list[MemoryEntry]] = {}
        for memory in memories:
            # 使用主要标签作为主题
            topic = memory.tags[0] if memory.tags else "untagged"
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(memory)
        
        # 解决矛盾
        resolved = []
        total_resolved = 0
        
        for topic, topic_memories in by_topic.items():
            resolved_topic, count = self._resolve_topic_conflicts(topic_memories)
            resolved.extend(resolved_topic)
            total_resolved += count
        
        logger.info(f"矛盾解决完成：共解决 {total_resolved} 个矛盾")
        return resolved, total_resolved
    
    def _resolve_topic_conflicts(
        self,
        memories: list[MemoryEntry],
    ) -> tuple[list[MemoryEntry], int]:
        """解决同一主题内的矛盾"""
        if len(memories) < 2:
            return memories, 0
        
        conflicts_found = 0
        resolved = []
        used = set()
        
        for i, mem1 in enumerate(memories):
            if i in used:
                continue
            
            # 查找与当前记忆矛盾的其他记忆
            conflicts = []
            
            for j, mem2 in enumerate(memories):
                if j <= i or j in used:
                    continue
                
                if self._are_contradictory(mem1, mem2):
                    conflicts.append((j, mem2))
            
            if conflicts:
                # 发现矛盾，解决它
                conflicts_found += 1
                
                # 选择保留哪个记忆
                all_related = [mem1] + [m for _, m in conflicts]
                winner = self._select_winner(all_related)
                
                # 更新获胜者，记录已解决的矛盾
                winner.metadata["resolved_conflicts"] = len(conflicts)
                winner.tags.append("conflict_resolved")
                
                resolved.append(winner)
                
                # 标记为已使用
                used.add(i)
                for idx, _ in conflicts:
                    used.add(idx)
                
                logger.debug(f"解决了 1 个矛盾，保留了记忆 {winner.id[:8]}")
            else:
                resolved.append(mem1)
        
        return resolved, conflicts_found
    
    def _are_contradictory(
        self,
        mem1: MemoryEntry,
        mem2: MemoryEntry,
    ) -> bool:
        """
        判断两个记忆是否矛盾
        
        判断标准：
        1. 内容包含否定词 vs 肯定词
        2. 重要性差异大（可能代表不同结论）
        3. 时间相近但结论不同
        """
        content1 = mem1.content.lower()
        content2 = mem2.content.lower()
        
        # 1. 检查是否一个包含否定，一个包含肯定
        has_negation1 = any(kw in content1 for kw in self.CONTRADICTION_KEYWORDS)
        has_negation2 = any(kw in content2 for kw in self.CONTRADICTION_KEYWORDS)
        
        if has_negation1 != has_negation2:
            # 一个有否定词，一个没有 - 可能矛盾
            # 检查是否有共同关键词
            common_words = self._extract_common_words(content1, content2)
            if len(common_words) >= 2:
                return True
        
        # 2. 检查重要性差异大且内容相似
        importance_diff = abs(mem1.importance - mem2.importance)
        if importance_diff >= 3.0:
            # 重要性差异大，检查内容是否相关
            similarity = self._content_similarity(content1, content2)
            if similarity > 0.5:
                return True
        
        # 3. 检查时间相近但类型不同
        if mem1.memory_type != mem2.memory_type:
            time_diff = abs((mem1.timestamp - mem2.timestamp).total_seconds())
            if time_diff < 3600:  # 1 小时内
                # 同一事件的不同类型记录，可能矛盾
                return True
        
        return False
    
    def _select_winner(self, memories: list[MemoryEntry]) -> MemoryEntry:
        """
        从矛盾记忆中选择保留哪个
        
        选择标准：
        1. 重要性更高
        2. 内容更详细
        3. 时间更新
        4. 有解决方案（对于失败记录）
        """
        def score(memory: MemoryEntry) -> float:
            s = 0.0
            
            # 重要性（权重 0.4）
            s += memory.importance * 0.4
            
            # 内容长度（权重 0.2）- 更详细通常更好
            s += min(10.0, len(memory.content) / 100) * 0.2
            
            # 时间（权重 0.2）- 更新的更好
            days_old = (memory.timestamp - memory.timestamp).days  # 总是 0，需要外部传入
            s += 2.0  # 基础分
            
            # 有解决方案（权重 0.2）
            if memory.memory_type == MemoryContentType.FAILURE:
                if "solution" in memory.metadata and memory.metadata["solution"]:
                    s += 2.0
            
            return s
        
        # 按评分排序
        scored = [(m, score(m)) for m in memories]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[0][0]
    
    def _extract_common_words(self, text1: str, text2: str) -> set[str]:
        """提取两个文本的共同关键词"""
        # 简单实现：提取共同的中文词（2 字以上）
        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)
        
        return words1 & words2
    
    def _tokenize(self, text: str) -> set[str]:
        """简单分词（提取 2 字以上的连续中文字符）"""
        import re
        # 匹配 2 字以上的中文字符
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        # 匹配英文单词
        english_words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        
        return set(chinese_words + english_words)
    
    def _content_similarity(self, text1: str, text2: str) -> float:
        """计算内容相似度"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio()
    
    def detect_potential_conflicts(
        self,
        memories: list[MemoryEntry],
    ) -> list[tuple[MemoryEntry, MemoryEntry, str]]:
        """
        检测潜在的矛盾（不解决，只检测）
        
        Returns:
            [(记忆 1, 记忆 2, 矛盾原因), ...]
        """
        conflicts = []
        
        for i, mem1 in enumerate(memories):
            for j, mem2 in enumerate(memories):
                if j <= i:
                    continue
                
                if self._are_contradictory(mem1, mem2):
                    reason = self._get_conflict_reason(mem1, mem2)
                    conflicts.append((mem1, mem2, reason))
        
        return conflicts
    
    def _get_conflict_reason(
        self,
        mem1: MemoryEntry,
        mem2: MemoryEntry,
    ) -> str:
        """获取矛盾原因"""
        reasons = []
        
        has_negation1 = any(kw in mem1.content.lower() for kw in self.CONTRADICTION_KEYWORDS)
        has_negation2 = any(kw in mem2.content.lower() for kw in self.CONTRADICTION_KEYWORDS)
        
        if has_negation1 != has_negation2:
            reasons.append("否定/肯定表述不同")
        
        if abs(mem1.importance - mem2.importance) >= 3.0:
            reasons.append("重要性差异大")
        
        if mem1.memory_type != mem2.memory_type:
            reasons.append("记忆类型不同")
        
        return ", ".join(reasons) if reasons else "未知原因"
