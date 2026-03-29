"""
Kernel Core Module Tests

测试内核态/用户态分离、保护内存、系统调用等核心功能
"""

import pytest
from intentos.kernel.core import (
    PrivilegeLevel,
    MemoryRegion,
    ProtectedMemory,
    SyscallTable,
    InvalidSyscallError,
    KernelMode,
    UserMode,
    ProtectionDomain,
    SecurityChecker,
)


class TestPrivilegeLevel:
    """测试特权级别枚举"""

    def test_kernel_level_value(self):
        """内核特权级别应为 0"""
        assert PrivilegeLevel.KERNEL.value == 0

    def test_user_level_value(self):
        """用户特权级别应为 3"""
        assert PrivilegeLevel.USER.value == 3

    def test_kernel_less_privileged_than_user(self):
        """内核特权级别数值小于用户（数值越小权限越高）"""
        assert PrivilegeLevel.KERNEL.value < PrivilegeLevel.USER.value


class TestMemoryRegion:
    """测试内存区域"""

    def test_create_region(self):
        """创建内存区域"""
        region = MemoryRegion(
            start=0x1000,
            end=0x1FFF,
            permissions="rw",
            owner="kernel"
        )
        assert region.start == 0x1000
        assert region.end == 0x1FFF
        assert region.permissions == "rw"
        assert region.owner == "kernel"

    def test_contains_address(self):
        """测试地址是否在区域内"""
        region = MemoryRegion(start=100, end=200, permissions="rw")
        
        assert region.contains(100) is True
        assert region.contains(150) is True
        assert region.contains(200) is True
        assert region.contains(99) is False
        assert region.contains(201) is False

    def test_can_access_read(self):
        """测试读权限"""
        region = MemoryRegion(start=0, end=100, permissions="r")
        assert region.can_access("r") is True
        assert region.can_access("w") is False

    def test_can_access_write(self):
        """测试写权限"""
        region = MemoryRegion(start=0, end=100, permissions="w")
        assert region.can_access("r") is False
        assert region.can_access("w") is True

    def test_can_access_read_write(self):
        """测试读写权限"""
        region = MemoryRegion(start=0, end=100, permissions="rw")
        assert region.can_access("r") is True
        assert region.can_access("w") is True

    def test_can_access_execute(self):
        """测试执行权限"""
        region = MemoryRegion(start=0, end=100, permissions="rx")
        assert region.can_access("r") is True
        assert region.can_access("x") is True
        assert region.can_access("w") is False


class TestProtectedMemory:
    """测试保护内存"""

    def test_add_region(self):
        """添加内存区域"""
        memory = ProtectedMemory()
        region = MemoryRegion(start=0, end=100, permissions="rw")
        memory.add_region(region)
        # 不抛出异常即为成功

    def test_read_unmapped_address(self):
        """读取未映射地址应抛出异常"""
        memory = ProtectedMemory()
        with pytest.raises(MemoryError, match="地址 100 未映射"):
            memory.read(100)

    def test_write_unmapped_address(self):
        """写入未映射地址应抛出异常"""
        memory = ProtectedMemory()
        with pytest.raises(MemoryError, match="地址 100 未映射"):
            memory.write(100, "value")

    def test_read_no_permission(self):
        """读取无权限区域应抛出异常"""
        memory = ProtectedMemory()
        region = MemoryRegion(start=0, end=100, permissions="w")
        memory.add_region(region)
        
        with pytest.raises(MemoryError, match="地址 50 不可读"):
            memory.read(50)

    def test_write_no_permission(self):
        """写入无权限区域应抛出异常"""
        memory = ProtectedMemory()
        region = MemoryRegion(start=0, end=100, permissions="r")
        memory.add_region(region)
        
        with pytest.raises(MemoryError, match="地址 50 不可写"):
            memory.write(50, "value")

    def test_user_read_kernel_memory(self):
        """用户程序读取内核内存应抛出权限异常"""
        memory = ProtectedMemory()
        region = MemoryRegion(start=0, end=100, permissions="rw", owner="kernel")
        memory.add_region(region)
        
        with pytest.raises(PermissionError, match="用户程序不能读取内核内存"):
            memory.read(50, caller="user")

    def test_user_write_kernel_memory(self):
        """用户程序写入内核内存应抛出权限异常"""
        memory = ProtectedMemory()
        region = MemoryRegion(start=0, end=100, permissions="rw", owner="kernel")
        memory.add_region(region)
        
        with pytest.raises(PermissionError, match="用户程序不能写入内核内存"):
            memory.write(50, "value", caller="user")

    def test_read_write_value(self):
        """正常读写操作"""
        memory = ProtectedMemory()
        region = MemoryRegion(start=0, end=100, permissions="rw", owner="user")
        memory.add_region(region)
        
        memory.write(50, "test_value", caller="user")
        value = memory.read(50, caller="user")
        assert value == "test_value"


class TestSyscallTable:
    """测试系统调用表"""

    def test_register_and_call(self):
        """注册并调用系统调用"""
        table = SyscallTable()
        
        def mock_handler(x, y):
            return x + y
        
        table.register(0, "add", mock_handler)
        result = table.call(0, 2, 3)
        assert result == 5

    def test_call_invalid_syscall(self):
        """调用不存在的系统调用应抛出异常"""
        table = SyscallTable()
        
        with pytest.raises(InvalidSyscallError, match="无效的系统调用"):
            table.call(999)

    def test_get_name(self):
        """获取系统调用名称"""
        table = SyscallTable()
        table.register(5, "test_call", lambda: None)
        
        assert table.get_name(5) == "test_call"
        assert table.get_name(999).startswith("unknown_")


class TestKernelMode:
    """测试内核空间"""

    def test_initialization(self):
        """内核初始化"""
        kernel = KernelMode()
        
        assert kernel.kernel_memory is not None
        assert kernel.syscall_table is not None
        assert isinstance(kernel.process_table, dict)

    def test_syscall_read(self):
        """测试读系统调用"""
        kernel = KernelMode()
        result = kernel.syscall(0, (0, bytearray(10), 10))
        assert result == 0

    def test_syscall_write(self):
        """测试写系统调用"""
        kernel = KernelMode()
        result = kernel.syscall(1, (0, b"data", 4))
        assert result == 0

    def test_syscall_open(self):
        """测试打开系统调用"""
        kernel = KernelMode()
        result = kernel.syscall(2, ("/test/file", 0))
        assert result == 0

    def test_syscall_close(self):
        """测试关闭系统调用"""
        kernel = KernelMode()
        result = kernel.syscall(3, (0,))
        assert result == 0

    def test_syscall_create(self):
        """测试创建系统调用"""
        kernel = KernelMode()
        result = kernel.syscall(4, ("INTENT", "test", {"data": "value"}))
        assert result == 0

    def test_syscall_modify(self):
        """测试修改系统调用"""
        kernel = KernelMode()
        result = kernel.syscall(5, ("INTENT", "test", {"data": "new_value"}))
        assert result == 0

    def test_syscall_execute(self):
        """测试执行系统调用"""
        kernel = KernelMode()
        result = kernel.syscall(6, ("program_id", {"context": "data"}))
        assert result == {}

    def test_syscall_bootstrap(self):
        """测试 Bootstrap 系统调用"""
        kernel = KernelMode()
        result = kernel.syscall(7, ("CREATE", "intent", {"data": "value"}))
        assert result is True

    def test_syscall_invalid(self):
        """测试无效系统调用"""
        kernel = KernelMode()
        
        with pytest.raises(InvalidSyscallError):
            kernel.syscall(999, ())


class TestUserMode:
    """测试用户空间"""

    def test_initialization(self):
        """用户空间初始化"""
        kernel = KernelMode()
        user = UserMode(kernel)
        
        assert user.kernel is kernel
        assert isinstance(user.user_memory, dict)
        assert user.protection_domain.level == PrivilegeLevel.USER

    def test_allowed_syscall(self):
        """用户程序调用允许的系统调用"""
        kernel = KernelMode()
        user = UserMode(kernel)
        
        result = user.syscall(0, 0, bytearray(10), 10)
        assert result == 0

    def test_blocked_syscall(self):
        """用户程序调用不允许的系统调用"""
        kernel = KernelMode()
        user = UserMode(kernel)
        
        # 假设 syscall 8 不在允许列表中
        with pytest.raises(PermissionError):
            user.syscall(8)

    def test_modify_config_blocked(self):
        """用户程序修改 CONFIG 应被阻止"""
        kernel = KernelMode()
        user = UserMode(kernel)
        
        with pytest.raises(PermissionError, match="禁止在用户态修改"):
            user.syscall(5, "CONFIG", "key", "value")

    def test_modify_policy_blocked(self):
        """用户程序修改 POLICY 应被阻止"""
        kernel = KernelMode()
        user = UserMode(kernel)
        
        with pytest.raises(PermissionError, match="禁止在用户态修改"):
            user.syscall(5, "POLICY", "key", "value")

    def test_modify_intent_allowed(self):
        """用户程序修改 INTENT 应被允许"""
        kernel = KernelMode()
        user = UserMode(kernel)
        
        # 不应抛出异常
        result = user.syscall(5, "INTENT", "test", {"data": "value"})
        assert result == 0

    def test_execute_program(self):
        """执行程序"""
        kernel = KernelMode()
        user = UserMode(kernel)
        
        result = user.execute_program({"program": "test"})
        assert result == {}


class TestProtectionDomain:
    """测试保护域"""

    def test_create_domain(self):
        """创建保护域"""
        domain = ProtectionDomain(
            level=PrivilegeLevel.USER,
            allowed_syscalls={0, 1, 2, 3}
        )
        
        assert domain.level == PrivilegeLevel.USER
        assert len(domain.allowed_syscalls) == 4


class TestSecurityChecker:
    """测试安全检查器"""

    def test_kernel_can_call_any_syscall(self):
        """内核可以调用任何系统调用"""
        assert SecurityChecker.check_syscall_permission(
            PrivilegeLevel.KERNEL, 999
        ) is True

    def test_user_allowed_syscall(self):
        """用户可以调用允许的系统调用"""
        assert SecurityChecker.check_syscall_permission(
            PrivilegeLevel.USER, 0
        ) is True

    def test_user_blocked_syscall(self):
        """用户不能调用不允许的系统调用"""
        assert SecurityChecker.check_syscall_permission(
            PrivilegeLevel.USER, 999
        ) is False

    def test_memory_access_allowed(self):
        """内存访问权限检查 - 允许"""
        region = MemoryRegion(start=0, end=100, permissions="rw", owner="user")
        
        assert SecurityChecker.check_memory_access(
            PrivilegeLevel.USER, 50, "r", [region]
        ) is True

    def test_memory_access_no_permission(self):
        """内存访问权限检查 - 无操作权限"""
        region = MemoryRegion(start=0, end=100, permissions="r", owner="user")
        
        assert SecurityChecker.check_memory_access(
            PrivilegeLevel.USER, 50, "w", [region]
        ) is False

    def test_memory_access_kernel_region(self):
        """内存访问权限检查 - 内核区域"""
        region = MemoryRegion(start=0, end=100, permissions="rw", owner="kernel")
        
        assert SecurityChecker.check_memory_access(
            PrivilegeLevel.USER, 50, "r", [region]
        ) is False

    def test_memory_access_not_found(self):
        """内存访问权限检查 - 未找到区域"""
        assert SecurityChecker.check_memory_access(
            PrivilegeLevel.USER, 50, "r", []
        ) is False
