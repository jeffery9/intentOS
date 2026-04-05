"""
IntentOS Unix 标准 Exit Codes

遵循 Unix 惯例的标准退出码：
- 0: 成功
- 1: 一般错误
- 2: 权限拒绝
- 3: 使用错误（无效输入）
- 4: 资源不可用
- 5: 超时
- 6: 连接失败
- 7: 编译错误
- 8: 执行错误
"""

from enum import IntEnum
from typing import Union


class ExitCode(IntEnum):
    """标准退出码枚举"""

    SUCCESS = 0  # 成功
    GENERAL_ERROR = 1  # 一般错误
    PERMISSION_DENIED = 2  # 权限拒绝
    USAGE_ERROR = 3  # 使用错误（无效输入）
    RESOURCE_UNAVAILABLE = 4  # 资源不可用
    TIMEOUT = 5  # 超时
    CONNECTION_FAILED = 6  # 连接失败
    COMPILE_ERROR = 7  # 编译错误
    EXECUTION_ERROR = 8  # 执行错误
    VALIDATION_ERROR = 9  # 验证错误
    FILE_NOT_FOUND = 10  # 文件未找到


# 退出码描述映射
EXIT_CODE_DESCRIPTIONS = {
    ExitCode.SUCCESS: "成功",
    ExitCode.GENERAL_ERROR: "一般错误",
    ExitCode.PERMISSION_DENIED: "权限拒绝",
    ExitCode.USAGE_ERROR: "使用错误",
    ExitCode.RESOURCE_UNAVAILABLE: "资源不可用",
    ExitCode.TIMEOUT: "超时",
    ExitCode.CONNECTION_FAILED: "连接失败",
    ExitCode.COMPILE_ERROR: "编译错误",
    ExitCode.EXECUTION_ERROR: "执行错误",
    ExitCode.VALIDATION_ERROR: "验证错误",
    ExitCode.FILE_NOT_FOUND: "文件未找到",
}


def get_exit_description(code: Union[ExitCode, int]) -> str:
    """获取退出码描述"""
    exit_code = ExitCode(code) if isinstance(code, int) else code
    return EXIT_CODE_DESCRIPTIONS.get(exit_code, "未知错误")
