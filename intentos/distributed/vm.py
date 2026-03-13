"""
分布式语义 VM (Distributed Semantic VM)

核心洞察:
- 单节点语义 VM → 多节点语义 VM 集群
- 集中式内存 → 分布式语义内存 (Redis/一致性哈希)
- 单 LLM 处理器 → 多 LLM 处理器 (负载均衡)
- 单程序执行 → 分布式程序执行 (Map/Reduce 语义)

架构目标:
1. 水平扩展：可以添加更多 VM 节点
2. 容错性：节点故障不影响整体
3. 语义一致性：分布式环境下的语义一致性
4. Self-Bootstrap：分布式自修改
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import uuid
import json
import hashlib


# =============================================================================
# 分布式节点
# =============================================================================

@dataclass
class VMNode:
    """
    VM 节点
    
    分布式语义 VM 集群中的单个节点
    """
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    host: str = "localhost"
    port: int = 8000
    status: str = "active"  # active/inactive/loading
    load: float = 0.0  # 0.0-1.0
    capabilities: list[str] = field(default_factory=list)  # 支持的指令类型
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "status": self.status,
            "load": self.load,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# 分布式语义内存
# =============================================================================

class DistributedSemanticMemory:
    """
    分布式语义内存
    
    使用一致性哈希在多个节点间分布语义数据
    """
    
    def __init__(self, nodes: Optional[list[VMNode]] = None):
        self.nodes = nodes or []
        self.ring: dict[int, VMNode] = {}  # 一致性哈希环
        self._rebuild_ring()
    
    def _rebuild_ring(self) -> None:
        """重建一致性哈希环"""
        self.ring = {}
        for node in self.nodes:
            if node.status == "active":
                # 为每个节点创建多个虚拟节点 (虚拟节点提高均衡性)
                for i in range(100):  # 100 个虚拟节点
                    key = f"{node.node_id}:{i}"
                    hash_key = self._hash_key(key)
                    self.ring[hash_key] = node
        
        # 排序哈希环
        self.ring = dict(sorted(self.ring.items()))
    
    def _hash_key(self, key: str) -> int:
        """计算一致性哈希"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def _get_node_for_key(self, key: str) -> Optional[VMNode]:
        """根据 key 获取负责节点"""
        if not self.ring:
            return None
        
        hash_key = self._hash_key(key)
        
        # 找到哈希环上第一个 >= hash_key 的节点
        for ring_key, node in self.ring.items():
            if ring_key >= hash_key:
                return node
        
        # 如果没找到，返回第一个节点 (环绕)
        return next(iter(self.ring.values()))
    
    async def get(self, store: str, key: str) -> Optional[Any]:
        """获取数据"""
        node = self._get_node_for_key(f"{store}:{key}")
        if not node:
            return None
        
        # 实际实现应该通过 RPC 调用远程节点
        # 这里简化为本地存储
        return await self._local_get(node, store, key)
    
    async def set(self, store: str, key: str, value: Any) -> None:
        """设置数据"""
        node = self._get_node_for_key(f"{store}:{key}")
        if not node:
            return
        
        # 实际实现应该通过 RPC 调用远程节点
        await self._local_set(node, store, key, value)
    
    async def delete(self, store: str, key: str) -> bool:
        """删除数据"""
        node = self._get_node_for_key(f"{store}:{key}")
        if not node:
            return False
        
        return await self._local_delete(node, store, key)
    
    async def _local_get(self, node: VMNode, store: str, key: str) -> Optional[Any]:
        """本地获取 (简化实现)"""
        # 实际应该通过 gRPC/HTTP 调用远程节点
        pass
    
    async def _local_set(self, node: VMNode, store: str, key: str, value: Any) -> None:
        """本地设置 (简化实现)"""
        pass
    
    async def _local_delete(self, node: VMNode, store: str, key: str) -> bool:
        """本地删除 (简化实现)"""
        return True
    
    def add_node(self, node: VMNode) -> None:
        """添加节点"""
        self.nodes.append(node)
        self._rebuild_ring()
    
    def remove_node(self, node_id: str) -> None:
        """移除节点"""
        self.nodes = [n for n in self.nodes if n.node_id != node_id]
        self._rebuild_ring()
    
    def get_nodes(self) -> list[VMNode]:
        """获取所有节点"""
        return self.nodes.copy()
    
    def get_active_nodes(self) -> list[VMNode]:
        """获取活跃节点"""
        return [n for n in self.nodes if n.status == "active"]


# =============================================================================
# 分布式程序计数器
# =============================================================================

@dataclass
class DistributedProgramCounter:
    """
    分布式程序计数器
    
    跟踪分布式环境中程序的执行进度
    """
    program_id: str
    node_id: str
    pc: int = 0
    status: str = "running"  # running/paused/stopped/failed
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "program_id": self.program_id,
            "node_id": self.node_id,
            "pc": self.pc,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# =============================================================================
# 分布式执行协调器
# =============================================================================

class DistributedCoordinator:
    """
    分布式执行协调器
    
    协调多个 VM 节点的程序执行
    """
    
    def __init__(self, memory: DistributedSemanticMemory):
        self.memory = memory
        self.program_counters: dict[str, DistributedProgramCounter] = {}
        self.results: dict[str, dict] = {}
    
    async def submit_program(
        self,
        program: Any,  # SemanticProgram
        context: Optional[dict] = None,
    ) -> str:
        """
        提交程序执行
        
        Args:
            program: 语义程序
            context: 执行上下文
        
        Returns:
            执行 ID
        """
        exec_id = str(uuid.uuid4())
        
        # 选择最佳节点
        node = await self._select_best_node()
        
        if not node:
            return self._create_error_result(exec_id, "没有可用节点")
        
        # 创建程序计数器
        pc = DistributedProgramCounter(
            program_id=program.name,
            node_id=node.node_id,
        )
        self.program_counters[exec_id] = pc
        
        # 在选定节点上执行程序
        # 实际实现应该通过 RPC 调用远程节点
        await self._execute_on_node(exec_id, program, node, context)
        
        return exec_id
    
    async def _select_best_node(self) -> Optional[VMNode]:
        """选择最佳节点"""
        active_nodes = self.memory.get_active_nodes()
        
        if not active_nodes:
            return None
        
        # 选择负载最低的节点
        return min(active_nodes, key=lambda n: n.load)
    
    async def _execute_on_node(
        self,
        exec_id: str,
        program: Any,
        node: VMNode,
        context: Optional[dict] = None,
    ) -> None:
        """在节点上执行程序"""
        # 实际实现应该通过 gRPC/HTTP 调用远程节点
        # 这里简化为直接执行
        pass
    
    def _create_error_result(self, exec_id: str, error: str) -> str:
        """创建错误结果"""
        self.results[exec_id] = {
            "success": False,
            "error": error,
        }
        return exec_id
    
    async def get_result(self, exec_id: str) -> Optional[dict]:
        """获取执行结果"""
        return self.results.get(exec_id)
    
    async def get_status(self, exec_id: str) -> Optional[dict]:
        """获取执行状态"""
        pc = self.program_counters.get(exec_id)
        if not pc:
            return None
        
        return pc.to_dict()


# =============================================================================
# 分布式语义 VM 集群
# =============================================================================

class DistributedSemanticVM:
    """
    分布式语义虚拟机集群
    
    管理多个 VM 节点，提供分布式语义执行能力
    """
    
    def __init__(self, llm_executor: Any = None):
        """
        初始化分布式 VM
        
        Args:
            llm_executor: LLM 执行器 (用于所有节点)
        """
        self.memory = DistributedSemanticMemory()
        self.coordinator = DistributedCoordinator(self.memory)
        self.llm_executor = llm_executor
        
        # 本地节点
        self.local_node = VMNode(
            host="localhost",
            port=8000,
            capabilities=["CREATE", "MODIFY", "DELETE", "QUERY", "EXECUTE", "LOOP", "WHILE", "IF"],
        )
        
        # 添加本地节点到集群
        self.memory.add_node(self.local_node)
    
    async def add_node(
        self,
        host: str,
        port: int,
        capabilities: Optional[list[str]] = None,
    ) -> VMNode:
        """添加远程节点"""
        node = VMNode(
            host=host,
            port=port,
            capabilities=capabilities or ["CREATE", "MODIFY", "DELETE", "QUERY", "EXECUTE"],
        )
        self.memory.add_node(node)
        return node
    
    async def remove_node(self, node_id: str) -> None:
        """移除节点"""
        self.memory.remove_node(node_id)
    
    async def get_cluster_status(self) -> dict[str, Any]:
        """获取集群状态"""
        nodes = self.memory.get_nodes()
        active_nodes = self.memory.get_active_nodes()
        
        return {
            "total_nodes": len(nodes),
            "active_nodes": len(active_nodes),
            "nodes": [n.to_dict() for n in nodes],
            "pending_programs": len(self.coordinator.program_counters),
        }
    
    async def execute_program(
        self,
        program: Any,  # SemanticProgram
        context: Optional[dict] = None,
    ) -> str:
        """
        执行程序 (分布式)
        
        Args:
            program: 语义程序
            context: 执行上下文
        
        Returns:
            执行 ID
        """
        return await self.coordinator.submit_program(program, context)
    
    async def get_execution_result(self, exec_id: str) -> Optional[dict]:
        """获取执行结果"""
        return await self.coordinator.get_result(exec_id)
    
    async def get_execution_status(self, exec_id: str) -> Optional[dict]:
        """获取执行状态"""
        return await self.coordinator.get_status(exec_id)


# =============================================================================
# 分布式语义指令
# =============================================================================

from enum import Enum

class DistributedOpcode(Enum):
    """分布式语义操作码"""
    
    # 基础指令 (继承自 SemanticOpcode)
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    QUERY = "query"
    EXECUTE = "execute"
    
    # 分布式指令
    REPLICATE = "replicate"     # 复制数据到多个节点
    SHARD = "shard"             # 分片数据
    MIGRATE = "migrate"         # 迁移数据到另一个节点
    BROADCAST = "broadcast"     # 广播到所有节点
    
    # 分布式控制流
    SPAWN = "spawn"             # 在新节点上生成子程序
    SYNC = "sync"               # 同步多个节点的执行
    BARRIER = "barrier"         # 执行屏障 (等待所有节点)


# =============================================================================
# 便捷函数
# =============================================================================

def create_distributed_vm(llm_executor: Any = None) -> DistributedSemanticVM:
    """创建分布式语义 VM"""
    return DistributedSemanticVM(llm_executor)


def create_node(host: str, port: int, **kwargs) -> VMNode:
    """创建 VM 节点"""
    return VMNode(host=host, port=port, **kwargs)
