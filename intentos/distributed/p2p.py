# -*- coding: utf-8 -*-
"""
IntentOS Distributed - Semantic P2P & Social Skill Transmission Layer

去中心化分布式语义 P2P 协议：
- 节点发现：全息节点的无感知广播发现
- 技能传染：新进化出的技能 Gossip 病毒式扩散，异步对齐整个集群的智商
- 意图接力：节点间管道指令弹性委托，算力/认知分担
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional, Union

from ..core.singularity import IntentSingularity
from ..skill.models import Skill
from ..skill.store import SkillStore

logger = logging.getLogger(__name__)


@dataclass
class P2PNode:
    """代表 P2P 活性邻居节点"""
    node_id: str
    host: str
    port: int
    last_seen: float = field(default_factory=time.time)
    skills_fingerprints: set[str] = field(default_factory=set)


class P2PNodeManager:
    """
    全息 P2P 节点路由表管理器 (路由大脑)
    """
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self.peers: dict[str, P2PNode] = {}
        self._lock = asyncio.Lock()

    async def register_peer(self, node_id: str, host: str, port: int, skill_ids: list[str]) -> P2PNode:
        """注册或更新邻居节点信息"""
        if node_id == self.local_node_id:
            return None  # 不注册自己
            
        async with self._lock:
            peer = self.peers.get(node_id)
            if not peer:
                peer = P2PNode(node_id=node_id, host=host, port=port)
                self.peers[node_id] = peer
                logger.info(f"[P2P] 🎯 发现新活性全息节点: {node_id} @ {host}:{port}")
            else:
                peer.last_seen = time.time()
                
            peer.skills_fingerprints = set(skill_ids)
            return peer

    async def remove_dead_peers(self, timeout_seconds: float = 5.0) -> list[str]:
        """清除失联节点"""
        current_time = time.time()
        dead_ids = []
        async with self._lock:
            for nid, peer in list(self.peers.items()):
                if current_time - peer.last_seen > timeout_seconds:
                    dead_ids.append(nid)
                    del self.peers[nid]
                    logger.warning(f"[P2P] ⚠️ 节点失联，移出路由表: {nid}")
        return dead_ids

    def get_peers_with_skill(self, skill_name: str) -> list[P2PNode]:
        """寻找拥有特定技能的节点候选列表"""
        candidates = []
        for peer in self.peers.values():
            if skill_name in peer.skills_fingerprints:
                candidates.append(peer)
        return candidates


class SemanticP2P:
    """
    语义 P2P 协议核心处理器
    """
    
    def __init__(self, local_node_id: str, host: str, port: int, vm: Any, skill_store: SkillStore):
        """
        Args:
            local_node_id: 本地节点唯一 ID
            host: 本地监听宿主地址
            port: 本地监听端口
            vm: 绑定的本地虚拟机大脑 (SemanticVM)
            skill_store: 本地技能物理存储
        """
        self.node_id = local_node_id
        self.host = host
        self.port = port
        self.vm = vm
        self.skill_store = skill_store
        
        self.node_manager = P2PNodeManager(local_node_id)
        self.is_running = False
        
        # 消息分流处理器表
        self._handlers: dict[str, Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]] = {
            "PING": self._handle_ping,
            "GOSSIP_SKILL": self._handle_gossip_skill,
            "INTENT_RELAY": self._handle_intent_relay,
        }
        
        # 单元测试高精度内存模拟总线 fallback (如果为 None，则走真实 Socket)
        self._mock_p2p_bus: Optional[dict[str, SemanticP2P]] = None

    def enable_mock_bus(self, bus: dict[str, SemanticP2P]) -> None:
        """使能模拟网络总线，用于单元测试在无网卡环境下的完美通关"""
        self._mock_p2p_bus = bus
        bus[self.node_id] = self

    async def start(self) -> None:
        """启动 P2P 服务端监听"""
        self.is_running = True
        logger.info(f"[P2P] 全息节点 {self.node_id} 语义网络接口启动于 {self.host}:{self.port}")
        # 在真实的 Socket 环境中，这里会运行 asyncio.start_server
        # 在 MOCK BUS 下，我们直接依靠 P2P 拓扑映射在内存中通信

    async def stop(self) -> None:
        """停止 P2P 服务"""
        self.is_running = False
        logger.info(f"[P2P] 全息节点 {self.node_id} 服务安全休眠")

    async def send_message(self, peer_host: str, peer_port: int, peer_node_id: str, msg: dict[str, Any]) -> dict[str, Any]:
        """向特定节点发送语义报文 (P2P Client)"""
        # 加签本地节点指纹
        msg["sender_id"] = self.node_id
        msg["sender_host"] = self.host
        msg["sender_port"] = self.port
        
        # ① 走高精度内存总线发送
        if self._mock_p2p_bus and peer_node_id in self._mock_p2p_bus:
            target_p2p = self._mock_p2p_bus[peer_node_id]
            if target_p2p.is_running:
                # 异步延迟，模拟网络报文震荡
                await asyncio.sleep(0.01)
                reply = await target_p2p.receive_message(msg)
                
                # 双向自动发现：如果接收端成功响应，发送端顺势将其注册进本地路由表
                if reply.get("success", False):
                    # 如果是 PONG 报文，拉取其返回的最新技能列表，否则默认空
                    peer_skills = reply.get("skills", [])
                    await self.node_manager.register_peer(
                        node_id=peer_node_id,
                        host=peer_host,
                        port=peer_port,
                        skill_ids=peer_skills
                    )
                return reply
            else:
                raise ConnectionError(f"物理节点失联: {peer_node_id}")
                
        # ② [未来扩展] 真实 TCP Socket 握手
        raise NotImplementedError("真实 Socket 握手待 PaaS 物理链路就位。目前采用极高精度的单元测试 Mock 网络总线。")

    async def receive_message(self, msg: dict[str, Any]) -> dict[str, Any]:
        """接收报文并分流解析 (P2P Server)"""
        sender_id = msg.get("sender_id")
        sender_host = msg.get("sender_host", "127.0.0.1")
        sender_port = msg.get("sender_port", 0)
        msg_type = msg.get("type", "UNKNOWN")
        
        # 在握手的同时，自动注册活性节点并心跳握手
        if sender_id:
            await self.node_manager.register_peer(
                node_id=sender_id,
                host=sender_host,
                port=sender_port,
                skill_ids=msg.get("sender_skills", [])
            )
            
        handler = self._handlers.get(msg_type)
        if handler:
            return await handler(msg)
            
        return {"success": False, "error": f"不合法的报文类型: {msg_type}"}

    # =============================================================================
    # 报文业务处理函数族
    # =============================================================================

    async def _handle_ping(self, msg: dict[str, Any]) -> dict[str, Any]:
        """PING 心跳报文，回复本地已载入的技能清单"""
        local_skills = [s.name for s in self.skill_store.list_skills()]
        return {
            "success": True, 
            "type": "PONG", 
            "node_id": self.node_id, 
            "skills": local_skills
        }

    async def _handle_gossip_skill(self, msg: dict[str, Any]) -> dict[str, Any]:
        """处理新收到的技能 Gossip (认知同步)"""
        raw_skill_data = msg.get("skill_data")
        if not raw_skill_data:
            return {"success": False, "error": "缺失技能载荷"}
            
        # 1. 免疫系统安全检测
        # (在此处可以对技能内容做静态安全沙箱断言，目前直接安全放行)
        try:
            skill = Skill.from_dict(raw_skill_data)
            logger.info(f"[P2P] 🧬 {self.node_id} 获得 Gossip 社会化认知传染 ➔ 技能: '{skill.name}'")
            
            # 2. 写入本地物理 SkillStore 达成智力对齐
            self.skill_store.save_skill(skill)
            return {"success": True, "node_id": self.node_id}
        except Exception as e:
            logger.error(f"[P2P] 技能认知传染落地失败: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_intent_relay(self, msg: dict[str, Any]) -> dict[str, Any]:
        """处理意图跨网接力请求 (算力/认知委托)"""
        program_data = msg.get("program_data")
        singularity_data = msg.get("singularity_data")
        
        if not program_data:
            return {"success": False, "error": "缺失要执行的语义程序"}
            
        try:
            # 延迟导入以防止循环引用
            from ..semantic_vm.vm import SemanticProgram
            
            # 1. 本地动态载入委托程序
            program = SemanticProgram.from_dict(program_data)
            await self.vm.load_program(program)
            
            # 2. 捕获第一因 Singularity
            singularity = IntentSingularity(**singularity_data) if singularity_data else None
            
            # 3. 本地大脑全速坍缩执行管道
            logger.info(f"[P2P] 🤝 {self.node_id} 接收到来自邻居的意图接力请求 ➔ 执行程序 '{program.name}'")
            result = await self.vm.execute_program(
                program_name=program.name,
                strategy="consultant"
            )
            
            # 4. 获取终态管道 STDOUT
            final_stdout = program.variables.get("_last_result")
            
            return {
                "success": result.get("success", False),
                "result": final_stdout,
                "vm_logs": result.get("results", []),
                "error": result.get("error")
            }
        except Exception as e:
            logger.error(f"[P2P] 意图接力失败: {e}")
            return {"success": False, "error": str(e)}

    # =============================================================================
    # P2P 主动出站请求函数族
    # =============================================================================

    async def broadcast_skill_gossip(self, skill: Skill) -> int:
        """
        [阶段 2] 全网 Gossip 广播高阶技能
        实现认知的社会化传播 (病毒式传染)
        """
        gossip_msg = {
            "type": "GOSSIP_SKILL",
            "skill_data": skill.to_dict(),
            "sender_skills": [s.name for s in self.skill_store.list_skills()]
        }
        
        success_nodes = 0
        logger.info(f"[P2P] 📢 {self.node_id} 启动网络 Gossip 广播 ➔ 开始传染技能 '{skill.name}'")
        
        # Gossip 算法：向路由表中的每个活性 peer 发送
        for peer_id, peer in list(self.node_manager.peers.items()):
            try:
                reply = await self.send_message(peer.host, peer.port, peer_id, gossip_msg)
                if reply.get("success", False):
                    success_nodes += 1
            except Exception as e:
                logger.warning(f"[P2P] 技能传染对节点 '{peer_id}' 宣告失败: {e}")
                
        logger.info(f"[P2P] Gossip 传播结束。成功将认知复制到了 {success_nodes} 个全息兄弟节点。")
        return success_nodes

    async def relay_intent(self, target_node_id: str, program: SemanticProgram, singularity: Optional[IntentSingularity] = None) -> dict[str, Any]:
        """
        [阶段 3] 意图跨网接力
        将本地难以吞噬的语义指令，跨物理边界委托给最擅长的全息兄弟执行。
        """
        peer = self.node_manager.peers.get(target_node_id)
        if not peer:
            raise ValueError(f"无法委托：目标节点 '{target_node_id}' 不在活性路由表中")
            
        relay_msg = {
            "type": "INTENT_RELAY",
            "program_data": program.to_dict(),
            "singularity_data": singularity.to_dict() if singularity else None,
            "sender_skills": [s.name for s in self.skill_store.list_skills()]
        }
        
        logger.info(f"[P2P] 🤝 {self.node_id} 启动跨网委托 ➔ 路由目标: {target_node_id} ➔ 管道程序: '{program.name}'")
        reply = await self.send_message(peer.host, peer.port, target_node_id, relay_msg)
        return reply
