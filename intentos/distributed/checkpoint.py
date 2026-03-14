"""
检查点与恢复

提供进程状态持久化和故障恢复

设计文档：docs/private/008-checkpoint-recovery.md
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CheckpointType(Enum):
    """检查点类型"""

    FULL = "full"
    INCREMENTAL = "incremental"
    SNAPSHOT = "snapshot"


@dataclass
class CheckpointMetadata:
    """检查点元数据"""

    id: str = field(
        default_factory=lambda: str(hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])
    )
    type: CheckpointType = CheckpointType.FULL
    timestamp: datetime = field(default_factory=datetime.now)

    process_id: str = ""
    program_name: str = ""
    node_id: str = ""

    size_bytes: int = 0
    compressed: bool = False
    checksum: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "process_id": self.process_id,
            "program_name": self.program_name,
            "node_id": self.node_id,
            "size_bytes": self.size_bytes,
            "compressed": self.compressed,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CheckpointMetadata:
        return cls(
            id=data["id"],
            type=CheckpointType(data["type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            process_id=data.get("process_id", ""),
            program_name=data.get("program_name", ""),
            node_id=data.get("node_id", ""),
            size_bytes=data.get("size_bytes", 0),
            compressed=data.get("compressed", False),
            checksum=data.get("checksum", ""),
        )


@dataclass
class ProcessCheckpoint:
    """进程检查点"""

    metadata: CheckpointMetadata

    pid: str
    pc: int
    status: str

    program_data: dict
    variables: dict
    context: dict

    gas_state: Optional[dict] = None
    execution_log: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata.to_dict(),
            "pid": self.pid,
            "pc": self.pc,
            "status": self.status,
            "program_data": self.program_data,
            "variables": self.variables,
            "context": self.context,
            "gas_state": self.gas_state,
            "execution_log": self.execution_log,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProcessCheckpoint:
        return cls(
            metadata=CheckpointMetadata.from_dict(data["metadata"]),
            pid=data["pid"],
            pc=data["pc"],
            status=data["status"],
            program_data=data["program_data"],
            variables=data["variables"],
            context=data["context"],
            gas_state=data.get("gas_state"),
            execution_log=data.get("execution_log", []),
        )

    def compute_checksum(self) -> str:
        """计算校验和"""
        import hashlib

        # 不包含 checksum 本身在计算中
        data = {
            "pid": self.pid,
            "pc": self.pc,
            "status": self.status,
            "program_data": self.program_data,
            "variables": self.variables,
            "context": self.context,
            "gas_state": self.gas_state,
            "execution_log": self.execution_log,
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """验证完整性"""
        return self.metadata.checksum == self.compute_checksum()


@dataclass
class CheckpointConfig:
    """检查点配置"""

    checkpoint_interval_seconds: int = 60
    max_checkpoints_per_process: int = 10
    retention_hours: int = 24

    storage_backend: str = "disk"
    storage_path: str = "./checkpoints"
    compress: bool = True

    @classmethod
    def default(cls) -> CheckpointConfig:
        return cls()

    @classmethod
    def frequent(cls) -> CheckpointConfig:
        """频繁检查点"""
        return cls(
            checkpoint_interval_seconds=10,
            max_checkpoints_per_process=100,
        )

    @classmethod
    def minimal(cls) -> CheckpointConfig:
        """最小检查点"""
        return cls(
            checkpoint_interval_seconds=300,
            max_checkpoints_per_process=3,
        )


class CheckpointManager:
    """检查点管理器"""

    def __init__(
        self,
        config: Optional[CheckpointConfig] = None,
    ):
        self.config = config or CheckpointConfig.default()
        self._storage_path = Path(self.config.storage_path)
        self._checkpoints: dict[str, list[CheckpointMetadata]] = {}

    def create_checkpoint(
        self,
        pid: str,
        pc: int,
        status: str,
        program_data: dict,
        variables: dict,
        context: dict,
        program_name: str = "",
    ) -> ProcessCheckpoint:
        """创建检查点"""
        metadata = CheckpointMetadata(
            type=CheckpointType.FULL,
            process_id=pid,
            program_name=program_name,
        )

        checkpoint = ProcessCheckpoint(
            metadata=metadata,
            pid=pid,
            pc=pc,
            status=status,
            program_data=program_data,
            variables=variables,
            context=context,
        )

        checkpoint.metadata.checksum = checkpoint.compute_checksum()

        self._save_checkpoint(checkpoint)

        logger.debug(f"创建检查点：{checkpoint.metadata.id} (进程 {pid})")

        return checkpoint

    def restore_checkpoint(
        self,
        checkpoint_id: str,
    ) -> Optional[ProcessCheckpoint]:
        """从检查点恢复"""
        checkpoint = self._load_checkpoint(checkpoint_id)

        if not checkpoint:
            logger.error(f"检查点不存在：{checkpoint_id}")
            return None

        if not checkpoint.verify_integrity():
            logger.error(f"检查点完整性验证失败：{checkpoint_id}")
            return None

        logger.info(f"从检查点恢复进程：{checkpoint.pid}")

        return checkpoint

    def _save_checkpoint(self, checkpoint: ProcessCheckpoint) -> None:
        """保存检查点"""
        # 计算校验和
        checkpoint.metadata.checksum = checkpoint.compute_checksum()

        data = json.dumps(checkpoint.to_dict(), indent=2, ensure_ascii=False)

        if self.config.compress:
            data_bytes = gzip.compress(data.encode("utf-8"))
            checkpoint.metadata.compressed = True
        else:
            data_bytes = data.encode("utf-8")

        checkpoint.metadata.size_bytes = len(data_bytes)

        filename = (
            f"{checkpoint.metadata.id}.json.gz"
            if self.config.compress
            else f"{checkpoint.metadata.id}.json"
        )
        filepath = self._storage_path / checkpoint.metadata.process_id / filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(data_bytes)

        # 注册到内存索引
        if checkpoint.metadata.process_id not in self._checkpoints:
            self._checkpoints[checkpoint.metadata.process_id] = []
        self._checkpoints[checkpoint.metadata.process_id].append(checkpoint.metadata)

        # 清理旧检查点
        self._cleanup_old_checkpoints(checkpoint.metadata.process_id)

    def _cleanup_old_checkpoints(self, process_id: str) -> None:
        """清理旧的检查点"""
        if process_id not in self._checkpoints:
            return

        checkpoints_for_process = self._checkpoints[process_id]

        # 按时间戳排序 (最旧在前)
        checkpoints_for_process.sort(key=lambda c: c.timestamp)

        # 1. 根据 retention_hours 清理
        retained_by_retention = []
        if self.config.retention_hours > 0:
            now = datetime.now()
            retention_threshold = now - timedelta(hours=self.config.retention_hours)
            retained_by_retention = [
                cp for cp in checkpoints_for_process if cp.timestamp >= retention_threshold
            ]
        else:
            retained_by_retention = list(checkpoints_for_process)

        # 2. 根据 max_checkpoints_per_process 清理
        checkpoints_to_keep = []
        if (
            self.config.max_checkpoints_per_process > 0
            and len(retained_by_retention) > self.config.max_checkpoints_per_process
        ):
            # 保留最新的 max_checkpoints_per_process 个
            checkpoints_to_keep = retained_by_retention[-self.config.max_checkpoints_per_process :]
        else:
            checkpoints_to_keep = retained_by_retention

        ids_to_keep = {cp.id for cp in checkpoints_to_keep}
        ids_to_remove = {cp.id for cp in checkpoints_for_process if cp.id not in ids_to_keep}

        for cp_id in ids_to_remove:
            cp_meta_to_remove = next((cp for cp in checkpoints_for_process if cp.id == cp_id), None)
            if cp_meta_to_remove:
                filename = (
                    f"{cp_meta_to_remove.id}.json.gz"
                    if cp_meta_to_remove.compressed
                    else f"{cp_meta_to_remove.id}.json"
                )
                filepath = self._storage_path / process_id / filename
                if filepath.exists():
                    filepath.unlink()  # 删除文件

        # 最后，更新内存中的列表
        self._checkpoints[process_id] = [
            cp for cp in checkpoints_for_process if cp.id not in ids_to_remove
        ]

    def _load_checkpoint(self, checkpoint_id: str) -> Optional[ProcessCheckpoint]:
        """加载检查点"""
        for process_id, checkpoints in self._checkpoints.items():
            for cp_meta in checkpoints:
                if cp_meta.id == checkpoint_id:
                    filename = (
                        f"{checkpoint_id}.json.gz"
                        if cp_meta.compressed
                        else f"{checkpoint_id}.json"
                    )
                    filepath = self._storage_path / process_id / filename

                    if not filepath.exists():
                        return None

                    with open(filepath, "rb") as f:
                        data_bytes = f.read()

                    if cp_meta.compressed:
                        data = gzip.decompress(data_bytes).decode("utf-8")
                    else:
                        data = data_bytes.decode("utf-8")

                    try:
                        data_dict = json.loads(data)
                    except json.JSONDecodeError:
                        logger.error(f"检查点文件 {filepath} 内容损坏或格式不正确")
                        return None
                    return ProcessCheckpoint.from_dict(data_dict)

        return None

    def list_checkpoints(
        self,
        process_id: Optional[str] = None,
    ) -> list[CheckpointMetadata]:
        """列出检查点"""
        if process_id:
            checkpoints = self._checkpoints.get(process_id, [])
        else:
            all_checkpoints = []
            for cps in self._checkpoints.values():
                all_checkpoints.extend(cps)
            checkpoints = all_checkpoints

        return sorted(checkpoints, key=lambda c: c.timestamp, reverse=True)
