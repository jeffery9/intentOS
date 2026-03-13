"""
完整的 Self-Bootstrap 演示

演示系统如何真正实现自举：
1. 修改自身的解析规则
2. 修改自身的执行规则
3. 扩展自身的指令集
4. 修改自身的策略
5. 自我复制
6. 自动扩缩容
"""

import asyncio
from datetime import datetime
from intentos.self_bootstrap_executor import (
    SelfBootstrapExecutor,
    BootstrapPolicy,
    BootstrapPrograms,
    BootstrapValidator,
    create_bootstrap_executor,
    create_bootstrap_validator,
    create_bootstrap_policy,
)
from intentos.semantic_vm import SemanticVM, create_semantic_vm
from intentos.distributed_semantic_vm import DistributedSemanticVM, create_distributed_vm


# Mock LLM Executor
class MockLLMExecutor:
    async def execute(self, messages: list[dict]) -> any:
        class Response:
            content = '{"operation": "bootstrap", "success": true}'
        return Response()


async def demo_1_modify_parse_prompt():
    """演示 1: 修改解析规则"""
    
    print("=" * 70)
    print("演示 1: 修改解析规则 (Self-Bootstrap Level 1)")
    print("=" * 70)
    
    # 创建语义 VM
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)
    
    # 初始化解析 Prompt
    INITIAL_PARSE_PROMPT = "你是一个意图解析专家..."
    vm.memory.set("CONFIG", "PARSE_PROMPT", INITIAL_PARSE_PROMPT)
    
    print(f"\n初始解析 Prompt: {INITIAL_PARSE_PROMPT}")
    
    # 创建 Self-Bootstrap 执行器
    bootstrap = create_bootstrap_executor(vm)
    
    # 创建解析 Prompt 修改程序
    new_prompt = """
你是一个更强大的意图解析专家。

新增能力:
1. 支持情感分析
2. 支持多轮对话
3. 支持模糊意图识别

输出格式:
{
    "action": "动作",
    "target": "目标",
    "parameters": {},
    "sentiment": "positive/neutral/negative",
    "follow_up_questions": []
}
"""
    
    program = BootstrapPrograms.create_parse_prompt_modifier(new_prompt)
    
    # 执行自修改
    record = await bootstrap.execute_bootstrap(
        action="modify_parse_prompt",
        target="CONFIG.PARSE_PROMPT",
        new_value=new_prompt,
        context={"user_id": "system"},
        program_id=program.name,
    )
    
    print(f"\n自修改结果:")
    print(f"  状态：{record.status}")
    print(f"  目标：{record.target}")
    print(f"  新值：{record.new_value[:50]}...")
    
    # 验证修改
    current_value = vm.memory.get("CONFIG", "PARSE_PROMPT")
    print(f"  当前值：{current_value[:50] if current_value else 'None'}...")
    
    print("\n✅ 解析规则已修改")


async def demo_2_modify_execute_prompt():
    """演示 2: 修改执行规则"""
    
    print("\n" + "=" * 70)
    print("演示 2: 修改执行规则 (Self-Bootstrap Level 1)")
    print("=" * 70)
    
    # 创建语义 VM
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)
    
    # 初始化执行 Prompt
    INITIAL_EXECUTE_PROMPT = "你是语义 VM 处理器..."
    vm.memory.set("CONFIG", "EXECUTE_PROMPT", INITIAL_EXECUTE_PROMPT)
    
    print(f"\n初始执行 Prompt: {INITIAL_EXECUTE_PROMPT}")
    
    # 创建 Self-Bootstrap 执行器
    bootstrap = create_bootstrap_executor(vm)
    
    # 创建执行 Prompt 修改程序
    new_prompt = """
你是更强大的语义 VM 处理器。

新增操作:
1. forecast: 预测分析
2. optimize: 优化建议
3. simulate: 模拟执行

输出格式:
{
    "operation": "操作名称",
    "parameters": {},
    "result": {},
    "error": "错误信息"
}
"""
    
    program = BootstrapPrograms.create_execute_prompt_modifier(new_prompt)
    
    # 执行自修改
    record = await bootstrap.execute_bootstrap(
        action="modify_execute_prompt",
        target="CONFIG.EXECUTE_PROMPT",
        new_value=new_prompt,
        context={"user_id": "system"},
        program_id=program.name,
    )
    
    print(f"\n自修改结果:")
    print(f"  状态：{record.status}")
    print(f"  目标：{record.target}")
    
    print("\n✅ 执行规则已修改")


async def demo_3_extend_instructions():
    """演示 3: 扩展指令集"""
    
    print("\n" + "=" * 70)
    print("演示 3: 扩展指令集 (Self-Bootstrap Level 2)")
    print("=" * 70)
    
    # 创建语义 VM
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)
    
    # 创建 Self-Bootstrap 执行器
    bootstrap = create_bootstrap_executor(vm)
    
    # 创建指令集扩展程序
    new_instructions = [
        "FORECAST: 预测分析指令",
        "OPTIMIZE: 优化建议指令",
        "SIMULATE: 模拟执行指令",
        "VALIDATE: 验证指令",
    ]
    
    program = BootstrapPrograms.create_instruction_extender(new_instructions)
    
    # 执行自修改
    record = await bootstrap.execute_bootstrap(
        action="extend_instruction_set",
        target="INSTRUCTION_SET.META_ACTIONS",
        new_value=new_instructions,
        context={"user_id": "system"},
        program_id=program.name,
    )
    
    print(f"\n自修改结果:")
    print(f"  状态：{record.status}")
    print(f"  新增指令：{new_instructions}")
    
    print("\n✅ 指令集已扩展")


async def demo_4_modify_policy():
    """演示 4: 修改自举策略"""
    
    print("\n" + "=" * 70)
    print("演示 4: 修改自举策略 (Self-Bootstrap Level 2)")
    print("=" * 70)
    
    # 创建语义 VM
    llm_executor = MockLLMExecutor()
    vm = create_semantic_vm(llm_executor)
    
    # 创建 Self-Bootstrap 执行器 (带策略)
    policy = create_bootstrap_policy(
        max_modifications_per_hour=10,
        require_confidence_threshold=0.8,
    )
    bootstrap = create_bootstrap_executor(vm, policy)
    
    print(f"\n初始策略:")
    print(f"  每小时最大修改：{policy.max_modifications_per_hour}")
    print(f"  置信度阈值：{policy.require_confidence_threshold}")
    
    # 创建策略修改程序
    program = BootstrapPrograms.create_policy_modifier(
        max_modifications_per_hour=20,
        require_confidence_threshold=0.9,
        replication_factor=5,
    )
    
    # 执行自修改
    record = await bootstrap.execute_bootstrap(
        action="modify_bootstrap_policy",
        target="POLICY.max_modifications_per_hour",
        new_value=20,
        context={"user_id": "system"},
        program_id=program.name,
    )
    
    print(f"\n自修改结果:")
    print(f"  状态：{record.status}")
    print(f"  新策略:")
    print(f"    每小时最大修改：{bootstrap.policy.max_modifications_per_hour}")
    print(f"    置信度阈值：{bootstrap.policy.require_confidence_threshold}")
    print(f"    复制因子：{bootstrap.policy.replication_factor}")
    
    print("\n✅ 自举策略已修改")


async def demo_5_self_replication():
    """演示 5: 自我复制"""
    
    print("\n" + "=" * 70)
    print("演示 5: 自我复制 (Self-Bootstrap Level 3)")
    print("=" * 70)
    
    # 创建分布式语义 VM
    llm_executor = MockLLMExecutor()
    cluster = create_distributed_vm(llm_executor)
    
    # 添加节点
    await cluster.add_node("node1.cluster.local", 8001)
    await cluster.add_node("node2.cluster.local", 8002)
    
    print(f"\n初始集群:")
    status = await cluster.get_cluster_status()
    print(f"  节点数：{status['total_nodes']}")
    
    # 创建 Self-Bootstrap 执行器
    bootstrap = create_bootstrap_executor(cluster)
    
    # 创建自我复制程序
    program = BootstrapPrograms.create_self_replicator()
    
    print(f"\n自我复制程序:")
    print(f"  名称：{program.name}")
    print(f"  描述：{program.description}")
    
    # 执行自复制
    exec_id = await cluster.execute_program(program)
    
    print(f"\n自复制执行:")
    print(f"  执行 ID: {exec_id}")
    
    # 等待执行完成
    await asyncio.sleep(0.1)
    
    print(f"\n✅ 程序已复制到其他节点")


async def demo_6_auto_scaling():
    """演示 6: 自动扩缩容"""
    
    print("\n" + "=" * 70)
    print("演示 6: 自动扩缩容 (Self-Bootstrap Level 3)")
    print("=" * 70)
    
    # 创建分布式语义 VM
    llm_executor = MockLLMExecutor()
    cluster = create_distributed_vm(llm_executor)
    
    # 初始 1 个节点
    print(f"\n初始集群:")
    status = await cluster.get_cluster_status()
    print(f"  节点数：{status['total_nodes']}")
    
    # 创建 Self-Bootstrap 执行器
    bootstrap = create_bootstrap_executor(cluster)
    
    # 创建自动扩缩容程序
    program = BootstrapPrograms.create_auto_scaler(
        scale_up_threshold=0.8,
        scale_down_threshold=0.3,
    )
    
    print(f"\n自动扩缩容程序:")
    print(f"  扩容阈值：80%")
    print(f"  缩容阈值：30%")
    
    # 模拟扩容
    await cluster.add_node("auto-node-1.cluster.local", 8004)
    await cluster.add_node("auto-node-2.cluster.local", 8005)
    
    print(f"\n扩容后:")
    status = await cluster.get_cluster_status()
    print(f"  节点数：{status['total_nodes']}")
    
    print(f"\n✅ 集群已自动扩缩容")


async def demo_7_full_bootstrap():
    """演示 7: 完整的 Self-Bootstrap 流程"""
    
    print("\n" + "=" * 70)
    print("演示 7: 完整的 Self-Bootstrap 流程")
    print("=" * 70)
    
    # 创建分布式语义 VM
    llm_executor = MockLLMExecutor()
    cluster = create_distributed_vm(llm_executor)
    await cluster.add_node("node1.cluster.local", 8001)
    
    # 创建 Self-Bootstrap 执行器
    policy = create_bootstrap_policy(
        allow_self_modification=True,
        max_modifications_per_hour=100,
    )
    bootstrap = create_bootstrap_executor(cluster, policy)
    validator = create_bootstrap_validator(bootstrap)
    
    print(f"\n初始系统状态:")
    print(f"  节点数：1")
    print(f"  自修改：允许")
    print(f"  速率限制：100/小时")
    
    # 步骤 1: 修改解析规则
    print(f"\n--- 步骤 1: 修改解析规则 ---")
    record1 = await bootstrap.execute_bootstrap(
        action="modify_parse_prompt",
        target="CONFIG.PARSE_PROMPT",
        new_value="更强大的解析 Prompt...",
        context={"user_id": "system"},
        program_id="bootstrap_demo",
    )
    print(f"  状态：{record1.status}")
    
    # 步骤 2: 修改执行规则
    print(f"\n--- 步骤 2: 修改执行规则 ---")
    record2 = await bootstrap.execute_bootstrap(
        action="modify_execute_prompt",
        target="CONFIG.EXECUTE_PROMPT",
        new_value="更强大的执行 Prompt...",
        context={"user_id": "system"},
        program_id="bootstrap_demo",
    )
    print(f"  状态：{record2.status}")
    
    # 步骤 3: 扩展指令集
    print(f"\n--- 步骤 3: 扩展指令集 ---")
    record3 = await bootstrap.execute_bootstrap(
        action="extend_instruction_set",
        target="INSTRUCTION_SET.META_ACTIONS",
        new_value=["FORECAST", "OPTIMIZE"],
        context={"user_id": "system"},
        program_id="bootstrap_demo",
    )
    print(f"  状态：{record3.status}")
    
    # 步骤 4: 修改策略
    print(f"\n--- 步骤 4: 修改策略 ---")
    record4 = await bootstrap.execute_bootstrap(
        action="modify_bootstrap_policy",
        target="POLICY.max_modifications_per_hour",
        new_value=200,
        context={"user_id": "system"},
        program_id="bootstrap_demo",
    )
    print(f"  状态：{record4.status}")
    
    # 步骤 5: 添加节点
    print(f"\n--- 步骤 5: 添加节点 ---")
    await cluster.add_node("node2.cluster.local", 8002)
    status = await cluster.get_cluster_status()
    print(f"  节点数：{status['total_nodes']}")
    
    # 验证 Self-Bootstrap 能力
    print(f"\n--- 验证 Self-Bootstrap 能力 ---")
    validation = await validator.validate_bootstrap_capability()
    print(f"  Self-Bootstrap 能力：{'✅' if validation['capable'] else '❌'}")
    print(f"  支持的能力:")
    for cap, capable in validation['capabilities'].items():
        print(f"    {cap}: {'✅' if capable else '❌'}")
    
    # 获取自举历史
    print(f"\n--- 自举历史 ---")
    history = bootstrap.get_bootstrap_history()
    print(f"  总修改数：{len(history)}")
    for record in history:
        print(f"    - {record.action}: {record.status}")
    
    print(f"\n✅ 完整的 Self-Bootstrap 流程完成")


async def main():
    """运行所有演示"""
    
    print("\n" + "=" * 70)
    print("完整的 Self-Bootstrap 演示")
    print("语义 VM + 分布式 + 自修改")
    print("=" * 70 + "\n")
    
    await demo_1_modify_parse_prompt()
    await demo_2_modify_execute_prompt()
    await demo_3_extend_instructions()
    await demo_4_modify_policy()
    await demo_5_self_replication()
    await demo_6_auto_scaling()
    await demo_7_full_bootstrap()
    
    print("\n" + "=" * 70)
    print("所有演示完成")
    print("=" * 70)
    
    print("\n🎯 Self-Bootstrap 总结:")
    print("1. Level 1: 修改解析/执行规则 (Prompt)")
    print("2. Level 2: 扩展指令集、修改策略")
    print("3. Level 3: 自我复制、自动扩缩容")
    print("\n🔑 核心洞察:")
    print("- 语义 VM 是 Self-Bootstrap 的基础架构")
    print("- 分布式是 Self-Bootstrap 的扩展能力")
    print("- 规则在存储中 (可修改)，而非代码中")
    print("- LLM 是处理器，解析和执行语义指令")


if __name__ == "__main__":
    asyncio.run(main())
