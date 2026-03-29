"""
Utils Concurrency Module Tests

测试并发控制：读写锁、键级锁、死锁检测和 MVCC 存储
"""

import asyncio
import pytest
from datetime import datetime

from intentos.utils.concurrency import (
    ReadWriteLock,
    KeyLockManager,
    LockInfo,
    DeadlockDetector,
    MVCCStore,
)


class TestReadWriteLock:
    """测试读写锁"""

    @pytest.mark.asyncio
    async def test_single_reader(self):
        """单个读者获取锁"""
        lock = ReadWriteLock()
        
        await lock.acquire_read()
        assert lock.reader_count == 1
        await lock.release_read()
        assert lock.reader_count == 0

    @pytest.mark.asyncio
    async def test_multiple_readers(self):
        """多个读者可同时持有锁"""
        lock = ReadWriteLock()
        
        await lock.acquire_read()
        await lock.acquire_read()
        await lock.acquire_read()
        
        assert lock.reader_count == 3
        
        await lock.release_read()
        await lock.release_read()
        await lock.release_read()
        
        assert lock.reader_count == 0

    @pytest.mark.asyncio
    async def test_single_writer(self):
        """单个写者获取锁"""
        lock = ReadWriteLock()
        
        await lock.acquire_write()
        # 写锁获取后应能释放
        await lock.release_write()

    @pytest.mark.asyncio
    async def test_writer_waiting(self):
        """写者等待计数"""
        lock = ReadWriteLock()
        
        # 初始无写者等待
        assert lock.has_writers_waiting is False
        
        # 模拟写者等待（不实际获取锁）
        lock._writers_waiting += 1
        assert lock.has_writers_waiting is True
        
        lock._writers_waiting -= 1
        assert lock.has_writers_waiting is False

    @pytest.mark.asyncio
    async def test_read_write_properties(self):
        """读写锁属性"""
        lock = ReadWriteLock()
        
        assert lock.reader_count == 0
        assert lock.has_writers_waiting is False


class TestKeyLockManager:
    """测试键级锁管理器"""

    @pytest.mark.asyncio
    async def test_create_read_lock(self):
        """创建读锁"""
        manager = KeyLockManager()
        
        async with manager.read_lock("key1"):
            # 锁应被创建
            assert "key1" in manager._locks

    @pytest.mark.asyncio
    async def test_create_write_lock(self):
        """创建写锁"""
        manager = KeyLockManager()
        
        async with manager.write_lock("key1"):
            # 锁应被创建
            assert "key1" in manager._locks

    @pytest.mark.asyncio
    async def test_lock_cleanup(self):
        """锁清理"""
        manager = KeyLockManager()
        
        async with manager.read_lock("key1"):
            pass
        
        # 使用后锁应被清理
        assert "key1" not in manager._locks
        assert "key1" not in manager._lock_counts

    @pytest.mark.asyncio
    async def test_max_locks_limit(self):
        """最大锁数量限制"""
        manager = KeyLockManager(max_locks=2)
        
        # 创建超过限制的锁
        async with manager.read_lock("key1"):
            async with manager.read_lock("key2"):
                # 触发清理后再创建第三个锁
                await manager._cleanup_unused_locks()
                async with manager.read_lock("key3"):
                    # 锁应被创建
                    assert "key3" in manager._locks

    @pytest.mark.asyncio
    async def test_multiple_keys(self):
        """多个键的锁"""
        manager = KeyLockManager()
        
        async with manager.read_lock("key1"):
            async with manager.write_lock("key2"):
                assert "key1" in manager._locks
                assert "key2" in manager._locks
        
        # 所有锁应被清理
        assert len(manager._locks) == 0


class TestLockInfo:
    """测试锁信息"""

    def test_create_lock_info(self):
        """创建锁信息"""
        info = LockInfo(
            key="key1",
            lock_type="read",
            holder_id="tx1"
        )
        
        assert info.key == "key1"
        assert info.lock_type == "read"
        assert info.holder_id == "tx1"
        assert isinstance(info.acquired_at, datetime)
        assert info.waiting_since is None

    def test_lock_info_with_waiting(self):
        """带等待时间的锁信息"""
        waiting_time = datetime(2024, 1, 1, 12, 0, 0)
        info = LockInfo(
            key="key1",
            lock_type="write",
            holder_id="tx2",
            waiting_since=waiting_time
        )
        
        assert info.waiting_since == waiting_time

    def test_lock_info_to_dict(self):
        """锁信息转换为字典"""
        info = LockInfo(
            key="key1",
            lock_type="read",
            holder_id="tx1"
        )
        
        data = info.to_dict()
        
        assert isinstance(data, dict)
        assert data["key"] == "key1"
        assert data["lock_type"] == "read"
        assert data["holder_id"] == "tx1"
        assert "acquired_at" in data


class TestDeadlockDetector:
    """测试死锁检测器"""

    def test_add_wait(self):
        """添加等待关系"""
        detector = DeadlockDetector()
        
        detector.add_wait("tx1", "lock1", "tx2")
        
        assert "tx1" in detector._wait_for_graph
        assert "tx2" in detector._wait_for_graph["tx1"]

    def test_remove_wait(self):
        """移除等待关系"""
        detector = DeadlockDetector()
        
        detector.add_wait("tx1", "lock1", "tx2")
        detector.remove_wait("tx1")
        
        assert "tx1" not in detector._wait_for_graph

    def test_set_lock_holder(self):
        """设置锁持有者"""
        detector = DeadlockDetector()
        
        detector.set_lock_holder("lock1", "tx1")
        
        assert detector._lock_holders["lock1"] == "tx1"

    def test_release_lock(self):
        """释放锁"""
        detector = DeadlockDetector()
        
        detector.set_lock_holder("lock1", "tx1")
        detector.release_lock("lock1")
        
        assert "lock1" not in detector._lock_holders

    def test_no_deadlock(self):
        """无死锁情况"""
        detector = DeadlockDetector()
        
        detector.add_wait("tx1", "lock1", "tx2")
        detector.add_wait("tx2", "lock2", "tx3")
        
        result = detector.detect_deadlock()
        
        assert result is None

    def test_simple_deadlock(self):
        """简单死锁"""
        detector = DeadlockDetector()
        
        # tx1 -> tx2 -> tx1 (循环)
        detector.add_wait("tx1", "lock1", "tx2")
        detector.add_wait("tx2", "lock2", "tx1")
        
        result = detector.detect_deadlock()
        
        assert result is not None
        assert len(result) > 0

    def test_complex_deadlock(self):
        """复杂死锁"""
        detector = DeadlockDetector()
        
        # tx1 -> tx2 -> tx3 -> tx1 (循环)
        detector.add_wait("tx1", "lock1", "tx2")
        detector.add_wait("tx2", "lock2", "tx3")
        detector.add_wait("tx3", "lock3", "tx1")
        
        result = detector.detect_deadlock()
        
        assert result is not None
        assert len(result) >= 3

    def test_get_wait_graph_stats(self):
        """获取等待图统计"""
        detector = DeadlockDetector()
        
        detector.add_wait("tx1", "lock1", "tx2")
        detector.add_wait("tx2", "lock2", "tx3")
        detector.set_lock_holder("lock1", "tx2")
        detector.set_lock_holder("lock2", "tx3")
        
        stats = detector.get_wait_graph_stats()
        
        assert "waiting_transactions" in stats
        assert "total_waits" in stats
        assert "active_locks" in stats
        assert stats["waiting_transactions"] == 2
        assert stats["total_waits"] == 2
        assert stats["active_locks"] == 2


class TestMVCCStore:
    """测试 MVCC 存储"""

    def test_get_nonexistent_key(self):
        """获取不存在的键"""
        store = MVCCStore()
        
        result = store.get("nonexistent")
        
        assert result is None

    def test_set_and_get(self):
        """设置和获取"""
        store = MVCCStore()
        
        store.set("key1", "value1", "tx1")
        result = store.get("key1", "tx1")
        
        assert result == "value1"

    def test_multiple_versions(self):
        """多版本控制"""
        store = MVCCStore()
        
        store.set("key1", "v1", "tx1")
        store.set("key1", "v2", "tx2")
        store.set("key1", "v3", "tx3")
        
        # 获取最新版本
        result = store.get("key1")
        assert result == "v3"

    def test_delete(self):
        """删除数据"""
        store = MVCCStore()
        
        store.set("key1", "value1", "tx1")
        store.delete("key1", "tx2")
        
        result = store.get("key1")
        assert result is None

    def test_commit(self):
        """提交事务"""
        store = MVCCStore()
        
        store.set("key1", "value1", "tx1")
        store.commit("tx1")
        
        # 提交后读集合应被清除
        assert "tx1" not in store._read_sets

    def test_rollback(self):
        """回滚事务"""
        store = MVCCStore()
        
        store.set("key1", "value1", "tx1")
        store.set("key2", "value2", "tx1")
        store.rollback("tx1")
        
        # 回滚后数据应被清除
        result1 = store.get("key1")
        result2 = store.get("key2")
        assert result1 is None
        assert result2 is None

    def test_max_versions(self):
        """最大版本数限制"""
        store = MVCCStore(max_versions=3)
        
        # 创建超过限制的版本
        for i in range(5):
            store.set("key1", f"v{i}", f"tx{i}")
        
        history = store.get_version_history("key1")
        
        # 版本数不应超过限制
        assert len(history) <= 3

    def test_get_version_history(self):
        """获取版本历史"""
        store = MVCCStore()
        
        store.set("key1", "v1", "tx1")
        store.set("key1", "v2", "tx2")
        
        history = store.get_version_history("key1")
        
        assert len(history) == 2
        assert history[0]["value"] == "v2"  # 最新版本在前
        assert history[1]["value"] == "v1"

    def test_read_set_isolation(self):
        """读集合隔离"""
        store = MVCCStore()
        
        store.set("key1", "v1", "tx1")
        store.set("key1", "v2", "tx2")
        
        # tx1 读取后应保持一致性
        result1 = store.get("key1", "tx1")
        result2 = store.get("key1", "tx1")
        
        assert result1 == result2

    def test_concurrent_transactions(self):
        """并发事务"""
        store = MVCCStore()
        
        # 多个事务同时写入
        store.set("key1", "v1", "tx1")
        store.set("key2", "v2", "tx2")
        store.set("key3", "v3", "tx3")
        
        assert store.get("key1") == "v1"
        assert store.get("key2") == "v2"
        assert store.get("key3") == "v3"
