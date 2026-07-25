# -*- coding: utf-8 -*-
"""
Unit test for Phase 1: Implicit Impedance Matching (万能语义阻抗匹配器)
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from intentos.semantic_vm.vm import SemanticVM, SemanticProgram, SemanticInstruction, SemanticOpcode
from intentos.llm.backends.base import LLMResponse, LLMUsage


@pytest.mark.anyio
async def test_implicit_impedance_matching():
    # 1. 模拟大模型处理器
    # 在这个 Pipeline 中，只有第二步的“阻抗适配器”会叩响大模型，将第一步的物理输出翻译成强类型 JSON。
    mock_llm_executor = AsyncMock()
    
    # 模拟 _match_impedance 输入散装文本，输出完美适配的强类型参数 JSON
    response_matcher = LLMResponse(
        content='{"revenue_amount": 1200000, "currency": "USD"}',
        model="mock-matcher-model",
        usage=LLMUsage(prompt_tokens=150, completion_tokens=40, total_tokens=190)
    )
    
    mock_llm_executor.execute.side_effect = [response_matcher]
    
    # 2. 模拟物理 IO 注册中心
    mock_registry = MagicMock()
    vm = SemanticVM(llm_executor=mock_llm_executor, registry=mock_registry)
    await vm.initialize()
    
    # 模拟物理 IO 执行处理器 (call_skill)
    # 第一步调用：返回原始散装非结构化文本
    # 第二步调用：返回物理 Skill 执行成功执勤
    mock_skill_handler = AsyncMock()
    mock_skill_handler.side_effect = [
        "分析结论: 项目真实营收为 120 万美元，币种为 USD",  # 第一步输出
        "Physical Skill Run Success"                       # 第二步输出
    ]
    vm.io_capabilities.skill_io = MagicMock()
    vm.io_capabilities.skill_io.skill_io_handler = mock_skill_handler
    
    # 3. 编织阻抗不对称 Pipeline 程序
    program = SemanticProgram(name="asymmetric_io_pipeline")
    
    # 第一步: 产生原始非结构化 Output
    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE,
        parameters={"intent": "第一阶段散装提取"}
    ))
    
    # 第二阶段: 调用特定物理技能 (不带具体参数，指望通过管道隐式 STDIN 与阻抗对齐提取出强类型参数)
    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE,
        parameters={
            "skill_name": "record_revenue_service",
            "tag": "financial" # 预置一个硬编码基础入参
        }
    ))
    
    await vm.load_program(program)
    
    # 4. 全速运转语义虚拟机
    result = await vm.execute_program(program_name="asymmetric_io_pipeline")
    
    # 5. 深度断言：
    # ① 程序执行完全成功
    assert result["success"] is True
    
    # ② 验证物理 Skill 层是否被成功触发了 2 次 (第一步和第二步各一次)
    assert mock_skill_handler.call_count == 2
    
    # ③ 终极断言：验证第二步物理 Skill 层收到的入参是否经过了「智能阻抗对齐」！
    # 提取第二次调用的 kwargs 参数
    called_kwargs = mock_skill_handler.call_args_list[1].kwargs
    
    # 验证散装文本 ➔ 智能转为了 `revenue_amount=1200000` (int) 并且 `currency="USD"`
    assert called_kwargs.get("revenue_amount") == 1200000
    assert called_kwargs.get("currency") == "USD"
    
    # 验证原有硬编码参数没有丢失 (对齐保留)
    assert called_kwargs.get("tag") == "financial"
    
    # 验证 P2P 及管道注入标记 _stdin 已带入
    assert "_stdin" in called_kwargs
