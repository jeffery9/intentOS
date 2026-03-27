"""
意图图谱 (Intent Graph)

意图图谱是 IntentOS 的核心高级功能，用于：
1. 存储和管理所有意图及其关系
2. 支持复杂推理和多跳查询
3. 实现意图相似度计算和推荐
4. 支持意图复用和组合

核心数据结构:
- IntentNode: 意图节点
- IntentEdge: 意图边（关系）
- IntentGraph: 意图图谱
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# =============================================================================
# 意图节点类型
# =============================================================================


class IntentNodeType(Enum):
    """意图节点类型"""

    ATOMIC = "atomic"  # 原子意图
    COMPOSITE = "composite"  # 复合意图
    TEMPLATE = "template"  # 意图模板
    CAPABILITY = "capability"  # 能力
    CONTEXT = "context"  # 上下文


class IntentEdgeType(Enum):
    """意图边类型（关系类型）"""

    DEPENDS_ON = "depends_on"  # 依赖于
    SIMILAR_TO = "similar_to"  # 类似于
    COMPOSED_OF = "composed_of"  # 由...组成
    REQUIRES = "requires"  # 需要
    TRIGGERS = "triggers"  # 触发
    REFINES = "refines"  # 细化
    GENERALIZES = "generalizes"  # 泛化
    RELATED_TO = "related_to"  # 相关于


# =============================================================================
# 意图节点
# =============================================================================


@dataclass
class IntentNode:
    """
    意图节点
    
    图谱中的基本单元，表示一个意图、能力或上下文
    """
    node_id: str
    node_type: IntentNodeType
    name: str
    description: str = ""
    content: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0  # 使用次数
    confidence: float = 1.0  # 置信度
    tags: list[str] = field(default_factory=list)
    
    @property
    def embedding_key(self) -> str:
        """生成用于相似度计算的嵌入键"""
        content = f"{self.name}:{self.description}:{self.tags}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
            "confidence": self.confidence,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> IntentNode:
        """从字典反序列化"""
        return cls(
            node_id=data["node_id"],
            node_type=IntentNodeType(data["node_type"]),
            name=data["name"],
            description=data.get("description", ""),
            content=data.get("content", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            usage_count=data.get("usage_count", 0),
            confidence=data.get("confidence", 1.0),
            tags=data.get("tags", []),
        )


# =============================================================================
# 意图边
# =============================================================================


@dataclass
class IntentEdge:
    """
    意图边
    
    表示两个意图节点之间的关系
    """
    edge_id: str
    source_id: str  # 源节点 ID
    target_id: str  # 目标节点 ID
    edge_type: IntentEdgeType
    weight: float = 1.0  # 权重
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> IntentEdge:
        """从字典反序列化"""
        return cls(
            edge_id=data["edge_id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            edge_type=IntentEdgeType(data["edge_type"]),
            weight=data.get("weight", 1.0),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


# =============================================================================
# 意图图谱
# =============================================================================


class IntentGraph:
    """
    意图图谱
    
    存储和管理所有意图节点及其关系的图结构
    """
    
    def __init__(self):
        self.nodes: dict[str, IntentNode] = {}
        self.edges: dict[str, IntentEdge] = {}
        # 邻接表用于快速查询
        self.adjacency: dict[str, dict[str, str]] = {}  # node_id -> {neighbor_id -> edge_id}
        # 索引
        self.name_index: dict[str, list[str]] = {}  # name -> [node_id]
        self.tag_index: dict[str, list[str]] = {}  # tag -> [node_id]
    
    def add_node(self, node: IntentNode) -> None:
        """添加节点"""
        self.nodes[node.node_id] = node
        self.adjacency[node.node_id] = {}
        
        # 更新索引
        if node.name not in self.name_index:
            self.name_index[node.name] = []
        self.name_index[node.name].append(node.node_id)
        
        for tag in node.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(node.node_id)
    
    def remove_node(self, node_id: str) -> None:
        """删除节点及其相关边"""
        if node_id not in self.nodes:
            return
        
        # 删除所有相关边
        edges_to_remove = list(self.adjacency.get(node_id, {}).keys())
        for neighbor_id in edges_to_remove:
            self.remove_edge(node_id, neighbor_id)
        
        # 从邻接表中删除
        if node_id in self.adjacency:
            del self.adjacency[node_id]
        
        # 从索引中删除
        node = self.nodes[node_id]
        if node.name in self.name_index:
            self.name_index[node.name].remove(node_id)
        for tag in node.tags:
            if tag in self.tag_index:
                self.tag_index[tag].remove(node_id)
        
        # 删除节点
        del self.nodes[node_id]
    
    def add_edge(self, edge: IntentEdge) -> None:
        """添加边"""
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError(f"边的源节点或目标节点不存在")
        
        self.edges[edge.edge_id] = edge
        
        # 更新邻接表
        self.adjacency[edge.source_id][edge.target_id] = edge.edge_id
        
        # 如果是无向关系，添加反向边
        if edge.edge_type in [IntentEdgeType.SIMILAR_TO, IntentEdgeType.RELATED_TO]:
            reverse_edge = IntentEdge(
                edge_id=f"{edge.edge_id}_reverse",
                source_id=edge.target_id,
                target_id=edge.source_id,
                edge_type=edge.edge_type,
                weight=edge.weight,
                metadata=edge.metadata,
            )
            self.edges[reverse_edge.edge_id] = reverse_edge
            self.adjacency[edge.target_id][edge.source_id] = reverse_edge.edge_id
    
    def remove_edge(self, source_id: str, target_id: str) -> None:
        """删除边"""
        if source_id not in self.adjacency:
            return
        
        edge_id = self.adjacency[source_id].get(target_id)
        if edge_id:
            del self.adjacency[source_id][target_id]
            if edge_id in self.edges:
                del self.edges[edge_id]
    
    def get_node(self, node_id: str) -> Optional[IntentNode]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str, edge_type: Optional[IntentEdgeType] = None) -> list[IntentNode]:
        """获取邻居节点"""
        if node_id not in self.adjacency:
            return []
        
        neighbors = []
        for neighbor_id, edge_id in self.adjacency[node_id].items():
            edge = self.edges.get(edge_id)
            if edge and (edge_type is None or edge.edge_type == edge_type):
                neighbor = self.nodes.get(neighbor_id)
                if neighbor:
                    neighbors.append(neighbor)
        
        return neighbors
    
    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> list[list[str]]:
        """
        查找两个节点之间的所有路径（多跳查询）
        
        Args:
            source_id: 源节点 ID
            target_id: 目标节点 ID
            max_depth: 最大深度
            
        Returns:
            所有路径列表，每条路径是节点 ID 列表
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        
        paths = []
        self._dfs_paths(source_id, target_id, [source_id], paths, max_depth)
        return paths
    
    def _dfs_paths(
        self,
        current_id: str,
        target_id: str,
        path: list[str],
        paths: list[list[str]],
        max_depth: int,
    ) -> None:
        """DFS 查找所有路径"""
        if len(path) > max_depth:
            return
        
        if current_id == target_id:
            paths.append(path.copy())
            return
        
        for neighbor_id in self.adjacency.get(current_id, {}).keys():
            if neighbor_id not in path:  # 避免循环
                path.append(neighbor_id)
                self._dfs_paths(neighbor_id, target_id, path, paths, max_depth)
                path.pop()
    
    def search_by_name(self, name: str) -> list[IntentNode]:
        """按名称搜索节点"""
        node_ids = self.name_index.get(name, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def search_by_tag(self, tag: str) -> list[IntentNode]:
        """按标签搜索节点"""
        node_ids = self.tag_index.get(tag, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def search_by_keyword(self, keyword: str) -> list[IntentNode]:
        """按关键词搜索（名称、描述、标签）"""
        results = []
        keyword_lower = keyword.lower()
        
        for node in self.nodes.values():
            if (keyword_lower in node.name.lower() or
                keyword_lower in node.description.lower() or
                any(keyword_lower in tag.lower() for tag in node.tags)):
                results.append(node)
        
        return results
    
    def get_statistics(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        node_types = {}
        edge_types = {}
        
        for node in self.nodes.values():
            node_type = node.node_type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        for edge in self.edges.values():
            edge_type = edge.edge_type.value
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "avg_degree": sum(len(neighbors) for neighbors in self.adjacency.values()) / max(1, len(self.nodes)),
        }
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": {eid: edge.to_dict() for eid, edge in self.edges.items()},
            "statistics": self.get_statistics(),
        }


# =============================================================================
# 意图相似度计算
# =============================================================================


class IntentSimilarityCalculator:
    """
    意图相似度计算器
    
    计算两个意图节点之间的相似度
    """
    
    @staticmethod
    def jaccard_similarity(set1: set, set2: set) -> float:
        """计算 Jaccard 相似度"""
        if not set1 and not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def calculate(self, node1: IntentNode, node2: IntentNode) -> float:
        """
        计算两个意图节点的相似度
        
        综合考虑：
        1. 标签相似度 (Jaccard)
        2. 名称相似度 (编辑距离)
        3. 描述相似度 (关键词重叠)
        """
        # 标签相似度
        tags1 = set(node1.tags)
        tags2 = set(node2.tags)
        tag_sim = self.jaccard_similarity(tags1, tags2)
        
        # 名称相似度
        name_sim = self._name_similarity(node1.name, node2.name)
        
        # 描述相似度
        desc_sim = self._description_similarity(node1.description, node2.description)
        
        # 加权平均
        similarity = 0.4 * tag_sim + 0.4 * name_sim + 0.2 * desc_sim
        return similarity
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度（基于编辑距离）"""
        if name1 == name2:
            return 1.0
        
        # 简单的字符重叠相似度
        set1 = set(name1.lower())
        set2 = set(name2.lower())
        return self.jaccard_similarity(set1, set2)
    
    def _description_similarity(self, desc1: str, desc2: str) -> float:
        """计算描述相似度（基于关键词重叠）"""
        if not desc1 or not desc2:
            return 0.0
        
        # 分词
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        
        # 去除停用词
        stopwords = {"的", "是", "在", "和", "与", "或", "了", "一个", "the", "a", "an", "is", "are"}
        words1 -= stopwords
        words2 -= stopwords
        
        return self.jaccard_similarity(words1, words2)
    
    def find_similar_intents(
        self,
        node: IntentNode,
        graph: IntentGraph,
        threshold: float = 0.5,
        top_k: int = 10,
    ) -> list[tuple[IntentNode, float]]:
        """
        查找相似的意图
        
        Args:
            node: 查询节点
            graph: 意图图谱
            threshold: 相似度阈值
            top_k: 返回的最大数量
            
        Returns:
            (节点，相似度) 列表，按相似度降序排列
        """
        similarities = []
        
        for other_node in graph.nodes.values():
            if other_node.node_id == node.node_id:
                continue
            
            sim = self.calculate(node, other_node)
            if sim >= threshold:
                similarities.append((other_node, sim))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# =============================================================================
# 意图推荐
# =============================================================================


class IntentRecommender:
    """
    意图推荐器
    
    基于图谱结构和相似度推荐相关意图
    """
    
    def __init__(self, graph: IntentGraph):
        self.graph = graph
        self.similarity_calculator = IntentSimilarityCalculator()
    
    def recommend_by_node(
        self,
        node_id: str,
        num_recommendations: int = 5,
    ) -> list[IntentNode]:
        """
        基于给定节点推荐相关意图
        
        考虑：
        1. 直接邻居
        2. 相似节点
        """
        node = self.graph.get_node(node_id)
        if not node:
            return []
        
        recommendations = []
        seen = {node_id}
        
        # 1. 添加直接邻居
        for neighbor in self.graph.get_neighbors(node_id):
            if neighbor.node_id not in seen:
                recommendations.append((neighbor, 1.0))  # 直接连接，权重 1.0
                seen.add(neighbor.node_id)
        
        # 2. 添加相似节点
        similar = self.similarity_calculator.find_similar_intents(
            node, self.graph, threshold=0.3, top_k=num_recommendations
        )
        for similar_node, sim in similar:
            if similar_node.node_id not in seen:
                recommendations.append((similar_node, sim * 0.8))  # 相似度权重
                seen.add(similar_node.node_id)
        
        # 按权重排序
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [node for node, _ in recommendations[:num_recommendations]]
    
    def recommend_by_context(
        self,
        context_tags: list[str],
        num_recommendations: int = 5,
    ) -> list[IntentNode]:
        """
        基于上下文标签推荐意图
        
        Args:
            context_tags: 上下文标签列表
            num_recommendations: 推荐数量
        """
        candidates = {}
        
        # 收集所有相关标签的节点
        for tag in context_tags:
            nodes = self.graph.search_by_tag(tag)
            for node in nodes:
                if node.node_id not in candidates:
                    candidates[node.node_id] = (node, 0)
                # 每匹配一个标签，权重 +1
                candidates[node.node_id] = (node, candidates[node.node_id][1] + 1)
        
        # 按匹配标签数排序
        sorted_candidates = sorted(
            candidates.values(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        return [node for node, _ in sorted_candidates[:num_recommendations]]


# =============================================================================
# 工厂函数
# =============================================================================


def create_intent_node(
    node_id: str,
    node_type: IntentNodeType,
    name: str,
    description: str = "",
    content: Optional[dict] = None,
    tags: Optional[list[str]] = None,
) -> IntentNode:
    """创建意图节点"""
    return IntentNode(
        node_id=node_id,
        node_type=node_type,
        name=name,
        description=description,
        content=content or {},
        tags=tags or [],
    )


def create_intent_edge(
    edge_id: str,
    source_id: str,
    target_id: str,
    edge_type: IntentEdgeType,
    weight: float = 1.0,
) -> IntentEdge:
    """创建意图边"""
    return IntentEdge(
        edge_id=edge_id,
        source_id=source_id,
        target_id=target_id,
        edge_type=edge_type,
        weight=weight,
    )


def create_intent_graph() -> IntentGraph:
    """创建意图图谱"""
    return IntentGraph()
