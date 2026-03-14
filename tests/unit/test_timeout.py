"""
超时机制测试

测试用例覆盖：
1. 超时配置测试
2. 超时控制器测试
3. 重试机制测试
4. 装饰器测试
"""

import asyncio
import pytest
from intentos.utils.timeout import (
    TimeoutController,
    TimeoutConfig,
    TimeoutLevel,
    TimeoutError,
    timeout_wrapper,
    with_timeout,
)


class TestTimeoutConfig:
    """超时配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = TimeoutConfig.default()
        assert config.instruction_timeout == 60.0
        assert config.program_timeout == 300.0
        assert config.request_timeout == 600.0
        assert config.llm_call_timeout == 30.0
    
    def test_strict_config(self):
        """测试严格配置"""
        config = TimeoutConfig.strict()
        assert config.instruction_timeout == 30.0
        assert config.program_timeout == 120.0
        assert config.llm_call_timeout == 15.0
    
    def test_relaxed_config(self):
        """测试宽松配置"""
        config = TimeoutConfig.relaxed()
        assert config.instruction_timeout == 120.0
        assert config.program_timeout == 600.0
        assert config.llm_call_timeout == 60.0
    
    def test_get_timeout(self):
        """测试获取超时时间"""
        config = TimeoutConfig.default()
        assert config.get_timeout(TimeoutLevel.INSTRUCTION) == 60.0
        assert config.get_timeout(TimeoutLevel.PROGRAM) == 300.0
        assert config.get_timeout(TimeoutLevel.LLM_CALL) == 30.0


class TestTimeoutController:
    """超时控制器测试"""
    
    def test_start_and_elapsed(self):
        """测试开始和经过时间"""
        controller = TimeoutController()
        controller.start()
        
        # 等待一小段时间
        asyncio.run(asyncio.sleep(0.1))
        
        elapsed = controller.get_elapsed()
        assert elapsed >= 0.1
        assert elapsed < 1.0
    
    def test_get_remaining(self):
        """测试剩余时间"""
        config = TimeoutConfig(instruction_timeout=1.0)
        controller = TimeoutController(config)
        controller.start()
        
        remaining = controller.get_remaining(TimeoutLevel.INSTRUCTION)
        assert remaining <= 1.0
        assert remaining > 0.0
    
    def test_check_timeout(self):
        """测试超时检查"""
        config = TimeoutConfig(instruction_timeout=0.1)
        controller = TimeoutController(config)
        controller.start()
        
        # 初始未超时
        assert controller.check_timeout(TimeoutLevel.INSTRUCTION) is False
        
        # 等待后超时
        asyncio.run(asyncio.sleep(0.2))
        assert controller.check_timeout(TimeoutLevel.INSTRUCTION) is True
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_success(self):
        """测试成功执行（未超时）"""
        controller = TimeoutController()
        controller.start()
        
        async def fast_operation():
            await asyncio.sleep(0.1)
            return "done"
        
        result = await controller.execute_with_timeout(
            fast_operation(),
            level=TimeoutLevel.INSTRUCTION,
            operation_name="test_fast",
        )
        assert result == "done"
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_expired(self):
        """测试超时"""
        config = TimeoutConfig(instruction_timeout=0.1)
        controller = TimeoutController(config)
        controller.start()
        
        async def slow_operation():
            await asyncio.sleep(1.0)
            return "done"
        
        with pytest.raises(TimeoutError) as exc_info:
            await controller.execute_with_timeout(
                slow_operation(),
                level=TimeoutLevel.INSTRUCTION,
                operation_name="test_slow",
            )
        assert "超时" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """测试重试成功"""
        config = TimeoutConfig(
            instruction_timeout=0.15,  # 超时时间
            max_retries=3,
            retry_base_delay=0.05,
        )
        controller = TimeoutController(config)
        controller.start()
        
        attempt_count = 0
        
        async def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                await asyncio.sleep(0.2)  # 超时 (> 0.15)
            return "success"
        
        result = await controller.execute_with_retry(
            flaky_operation,
            level=TimeoutLevel.INSTRUCTION,
            operation_name="test_retry",
        )
        assert result == "success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausted(self):
        """测试重试耗尽"""
        config = TimeoutConfig(
            instruction_timeout=0.1,
            max_retries=2,
            retry_base_delay=0.05,
        )
        controller = TimeoutController(config)
        controller.start()
        
        async def always_slow():
            await asyncio.sleep(1.0)
            return "done"
        
        with pytest.raises(TimeoutError):
            await controller.execute_with_retry(
                always_slow,
                level=TimeoutLevel.INSTRUCTION,
                operation_name="test_exhausted",
            )
    
    def test_instruction_count(self):
        """测试指令计数"""
        controller = TimeoutController()
        
        assert controller.get_instruction_count() == 0
        
        controller.increment_instruction_count()
        controller.increment_instruction_count()
        
        assert controller.get_instruction_count() == 2


class TestTimeoutWrapper:
    """超时包装器测试"""
    
    @pytest.mark.asyncio
    async def test_timeout_wrapper_success(self):
        """测试成功执行"""
        async def fast_op():
            await asyncio.sleep(0.1)
            return "ok"
        
        result = await timeout_wrapper(fast_op(), timeout=1.0)
        assert result == "ok"
    
    @pytest.mark.asyncio
    async def test_timeout_wrapper_expired(self):
        """测试超时"""
        async def slow_op():
            await asyncio.sleep(1.0)
            return "ok"
        
        with pytest.raises(TimeoutError):
            await timeout_wrapper(slow_op(), timeout=0.1)


class TestTimeoutDecorator:
    """超时装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """测试装饰器成功"""
        @with_timeout(timeout=1.0, operation_name="test")
        async def fast_func():
            await asyncio.sleep(0.1)
            return "ok"
        
        result = await fast_func()
        assert result == "ok"
    
    @pytest.mark.asyncio
    async def test_decorator_timeout(self):
        """测试装饰器超时"""
        @with_timeout(timeout=0.1, operation_name="test")
        async def slow_func():
            await asyncio.sleep(1.0)
            return "ok"
        
        with pytest.raises(TimeoutError):
            await slow_func()
    
    @pytest.mark.asyncio
    async def test_decorator_with_function_name(self):
        """测试装饰器使用函数名"""
        @with_timeout(timeout=0.1)  # 不指定 operation_name
        async def my_func():
            await asyncio.sleep(1.0)
            return "ok"
        
        with pytest.raises(TimeoutError) as exc_info:
            await my_func()
        
        # 错误信息应包含函数名
        assert "my_func" in str(exc_info.value)


class TestTimeoutIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_nested_timeout_levels(self):
        """测试嵌套超时级别"""
        config = TimeoutConfig(
            instruction_timeout=0.5,
            program_timeout=1.0,
        )
        controller = TimeoutController(config)
        controller.start()
        
        async def inner_operation():
            await asyncio.sleep(0.2)
            return "inner done"
        
        async def outer_operation():
            # 指令级超时
            result = await controller.execute_with_timeout(
                inner_operation(),
                level=TimeoutLevel.INSTRUCTION,
            )
            return result
        
        # 程序级超时内执行
        result = await controller.execute_with_timeout(
            outer_operation(),
            level=TimeoutLevel.PROGRAM,
        )
        assert result == "inner done"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作"""
        controller = TimeoutController()
        controller.start()
        
        async def task(i: int):
            await asyncio.sleep(0.1 * i)
            return f"task {i} done"
        
        # 并发执行多个任务
        tasks = [
            controller.execute_with_timeout(
                task(i),
                level=TimeoutLevel.INSTRUCTION,
                operation_name=f"task_{i}",
            )
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert results[0] == "task 0 done"
        assert results[4] == "task 4 done"
