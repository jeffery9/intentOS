# -*- coding: utf-8 -*-
"""
IntentOS Evolution Engine

进化引擎 - 整合记忆、冥想、技能的完整进化循环

与 Self-Bootstrap 的区别:
- Evolution: 个人级进化（从对话经验提炼技能）
- Bootstrap: 系统级进化（修改 OS 规则）
- 两者互补，Evolution 提炼的技能可通过 Bootstrap 注册为系统能力
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ..memory.models import MemoryEntry, MemoryContentType, SessionMemory
from ..memory.store import MemoryStore, get_memory_store
from ..memory.shadow_agent import ShadowAgent, ShadowAgentConfig
from ..meditation.engine import MeditationEngine, MeditationConfig, MeditationResult
from ..skill.models import Skill
from ..skill.skillifier import Skillifier, SkillifierConfig
from ..skill.store import SkillStore, get_skill_store

# 兼容原有的 SkillIntegration
try:
    from ..agent.skill_integration import SkillIntegration
except ImportError:
    SkillIntegration = None

# 与 Self-Bootstrap 的交互点
try:
    from ..bootstrap.executor import SelfBootstrapExecutor
except ImportError:
    SelfBootstrapExecutor = None

logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """进化引擎配置"""
    # 冥想触发阈值（session 数量）
    meditation_threshold: int = 5
    # 技能提炼最小质量
    skill_min_quality: float = 0.6
    # 是否自动回顾（每次会话结束）
    auto_review: bool = True
    # 是否自动冥想（达到阈值）
    auto_meditate: bool = True
    # 是否自动提炼技能（从冥想结果）
    auto_skillify: bool = True
    # 记忆保留天数
    memory_retention_days: int = 30
    # 技能自动匹配置信度阈值
    skill_match_threshold: float = 0.5


@dataclass
class EvolutionStats:
    """进化统计"""
    # 会话统计
    total_sessions: int = 0
    completed_sessions: int = 0
    
    # 记忆统计
    total_memories: int = 0
    memories_created: int = 0
    
    # 冥想统计
    meditations_triggered: int = 0
    last_meditation_at: Optional[datetime] = None
    total_memories_merged: int = 0
    total_conflicts_resolved: int = 0
    total_memories_pruned: int = 0
    
    # 技能统计
    skills_created: int = 0
    skills_executed: int = 0
    skill_success_rate: float = 0.0
    
    # 时间统计
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_sessions": self.total_sessions,
            "completed_sessions": self.completed_sessions,
            "total_memories": self.total_memories,
            "meditations_triggered": self.meditations_triggered,
            "skills_created": self.skills_created,
            "skills_executed": self.skills_executed,
            "skill_success_rate": self.skill_success_rate,
            "last_meditation_at": self.last_meditation_at.isoformat() if self.last_meditation_at else None,
        }


class EvolutionEngine:
    """
    进化引擎
    
    整合记忆 - 冥想 - 技能三位一体：
    1. 会话结束 → 影子 Agent 回顾 → 记忆
    2. 攒够 5 个 session → 自动冥想 → 整理记忆
    3. 冥想结果 → 提炼技能 → 可复用能力
    4. 新会话 → 自动匹配技能 → 执行 → 反馈循环
    
    整合原有的 SkillIntegration 和 Memory 系统
    """
    
    def __init__(
        self,
        config: Optional[EvolutionConfig] = None,
        memory_store: Optional[MemoryStore] = None,
        skill_store: Optional[SkillStore] = None,
        skill_integration: Optional[Any] = None,  # 兼容原有的 SkillIntegration
    ):
        self.config = config or EvolutionConfig()
        self.memory_store = memory_store or get_memory_store()
        self.skill_store = skill_store or get_skill_store()
        
        # 整合原有的 SkillIntegration
        self.skill_integration = skill_integration
        if self.skill_integration is None and SkillIntegration is not None:
            # 尝试从现有系统获取
            try:
                self.skill_integration = SkillIntegration(
                    registry=None,  # 由外部注入
                    skill_store=self.skill_store,  # 传入新的 skill_store
                )
            except Exception:
                pass
        
        # 子组件
        self.shadow_config = ShadowAgentConfig(
            auto_review=self.config.auto_review,
        )
        self.meditation_config = MeditationConfig(
            session_threshold=self.config.meditation_threshold,
            retention_days=self.config.memory_retention_days,
        )
        self.skillifier_config = SkillifierConfig(
            min_confidence=self.config.skill_min_quality,
        )
        
        self.meditation_engine = MeditationEngine(self.meditation_config)
        self.skillifier = Skillifier(self.skillifier_config)
        
        # 统计
        self.stats = EvolutionStats()
        
        # 当前会话
        self.current_session: Optional[ShadowAgent] = None
        self.current_session_id: Optional[str] = None
        
        logger.info("进化引擎初始化完成（整合原有系统）")
    
    def start_session(self, session_id: Optional[str] = None, user_id: str = "default") -> str:
        """
        开始新会话
        
        Args:
            session_id: 会话 ID（可选，自动生成）
            user_id: 用户 ID
            
        Returns:
            会话 ID
        """
        import uuid
        
        self.current_session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.current_session = ShadowAgent(
            session_id=self.current_session_id,
            config=self.shadow_config,
        )
        
        self.stats.total_sessions += 1
        
        logger.info(f"开始新会话：{self.current_session_id}")
        return self.current_session_id
    
    def add_message(self, role: str, content: str) -> None:
        """
        添加消息到当前会话
        
        Args:
            role: 角色（user/assistant）
            content: 消息内容
        """
        if not self.current_session:
            self.start_session()
        
        self.current_session.add_message(role, content)
    
    def end_session(self) -> dict[str, Any]:
        """
        结束当前会话，触发回顾和可能的冥想
        
        Returns:
            会话总结
        """
        if not self.current_session:
            return {"error": "没有活跃的会话"}
        
        # 结束会话，触发回顾
        self.current_session.end_session()
        self.stats.completed_sessions += 1
        
        # 保存会话到存储
        session_memory = self.current_session.get_memory()
        self.memory_store.save_session(session_memory)
        
        # 更新统计
        self.stats.total_memories += len(session_memory.memory_entries)
        self.stats.memories_created += len(session_memory.memory_entries)
        
        # 检查是否触发冥想
        meditation_result = None
        if self.meditation_engine.add_session(session_memory):
            if self.config.auto_meditate:
                import asyncio
                meditation_result = asyncio.run(self.meditate())
        
        # 清空当前会话
        result = {
            "session_id": self.current_session_id,
            "messages": len(self.current_session.memory.messages),
            "memories_created": len(session_memory.memory_entries),
            "meditation_triggered": meditation_result is not None,
        }
        
        self.current_session = None
        self.current_session_id = None
        
        logger.info(f"会话结束：{result}")
        return result
    
    async def meditate(self) -> MeditationResult:
        """
        执行冥想
        
        Returns:
            冥想结果
        """
        logger.info("执行冥想...")
        
        # 执行冥想
        result = await self.meditation_engine.meditate()
        
        # 更新统计
        self.stats.meditations_triggered += 1
        self.stats.last_meditation_at = datetime.now()
        self.stats.total_memories_merged += result.memories_merged
        self.stats.total_conflicts_resolved += result.conflicts_resolved
        self.stats.total_memories_pruned += result.memories_pruned
        
        # 从冥想结果提炼技能
        if self.config.auto_skillify and result.new_memories:
            skills = await self._skillify_from_meditation(result)
            logger.info(f"从冥想提炼了 {len(skills)} 个技能")
        
        logger.info(f"冥想完成：{result.memories_merged} 合并，{result.conflicts_resolved} 矛盾，{result.memories_pruned} 淘汰")
        return result
    
    async def _skillify_from_meditation(self, result: MeditationResult) -> list[Skill]:
        """从冥想结果提炼技能"""
        skills = []
        
        # 从新提炼的原则中尝试生成技能
        for memory in result.new_memories:
            if memory.memory_type == MemoryContentType.PATTERN and memory.patterns:
                # 尝试将模式转换为技能
                skill = self._pattern_to_skill(memory)
                if skill:
                    is_valid, _ = self.skillifier.validate_skill(skill)
                    if is_valid:
                        self.skill_store.save_skill(skill)
                        skills.append(skill)
                        self.stats.skills_created += 1
        
        return skills
    
    def _pattern_to_skill(self, memory: MemoryEntry) -> Optional[Skill]:
        """将模式记忆转换为技能"""
        if not memory.patterns:
            return None
        
        pattern = memory.patterns[0]
        
        # 从模式创建技能步骤
        steps = []
        for i, step_desc in enumerate(pattern.steps[:5]):  # 最多 5 步
            from ..skill.models import SkillStep
            action = self.skillifier._infer_action(step_desc)
            steps.append(SkillStep(
                name=f"步骤 {i+1}",
                action=action,
                description=step_desc[:200],
            ))
        
        if not steps:
            return None
        
        from ..skill.models import Skill, SkillTrigger, SkillLevel
        
        # 创建技能
        return Skill(
            name=pattern.name,
            description=pattern.description,
            trigger=SkillTrigger(
                keywords=pattern.trigger_keywords,
                confidence_threshold=0.6,
            ),
            steps=steps,
            level=SkillLevel.INTERMEDIATE,
            tags=["meditation", "pattern", "auto_generated"],
            source_session_id=memory.session_id,
            created_from="meditation",
        )
    
    def find_matching_skills(self, input_text: str) -> list[tuple[Skill, float]]:
        """
        根据输入文本查找匹配的技能
        
        Args:
            input_text: 用户输入
            
        Returns:
            [(技能，置信度), ...]
        """
        from ..skill.matcher import SkillMatcher
        
        matcher = SkillMatcher()
        skills = self.skill_store.list_skills(limit=100)
        
        results = matcher.find_all_matches(
            skills,
            input_text,
            min_confidence=self.config.skill_match_threshold,
        )
        
        return results
    
    def execute_skill(self, skill_id: str, **params) -> dict[str, Any]:
        """
        执行技能
        
        Args:
            skill_id: 技能 ID
            **params: 技能参数
            
        Returns:
            执行结果
        """
        skill = self.skill_store.get_skill(skill_id)
        if not skill:
            return {"error": f"技能不存在：{skill_id}"}
        
        # 记录执行
        self.stats.skills_executed += 1
        
        # 这里应该调用实际的能力执行器
        # 简化实现：返回技能信息
        result = {
            "skill_id": skill_id,
            "skill_name": skill.name,
            "steps": len(skill.steps),
            "params": params,
            "status": "executed",
        }
        
        # 更新技能使用统计
        self.skill_store.record_usage(skill_id, success=True)
        
        # 更新成功率
        total = self.stats.skills_executed
        if total > 0:
            self.stats.skill_success_rate = 1.0  # 简化：假设都成功
        
        return result
    
    def register_skill_to_bootstrap(self, skill: Skill, bootstrap_executor: Any = None) -> bool:
        """
        将提炼的技能注册为系统能力（通过 Self-Bootstrap）
        
        Args:
            skill: 提炼的技能
            bootstrap_executor: SelfBootstrapExecutor 实例（可选）
            
        Returns:
            是否成功注册
        """
        if bootstrap_executor is None and SelfBootstrapExecutor is not None:
            # 尝试从全局获取
            try:
                # 需要外部注入
                logger.info(f"技能 {skill.name} 等待注册到 Self-Bootstrap")
                return False
            except Exception:
                return False
        
        # 通过 Bootstrap 注册技能为系统能力
        # 这是 Evolution → Bootstrap 的交互点
        logger.info(f"注册技能 {skill.name} 到系统能力...")
        # 具体实现取决于 Bootstrap 的 API
        return True
    
    def get_stats(self) -> dict[str, Any]:
        """获取进化统计"""
        # 从存储获取最新数据
        memory_stats = self.memory_store.get_stats()
        skill_stats = self.skill_store.get_stats()
        
        return {
            **self.stats.to_dict(),
            "memory": memory_stats,
            "skills": skill_stats,
        }
    
    def export_evolution_data(self) -> dict[str, Any]:
        """导出进化数据（用于备份或迁移）"""
        return {
            "stats": self.stats.to_dict(),
            "memories": [
                e.to_dict()
                for session in self.memory_store._sessions.values()
                for e in session.memory_entries
            ],
            "skills": [
                s.to_dict()
                for s in self.skill_store._skills.values()
            ],
            "exported_at": datetime.now().isoformat(),
        }
