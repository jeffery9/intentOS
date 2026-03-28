"""
意图模板自生长器 (Intent Template Self-Grower)

从高频用户交互中自动提炼新的意图模板
"""

from __future__ import annotations
import logging

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from ..graph import IntentGraph, IntentNode, IntentNodeType


@dataclass
class IntentPattern:
    """
    意图模式
    
    从历史交互中挖掘出的高频模式
    """
    pattern_id: str
    pattern_text: str  # 如 "对比 {region1} 和 {region2} 的{period}销售"
    parameters: list[str]  # 如 ["region1", "region2", "period"]
    frequency: int  # 出现频率
    first_seen: datetime
    last_seen: datetime
    examples: list[str] = field(default_factory=list)  # 示例意图文本
    confidence: float = 1.0
    
    def is_template_candidate(self, min_frequency: int = 5) -> bool:
        """检查是否是模板候选"""
        return (
            self.frequency >= min_frequency and
            len(self.parameters) > 0 and
            self.confidence > 0.7
        )
    
    def to_template(self) -> dict[str, Any]:
        """转换为意图模板"""
        return {
            "name": self._generate_name(),
            "description": f"Auto-generated from pattern: {self.pattern_text}",
            "patterns": [self.pattern_text],
            "parameters": [
                {
                    "name": param,
                    "type": "string",
                    "required": True,
                }
                for param in self.parameters
            ],
            "tags": ["auto-generated"],
        }
    
    def _generate_name(self) -> str:
        """生成模板名称"""
        # 从模式中提取动词和名词
        # 简化版本：使用模式文本的关键词
        words = self.pattern_text.split()
        verbs = [w for w in words if any(v in w.lower() for v in ["对比", "分析", "查询", "生成"])]
        
        if verbs:
            return f"{verbs[0]}_auto_{len(self.parameters)}params"
        else:
            return f"template_{self.pattern_id}"


@dataclass
class IntentHistoryEntry:
    """
    意图历史条目
    
    记录一次意图执行
    """
    intent_text: str
    timestamp: datetime
    parameters: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    execution_time_ms: float = 0.0
    user_id: str = ""
    session_id: str = ""


class IntentPatternMiner:
    """
    意图模式挖掘器
    
    从历史交互中挖掘高频模式
    """
    
    def __init__(self):
        self.history: list[IntentHistoryEntry] = []
        self.patterns: dict[str, IntentPattern] = {}
    
    def record_intent(
        self,
        intent_text: str,
        parameters: Optional[dict] = None,
        success: bool = True,
        execution_time_ms: float = 0.0,
        user_id: str = "",
        session_id: str = "",
    ) -> None:
        """记录意图执行"""
        entry = IntentHistoryEntry(
            intent_text=intent_text,
            timestamp=datetime.now(),
            parameters=parameters or {},
            success=success,
            execution_time_ms=execution_time_ms,
            user_id=user_id,
            session_id=session_id,
        )
        self.history.append(entry)
    
    async def analyze_patterns(
        self,
        time_range: str = "7d",
        min_frequency: int = 3,
        use_llm: bool = True,
    ) -> list[IntentPattern]:
        """
        分析意图模式
        
        Args:
            time_range: 时间范围 (如 "7d", "24h")
            min_frequency: 最小频率
            
        Returns:
            识别出的模式列表
        """
        # 1. 过滤时间范围
        cutoff = self._parse_time_range(time_range)
        recent_history = [h for h in self.history if h.timestamp > cutoff]
        
        # 2. 聚类相似的意图
        clusters = await self._cluster_intents(recent_history, use_llm=use_llm)
        
        # 3. 从每个聚类中提取模式
        patterns = []
        for cluster_id, entries in clusters.items():
            if len(entries) >= min_frequency:
                pattern = await self._extract_pattern(cluster_id, entries, use_llm=use_llm)
                if pattern:
                    patterns.append(pattern)
                    self.patterns[pattern.pattern_id] = pattern
        
        return patterns
    
    def get_template_candidates(
        self,
        min_frequency: int = 5,
    ) -> list[IntentPattern]:
        """获取模板候选"""
        return [
            p for p in self.patterns.values()
            if p.is_template_candidate(min_frequency)
        ]
    
    def _parse_time_range(self, time_range: str) -> datetime:
        """解析时间范围"""
        now = datetime.now()
        
        if time_range.endswith("h"):
            hours = int(time_range[:-1])
            return now - timedelta(hours=hours)
        elif time_range.endswith("d"):
            days = int(time_range[:-1])
            return now - timedelta(days=days)
        else:
            return now - timedelta(days=7)
    
    def _cluster_intents(
        self,
        entries: list[IntentHistoryEntry],
    ) -> dict[str, list[IntentHistoryEntry]]:
        """
        聚类相似的意图
        
        在实际系统中，这里会使用语义相似度聚类
        这里使用简化的关键词匹配
        """
        clusters: dict[str, list[IntentHistoryEntry]] = defaultdict(list)
        
        for entry in entries:
            # 提取关键词作为聚类 ID
            # 简化版本：使用前两个词作为聚类 ID
            words = entry.intent_text.split()[:2]
            cluster_id = "_".join(words)
            clusters[cluster_id].append(entry)
        
        return clusters
    
    def _extract_pattern(
        self,
        cluster_id: str,
        entries: list[IntentHistoryEntry],
    ) -> Optional[IntentPattern]:
        """
        从聚类中提取模式
        
        在实际系统中，这里会使用 LLM 生成泛化的模式
        """
        if not entries:
            return None
        
        # 收集所有参数
        all_params = set()
        for entry in entries:
            all_params.update(entry.parameters.keys())
        
        # 使用第一个意图作为基础模式
        base_text = entries[0].intent_text
        
        # 泛化参数
        pattern_text = base_text
        for param in all_params:
            pattern_text = pattern_text.replace(
                entries[0].parameters.get(param, param),
                f"{{{param}}}"
            )
        
        return IntentPattern(
            pattern_id=cluster_id,
            pattern_text=pattern_text,
            parameters=list(all_params),
            frequency=len(entries),
            first_seen=min(e.timestamp for e in entries),
            last_seen=max(e.timestamp for e in entries),
            examples=[e.intent_text for e in entries[:5]],
            confidence=0.9,
        )


class IntentTemplateSelfGrower:
    """
    意图模板自生长器
    
    自动从高频模式生成新的意图模板
    """
    
    def __init__(
        self,
        intent_graph: IntentGraph,
        miner: Optional[IntentPatternMiner] = None,
    ):
        self.intent_graph = intent_graph
        self.miner = miner or IntentPatternMiner()
        self.growth_history: list[dict] = []
    
    async def grow_from_history(
        self,
        time_range: str = "7d",
        min_frequency: int = 5,
        auto_approve: bool = False,
    ) -> list[dict]:
        """
        从历史交互中生长新的意图模板
        
        Args:
            time_range: 时间范围
            min_frequency: 最小频率
            auto_approve: 是否自动批准
            
        Returns:
            新生成的模板列表
        """
        new_templates = []
        
        # 1. 分析模式
        patterns = self.miner.analyze_patterns(time_range, min_frequency)
        
        # 2. 获取模板候选
        candidates = self.miner.get_template_candidates(min_frequency)
        
        # 3. 为每个候选生成模板
        for candidate in candidates:
            # 检查是否已存在
            existing = self.intent_graph.search_by_name(candidate._generate_name())
            if existing:
                continue
            
            # 生成模板
            template = candidate.to_template()
            
            # 在实际系统中，这里需要人工审批
            if not auto_approve:
                # 触发审批流程
                continue
            
            # 注册模板
            node = IntentNode(
                node_id=f"template_{template['name']}",
                node_type=IntentNodeType.TEMPLATE,
                name=template["name"],
                description=template["description"],
                content=template,
                tags=template.get("tags", []),
            )
            
            self.intent_graph.add_node(node)
            
            new_templates.append({
                "template": template,
                "node_id": node.node_id,
                "status": "registered",
            })
            
            self.growth_history.append({
                "timestamp": datetime.now().isoformat(),
                "pattern_id": candidate.pattern_id,
                "template_name": template["name"],
                "status": "registered",
            })
        
        return new_templates
    
    def record_intent(
        self,
        intent_text: str,
        parameters: Optional[dict] = None,
        success: bool = True,
        execution_time_ms: float = 0.0,
        user_id: str = "",
        session_id: str = "",
    ) -> None:
        """记录意图执行（用于后续分析）"""
        self.miner.record_intent(
            intent_text=intent_text,
            parameters=parameters,
            success=success,
            execution_time_ms=execution_time_ms,
            user_id=user_id,
            session_id=session_id,
        )
    
    def get_growth_history(self) -> list[dict]:
        """获取生长历史"""
        return self.growth_history
    
    def get_statistics(self) -> dict[str, Any]:
        """获取统计"""
        return {
            "total_history_entries": len(self.miner.history),
            "total_patterns": len(self.miner.patterns),
            "template_candidates": len(self.miner.get_template_candidates()),
            "grown_templates": len(self.growth_history),
        }


# =============================================================================
# 使用示例
# =============================================================================


async def demo_template_self_growth():
    """演示意图模板自生长"""
    from ..graph import create_intent_graph
    
    # 1. 初始化
    graph = create_intent_graph()
    grower = IntentTemplateSelfGrower(intent_graph=graph)
    
    # 2. 模拟历史交互
    for i in range(10):
        grower.record_intent(
            intent_text=f"对比华东和华南的 Q{i%4+1}销售",
            parameters={"region1": "华东", "region2": "华南", "period": f"Q{i%4+1}"},
            success=True,
            execution_time_ms=100,
            user_id=f"user_{i%3}",
        )
    
    # 3. 生长新模板
    new_templates = await grower.grow_from_history(
        time_range="7d",
        min_frequency=5,
        auto_approve=True,  # 演示用，实际应该人工审批
    )
    
    print(f"新生成的模板数：{len(new_templates)}")
    for template_info in new_templates:
        print(f"  - {template_info['template']['name']}")
    
    # 4. 查看统计
    stats = grower.get_statistics()
    print(f"统计：{stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_template_self_growth())
