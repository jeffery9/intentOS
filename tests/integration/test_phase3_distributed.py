"""
Phase 3 分布式增强测试

测试一致性协议、检查点恢复、并发控制
"""

import asyncio

import pytest

from intentos.distributed.checkpoint import (
    CheckpointConfig,
    CheckpointManager,
    CheckpointMetadata,
    CheckpointType,
    ProcessCheckpoint,
)
from intentos.distributed.consensus import (
    ConsistencyLevel,
    QuorumReplicator,
    ReadRequest,
    VersionedValue,
    VersionVector,
    WriteRequest,
)
from intentos.utils.concurrency import (
    DeadlockDetector,
    KeyLockManager,
    MVCCStore,
    ReadWriteLock,
)

# =============================================================================
# 一致性协议测试
# =============================================================================


class TestVersionVector:
    """版本向量测试"""

    def test_increment(self):
        """测试版本递增"""
        vv = VersionVector()

        vv.increment("node1")
        assert vv.versions["node1"] == 1

        vv.increment("node1")
        assert vv.versions["node1"] == 2

    def test_merge(self):
        """测试合并"""
        vv1 = VersionVector({"node1": 1, "node2": 2})
        vv2 = VersionVector({"node1": 3, "node3": 1})

        vv1.merge(vv2)

        assert vv1.versions["node1"] == 3  # 取最大值
        assert vv1.versions["node2"] == 2
        assert vv1.versions["node3"] == 1

    def test_dominates(self):
        """测试支配关系"""
        vv1 = VersionVector({"node1": 2, "node2": 2})
        vv2 = VersionVector({"node1": 1, "node2": 1})

        assert vv1.dominates(vv2) is True
        assert vv2.dominates(vv1) is False

    def test_concurrent_with(self):
        """测试并发检测"""
        vv1 = VersionVector({"node1": 2, "node2": 1})
        vv2 = VersionVector({"node1": 1, "node2": 2})

        assert vv1.concurrent_with(vv2) is True

    def test_to_dict(self):
        """测试序列化"""
        vv = VersionVector({"node1": 1, "node2": 2})

        data = vv.to_dict()

        assert data["versions"]["node1"] == 1
        assert data["versions"]["node2"] == 2

    def test_from_dict(self):
        """测试反序列化"""
        data = {"versions": {"node1": 3, "node2": 4}}

        vv = VersionVector.from_dict(data)

        assert vv.versions["node1"] == 3
        assert vv.versions["node2"] == 4


class TestVersionedValue:
    """带版本的值测试"""

    def test_create_versioned_value(self):
        """测试创建带版本的值"""
        version = VersionVector()
        version.increment("node1")

        vv = VersionedValue(value={"data": "test"}, version=version)

        assert vv.value["data"] == "test"
        assert vv.version.versions["node1"] == 1

    def test_compute_checksum(self):
        """测试计算校验和"""
        vv = VersionedValue(value="test", version=VersionVector())

        checksum1 = vv.compute_checksum()
        vv.checksum = checksum1

        assert vv.verify_integrity() is True

    def test_verify_integrity(self):
        """测试验证完整性"""
        vv = VersionedValue(value="test", version=VersionVector())
        vv.checksum = vv.compute_checksum()

        assert vv.verify_integrity() is True

        # 篡改数据
        vv.value = "tampered"
        assert vv.verify_integrity() is False


class TestWriteRequest:
    """写请求测试"""

    def test_quorum_size_strong(self):
        """测试强一致法定人数"""
        req = WriteRequest(consistency=ConsistencyLevel.STRONG)

        assert req.quorum_size(3) == 3
        assert req.quorum_size(5) == 5

    def test_quorum_size_quorum(self):
        """测试法定人数一致"""
        req = WriteRequest(consistency=ConsistencyLevel.QUORUM)

        assert req.quorum_size(3) == 2  # 3/2 + 1 = 2
        assert req.quorum_size(5) == 3  # 5/2 + 1 = 3

    def test_quorum_size_eventual(self):
        """测试最终一致"""
        req = WriteRequest(consistency=ConsistencyLevel.EVENTUAL)

        assert req.quorum_size(3) == 1
        assert req.quorum_size(5) == 1

    def test_has_quorum(self):
        """测试是否达到法定人数"""
        req = WriteRequest(consistency=ConsistencyLevel.QUORUM)
        req.acks["node1"] = True
        req.acks["node2"] = True
        req.acks["node3"] = False

        assert req.has_quorum(3) is True  # 2 >= 2

        req.acks["node2"] = False
        assert req.has_quorum(3) is False  # 1 < 2


class TestReadRequest:
    """读请求测试"""

    def test_get_latest_value_single(self):
        """测试获取单个值"""
        req = ReadRequest()

        version = VersionVector()
        version.increment("node1")

        req.responses.append(VersionedValue(value="test", version=version))

        assert req.get_latest_value() == "test"

    def test_get_latest_value_dominates(self):
        """测试获取支配值"""
        req = ReadRequest()

        vv1 = VersionedValue(value="old", version=VersionVector({"node1": 1}))
        vv2 = VersionedValue(value="new", version=VersionVector({"node1": 2}))

        req.responses.append(vv1)
        req.responses.append(vv2)

        assert req.get_latest_value() == "new"

    def test_get_latest_value_concurrent(self):
        """测试获取并发值（基于时间戳）"""
        import time

        req = ReadRequest()

        vv1 = VersionedValue(
            value="old", version=VersionVector({"node1": 1, "node2": 2}), timestamp=time.time() - 1
        )
        vv2 = VersionedValue(
            value="new", version=VersionVector({"node1": 2, "node2": 1}), timestamp=time.time()
        )

        req.responses.append(vv1)
        req.responses.append(vv2)

        assert req.get_latest_value() == "new"


class TestQuorumReplicator:
    """Quorum 复制器测试"""

    @pytest.mark.asyncio
    async def test_write_read_local(self):
        """测试本地读写"""
        replicator = QuorumReplicator(nodes=[], consistency=ConsistencyLevel.EVENTUAL)

        # 写
        success = await replicator.write("TEST", "key1", "value1")
        assert success is True

        # 读
        value = await replicator.read("TEST", "key1")
        assert value == "value1"

    def test_get_storage_stats(self):
        """测试获取存储统计"""
        replicator = QuorumReplicator(nodes=[])

        stats = replicator.get_storage_stats()

        assert stats["total_keys"] == 0
        assert stats["nodes_count"] == 0
        assert stats["consistency"] == "quorum"


# =============================================================================
# 检查点恢复测试
# =============================================================================


class TestCheckpointMetadata:
    """检查点元数据测试"""

    def test_to_dict(self):
        """测试序列化"""
        metadata = CheckpointMetadata(
            type=CheckpointType.FULL, process_id="proc-123", program_name="test_program"
        )

        data = metadata.to_dict()

        assert data["type"] == "full"
        assert data["process_id"] == "proc-123"
        assert data["program_name"] == "test_program"

    def test_from_dict(self):
        """测试反序列化"""
        data = {
            "id": "cp-123",
            "type": "incremental",
            "timestamp": "2026-03-14T10:00:00",
            "process_id": "proc-456",
            "program_name": "my_program",
        }

        metadata = CheckpointMetadata.from_dict(data)

        assert metadata.id == "cp-123"
        assert metadata.type == CheckpointType.INCREMENTAL
        assert metadata.process_id == "proc-456"


class TestProcessCheckpoint:
    """进程检查点测试"""

    def test_to_dict(self):
        """测试序列化"""
        metadata = CheckpointMetadata()
        checkpoint = ProcessCheckpoint(
            metadata=metadata,
            pid="proc-123",
            pc=100,
            status="running",
            program_data={"name": "test"},
            variables={"x": 10},
            context={},
        )

        data = checkpoint.to_dict()

        assert data["pid"] == "proc-123"
        assert data["pc"] == 100
        assert data["variables"]["x"] == 10

    def test_compute_and_verify_checksum(self):
        """测试计算和验证校验和"""
        metadata = CheckpointMetadata()
        checkpoint = ProcessCheckpoint(
            metadata=metadata,
            pid="proc-123",
            pc=0,
            status="running",
            program_data={},
            variables={},
            context={},
        )

        # 计算并设置校验和
        checksum = checkpoint.compute_checksum()
        checkpoint.metadata.checksum = checksum

        assert checkpoint.verify_integrity() is True


class TestCheckpointConfig:
    """检查点配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = CheckpointConfig.default()

        assert config.checkpoint_interval_seconds == 60
        assert config.max_checkpoints_per_process == 10

    def test_frequent_config(self):
        """测试频繁检查点配置"""
        config = CheckpointConfig.frequent()

        assert config.checkpoint_interval_seconds == 10
        assert config.max_checkpoints_per_process == 100

    def test_minimal_config(self):
        """测试最小检查点配置"""
        config = CheckpointConfig.minimal()

        assert config.checkpoint_interval_seconds == 300
        assert config.max_checkpoints_per_process == 3


class TestCheckpointManager:
    """检查点管理器测试"""

    def test_create_checkpoint(self, tmp_path):
        """测试创建检查点"""
        config = CheckpointConfig(storage_path=str(tmp_path / "checkpoints"), compress=True)
        manager = CheckpointManager(config)

        checkpoint = manager.create_checkpoint(
            pid="proc-123",
            pc=100,
            status="running",
            program_data={"name": "test"},
            variables={"x": 10},
            context={},
            program_name="test_program",
        )

        assert checkpoint.pid == "proc-123"
        assert checkpoint.pc == 100
        assert checkpoint.metadata.type == CheckpointType.FULL

    def test_restore_checkpoint(self, tmp_path):
        """测试恢复检查点"""
        config = CheckpointConfig(storage_path=str(tmp_path / "checkpoints"), compress=False)
        manager = CheckpointManager(config)

        # 创建检查点
        checkpoint = manager.create_checkpoint(
            pid="proc-456",
            pc=50,
            status="running",
            program_data={"name": "restore_test"},
            variables={"y": 20},
            context={},
        )

        # 恢复检查点
        restored = manager.restore_checkpoint(checkpoint.metadata.id)

        assert restored is not None
        assert restored.pid == "proc-456"
        assert restored.pc == 50

    def test_list_checkpoints(self, tmp_path):
        """测试列出检查点"""
        config = CheckpointConfig(storage_path=str(tmp_path / "checkpoints"))
        manager = CheckpointManager(config)

        # 创建多个检查点
        for i in range(3):
            manager.create_checkpoint(
                pid=f"proc-{i}",
                pc=i * 10,
                status="running",
                program_data={},
                variables={},
                context={},
            )

        checkpoints = manager.list_checkpoints()

        assert len(checkpoints) == 3


# =============================================================================
# 并发控制测试
# =============================================================================


class TestReadWriteLock:
    """读写锁测试"""

    @pytest.mark.asyncio
    async def test_multiple_readers(self):
        """测试多读并发"""
        lock = ReadWriteLock()

        results = []

        async def reader(id: int):
            await lock.acquire_read()
            try:
                results.append(f"reader_{id}_start")
                await asyncio.sleep(0.1)
                results.append(f"reader_{id}_end")
            finally:
                await lock.release_read()

        # 启动 3 个读者
        await asyncio.gather(
            reader(1),
            reader(2),
            reader(3),
        )

        # 所有读者应该并发执行
        assert len([r for r in results if "start" in r]) == 3

    @pytest.mark.asyncio
    async def test_write_exclusive(self):
        """测试写独占"""
        lock = ReadWriteLock()
        results = []

        async def reader():
            await lock.acquire_read()
            try:
                results.append("reading")
                await asyncio.sleep(0.2)
            finally:
                await lock.release_read()

        async def writer():
            await lock.acquire_write()
            try:
                results.append("writing")
                await asyncio.sleep(0.1)
            finally:
                await lock.release_write()

        # 读者先开始
        reader_task = asyncio.create_task(reader())
        await asyncio.sleep(0.05)

        # 写者需要等待
        await writer()

        # 读者结束后写者才能执行
        assert results == ["reading", "writing"]


class TestKeyLockManager:
    """键级锁管理器测试"""

    @pytest.mark.asyncio
    async def test_read_lock(self):
        """测试读锁"""
        manager = KeyLockManager()

        async with manager.read_lock("key1"):
            # 持有读锁
            assert "key1" in manager._locks

    @pytest.mark.asyncio
    async def test_write_lock(self):
        """测试写锁"""
        manager = KeyLockManager()

        async with manager.write_lock("key1"):
            # 持有写锁
            assert "key1" in manager._locks

    @pytest.mark.asyncio
    async def test_lock_cleanup(self):
        """测试锁清理"""
        manager = KeyLockManager(max_locks=10)

        # 创建多个锁
        for i in range(15):
            async with manager.write_lock(f"key{i}"):
                pass

        # 应该清理未使用的锁
        assert len(manager._locks) <= 10


class TestDeadlockDetector:
    """死锁检测器测试"""

    def test_detect_simple_deadlock(self):
        """测试简单死锁检测"""
        detector = DeadlockDetector()

        # A 持有锁 1，B 等待锁 1
        detector.set_lock_holder("lock1", "A")
        detector.add_wait("B", "lock1", "A")

        # B 持有锁 2，A 等待锁 2
        detector.set_lock_holder("lock2", "B")
        detector.add_wait("A", "lock2", "B")

        # 检测死锁
        cycle = detector.detect_deadlock()

        assert cycle is not None

    def test_no_deadlock(self):
        """测试无死锁"""
        detector = DeadlockDetector()

        # A 持有锁 1，B 等待锁 1
        detector.set_lock_holder("lock1", "A")
        detector.add_wait("B", "lock1", "A")

        # C 持有锁 2，无等待
        detector.set_lock_holder("lock2", "C")

        # 检测死锁
        cycle = detector.detect_deadlock()

        assert cycle is None

    def test_get_wait_graph_stats(self):
        """测试获取等待图统计"""
        detector = DeadlockDetector()

        detector.set_lock_holder("lock1", "A")
        detector.add_wait("B", "lock1", "A")

        stats = detector.get_wait_graph_stats()

        assert stats["waiting_transactions"] == 1
        assert stats["active_locks"] == 1


class TestMVCCStore:
    """MVCC 存储测试"""

    def test_basic_set_get(self):
        """测试基本读写"""
        store = MVCCStore()

        store.set("key1", "value1", "tx1")
        value = store.get("key1", "tx1")

        assert value == "value1"

    def test_snapshot_read(self):
        """测试快照读"""
        store = MVCCStore()

        # 初始值
        store.set("x", 1, "tx1")
        store.commit("tx1")

        # 事务 2 开始读
        val1 = store.get("x", "tx2")
        assert val1 == 1

        # 事务 3 修改
        store.set("x", 2, "tx3")
        store.commit("tx3")

        # 事务 2 再次读，应该还是 1（可重复读）
        val2 = store.get("x", "tx2")
        assert val2 == 1

    def test_version_history(self):
        """测试版本历史"""
        store = MVCCStore(max_versions=5)

        # 多次写入
        for i in range(10):
            store.set("x", i, f"tx{i}")
            store.commit(f"tx{i}")

        history = store.get_version_history("x")

        # 只保留最近 5 个版本
        assert len(history) == 5
        assert history[0]["value"] == 9  # 最新值

    def test_delete(self):
        """测试删除"""
        store = MVCCStore()

        store.set("x", 100, "tx1")
        store.delete("x", "tx2")

        value = store.get("x", "tx2")
        assert value is None

    def test_rollback(self):
        """测试回滚"""
        store = MVCCStore()

        store.set("x", 100, "tx1")
        store.set("x", 200, "tx2")

        store.rollback("tx2")

        # tx2 的写入应该被回滚
        value = store.get("x")
        assert value == 100


# =============================================================================
# 集成测试
# =============================================================================


class TestPhase3Integration:
    """Phase 3 集成测试"""

    @pytest.mark.asyncio
    async def test_quorum_with_versioning(self):
        """测试 Quorum + 版本控制集成"""
        replicator = QuorumReplicator(nodes=[], consistency=ConsistencyLevel.QUORUM)

        # 写
        success = await replicator.write("TEST", "counter", 0)
        assert success is True

        # 读
        value = await replicator.read("TEST", "counter")
        assert value == 0

    @pytest.mark.asyncio
    async def test_checkpoint_with_mvcc(self, tmp_path):
        """测试检查点 + MVCC 集成"""
        # 创建 MVCC store
        store = MVCCStore()

        # 写入数据
        store.set("x", 100, "tx1")
        store.commit("tx1")

        # 创建检查点
        config = CheckpointConfig(storage_path=str(tmp_path / "checkpoints"))
        manager = CheckpointManager(config)

        checkpoint = manager.create_checkpoint(
            pid="mvcc-proc",
            pc=0,
            status="running",
            program_data={},
            variables={"mvcc_value": store.get("x")},
            context={},
        )

        assert checkpoint.variables["mvcc_value"] == 100

    @pytest.mark.asyncio
    async def test_concurrent_access_with_locks(self):
        """测试并发访问 + 锁集成"""
        manager = KeyLockManager()
        shared_data = {"counter": 0}

        async def increment():
            async with manager.write_lock("counter"):
                current = shared_data["counter"]
                await asyncio.sleep(0.01)
                shared_data["counter"] = current + 1

        # 并发执行 10 次递增
        await asyncio.gather(*[increment() for _ in range(10)])

        # 结果应该是 10
        assert shared_data["counter"] == 10
