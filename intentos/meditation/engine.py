# -*- coding: utf-8 -*-
"""
IntentOS Meditation Engine

冥想引擎 - 定期整理记忆，防止膨胀
"""

from __future__ import annotations

import logging
import time
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


# =============================================================================
# Skill 凋亡与熵减引擎 (Loop 5: Apoptosis Engine)
# =============================================================================

@dataclass
class SkillApoptosisResult:
    """技能凋亡/熵减结果"""
    timestamp: datetime = field(default_factory=datetime.now)
    total_skills_scanned: int = 0
    redundant_pairs_found: int = 0
    skills_merged: int = 0
    skills_pruned: int = 0
    original_entropy_score: float = 0.0
    final_entropy_score: float = 0.0
    action_log: list[str] = field(default_factory=list)
    merged_skills_details: list[dict[str, Any]] = field(default_factory=list)


class SkillApoptosisEngine:
    """
    技能凋亡与熵减引擎 (The Apoptosis & Meditation Engine)
    
    Loop 5 的物理实现。负责在系统空闲时对 SkillStore 进行深度扫描、
    重合度分析、大模型抽象合并（Merge）和冗余规则裁剪（Apoptosis）。
    """
    
    def __init__(self, llm_executor: Any, skill_store: Optional[Any] = None):
        """
        初始化技能凋亡引擎
        
        Args:
            llm_executor: 用于语义分析与合并的高精度 LLM 执行器
            skill_store: 技能存储中心，若不提供则自动获取默认
        """
        self.llm_executor = llm_executor
        from ..skill import get_skill_store
        self.skill_store = skill_store or get_skill_store()
        logger.info("[Apoptosis] 技能凋亡与数字冥想引擎初始化完成")
        
    async def run_meditation(self, max_pairs_to_process: int = 3) -> SkillApoptosisResult:
        """
        对技能库运行数字冥想，执行熵减修剪。
        
        Args:
            max_pairs_to_process: 单次冥想最多处理的冲突/冗余对数，防止大范围修改导致风险。
        """
        logger.info("[Apoptosis] 开始技能冥想：扫描 SkillStore 中的物理规则...")
        skills = self.skill_store.list_skills()
        
        result = SkillApoptosisResult(
            total_skills_scanned=len(skills),
            original_entropy_score=self._calculate_entropy(skills)
        )
        
        if len(skills) < 2:
            logger.info("[Apoptosis] 技能库小于 2，无需运行凋亡修剪")
            result.final_entropy_score = result.original_entropy_score
            return result
            
        # 1. 计算两两之间的语义重合度并筛选出高度重合对
        overlapping_pairs = await self._find_overlapping_pairs(skills)
        result.redundant_pairs_found = len(overlapping_pairs)
        
        processed_count = 0
        for skill_a, skill_b, reason in overlapping_pairs:
            if processed_count >= max_pairs_to_process:
                break
                
            logger.info(f"[Apoptosis] 发现重合对：'{skill_a.name}' ⬌ '{skill_b.name}' ({reason})")
            
            # 2. 调用高精度模型尝试融合成高维抽象 Skill
            merged_skill = await self._attempt_merge(skill_a, skill_b, reason)
            if merged_skill:
                # 3. 物理替换：将合并后的高维 Skill 注册，并把两个零散的原 Skill 凋亡掉
                # 保护内核基石能力，只允许对动态产生的/非核心技能执行凋亡
                if skill_a.tags and "builtin" in skill_a.tags:
                    logger.warning(f"[Apoptosis] 技能 '{skill_a.name}' 属于内核基石，免疫凋亡")
                    continue
                if skill_b.tags and "builtin" in skill_b.tags:
                    logger.warning(f"[Apoptosis] 技能 '{skill_b.name}' 属于内核基石，免疫凋亡")
                    continue
                
                # 保存新技能并删除旧技能
                self.skill_store.save_skill(merged_skill)
                self.skill_store.delete_skill(skill_a.id)
                self.skill_store.delete_skill(skill_b.id)
                
                result.skills_merged += 1
                result.skills_pruned += 2
                
                log_msg = f"合并并凋亡: '{skill_a.name}' 和 '{skill_b.name}' ⬌ 新高维技能 '{merged_skill.name}'"
                result.action_log.append(log_msg)
                logger.info(f"[Apoptosis] {log_msg}")
                
                result.merged_skills_details.append({
                    "from_a": skill_a.name,
                    "from_b": skill_b.name,
                    "to": merged_skill.name,
                    "reason": reason
                })
                processed_count += 1
                
        # 4. 计算冥想后的系统熵值
        remaining_skills = self.skill_store.list_skills()
        result.final_entropy_score = self._calculate_entropy(remaining_skills)
        logger.info(f"[Apoptosis] 技能冥想完成：系统熵值 {result.original_entropy_score:.2f} ➔ {result.final_entropy_score:.2f}")
        
        return result
        
    def _calculate_entropy(self, skills: list[Any]) -> float:
        """
        计算当前的系统熵值（混乱度/臃肿度评级）
        第一性原理：技能数量越多，冗余标签越多，系统的熵值越大。
        """
        if not skills:
            return 0.0
        # 基础熵值 = 技能总数 * 1.5
        # 加上命名相似性或标签重合性权重
        tag_pool = []
        for s in skills:
            tag_pool.extend(s.tags or [])
        unique_tags = len(set(tag_pool))
        tag_redundancy = len(tag_pool) - unique_tags
        
        return len(skills) * 1.5 + tag_redundancy * 0.2

    async def _find_overlapping_pairs(self, skills: list[Any]) -> list[tuple[Any, Any, str]]:
        """
        利用大模型对所有技能组合进行语义扫描，识别高度重合可合并的候选对。
        """
        overlapping = []
        # 双重循环比对（实际生产中可引入向量数据库加速，这里利用 LLM 语义鉴别）
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                skill_a = skills[i]
                skill_b = skills[j]
                
                # 简单的前置名称/标签重合性过滤，降低 LLM 损耗
                name_overlap = any(w in skill_b.name.lower() for w in skill_a.name.lower().split("_") if len(w) > 2)
                tag_overlap = len(set(skill_a.tags or []) & set(skill_b.tags or [])) >= 2
                
                if name_overlap or tag_overlap:
                    # 调用高精度大模型判断语义重合度
                    is_redundant, reason = await self._check_semantic_overlap_llm(skill_a, skill_b)
                    if is_redundant:
                        overlapping.append((skill_a, skill_b, reason))
                        
        return overlapping

    async def _check_semantic_overlap_llm(self, skill_a: Any, skill_b: Any) -> tuple[bool, str]:
        """使用 LLM 鉴别两个 Skill 在语义上是否属于冗余或可合并关系"""
        from ..llm.backends.base import Message
        
        prompt = (
            f"请对比以下两个技能（Skills）的定义，判断它们是否高度重复、语义重合，或者能被融合成一个更通用的高维技能。\n\n"
            f"### 技能 A:\n"
            f"名称: {skill_a.name}\n"
            f"描述: {skill_a.description}\n"
            f"触发器: {skill_a.trigger}\n\n"
            f"### 技能 B:\n"
            f"名称: {skill_b.name}\n"
            f"描述: {skill_b.description}\n"
            f"触发器: {skill_b.trigger}\n\n"
            f"请严格按照以下 JSON 格式回复，不要包含任何 Markdown 格式，哪怕是代码块标记：\n"
            f"{{\n"
            f"  \"is_redundant\": true/false,\n"
            f"  \"reason\": \"如果是，请给出合并该对技能的合理依据，如果不是，置空\"\n"
            f"}}"
        )
        
        try:
            response = await self.llm_executor.execute([Message.user(prompt)])
            # 兼容 Markdown 包裹
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            import json
            data = json.loads(content)
            return bool(data.get("is_redundant", False)), data.get("reason", "")
        except Exception as e:
            logger.warning(f"[Apoptosis] 语义重合度鉴别失败: {e}")
            return False, ""

    async def _attempt_merge(self, skill_a: Any, skill_b: Any, reason: str) -> Optional[Any]:
        """
        调用高精度 LLM 将两个零散的 Skill 进行降维合并，产生通用的高维 Skill (PEF/FDL DNA)。
        """
        from ..llm.backends.base import Message
        from ..skill import Skill
        
        prompt = (
            f"依据以下合理化原因，请将两个高度重合的技能融合成一个具有高度泛化性、能够同时覆盖二者功能的“高维通用技能”。\n\n"
            f"### 合并理由:\n{reason}\n\n"
            f"### 技能 A:\n{skill_a.to_dict() if hasattr(skill_a, 'to_dict') else str(skill_a)}\n\n"
            f"### 技能 B:\n{skill_b.to_dict() if hasattr(skill_b, 'to_dict') else str(skill_b)}\n\n"
            f"请提取二者的公共特征，设计出更高维度的抽象触发器（Trigger）与执行步骤（Steps），回复一个全新的 Skill 定义。\n"
            f"请严格返回如下 JSON 格式回复，绝对不要用任何 ```json 语法包裹，确保是纯粹的 JSON 字符串：\n"
            f"{{\n"
            f"  \"name\": \"合并后的通用名称 (如 universal_xxx_worker)\",\n"
            f"  \"description\": \"融合了 A 和 B 的高维抽象描述\",\n"
            f"  \"level\": \"user\",\n"
            f"  \"tags\": [\"merged\", \"abstract\"],\n"
            f"  \"trigger\": {{\n"
            f"     \"intent\": \"抽象后的通用意图（包含 A 和 B 的共性）\"\n"
            f"  }},\n"
            f"  \"steps\": []\n"
            f"}}"
        )
        
        try:
            response = await self.llm_executor.execute([Message.user(prompt)])
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            import json
            data = json.loads(content)
            
            # 使用 Skill 构造器安全反序列化
            merged_skill = Skill(
                id=f"skill_apoptosis_{int(time.time())}",
                name=data["name"],
                description=data["description"],
                trigger=data.get("trigger", {}),
                steps=data.get("steps", []),
                tags=data.get("tags", ["merged", "abstract"])
            )
            return merged_skill
        except Exception as e:
            logger.error(f"[Apoptosis] 技能高维合并失败: {e}")
            return None

