"""
一致性协议

提供 Quorum 复制和版本向量

设计文档：docs/private/007-consensus-protocol.md
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ConsistencyLevel(Enum):
    """一致性级别"""
    STRONG = "strong"
    QUORUM = "quorum"
    EVENTUAL = "eventual"


@dataclass
class VersionVector:
    """版本向量"""
    
    versions: dict[str, int] = field(default_factory=dict)
    
    def increment(self, node_id: str) -> None:
        """增加当前节点的版本"""
        self.versions[node_id] = self.versions.get(node_id, 0) + 1
    
    def merge(self, other: VersionVector) -> None:
        """合并另一个版本向量"""
        for node_id, version in other.versions.items():
            self.versions[node_id] = max(
                self.versions.get(node_id, 0),
                version
            )
    
    def dominates(self, other: VersionVector) -> bool:
        """检查是否支配另一个版本向量"""
        dominated = False
        for node_id in set(self.versions.keys()) | set(other.versions.keys()):
            self_ver = self.versions.get(node_id, 0)
            other_ver = other.versions.get(node_id, 0)
            
            if self_ver < other_ver:
                return False
            if self_ver > other_ver:
                dominated = True
        
        return dominated
    
    def concurrent_with(self, other: VersionVector) -> bool:
        """检查是否并发（冲突）"""
        return not self.dominates(other) and not other.dominates(self)
    
    def to_dict(self) -> dict:
        return {"versions": self.versions.copy()}
    
    @classmethod
    def from_dict(cls, data: dict) -> VersionVector:
        return cls(versions=data.get("versions", {}).copy())


@dataclass
class VersionedValue:
    """带版本的值"""
    
    value: Any
    version: VersionVector
    timestamp: datetime = field(default_factory=datetime.now)
    checksum: str = ""
    
    def compute_checksum(self) -> str:
        """计算校验和"""
        data = f"{self.value}:{self.timestamp.isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "version": self.version.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> VersionedValue:
        return cls(
            value=data["value"],
            version=VersionVector.from_dict(data["version"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            checksum=data.get("checksum", ""),
        )


@dataclass
class WriteRequest:
    """写请求"""
    
    id: str = field(default_factory=lambda: str(hashlib.md5(
        str(datetime.now()).encode()
    ).hexdigest()[:8]))
    store: str = ""
    key: str = ""
    value: Any = None
    version: VersionVector = field(default_factory=VersionVector)
    consistency: ConsistencyLevel = ConsistencyLevel.QUORUM
    
    acks: dict[str, bool] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def ack_count(self) -> int:
        return sum(1 for v in self.acks.values() if v)
    
    def quorum_size(self, total_nodes: int) -> int:
        """计算法定人数"""
        if self.consistency == ConsistencyLevel.STRONG:
            return total_nodes
        elif self.consistency == ConsistencyLevel.QUORUM:
            return total_nodes // 2 + 1
        else:
            return 1
    
    def has_quorum(self, total_nodes: int) -> bool:
        """检查是否达到法定人数"""
        return self.ack_count >= self.quorum_size(total_nodes)


@dataclass
class ReadRequest:
    """读请求"""
    
    id: str = field(default_factory=lambda: str(hashlib.md5(
        str(datetime.now()).encode()
    ).hexdigest()[:8]))
    store: str = ""
    key: str = ""
    consistency: ConsistencyLevel = ConsistencyLevel.QUORUM
    
    responses: list[VersionedValue] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_latest_value(self) -> Optional[Any]:
        """获取最新值"""
        if not self.responses:
            return None
        
        latest = self.responses[0]
        for response in self.responses[1:]:
            if response.version.dominates(latest.version):
                latest = response
            elif latest.version.concurrent_with(response.version):
                if response.timestamp > latest.timestamp:
                    latest = response
        
        return latest.value


class QuorumReplicator:
    """Quorum 复制器"""
    
    def __init__(
        self,
        nodes: Optional[list] = None,
        replication_factor: int = 3,
        consistency: ConsistencyLevel = ConsistencyLevel.QUORUM,
    ):
        self.nodes = nodes or []
        self.replication_factor = replication_factor
        self.consistency = consistency
        self._storage: dict[str, VersionedValue] = {}
    
    async def write(
        self,
        store: str,
        key: str,
        value: Any,
        consistency: Optional[ConsistencyLevel] = None,
    ) -> bool:
        """写操作（带 Quorum 确认）"""
        consistency = consistency or self.consistency
        
        version = VersionVector()
        version.increment("local")
        
        versioned_value = VersionedValue(
            value=value,
            version=version,
        )
        versioned_value.checksum = versioned_value.compute_checksum()
        
        write_req = WriteRequest(
            store=store,
            key=key,
            value=value,
            version=version,
            consistency=consistency,
        )
        
        self._storage[f"{store}:{key}"] = versioned_value
        write_req.acks["local"] = True
        
        if consistency != ConsistencyLevel.EVENTUAL:
            await self._replicate_write(write_req)
        
        total_nodes = 1 + len(self.nodes)
        return write_req.has_quorum(total_nodes)
    
    async def read(
        self,
        store: str,
        key: str,
        consistency: Optional[ConsistencyLevel] = None,
    ) -> Optional[Any]:
        """读操作（带 Quorum 确认）"""
        consistency = consistency or self.consistency
        
        read_req = ReadRequest(
            store=store,
            key=key,
            consistency=consistency,
        )
        
        full_key = f"{store}:{key}"
        if full_key in self._storage:
            read_req.responses.append(self._storage[full_key])
        
        if consistency != ConsistencyLevel.EVENTUAL:
            await self._gather_reads(read_req)
        
        return read_req.get_latest_value()
    
    async def _replicate_write(self, req: WriteRequest) -> None:
        """复制写操作到其它节点"""
        for node in self.nodes:
            try:
                await self._send_to_node(node, "write", req)
                req.acks[node.get("node_id", "unknown")] = True
            except Exception:
                req.acks[node.get("node_id", "unknown")] = False
    
    async def _gather_reads(self, req: ReadRequest) -> None:
        """从其它节点收集读响应"""
        for node in self.nodes:
            try:
                response = await self._send_to_node(node, "read", req)
                if response:
                    req.responses.append(response)
            except Exception:
                pass
    
    async def _send_to_node(
        self,
        node: dict,
        operation: str,
        request: Any,
    ) -> Any:
        """发送请求到节点（模拟）"""
        await asyncio.sleep(0.01)
        return None
    
    def get_storage_stats(self) -> dict:
        """获取存储统计"""
        return {
            "total_keys": len(self._storage),
            "nodes_count": len(self.nodes),
            "replication_factor": self.replication_factor,
            "consistency": self.consistency.value,
        }


import asyncio
