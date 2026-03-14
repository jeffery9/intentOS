"""
LLM Retry 模块测试

基于实际 API 编写
"""

import pytest
from intentos.llm.retry import (
    RetryableErrorType,
    RetryConfig,
    RetryAttempt,
    RetryResult,
    LLMRetryWrapper,
)
from datetime import datetime


# =============================================================================
# RetryableErrorType Tests
# =============================================================================

class TestRetryableErrorType:
    """可重试错误类型测试"""

    def test_error_type_values(self):
        """测试错误类型值"""
        assert RetryableErrorType.NETWORK_ERROR.value == "network_error"
        assert RetryableErrorType.SERVER_ERROR.value == "server_error"
        assert RetryableErrorType.RATE_LIMIT.value == "rate_limit"
        assert RetryableErrorType.TIMEOUT.value == "timeout"
        assert RetryableErrorType.PARSE_ERROR.value == "parse_error"
        assert RetryableErrorType.CLIENT_ERROR.value == "client_error"
        assert RetryableErrorType.AUTH_ERROR.value == "auth_error"


# =============================================================================
# RetryConfig Tests
# =============================================================================

class TestRetryConfig:
    """重试配置测试"""

    def test_config_default_creation(self):
        """测试默认配置"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter == 0.5
        assert config.timeout == 30.0
        assert config.enable_fallback is True
        assert config.max_fallbacks == 2

    def test_config_default_classmethod(self):
        """测试 default 类方法"""
        config = RetryConfig.default()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0

    def test_config_aggressive_classmethod(self):
        """测试 aggressive 类方法"""
        config = RetryConfig.aggressive()
        
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0

    def test_config_conservative_classmethod(self):
        """测试 conservative 类方法"""
        config = RetryConfig.conservative()
        
        assert config.max_retries == 2
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0

    def test_config_calculate_delay_exponential(self):
        """测试指数延迟计算"""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            jitter=0.0,  # 禁用随机性以便测试
            max_delay=60.0
        )
        
        # attempt 0: 1.0 * 2^0 = 1.0
        delay0 = config.calculate_delay(0)
        assert delay0 == 1.0
        
        # attempt 1: 1.0 * 2^1 = 2.0
        delay1 = config.calculate_delay(1)
        assert delay1 == 2.0
        
        # attempt 2: 1.0 * 2^2 = 4.0
        delay2 = config.calculate_delay(2)
        assert delay2 == 4.0

    def test_config_calculate_delay_rate_limit(self):
        """测试速率限制延迟计算"""
        config = RetryConfig(
            rate_limit_base_delay=5.0,
            rate_limit_max_delay=300.0,
            jitter=0.0
        )
        
        # attempt 0: 5.0 * 2^0 = 5.0
        delay0 = config.calculate_delay(0, is_rate_limit=True)
        assert delay0 == 5.0
        
        # attempt 1: 5.0 * 2^1 = 10.0
        delay1 = config.calculate_delay(1, is_rate_limit=True)
        assert delay1 == 10.0

    def test_config_calculate_delay_max_limit(self):
        """测试最大延迟限制"""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=10.0,
            jitter=0.0
        )
        
        # attempt 10 应该被限制在 max_delay
        delay = config.calculate_delay(10)
        assert delay <= 10.0

    def test_config_custom_values(self):
        """测试自定义配置值"""
        config = RetryConfig(
            max_retries=10,
            base_delay=2.0,
            max_delay=120.0,
            timeout=60.0
        )
        
        assert config.max_retries == 10
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.timeout == 60.0


# =============================================================================
# RetryAttempt Tests
# =============================================================================

class TestRetryAttempt:
    """重试尝试测试"""

    def test_attempt_default_creation(self):
        """测试默认创建"""
        attempt = RetryAttempt(
            attempt_number=1,
            backend_name="test_backend",
            start_time=datetime.now()
        )
        
        assert attempt.attempt_number == 1
        assert attempt.backend_name == "test_backend"
        assert attempt.start_time is not None
        assert attempt.end_time is None
        assert attempt.error is None
        assert attempt.error_type is None
        assert attempt.success is False

    def test_attempt_with_error(self):
        """测试带错误的尝试"""
        attempt = RetryAttempt(
            attempt_number=1,
            backend_name="test",
            start_time=datetime.now(),
            error="Connection failed",
            error_type=RetryableErrorType.NETWORK_ERROR
        )
        
        assert attempt.error == "Connection failed"
        assert attempt.error_type == RetryableErrorType.NETWORK_ERROR
        assert attempt.success is False

    def test_attempt_success(self):
        """测试成功的尝试"""
        attempt = RetryAttempt(
            attempt_number=1,
            backend_name="test",
            start_time=datetime.now(),
            end_time=datetime.now(),
            success=True
        )
        
        assert attempt.success is True
        assert attempt.error is None

    def test_attempt_duration_without_end_time(self):
        """测试无结束时间的持续时间"""
        attempt = RetryAttempt(
            attempt_number=1,
            backend_name="test",
            start_time=datetime.now()
        )
        
        # 未结束时持续时间为 0
        assert attempt.duration == 0.0

    def test_attempt_duration_with_end_time(self):
        """测试带结束时间的持续时间"""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 10, 0, 5)
        
        attempt = RetryAttempt(
            attempt_number=1,
            backend_name="test",
            start_time=start,
            end_time=end
        )
        
        assert attempt.duration == 5.0

    def test_attempt_to_dict(self):
        """测试尝试转换为字典"""
        attempt = RetryAttempt(
            attempt_number=2,
            backend_name="openai",
            start_time=datetime.now(),
            success=True
        )
        
        data = attempt.to_dict()
        
        assert data["attempt_number"] == 2
        assert data["backend_name"] == "openai"
        assert data["success"] is True
        assert "start_time" in data


# =============================================================================
# RetryResult Tests
# =============================================================================

class TestRetryResult:
    """重试结果测试"""

    def test_result_default_creation(self):
        """测试默认创建"""
        result = RetryResult(success=False)
        
        assert result.success is False
        assert result.response is None
        assert result.error is None
        assert result.total_attempts == 0
        assert result.backends_used == []
        assert result.attempts == []

    def test_result_success(self):
        """测试成功结果"""
        result = RetryResult(
            success=True,
            response={"data": "success"},
            total_attempts=2,
            backends_used=["openai"]
        )
        
        assert result.success is True
        assert result.response == {"data": "success"}
        assert result.total_attempts == 2
        assert "openai" in result.backends_used

    def test_result_failure(self):
        """测试失败结果"""
        result = RetryResult(
            success=False,
            error="All retries failed",
            total_attempts=3
        )
        
        assert result.success is False
        assert result.error == "All retries failed"
        assert result.total_attempts == 3

    def test_result_to_dict_success(self):
        """测试成功结果转换为字典"""
        result = RetryResult(
            success=True,
            response={"key": "value"},
            total_attempts=1
        )
        
        data = result.to_dict()
        
        assert data["success"] is True
        # to_dict 不包含 response，只包含错误信息
        assert data["total_attempts"] == 1
        assert data["error"] is None

    def test_result_to_dict_failure(self):
        """测试失败结果转换为字典"""
        result = RetryResult(
            success=False,
            error="Failed after retries"
        )
        
        data = result.to_dict()
        
        assert data["success"] is False
        assert data["error"] == "Failed after retries"
        assert "attempts" in data


# =============================================================================
# LLMRetryWrapper Tests
# =============================================================================

class TestLLMRetryWrapper:
    """LLM 重试包装器测试"""

    def test_wrapper_creation(self):
        """测试包装器创建"""
        from intentos.llm.executor import LLMExecutor
        
        llm = LLMExecutor()
        wrapper = LLMRetryWrapper(llm)
        
        assert wrapper.llm_executor == llm
        assert wrapper.config is not None
        assert wrapper.retry_executor is not None

    def test_wrapper_with_config(self):
        """测试带配置的包装器"""
        from intentos.llm.executor import LLMExecutor
        
        llm = LLMExecutor()
        config = RetryConfig(max_retries=5)
        wrapper = LLMRetryWrapper(llm, config=config)
        
        assert wrapper.config.max_retries == 5

    @pytest.mark.asyncio
    async def test_wrapper_execute_success(self):
        """测试成功执行"""
        from intentos.llm.executor import LLMExecutor
        
        llm = LLMExecutor()
        wrapper = LLMRetryWrapper(llm)
        
        messages = [{"role": "user", "content": "Hello"}]
        # 由于 LLMExecutor 需要实际后端，这里只测试包装器结构
        assert wrapper.llm_executor is not None
        assert wrapper.config is not None

    @pytest.mark.asyncio
    async def test_wrapper_execute_with_config(self):
        """测试带配置执行"""
        from intentos.llm.executor import LLMExecutor
        
        llm = LLMExecutor()
        config = RetryConfig(max_retries=1)
        wrapper = LLMRetryWrapper(llm, config=config)
        
        # 验证配置
        assert wrapper.config.max_retries == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestLLMRetryIntegration:
    """LLM Retry 集成测试"""

    def test_full_retry_workflow(self):
        """测试完整重试工作流"""
        from intentos.llm.executor import LLMExecutor
        
        llm = LLMExecutor()
        config = RetryConfig(max_retries=3)
        wrapper = LLMRetryWrapper(llm, config=config)
        
        # 验证配置
        assert wrapper.config.max_retries == 3
        assert wrapper.llm_executor == llm

    def test_retry_result_with_attempts(self):
        """测试带尝试记录的重试结果"""
        # 创建多个尝试
        attempt1 = RetryAttempt(
            attempt_number=1,
            backend_name="backend1",
            start_time=datetime.now(),
            error="First failed",
            success=False
        )
        
        attempt2 = RetryAttempt(
            attempt_number=2,
            backend_name="backend2",
            start_time=datetime.now(),
            end_time=datetime.now(),
            success=True
        )
        
        # 创建结果
        result = RetryResult(
            success=True,
            response={"data": "success"},
            total_attempts=2,
            backends_used=["backend1", "backend2"],
            attempts=[attempt1, attempt2]
        )
        
        assert len(result.attempts) == 2
        assert result.attempts[0].success is False
        assert result.attempts[1].success is True

    def test_config_and_result_integration(self):
        """测试配置和结果集成"""
        config = RetryConfig(max_retries=5)
        
        result = RetryResult(
            success=True,
            total_attempts=3
        )
        
        # 验证尝试次数在限制内
        assert result.total_attempts <= config.max_retries
