"""
测试 intentos.semantic_vm.transaction - 事务支持

覆盖:
- TransactionStatus / IsolationLevel 枚举
- WriteOperation (创建, to_dict)
- Transaction (创建, duration, write_log)
"""


import pytest


class TestTransactionStatus:
    """事务状态枚举测试"""

    def test_all_statuses_exist(self):
        from intentos.semantic_vm.transaction import TransactionStatus
        statuses = [s.value for s in TransactionStatus]
        assert "active" in statuses
        assert "committed" in statuses
        assert "rolled_back" in statuses
        assert "failed" in statuses


class TestIsolationLevel:
    """隔离级别测试"""

    def test_all_levels_exist(self):
        from intentos.semantic_vm.transaction import IsolationLevel
        levels = [l.value for l in IsolationLevel]
        assert "read_uncommitted" in levels
        assert "serializable" in levels


class TestWriteOperation:
    """写操作记录测试"""

    def test_create_write_operation(self):
        from intentos.semantic_vm.transaction import WriteOperation
        op = WriteOperation(
            operation="set",
            store="memory",
            key="user_data",
            old_value=None,
            new_value={"name": "Alice"},
           )
        assert op.operation == "set"
        assert op.store == "memory"

    def test_to_dict(self):
        from intentos.semantic_vm.transaction import WriteOperation
        op = WriteOperation(
            operation="delete",
            store="cache",
            key="expired_entry",
            old_value={"data": "old"},
            new_value=None,
           )
        d = op.to_dict()
        assert d["operation"] == "delete"
        assert d["store"] == "cache"


class TestTransaction:
    """事务测试"""

    def test_create_transaction(self):
        from intentos.semantic_vm.transaction import Transaction, TransactionStatus
        tx = Transaction()
        assert tx.status == TransactionStatus.ACTIVE
        assert len(tx.write_log) == 0

    def test_duration_zero_when_active(self):
        from intentos.semantic_vm.transaction import Transaction
        tx = Transaction()
        assert tx.duration == 0.0

    def test_transaction_with_program_id(self):
        from intentos.semantic_vm.transaction import Transaction
        tx = Transaction(program_id="prog_123")
        assert tx.program_id == "prog_123"
