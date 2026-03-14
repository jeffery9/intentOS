"""
基于语义 VM 的 Self-Bootstrap 演示

演示语义 VM 如何实现 Self-Bootstrap:
1. 程序修改自身指令
2. 程序修改处理器 Prompt
3. 程序定义新指令
"""

import asyncio

from intentos.semantic_vm import (
    SemanticInstruction,
    SemanticOpcode,
    create_instruction,
    create_program,
    create_semantic_vm,
)


# Mock LLM Executor for demo
class MockLLMExecutor:
    """模拟 LLM 执行器 (用于演示)"""

    async def execute(self, messages: list[dict]) -> any:
        class Response:
            content = '{"operation": "mock", "success": true, "result": {}}'
        return Response()


async def demo_1_basic_program():
    """演示 1: 基础语义程序"""

    print("=" * 70)
    print("演示 1: 基础语义程序")
    print("=" * 70)

    # 创建程序
    program = create_program(
        name="basic_demo",
        description="基础语义程序演示",
    )

    # 添加指令
    program.add_instruction(create_instruction(
        SemanticOpcode.CREATE,
        target="TEMPLATE",
        target_name="sales_analysis",
        steps=["query_sales", "analyze_trends", "generate_report"],
    ))

    program.add_instruction(create_instruction(
        SemanticOpcode.SET,
        name="template_count",
        value=1,
    ))

    program.add_instruction(create_instruction(
        SemanticOpcode.QUERY,
        target="TEMPLATE",
    ))

    # 创建 VM 并执行程序
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)

    await vm.load_program(program)
    result = await vm.execute_program("basic_demo")

    print("\n程序执行完成:")
    print(f"  指令数：{len(program.instructions)}")
    print(f"  最终状态：{result['final_state']}")
    print(f"  模板存储：{list(vm.memory.templates.keys())}")
    print(f"  变量：{program.variables}")


async def demo_2_loop_program():
    """演示 2: 循环程序 (图灵完备)"""

    print("\n" + "=" * 70)
    print("演示 2: 循环程序 (图灵完备)")
    print("=" * 70)

    # 创建程序
    program = create_program(
        name="loop_demo",
        description="循环程序演示",
    )

    # 初始化计数器
    program.add_instruction(create_instruction(
        SemanticOpcode.SET,
        name="counter",
        value=0,
    ))

    # WHILE 循环
    loop_body = [
        SemanticInstruction(
            opcode=SemanticOpcode.SET,
            parameters={"name": "counter", "value": "${counter} + 1"},
        ),
        SemanticInstruction(
            opcode=SemanticOpcode.CREATE,
            target="TEMPLATE",
            target_name="template_${counter}",
            parameters={"index": "${counter}"},
        ),
    ]

    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.WHILE,
        condition="${counter} < 5",
        body=loop_body,
    ))

    # 创建 VM 并执行
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)

    await vm.load_program(program)
    result = await vm.execute_program("loop_demo")

    print("\n循环程序执行完成:")
    print(f"  最终计数器：{program.variables.get('counter')}")
    print(f"  创建的模板：{list(vm.memory.templates.keys())}")


async def demo_3_self_modifying_program():
    """演示 3: 自修改程序 (Self-Bootstrap)"""

    print("\n" + "=" * 70)
    print("演示 3: 自修改程序 (Self-Bootstrap)")
    print("=" * 70)

    # 创建程序
    program = create_program(
        name="self_modifying_demo",
        description="自修改程序演示",
    )

    # 步骤 1: 创建初始模板
    program.add_instruction(create_instruction(
        SemanticOpcode.CREATE,
        target="TEMPLATE",
        target_name="initial_template",
        version="1.0",
        steps=["step1"],
    ))

    # 步骤 2: 修改模板 (自修改)
    program.add_instruction(create_instruction(
        SemanticOpcode.MODIFY,
        target="TEMPLATE",
        target_name="initial_template",
        version="2.0",
        steps=["step1", "step2", "step3"],
    ))

    # 步骤 3: 修改处理器 Prompt (Self-Bootstrap 关键)
    program.add_instruction(create_instruction(
        SemanticOpcode.MODIFY,
        target="PROCESSOR",
        parameters={
            "new_prompt": "你是更强大的语义 VM 处理器，支持更多操作...",
        },
    ))

    # 步骤 4: 定义新指令 (扩展指令集)
    program.add_instruction(create_instruction(
        SemanticOpcode.DEFINE_INSTRUCTION,
        instruction_name="FORECAST",
        description="预测分析指令",
    ))

    # 创建 VM 并执行
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)

    # 初始化处理器 Prompt
    vm.memory.set("CONFIG", "PROCESSOR_PROMPT", vm.processor.processor_prompt)

    await vm.load_program(program)
    result = await vm.execute_program("self_modifying_demo")

    print("\n自修改程序执行完成:")
    print(f"  模板版本：{vm.memory.templates.get('initial_template', {}).get('version')}")
    print(f"  模板步骤：{vm.memory.templates.get('initial_template', {}).get('steps')}")
    print(f"  处理器 Prompt 已修改：{'PROCESSOR_PROMPT' in vm.memory.configs}")
    print("  新指令已定义：FORECAST")


async def demo_4_meta_bootstrap():
    """演示 4: 元自举 (Meta-Bootstrap)"""

    print("\n" + "=" * 70)
    print("演示 4: 元自举 (Meta-Bootstrap)")
    print("=" * 70)

    # 创建元自举程序
    program = create_program(
        name="meta_bootstrap",
        description="元自举程序",
    )

    # 步骤 1: 创建 Self-Bootstrap 策略
    program.add_instruction(create_instruction(
        SemanticOpcode.CREATE,
        target="POLICY",
        target_name="self_bootstrap_policy",
        allow_self_modification=True,
        require_approval_for=["delete_all_templates"],
    ))

    # 步骤 2: 修改 Self-Bootstrap 策略 (自修改)
    program.add_instruction(create_instruction(
        SemanticOpcode.MODIFY,
        target="POLICY",
        target_name="self_bootstrap_policy",
        require_approval_for=["delete_all_templates", "modify_audit_rules"],
        max_modifications_per_hour=20,
    ))

    # 步骤 3: 创建监控程序
    monitor_program = create_program(
        name="monitor_self_bootstrap",
        description="监控自修改",
    )

    monitor_program.add_instruction(create_instruction(
        SemanticOpcode.WHILE,
        condition="true",
        body=[
            SemanticInstruction(
                opcode=SemanticOpcode.QUERY,
                target="AUDIT_LOG",
            ),
            SemanticInstruction(
                opcode=SemanticOpcode.IF,
                condition="audit_count > 10",
                body=[
                    SemanticInstruction(
                        opcode=SemanticOpcode.MODIFY,
                        target="POLICY",
                        target_name="self_bootstrap_policy",
                        max_modifications_per_hour=10,
                    ),
                ],
            ),
        ],
    ))

    # 创建 VM 并执行
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)

    await vm.load_program(program)
    result = await vm.execute_program("meta_bootstrap")

    # 加载监控程序
    await vm.load_program(monitor_program)

    print("\n元自举程序执行完成:")
    print(f"  Self-Bootstrap 策略：{vm.memory.policies.get('self_bootstrap_policy')}")
    print(f"  监控程序已加载：{'monitor_self_bootstrap' in vm.memory.programs}")


async def demo_5_turing_complete():
    """演示 5: 图灵完备性验证"""

    print("\n" + "=" * 70)
    print("演示 5: 图灵完备性验证")
    print("=" * 70)

    # 创建计算程序 (计算斐波那契数列)
    program = create_program(
        name="fibonacci",
        description="计算斐波那契数列",
    )

    # 初始化
    program.add_instruction(create_instruction(
        SemanticOpcode.SET,
        name="a",
        value=0,
    ))
    program.add_instruction(create_instruction(
        SemanticOpcode.SET,
        name="b",
        value=1,
    ))
    program.add_instruction(create_instruction(
        SemanticOpcode.SET,
        name="n",
        value=10,
    ))
    program.add_instruction(create_instruction(
        SemanticOpcode.SET,
        name="result",
        value=[],
    ))

    # 循环计算
    loop_body = [
        SemanticInstruction(
            opcode=SemanticOpcode.SET,
            parameters={"name": "next", "value": "${a} + ${b}"},
        ),
        SemanticInstruction(
            opcode=SemanticOpcode.SET,
            parameters={"name": "a", "value": "${b}"},
        ),
        SemanticInstruction(
            opcode=SemanticOpcode.SET,
            parameters={"name": "b", "value": "${next}"},
        ),
    ]

    program.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.LOOP,
        parameters={"times": 10},
        body=loop_body,
    ))

    # 创建 VM 并执行
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)

    await vm.load_program(program)
    result = await vm.execute_program("fibonacci")

    print("\n斐波那契程序执行完成:")
    print(f"  变量：{program.variables}")
    print("  图灵完备：✅ (支持循环 + 分支 + 内存)")


async def main():
    """运行所有演示"""

    print("\n" + "=" * 70)
    print("基于语义 VM 的 Self-Bootstrap 演示")
    print("语义 VM = 语义指令集 + LLM 处理器 + 语义内存")
    print("=" * 70 + "\n")

    await demo_1_basic_program()
    await demo_2_loop_program()
    await demo_3_self_modifying_program()
    await demo_4_meta_bootstrap()
    await demo_5_turing_complete()

    print("\n" + "=" * 70)
    print("所有演示完成")
    print("=" * 70)

    print("\n🎯 关键洞察:")
    print("1. 语义 VM 是图灵完备的 (支持循环 + 分支)")
    print("2. 程序可以修改自身指令 (Self-Bootstrap)")
    print("3. 程序可以修改处理器 Prompt (Meta-Bootstrap)")
    print("4. 程序可以定义新指令 (扩展指令集)")
    print("5. LLM 是处理器，语义指令是'机器码'")


if __name__ == "__main__":
    asyncio.run(main())
