"""
记忆系统

为 AI Agent 提供短期记忆和长期记忆能力
"""

from __future__ import annotations

import json
import os
import hashlib
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class Memory:
    """记忆条目"""
    id: str
    content: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 重要性 0-1
    access_count: int = 0  # 访问次数
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at,
            "tags": self.tags,
            "metadata": self.metadata,
            "importance": self.importance,
            "access_count": self.access_count,
        }


class ShortTermMemory:
    """
    短期记忆
    
    存储最近的对话历史和上下文
    特点：
    - 容量有限（最近 N 条）
    - 快速访问
    - 会话结束后清除
    """
    
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.memories: list[Memory] = []
    
    def add(
        self,
        content: str,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> Memory:
        """添加记忆"""
        memory = Memory(
            id=self._generate_id(content),
            content=content,
            tags=tags or [],
            metadata=metadata or {},
        )

        self.memories.append(memory)

        # 超出容量时删除最旧的
        if len(self.memories) > self.max_size:
            self.memories.pop(0)
        
        return memory
    
    def get_recent(self, limit: int = 10) -> list[Memory]:
        """获取最近的记忆"""
        return self.memories[-limit:]
    
    def search(self, query: str) -> list[Memory]:
        """搜索记忆"""
        query_lower = query.lower()
        return [
            m for m in self.memories
            if query_lower in m.content.lower() or
               any(query_lower in tag.lower() for tag in m.tags)
        ]
    
    def clear(self) -> None:
        """清空记忆"""
        self.memories.clear()
    
    def get_context(self) -> str:
        """获取上下文文本"""
        if not self.memories:
            return ""
        
        lines = []
        for m in self.memories[-10:]:
            lines.append(f"[{m.created_at[11:19]}] {m.content}")
        
        return "\n".join(lines)
    
    def _generate_id(self, content: str) -> str:
        """生成 ID"""
        return hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "short_term",
            "count": len(self.memories),
            "max_size": self.max_size,
            "memories": [m.to_dict() for m in self.memories[-10:]],
        }


class LongTermMemory:
    """
    长期记忆
    
    存储重要信息和知识
    特点：
    - 持久化存储
    - 支持向量搜索
    - 跨会话保留
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.expanduser("~/.intentos/memory")
        self.memories: dict[str, Memory] = {}
        self._load()
    
    def add(
        self,
        content: str,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        importance: float = 0.5
    ) -> Memory:
        """添加记忆"""
        memory = Memory(
            id=self._generate_id(content),
            content=content,
            tags=tags or [],
            metadata=metadata or {},
            importance=importance,
        )

        self.memories[memory.id] = memory
        self._save()

        return memory
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        memory = self.memories.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.updated_at = datetime.now().isoformat()
            self._save()
        return memory
    
    def search(self, query: str, limit: int = 10) -> list[Memory]:
        """搜索记忆"""
        query_lower = query.lower()
        
        # 简单文本搜索（实际应该用向量搜索）
        scored: list[tuple[float, Memory]] = []
        for memory in self.memories.values():
            score: float = 0.0

            # 内容匹配
            if query_lower in memory.content.lower():
                score += 0.5

            # 标签匹配
            if memory.tags and any(query_lower in tag.lower() for tag in memory.tags):
                score += 0.3

            # 重要性
            score += memory.importance * 0.2

            if score > 0:
                scored.append((score, memory))
        
        # 按分数排序
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [m for _, m in scored[:limit]]
    
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self.memories:
            del self.memories[memory_id]
            self._save()
            return True
        return False
    
    def get_by_tags(self, tags: list[str]) -> list[Memory]:
        """按标签获取"""
        result = []
        for memory in self.memories.values():
            if any(tag in memory.tags for tag in tags):
                result.append(memory)
        return result
    
    def get_important(self, limit: int = 20) -> list[Memory]:
        """获取重要记忆"""
        sorted_mem = sorted(
            self.memories.values(),
            key=lambda m: m.importance,
            reverse=True
        )
        return sorted_mem[:limit]
    
    def _generate_id(self, content: str) -> str:
        """生成 ID"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _load(self) -> None:
        """加载记忆"""
        os.makedirs(self.storage_path, exist_ok=True)
        memory_file = os.path.join(self.storage_path, "long_term.json")
        
        if os.path.exists(memory_file):
            with open(memory_file) as f:
                data = json.load(f)
                for id, m_data in data.items():
                    self.memories[id] = Memory(**m_data)
    
    def _save(self) -> None:
        """保存记忆"""
        os.makedirs(self.storage_path, exist_ok=True)
        memory_file = os.path.join(self.storage_path, "long_term.json")
        
        data = {id: m.to_dict() for id, m in self.memories.items()}
        with open(memory_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "long_term",
            "count": len(self.memories),
            "storage_path": self.storage_path,
            "important_count": len(self.get_important()),
        }


class MemorySystem:
    """
    记忆系统
    
    统一管理短期和长期记忆
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(
            storage_path=os.path.expanduser(f"~/.intentos/memory/{user_id}")
        )
    
    def add_conversation(
        self,
        intent: str,
        response: str,
        tags: Optional[list[str]] = None
    ) -> None:
        """添加对话到记忆"""
        # 短期记忆
        self.short_term.add(
            content=f"用户：{intent}\n助手：{response}",
            tags=tags or ["conversation"],
        )

        # 长期记忆（重要对话）
        if self._is_important(intent, response):
            self.long_term.add(
                content=f"对话：{intent}",
                tags=["conversation"] + (tags or []),
                importance=0.7,
            )
    
    def get_context(self) -> dict[str, Any]:
        """获取完整上下文"""
        return {
            "short_term": self.short_term.get_context(),
            "important_memories": [
                m.content for m in self.long_term.get_important(5)
            ],
        }
    
    def search(self, query: str) -> list[dict]:
        """搜索记忆"""
        short_results = self.short_term.search(query)
        long_results = self.long_term.search(query)
        
        return [
            {"source": "short_term", **m.to_dict()}
            for m in short_results
        ] + [
            {"source": "long_term", **m.to_dict()}
            for m in long_results
        ]
    
    def _is_important(self, intent: str, response: str) -> bool:
        """判断是否重要"""
        # 简单规则：包含特定关键词
        important_keywords = ["偏好", "喜欢", "重要", "记住", "收藏"]
        return any(kw in intent for kw in important_keywords)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "short_term": self.short_term.to_dict(),
            "long_term": self.long_term.to_dict(),
        }
