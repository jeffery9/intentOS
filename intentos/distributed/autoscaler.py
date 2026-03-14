"""
Cloud-Native 自动扩缩容

提供 Kubernetes HPA 集成和自动扩缩容

设计文档：docs/private/013-cloud-native-architecture.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ScaleDirection(Enum):
    """扩缩容方向"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_CHANGE = "no_change"


@dataclass
class ScalingPolicy:
    """扩缩容策略"""
    
    min_replicas: int = 1
    max_replicas: int = 10000
    
    target_cpu_utilization: float = 70.0
    target_memory_utilization: float = 80.0
    target_requests_per_second: int = 1000
    
    scale_up_stabilization_seconds: int = 0
    scale_down_stabilization_seconds: int = 300
    
    scale_up_rate_percent: int = 100
    scale_down_rate_percent: int = 50
    
    @classmethod
    def default(cls) -> ScalingPolicy:
        return cls()
    
    @classmethod
    def aggressive(cls) -> ScalingPolicy:
        """激进扩缩容"""
        return cls(
            min_replicas=1,
            max_replicas=50000,
            scale_up_stabilization_seconds=0,
            scale_down_stabilization_seconds=60,
        )
    
    @classmethod
    def conservative(cls) -> ScalingPolicy:
        """保守扩缩容"""
        return cls(
            min_replicas=3,
            max_replicas=1000,
            scale_up_stabilization_seconds=300,
            scale_down_stabilization_seconds=600,
        )


@dataclass
class Metrics:
    """指标数据"""
    
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    requests_per_second: int = 0
    pending_requests: int = 0
    error_rate: float = 0.0
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "cpu_utilization": self.cpu_utilization,
            "memory_utilization": self.memory_utilization,
            "requests_per_second": self.requests_per_second,
            "pending_requests": self.pending_requests,
            "error_rate": self.error_rate,
            "timestamp": self.timestamp.isoformat(),
        }


class AutoScaler:
    """自动扩缩容器"""
    
    def __init__(
        self,
        policy: Optional[ScalingPolicy] = None,
        current_replicas: int = 1,
    ):
        self.policy = policy or ScalingPolicy.default()
        self.current_replicas = current_replicas
        self._scale_up_cooldown: Optional[datetime] = None
        self._scale_down_cooldown: Optional[datetime] = None
    
    def decide_scaling(
        self,
        metrics: Metrics,
    ) -> tuple[ScaleDirection, int]:
        """
        决定扩缩容
        
        Returns:
            (方向，目标副本数)
        """
        direction = ScaleDirection.NO_CHANGE
        target_replicas = self.current_replicas
        
        # CPU 扩缩容决策
        if metrics.cpu_utilization > self.policy.target_cpu_utilization:
            direction = ScaleDirection.SCALE_UP
            scale_factor = metrics.cpu_utilization / self.policy.target_cpu_utilization
            target_replicas = int(self.current_replicas * scale_factor)
        
        elif metrics.cpu_utilization < self.policy.target_cpu_utilization * 0.5:
            direction = ScaleDirection.SCALE_DOWN
            scale_factor = metrics.cpu_utilization / (self.policy.target_cpu_utilization * 0.5)
            target_replicas = max(
                self.policy.min_replicas,
                int(self.current_replicas * scale_factor)
            )
        
        # 请求速率扩缩容决策
        if metrics.requests_per_second > self.policy.target_requests_per_second:
            if direction == ScaleDirection.SCALE_UP:
                # 叠加
                rps_factor = metrics.requests_per_second / self.policy.target_requests_per_second
                target_replicas = int(target_replicas * rps_factor)
            else:
                direction = ScaleDirection.SCALE_UP
                target_replicas = int(
                    self.current_replicas * 
                    (metrics.requests_per_second / self.policy.target_requests_per_second)
                )
        
        # 应用扩缩容速率限制
        if direction == ScaleDirection.SCALE_UP:
            max_increase = int(
                self.current_replicas * self.policy.scale_up_rate_percent / 100
            )
            target_replicas = min(
                target_replicas,
                self.current_replicas + max_increase,
                self.policy.max_replicas
            )
        
        elif direction == ScaleDirection.SCALE_DOWN:
            max_decrease = int(
                self.current_replicas * self.policy.scale_down_rate_percent / 100
            )
            target_replicas = max(
                target_replicas,
                self.current_replicas - max_decrease,
                self.policy.min_replicas
            )
        
        # 稳定窗口检查
        now = datetime.now()
        if direction == ScaleDirection.SCALE_UP and self._scale_up_cooldown:
            if (now - self._scale_up_cooldown).total_seconds() < self.policy.scale_up_stabilization_seconds:
                direction = ScaleDirection.NO_CHANGE
        
        elif direction == ScaleDirection.SCALE_DOWN and self._scale_down_cooldown:
            if (now - self._scale_down_cooldown).total_seconds() < self.policy.scale_down_stabilization_seconds:
                direction = ScaleDirection.NO_CHANGE
        
        # 更新冷却时间
        if direction == ScaleDirection.SCALE_UP:
            self._scale_up_cooldown = now
        elif direction == ScaleDirection.SCALE_DOWN:
            self._scale_down_cooldown = now
        
        return direction, target_replicas
    
    def update_replicas(self, new_replicas: int) -> None:
        """更新当前副本数"""
        self.current_replicas = new_replicas
    
    def get_status(self) -> dict:
        """获取状态"""
        return {
            "current_replicas": self.current_replicas,
            "min_replicas": self.policy.min_replicas,
            "max_replicas": self.policy.max_replicas,
            "scale_up_cooldown": self._scale_up_cooldown.isoformat() if self._scale_up_cooldown else None,
            "scale_down_cooldown": self._scale_down_cooldown.isoformat() if self._scale_down_cooldown else None,
        }


class SpotInstanceManager:
    """Spot 实例管理器"""
    
    def __init__(self):
        self.spot_enabled = True
        self.spot_percentage = 0.8
        self.on_demand_min = 2
    
    def get_optimal_instance_mix(self) -> dict[str, float]:
        """获取最优实例组合"""
        return {
            "spot": self.spot_percentage,
            "on_demand": 1 - self.spot_percentage,
        }
    
    def handle_spot_interruption(
        self,
        instance_id: str,
        total_capacity: int,
    ) -> dict[str, Any]:
        """处理 Spot 实例中断"""
        # 计算需要补充的容量
        spot_capacity = int(total_capacity * self.spot_percentage)
        on_demand_capacity = total_capacity - spot_capacity
        
        # 如果 Spot 实例中断，临时用按需实例补充
        return {
            "action": "replace_with_on_demand",
            "instance_id": instance_id,
            "priority": "high",
        }


class ResourceReclaimer:
    """资源回收器"""
    
    def __init__(self):
        self.idle_threshold_seconds = 900  # 15 分钟
        self.expired_key_max_age_seconds = 7 * 24 * 3600  # 7 天
    
    async def reclaim_idle_resources(self, resources: list[dict]) -> int:
        """回收闲置资源"""
        reclaimed = 0
        now = datetime.now()
        
        for resource in resources:
            last_used = resource.get("last_used")
            if last_used:
                idle_seconds = (now - last_used).total_seconds()
                if idle_seconds > self.idle_threshold_seconds:
                    # 标记为可回收
                    reclaimed += 1
        
        return reclaimed
    
    async def cleanup_expired_data(self, data_store: Any) -> int:
        """清理过期数据"""
        cleaned = 0
        now = datetime.now().timestamp()
        
        # 实际实现会根据存储类型不同而不同
        # 这里是简化版本
        return cleaned
