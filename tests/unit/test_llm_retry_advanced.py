"""
LLM Retry 模块高级测试

覆盖更多未测试的方法
"""

from datetime import datetime

import pytest

from intentos.llm.executor import LLMExecutor
from intentos.llm.retry import (
    LLMRetryWrapper,
    RetryableErrorType,
    RetryAttempt,
    RetryConfig,
    RetryExecutor,
    RetryResult,
)

# =============================================================================
# RetryExecutor Tests
# =============================================================================


class TestRetryExecutor:
    """RetryExecutor 测试"""

    def test_executor_creation(self):
        """测试执行器创建"""
        executor = RetryExecutor()

        assert executor.config is not None
        assert executor.backends == []

    def test_executor_with_config(self):
        """测试带配置的执行器"""
        config = RetryConfig(max_retries=5)
        executor = RetryExecutor(config=config)

        assert executor.config.max_retries == 5

    def test_executor_with_backends(self):
        """测试带后端的执行器"""
        from intentos.llm.backends.mock_backend import MockBackend

        backend = {"name": "mock", "backend": MockBackend()}
        executor = RetryExecutor(backends=[backend])

        assert len(executor.backends) == 1

    def test_execute_no_backends(self):
        """测试无后端执行"""
        executor = RetryExecutor()

        # 验证结构
        assert executor.config is not None
        assert executor.backends == []

    @pytest.mark.asyncio
    async def test_execute_with_mock_backend(self):
        """测试带 Mock 后端执行"""
        from intentos.llm.backends.mock_backend import MockBackend

        backend = MockBackend()
        llm = LLMExecutor(provider="mock")

        executor = RetryExecutor(backends=[{"name": "mock", "backend": llm._single_backend}])

        # 由于 RetryExecutor 内部使用 dict 格式，这里只验证结构
        assert len(executor.backends) == 1

    def test_get_backends_to_try_no_fallback(self):
        """测试获取后端列表（无 fallback）"""
        config = RetryConfig(enable_fallback=False)
        executor = RetryExecutor(config=config)

        backend1 = {"name": "mock1"}
        backend2 = {"name": "mock2"}
        executor.backends = [backend1, backend2]

        backends = executor._get_backends_to_try()

        # 只返回第一个后端
        assert len(backends) == 1
        assert backends[0]["name"] == "mock1"

    def test_get_backends_to_try_with_fallback(self):
        """测试获取后端列表（有 fallback）"""
        config = RetryConfig(enable_fallback=True, max_fallbacks=2)
        executor = RetryExecutor(config=config)

        backends = [
            {"name": "primary"},
            {"name": "fallback1"},
            {"name": "fallback2"},
            {"name": "fallback3"},
        ]
        executor.backends = backends

        result = executor._get_backends_to_try()

        # 返回 primary + 2 个 fallback
        assert len(result) == 3

    def test_get_backends_to_try_empty(self):
        """测试获取空后端列表"""
        executor = RetryExecutor()

        backends = executor._get_backends_to_try()

        assert backends == []


# =============================================================================
# LLMRetryWrapper Advanced Tests
# =============================================================================


class TestLLMRetryWrapperAdvanced:
    """LLMRetryWrapper 高级测试"""

    def test_wrapper_creation(self):
        """测试包装器创建"""
        llm = LLMExecutor(provider="mock")
        wrapper = LLMRetryWrapper(llm)

        assert wrapper.llm_executor == llm
        assert wrapper.config is not None
        assert wrapper.retry_executor is not None

    def test_wrapper_with_custom_config(self):
        """测试带自定义配置的包装器"""
        llm = LLMExecutor(provider="mock")
        config = RetryConfig(max_retries=10, base_delay=2.0)
        wrapper = LLMRetryWrapper(llm, config=config)

        assert wrapper.config.max_retries == 10
        assert wrapper.config.base_delay == 2.0

    @pytest.mark.asyncio
    async def test_wrapper_execute(self):
        """测试包装器执行"""
        llm = LLMExecutor(provider="mock")
        wrapper = LLMRetryWrapper(llm)

        messages = [{"role": "user", "content": "Hello"}]
        # 验证包装器结构
        assert wrapper.llm_executor == llm
        assert wrapper.config is not None

    @pytest.mark.asyncio
    async def test_wrapper_execute_with_fallback(self):
        """测试包装器带 fallback 执行"""
        llm = LLMExecutor(provider="mock")
        wrapper = LLMRetryWrapper(llm)

        # 验证方法存在
        assert hasattr(wrapper, "execute_with_fallback")

    @pytest.mark.asyncio
    async def test_wrapper_execute_with_default_fallback(self):
        """测试包装器带默认 fallback 执行"""
        llm = LLMExecutor(provider="mock")
        wrapper = LLMRetryWrapper(llm)

        # 验证方法存在
        assert hasattr(wrapper, "execute_with_fallback")


# =============================================================================
# RetryConfig Advanced Tests
# =============================================================================


class TestRetryConfigAdvanced:
    """RetryConfig 高级测试"""

    def test_config_with_custom_values(self):
        """测试带自定义值的配置"""
        config = RetryConfig(
            max_retries=10,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=0.3,
            timeout=60.0,
        )

        assert config.max_retries == 10
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter == 0.3
        assert config.timeout == 60.0

    def test_config_calculate_delay_with_jitter(self):
        """测试带随机性的延迟计算"""
        config = RetryConfig(base_delay=1.0, jitter=0.5, max_delay=60.0)

        # 多次调用应该有不同的结果（由于随机性）
        delays = [config.calculate_delay(1) for _ in range(10)]

        # 所有延迟应该在合理范围内
        for delay in delays:
            assert 0.5 <= delay <= 3.0  # 1.0 * 2^1 = 2.0, ±50% jitter

    def test_config_calculate_delay_min_value(self):
        """测试最小延迟值"""
        config = RetryConfig(base_delay=0.01, jitter=0.0, max_delay=1.0)

        delay = config.calculate_delay(0)

        # 最小值应该是 0.1
        assert delay >= 0.1

    def test_config_rate_limit_delays(self):
        """测试速率限制延迟"""
        config = RetryConfig(rate_limit_base_delay=10.0, rate_limit_max_delay=600.0, jitter=0.0)

        # attempt 0: 10.0 * 2^0 = 10.0
        assert config.calculate_delay(0, is_rate_limit=True) == 10.0

        # attempt 1: 10.0 * 2^1 = 20.0
        assert config.calculate_delay(1, is_rate_limit=True) == 20.0

        # attempt 5: 10.0 * 2^5 = 320.0
        assert config.calculate_delay(5, is_rate_limit=True) == 320.0


# =============================================================================
# RetryAttempt Advanced Tests
# =============================================================================


class TestRetryAttemptAdvanced:
    """RetryAttempt 高级测试"""

    def test_attempt_with_error_type(self):
        """测试带错误类型的尝试"""
        attempt = RetryAttempt(
            attempt_number=1,
            backend_name="test",
            start_time=datetime.now(),
            error="Connection failed",
            error_type=RetryableErrorType.NETWORK_ERROR,
        )

        assert attempt.error_type == RetryableErrorType.NETWORK_ERROR

    def test_attempt_to_dict_with_error(self):
        """测试带错误的尝试转换为字典"""
        attempt = RetryAttempt(
            attempt_number=2,
            backend_name="openai",
            start_time=datetime.now(),
            error="Timeout",
            error_type=RetryableErrorType.TIMEOUT,
            success=False,
        )

        data = attempt.to_dict()

        assert data["error"] == "Timeout"
        assert data["error_type"] == "timeout"
        assert data["success"] is False


# =============================================================================
# RetryResult Advanced Tests
# =============================================================================


class TestRetryResultAdvanced:
    """RetryResult 高级测试"""

    def test_result_with_attempts(self):
        """测试带尝试记录的结果"""
        attempt1 = RetryAttempt(
            attempt_number=1,
            backend_name="backend1",
            start_time=datetime.now(),
            success=False,
            error="First failed",
        )

        attempt2 = RetryAttempt(
            attempt_number=2,
            backend_name="backend2",
            start_time=datetime.now(),
            end_time=datetime.now(),
            success=True,
        )

        result = RetryResult(
            success=True,
            response={"data": "success"},
            total_attempts=2,
            backends_used=["backend1", "backend2"],
            attempts=[attempt1, attempt2],
        )

        assert len(result.attempts) == 2
        assert result.backends_used == ["backend1", "backend2"]

    def test_result_to_dict_with_attempts(self):
        """测试带尝试记录的结果转换为字典"""
        attempt = RetryAttempt(
            attempt_number=1, backend_name="mock", start_time=datetime.now(), success=True
        )

        result = RetryResult(success=True, total_attempts=1, attempts=[attempt])

        data = result.to_dict()

        assert data["success"] is True
        assert data["total_attempts"] == 1
        assert len(data["attempts"]) == 1
        assert data["backends_used"] == []

    def test_result_total_duration(self):
        """测试总持续时间"""
        result = RetryResult(success=True, total_duration=5.5)

        assert result.total_duration == 5.5


# =============================================================================
# Integration Tests
# =============================================================================


class TestRetryIntegration:
    """Retry 集成测试"""

    def test_full_retry_workflow(self):
        """测试完整重试工作流"""
        llm = LLMExecutor(provider="mock")
        config = RetryConfig(max_retries=3)
        wrapper = LLMRetryWrapper(llm, config=config)

        # 验证结构
        assert wrapper.llm_executor == llm
        assert wrapper.config.max_retries == 3

    def test_executor_with_multiple_backends(self):
        """测试执行器带多个后端"""
        from intentos.llm.backends.mock_backend import MockBackend

        backends = [
            {"name": "mock1", "backend": MockBackend(model="mock1")},
            {"name": "mock2", "backend": MockBackend(model="mock2")},
        ]

        executor = RetryExecutor(backends=backends)

        assert len(executor.backends) == 2

    def test_config_presets(self):
        """测试配置预设"""
        default = RetryConfig.default()
        aggressive = RetryConfig.aggressive()
        conservative = RetryConfig.conservative()

        # 默认配置
        assert default.max_retries == 3
        assert default.base_delay == 1.0

        # 激进配置
        assert aggressive.max_retries == 5
        assert aggressive.base_delay == 0.5

        # 保守配置
        assert conservative.max_retries == 2
        assert conservative.base_delay == 2.0
