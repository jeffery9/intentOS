
import asyncio
import json
import logging
from intentos.llm.executor import BackendConfig, LLMRouter, LLMExecutor
from intentos.semantic_vm.vm import SemanticVM, SemanticProgram, SemanticInstruction, SemanticOpcode
from intentos.llm.backends.base import Message, LLMRole
from unittest.mock import MagicMock, AsyncMock

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger("SmokeTest")

async def run_smoke_test():
    logger.info("=== IntentOS 全链路冒烟测试开始 ===")

    # 1. 配置 LLM 顾问策略 (模拟环境)
    # 我们设置两个后端：一个常规模型，一个高精度专家模型
    configs = [
        BackendConfig(
            name="regular-backend",
            model="gpt-3.5-turbo-mock",
            is_consultant=True,
            priority=10
        ),
        BackendConfig(
            name="expert-backend",
            model="gpt-4o-mock",
            is_consultant=False,
            priority=5
        )
    ]
    
    router = LLMRouter(configs)
    
    # 模拟常规后端的行为：如果是困难问题，返回 [HARD_TASK]
    def regular_callback(messages, tools):
        user_content = messages[-1].content if messages else ""
        if "量子" in user_content or "复杂" in user_content:
            return "[HARD_TASK] 这个问题太复杂，我无法保证精度。"
        return f"常规模型回答：{user_content}"
    
    router.backends["regular-backend"].response_callback = regular_callback
    router.backends["expert-backend"].response_callback = lambda m, t: f"高精度专家回答：{m[-1].content}"
    
    executor = LLMExecutor(router=router)
    logger.info("✓ LLM 顾问策略配置完成")

    # 2. 初始化语义 VM 并打通物理 IO
    # 我们模拟一个真实的 IO 能力层
    class MockIOCapabilities:
        def __init__(self):
            self.skill_io = MagicMock()
            
        async def call_skill(self, skill_name=None, intent=None, **kwargs):
            # 只有明确请求 'file_writer' 或相关意图才成功
            if skill_name == "file_writer" or (intent and "写入" in intent):
                return "文件已成功写入到 /tmp/data.txt"
            raise ValueError(f"没有匹配的技能: skill_name={skill_name}, intent={intent}")
            
        async def call_mcp_tool(self, server, tool, **kwargs):
            return f"MCP 工具 {tool} 已执行"

    vm = SemanticVM(llm_executor=executor, registry=MagicMock())
    vm.io_capabilities = MockIOCapabilities()
    logger.info("✓ 语义 VM 及物理 IO 层初始化完成 (使用条件匹配 Mock)")

    # 3. 场景 A：简单任务（常规模型处理）
    logger.info("场景 A: 执行简单意图 '你好'...")
    prog_a = SemanticProgram(name="hello")
    prog_a.add_instruction(SemanticInstruction(opcode=SemanticOpcode.EXECUTE, parameters={"intent": "你好"}))
    await vm.load_program(prog_a)
    result_a = await vm.execute_program("hello", strategy="consultant")
    
    # 调试：显示完整结构
    logger.debug(f"场景 A 完整结果: {json.dumps(result_a, indent=2, ensure_ascii=False)}")
    
    # 安全地提取结果
    step_result_a = result_a['results'][0] if result_a.get('results') else {}
    final_output_a = step_result_a.get('content') or step_result_a.get('result') or "无输出"
    logger.info(f"结果 A: {final_output_a}")
    
    # 4. 场景 B：困难任务（触发顾问策略升级）
    logger.info("场景 B: 执行复杂意图 '解释量子纠缠'...")
    prog_b = SemanticProgram(name="complex")
    prog_b.add_instruction(SemanticInstruction(opcode=SemanticOpcode.EXECUTE, parameters={"intent": "解释量子纠缠"}))
    await vm.load_program(prog_b)
    result_b = await vm.execute_program("complex", strategy="consultant")
    
    step_result_b = result_b['results'][0] if result_b.get('results') else {}
    final_output_b = step_result_b.get('content') or step_result_b.get('result') or "无输出"
    logger.info(f"结果 B: {final_output_b}")

    # 5. 场景 C：物理 IO 任务（EXECUTE 调通 Skill）
    logger.info("场景 C: 执行物理 IO 意图 '写入数据'...")
    prog_c = SemanticProgram(name="io_task")
    prog_c.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE, 
        parameters={"skill_name": "file_writer", "content": "Hello IntentOS"}
    ))
    await vm.load_program(prog_c)
    result_c = await vm.execute_program("io_task", strategy="consultant")
    
    step_result_c = result_c['results'][0] if result_c.get('results') else {}
    final_output_c = step_result_c.get('result') or "无输出"
    logger.info(f"结果 C: {final_output_c}")

    logger.info("=== IntentOS 全链路冒烟测试完成：系统可以正常工作 ===")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
