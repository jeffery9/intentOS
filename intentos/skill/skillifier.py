# -*- coding: utf-8 -*-
"""
IntentOS Skillifier

技能提炼器 - 将工作流自动提炼为可复用技能
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from ..memory.models import MemoryEntry, MemoryContentType, SessionMemory
from .models import (
    Skill,
    SkillParam,
    SkillStep,
    SkillTrigger,
    Workflow,
    SkillLevel,
)

logger = logging.getLogger(__name__)


class SkillifierConfig:
    """技能提炼器配置"""
    
    def __init__(
        self,
        min_steps: int = 2,          # 最少步骤数
        max_steps: int = 10,         # 最多步骤数
        min_confidence: float = 0.6, # 最小置信度
        auto_parametrize: bool = True, # 自动参数化
    ):
        self.min_steps = min_steps
        self.max_steps = max_steps
        self.min_confidence = min_confidence
        self.auto_parametrize = auto_parametrize


class Skillifier:
    """
    技能提炼器
    
    将完整的工作流自动提炼为可复用的技能文件。
    支持：
    - 从会话记忆提取工作流
    - 自动参数化
    - 触发器生成
    - 技能质量评估
    """
    
    def __init__(self, config: Optional[SkillifierConfig] = None):
        self.config = config or SkillifierConfig()
        logger.info("技能提炼器初始化完成")
    
    async def skillify(
        self,
        session_id: str,
        memories: list[MemoryEntry],
    ) -> Optional[Skill]:
        """
        将 session 提炼为技能
        
        Args:
            session_id: 会话 ID
            memories: 会话记忆列表
            
        Returns:
            提炼的技能，如果无法提炼则返回 None
        """
        logger.info(f"开始提炼会话 {session_id} 为技能")
        
        # 1. 提取工作流
        workflow = self._extract_workflow(session_id, memories)
        
        if not workflow or len(workflow.steps) < self.config.min_steps:
            logger.info(f"会话 {session_id} 无法提炼为技能（步骤不足）")
            return None
        
        # 2. 抽象为通用模式（参数化）
        if self.config.auto_parametrize:
            workflow = self._abstract_workflow(workflow)
        
        # 3. 生成触发器
        trigger = self._generate_trigger(workflow, memories)
        
        # 4. 生成技能
        skill = self._generate_skill(workflow, trigger, session_id)
        
        # 5. 质量评估
        quality_score = self._evaluate_skill_quality(skill)
        skill.success_rate = quality_score
        
        if quality_score < self.config.min_confidence:
            logger.info(f"技能质量不足 ({quality_score})，放弃提炼")
            return None
        
        logger.info(f"成功提炼技能：{skill.name} (质量：{quality_score:.2f})")
        return skill
    
    def _extract_workflow(
        self,
        session_id: str,
        memories: list[MemoryEntry],
    ) -> Optional[Workflow]:
        """从会话记忆提取工作流"""
        # 查找包含模式/步骤的记忆
        workflow_steps = []
        
        for memory in memories:
            # 从模式中提取步骤
            for pattern in memory.patterns:
                if pattern.steps:
                    for i, step_desc in enumerate(pattern.steps):
                        step = self._parse_step_description(step_desc, i)
                        if step:
                            workflow_steps.append(step)
            
            # 从成功/失败经验中提取
            if memory.memory_type in (MemoryContentType.SUCCESS, MemoryContentType.FAILURE):
                step = self._extract_step_from_experience(memory)
                if step:
                    workflow_steps.append(step)
        
        if not workflow_steps:
            return None
        
        # 创建工组流
        workflow = Workflow(
            name=self._infer_workflow_name(workflow_steps),
            description=self._infer_workflow_description(workflow_steps),
            steps=workflow_steps[:self.config.max_steps],
            source_session_id=session_id,
        )
        
        return workflow
    
    def _parse_step_description(
        self,
        description: str,
        index: int,
    ) -> Optional[SkillStep]:
        """解析步骤描述为 SkillStep"""
        # 尝试识别动作类型
        action = self._infer_action(description)
        
        # 提取参数
        params = self._extract_params_from_step(description)
        
        return SkillStep(
            name=f"步骤 {index + 1}",
            action=action,
            description=description.strip()[:200],
            params=params,
        )
    
    def _infer_action(self, description: str) -> str:
        """从描述推断动作类型"""
        desc_lower = description.lower()
        
        action_keywords = {
            "query": ["查询", "获取", "查找", "搜索", "query", "get", "search"],
            "execute": ["执行", "运行", "调用", "启动", "execute", "run", "call"],
            "analyze": ["分析", "评估", "检查", "诊断", "analyze", "check"],
            "generate": ["生成", "创建", "构建", "编写", "generate", "create", "write"],
            "modify": ["修改", "更新", "更改", "调整", "modify", "update", "change"],
            "delete": ["删除", "移除", "清理", "delete", "remove", "clean"],
        }
        
        for action, keywords in action_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                return action
        
        return "execute"  # 默认动作
    
    def _extract_params_from_step(self, description: str) -> dict[str, Any]:
        """从步骤描述提取参数"""
        params = {}
        
        # 提取引号内的值作为参数
        quoted_values = re.findall(r'["\']([^"\']+)["\']', description)
        if quoted_values:
            params["values"] = quoted_values
        
        # 提取变量名（如 ${var} 或 {{var}}）
        variables = re.findall(r'\$\{(\w+)\}|\{\{(\w+)\}\}', description)
        if variables:
            params["variables"] = [v[0] or v[1] for v in variables]
        
        return params
    
    def _extract_step_from_experience(
        self,
        memory: MemoryEntry,
    ) -> Optional[SkillStep]:
        """从经验记忆提取步骤"""
        content = memory.content
        
        if len(content) < 10:
            return None
        
        action = self._infer_action(content)
        
        return SkillStep(
            name=f"{action.title()} 步骤",
            action=action,
            description=content[:200],
            params=self._extract_params_from_step(content),
        )
    
    def _abstract_workflow(self, workflow: Workflow) -> Workflow:
        """抽象工作流为通用模式（参数化）"""
        # 1. 识别具体值，替换为参数
        param_index = 0
        params = []
        
        for step in workflow.steps:
            # 查找可能的具体值
            for key, value in step.params.items():
                if isinstance(value, str) and len(value) < 50:
                    # 可能是具体参数值
                    param_name = f"param_{param_index}"
                    params.append(SkillParam(
                        name=param_name,
                        type="string",
                        description=f"自动提取的参数",
                        required=False,
                    ))
                    step.params[key] = f"${{{param_name}}}"
                    param_index += 1
        
        # 添加工组流参数
        workflow.params.extend(params)
        
        return workflow
    
    def _generate_trigger(
        self,
        workflow: Workflow,
        memories: list[MemoryEntry],
    ) -> SkillTrigger:
        """生成技能触发器"""
        # 从记忆和工组流名称提取关键词
        keywords = []
        
        # 添加工组流名称作为关键词
        name_words = re.findall(r'[\w]+', workflow.name)
        keywords.extend(name_words)
        
        # 从步骤描述提取关键词
        for step in workflow.steps:
            words = re.findall(r'[\u4e00-\u9fa5]{2,}', step.description)
            keywords.extend(words[:3])  # 每个步骤最多 3 个中文词
        
        # 去重
        keywords = list(set(keywords))[:10]
        
        # 生成意图模式
        intent_pattern = self._generate_intent_pattern(workflow.name)
        
        return SkillTrigger(
            keywords=keywords,
            intent_pattern=intent_pattern,
            confidence_threshold=0.6,
        )
    
    def _generate_intent_pattern(self, workflow_name: str) -> str:
        """生成意图匹配模式"""
        # 简单实现：将名称转换为正则模式
        # 例如："数据分析" → ".*分析.*数据.*"
        words = re.findall(r'[\u4e00-\u9fa5]+|[\w]+', workflow_name)
        pattern = ".*".join(words)
        return f".*{pattern}.*"
    
    def _generate_skill(
        self,
        workflow: Workflow,
        trigger: SkillTrigger,
        session_id: str,
    ) -> Skill:
        """生成技能"""
        return Skill(
            name=workflow.name,
            description=workflow.description,
            trigger=trigger,
            steps=workflow.steps,
            params=workflow.params,
            source_workflow_id=workflow.id,
            source_session_id=session_id,
            created_from="skillify",
            tags=self._generate_tags(workflow),
        )
    
    def _infer_workflow_name(self, steps: list[SkillStep]) -> str:
        """推断工作流名称"""
        if not steps:
            return "未命名工作流"
        
        # 从第一步和最后一步推断
        first_action = steps[0].action
        last_action = steps[-1].action if len(steps) > 1 else None
        
        # 简单命名
        if last_action:
            return f"{first_action.title()} 到 {last_action.title()} 工作流"
        return f"{first_action.title()} 工作流"
    
    def _infer_workflow_description(self, steps: list[SkillStep]) -> str:
        """推断工作流描述"""
        if not steps:
            return ""
        
        # 组合步骤描述
        descriptions = [s.description for s in steps if s.description]
        return " → ".join(descriptions[:3])  # 最多 3 步
    
    def _generate_tags(self, workflow: Workflow) -> list[str]:
        """生成技能标签"""
        tags = set()
        
        # 从动作类型添加标签
        for step in workflow.steps:
            tags.add(step.action)
        
        # 从名称添加标签
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', workflow.name)
        tags.update(words)
        
        # 添加 skillify 标签
        tags.add("skillify")
        tags.add("auto_generated")
        
        return list(tags)[:10]
    
    def _evaluate_skill_quality(self, skill: Skill) -> float:
        """
        评估技能质量
        
        评分标准：
        - 步骤数量适中 (0.3)
        - 有明确的触发器 (0.2)
        - 有参数定义 (0.2)
        - 步骤描述清晰 (0.3)
        """
        score = 0.0
        
        # 步骤数量评分
        step_count = len(skill.steps)
        if 2 <= step_count <= 10:
            score += 0.3
        elif step_count > 1:
            score += 0.15
        
        # 触发器评分
        if skill.trigger.keywords or skill.trigger.intent_pattern:
            score += 0.2
        
        # 参数评分
        if skill.params:
            score += 0.2
        
        # 步骤描述清晰度评分
        clear_steps = sum(1 for s in skill.steps if len(s.description) >= 10)
        if clear_steps >= len(skill.steps) * 0.8:
            score += 0.3
        elif clear_steps >= len(skill.steps) * 0.5:
            score += 0.15
        
        return min(1.0, score)
    
    def validate_skill(self, skill: Skill) -> tuple[bool, list[str]]:
        """
        验证技能有效性
        
        Returns:
            (是否有效，问题列表)
        """
        issues = []
        
        # 检查步骤数量
        if len(skill.steps) < 1:
            issues.append("技能至少需要 1 个步骤")
        if len(skill.steps) > self.config.max_steps:
            issues.append(f"技能步骤不能超过 {self.config.max_steps} 个")
        
        # 检查触发器
        if not skill.trigger.keywords and not skill.trigger.intent_pattern:
            issues.append("技能需要至少一个触发器（关键词或意图模式）")
        
        # 检查步骤完整性
        for i, step in enumerate(skill.steps):
            if not step.name:
                issues.append(f"步骤 {i+1} 缺少名称")
            if not step.action:
                issues.append(f"步骤 {i+1} 缺少动作类型")
        
        return len(issues) == 0, issues
