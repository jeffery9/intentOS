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
from typing import Any, Optional, Union
from datetime import datetime
import uuid
import json
import hashlib
import asyncio
import aiohttp
from aiohttp import web


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
        self.local_storage = SemanticMemory()  # 本地缓存或主存储
        self._rebuild_ring()
    
    def get_state(self) -> dict[str, Any]:
        """获取内存状态"""
        # 返回本地存储状态作为集群状态的代理
        return self.local_storage.get_state()
    
    async def get(self, store: str, key: str) -> Optional[Any]:
        """获取数据"""
        node = self._get_node_for_key(f"{store}:{key}")
        if not node:
            return None
        
        # 如果是本地节点，直接返回
        if node.host == "localhost":
            return self.local_storage.get(store, key)
        
        return await self._remote_get(node, store, key)
    
    async def set(self, store: str, key: str, value: Any) -> None:
        """设置数据"""
        node = self._get_node_for_key(f"{store}:{key}")
        if not node:
            return
        
        # 如果是本地节点，直接设置
        if node.host == "localhost":
            self.local_storage.set(store, key, value)
            return
            
        await self._remote_set(node, store, key, value)
    
    async def delete(self, store: str, key: str) -> bool:
        """删除数据"""
        node = self._get_node_for_key(f"{store}:{key}")
        if not node:
            return False
        
        # 如果是本地节点，直接删除
        if node.host == "localhost":
            return self.local_storage.delete(store, key)
            
        return await self._remote_delete(node, store, key)
    
    async def _remote_get(self, node: VMNode, store: str, key: str) -> Optional[Any]:
        """通过 HTTP 调用远程节点获取数据"""
        url = f"http://{node.host}:{node.port}/memory/get"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"store": store, "key": key}, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("value")
        except Exception:
            return None
        return None
    
    async def _remote_set(self, node: VMNode, store: str, key: str, value: Any) -> None:
        """通过 HTTP 调用远程节点设置数据"""
        url = f"http://{node.host}:{node.port}/memory/set"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"store": store, "key": key, "value": value}, timeout=5) as resp:
                    pass
        except Exception:
            pass
    
    async def _remote_delete(self, node: VMNode, store: str, key: str) -> bool:
        """通过 HTTP 调用远程节点删除数据"""
        url = f"http://{node.host}:{node.port}/memory/delete"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"store": store, "key": key}, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("success", False)
        except Exception:
            return False
        return False
    
    def log_audit(self, action: str, details: dict) -> str:
        """记录审计日志"""
        return self.local_storage.log_audit(action, details)
    
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

from enum import Enum

class ProcessState(Enum):
    """进程状态"""
    NEW = "new"
    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ZOMBIE = "zombie"

@dataclass
class SemanticProcess:
    """
    语义进程 (Process Control Block - PCB)
    
    在分布式内核中代表一个正在执行的语义程序
    """
    pid: str = field(default_factory=lambda: str(uuid.uuid4()))
    program_name: str = ""
    node_id: str = ""
    state: ProcessState = ProcessState.NEW
    pc: int = 0  # 程序计数器
    parent_pid: Optional[str] = None
    priority: int = 10
    start_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "pid": self.pid,
            "program_name": self.program_name,
            "node_id": self.node_id,
            "state": self.state.value,
            "pc": self.pc,
            "parent_pid": self.parent_pid,
            "priority": self.priority,
            "start_time": self.start_time.isoformat(),
            "update_time": self.update_time.isoformat(),
            "context": self.context,
            "error": self.error
        }

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
    分布式执行协调器 / 进程调度器
    
    协调多个 VM 节点的程序执行并管理 PCB
    """
    
    def __init__(self, memory: DistributedSemanticMemory, local_vm: Any = None):
        self.memory = memory
        self.local_vm = local_vm
        self.processes: dict[str, SemanticProcess] = {}  # 活跃进程表 (PID -> PCB)
        self.results: dict[str, dict] = {}
        self.last_sync_time: datetime = datetime.now()

    async def fork_process(
        self,
        program: Any,  # SemanticProgram
        context: Optional[dict] = None,
        parent_pid: Optional[str] = None
    ) -> str:
        """
        生成/分发新进程 (Equivalent to fork + exec)
        
        Args:
            program: 语义程序
            context: 执行上下文
            parent_pid: 父进程 PID
        
        Returns:
            PID
        """
        pid = str(uuid.uuid4())
        
        # 1. 选择最佳节点 (调度策略)
        node = await self._select_best_node()
        if not node:
            return self._create_error_result(pid, "调度失败：没有可用节点")
        
        # 2. 创建 PCB
        pcb = SemanticProcess(
            pid=pid,
            program_name=program.name,
            node_id=node.node_id,
            parent_pid=parent_pid,
            context=context or {},
            state=ProcessState.NEW
        )
        self.processes[pid] = pcb
        
        # 3. 跨节点执行
        if node.host == "localhost" and self.local_vm:
            # 本地直接执行
            pcb.state = ProcessState.RUNNING
            asyncio.create_task(self._run_local_executor(pid, program, context))
        else:
            # 远程 RPC 执行
            await self._execute_on_node(pid, program, node, context)
            pcb.state = ProcessState.RUNNING
            
        return pid

    async def _run_local_executor(self, pid: str, program: Any, context: Optional[dict]):
        """本地执行包装器，负责更新 PCB"""
        try:
            # 在执行过程中实时更新 PC (模拟执行)
            # 实际需要修改 SemanticVM 以提供回调或 Hook
            result = await self.local_vm.execute_program(program.name, context)
            
            # 更新 PCB 状态
            if pid in self.processes:
                pcb = self.processes[pid]
                pcb.state = ProcessState.COMPLETED
                pcb.pc = len(program.instructions)
                pcb.update_time = datetime.now()
            
            self.results[pid] = result
        except Exception as e:
            if pid in self.processes:
                pcb = self.processes[pid]
                pcb.state = ProcessState.FAILED
                pcb.error = str(e)
            self.results[pid] = {"success": False, "error": str(e)}

    async def update_pcb(self, pid: str, pc: int, state: str = "running"):
        """接收节点报告的 PCB 更新 (Heartbeat/Progress)"""
        if pid in self.processes:
            pcb = self.processes[pid]
            pcb.pc = pc
            pcb.state = ProcessState(state)
            pcb.update_time = datetime.now()

    async def kill_process(self, pid: str):
        """杀死进程 (SIGKILL)"""
        if pid in self.processes:
            self.processes[pid].state = ProcessState.ZOMBIE
            # 实际应该发送 RPC 到对应节点停止执行
            return True
        return False

    async def get_process_list(self) -> list[SemanticProcess]:
        """获取进程列表"""
        # 清理旧僵尸进程
        now = datetime.now()
        active_processes = []
        for pid, pcb in list(self.processes.items()):
            # 超过 1 小时的完成/失败进程视为过时
            if pcb.state in [ProcessState.COMPLETED, ProcessState.FAILED, ProcessState.ZOMBIE]:
                if (now - pcb.update_time).total_seconds() > 3600:
                    del self.processes[pid]
                    continue
            active_processes.append(pcb)
        return active_processes
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
        url = f"http://{node.host}:{node.port}/execute"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"program": program.to_dict(), "context": context or {}}, timeout=5) as resp:
                    if resp.status == 200:
                        self.results[exec_id] = {"success": True, "message": "Program started on remote node"}
                    else:
                        self.results[exec_id] = {"success": False, "error": f"Failed to start on node: {resp.status}"}
        except Exception as e:
            self.results[exec_id] = {"success": False, "error": str(e)}
    
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
        from intentos.semantic_vm import SemanticVM
        self.local_vm = SemanticVM(llm_executor)
        
        self.memory = DistributedSemanticMemory()
        
        # 让 local_vm 使用分布式内存 (部分覆盖)
        # 注意：SemanticVM.memory 是 SemanticMemory 类型，
        # DistributedSemanticMemory 接口略有不同，但我们可以进行桥接
        self.local_vm.memory = self.memory
        
        # 替换为分布式处理器
        self.local_vm.processor = DistributedProcessor(llm_executor, self)
        
        self.coordinator = DistributedCoordinator(self.memory, self.local_vm)
        self.llm_executor = llm_executor
        
        # 本地节点
        self.local_node = VMNode(
            host="localhost",
            port=8000,
            capabilities=["CREATE", "MODIFY", "DELETE", "QUERY", "EXECUTE", "LOOP", "WHILE", "IF"],
        )
        
        # 本地服务器
        self.server = VMServer(self.local_node, self.local_vm)
        
        # 添加本地节点到集群
        self.memory.add_node(self.local_node)
    
    async def start(self):
        """启动本地节点服务器"""
        await self.server.start()
    
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
        """执行程序 (通过内核 fork)"""
        return await self.coordinator.fork_process(program, context)

    async def ps(self) -> list[SemanticProcess]:
        """获取进程列表 (System Call: ps)"""
        return await self.coordinator.get_process_list()

    async def kill(self, pid: str):
        """杀死进程 (System Call: kill)"""
        return await self.coordinator.kill_process(pid)

    async def get_execution_result(self, exec_id: str) -> Optional[dict]:
        """获取执行结果"""
        return self.coordinator.results.get(exec_id)


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


from intentos.semantic_vm import LLMProcessor, SemanticOpcode, SemanticMemory, SemanticInstruction

class DistributedProcessor(LLMProcessor):
    """
    分布式 LLM 处理器
    
    支持分布式语义指令 (REPLICATE, SPAWN, BROADCAST...)
    """
    
    def __init__(self, llm_executor: Any, cluster: DistributedSemanticVM):
        super().__init__(llm_executor)
        self.cluster = cluster
    
    async def execute(
        self,
        instruction: Union[SemanticInstruction, Any],
        memory: SemanticMemory,
    ) -> dict[str, Any]:
        """执行指令，支持分布式操作码"""
        
        # 处理分布式操作码
        opcode = instruction.opcode
        
        if isinstance(opcode, DistributedOpcode):
            return await self._execute_distributed(instruction, memory)
        
        # 处理基础操作码 (如果被标记为分布式)
        # 例如：BROADCAST CREATE ...
        
        return await super().execute(instruction, memory)
    
    async def _execute_distributed(self, instruction, memory) -> dict[str, Any]:
        opcode = instruction.opcode
        
        if opcode == DistributedOpcode.REPLICATE:
            # 复制数据到远程节点
            target = instruction.target
            name = instruction.target_name
            node_id = instruction.parameters.get("node")
            
            value = memory.get(target, name)
            if value:
                # 实际应该找到特定节点并设置
                # 简化为全局设置 (会自动哈希到对应节点)
                await self.cluster.memory.set(target, name, value)
                return {"success": True, "message": f"Replicated {target}:{name}"}
        
        elif opcode == DistributedOpcode.SPAWN:
            # 在新节点上生成程序
            target_name = instruction.target_name
            program = memory.get("PROGRAM", target_name)
            if program:
                exec_id = await self.cluster.execute_program(program, instruction.parameters.get("context"))
                return {"success": True, "exec_id": exec_id}
        
        elif opcode == DistributedOpcode.BROADCAST:
            # 广播修改到所有节点
            target = instruction.target
            name = instruction.target_name
            value = instruction.parameters.get("value")
            
            nodes = self.cluster.memory.get_active_nodes()
            for node in nodes:
                # 这里简化为直接调用远程设置
                await self.cluster.memory._remote_set(node, target, name, value)
            
            return {"success": True, "message": f"Broadcasted {target}:{name}"}
        
        return {"success": False, "error": f"Unsupported distributed opcode: {opcode}"}


# =============================================================================
# VM 节点服务器
# =============================================================================

class VMServer:
    """
    VM 节点服务器
    
    处理来自其他节点的 RPC 调用
    """
    
    def __init__(self, node: VMNode, vm: Any):
        self.node = node
        self.vm = vm
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        self.app.router.add_post("/memory/get", self._handle_get)
        self.app.router.add_post("/memory/set", self._handle_set)
        self.app.router.add_post("/memory/delete", self._handle_delete)
        self.app.router.add_post("/execute", self._handle_execute)
        self.app.router.add_get("/status", self._handle_status)
    
    async def _handle_get(self, request):
        data = await request.json()
        store, key = data.get("store"), data.get("key")
        value = self.vm.memory.get(store, key)
        return web.json_response({"value": value})
    
    async def _handle_set(self, request):
        data = await request.json()
        store, key, value = data.get("store"), data.get("key"), data.get("value")
        self.vm.memory.set(store, key, value)
        return web.json_response({"success": True})
    
    async def _handle_delete(self, request):
        data = await request.json()
        store, key = data.get("store"), data.get("key")
        success = self.vm.memory.delete(store, key)
        return web.json_response({"success": success})
    
    async def _handle_execute(self, request):
        data = await request.json()
        program_data = data.get("program")
        context = data.get("context", {})
        
        from intentos.semantic_vm import SemanticProgram
        program = SemanticProgram.from_dict(program_data)
        
        # 异步执行，不阻塞 HTTP 响应
        asyncio.create_task(self.vm.execute_program(program.name, context))
        
        return web.json_response({"success": True, "message": "Program execution started"})
    
    async def _handle_status(self, request):
        return web.json_response(self.node.to_dict())
    
    async def start(self):
        """启动服务器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.node.host, self.node.port)
        await site.start()
        print(f"VM Node {self.node.node_id} started on {self.node.host}:{self.node.port}")


# =============================================================================
# 便捷函数
# =============================================================================

def create_distributed_vm(llm_executor: Any = None) -> DistributedSemanticVM:
    """创建分布式语义 VM"""
    return DistributedSemanticVM(llm_executor)


def create_node(host: str, port: int, **kwargs) -> VMNode:
    """创建 VM 节点"""
    return VMNode(host=host, port=port, **kwargs)
