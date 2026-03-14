"""
事务支持

提供 ACID 语义的事务管理

设计文档：docs/private/005-transaction-support.md
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TransactionStatus(Enum):
    """事务状态"""
    ACTIVE = "active"
    COMMITTING = "committing"
    COMMITTED = "committed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class IsolationLevel(Enum):
    """隔离级别"""
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


@dataclass
class WriteOperation:
    """写操作记录"""
    
    operation: str  # "set", "delete", "modify"
    store: str
    key: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "store": self.store,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Transaction:
    """事务对象"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TransactionStatus = TransactionStatus.ACTIVE
    isolation_level: IsolationLevel = IsolationLevel.SERIALIZABLE
    
    write_log: list[WriteOperation] = field(default_factory=list)
    read_set: dict[str, Any] = field(default_factory=dict)
    write_set: dict[str, WriteOperation] = field(default_factory=dict)
    
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    program_id: str = ""
    
    @property
    def duration(self) -> float:
        """事务持续时间（秒）"""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()
    
    def add_write(self, op: WriteOperation) -> None:
        """添加写操作"""
        self.write_log.append(op)
        key = f"{op.store}:{op.key}"
        self.write_set[key] = op
    
    def add_read(self, key: str, value: Any) -> None:
        """添加读记录"""
        self.read_set[key] = value
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "isolation_level": self.isolation_level.value,
            "write_log": [op.to_dict() for op in self.write_log],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "program_id": self.program_id,
        }


class TransactionManager:
    """事务管理器"""
    
    def __init__(self):
        self._active_transactions: dict[str, Transaction] = {}
        self._committed_transactions: dict[str, Transaction] = {}
        self._locks: dict[str, Any] = {}
        self.max_transaction_duration = 300.0
    
    def begin_transaction(
        self,
        isolation_level: IsolationLevel = IsolationLevel.SERIALIZABLE,
        program_id: str = "",
    ) -> Transaction:
        """开始事务"""
        tx = Transaction(
            isolation_level=isolation_level,
            program_id=program_id,
        )
        
        self._active_transactions[tx.id] = tx
        return tx
    
    def commit_transaction(self, tx: Transaction, memory: Any) -> bool:
        """提交事务"""
        if tx.status != TransactionStatus.ACTIVE:
            return False
        
        tx.status = TransactionStatus.COMMITTING
        
        try:
            # 应用写操作
            for op in tx.write_log:
                if op.operation == "set":
                    memory.set(op.store, op.key, op.new_value)
                elif op.operation == "delete":
                    memory.delete(op.store, op.key)
            
            tx.status = TransactionStatus.COMMITTED
            tx.end_time = datetime.now()
            
            # 移动到已提交事务
            del self._active_transactions[tx.id]
            self._committed_transactions[tx.id] = tx
            
            # 清理旧的已提交事务
            if len(self._committed_transactions) > 100:
                oldest_id = list(self._committed_transactions.keys())[0]
                del self._committed_transactions[oldest_id]
            
            return True
            
        except Exception as e:
            tx.status = TransactionStatus.FAILED
            tx.end_time = datetime.now()
            return False
    
    def rollback_transaction(self, tx: Transaction, memory: Any) -> bool:
        """回滚事务"""
        if tx.status not in [TransactionStatus.ACTIVE, TransactionStatus.FAILED]:
            return False
        
        tx.status = TransactionStatus.ROLLING_BACK
        
        try:
            # 按相反顺序撤销写操作
            for op in reversed(tx.write_log):
                if op.old_value is None:
                    memory.delete(op.store, op.key)
                else:
                    memory.set(op.store, op.key, op.old_value)
            
            tx.status = TransactionStatus.ROLLED_BACK
            tx.end_time = datetime.now()
            
            del self._active_transactions[tx.id]
            return True
            
        except Exception:
            tx.status = TransactionStatus.FAILED
            tx.end_time = datetime.now()
            return False
    
    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        """获取事务"""
        return (
            self._active_transactions.get(tx_id) or
            self._committed_transactions.get(tx_id)
        )
    
    def get_active_transactions(self) -> list[Transaction]:
        """获取所有活跃事务"""
        return list(self._active_transactions.values())


class TransactionalMemory:
    """事务性内存包装器"""
    
    def __init__(self, memory: Any):
        self._memory = memory
        self._current_transaction: Optional[Transaction] = None
    
    def begin_transaction(
        self,
        isolation_level: IsolationLevel = IsolationLevel.SERIALIZABLE,
    ) -> Transaction:
        """开始事务"""
        self._current_transaction = Transaction(
            isolation_level=isolation_level,
        )
        return self._current_transaction
    
    def commit(self) -> bool:
        """提交当前事务"""
        if self._current_transaction is None:
            return False
        
        success = TransactionManager().commit_transaction(
            self._current_transaction, self._memory
        )
        
        if success:
            self._current_transaction = None
        
        return success
    
    def rollback(self) -> bool:
        """回滚当前事务"""
        if self._current_transaction is None:
            return False
        
        success = TransactionManager().rollback_transaction(
            self._current_transaction, self._memory
        )
        
        self._current_transaction = None
        return success
    
    def get(self, store: str, key: str) -> Optional[Any]:
        """获取数据（支持事务）"""
        if self._current_transaction:
            # 检查写集合
            tx_key = f"{store}:{key}"
            if tx_key in self._current_transaction.write_set:
                op = self._current_transaction.write_set[tx_key]
                return op.new_value
            
            # 记录读集合
            value = self._memory.get(store, key)
            self._current_transaction.add_read(tx_key, value)
            return value
        
        return self._memory.get(store, key)
    
    def set(self, store: str, key: str, value: Any) -> None:
        """设置数据（支持事务）"""
        if self._current_transaction:
            # 记录写操作
            old_value = self._memory.get(store, key)
            op = WriteOperation(
                operation="set",
                store=store,
                key=key,
                old_value=old_value,
                new_value=value,
            )
            self._current_transaction.add_write(op)
        
        self._memory.set(store, key, value)
    
    def delete(self, store: str, key: str) -> bool:
        """删除数据（支持事务）"""
        if self._current_transaction:
            old_value = self._memory.get(store, key)
            op = WriteOperation(
                operation="delete",
                store=store,
                key=key,
                old_value=old_value,
                new_value=None,
            )
            self._current_transaction.add_write(op)
        
        return self._memory.delete(store, key)
