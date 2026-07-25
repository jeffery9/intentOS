# -*- coding: utf-8 -*-
"""
Unit and integration tests for Distributed Semantic P2P & Social Skill Transmission.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from intentos.skill import Skill, SkillTrigger
from intentos.core.singularity import IntentSingularity
from intentos.semantic_vm.vm import SemanticVM, SemanticProgram, SemanticInstruction, SemanticOpcode
from intentos.distributed import SemanticP2P, P2PNode, P2PNodeManager
from intentos.llm.backends.base import LLMResponse, LLMUsage


class MockSkillStore:
    """Mock 的物理技能存储，记录写盘动作"""
    def __init__(self):
        self.skills = {}

    def list_skills(self):
        return list(self.skills.values())

    def save_skill(self, skill):
        self.skills[skill.name] = skill


@pytest.mark.anyio
async def test_distributed_p2p_full_lifecycle():
    # =============================================================================
    # 0. 初始化两个完全隔离的全息节点 Node_A 和 Node_B
    # =============================================================================
    mock_llm_a = AsyncMock()
    mock_llm_b = AsyncMock()
    
    vm_a = SemanticVM(llm_executor=mock_llm_a, registry=MagicMock())
    vm_b = SemanticVM(llm_executor=mock_llm_b, registry=MagicMock())
    await vm_a.initialize()
    await vm_b.initialize()
    
    store_a = MockSkillStore()
    store_b = MockSkillStore()
    
    # 构建 P2P 实例
    p2p_a = SemanticP2P(local_node_id="Node_A", host="127.0.0.1", port=9001, vm=vm_a, skill_store=store_a)
    p2p_b = SemanticP2P(local_node_id="Node_B", host="127.0.0.1", port=9002, vm=vm_b, skill_store=store_b)
    
    # 建立虚拟拓扑网络总线 (测试环境下 100% 稳定的无网卡沙箱)
    mock_network_bus = {}
    p2p_a.enable_mock_bus(mock_network_bus)
    p2p_b.enable_mock_bus(mock_network_bus)
    
    # 双机启动监听
    await p2p_a.start()
    await p2p_b.start()
    
    try:
        # =============================================================================
        # 1. 验证阶段 1: 节点发现与 PING/PONG 握手
        # =============================================================================
        ping_msg = {"type": "PING"}
        # Node_A 主动投递心跳报文给 Node_B
        reply = await p2p_a.send_message(
            peer_host="127.0.0.1", 
            peer_port=9002, 
            peer_node_id="Node_B", 
            msg=ping_msg
        )
        
        # 验证回复报文的正确性
        assert reply["success"] is True
        assert reply["type"] == "PONG"
        assert reply["node_id"] == "Node_B"
        
        # 验证 Node_A 路由大脑（P2PNodeManager）是否已经自发捕捉并注册了 Node_B
        peer_node = p2p_a.node_manager.peers.get("Node_B")
        assert peer_node is not None
        assert peer_node.host == "127.0.0.1"
        assert peer_node.port == 9002
        
        # =============================================================================
        # 2. 验证阶段 2: 社会化认知传染 (Gossip Skill)
        # =============================================================================
        # Node_A 独家进化出一个高级安全守卫技能
        evolved_skill = Skill(
            id="cyber_security_guardian",
            name="cyber_security_guardian",
            description="网络边界溢出自动熔断与流量免疫清洗技能",
            trigger=SkillTrigger(intent_pattern="拦截网络攻击并清洗"),
            steps=[],
            tags=["distributed", "security"]
        )
        store_a.save_skill(evolved_skill)
        
        # 开始 Gossip 广播，让高阶思想在空气中流动！
        infected_count = await p2p_a.broadcast_skill_gossip(evolved_skill)
        
        # 验证是否成功传染到了 Node_B
        assert infected_count == 1
        
        # 深入 Node_B 本地物理存盘进行深度断言
        node_b_skills = store_b.list_skills()
        assert len(node_b_skills) == 1
        assert node_b_skills[0].name == "cyber_security_guardian"
        assert node_b_skills[0].description == "网络边界溢出自动熔断与流量免疫清洗技能"
        
        # =============================================================================
        # 3. 验证阶段 3: 意图分布式接力 (Intent Relay / Delegation)
        # =============================================================================
        # Node_A 有一个复杂的任务管道，决定委托给此时处于空闲态的 Node_B 执行。
        # 构造要执行的程序
        program = SemanticProgram(name="cross_network_pipeline")
        program.add_instruction(SemanticInstruction(
            opcode=SemanticOpcode.EXECUTE,
            parameters={"intent": "执行高带宽安全审计清洗"}
        ))
        
        # Mock Node_B 大脑的 LLM 响应
        response_data = LLMResponse(
            content='{"success": true, "content": "Node_B 清洗完毕：拦截 5 个 SQL 注入，系统完全复原。"}',
            model="mock-expert-model",
            usage=LLMUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80)
        )
        mock_llm_b.execute.return_value = response_data
        
        # 组装第一推动力
        singularity = IntentSingularity(
            singularity_id="singularity_relay_12345",
            raw_intent="跨物理网络净化 Node_A 的通信信道"
        )
        
        # Node_A 发起跨网接力，物理投递给 Node_B
        relay_result = await p2p_a.relay_intent(
            target_node_id="Node_B",
            program=program,
            singularity=singularity
        )
        
        # 验证 Node_B 远端坍缩执行后的回执结果
        assert relay_result["success"] is True
        # 确认 Node_A 拿到了 Node_B 的 Standard Output (Result)
        assert "Node_B 清洗完毕" in relay_result["result"]
        
        # 验证 Node_B 的大模型确实被远程激活并工作了 1 次
        assert mock_llm_b.execute.call_count == 1
        
    finally:
        # 双机安全退役
        await p2p_a.stop()
        await p2p_b.stop()
