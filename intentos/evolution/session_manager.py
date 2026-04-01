# -*- coding: utf-8 -*-
"""
IntentOS Session Manager

会话管理器 - 管理会话生命周期和上下文
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ..memory.models import SessionMemory
from ..memory.store import MemoryStore, get_memory_store

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """
    会话上下文
    
    包含会话的所有相关信息
    """
    session_id: str
    user_id: str
    start_time: datetime = field(default_factory=datetime.now)
    
    # 对话历史
    messages: list[dict[str, Any]] = field(default_factory=list)
    
    # 关联的记忆 ID
    memory_ids: list[str] = field(default_factory=list)
    
    # 使用的技能
    skills_used: list[str] = field(default_factory=list)
    
    # 自定义元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # 状态
    is_active: bool = True
    end_time: Optional[datetime] = None
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
    
    def add_memory(self, memory_id: str) -> None:
        """添加记忆引用"""
        self.memory_ids.append(memory_id)
    
    def add_skill(self, skill_id: str) -> None:
        """添加技能使用记录"""
        self.skills_used.append(skill_id)
    
    def end(self) -> None:
        """结束会话"""
        self.is_active = False
        self.end_time = datetime.now()
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "messages": self.messages,
            "memory_ids": self.memory_ids,
            "skills_used": self.skills_used,
            "metadata": self.metadata,
            "is_active": self.is_active,
        }


class SessionManager:
    """
    会话管理器
    
    管理所有会话的生命周期：
    - 创建会话
    - 添加消息
    - 结束会话
    - 查询历史
    """
    
    def __init__(self, memory_store: Optional[MemoryStore] = None):
        self.memory_store = memory_store or get_memory_store()
        
        # 活跃会话
        self.active_sessions: dict[str, SessionContext] = {}
        
        # 会话历史索引
        self.session_history: dict[str, list[str]] = {}  # user_id -> [session_id, ...]
        
        logger.info("会话管理器初始化完成")
    
    def create_session(
        self,
        user_id: str = "default",
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SessionContext:
        """
        创建新会话
        
        Args:
            user_id: 用户 ID
            session_id: 会话 ID（可选，自动生成）
            metadata: 自定义元数据
            
        Returns:
            会话上下文
        """
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        
        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )
        
        self.active_sessions[session_id] = context
        
        # 添加到用户历史
        if user_id not in self.session_history:
            self.session_history[user_id] = []
        self.session_history[user_id].append(session_id)
        
        logger.info(f"创建会话：{session_id} (user={user_id})")
        return context
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """获取会话"""
        # 检查活跃会话
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # 从存储加载
        session_memory = self.memory_store.get_session(session_id)
        if session_memory:
            context = SessionContext(
                session_id=session_id,
                user_id=session_memory.user_id or "default",
                start_time=session_memory.start_time,
                end_time=session_memory.end_time,
                messages=session_memory.messages,
            )
            context.is_active = False
            return context
        
        return None
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> bool:
        """
        添加消息到会话
        
        Args:
            session_id: 会话 ID
            role: 角色（user/assistant）
            content: 消息内容
            
        Returns:
            是否成功
        """
        context = self.get_session(session_id)
        if not context:
            logger.warning(f"会话不存在：{session_id}")
            return False
        
        context.add_message(role, content)
        return True
    
    def end_session(self, session_id: str) -> bool:
        """
        结束会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否成功
        """
        context = self.get_session(session_id)
        if not context:
            return False
        
        context.end()
        
        # 从活跃会话移除
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # 保存到存储
        session_memory = SessionMemory(
            session_id=session_id,
            start_time=context.start_time,
            end_time=context.end_time,
            messages=context.messages,
            user_id=context.user_id,
        )
        self.memory_store.save_session(session_memory)
        
        logger.info(f"结束会话：{session_id}")
        return True
    
    def get_user_sessions(
        self,
        user_id: str,
        limit: int = 10,
        active_only: bool = False,
    ) -> list[SessionContext]:
        """
        获取用户的会话列表
        
        Args:
            user_id: 用户 ID
            limit: 数量限制
            active_only: 只返回活跃会话
            
        Returns:
            会话上下文列表
        """
        if active_only:
            return [
                ctx for ctx in self.active_sessions.values()
                if ctx.user_id == user_id and ctx.is_active
            ]
        
        # 从历史获取
        session_ids = self.session_history.get(user_id, [])
        sessions = []
        
        for sid in session_ids[-limit:]:
            context = self.get_session(sid)
            if context:
                sessions.append(context)
        
        return sessions
    
    def get_active_session_count(self) -> int:
        """获取活跃会话数量"""
        return len(self.active_sessions)
    
    def cleanup_inactive(self, max_age_hours: int = 24) -> int:
        """
        清理非活跃会话
        
        Args:
            max_age_hours: 最大保留小时数
            
        Returns:
            清理的会话数量
        """
        now = datetime.now()
        cleaned = 0
        
        to_remove = []
        for session_id, context in self.active_sessions.items():
            if not context.is_active:
                age = (now - context.start_time).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(session_id)
        
        for session_id in to_remove:
            self.end_session(session_id)
            cleaned += 1
        
        if cleaned > 0:
            logger.info(f"清理了 {cleaned} 个非活跃会话")
        
        return cleaned
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        # 按用户统计
        user_counts = {}
        for context in self.active_sessions.values():
            uid = context.user_id
            user_counts[uid] = user_counts.get(uid, 0) + 1
        
        # 总会话数
        total_sessions = sum(len(sessions) for sessions in self.session_history.values())
        
        return {
            "active_sessions": len(self.active_sessions),
            "total_sessions": total_sessions,
            "users": len(self.session_history),
            "active_by_user": user_counts,
        }
