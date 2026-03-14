"""
并发控制

提供读写锁和死锁检测

设计文档：docs/private/009-concurrency-control.md
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class ReadWriteLock:
    """读写锁"""
    
    def __init__(self):
        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._readers = 0
        self._writers_waiting = 0
    
    async def acquire_read(self) -> None:
        """获取读锁"""
        self._writers_waiting += 1
        try:
            async with self._read_lock:
                self._readers += 1
        finally:
            self._writers_waiting -= 1
    
    async def release_read(self) -> None:
        """释放读锁"""
        async with self._read_lock:
            self._readers -= 1
    
    async def acquire_write(self) -> None:
        """获取写锁"""
        self._writers_waiting += 1
        try:
            await self._write_lock.acquire()
        finally:
            self._writers_waiting -= 1
    
    async def release_write(self) -> None:
        """释放写锁"""
        self._write_lock.release()
    
    @property
    def reader_count(self) -> int:
        return self._readers
    
    @property
    def has_writers_waiting(self) -> bool:
        return self._writers_waiting > 0


class KeyLockManager:
    """键级锁管理器"""
    
    def __init__(self, max_locks: int = 10000):
        self._locks: dict[str, ReadWriteLock] = {}
        self._lock_counts: dict[str, int] = defaultdict(int)
        self._global_lock = asyncio.Lock()
        self.max_locks = max_locks
    
    async def _get_or_create_lock(self, key: str) -> ReadWriteLock:
        """获取或创建键的锁"""
        async with self._global_lock:
            if key not in self._locks:
                if len(self._locks) >= self.max_locks:
                    await self._cleanup_unused_locks()
                self._locks[key] = ReadWriteLock()
            
            self._lock_counts[key] += 1
            return self._locks[key]
    
    async def _release_lock(self, key: str) -> None:
        """释放键的锁引用"""
        async with self._global_lock:
            self._lock_counts[key] -= 1
            
            if self._lock_counts[key] <= 0:
                self._locks.pop(key, None)
                self._lock_counts.pop(key, None)
    
    async def _cleanup_unused_locks(self) -> None:
        """清理未使用的锁"""
        unused_keys = [
            key for key, count in self._lock_counts.items()
            if count <= 0
        ]
        for key in unused_keys:
            self._locks.pop(key, None)
            self._lock_counts.pop(key, None)
    
    @asynccontextmanager
    async def read_lock(self, key: str):
        """读锁上下文管理器"""
        lock = await self._get_or_create_lock(key)
        try:
            await lock.acquire_read()
            yield
        finally:
            await lock.release_read()
            await self._release_lock(key)
    
    @asynccontextmanager
    async def write_lock(self, key: str):
        """写锁上下文管理器"""
        lock = await self._get_or_create_lock(key)
        try:
            await lock.acquire_write()
            yield
        finally:
            await lock.release_write()
            await self._release_lock(key)


@dataclass
class LockInfo:
    """锁信息"""
    
    key: str
    lock_type: str
    holder_id: str
    acquired_at: datetime = field(default_factory=datetime.now)
    waiting_since: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "lock_type": self.lock_type,
            "holder_id": self.holder_id,
            "acquired_at": self.acquired_at.isoformat(),
            "waiting_since": self.waiting_since.isoformat() if self.waiting_since else None,
        }


class DeadlockDetector:
    """死锁检测器"""
    
    def __init__(self):
        self._wait_for_graph: dict[str, set[str]] = defaultdict(set)
        self._lock_holders: dict[str, str] = {}
    
    def add_wait(self, waiter: str, lock: str, holder: str) -> None:
        """添加等待关系"""
        self._wait_for_graph[waiter].add(holder)
    
    def remove_wait(self, waiter: str) -> None:
        """移除等待关系"""
        self._wait_for_graph.pop(waiter, None)
        for waiters in self._wait_for_graph.values():
            waiters.discard(waiter)
    
    def set_lock_holder(self, lock: str, holder: str) -> None:
        """设置锁持有者"""
        self._lock_holders[lock] = holder
    
    def release_lock(self, lock: str) -> None:
        """释放锁"""
        self._lock_holders.pop(lock, None)
    
    def detect_deadlock(self) -> Optional[list[str]]:
        """检测死锁"""
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> Optional[list[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self._wait_for_graph.get(node, set()):
                if neighbor not in visited:
                    result = dfs(neighbor)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        for node in list(self._wait_for_graph.keys()):
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle
        
        return None
    
    def get_wait_graph_stats(self) -> dict:
        """获取等待图统计"""
        return {
            "waiting_transactions": len(self._wait_for_graph),
            "total_waits": sum(len(waits) for waits in self._wait_for_graph.values()),
            "active_locks": len(self._lock_holders),
        }


class MVCCStore:
    """MVCC 存储"""
    
    def __init__(self, max_versions: int = 10):
        self._versions: dict[str, list] = {}
        self.max_versions = max_versions
        self._read_sets: dict[str, dict[str, int]] = {}
    
    def get(
        self,
        key: str,
        transaction_id: Optional[str] = None,
    ) -> Optional[Any]:
        """读取数据"""
        if key not in self._versions:
            return None
        
        versions = self._versions[key]
        if not versions:
            return None
        
        if transaction_id and transaction_id in self._read_sets:
            read_version = self._read_sets[transaction_id].get(key)
            if read_version is not None:
                for entry in versions:
                    if entry["version"] == read_version:
                        return entry["value"] if not entry["deleted"] else None
        
        latest = versions[0]
        
        if transaction_id:
            if transaction_id not in self._read_sets:
                self._read_sets[transaction_id] = {}
            self._read_sets[transaction_id][key] = latest["version"]
        
        return latest["value"] if not latest["deleted"] else None
    
    def set(
        self,
        key: str,
        value: Any,
        transaction_id: str,
    ) -> None:
        """写入数据"""
        current_version = 0
        if key in self._versions:
            current_version = self._versions[key][0]["version"]
        
        new_entry = {
            "value": value,
            "version": current_version + 1,
            "timestamp": datetime.now().isoformat(),
            "transaction_id": transaction_id,
            "deleted": False,
        }
        
        if key not in self._versions:
            self._versions[key] = []
        
        self._versions[key].insert(0, new_entry)
        
        if len(self._versions[key]) > self.max_versions:
            self._versions[key] = self._versions[key][:self.max_versions]
    
    def delete(
        self,
        key: str,
        transaction_id: str,
    ) -> None:
        """删除数据"""
        current_version = 0
        if key in self._versions:
            current_version = self._versions[key][0]["version"]
        
        delete_entry = {
            "value": None,
            "version": current_version + 1,
            "timestamp": datetime.now().isoformat(),
            "transaction_id": transaction_id,
            "deleted": True,
        }
        
        if key not in self._versions:
            self._versions[key] = []
        
        self._versions[key].insert(0, delete_entry)
    
    def commit(self, transaction_id: str) -> None:
        """提交事务"""
        self._read_sets.pop(transaction_id, None)
    
    def rollback(self, transaction_id: str) -> None:
        """回滚事务"""
        self._read_sets.pop(transaction_id, None)
        
        for key in list(self._versions.keys()):
            self._versions[key] = [
                entry for entry in self._versions[key]
                if entry["transaction_id"] != transaction_id
            ]
            
            if not self._versions[key]:
                del self._versions[key]
    
    def get_version_history(self, key: str) -> list[dict]:
        """获取版本历史"""
        if key not in self._versions:
            return []
        
        return self._versions[key].copy()
