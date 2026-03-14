# -*- coding: utf-8 -*-
import pytest
import os
import shutil
import json
import gzip
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from pathlib import Path
import hashlib

from intentos.distributed.checkpoint import (
    CheckpointType, CheckpointMetadata, ProcessCheckpoint, CheckpointConfig, CheckpointManager
)

# =============================================================================
# Enum Tests
# =============================================================================

class TestCheckpointType:
    """CheckpointType 测试"""

    def test_enum_values(self):
        assert CheckpointType.FULL.value == "full"
        assert CheckpointType.INCREMENTAL.value == "incremental"
        assert CheckpointType.SNAPSHOT.value == "snapshot"

# =============================================================================
# CheckpointMetadata Tests
# =============================================================================

class TestCheckpointMetadata:
    """CheckpointMetadata 测试"""

    def test_default_creation(self):
        metadata = CheckpointMetadata()
        assert metadata.type == CheckpointType.FULL
        assert isinstance(metadata.timestamp, datetime)
        assert len(metadata.id) == 8

    def test_custom_creation(self):
        timestamp = datetime(2023, 1, 1)
        metadata = CheckpointMetadata(
            id="test_id",
            type=CheckpointType.SNAPSHOT,
            timestamp=timestamp,
            process_id="pid123",
            program_name="prog_a",
            node_id="node_x",
            size_bytes=100,
            compressed=True,
            checksum="abc"
        )
        assert metadata.id == "test_id"
        assert metadata.type == CheckpointType.SNAPSHOT
        assert metadata.timestamp == timestamp
        assert metadata.process_id == "pid123"
        assert metadata.program_name == "prog_a"
        assert metadata.node_id == "node_x"
        assert metadata.size_bytes == 100
        assert metadata.compressed is True
        assert metadata.checksum == "abc"

    def test_to_dict(self):
        metadata = CheckpointMetadata(id="test", process_id="p1", program_name="pr1")
        d = metadata.to_dict()
        assert d["id"] == "test"
        assert d["process_id"] == "p1"
        assert d["program_name"] == "pr1"
        assert d["type"] == "full"

    def test_from_dict(self):
        data = {
            "id": "dict_id",
            "type": "incremental",
            "timestamp": datetime.now().isoformat(),
            "process_id": "p_dict",
            "program_name": "pr_dict",
            "node_id": "n_dict",
            "size_bytes": 200,
            "compressed": False,
            "checksum": "def"
        }
        metadata = CheckpointMetadata.from_dict(data)
        assert metadata.id == "dict_id"
        assert metadata.type == CheckpointType.INCREMENTAL
        assert metadata.process_id == "p_dict"

# =============================================================================
# ProcessCheckpoint Tests
# =============================================================================

class TestProcessCheckpoint:
    """ProcessCheckpoint 测试"""

    @pytest.fixture
    def sample_metadata(self):
        return CheckpointMetadata(id="meta1", process_id="p1")

    def test_creation(self, sample_metadata):
        checkpoint = ProcessCheckpoint(
            metadata=sample_metadata,
            pid="p1", pc=10, status="running",
            program_data={"code": "abc"},
            variables={"x": 1},
            context={"user": "test"}
        )
        assert checkpoint.pid == "p1"
        assert checkpoint.metadata == sample_metadata

    def test_to_dict(self, sample_metadata):
        checkpoint = ProcessCheckpoint(
            metadata=sample_metadata,
            pid="p1", pc=10, status="running",
            program_data={"code": "abc"},
            variables={"x": 1},
            context={"user": "test"}
        )
        d = checkpoint.to_dict()
        assert d["pid"] == "p1"
        assert d["metadata"]["id"] == "meta1"
        assert d["program_data"] == {"code": "abc"}

    def test_from_dict(self, sample_metadata):
        data = {
            "metadata": sample_metadata.to_dict(),
            "pid": "p_dict",
            "pc": 20,
            "status": "paused",
            "program_data": {"code": "def"},
            "variables": {"y": 2},
            "context": {"env": "prod"},
            "gas_state": {"limit": 100}
        }
        checkpoint = ProcessCheckpoint.from_dict(data)
        assert checkpoint.pid == "p_dict"
        assert checkpoint.pc == 20
        assert checkpoint.gas_state == {"limit": 100}

    def test_compute_checksum(self, sample_metadata):
        checkpoint = ProcessCheckpoint(
            metadata=sample_metadata,
            pid="p1", pc=10, status="running",
            program_data={"code": "abc"},
            variables={"x": 1},
            context={"user": "test"}
        )
        checksum = checkpoint.compute_checksum()
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 output length

    def test_verify_integrity_success(self, sample_metadata):
        checkpoint = ProcessCheckpoint(
            metadata=sample_metadata,
            pid="p1", pc=10, status="running",
            program_data={"code": "abc"},
            variables={"x": 1},
            context={"user": "test"}
        )
        checkpoint.metadata.checksum = checkpoint.compute_checksum()
        assert checkpoint.verify_integrity() is True

    def test_verify_integrity_failure(self, sample_metadata):
        checkpoint = ProcessCheckpoint(
            metadata=sample_metadata,
            pid="p1", pc=10, status="running",
            program_data={"code": "abc"},
            variables={"x": 1},
            context={"user": "test"}
        )
        checkpoint.metadata.checksum = "invalid_checksum"
        assert checkpoint.verify_integrity() is False

# =============================================================================
# CheckpointConfig Tests
# =============================================================================

class TestCheckpointConfig:
    """CheckpointConfig 测试"""

    def test_default_config(self):
        config = CheckpointConfig.default()
        assert config.checkpoint_interval_seconds == 60
        assert config.max_checkpoints_per_process == 10
        assert config.storage_path == "./checkpoints"

    def test_frequent_config(self):
        config = CheckpointConfig.frequent()
        assert config.checkpoint_interval_seconds == 10
        assert config.max_checkpoints_per_process == 100

    def test_minimal_config(self):
        config = CheckpointConfig.minimal()
        assert config.checkpoint_interval_seconds == 300
        assert config.max_checkpoints_per_process == 3

# =============================================================================
# CheckpointManager Tests
# =============================================================================

class TestCheckpointManager:
    """CheckpointManager 测试"""

    _temp_dir = Path("./test_checkpoints")

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Setup: Create a temporary directory for checkpoints
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        yield
        # Teardown: Remove the temporary directory after tests
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)

    @pytest.fixture
    def manager(self):
        config = CheckpointConfig(storage_path=str(self._temp_dir), compress=False)
        return CheckpointManager(config)

    @pytest.fixture
    def compressed_manager(self):
        config = CheckpointConfig(storage_path=str(self._temp_dir), compress=True)
        return CheckpointManager(config)

    def _get_process_dir(self, pid: str) -> Path:
        return self._temp_dir / pid

    def test_manager_creation(self, manager):
        assert manager is not None
        assert manager.config.storage_path == str(self._temp_dir)

    def test_create_checkpoint(self, manager):
        pid = "process_a"
        checkpoint = manager.create_checkpoint(
            pid=pid, pc=1, status="running",
            program_data={"instr": "add"},
            variables={"a": 1},
            context={"user": "guest"},
            program_name="prog_a"
        )
        assert checkpoint.pid == pid
        assert checkpoint.metadata.program_name == "prog_a"
        assert checkpoint.metadata.checksum != ""

        # Verify file exists
        process_dir = self._get_process_dir(pid)
        assert process_dir.exists()
        assert any(f.name.endswith(".json") for f in process_dir.iterdir())
        assert pid in manager._checkpoints
        assert len(manager._checkpoints[pid]) == 1

    def test_create_checkpoint_compressed(self, compressed_manager):
        pid = "process_c"
        checkpoint = compressed_manager.create_checkpoint(
            pid=pid, pc=1, status="running",
            program_data={"instr": "add"},
            variables={"a": 1},
            context={"user": "guest"},
            program_name="prog_c"
        )
        assert checkpoint.metadata.compressed is True
        process_dir = self._get_process_dir(pid)
        assert any(f.name.endswith(".json.gz") for f in process_dir.iterdir())

    def test_restore_checkpoint_success(self, manager):
        pid = "process_b"
        created_checkpoint = manager.create_checkpoint(
            pid=pid, pc=2, status="paused",
            program_data={"instr": "sub"},
            variables={"b": 2},
            context={"user": "admin"},
            program_name="prog_b"
        )
        restored_checkpoint = manager.restore_checkpoint(created_checkpoint.metadata.id)
        assert restored_checkpoint is not None
        assert restored_checkpoint.pid == pid
        assert restored_checkpoint.pc == 2
        assert restored_checkpoint.verify_integrity() is True

    def test_restore_checkpoint_not_found(self, manager):
        restored_checkpoint = manager.restore_checkpoint("nonexistent_id")
        assert restored_checkpoint is None

    def test_restore_checkpoint_integrity_failure(self, manager):
        pid = "process_d"
        created_checkpoint = manager.create_checkpoint(
            pid=pid, pc=3, status="running",
            program_data={"instr": "mul"},
            variables={"c": 3},
            context={"user": "tester"},
            program_name="prog_d"
        )
        
        # Manually corrupt the file
        process_dir = self._get_process_dir(pid)
        filepath = next(process_dir.glob(f"{created_checkpoint.metadata.id}.json"))
        with open(filepath, "w") as f:
            f.write("corrupted data")

        restored_checkpoint = manager.restore_checkpoint(created_checkpoint.metadata.id)
        assert restored_checkpoint is None

    def test_list_checkpoints_all(self, manager):
        pid1 = "list_proc1"
        pid2 = "list_proc2"
        # Ensure distinct timestamps for sorting in list_checkpoints
        with patch('intentos.distributed.checkpoint.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 0)
            cp_1_1 = manager.create_checkpoint(pid=pid1, pc=1, status="r", program_data={}, variables={}, context={})
            mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 1)
            cp_1_2 = manager.create_checkpoint(pid=pid1, pc=2, status="r", program_data={}, variables={}, context={})
            mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 2)
            cp_2_1 = manager.create_checkpoint(pid=pid2, pc=1, status="r", program_data={}, variables={}, context={})

        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 3
        # Check sort order (newest first)
        assert checkpoints[0].id == cp_2_1.metadata.id
        assert checkpoints[1].id == cp_1_2.metadata.id
        assert checkpoints[2].id == cp_1_1.metadata.id
        assert all(isinstance(cp, CheckpointMetadata) for cp in checkpoints)

    def test_list_checkpoints_by_process_id(self, manager):
        pid1 = "filter_proc1"
        pid2 = "filter_proc2"
        with patch('intentos.distributed.checkpoint.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 0)
            cp_1_1 = manager.create_checkpoint(pid=pid1, pc=1, status="r", program_data={}, variables={}, context={})
            mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 1)
            cp_1_2 = manager.create_checkpoint(pid=pid1, pc=2, status="r", program_data={}, variables={}, context={})
            mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 2)
            cp_2_1 = manager.create_checkpoint(pid=pid2, pc=1, status="r", program_data={}, variables={}, context={})

        checkpoints = manager.list_checkpoints(process_id=pid1)
        assert len(checkpoints) == 2
        assert all(cp.process_id == pid1 for cp in checkpoints)
        assert checkpoints[0].id == cp_1_2.metadata.id
        assert checkpoints[1].id == cp_1_1.metadata.id

    @patch('intentos.distributed.checkpoint.datetime')
    def test_retention_policy_cleanup(self, mock_datetime, manager):
        manager.config.retention_hours = 1 # 1 hour retention
        pid = "retention_process"

        # Create an old checkpoint (should be cleaned up)
        old_time = datetime(2023, 1, 1, 8, 0, 0) # 2 hours old
        mock_datetime.now.return_value = old_time
        old_cp = manager.create_checkpoint(pid=pid, pc=1, status="r", program_data={}, variables={}, context={})

        # Create recent checkpoints (should remain)
        mid_time = datetime(2023, 1, 1, 9, 30, 0) # 30 mins old
        mock_datetime.now.return_value = mid_time
        mid_cp = manager.create_checkpoint(pid=pid, pc=2, status="r", program_data={}, variables={}, context={})

        latest_time = datetime(2023, 1, 1, 10, 0, 0) # Current time for cleanup check
        mock_datetime.now.return_value = latest_time
        latest_cp = manager.create_checkpoint(pid=pid, pc=3, status="r", program_data={}, variables={}, context={})

        # After cleanup, old_cp should be gone, mid_cp and latest_cp should remain
        assert len(manager._checkpoints[pid]) == 2
        assert old_cp.metadata.id not in [cp.id for cp in manager._checkpoints[pid]]
        assert mid_cp.metadata.id in [cp.id for cp in manager._checkpoints[pid]]
        assert latest_cp.metadata.id in [cp.id for cp in manager._checkpoints[pid]]
        assert not (manager._storage_path / pid / f"{old_cp.metadata.id}.json").exists()
        assert (manager._storage_path / pid / f"{mid_cp.metadata.id}.json").exists()
        assert (manager._storage_path / pid / f"{latest_cp.metadata.id}.json").exists()

    @patch('intentos.distributed.checkpoint.datetime')
    def test_max_checkpoints_per_process(self, mock_datetime, manager):
        pid = "max_cp_process"
        manager.config.max_checkpoints_per_process = 2
        base_time = datetime(2023, 1, 1, 10, 0, 0)

        # Create 3 checkpoints
        mock_datetime.now.return_value = base_time
        cp1 = manager.create_checkpoint(pid=pid, pc=1, status="r", program_data={}, variables={}, context={})
        mock_datetime.now.return_value = base_time + timedelta(seconds=1)
        cp2 = manager.create_checkpoint(pid=pid, pc=2, status="r", program_data={}, variables={}, context={})
        mock_datetime.now.return_value = base_time + timedelta(seconds=2)
        cp3 = manager.create_checkpoint(pid=pid, pc=3, status="r", program_data={}, variables={}, context={})

        # The manager should now only contain the 2 most recent checkpoints
        assert len(manager._checkpoints[pid]) == 2
        assert cp1.metadata.id not in [cp.id for cp in manager._checkpoints[pid]] # cp1 should be removed
        assert cp2.metadata.id in [cp.id for cp in manager._checkpoints[pid]]
        assert cp3.metadata.id in [cp.id for cp in manager._checkpoints[pid]]
        assert not (manager._storage_path / pid / f"{cp1.metadata.id}.json").exists()
        assert (manager._storage_path / pid / f"{cp2.metadata.id}.json").exists()
        assert (manager._storage_path / pid / f"{cp3.metadata.id}.json").exists()

