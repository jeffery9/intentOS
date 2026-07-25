# -*- coding: utf-8 -*-
"""
Integration tests for Phase 1 (Semantic Pipeline |) and Phase 2 (Daemon Runner).
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from intentos.core.singularity import IntentSingularity
from intentos.semantic_vm.vm import SemanticVM, SemanticProgram, SemanticInstruction, SemanticOpcode
from intentos.runtime.daemon import DaemonRunner, EventTrigger
from intentos.llm.backends.base import LLMResponse, LLMUsage


@pytest.mark.anyio
async def test_semantic_pipeline_and_daemon_integration():
    # 1. 初始化大脑（SemanticVM）与模拟环境
    # 使用 Mock 大脑执行器
    mock_llm_executor = AsyncMock()
    
    # 模拟四级级联：
    # ① 第一步阻抗匹配：将 Webhook 原始物理事件适配给第一步，返回空字典
    # ② 第一步 LLM 执行：解析遥测并返回 Processed: Telemetry_Value_42
    # ③ 第二步阻抗匹配：将第一步的散装输出适配给第二步，返回空字典
    # ④ 第二步 LLM 执行：总结管道，输出最终交付报告
    response_matcher_1 = LLMResponse(
        content='{}',
        model="mock-matcher-model",
        usage=LLMUsage(prompt_tokens=100, completion_tokens=10, total_tokens=110)
    )
    
    response_1 = LLMResponse(
        content='{"success": true, "content": "Processed: Telemetry_Value_42"}',
        model="mock-model",
        usage=LLMUsage(prompt_tokens=120, completion_tokens=50, total_tokens=170)
    )
    
    response_matcher_2 = LLMResponse(
        content='{}',
        model="mock-matcher-model",
        usage=LLMUsage(prompt_tokens=150, completion_tokens=10, total_tokens=160)
    )
    
    response_2 = LLMResponse(
        content='{"success": true, "content": "最终交付报告：系统状态极其健康，当前遥测参数 Telemetry_Value_42 已就位"}',
        model="mock-model",
        usage=LLMUsage(prompt_tokens=200, completion_tokens=80, total_tokens=280)
    )
    
    mock_llm_executor.execute.side_effect = [
        response_matcher_1, 
        response_1, 
        response_matcher_2, 
        response_2
    ]
    
    # 组装 VM
    vm = SemanticVM(llm_executor=mock_llm_executor, registry=MagicMock())
    await vm.initialize()
    
    # 2. 编织我们的 Pipeline 语义程序 (包含两级 EXECUTE 指令)
    program = SemanticProgram(name="telem_pipeline_program")
    
    # 步骤 A: 提取遥测
    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE,
        parameters={"intent": "解析原始报文并提取数值"}
    ))
    
    # 步骤 B: 总结成最终交付物 (此步骤将隐式继承步骤 A 的输出作为 _stdin 并追加到意图中)
    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE,
        parameters={"intent": "总结管道上下文并输出最终健康度报告"}
    ))
    
    await vm.load_program(program)
    
    # 3. 部署并驱动 DaemonRunner (运行引擎)
    daemon = DaemonRunner(vm=vm)
    
    # 模拟 Webhook 网卡队列输入
    mock_webhook_queue = []
    
    # 注册一个 Webhook 事件触发器，联动我们的流水线程序
    daemon.register_trigger(
        trigger_id="webhook_telemetry_event",
        trigger_type="webhook",
        config={
            "interval_seconds": 1,
            "_mock_webhook_queue": mock_webhook_queue,
            "gas_limit": 500,
            "assertions": ["output_must_be_positive"]
        },
        target_program="telem_pipeline_program"
    )
    
    # 开启事件循环监听
    await daemon.start()
    
    try:
        # 4. 物理事件爆发！网卡塞入 payload
        logger_mock = MagicMock()
        mock_webhook_queue.append({
            "sensor": "GPS_01",
            "raw_hex": "0x2A", # 十进制为 42
            "reason": "遥测器爆发 0x2A"
        })
        
        # 给事件循环充分的响应和串联坍缩执行时间
        await asyncio.sleep(1.2)
        
        # 5. 深度管道串联断言验证：
        # ① 第一步的 Standard Output（_last_result）必须成功被写入局部变量
        final_stdout = program.variables.get("_last_result")
        assert final_stdout is not None
        
        # ② 验证最终输出中，是否成功融入了第一步提取出的 "Telemetry_Value_42"
        # 这证明了：第一阶段提取的 STDOUT 成功流经管道，并作为 STDIN 精准注入给了第二阶段！
        assert "Telemetry_Value_42" in final_stdout
        assert "最终交付报告" in final_stdout
        
        # ③ 验证大模型是否被准确执行了 4 次 (第一步阻抗、第一步执行、第二步阻抗、第二步执行)
        assert mock_llm_executor.execute.call_count == 4
        
        # 验证第一步执行（第二次调用）的 intent
        first_call_prompt = mock_llm_executor.execute.call_args_list[1][0][0][1].content
        assert "解析原始报文并提取数值" in first_call_prompt
        
        # 核心断言 ➔ 验证第二步执行（第四次调用）的 intent 是否被隐式自动追加了管道上下文
        second_call_prompt = mock_llm_executor.execute.call_args_list[3][0][0][1].content
        assert "总结管道上下文并输出最终健康度报告" in second_call_prompt
        # 确认隐式注入了第一阶段的输出
        assert "管道输入: Processed: Telemetry_Value_42" in second_call_prompt
        
    finally:
        # 6. 安全休眠，杜绝资源泄漏
        await daemon.stop()
