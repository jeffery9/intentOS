# -*- coding: utf-8 -*-
"""
IntentOS Memory Store

记忆存储和检索
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import MemoryEntry, MemoryQuery, MemoryContentType, SessionMemory

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    记忆存储器
    
    支持：
    - 会话存储和检索
    - 记忆条目查询
    - 持久化（JSON 文件）
    - 内存缓存
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化记忆存储器
        
        Args:
            storage_dir: 存储目录，默认 ~/.intentos/memory
        """
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.intentos/memory")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._sessions: dict[str, SessionMemory] = {}
        self._entries: dict[str, MemoryEntry] = {}
        
        # 加载已存储的数据
        self._load_from_disk()
        
        logger.info(f"MemoryStore 初始化完成：{self.storage_dir}")
    
    def save_session(self, session: SessionMemory) -> None:
        """保存会话"""
        self._sessions[session.session_id] = session
        
        # 索引记忆条目
        for entry in session.memory_entries:
            self._entries[entry.id] = entry
        
        # 持久化
        self._persist_session(session)
        logger.debug(f"会话 {session.session_id} 已保存")
    
    def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """获取会话"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # 尝试从磁盘加载
        session = self._load_session_from_disk(session_id)
        if session:
            self._sessions[session_id] = session
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id not in self._sessions:
            session = self._load_session_from_disk(session_id)
            if session:
                self._sessions[session_id] = session
        
        if session_id in self._sessions:
            session = self._sessions[session_id]
            
            # 删除记忆条目索引
            for entry in session.memory_entries:
                self._entries.pop(entry.id, None)
            
            # 删除缓存
            del self._sessions[session_id]
            
            # 删除磁盘文件
            self._delete_session_file(session_id)
            
            logger.info(f"会话 {session_id} 已删除")
            return True
        
        return False
    
    def get_memory_entry(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        return self._entries.get(entry_id)
    
    def query_memories(self, query: MemoryQuery) -> list[MemoryEntry]:
        """查询记忆"""
        results = []
        
        for entry in self._entries.values():
            # 过滤条件
            if not self._matches_query(entry, query):
                continue
            
            results.append(entry)
        
        # 排序（按重要性）
        results.sort(key=lambda e: e.importance, reverse=True)
        
        # 限制数量
        return results[:query.limit]
    
    def query_sessions(self, query: MemoryQuery) -> list[SessionMemory]:
        """查询会话"""
        results = []
        
        for session in self._sessions.values():
            # 过滤条件
            if not self._matches_session_query(session, query):
                continue
            
            results.append(session)
        
        # 排序（按结束时间）
        results.sort(
            key=lambda s: s.end_time or s.start_time,
            reverse=True
        )
        
        # 限制数量
        return results[:query.limit]
    
    def get_recent_sessions(self, limit: int = 10) -> list[SessionMemory]:
        """获取最近的会话"""
        sessions = list(self._sessions.values())
        sessions.sort(
            key=lambda s: s.end_time or s.start_time,
            reverse=True
        )
        return sessions[:limit]
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total_entries = len(self._entries)
        total_sessions = len(self._sessions)
        
        # 按类型统计
        type_counts = {}
        for entry in self._entries.values():
            t = entry.memory_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # 按标签统计
        tag_counts = {}
        for entry in self._entries.values():
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "total_entries": total_entries,
            "by_type": type_counts,
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        }
    
    def clear_all(self) -> None:
        """清除所有记忆"""
        self._sessions.clear()
        self._entries.clear()
        
        # 清除磁盘文件
        for file in self.storage_dir.glob("*.json"):
            file.unlink()
        
        logger.info("所有记忆已清除")
    
    def _matches_query(self, entry: MemoryEntry, query: MemoryQuery) -> bool:
        """检查记忆是否匹配查询"""
        # 会话 ID
        if query.session_id and entry.session_id != query.session_id:
            return False
        
        # 类型
        if query.memory_type and entry.memory_type != query.memory_type:
            return False
        
        # 关键词
        if query.keywords:
            content = (entry.content + " ".join(entry.tags)).lower()
            if not any(kw.lower() in content for kw in query.keywords):
                return False
        
        # 标签
        if query.tags:
            if not any(tag in entry.tags for tag in query.tags):
                return False
        
        # 时间范围
        if query.start_time and entry.timestamp < query.start_time:
            return False
        if query.end_time and entry.timestamp > query.end_time:
            return False
        
        # 重要性
        if entry.importance < query.min_importance:
            return False
        
        return True
    
    def _matches_session_query(self, session: SessionMemory, query: MemoryQuery) -> bool:
        """检查会话是否匹配查询"""
        # 会话 ID
        if query.session_id and session.session_id != query.session_id:
            return False
        
        # 标签
        if query.tags:
            if not any(tag in session.tags for tag in query.tags):
                return False
        
        # 时间范围
        if query.start_time and session.start_time < query.start_time:
            return False
        if query.end_time and session.start_time > query.end_time:
            return False
        
        # 关键词（搜索消息内容）
        if query.keywords:
            content = " ".join([m["content"] for m in session.messages]).lower()
            if not any(kw.lower() in content for kw in query.keywords):
                return False
        
        return True
    
    def _persist_session(self, session: SessionMemory) -> None:
        """持久化会话到磁盘"""
        file_path = self.storage_dir / f"{session.session_id}.json"
        
        data = {
            "version": "1.0",
            "session": session.to_dict(),
            "saved_at": datetime.now().isoformat(),
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_session_from_disk(self, session_id: str) -> Optional[SessionMemory]:
        """从磁盘加载会话"""
        file_path = self.storage_dir / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            session = SessionMemory.from_dict(data["session"])
            return session
        except Exception as e:
            logger.error(f"加载会话失败：{e}")
            return None
    
    def _load_from_disk(self) -> None:
        """从磁盘加载所有会话"""
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                session = SessionMemory.from_dict(data["session"])
                self._sessions[session.session_id] = session
                
                # 索引记忆条目
                for entry in session.memory_entries:
                    self._entries[entry.id] = entry
                
            except Exception as e:
                logger.error(f"加载文件 {file_path} 失败：{e}")
        
        logger.info(f"从磁盘加载了 {len(self._sessions)} 个会话")
    
    def _delete_session_file(self, session_id: str) -> None:
        """删除会话文件"""
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()


# 全局记忆存储器实例
_global_memory_store: Optional[MemoryStore] = None


def get_memory_store(storage_dir: Optional[str] = None) -> MemoryStore:
    """获取全局记忆存储器"""
    global _global_memory_store
    if _global_memory_store is None:
        _global_memory_store = MemoryStore(storage_dir)
    return _global_memory_store


def reset_memory_store() -> None:
    """重置记忆存储器"""
    global _global_memory_store
    _global_memory_store = None
