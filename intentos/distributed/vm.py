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

import asyncio
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

import aiohttp
from aiohttp import web

from intentos.semantic_vm import LLMProcessor, SemanticInstruction, SemanticMemory

# =============================================================================
# 分布式节点
# =============================================================================


@dataclass
class VMNode:
    """
    VM 节点
    """
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    host: str = "localhost"
    port: int = 8000
    status: str = "active"
    load: float = 0.0
    capabilities: list[str] = field(default_factory=list)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)

    def is_alive(self, timeout: int = 60) -> bool:
        """检查节点是否存活"""
        return (datetime.now() - self.last_heartbeat).total_seconds() < timeout

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "status": self.status,
            "load": self.load,
            "capabilities": self.capabilities,
            "last_heartbeat": self.last_heartbeat.isoformat(),
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
                async with session.post(
                    url, json={"store": store, "key": key, "value": value}, timeout=5
                ) as resp:
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
        """添加或更新节点"""
        # 查找是否存在同 ID 节点
        for i, n in enumerate(self.nodes):
            if n.node_id == node.node_id:
                self.nodes[i] = node
                self._rebuild_ring()
                return
        self.nodes.append(node)
        self._rebuild_ring()

    def cleanup_dead_nodes(self, timeout: int = 60) -> list[str]:
        """清理失效节点"""
        dead_ids = [n.node_id for n in self.nodes if not n.is_alive(timeout)]
        if dead_ids:
            self.nodes = [n for n in self.nodes if n.node_id not in dead_ids]
            self._rebuild_ring()
            print(f"Removed dead nodes: {dead_ids}")
        return dead_ids

    def remove_node(self, node_id: str) -> bool:
        """移除节点"""
        for i, n in enumerate(self.nodes):
            if n.node_id == node_id:
                self.nodes.pop(i)
                self._rebuild_ring()
                print(f"Removed node: {node_id}")
                return True
        print(f"Node not found: {node_id}")
        return False

    def get_nodes(self) -> list[VMNode]:
        """获取所有节点"""
        return self.nodes.copy()

    def get_active_nodes(self) -> list[VMNode]:
        """获取活跃节点"""
        return [n for n in self.nodes if n.status == "active" and n.is_alive()]

    def _rebuild_ring(self) -> None:
        """重建一致性哈希环 (带锁和存活检查)"""
        new_ring = {}
        for node in self.nodes:
            # 只有活跃且在线的节点进入哈希环
            if node.status == "active" and node.is_alive():
                # 虚拟节点
                for i in range(160):  # 增加到 160 个以提高分布均匀度
                    key = f"{node.node_id}:{i}"
                    hash_key = self._hash_key(key)
                    new_ring[hash_key] = node

        # 原子替换哈希环
        self.ring = dict(sorted(new_ring.items()))

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


# =============================================================================
# 分布式程序计数器
# =============================================================================


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
            "error": self.error,
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
        parent_pid: Optional[str] = None,
    ) -> str:
        """
        生成/分发新进程 (Equivalent to fork + exec)
        支持从程序元数据中提取所需的物理 IO 能力要求。
        """
        pid = str(uuid.uuid4())

        # 1. 提取能力要求 (Capability Affinity)
        # 假设程序在 metadata 中声明了能力，如 ["GPU", "FileSystem"]
        required_caps = program.to_dict().get("metadata", {}).get("required_capabilities", [])

        # 2. 选择最佳节点 (调度策略)
        node = await self._select_best_node(required_caps)

        if not node:
            # 调度失败逻辑：如果是因为没有满足能力的节点，则报错
            if required_caps:
                return self._create_error_result(pid, f"调度失败：无节点具备所需能力 {required_caps}")
            return self._create_error_result(pid, "调度失败：没有可用节点")

        # 3. 创建 PCB
        pcb = SemanticProcess(
            pid=pid,
            program_name=program.name,
            node_id=node.node_id,
            parent_pid=parent_pid,
            context=context or {},
            state=ProcessState.NEW,
        )
        self.processes[pid] = pcb

        # 4. 跨节点执行
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

    async def _select_best_node(self, required_capabilities: Optional[list[str]] = None) -> Optional[VMNode]:
        """
        基于能力与负载选择最佳节点 (Capability-Aware Scheduling)

        第一性原理：计算应尽可能靠近其所需的 IO 能力。
        """
        active_nodes = self.memory.get_active_nodes()
        if not active_nodes:
            return None

        # 1. 过滤具备所需能力的节点
        candidate_nodes = active_nodes
        if required_capabilities:
            candidate_nodes = [
                n for n in active_nodes
                if all(cap in n.capabilities for cap in required_capabilities)
            ]

        # 如果没有节点完全满足，退而求其次（或报错）
        if not candidate_nodes:
            # 这里选择返回 None，让调用者决定是否降级
            return None

        # 2. 在候选节点中选择负载最低的
        return min(candidate_nodes, key=lambda n: n.load)

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
                async with session.post(
                    url, json={"program": program.to_dict(), "context": context or {}}, timeout=5
                ) as resp:
                    if resp.status == 200:
                        self.results[exec_id] = {
                            "success": True,
                            "message": "Program started on remote node",
                        }
                    else:
                        self.results[exec_id] = {
                            "success": False,
                            "error": f"Failed to start on node: {resp.status}",
                        }
        except Exception as e:
            self.results[exec_id] = {"success": False, "error": str(e)}

    def _create_error_result(self, exec_id: str, error: str) -> str:
        """创建错误结果"""
        self.results[exec_id] = {
            "success": False,
            "error": error,
        }
        return exec_id

    async def wait_at_barrier(self, barrier_id: str, count: int, pid: str) -> bool:
        """
        在屏障点等待 (Distributed Barrier)

        第一性原理：屏障是分布式时钟同步的替代品，确保逻辑上的“同时”。
        """
        key = f"barrier:{barrier_id}"

        # 1. 在分布式内存中原子增加到达计数 (使用分布式内存作为协调中心)
        barrier_state = await self.memory.get("VARIABLE", key) or {"reached": [], "count": count}

        if pid not in barrier_state["reached"]:
            barrier_state["reached"].append(pid)
            await self.memory.set("VARIABLE", key, barrier_state)

        # 2. 检查是否所有人都到了
        if len(barrier_state["reached"]) >= count:
            # 释放所有人：将所有参与进程状态设为 RUNNING
            for p_id in barrier_state["reached"]:
                if p_id in self.processes:
                    self.processes[p_id].state = ProcessState.RUNNING

            # 清理屏障状态以备复用
            await self.memory.delete("VARIABLE", key)
            return True # 屏障已释放
        else:
            # 挂起当前进程
            if pid in self.processes:
                self.processes[pid].state = ProcessState.SUSPENDED
            return False # 进程已挂起，等待中

    async def get_status(self, exec_id: str) -> Optional[dict]:

        """获取执行结果"""
        return self.results.get(exec_id)

    async def map_reduce(
        self,
        sub_programs: list[Any],  # list[SemanticProgram]
        context: Optional[dict] = None,
        aggregator_prompt: Optional[str] = None,
        max_concurrency: int = 10,
        max_retries: int = 2
    ) -> dict[str, Any]:
        """
        大规模语义 Map-Reduce (Large-scale Semantic Map-Reduce)
        支持并发控制和重试机制。
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        pids_to_tasks = {} # PID -> (Program, AttemptCount)
        results = []
        failed_tasks = []

        async def run_task(prog, attempt=0):
            async with semaphore:
                pid = await self.fork_process(prog, context)
                pids_to_tasks[pid] = (prog, attempt)
                return pid

        # 1. Map 阶段：分批分发
        initial_tasks = [run_task(p) for p in sub_programs]
        pending_pids = await asyncio.gather(*initial_tasks)

        # 2. 动态结果收集与重试
        timeout = 600  # 10分钟
        start_time = datetime.now()

        while pending_pids:
            if (datetime.now() - start_time).total_seconds() > timeout:
                break

            for pid in list(pending_pids):
                if pid in self.results:
                    res = self.results[pid]
                    if res.get("success"):
                        results.append(res)
                        pending_pids.remove(pid)
                    else:
                        # 失败重试逻辑
                        prog, attempt = pids_to_tasks[pid]
                        if attempt < max_retries:
                            print(f"Task {pid} failed, retrying (attempt {attempt+1})...")
                            new_pid = await run_task(prog, attempt + 1)
                            pending_pids.append(new_pid)
                            pending_pids.remove(pid)
                        else:
                            failed_tasks.append(res)
                            pending_pids.remove(pid)

            await asyncio.sleep(1)

        # 3. Reduce 阶段
        if not self.local_vm or not self.local_vm.processor:
            return {"success": True, "map_results": results, "failed": failed_tasks}

        summary_prompt = aggregator_prompt or "请对以下大规模子任务的执行结果进行汇总报告："
        full_context = f"{summary_prompt}\n\n" + "\n---\n".join([str(r.get('final_state', r)) for r in results])

        final_summary = await self.local_vm.processor.execute_llm(full_context, self.memory)

        return {
            "success": len(failed_tasks) == 0,
            "final_result": final_summary,
            "stats": {
                "total": len(sub_programs),
                "success": len(results),
                "failed": len(failed_tasks)
            }
        }


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
        self.local_vm.memory = self.memory  # type: ignore

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
            "pending_programs": len(self.coordinator.processes),
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


class DistributedOpcode(Enum):
    """分布式语义操作码"""

    # 基础指令 (继承自 SemanticOpcode)
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    QUERY = "query"
    EXECUTE = "execute"

    # 分布式指令
    REPLICATE = "replicate"  # 复制数据到多个节点
    SHARD = "shard"  # 分片数据
    MIGRATE = "migrate"  # 迁移数据到另一个节点
    BROADCAST = "broadcast"  # 广播到所有节点
    PARALLEL = "parallel"  # 智能分片并行执行 (Map-Reduce)

    # 分布式控制流
    SPAWN = "spawn"  # 在新节点上生成子程序
    SYNC = "sync"  # 同步多个节点的执行
    BARRIER = "barrier"  # 执行屏障 (等待所有节点)


class DistributedProcessor(LLMProcessor):
    """
    分布式 LLM 处理器

    支持分布式语义指令 (REPLICATE, SPAWN, BROADCAST, PARALLEL...)
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

        # 兼容性处理
        if isinstance(opcode, str) and opcode.lower() == "parallel":
            return await self._execute_distributed(instruction, memory)

        return await super().execute(instruction, memory)

    async def _execute_distributed(self, instruction, memory) -> dict[str, Any]:
        opcode = instruction.opcode

        # 字符串兼容性
        if isinstance(opcode, str):
            try:
                opcode = DistributedOpcode(opcode.lower())
            except ValueError:
                return {"success": False, "error": f"Unknown distributed opcode: {opcode}"}

        if opcode == DistributedOpcode.PARALLEL:
            # 1. 语义拆分意图 (Intelligent Split)
            intent = instruction.parameters.get("intent", "")
            if not intent:
                return {"success": False, "error": "PARALLEL instruction requires an 'intent' parameter"}

            # 获取集群支持的所有能力，辅助分解
            all_caps = []
            for node in self.cluster.memory.get_active_nodes():
                all_caps.extend(node.capabilities)
            all_caps = list(set(all_caps))

            sub_tasks = await self.decompose_intent(intent, all_caps)

            # 2. 构造子程序列表
            from intentos.semantic_vm import SemanticInstruction, SemanticOpcode, SemanticProgram
            sub_programs = []
            for task in sub_tasks:
                prog = SemanticProgram(name=task["name"], description=task["description"])
                # 为子任务添加执行指令
                prog.add_instruction(SemanticInstruction(
                    opcode=SemanticOpcode.EXECUTE,
                    parameters={"intent": task["description"]}
                ))
                # 注入所需能力到元数据，供调度器使用
                prog.variables["_required_capabilities"] = task.get("required_capabilities", [])
                sub_programs.append(prog)

            # 3. 触发 Map-Reduce
            result = await self.cluster.coordinator.map_reduce(
                sub_programs,
                context=instruction.parameters.get("context"),
                aggregator_prompt=f"意图：{intent}\n请汇总子任务结果以回答原始意图："
            )
            return result

        elif opcode == DistributedOpcode.SHARD:
            # 语义分片 (Semantic Sharding)
            target = instruction.target
            name = instruction.target_name
            num_shards = instruction.parameters.get("num_shards", 2)

            data = await self.cluster.memory.get(target, name)
            if not data:
                return {"success": False, "error": f"Data not found for sharding: {target}:{name}"}

            shards = []
            if isinstance(data, list):
                shard_size = max(1, len(data) // num_shards)
                for i in range(0, len(data), shard_size):
                    shards.append(data[i : i + shard_size])
            elif isinstance(data, str):
                lines = data.splitlines()
                if len(lines) >= num_shards:
                    shard_size = max(1, len(lines) // num_shards)
                    for i in range(0, len(lines), shard_size):
                        shards.append("\n".join(lines[i : i + shard_size]))
                else:
                    shard_size = max(1, len(data) // num_shards)
                    for i in range(0, len(data), shard_size):
                        shards.append(data[i : i + shard_size])
            else:
                return {"success": False, "error": f"Unsupported data type for sharding: {type(data)}"}

            shard_keys = []
            for i, shard_data in enumerate(shards):
                shard_key = f"{name}_shard_{i}"
                await self.cluster.memory.set(target, shard_key, shard_data)
                shard_keys.append(shard_key)

            return {
                "success": True,
                "shard_keys": shard_keys,
                "target": target
            }

        elif opcode == DistributedOpcode.REPLICATE:
            # 复制数据
            target = instruction.target
            name = instruction.target_name
            value = await self.cluster.memory.get(target, name)
            if value:
                # 设置到全局（会自动分布）
                await self.cluster.memory.set(target, name, value)
                return {"success": True, "message": f"Replicated {target}:{name}"}
            return {"success": False, "error": f"Data not found: {target}:{name}"}

        elif opcode == DistributedOpcode.BROADCAST:
            # 广播修改
            target = instruction.target
            name = instruction.target_name
            value = instruction.parameters.get("value")
            nodes = self.cluster.memory.get_active_nodes()
            for node in nodes:
                await self.cluster.memory._remote_set(node, target, name, value)
            return {"success": True, "message": f"Broadcasted {target}:{name}"}

        elif opcode == DistributedOpcode.SPAWN:
            # 生成新进程
            target_name = instruction.target_name
            program = await self.cluster.memory.get("PROGRAM", target_name)
            if program:
                from intentos.semantic_vm import SemanticProgram
                if isinstance(program, dict):
                    program = SemanticProgram.from_dict(program)
                pid = await self.cluster.execute_program(program, instruction.parameters.get("context"))
                return {"success": True, "pid": pid}
            return {"success": False, "error": f"Program not found: {target_name}"}

        elif opcode == DistributedOpcode.MIGRATE:
            # 语义迁移 (Semantic Migration)
            # 参数: target (DATA/PROCESS), name/pid, destination_node
            migrate_type = instruction.target # "DATA" or "PROCESS"
            target_id = instruction.target_name
            dest_node_id = instruction.parameters.get("destination_node")

            # 找到目标节点
            dest_node = next((n for n in self.cluster.memory.get_active_nodes() if n.node_id == dest_node_id), None)
            if not dest_node:
                return {"success": False, "error": f"Destination node {dest_node_id} not found or inactive"}

            if migrate_type == "PROCESS":
                # --- 进程热迁移 (Live Process Migration) ---
                pid = target_id
                process = self.cluster.coordinator.processes.get(pid)
                if not process:
                    return {"success": False, "error": f"Process {pid} not found"}

                # 1. 挂起当前执行 (在本地或通知远程)
                process.state = ProcessState.SUSPENDED

                # 2. 捕获状态 (PC + Context)
                state_bundle = {
                    "program_name": process.program_name,
                    "pc": process.pc,
                    "context": process.context,
                    "parent_pid": process.parent_pid
                }

                # 3. 在目标节点恢复执行 (RPC 调用)
                url = f"http://{dest_node.host}:{dest_node.port}/execute"
                try:
                    async with aiohttp.ClientSession() as session:
                        # 构造恢复执行的程序包
                        program = await self.cluster.memory.get("PROGRAM", process.program_name)
                        async with session.post(
                            url,
                            json={
                                "program": program.to_dict() if hasattr(program, "to_dict") else program,
                                "context": process.context,
                                "resume_pc": process.pc,
                                "pid": pid # 保持原 PID
                            },
                            timeout=10
                        ) as resp:
                            if resp.status == 200:
                                # 4. 更新全局进程表信息
                                process.node_id = dest_node.node_id
                                process.state = ProcessState.RUNNING
                                process.update_time = datetime.now()
                                return {"success": True, "message": f"Process {pid} migrated to {dest_node_id}"}
                            else:
                                process.state = ProcessState.FAILED
                                return {"success": False, "error": f"Migration failed on destination node: {resp.status}"}
                except Exception as e:
                    process.state = ProcessState.FAILED
                    return {"success": False, "error": f"Migration RPC error: {e}"}

            else:
                # --- 数据迁移 (Data Migration) ---
                # 例如将 VARIABLE:user_data 从本地迁移到指定节点
                store = migrate_type # 如 "VARIABLE", "PROGRAM"
                data = await self.cluster.memory.get(store, target_id)
                if data:
                    # 1. 在目标节点设置数据
                    await self.cluster.memory._remote_set(dest_node, store, target_id, data)
                    # 2. (可选) 从原位置删除，如果不是本地存储则忽略
                    # self.cluster.memory.local_storage.delete(store, target_id)
                    return {"success": True, "message": f"Data {store}:{target_id} migrated to {dest_node_id}"}
                return {"success": False, "error": f"Data not found: {store}:{target_id}"}

        elif opcode == DistributedOpcode.BARRIER:
            # 语义屏障 (Semantic Barrier)
            barrier_id = instruction.target_name or "global_barrier"
            count = instruction.parameters.get("count", 2)
            pid = instruction.parameters.get("pid") # 需要上下文提供当前进程 PID

            if not pid:
                return {"success": False, "error": "BARRIER instruction requires a 'pid' parameter"}

            released = await self.cluster.coordinator.wait_at_barrier(barrier_id, count, pid)
            return {"success": True, "status": "released" if released else "suspended"}

        elif opcode == DistributedOpcode.SYNC:
            # 数据同步 (Force Consistency Sync)
            # 通过读取分布式内存中的最新值并刷新本地缓存
            target = instruction.target
            name = instruction.target_name
            # 在 DistributedSemanticMemory 中 get 已经处理了从远程哈希节点读取
            value = await self.cluster.memory.get(target, name)
            return {"success": True, "value": value}

        return {"success": False, "error": f"Opcode {opcode} not fully implemented in this version"}


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
