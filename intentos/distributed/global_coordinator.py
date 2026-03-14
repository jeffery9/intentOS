"""
全球大脑协调协议

协调全球分布式节点的思考

设计文档：docs/private/017-global-brain-coordination.md
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class BrainRegion:
    """大脑区域"""
    
    id: str
    location: tuple[float, float]
    nodes: list[str] = field(default_factory=list)
    leader_node: Optional[str] = None
    
    status: str = "active"
    load: float = 0.0
    latency_to_global: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location": self.location,
            "nodes": self.nodes,
            "leader_node": self.leader_node,
            "status": self.status,
            "load": self.load,
            "latency_to_global": self.latency_to_global,
        }


@dataclass
class ThoughtFragment:
    """思考片段"""
    
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    parent_thought_id: Optional[str] = None
    
    intent: Any = None
    context: dict[str, Any] = field(default_factory=dict)
    
    assigned_region: str = ""
    assigned_node: str = ""
    
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parent_thought_id": self.parent_thought_id,
            "intent": self.intent.to_dict() if self.intent else None,
            "context": self.context,
            "assigned_region": self.assigned_region,
            "assigned_node": self.assigned_node,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class GlobalState:
    """全球状态"""
    
    active_regions: int = 0
    average_load: float = 0.0
    total_thoughts: int = 0
    active_thoughts: int = 0
    
    timestamp: datetime = field(default_factory=datetime.now)


class GlobalCoordinator:
    """全球协调器"""
    
    def __init__(self):
        self.regions: dict[str, BrainRegion] = {}
        self.active_thoughts: dict[str, ThoughtFragment] = {}
        self.completed_thoughts: dict[str, ThoughtFragment] = {}
        self.region_coordinators: dict[str, Any] = {}
        self.global_state = GlobalState()
    
    async def submit_thought(
        self,
        intent: Any,
        context: dict[str, Any],
    ) -> str:
        """提交思考"""
        fragment = ThoughtFragment(
            intent=intent,
            context=context,
        )
        
        region = self._select_best_region(intent, context)
        fragment.assigned_region = region.id
        
        node = await self._select_best_node(region, intent)
        fragment.assigned_node = node
        
        self.active_thoughts[fragment.id] = fragment
        
        region_coordinator = self.region_coordinators.get(region.id)
        if region_coordinator:
            await region_coordinator.execute_fragment(fragment)
        
        return fragment.id
    
    def _select_best_region(
        self,
        intent: Any,
        context: dict,
    ) -> BrainRegion:
        """选择最佳区域"""
        user_location = context.get("user_location")
        
        if user_location:
            active_regions = [
                r for r in self.regions.values() if r.status == "active"
            ]
            
            if active_regions:
                best_region = min(
                    active_regions,
                    key=lambda r: self._calculate_distance(
                        user_location, r.location
                    )
                )
                return best_region
        
        active_regions = [
            r for r in self.regions.values() if r.status == "active"
        ]
        
        if active_regions:
            return min(active_regions, key=lambda r: r.load)
        
        raise RuntimeError("无可用区域")
    
    async def _select_best_node(
        self,
        region: BrainRegion,
        intent: Any,
    ) -> str:
        """选择区域内最佳节点"""
        if region.nodes:
            return region.nodes[0]
        return ""
    
    async def _coordination_loop(self) -> None:
        """全球协调循环"""
        while True:
            try:
                await asyncio.sleep(1.0)
                await self._update_global_state()
                await self._check_active_thoughts()
                await self._balance_load()
                await self._handle_failures()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"全球协调循环错误：{e}")
    
    async def _update_global_state(self) -> None:
        """更新全球状态"""
        active_regions = sum(
            1 for r in self.regions.values() if r.status == "active"
        )
        total_load = sum(r.load for r in self.regions.values())
        
        self.global_state.active_regions = active_regions
        self.global_state.average_load = (
            total_load / len(self.regions) if self.regions else 0
        )
        self.global_state.total_thoughts = (
            len(self.active_thoughts) + len(self.completed_thoughts)
        )
        self.global_state.active_thoughts = len(self.active_thoughts)
    
    async def _handle_failures(self) -> None:
        """故障检测和恢复"""
        for fragment_id, fragment in list(self.active_thoughts.items()):
            if fragment.started_at:
                elapsed = (datetime.now() - fragment.started_at).total_seconds()
                if elapsed > 300:
                    fragment.status = "failed"
                    fragment.error = "Thought execution timeout"
                    await self._reschedule_fragment(fragment)
    
    async def _reschedule_fragment(self, fragment: ThoughtFragment) -> None:
        """重新调度片段"""
        pass
    
    def _calculate_distance(
        self,
        loc1: tuple[float, float],
        loc2: tuple[float, float],
    ) -> float:
        """计算距离"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371
        
        lat1, lon1, lat2, lon2 = map(radians, [loc1[0], loc1[1], loc2[0], loc2[1]])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


class RegionCoordinator:
    """区域协调器"""
    
    def __init__(self, region: BrainRegion):
        self.region = region
        self.nodes: dict[str, Any] = {}
        self.pending_fragments: list[ThoughtFragment] = []
        self.running_fragments: dict[str, ThoughtFragment] = {}
    
    async def execute_fragment(self, fragment: ThoughtFragment) -> None:
        """执行思考片段"""
        self.pending_fragments.append(fragment)
        await self._schedule_fragments()
    
    async def _schedule_fragments(self) -> None:
        """调度待处理片段"""
        while self.pending_fragments:
            fragment = self.pending_fragments[0]
            node = await self.select_node(fragment.intent)
            
            if node:
                self.pending_fragments.pop(0)
                self.running_fragments[fragment.id] = fragment
    
    async def select_node(self, intent: Any) -> Optional[str]:
        """选择最佳节点"""
        healthy_nodes = [
            (node_id, agent)
            for node_id, agent in self.nodes.items()
            if getattr(agent, 'status', None) == "healthy"
        ]
        
        if not healthy_nodes:
            return None
        
        return min(healthy_nodes, key=lambda x: getattr(x[1], 'load', 0))[0]
    
    async def get_state(self) -> dict:
        """获取区域状态"""
        node_states = [
            await agent.get_state()
            for agent in self.nodes.values()
        ]
        
        total_load = sum(s.get("load", 0) for s in node_states)
        avg_load = total_load / len(node_states) if node_states else 0
        
        healthy_count = sum(1 for s in node_states if s.get("status") == "healthy")
        
        return {
            "region_id": self.region.id,
            "load": avg_load,
            "status": "active" if healthy_count > 0 else "offline",
            "node_count": len(self.nodes),
            "healthy_nodes": healthy_count,
            "pending_fragments": len(self.pending_fragments),
            "running_fragments": len(self.running_fragments),
        }
