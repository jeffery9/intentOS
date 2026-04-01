# -*- coding: utf-8 -*-
"""
IntentOS Skill Matcher

技能匹配器 - 根据输入文本匹配最相关的技能
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import Optional

from .models import Skill, SkillTrigger

logger = logging.getLogger(__name__)


class SkillMatcher:
    """
    技能匹配器
    
    根据用户输入匹配最相关的技能：
    - 关键词匹配
    - 意图模式匹配
    - 语义相似度
    """
    
    def __init__(self):
        logger.info("技能匹配器初始化完成")
    
    def match(self, skill: Skill, input_text: str) -> float:
        """
        匹配技能与输入文本
        
        Args:
            skill: 技能
            input_text: 用户输入文本
            
        Returns:
            置信度 (0-1)
        """
        trigger = skill.trigger
        confidence = 0.0
        
        # 1. 关键词匹配
        keyword_score = self._match_keywords(trigger, input_text)
        confidence = max(confidence, keyword_score * 0.5)
        
        # 2. 意图模式匹配
        pattern_score = self._match_intent_pattern(trigger, input_text)
        confidence = max(confidence, pattern_score * 0.7)
        
        # 3. 步骤内容匹配
        step_score = self._match_steps(skill, input_text)
        confidence = max(confidence, step_score * 0.4)
        
        # 4. 标签匹配
        tag_score = self._match_tags(skill, input_text)
        confidence = max(confidence, tag_score * 0.3)
        
        # 应用置信度阈值
        if confidence < trigger.confidence_threshold:
            return 0.0
        
        return min(1.0, confidence)
    
    def _match_keywords(self, trigger: SkillTrigger, input_text: str) -> float:
        """关键词匹配"""
        if not trigger.keywords:
            return 0.0
        
        input_lower = input_text.lower()
        matched = sum(1 for kw in trigger.keywords if kw.lower() in input_lower)
        
        return matched / len(trigger.keywords)
    
    def _match_intent_pattern(
        self,
        trigger: SkillTrigger,
        input_text: str,
    ) -> float:
        """意图模式匹配"""
        if not trigger.intent_pattern:
            return 0.0
        
        try:
            if re.search(trigger.intent_pattern, input_text, re.IGNORECASE):
                return 1.0
        except re.error:
            logger.warning(f"无效的正则表达式：{trigger.intent_pattern}")
        
        return 0.0
    
    def _match_steps(self, skill: Skill, input_text: str) -> float:
        """步骤内容匹配"""
        if not skill.steps:
            return 0.0
        
        # 组合所有步骤描述
        steps_text = " ".join([s.description for s in skill.steps])
        
        # 计算相似度
        similarity = SequenceMatcher(
            None,
            steps_text.lower(),
            input_text.lower(),
        ).ratio()
        
        return similarity
    
    def _match_tags(self, skill: Skill, input_text: str) -> float:
        """标签匹配"""
        if not skill.tags:
            return 0.0
        
        input_lower = input_text.lower()
        matched = sum(1 for tag in skill.tags if tag.lower() in input_lower)
        
        return matched / len(skill.tags)
    
    def find_best_match(
        self,
        skills: list[Skill],
        input_text: str,
        min_confidence: float = 0.5,
    ) -> Optional[tuple[Skill, float]]:
        """
        查找最佳匹配的技能
        
        Args:
            skills: 技能列表
            input_text: 用户输入
            min_confidence: 最小置信度
            
        Returns:
            (最佳匹配技能，置信度) 或 None
        """
        best_skill = None
        best_confidence = 0.0
        
        for skill in skills:
            confidence = self.match(skill, input_text)
            
            if confidence > best_confidence and confidence >= min_confidence:
                best_skill = skill
                best_confidence = confidence
        
        if best_skill:
            return (best_skill, best_confidence)
        
        return None
    
    def find_all_matches(
        self,
        skills: list[Skill],
        input_text: str,
        min_confidence: float = 0.3,
    ) -> list[tuple[Skill, float]]:
        """
        查找所有匹配的技能
        
        Returns:
            [(技能，置信度), ...] 按置信度降序
        """
        results = []
        
        for skill in skills:
            confidence = self.match(skill, input_text)
            
            if confidence >= min_confidence:
                results.append((skill, confidence))
        
        # 按置信度降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
