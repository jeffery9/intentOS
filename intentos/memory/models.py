# -*- coding: utf-8 -*-
"""
IntentOS Memory Models

记忆数据模型
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class MemoryContentType(Enum):
    """记忆内容类型（新系统：按内容分类）
    
    与 types.py 的 MemoryType（按存储时间分类）互补：
    - MemoryType: WORKING/SHORT_TERM/LONG_TERM（存储位置）
    - MemoryContentType: SUCCESS/FAILURE/PATTERN（内容性质）
    """
    SUCCESS = "success"      # 成功做法
    FAILURE = "failure"      # 失败教训
    PATTERN = "pattern"      # 识别的模式
    CONTEXT = "context"      # 上下文信息
    SKILL = "skill"          # 技能引用


@dataclass
class Pattern:
    """模式"""
    name: str
    description: str
    trigger_keywords: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 置信度 0-1
    occurrences: int = 1     # 出现次数
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "trigger_keywords": self.trigger_keywords,
            "steps": self.steps,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
        }


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    memory_type: MemoryContentType = MemoryContentType.CONTEXT
    content: str = ""  # 记忆内容
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # 成功/失败特有字段
    successes: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    patterns: list[Pattern] = field(default_factory=list)
    
    # 上下文
    context: dict[str, Any] = field(default_factory=dict)
    
    # 标签
    tags: list[str] = field(default_factory=list)
    
    # 重要性评分 (0-10)
    importance: float = 5.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "memory_type": self.memory_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "successes": self.successes,
            "failures": self.failures,
            "patterns": [p.to_dict() for p in self.patterns],
            "context": self.context,
            "tags": self.tags,
            "importance": self.importance,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            session_id=data.get("session_id", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            memory_type=MemoryContentType(data.get("memory_type", "context")),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            successes=data.get("successes", []),
            failures=data.get("failures", []),
            patterns=[Pattern(**p) for p in data.get("patterns", [])],
            context=data.get("context", {}),
            tags=data.get("tags", []),
            importance=data.get("importance", 5.0),
        )


@dataclass
class SessionMemory:
    """会话记忆"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    memory_entries: list[MemoryEntry] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    
    # 会话元数据
    user_id: Optional[str] = None
    node_id: Optional[str] = None
    intent_count: int = 0
    success_count: int = 0
    error_count: int = 0
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
    
    def add_memory_entry(self, entry: MemoryEntry) -> None:
        """添加记忆条目"""
        self.memory_entries.append(entry)
    
    def end_session(self) -> None:
        """结束会话"""
        self.end_time = datetime.now()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "messages": self.messages,
            "memory_entries": [e.to_dict() for e in self.memory_entries],
            "tags": self.tags,
            "user_id": self.user_id,
            "node_id": self.node_id,
            "intent_count": self.intent_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMemory":
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            start_time=datetime.fromisoformat(data["start_time"]) if "start_time" in data else datetime.now(),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            messages=data.get("messages", []),
            memory_entries=[MemoryEntry.from_dict(e) for e in data.get("memory_entries", [])],
            tags=data.get("tags", []),
            user_id=data.get("user_id"),
            node_id=data.get("node_id"),
            intent_count=data.get("intent_count", 0),
            success_count=data.get("success_count", 0),
            error_count=data.get("error_count", 0),
        )


@dataclass
class MemoryQuery:
    """记忆查询"""
    session_id: Optional[str] = None
    memory_type: Optional[MemoryContentType] = None
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_importance: float = 0.0
    limit: int = 100
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "memory_type": self.memory_type.value if self.memory_type else None,
            "keywords": self.keywords,
            "tags": self.tags,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "min_importance": self.min_importance,
            "limit": self.limit,
        }
