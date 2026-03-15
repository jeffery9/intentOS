"""
Agent 错误处理

统一错误类型和错误码
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class ErrorCode(Enum):
    """错误码"""
    # 成功
    SUCCESS = "SUCCESS_000"
    
    # 通用错误 (1xxx)
    UNKNOWN_ERROR = "ERR_1000"
    INVALID_ARGUMENT = "ERR_1001"
    MISSING_ARGUMENT = "ERR_1002"
    TIMEOUT = "ERR_1003"
    
    # 能力相关错误 (2xxx)
    CAPABILITY_NOT_FOUND = "ERR_2000"
    CAPABILITY_EXECUTION_FAILED = "ERR_2001"
    CAPABILITY_NOT_REGISTERED = "ERR_2002"
    
    # 意图相关错误 (3xxx)
    INTENT_NOT_UNDERSTOOD = "ERR_3000"
    INTENT_AMBIGUOUS = "ERR_3001"
    INTENT_NO_MATCHING_CAPABILITY = "ERR_3002"
    
    # PEF 相关错误 (4xxx)
    PEF_COMPILE_FAILED = "ERR_4000"
    PEF_EXECUTE_FAILED = "ERR_4001"
    PEF_CACHE_ERROR = "ERR_4002"
    
    # MCP 相关错误 (5xxx)
    MCP_CONNECTION_FAILED = "ERR_5000"
    MCP_TIMEOUT = "ERR_5001"
    MCP_TOOL_NOT_FOUND = "ERR_5002"
    
    # Skill 相关错误 (6xxx)
    SKILL_NOT_FOUND = "ERR_6000"
    SKILL_LOAD_FAILED = "ERR_6001"
    SKILL_EXECUTION_FAILED = "ERR_6002"
    
    # 权限相关错误 (7xxx)
    PERMISSION_DENIED = "ERR_7000"
    AUTHENTICATION_REQUIRED = "ERR_7001"
    AUTHENTICATION_FAILED = "ERR_7002"


@dataclass
class AgentError:
    """Agent 错误"""
    code: ErrorCode
    message: str
    details: Optional[dict[str, Any]] = None
    cause: Optional[Exception] = None
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None,
        }
    
    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"


class AgentException(Exception):
    """Agent 异常"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.cause = cause
        self.error = AgentError(code, message, details, cause)
    
    def to_error(self) -> AgentError:
        """转换为错误对象"""
        return self.error
    
    def __str__(self) -> str:
        return str(self.error)


# ========== 快捷错误创建函数 ==========

def create_unknown_error(message: str, cause: Optional[Exception] = None) -> AgentError:
    """创建未知错误"""
    return AgentError(ErrorCode.UNKNOWN_ERROR, message, cause=cause)

def create_invalid_argument_error(message: str) -> AgentError:
    """创建无效参数错误"""
    return AgentError(ErrorCode.INVALID_ARGUMENT, message)

def create_capability_not_found_error(capability_id: str) -> AgentError:
    """创建能力未找到错误"""
    return AgentError(
        ErrorCode.CAPABILITY_NOT_FOUND,
        f"能力未找到：{capability_id}",
        details={"capability_id": capability_id}
    )

def create_capability_execution_error(
    capability_id: str,
    error: str,
    cause: Optional[Exception] = None
) -> AgentError:
    """创建能力执行错误"""
    return AgentError(
        ErrorCode.CAPABILITY_EXECUTION_FAILED,
        f"能力执行失败：{capability_id} - {error}",
        details={"capability_id": capability_id, "execution_error": error},
        cause=cause
    )

def create_intent_not_understood_error(intent: str) -> AgentError:
    """创建意图未理解错误"""
    return AgentError(
        ErrorCode.INTENT_NOT_UNDERSTOOD,
        f"无法理解意图：{intent}",
        details={"intent": intent}
    )

def create_intent_no_matching_capability_error(intent: str) -> AgentError:
    """创建意图无匹配能力错误"""
    return AgentError(
        ErrorCode.INTENT_NO_MATCHING_CAPABILITY,
        f"没有匹配的能力来处理意图：{intent}",
        details={"intent": intent}
    )

def create_pef_compile_error(message: str, cause: Optional[Exception] = None) -> AgentError:
    """创建 PEF 编译错误"""
    return AgentError(
        ErrorCode.PEF_COMPILE_FAILED,
        f"PEF 编译失败：{message}",
        cause=cause
    )

def create_pef_execute_error(message: str, cause: Optional[Exception] = None) -> AgentError:
    """创建 PEF 执行错误"""
    return AgentError(
        ErrorCode.PEF_EXECUTE_FAILED,
        f"PEF 执行失败：{message}",
        cause=cause
    )

def create_mcp_connection_error(server_name: str, error: str) -> AgentError:
    """创建 MCP 连接错误"""
    return AgentError(
        ErrorCode.MCP_CONNECTION_FAILED,
        f"MCP 服务器连接失败：{server_name} - {error}",
        details={"server_name": server_name, "connection_error": error}
    )

def create_skill_not_found_error(skill_id: str) -> AgentError:
    """创建 Skill 未找到错误"""
    return AgentError(
        ErrorCode.SKILL_NOT_FOUND,
        f"Skill 未找到：{skill_id}",
        details={"skill_id": skill_id}
    )

def create_permission_denied_error(resource: str) -> AgentError:
    """创建权限拒绝错误"""
    return AgentError(
        ErrorCode.PERMISSION_DENIED,
        f"权限不足：{resource}",
        details={"resource": resource}
    )


# ========== 错误处理器 ==========

class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_error(error: Exception) -> AgentError:
        """
        处理错误，转换为统一的 AgentError
        
        Args:
            error: 原始异常
        
        Returns:
            统一的错误对象
        """
        # 如果已经是 AgentException，直接返回
        if isinstance(error, AgentException):
            return error.to_error()
        
        # 根据异常类型转换
        if isinstance(error, ValueError):
            return create_invalid_argument_error(str(error))
        
        if isinstance(error, KeyError):
            return create_capability_not_found_error(str(error))
        
        if isinstance(error, TimeoutError):
            return AgentError(ErrorCode.TIMEOUT, str(error))
        
        # 未知错误
        return create_unknown_error(str(error), cause=error)
    
    @staticmethod
    def should_retry(error: AgentError) -> bool:
        """
        判断是否应该重试
        
        Args:
            error: 错误对象
        
        Returns:
            是否应该重试
        """
        retry_codes = {
            ErrorCode.TIMEOUT,
            ErrorCode.MCP_TIMEOUT,
            ErrorCode.CAPABILITY_EXECUTION_FAILED,
            ErrorCode.PEF_EXECUTE_FAILED,
        }
        return error.code in retry_codes
    
    @staticmethod
    def is_user_error(error: AgentError) -> bool:
        """
        判断是否为用户错误（非系统错误）
        
        Args:
            error: 错误对象
        
        Returns:
            是否为用户错误
        """
        user_error_codes = {
            ErrorCode.INVALID_ARGUMENT,
            ErrorCode.MISSING_ARGUMENT,
            ErrorCode.PERMISSION_DENIED,
            ErrorCode.AUTHENTICATION_REQUIRED,
            ErrorCode.AUTHENTICATION_FAILED,
        }
        return error.code in user_error_codes
