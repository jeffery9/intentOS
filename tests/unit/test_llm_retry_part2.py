"""
LLM Retry 模块测试 - 第 2 部分
"""

import pytest
from intentos.llm.retry import (
    RetryableErrorType,
    RetryConfig,
    RetryAttempt,
    RetryResult,
    RetryExecutor,
    LLMRetryWrapper,
)
from datetime import datetime


class TestRetryableErrorTypeAdvanced:
    """RetryableErrorType 高级测试"""

    def test_all_error_types(self):
        assert RetryableErrorType.NETWORK_ERROR.value == "network_error"
        assert RetryableErrorType.SERVER_ERROR.value == "server_error"
        assert RetryableErrorType.RATE_LIMIT.value == "rate_limit"
        assert RetryableErrorType.TIMEOUT.value == "timeout"
        assert RetryableErrorType.PARSE_ERROR.value == "parse_error"
        assert RetryableErrorType.CLIENT_ERROR.value == "client_error"
        assert RetryableErrorType.AUTH_ERROR.value == "auth_error"


class TestRetryConfigAdvanced:
    """RetryConfig 高级测试"""

    def test_config_custom_all_values(self):
        config = RetryConfig(
            max_retries=10,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=0.3,
            timeout=60.0,
            enable_fallback=False,
            max_fallbacks=1
        )
        assert config.max_retries == 10
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter == 0.3
        assert config.timeout == 60.0
        assert config.enable_fallback is False
        assert config.max_fallbacks == 1

    def test_config_calculate_delay_with_jitter(self):
        config = RetryConfig(base_delay=1.0, jitter=0.5, max_delay=60.0)
        delays = [config.calculate_delay(1) for _ in range(10)]
        for delay in delays:
            assert 0.5 <= delay <= 3.0

    def test_config_calculate_delay_min_value(self):
        config = RetryConfig(base_delay=0.01, jitter=0.0, max_delay=1.0)
        delay = config.calculate_delay(0)
        assert delay >= 0.1

    def test_config_rate_limit_delays(self):
        config = RetryConfig(rate_limit_base_delay=10.0, rate_limit_max_delay=600.0, jitter=0.0)
        assert config.calculate_delay(0, is_rate_limit=True) == 10.0
        assert config.calculate_delay(1, is_rate_limit=True) == 20.0
        assert config.calculate_delay(5, is_rate_limit=True) == 320.0


class TestRetryAttemptAdvanced:
    """RetryAttempt 高级测试"""

    def test_attempt_with_error_type(self):
        attempt = RetryAttempt(
            attempt_number=1,
            backend_name="test",
            start_time=datetime.now(),
            error="Connection failed",
            error_type=RetryableErrorType.NETWORK_ERROR
        )
        assert attempt.error_type == RetryableErrorType.NETWORK_ERROR

    def test_attempt_to_dict_with_error(self):
        attempt = RetryAttempt(
            attempt_number=2,
            backend_name="openai",
            start_time=datetime.now(),
            error="Timeout",
            error_type=RetryableErrorType.TIMEOUT,
            success=False
        )
        data = attempt.to_dict()
        assert data["error"] == "Timeout"
        assert data["error_type"] == "timeout"
        assert data["success"] is False


class TestRetryResultAdvanced:
    """RetryResult 高级测试"""

    def test_result_with_attempts(self):
        attempt1 = RetryAttempt(
            attempt_number=1,
            backend_name="backend1",
            start_time=datetime.now(),
            success=False,
            error="First failed"
        )
        attempt2 = RetryAttempt(
            attempt_number=2,
            backend_name="backend2",
            start_time=datetime.now(),
            end_time=datetime.now(),
            success=True
        )
        result = RetryResult(
            success=True,
            response={"data": "success"},
            total_attempts=2,
            backends_used=["backend1", "backend2"],
            attempts=[attempt1, attempt2]
        )
        assert len(result.attempts) == 2
        assert result.backends_used == ["backend1", "backend2"]

    def test_result_to_dict_with_attempts(self):
        attempt = RetryAttempt(
            attempt_number=1,
            backend_name="mock",
            start_time=datetime.now(),
            success=True
        )
        result = RetryResult(success=True, total_attempts=1, attempts=[attempt])
        data = result.to_dict()
        assert data["success"] is True
        assert data["total_attempts"] == 1
        assert len(data["attempts"]) == 1
        assert data["backends_used"] == []

    def test_result_total_duration(self):
        result = RetryResult(success=True, total_duration=5.5)
        assert result.total_duration == 5.5


class TestRetryExecutorAdvanced:
    """RetryExecutor 高级测试"""

    def test_executor_with_config(self):
        config = RetryConfig(max_retries=5)
        executor = RetryExecutor(config=config)
        assert executor.config.max_retries == 5

    def test_executor_with_backends(self):
        from intentos.llm.backends.mock_backend import MockBackend
        backend = {"name": "mock", "backend": MockBackend()}
        executor = RetryExecutor(backends=[backend])
        assert len(executor.backends) == 1

    @pytest.mark.asyncio
    async def test_execute_no_backends(self):
        executor = RetryExecutor()
        # 验证结构
        assert executor.config is not None
        assert executor.backends == []

    def test_get_backends_to_try_no_fallback(self):
        config = RetryConfig(enable_fallback=False)
        executor = RetryExecutor(config=config)
        backend1 = {"name": "mock1"}
        backend2 = {"name": "mock2"}
        executor.backends = [backend1, backend2]
        backends = executor._get_backends_to_try()
        assert len(backends) == 1
        assert backends[0]["name"] == "mock1"

    def test_get_backends_to_try_with_fallback(self):
        config = RetryConfig(enable_fallback=True, max_fallbacks=2)
        executor = RetryExecutor(config=config)
        backends = [
            {"name": "primary"},
            {"name": "fallback1"},
            {"name": "fallback2"},
            {"name": "fallback3"}
        ]
        executor.backends = backends
        result = executor._get_backends_to_try()
        assert len(result) == 3

    def test_get_backends_to_try_empty(self):
        executor = RetryExecutor()
        backends = executor._get_backends_to_try()
        assert backends == []


class TestLLMRetryWrapperAdvanced:
    """LLMRetryWrapper 高级测试"""

    def test_wrapper_with_custom_config(self):
        from intentos.llm.executor import LLMExecutor
        llm = LLMExecutor(provider="mock")
        config = RetryConfig(max_retries=10, base_delay=2.0)
        wrapper = LLMRetryWrapper(llm, config=config)
        assert wrapper.config.max_retries == 10
        assert wrapper.config.base_delay == 2.0


class TestRetryIntegration:
    """Retry 集成测试"""

    def test_executor_with_multiple_backends(self):
        from intentos.llm.backends.mock_backend import MockBackend
        backends = [
            {"name": "mock1", "backend": MockBackend(model="mock1")},
            {"name": "mock2", "backend": MockBackend(model="mock2")}
        ]
        executor = RetryExecutor(backends=backends)
        assert len(executor.backends) == 2

    def test_config_presets(self):
        default = RetryConfig.default()
        aggressive = RetryConfig.aggressive()
        conservative = RetryConfig.conservative()
        
        assert default.max_retries == 3
        assert default.base_delay == 1.0
        
        assert aggressive.max_retries == 5
        assert aggressive.base_delay == 0.5
        
        assert conservative.max_retries == 2
        assert conservative.base_delay == 2.0

    def test_full_retry_workflow(self):
        from intentos.llm.executor import LLMExecutor
        llm = LLMExecutor(provider="mock")
        config = RetryConfig(max_retries=3)
        wrapper = LLMRetryWrapper(llm, config=config)
        assert wrapper.llm_executor == llm
        assert wrapper.config.max_retries == 3
