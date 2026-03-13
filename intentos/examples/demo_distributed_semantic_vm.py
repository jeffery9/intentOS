"""
分布式语义 VM Self-Bootstrap 演示

演示分布式环境下的 Self-Bootstrap:
1. 程序在多个节点上执行
2. 程序复制自身到其他节点
3. 程序修改分布式配置
4. 程序添加/移除节点
"""

import asyncio
from intentos.distributed import (
    DistributedSemanticVM,
    DistributedOpcode,
    create_distributed_vm,
    create_node,
)
from intentos.semantic_vm import (
    SemanticProgram,
    SemanticInstruction,
    SemanticOpcode,
    create_program,
    create_instruction,
)

# 前向引用修复
SemanticInstruction  # Make linter happy


# Mock LLM Executor
class MockLLMExecutor:
    async def execute(self, messages: list[dict]) -> any:
        class Response:
            content = '{"operation": "mock", "success": true}'
        return Response()


async def demo_1_cluster_setup():
    """演示 1: 集群搭建"""
    
    print("=" * 70)
    print("演示 1: 分布式集群搭建")
    print("=" * 70)
    
    # 创建分布式 VM
    llm_executor = MockLLMExecutor()
    cluster = create_distributed_vm(llm_executor)
    
    # 添加节点
    node1 = await cluster.add_node("node1.cluster.local", 8001)
    node2 = await cluster.add_node("node2.cluster.local", 8002)
    node3 = await cluster.add_node("node3.cluster.local", 8003)
    
    # 获取集群状态
    status = await cluster.get_cluster_status()
    
    print(f"\n集群状态:")
    print(f"  总节点数：{status['total_nodes']}")
    print(f"  活跃节点：{status['active_nodes']}")
    print(f"  节点列表:")
    for node in status['nodes']:
        print(f"    - {node['host']}:{node['port']} ({node['status']})")


async def demo_2_distributed_program():
    """演示 2: 分布式程序执行"""
    
    print("\n" + "=" * 70)
    print("演示 2: 分布式程序执行")
    print("=" * 70)
    
    # 创建集群
    cluster = create_distributed_vm(MockLLMExecutor())
    await cluster.add_node("node1.cluster.local", 8001)
    await cluster.add_node("node2.cluster.local", 8002)
    
    # 创建分布式程序
    program = create_program(
        name="distributed_analysis",
        description="分布式销售分析",
    )
    
    # 在不同节点上执行
    program.add_instruction(create_instruction(
        DistributedOpcode.SPAWN,
        target="PROGRAM",
        target_name="analyze_east",
        node="node1.cluster.local",
        parameters={"region": "华东"},
    ))
    
    program.add_instruction(create_instruction(
        DistributedOpcode.SPAWN,
        target="PROGRAM",
        target_name="analyze_south",
        node="node2.cluster.local",
        parameters={"region": "华南"},
    ))
    
    program.add_instruction(create_instruction(
        DistributedOpcode.BARRIER,
    ))
    
    program.add_instruction(create_instruction(
        DistributedOpcode.SYNC,
        target="RESULTS",
    ))
    
    # 执行程序
    exec_id = await cluster.execute_program(program)
    
    # 等待执行完成
    while True:
        status = await cluster.get_execution_status(exec_id)
        if status and status.get("status") != "running":
            break
        await asyncio.sleep(0.1)
    
    result = await cluster.get_execution_result(exec_id)
    
    print(f"\n分布式程序执行完成:")
    print(f"  执行 ID: {exec_id}")
    print(f"  结果：{result}")


async def demo_3_self_replication():
    """演示 3: 程序自我复制 (Self-Bootstrap)"""
    
    print("\n" + "=" * 70)
    print("演示 3: 程序自我复制 (Self-Bootstrap)")
    print("=" * 70)
    
    # 创建集群
    cluster = create_distributed_vm(MockLLMExecutor())
    await cluster.add_node("node1.cluster.local", 8001)
    await cluster.add_node("node2.cluster.local", 8002)
    
    # 创建自复制程序
    program = create_program(
        name="self_replicating",
        description="自我复制的程序",
    )
    
    # 在本地节点创建自身
    program.add_instruction(create_instruction(
        SemanticOpcode.CREATE,
        target="PROGRAM",
        target_name="self_copy_1",
        instructions=program.instructions,  # 复制自身指令
    ))
    
    # 复制到远程节点
    program.add_instruction(create_instruction(
        DistributedOpcode.REPLICATE,
        target="PROGRAM",
        target_name="self_copy_1",
        node="node2.cluster.local",
    ))
    
    # 在远程节点执行副本
    program.add_instruction(create_instruction(
        DistributedOpcode.SPAWN,
        target="PROGRAM",
        target_name="self_copy_1",
        node="node2.cluster.local",
    ))
    
    print(f"\n自复制程序:")
    print(f"  程序名称：{program.name}")
    print(f"  指令数：{len(program.instructions)}")
    print(f"  自复制：✅")
    
    # 执行程序
    exec_id = await cluster.execute_program(program)
    print(f"  执行 ID: {exec_id}")


async def demo_4_dynamic_scaling():
    """演示 4: 动态扩缩容 (Self-Bootstrap)"""
    
    print("\n" + "=" * 70)
    print("演示 4: 动态扩缩容 (Self-Bootstrap)")
    print("=" * 70)
    
    # 创建初始集群 (1 个节点)
    cluster = create_distributed_vm(MockLLMExecutor())
    
    print(f"\n初始集群:")
    status = await cluster.get_cluster_status()
    print(f"  节点数：{status['total_nodes']}")
    
    # 程序检测负载并自动扩容
    scaling_program = create_program(
        name="auto_scaling",
        description="自动扩缩容程序",
    )
    
    # 检测负载
    scaling_program.add_instruction(create_instruction(
        SemanticOpcode.QUERY,
        target="CLUSTER_STATUS",
    ))
    
    # 如果负载高，添加节点
    scaling_program.add_instruction(create_instruction(
        SemanticOpcode.IF,
        condition="cluster_load > 0.8",
        body=[
            SemanticInstruction(
                opcode=DistributedOpcode.SPAWN,
                target="NODE",
                parameters={
                    "host": "auto-node-1.cluster.local",
                    "port": 8004,
                },
            ),
            SemanticInstruction(
                opcode=DistributedOpcode.SPAWN,
                target="NODE",
                parameters={
                    "host": "auto-node-2.cluster.local",
                    "port": 8005,
                },
            ),
        ],
    ))
    
    # 模拟执行 (添加节点)
    await cluster.add_node("auto-node-1.cluster.local", 8004)
    await cluster.add_node("auto-node-2.cluster.local", 8005)
    
    print(f"\n自动扩容后:")
    status = await cluster.get_cluster_status()
    print(f"  节点数：{status['total_nodes']}")
    print(f"  新增节点：auto-node-1, auto-node-2")


async def demo_5_distributed_self_modification():
    """演示 5: 分布式自修改 (Meta-Bootstrap)"""
    
    print("\n" + "=" * 70)
    print("演示 5: 分布式自修改 (Meta-Bootstrap)")
    print("=" * 70)
    
    # 创建集群
    cluster = create_distributed_vm(MockLLMExecutor())
    await cluster.add_node("node1.cluster.local", 8001)
    await cluster.add_node("node2.cluster.local", 8002)
    
    # 创建自修改程序
    program = create_program(
        name="distributed_self_modify",
        description="分布式自修改程序",
    )
    
    # 修改分布式配置 (所有节点)
    program.add_instruction(create_instruction(
        DistributedOpcode.BROADCAST,
        target="CONFIG",
        target_name="PROCESSOR_PROMPT",
        value="你是更强大的分布式语义 VM 处理器...",
    ))
    
    # 修改复制策略
    program.add_instruction(create_instruction(
        SemanticOpcode.MODIFY,
        target="POLICY",
        target_name="replication_policy",
        replication_factor=3,  # 3 副本
        consistency_level="quorum",
    ))
    
    # 修改分片策略
    program.add_instruction(create_instruction(
        SemanticOpcode.MODIFY,
        target="POLICY",
        target_name="sharding_policy",
        shard_key="region",
        num_shards=10,
    ))
    
    print(f"\n分布式自修改程序:")
    print(f"  广播修改：PROCESSOR_PROMPT")
    print(f"  修改策略：replication_policy, sharding_policy")
    
    # 执行程序
    exec_id = await cluster.execute_program(program)
    print(f"  执行 ID: {exec_id}")


async def demo_6_consensus():
    """演示 6: 分布式共识 (Self-Bootstrap)"""
    
    print("\n" + "=" * 70)
    print("演示 6: 分布式共识 (Self-Bootstrap)")
    print("=" * 70)
    
    # 创建集群
    cluster = create_distributed_vm(MockLLMExecutor())
    await cluster.add_node("node1.cluster.local", 8001)
    await cluster.add_node("node2.cluster.local", 8002)
    await cluster.add_node("node3.cluster.local", 8003)
    
    # 创建共识程序
    consensus_program = create_program(
        name="distributed_consensus",
        description="分布式共识程序",
    )
    
    # 提议修改
    consensus_program.add_instruction(create_instruction(
        SemanticOpcode.SET,
        name="proposal",
        value={"action": "modify_parse_prompt", "value": "new_prompt"},
    ))
    
    # 投票
    consensus_program.add_instruction(create_instruction(
        DistributedOpcode.BROADCAST,
        target="VOTE",
        target_name="proposal_vote",
    ))
    
    # 等待多数节点同意
    consensus_program.add_instruction(create_instruction(
        SemanticOpcode.WHILE,
        condition="votes < total_nodes / 2",
        body=[
            SemanticInstruction(
                opcode=SemanticOpcode.QUERY,
                target="VOTES",
            ),
        ],
    ))
    
    # 执行修改
    consensus_program.add_instruction(create_instruction(
        SemanticOpcode.IF,
        condition="votes >= total_nodes / 2",
        body=[
            SemanticInstruction(
                opcode=SemanticOpcode.MODIFY,
                target="CONFIG",
                target_name="PARSE_PROMPT",
                value="new_prompt",
            ),
        ],
    ))
    
    print(f"\n分布式共识程序:")
    print(f"  节点数：3")
    print(f"  共识机制：多数投票")
    print(f"  修改内容：PARSE_PROMPT")


async def main():
    """运行所有演示"""
    
    print("\n" + "=" * 70)
    print("分布式语义 VM Self-Bootstrap 演示")
    print("分布式集群 + 自修改 + 自复制 + 动态扩缩容")
    print("=" * 70 + "\n")
    
    await demo_1_cluster_setup()
    await demo_2_distributed_program()
    await demo_3_self_replication()
    await demo_4_dynamic_scaling()
    await demo_5_distributed_self_modification()
    await demo_6_consensus()
    
    print("\n" + "=" * 70)
    print("所有演示完成")
    print("=" * 70)
    
    print("\n🎯 关键洞察:")
    print("1. 语义 VM 是分布式的 (多节点集群)")
    print("2. 程序可以在节点间复制 (Self-Replication)")
    print("3. 集群可以动态扩缩容 (Auto-Scaling)")
    print("4. 修改需要分布式共识 (Consensus)")
    print("5. 分布式 Self-Bootstrap = 语义 VM + 分布式")


if __name__ == "__main__":
    asyncio.run(main())
