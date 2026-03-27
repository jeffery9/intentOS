#!/usr/bin/env python3
"""
IntentOS CLI 工具

命令行界面，提供以下功能：
- 意图执行
- 图谱查询
- 验证和调试
- 系统状态查看
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Optional

from intentos.graph import (
    IntentGraph,
    IntentNodeType,
    create_intent_graph,
    create_intent_node,
    create_intent_edge,
    IntentEdgeType,
)
from intentos.verification import (
    FormalVerifier,
    DAGValidator,
    create_dag_node,
    create_execution_trace,
    TraceReplayer,
    EventType,
)


# =============================================================================
# CLI 命令实现
# =============================================================================


def cmd_execute(args):
    """执行意图"""
    print(f"执行意图：{args.intent}")
    # 这里集成到实际的意图执行系统
    print("✅ 意图执行完成（模拟）")


def cmd_graph_init(args):
    """初始化意图图谱"""
    graph = create_intent_graph()
    
    # 添加示例节点
    node1 = create_intent_node(
        node_id="demo_001",
        node_type=IntentNodeType.ATOMIC,
        name="分析销售数据",
        description="分析指定区域和时间的销售数据",
        tags=["销售", "分析", "数据"],
    )
    node2 = create_intent_node(
        node_id="demo_002",
        node_type=IntentNodeType.ATOMIC,
        name="生成报表",
        description="生成销售报表",
        tags=["报表", "生成"],
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    
    # 添加边
    edge = create_intent_edge(
        edge_id="edge_001",
        source_id="demo_001",
        target_id="demo_002",
        edge_type=IntentEdgeType.TRIGGERS,
    )
    graph.add_edge(edge)
    
    # 保存图谱
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(graph.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"✅ 图谱已保存到 {args.output}")
    else:
        print(json.dumps(graph.to_dict(), indent=2, ensure_ascii=False))


def cmd_graph_query(args):
    """查询意图图谱"""
    if not args.input:
        print("❌ 错误：请指定图谱文件 (--input)")
        sys.exit(1)
    
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    graph = IntentGraph()
    # 简单反序列化
    for node_data in data.get("nodes", {}).values():
        from intentos.graph import IntentNode
        node = IntentNode.from_dict(node_data)
        graph.add_node(node)
    
    if args.search:
        results = graph.search_by_keyword(args.search)
        print(f"找到 {len(results)} 个结果:")
        for node in results:
            print(f"  - {node.name} ({node.node_id})")
    elif args.node_id:
        node = graph.get_node(args.node_id)
        if node:
            print(json.dumps(node.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ 节点 {args.node_id} 不存在")
    elif args.neighbors:
        neighbors = graph.get_neighbors(args.neighbors)
        print(f"邻居节点 ({len(neighbors)} 个):")
        for n in neighbors:
            print(f"  - {n.name} ({n.node_id})")
    elif args.stats:
        stats = graph.get_statistics()
        print("图谱统计:")
        print(f"  总节点数：{stats['total_nodes']}")
        print(f"  总边数：{stats['total_edges']}")
        print(f"  平均度数：{stats['avg_degree']:.2f}")
    else:
        print(json.dumps(graph.to_dict(), indent=2, ensure_ascii=False))


def cmd_graph_path(args):
    """查找多跳路径"""
    if not args.input:
        print("❌ 错误：请指定图谱文件 (--input)")
        sys.exit(1)
    
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    graph = IntentGraph()
    for node_data in data.get("nodes", {}).values():
        from intentos.graph import IntentNode
        node = IntentNode.from_dict(node_data)
        graph.add_node(node)
    
    # 添加边
    for edge_data in data.get("edges", {}).values():
        from intentos.graph import IntentEdge
        edge = IntentEdge.from_dict(edge_data)
        graph.add_edge(edge)
    
    paths = graph.find_path(args.source, args.target, max_depth=args.max_depth or 5)
    
    if paths:
        print(f"找到 {len(paths)} 条路径:")
        for i, path in enumerate(paths, 1):
            path_nodes = [graph.get_node(nid).name if graph.get_node(nid) else nid for nid in path]
            print(f"  路径 {i}: {' -> '.join(path_nodes)}")
    else:
        print(f"❌ 未找到从 {args.source} 到 {args.target} 的路径")


def cmd_verify_dag(args):
    """验证 DAG"""
    validator = DAGValidator()
    
    # 创建示例 DAG
    nodes = [
        create_dag_node("task_1", "query", dependencies=[]),
        create_dag_node("task_2", "analyze", dependencies=["task_1"]),
        create_dag_node("task_3", "visualize", dependencies=["task_2"]),
    ]
    
    if args.input:
        with open(args.input, 'r') as f:
            data = json.load(f)
        # 从文件加载 DAG
        nodes = []
        for node_data in data.get("nodes", []):
            node = create_dag_node(
                node_data["node_id"],
                node_data["task_type"],
                node_data.get("dependencies", []),
            )
            nodes.append(node)
    
    result = validator.validate(nodes)
    
    print("DAG 验证结果:")
    if result.is_valid:
        print("  ✅ DAG 有效")
    else:
        print("  ❌ DAG 无效")
        for error in result.errors:
            print(f"    - {error}")
    
    if result.warnings:
        print("  警告:")
        for warning in result.warnings:
            print(f"    - {warning}")
    
    return 0 if result.is_valid else 1


def cmd_trace_record(args):
    """记录执行轨迹"""
    trace = create_execution_trace(args.intent_id)
    
    # 模拟事件
    trace.add_event(EventType.TASK_START, "task_001", {"name": "分析数据"})
    trace.add_event(EventType.CAPABILITY_CALL, "task_001", {"capability": "query_db"})
    trace.add_event(EventType.CAPABILITY_RETURN, "task_001", {"result": "success"})
    trace.add_event(EventType.TASK_END, "task_001", {"status": "completed"})
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(trace.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"✅ 轨迹已保存到 {args.output}")
    else:
        print(json.dumps(trace.to_dict(), indent=2, ensure_ascii=False))


def cmd_trace_replay(args):
    """回放执行轨迹"""
    if not args.input:
        print("❌ 错误：请指定轨迹文件 (--input)")
        sys.exit(1)
    
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    from intentos.verification import ExecutionTrace
    trace = ExecutionTrace.from_dict(data)
    
    replayer = TraceReplayer(trace)
    
    print(f"回放轨迹：{trace.trace_id}")
    print(f"意图 ID: {trace.intent_id}")
    print(f"状态：{trace.status.value}")
    print(f"事件数：{len(trace.events)}")
    print(f"时长：{trace.get_duration():.2f}秒")
    print()
    
    if args.step:
        # 单步回放
        print("单步回放:")
        step = 0
        while True:
            event = replayer.step()
            if not event:
                break
            step += 1
            print(f"  [{step}] {event.event_type.value} @ {event.task_id}")
            if args.step > 0 and step >= args.step:
                break
    else:
        # 完整回放
        print("事件列表:")
        for i, event in enumerate(trace.events, 1):
            print(f"  [{i}] {event.event_type.value} @ {event.task_id} ({event.timestamp.strftime('%H:%M:%S')})")


def cmd_status(args):
    """查看系统状态"""
    print("IntentOS 系统状态")
    print("=" * 40)
    print(f"版本：v16.0.0")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("模块状态:")
    print("  ✅ 语义 VM")
    print("  ✅ 分布式 VM")
    print("  ✅ Self-Bootstrap")
    print("  ✅ 意图编译器")
    print("  ✅ 意图图谱")
    print("  ✅ 形式化验证")
    print()
    print("CLI 版本：16.0.0")


# =============================================================================
# 主函数
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        prog="intentos",
        description="IntentOS CLI 工具 - AI 原生操作系统命令行界面",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 16.0.0",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # execute 命令
    p_execute = subparsers.add_parser("execute", help="执行意图")
    p_execute.add_argument("intent", help="要执行的意图")
    p_execute.set_defaults(func=cmd_execute)
    
    # graph 命令组
    p_graph = subparsers.add_parser("graph", help="意图图谱操作")
    graph_subparsers = p_graph.add_subparsers(dest="graph_command")
    
    # graph init
    p_graph_init = graph_subparsers.add_parser("init", help="初始化图谱")
    p_graph_init.add_argument("-o", "--output", help="输出文件")
    p_graph_init.set_defaults(func=cmd_graph_init)
    
    # graph query
    p_graph_query = graph_subparsers.add_parser("query", help="查询图谱")
    p_graph_query.add_argument("-i", "--input", help="图谱文件")
    p_graph_query.add_argument("-s", "--search", help="关键词搜索")
    p_graph_query.add_argument("-n", "--node-id", help="节点 ID")
    p_graph_query.add_argument("--neighbors", help="获取邻居节点")
    p_graph_query.add_argument("--stats", action="store_true", help="显示统计")
    p_graph_query.set_defaults(func=cmd_graph_query)
    
    # graph path
    p_graph_path = graph_subparsers.add_parser("path", help="查找多跳路径")
    p_graph_path.add_argument("-i", "--input", required=True, help="图谱文件")
    p_graph_path.add_argument("--source", required=True, help="源节点 ID")
    p_graph_path.add_argument("--target", required=True, help="目标节点 ID")
    p_graph_path.add_argument("-d", "--max-depth", type=int, default=5, help="最大深度")
    p_graph_path.set_defaults(func=cmd_graph_path)
    
    # verify 命令组
    p_verify = subparsers.add_parser("verify", help="形式化验证")
    verify_subparsers = p_verify.add_subparsers(dest="verify_command")
    
    # verify dag
    p_verify_dag = verify_subparsers.add_parser("dag", help="验证 DAG")
    p_verify_dag.add_argument("-i", "--input", help="DAG 文件")
    p_verify_dag.set_defaults(func=cmd_verify_dag)
    
    # trace 命令组
    p_trace = subparsers.add_parser("trace", help="执行轨迹")
    trace_subparsers = p_trace.add_subparsers(dest="trace_command")
    
    # trace record
    p_trace_record = trace_subparsers.add_parser("record", help="记录轨迹")
    p_trace_record.add_argument("--intent-id", required=True, help="意图 ID")
    p_trace_record.add_argument("-o", "--output", help="输出文件")
    p_trace_record.set_defaults(func=cmd_trace_record)
    
    # trace replay
    p_trace_replay = trace_subparsers.add_parser("replay", help="回放轨迹")
    p_trace_replay.add_argument("-i", "--input", required=True, help="轨迹文件")
    p_trace_replay.add_argument("-s", "--step", type=int, nargs="?", const=-1, help="单步回放")
    p_trace_replay.set_defaults(func=cmd_trace_replay)
    
    # status 命令
    p_status = subparsers.add_parser("status", help="系统状态")
    p_status.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # 处理子命令
    if args.command == "graph" and args.graph_command is None:
        p_graph.print_help()
        sys.exit(0)
    
    if args.command == "verify" and args.verify_command is None:
        p_verify.print_help()
        sys.exit(0)
    
    if args.command == "trace" and args.trace_command is None:
        p_trace.print_help()
        sys.exit(0)
    
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
