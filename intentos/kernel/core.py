"""
内核态/用户态分离

提供特权级别隔离和系统调用接口

设计文档：docs/private/015-kernel-user-separation.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class PrivilegeLevel(Enum):
    """特权级别"""

    KERNEL = 0
    USER = 3


@dataclass
class MemoryRegion:
    """内存区域"""

    start: int
    end: int
    permissions: str  # "r", "w", "x", "rw", "rx", "rwx"
    owner: str = "kernel"

    def contains(self, address: int) -> bool:
        return self.start <= address <= self.end

    def can_access(self, operation: str) -> bool:
        return operation in self.permissions


class ProtectedMemory:
    """受保护的内存"""

    def __init__(self):
        self._regions: list[MemoryRegion] = []
        self._data: dict[int, Any] = {}

    def add_region(self, region: MemoryRegion) -> None:
        """添加内存区域"""
        self._regions.append(region)

    def read(self, address: int, caller: str = "kernel") -> Any:
        """读取内存"""
        region = self._find_region(address)

        if not region:
            raise MemoryError(f"地址 {address} 未映射")

        if not region.can_access("r"):
            raise MemoryError(f"地址 {address} 不可读")

        if caller == "user" and region.owner == "kernel":
            raise PermissionError(f"用户程序不能读取内核内存 {address}")

        return self._data.get(address)

    def write(self, address: int, value: Any, caller: str = "kernel") -> None:
        """写入内存"""
        region = self._find_region(address)

        if not region:
            raise MemoryError(f"地址 {address} 未映射")

        if not region.can_access("w"):
            raise MemoryError(f"地址 {address} 不可写")

        if caller == "user" and region.owner == "kernel":
            raise PermissionError(f"用户程序不能写入内核内存 {address}")

        self._data[address] = value

    def _find_region(self, address: int) -> Optional[MemoryRegion]:
        """查找地址所在的区域"""
        for region in self._regions:
            if region.contains(address):
                return region
        return None


class SyscallTable:
    """系统调用表"""

    def __init__(self):
        self._handlers: dict[int, Callable] = {}
        self._names: dict[int, str] = {}

    def register(
        self,
        number: int,
        name: str,
        handler: Callable,
    ) -> None:
        """注册系统调用"""
        self._handlers[number] = handler
        self._names[number] = name

    def call(
        self,
        number: int,
        *args,
        **kwargs,
    ) -> Any:
        """调用系统调用"""
        if number not in self._handlers:
            raise InvalidSyscallError(f"无效的系统调用：{number}")

        handler = self._handlers[number]
        return handler(*args, **kwargs)

    def get_name(self, number: int) -> str:
        """获取系统调用名称"""
        return self._names.get(number, f"unknown_{number}")


class InvalidSyscallError(Exception):
    """无效系统调用错误"""

    pass


class KernelMode:
    """内核空间"""

    def __init__(self):
        self.kernel_memory = ProtectedMemory()
        self.syscall_table = SyscallTable()
        self.process_table: dict[int, Any] = {}

        self._register_syscalls()

    def _register_syscalls(self) -> None:
        """注册系统调用"""
        self.syscall_table.register(0, "read", self.sys_read)
        self.syscall_table.register(1, "write", self.sys_write)
        self.syscall_table.register(2, "open", self.sys_open)
        self.syscall_table.register(3, "close", self.sys_close)
        self.syscall_table.register(4, "create", self.sys_create)
        self.syscall_table.register(5, "modify", self.sys_modify)
        self.syscall_table.register(6, "execute", self.sys_execute)
        self.syscall_table.register(7, "bootstrap", self.sys_bootstrap)

    def syscall(self, call_id: int, args: tuple, caller: str = "user") -> Any:
        """系统调用入口"""
        try:
            result = self.syscall_table.call(call_id, *args)
            return result
        except InvalidSyscallError as e:
            logger.error(f"无效系统调用：{call_id}")
            raise
        except Exception as e:
            logger.exception(f"系统调用失败：{e}")
            raise

    def sys_read(self, fd: int, buffer: bytearray, size: int) -> int:
        """读取数据"""
        return 0

    def sys_write(self, fd: int, buffer: bytes, size: int) -> int:
        """写入数据"""
        return 0

    def sys_open(self, path: str, flags: int) -> int:
        """打开文件"""
        return 0

    def sys_close(self, fd: int) -> int:
        """关闭文件"""
        return 0

    def sys_create(self, target_type: str, name: str, data: Any) -> int:
        """创建意图对象"""
        return 0

    def sys_modify(self, target_type: str, name: str, data: Any) -> int:
        """修改意图对象"""
        return 0

    def sys_execute(self, program_id: str, context: dict) -> dict:
        """执行程序"""
        return {}

    def sys_bootstrap(self, action: str, target: str, value: Any) -> bool:
        """Self-Bootstrap 操作"""
        return True


class UserMode:
    """用户空间"""

    def __init__(self, kernel: KernelMode):
        self.kernel = kernel
        self.user_memory: dict[str, Any] = {}

        self.protection_domain = ProtectionDomain(
            level=PrivilegeLevel.USER,
            allowed_syscalls={0, 1, 2, 3, 4, 5, 6},
        )

    def syscall(self, call_id: int, *args) -> Any:
        """发起系统调用"""
        if call_id not in self.protection_domain.allowed_syscalls:
            raise PermissionError(f"用户程序不允许调用 syscall {call_id}")

        return self.kernel.syscall(call_id, args)

    def execute_program(self, program: Any) -> dict:
        """执行程序"""
        return {}


@dataclass
class ProtectionDomain:
    """保护域"""

    level: PrivilegeLevel
    allowed_syscalls: set[int]
    memory_regions: list[MemoryRegion] = field(default_factory=list)


class SecurityChecker:
    """安全检查器"""

    @staticmethod
    def check_syscall_permission(
        caller: PrivilegeLevel,
        syscall_id: int,
    ) -> bool:
        """检查系统调用权限"""
        if caller == PrivilegeLevel.KERNEL:
            return True

        user_allowed = {0, 1, 2, 3, 4, 5, 6}
        return syscall_id in user_allowed

    @staticmethod
    def check_memory_access(
        caller: PrivilegeLevel,
        address: int,
        operation: str,
        regions: list[MemoryRegion],
    ) -> bool:
        """检查内存访问权限"""
        for region in regions:
            if region.contains(address):
                if not region.can_access(operation):
                    return False
                if caller == PrivilegeLevel.USER and region.owner == "kernel":
                    return False
                return True

        return False
