"""
并行和分布式执行演示
"""

import asyncio
import time

from intentos import (
    DistributedExecutor,
    ParallelDAGExecutor,
    TaskResult,
    TaskStatus,
    create_dag,
    create_local_node,
    create_task,
)
from intentos import (
    ParallelExecutionMode as ExecutionMode,
)


async def _execute_task_mock(task, delay=0.1):
    """模拟任务执行"""
    print(f"  执行：{task.name}...")
    await asyncio.sleep(delay)
    return TaskResult(
        task_id=task.id,
        status=TaskStatus.COMPLETED,
        result=f"Result of {task.name}",
        start_time=time.time(),
        end_time=time.time() + delay,
        node_id="local",
    )


async def demo_sequential_execution():
    """演示顺序执行"""
    print("=" * 60)
    print("演示 1: 顺序执行 (Sequential)")
    print("=" * 60)

    dag = create_dag(name="sequential_demo")
    dag.add_task(create_task("step1", "查询数据 A", "query", params={"source": "A"}))
    dag.add_task(
        create_task("step2", "查询数据 B", "query", params={"source": "B"}, depends_on=["step1"])
    )
    dag.add_task(create_task("step3", "分析数据", "analyze", depends_on=["step2"]))
    dag.add_task(create_task("step4", "生成报告", "report", depends_on=["step3"]))

    executor = ParallelDAGExecutor(max_concurrency=1)
    results = await executor.execute(
        dag, lambda t: _execute_task_mock(t, 0.1), mode=ExecutionMode.SEQUENTIAL
    )

    print("\n执行完成:")
    summary = executor.get_results_summary()
    print(f"  总任务数：{summary['total_tasks']}")
    print(f"  成功：{summary['successful']}")
    print(f"  总耗时：{summary['total_duration_ms']}ms")


async def demo_parallel_execution():
    """演示并行执行"""
    print("\n" + "=" * 60)
    print("演示 2: 并行执行 (Parallel)")
    print("=" * 60)

    dag = create_dag(name="parallel_demo")
    dag.add_task(create_task("init", "初始化", "init"))
    dag.add_task(create_task("query_a", "查询数据 A", "query", depends_on=["init"]))
    dag.add_task(create_task("query_b", "查询数据 B", "query", depends_on=["init"]))
    dag.add_task(create_task("query_c", "查询数据 C", "query", depends_on=["init"]))
    dag.add_task(create_task("query_d", "查询数据 D", "query", depends_on=["init"]))
    dag.add_task(
        create_task(
            "aggregate",
            "聚合分析",
            "analyze",
            depends_on=["query_a", "query_b", "query_c", "query_d"],
        )
    )

    executor = ParallelDAGExecutor(max_concurrency=10)
    results = await executor.execute(
        dag, lambda t: _execute_task_mock(t, 0.1), mode=ExecutionMode.PARALLEL
    )

    print("\n执行完成:")
    summary = executor.get_results_summary()
    print(f"  总任务数：{summary['total_tasks']}")
    print(f"  成功：{summary['successful']}")
    print(f"  总耗时：{summary['total_duration_ms']}ms")
    print("\n并行优势：4 个查询任务同时执行，而非顺序执行")


async def demo_distributed_execution():
    """演示分布式执行"""
    print("\n" + "=" * 60)
    print("演示 3: 分布式执行 (Distributed)")
    print("=" * 60)

    distributed = DistributedExecutor()
    distributed.register_node(create_local_node("node1", ["query", "analyze"]))
    distributed.register_node(create_local_node("node2", ["query", "report"]))
    distributed.register_node(create_local_node("node3", ["analyze", "report"]))

    print(f"已注册节点：{list(distributed.nodes.keys())}")

    dag = create_dag(name="distributed_demo")
    dag.add_task(create_task("task1", "查询 A", "query"))
    dag.add_task(create_task("task2", "查询 B", "query"))
    dag.add_task(create_task("task3", "分析", "analyze", depends_on=["task1", "task2"]))
    dag.add_task(create_task("task4", "报告", "report", depends_on=["task3"]))

    async def execute_on_node(task):
        node = distributed.select_node(task.capability)
        node_id = node.node_id if node else "local"
        print(f"  执行：{task.name} (节点：{node_id})...")
        await asyncio.sleep(0.1)
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            result=f"Result of {task.name}",
            start_time=time.time(),
            end_time=time.time() + 0.1,
            node_id=node_id,
        )

    executor = ParallelDAGExecutor(max_concurrency=10, distributed_executor=distributed)
    results = await executor.execute(dag, execute_on_node, mode=ExecutionMode.DISTRIBUTED)

    print("\n执行完成:")
    summary = executor.get_results_summary()
    print(f"  总任务数：{summary['total_tasks']}")
    print(f"  成功：{summary['successful']}")

    print("\n节点统计:")
    for node_id, node in distributed.nodes.items():
        print(f"  {node_id}: {node.stats['total_tasks']} 任务")


async def demo_progress_tracking():
    """演示进度追踪"""
    print("\n" + "=" * 60)
    print("演示 4: 进度追踪 (Progress Tracking)")
    print("=" * 60)

    dag = create_dag(name="progress_demo")
    for i in range(10):
        dag.add_task(create_task(f"task{i}", f"任务 {i}", "process"))

    executor = ParallelDAGExecutor(max_concurrency=3)

    exec_task = asyncio.create_task(
        executor.execute(dag, lambda t: _execute_task_mock(t, 0.05), mode=ExecutionMode.PARALLEL)
    )

    while not exec_task.done():
        progress = executor.get_progress()
        if progress:
            print(
                f"\r  进度：{progress.progress_percent:.1f}% "
                f"(完成:{progress.completed_tasks}/{progress.total_tasks}, "
                f"剩余:{progress.estimated_remaining_seconds:.1f}s)",
                end="",
            )
        await asyncio.sleep(0.1)

    print("\n")
    summary = executor.get_results_summary()
    print(f"执行完成：{summary['successful']}/{summary['total_tasks']}")


async def demo_complex_dag():
    """演示复杂 DAG 执行"""
    print("\n" + "=" * 60)
    print("演示 5: 复杂 DAG (Complex Workflow)")
    print("=" * 60)

    dag = create_dag(name="complex_workflow")

    dag.add_task(create_task("collect_1", "收集数据源 1", "collect"))
    dag.add_task(create_task("collect_2", "收集数据源 2", "collect"))
    dag.add_task(create_task("collect_3", "收集数据源 3", "collect"))

    dag.add_task(create_task("process_1", "处理数据 1", "process", depends_on=["collect_1"]))
    dag.add_task(create_task("process_2", "处理数据 2", "process", depends_on=["collect_2"]))
    dag.add_task(create_task("process_3", "处理数据 3", "process", depends_on=["collect_3"]))

    dag.add_task(
        create_task(
            "merge", "合并数据", "merge", depends_on=["process_1", "process_2", "process_3"]
        )
    )

    dag.add_task(create_task("analyze_1", "趋势分析", "analyze", depends_on=["merge"]))
    dag.add_task(create_task("analyze_2", "异常检测", "analyze", depends_on=["merge"]))

    dag.add_task(create_task("report", "生成报告", "report", depends_on=["analyze_1", "analyze_2"]))

    async def execute_task(task):
        print(f"  [{task.id}] {task.name}...")
        await asyncio.sleep(0.05)
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            result=f"Result of {task.name}",
            start_time=time.time(),
            end_time=time.time() + 0.05,
            node_id="local",
        )

    executor = ParallelDAGExecutor(max_concurrency=5)
    results = await executor.execute(dag, execute_task, mode=ExecutionMode.PARALLEL)

    print("\n执行完成:")
    summary = executor.get_results_summary()
    print(f"  总任务数：{summary['total_tasks']}")
    print(f"  成功：{summary['successful']}")
    print(f"  总耗时：{summary['total_duration_ms']}ms")

    print("\nDAG 拓扑顺序:")
    for i, task_id in enumerate(dag.get_topological_order(), 1):
        task = dag.get_task(task_id)
        deps = f" <- [{', '.join(task.depends_on)}]" if task.depends_on else ""
        print(f"  {i}. {task_id}{deps}")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print("并行和分布式执行演示")
    print("=" * 70 + "\n")

    await demo_sequential_execution()
    await demo_parallel_execution()
    await demo_distributed_execution()
    await demo_progress_tracking()
    await demo_complex_dag()

    print("\n" + "=" * 70)
    print("演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
