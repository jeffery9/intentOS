"""
测试 intentos.agent.errors - 错误处理系统

覆盖:
- ErrorCode 枚举所有值
- AgentError 数据类 (to_dict, __str__)
- AgentException 基类
- ErrorHandler (should_retry, is_user_error)
- 工厂函数 (create_*_error)
"""

import pytest
from intentos.agent.errors import (
    AgentError,
    AgentException,
    ErrorCode,
    ErrorHandler,
)


class TestErrorCode:
    """错误码枚举测试"""

    def test_success_code(self):
        assert ErrorCode.SUCCESS.value == "SUCCESS_000"

    def test_unknown_error(self):
        assert ErrorCode.UNKNOWN_ERROR.value == "ERR_1000"

    def test_invalid_argument(self):
        assert ErrorCode.INVALID_ARGUMENT.value == "ERR_1001"

    def test_missing_argument(self):
        assert ErrorCode.MISSING_ARGUMENT.value == "ERR_1002"

    def test_timeout(self):
        assert ErrorCode.TIMEOUT.value == "ERR_1003"

    def test_capability_not_found(self):
        assert ErrorCode.CAPABILITY_NOT_FOUND.value == "ERR_2000"

    def test_puf_compile_failed(self):
        assert ErrorCode.PEF_COMPILE_FAILED.value == "ERR_4000"

    def test_mcp_connection_failed(self):
        assert ErrorCode.MCP_CONNECTION_FAILED.value == "ERR_5000"

    def test_skill_not_found(self):
        assert ErrorCode.SKILL_NOT_FOUND.value == "ERR_6000"

    def test_permission_denied(self):
        assert ErrorCode.PERMISSION_DENIED.value == "ERR_7000"

    def test_all_error_codes_have_values(self):
           # All error codes should have non-empty values
        for code in ErrorCode:
            assert code.value is not None and len(code.value) > 0


class TestAgentError:
    """AgentError 数据类测试"""

    def test_create_error(self):
        error = AgentError(
            code=ErrorCode.CAPABILITY_NOT_FOUND,
           )
        assert error.code == ErrorCode.CAPABILITY_NOT_FOUND
        assert error.details is None
        assert error.cause is None

    def test_create_error_with_details(self):
        error = AgentError(
            code=ErrorCode.INVALID_ARGUMENT,
            details={"field": "region"},
           )
        assert error.details == {"field": "region"}

    def test_create_error_with_cause(self):
        error = AgentError(
            code=ErrorCode.CAPABILITY_EXECUTION_FAILED,
            cause=cause,
           )
        assert isinstance(error.cause, ValueError)

    def test_to_dict_basic(self):
        error = AgentError(
            code=ErrorCode.TIMEOUT,
           )
        d = error.to_dict()
        assert d["code"] == "ERR_1003"

    def test_to_dict_with_details_and_cause(self):
        error = AgentError(
            code=ErrorCode.MCP_CONNECTION_FAILED,
            details={"server": "my-server"},
            cause=cause,
           )
        d = error.to_dict()
        assert d["details"] == {"server": "my-server"}

    def test_str_representation(self):
        error = AgentError(
            code=ErrorCode.PERMISSION_DENIED,
           )


class TestAgentException:
    """AgentException 异常类测试"""

    def test_basic_exception(self):
        with pytest.raises(AgentException):
            raise AgentException("test error")

    def test_exception_is_exception_subclass(self):
        assert issubclass(AgentException, Exception)


class TestErrorHandler:
    """错误处理器测试"""

    def test_should_retry_timeout(self):
        assert ErrorHandler.should_retry(error) is True

    def test_should_retry_capability_failed(self):
        assert ErrorHandler.should_retry(error) is True

    def test_should_not_retry_permission_denied(self):
        assert ErrorHandler.should_retry(error) is False

    def test_is_user_error_invalid_argument(self):
        assert ErrorHandler.is_user_error(error) is True

    def test_is_user_error_permission_denied(self):
        assert ErrorHandler.is_user_error(error) is True

    def test_not_user_error_system_timeout(self):
        assert ErrorHandler.is_user_error(error) is False

    def test_retryable_and_user_error_mutually_exclusive(self):
        for code in ErrorCode:
            err = AgentError(code=code, message="test")
            retryable = ErrorHandler.should_retry(err)
            user_error = ErrorHandler.is_user_error(err)
            assert not (retryable and user_error), f"{code} should not be both"


class TestFactoryFunctions:
    """工厂函数测试"""

    def test_create_unknown_error(self):
        from intentos.agent.errors import create_unknown_error
        error = create_unknown_error("unknown issue")
        assert error.code == ErrorCode.UNKNOWN_ERROR

    def test_create_invalid_argument_error(self):
        from intentos.agent.errors import create_invalid_argument_error
        error = create_invalid_argument_error("bad arg")
        assert error.code == ErrorCode.INVALID_ARGUMENT

    def test_create_capability_not_found_error(self):
        from intentos.agent.errors import create_capability_not_found_error
        error = create_capability_not_found_error("query_sales")
        assert error.code == ErrorCode.CAPABILITY_NOT_FOUND

    def test_create_permission_denied_error(self):
        from intentos.agent.errors import create_permission_denied_error
        error = create_permission_denied_error("file:write")
        assert error.code == ErrorCode.PERMISSION_DENIED

    def test_handle_value_error(self):
        result = ErrorHandler.handle_error(ValueError("bad"))
        assert isinstance(result, AgentError)

    def test_handle_key_error(self):
        result = ErrorHandler.handle_error(KeyError("missing"))
        assert isinstance(result, AgentError)
