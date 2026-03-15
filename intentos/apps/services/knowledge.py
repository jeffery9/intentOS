"""
知识系统

为 AI Agent 提供知识库和知识图谱能力
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class KnowledgeItem:
    """知识条目"""
    id: str
    title: str
    content: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""  # 来源
    confidence: float = 1.0  # 置信度
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "source": self.source,
            "confidence": self.confidence,
        }


@dataclass
class KnowledgeRelation:
    """知识关系"""
    from_id: str
    to_id: str
    relation_type: str  # is_a, part_of, related_to, etc.
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeBase:
    """
    知识库
    
    存储结构化知识
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.expanduser("~/.intentos/knowledge")
        self.items: dict[str, KnowledgeItem] = {}
        self._load()
    
    def add(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: Optional[list[str]] = None,
        source: str = "",
    ) -> KnowledgeItem:
        """添加知识"""
        import hashlib
        item_id = hashlib.md5(f"{title}{content}".encode()).hexdigest()[:12]

        item = KnowledgeItem(
            id=item_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            source=source,
        )
        
        self.items[item_id] = item
        self._save()
        
        return item
    
    def get(self, item_id: str) -> Optional[KnowledgeItem]:
        """获取知识"""
        return self.items.get(item_id)
    
    def search(self, query: str, limit: int = 10) -> list[KnowledgeItem]:
        """搜索知识"""
        query_lower = query.lower()
        
        scored = []
        for item in self.items.values():
            score = 0
            
            # 标题匹配
            if query_lower in item.title.lower():
                score += 0.5
            
            # 内容匹配
            if query_lower in item.content.lower():
                score += 0.3
            
            # 标签匹配
            if any(query_lower in tag.lower() for tag in item.tags):
                score += 0.2
            
            if score > 0:
                scored.append((score, item))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]
    
    def get_by_category(self, category: str) -> list[KnowledgeItem]:
        """按分类获取"""
        return [
            item for item in self.items.values()
            if item.category == category
        ]
    
    def delete(self, item_id: str) -> bool:
        """删除知识"""
        if item_id in self.items:
            del self.items[item_id]
            self._save()
            return True
        return False
    
    def _load(self) -> None:
        """加载知识"""
        os.makedirs(self.storage_path, exist_ok=True)
        knowledge_file = os.path.join(self.storage_path, "knowledge.json")
        
        if os.path.exists(knowledge_file):
            with open(knowledge_file) as f:
                data = json.load(f)
                for id, item_data in data.items():
                    self.items[id] = KnowledgeItem(**item_data)
    
    def _save(self) -> None:
        """保存知识"""
        os.makedirs(self.storage_path, exist_ok=True)
        knowledge_file = os.path.join(self.storage_path, "knowledge.json")
        
        data = {id: item.to_dict() for id, item in self.items.items()}
        with open(knowledge_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self.items),
            "categories": list(set(i.category for i in self.items.values())),
            "storage_path": self.storage_path,
        }


class KnowledgeGraph:
    """
    知识图谱
    
    存储知识之间的关系
    """
    
    def __init__(self):
        self.relations: list[KnowledgeRelation] = []
    
    def add_relation(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        weight: float = 1.0
    ) -> KnowledgeRelation:
        """添加关系"""
        relation = KnowledgeRelation(
            from_id=from_id,
            to_id=to_id,
            relation_type=relation_type,
            weight=weight,
        )
        
        self.relations.append(relation)
        return relation
    
    def get_relations(self, item_id: str) -> list[KnowledgeRelation]:
        """获取实体的关系"""
        return [
            r for r in self.relations
            if r.from_id == item_id or r.to_id == item_id
        ]
    
    def get_connected(self, item_id: str, knowledge_base: KnowledgeBase) -> list[KnowledgeItem]:
        """获取关联的知识"""
        relations = self.get_relations(item_id)
        connected_ids = set()
        
        for r in relations:
            if r.from_id == item_id:
                connected_ids.add(r.to_id)
            else:
                connected_ids.add(r.from_id)
        
        return [
            knowledge_base.get(id)
            for id in connected_ids
            if knowledge_base.get(id)
        ]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_count": len(self.relations),
            "relation_types": list(set(r.relation_type for r in self.relations)),
        }


# ========== 预定义知识 ==========

def load_builtin_knowledge(kb: KnowledgeBase) -> None:
    """加载内置知识"""
    
    # 公司信息
    kb.add(
        title="IntentOS 公司信息",
        content="IntentOS 是一个 AI 原生操作系统项目，致力于将自然语言意图编译为可执行程序。",
        category="company",
        tags=["IntentOS", "AI", "操作系统"],
        source="builtin",
    )
    
    # 产品知识
    kb.add(
        title="IntentOS 核心特性",
        content="""
IntentOS 的核心特性包括：
1. 语义虚拟机 (SVM) - LLM 作为处理器
2. Self-Bootstrap - 系统自我演化
3. 分布式部署 - 多节点集群
4. 意图编译器 - 自然语言到 Prompt
""",
        category="product",
        tags=["特性", "核心"],
        source="builtin",
    )
    
    # 用户偏好示例
    kb.add(
        title="默认用户偏好",
        content="""
默认偏好设置：
- 语言：中文
- 时区：Asia/Shanghai
- 日期格式：YYYY-MM-DD
- 时间格式：24 小时制
""",
        category="preferences",
        tags=["偏好", "默认"],
        source="builtin",
    )
