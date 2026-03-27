#!/usr/bin/env python3
"""
IntentOS Python SDK

Python 软件开发工具包，提供简洁的 API 用于：
- 意图执行
- 图谱管理
- 验证和调试
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from intentos.graph import (
    IntentGraph,
    IntentNode,
    IntentEdge,
    IntentNodeType,
    IntentEdgeType,
    IntentSimilarityCalculator,
    IntentRecommender,
    create_intent_graph,
    create_intent_node,
    create_intent_edge,
)
from intentos.verification import (
    FormalVerifier,
    DAGValidator,
    CapabilityTypeChecker,
    TraceReplayer,
    ExecutionTrace,
    DAGNode,
    CapabilitySignature,
    create_execution_trace,
    create_dag_node,
    create_capability_signature,
    create_formal_verifier,
)


# =============================================================================
# IntentOS SDK 主类
# =============================================================================


class IntentOSClient:
    """
    IntentOS 客户端
    
    提供高级 API 用于与 IntentOS 交互
    """
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.graph = create_intent_graph()
        self.verifier = create_formal_verifier()
    
    # -------------------------------------------------------------------------
    # 意图图谱 API
    # -------------------------------------------------------------------------
    
    def create_intent(
        self,
        name: str,
        description: str = "",
        intent_type: IntentNodeType = IntentNodeType.ATOMIC,
        tags: Optional[list[str]] = None,
        content: Optional[dict] = None,
    ) -> IntentNode:
        """
        创建意图
        
        Args:
            name: 意图名称
            description: 意图描述
            intent_type: 意图类型
            tags: 标签列表
            content: 意图内容
            
        Returns:
            创建的意图节点
        """
        import uuid
        node = create_intent_node(
            node_id=str(uuid.uuid4()),
            node_type=intent_type,
            name=name,
            description=description,
            tags=tags or [],
            content=content or {},
        )
        self.graph.add_node(node)
        return node
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship: IntentEdgeType,
        weight: float = 1.0,
    ) -> IntentEdge:
        """
        添加意图关系
        
        Args:
            source_id: 源意图 ID
            target_id: 目标意图 ID
            relationship: 关系类型
            weight: 权重
            
        Returns:
            创建的边
        """
        import uuid
        edge = create_intent_edge(
            edge_id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            edge_type=relationship,
            weight=weight,
        )
        self.graph.add_edge(edge)
        return edge
    
    def search_intents(
        self,
        keyword: Optional[str] = None,
        tag: Optional[str] = None,
        node_id: Optional[str] = None,
    ) -> list[IntentNode]:
        """
        搜索意图
        
        Args:
            keyword: 关键词
            tag: 标签
            node_id: 节点 ID
            
        Returns:
            匹配的意图列表
        """
        if node_id:
            node = self.graph.get_node(node_id)
            return [node] if node else []
        
        if keyword:
            return self.graph.search_by_keyword(keyword)
        
        if tag:
            return self.graph.search_by_tag(tag)
        
        return list(self.graph.nodes.values())
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        """
        查找多跳路径
        
        Args:
            source_id: 源节点 ID
            target_id: 目标节点 ID
            max_depth: 最大深度
            
        Returns:
            路径列表
        """
        return self.graph.find_path(source_id, target_id, max_depth)
    
    def recommend_intents(
        self,
        node_id: str,
        num_recommendations: int = 5,
    ) -> list[IntentNode]:
        """
        推荐相关意图
        
        Args:
            node_id: 参考节点 ID
            num_recommendations: 推荐数量
            
        Returns:
            推荐的意图列表
        """
        recommender = IntentRecommender(self.graph)
        return recommender.recommend_by_node(node_id, num_recommendations)
    
    def get_graph_stats(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        return self.graph.get_statistics()
    
    # -------------------------------------------------------------------------
    # 验证 API
    # -------------------------------------------------------------------------
    
    def validate_dag(self, dag_nodes: list[DAGNode]) -> dict[str, Any]:
        """
        验证 DAG
        
        Args:
            dag_nodes: DAG 节点列表
            
        Returns:
            验证结果
        """
        result = self.verifier.dag_validator.validate(dag_nodes)
        return {
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
        }
    
    def register_capability(
        self,
        name: str,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        description: str = "",
    ) -> CapabilitySignature:
        """
        注册能力
        
        Args:
            name: 能力名称
            input_schema: 输入 Schema
            output_schema: 输出 Schema
            description: 描述
            
        Returns:
            能力签名
        """
        signature = create_capability_signature(
            name=name,
            input_schema=input_schema,
            output_schema=output_schema,
            description=description,
        )
        self.verifier.register_capability(signature)
        return signature
    
    def validate_capability_call(
        self,
        capability_name: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        验证能力调用
        
        Args:
            capability_name: 能力名称
            inputs: 输入参数
            
        Returns:
            验证结果
        """
        is_valid, errors = self.verifier.validate_capability_call(
            capability_name, inputs
        )
        return {
            "is_valid": is_valid,
            "errors": errors,
        }
    
    # -------------------------------------------------------------------------
    # 轨迹 API
    # -------------------------------------------------------------------------
    
    def create_trace(self, intent_id: str) -> ExecutionTrace:
        """
        创建执行轨迹
        
        Args:
            intent_id: 意图 ID
            
        Returns:
            执行轨迹
        """
        return create_execution_trace(intent_id)
    
    def replay_trace(
        self,
        trace: ExecutionTrace,
        step: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        回放执行轨迹
        
        Args:
            trace: 执行轨迹
            step: 单步步数（None 表示完整回放）
            
        Returns:
            回放的事件列表
        """
        replayer = TraceReplayer(trace)
        
        if step is not None:
            events = []
            for _ in range(step if step > 0 else len(trace.events)):
                event = replayer.step()
                if event:
                    events.append(event.to_dict())
                else:
                    break
            return events
        else:
            events = replayer.play_all()
            return [e.to_dict() for e in events]
    
    # -------------------------------------------------------------------------
    # 导出/导入
    # -------------------------------------------------------------------------
    
    def export_graph(self, filepath: str) -> None:
        """导出图谱到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.graph.to_dict(), f, indent=2, ensure_ascii=False)
    
    def import_graph(self, filepath: str) -> None:
        """从文件导入图谱"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.graph = IntentGraph()
        for node_data in data.get("nodes", {}).values():
            node = IntentNode.from_dict(node_data)
            self.graph.add_node(node)
        
        for edge_data in data.get("edges", {}).values():
            edge = IntentEdge.from_dict(edge_data)
            self.graph.add_edge(edge)
    
    def export_trace(self, trace: ExecutionTrace, filepath: str) -> None:
        """导出轨迹到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(trace.to_dict(), f, indent=2, ensure_ascii=False)
    
    def import_trace(self, filepath: str) -> ExecutionTrace:
        """从文件导入轨迹"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ExecutionTrace.from_dict(data)


# =============================================================================
# 便捷函数
# =============================================================================


def create_client(host: str = "localhost", port: int = 8080) -> IntentOSClient:
    """创建 IntentOS 客户端"""
    return IntentOSClient(host, port)


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 创建客户端
    client = create_client()
    
    # 创建意图
    intent1 = client.create_intent(
        name="分析销售数据",
        description="分析指定区域和时间的销售数据",
        tags=["销售", "分析"],
    )
    
    intent2 = client.create_intent(
        name="生成报表",
        description="生成销售报表",
        tags=["报表", "生成"],
    )
    
    # 添加关系
    client.add_relationship(
        source_id=intent1.node_id,
        target_id=intent2.node_id,
        relationship=IntentEdgeType.TRIGGERS,
    )
    
    # 搜索意图
    results = client.search_intents(keyword="销售")
    print(f"找到 {len(results)} 个意图")
    
    # 获取统计
    stats = client.get_graph_stats()
    print(f"图谱统计：{stats}")
    
    # 验证 DAG
    dag_nodes = [
        create_dag_node("task_1", "query", dependencies=[]),
        create_dag_node("task_2", "analyze", dependencies=["task_1"]),
        create_dag_node("task_3", "visualize", dependencies=["task_2"]),
    ]
    result = client.validate_dag(dag_nodes)
    print(f"DAG 验证：{'有效' if result['is_valid'] else '无效'}")
