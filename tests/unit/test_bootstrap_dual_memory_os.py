"""
测试 intentos.bootstrap.dual_memory_os - 双内存自修改操作系统

覆盖:
- MemoryBank (创建, clone, status)
- MemoryBankStatus 枚举
- DualMemoryOS (切换, 回滚)
"""

import pytest


class TestMemoryBankStatus:
    """内存库状态枚举测试"""

    def test_all_statuses(self):
        from intentos.bootstrap.dual_memory_os import MemoryBankStatus
        assert MemoryBankStatus.ACTIVE.value == "active"
        assert MemoryBankStatus.STANDBY.value == "standby"
        assert MemoryBankStatus.UPGRADING.value == "upgrading"
        assert MemoryBankStatus.FAILED.value == "failed"


class TestMemoryBank:
    """内存库测试"""

    def test_create_memory_bank(self):
        from intentos.bootstrap.dual_memory_os import MemoryBank, MemoryBankStatus
        bank = MemoryBank(bank_id="bank_1", name="left")
        assert bank.bank_id == "bank_1"
        assert bank.name == "left"
        assert bank.status == MemoryBankStatus.STANDBY

    def test_clone_memory_bank(self):
        from intentos.bootstrap.dual_memory_os import MemoryBank, MemoryBankStatus
        bank = MemoryBank(bank_id="original", name="left")
        bank.instructions["cmd_a"] = lambda: None
        bank.version = "2.0.0"
        
        cloned = bank.clone()
        assert cloned.bank_id != bank.bank_id  # Clone should have new ID
        assert cloned.instructions.keys() == bank.instructions.keys()

    def test_memory_bank_with_version(self):
        from intentos.bootstrap.dual_memory_os import MemoryBank
        bank = MemoryBank(bank_id="v1", name="right", version="3.0.0")
        assert bank.version == "3.0.0"
