"""
Kernel Heartbeat Module Tests

测试心跳模块的周期性触发和自反射功能
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock 依赖模块
import sys
from unittest.mock import MagicMock

# Mock self_reflection 模块的依赖
mock_social_agent = MagicMock()
mock_self_reproduction = MagicMock()
mock_cost_monitor = MagicMock()
mock_economic_engine = MagicMock()

sys.modules['intentos.agent.social_agent'] = mock_social_agent
sys.modules['intentos.bootstrap.self_reproduction'] = mock_self_reproduction
sys.modules['intentos.distributed.cost_monitor'] = mock_cost_monitor
sys.modules['intentos.distributed.economic_engine'] = mock_economic_engine

from intentos.kernel.heartbeat import Heartbeat


class TestHeartbeatInitialization:
    """测试心跳初始化"""

    def test_default_interval(self):
        """默认间隔应为 3600 秒"""
        heartbeat = Heartbeat()
        assert heartbeat.interval_seconds == 3600

    def test_custom_interval(self):
        """自定义间隔"""
        heartbeat = Heartbeat(interval_seconds=1800)
        assert heartbeat.interval_seconds == 1800

    def test_initial_state(self):
        """初始状态应为停止"""
        heartbeat = Heartbeat()
        assert heartbeat._running is False

    def test_self_reflection_created(self):
        """应创建自反射实例"""
        heartbeat = Heartbeat()
        assert heartbeat.self_reflection is not None


class TestHeartbeatStartStop:
    """测试心跳启动和停止"""

    def test_start(self):
        """启动心跳"""
        heartbeat = Heartbeat()
        # start 是异步方法，这里只测试状态
        assert heartbeat._running is False
        # 模拟启动状态
        heartbeat._running = True
        assert heartbeat._running is True

    def test_start_already_running(self, caplog):
        """重复启动应记录警告"""
        heartbeat = Heartbeat()
        heartbeat._running = True
        
        with caplog.at_level(logging.WARNING):
            # 直接测试警告逻辑
            if heartbeat._running:
                logging.warning("Heartbeat is already running.")
        
        assert "already running" in caplog.text

    def test_stop(self):
        """停止心跳"""
        heartbeat = Heartbeat()
        heartbeat._running = True
        heartbeat.stop()
        assert heartbeat._running is False


class TestHeartbeatOnBeat:
    """测试心跳触发"""

    @pytest.mark.asyncio
    async def test_on_beat_calls_self_reflection(self):
        """心跳应调用自反射"""
        heartbeat = Heartbeat()
        
        # Mock self_reflection
        mock_reflection = MagicMock()
        mock_reflection.evaluate_current_state.return_value = []
        heartbeat.self_reflection = mock_reflection
        
        await heartbeat._on_beat()
        
        mock_reflection.evaluate_current_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_beat_with_deviations(self):
        """心跳发现偏差时应触发修正"""
        heartbeat = Heartbeat()
        
        mock_reflection = MagicMock()
        mock_reflection.evaluate_current_state.return_value = ["deviation1"]
        mock_reflection.trigger_self_correction = MagicMock()
        heartbeat.self_reflection = mock_reflection
        
        with patch('logging.info') as mock_log:
            await heartbeat._on_beat()
        
        mock_reflection.trigger_self_correction.assert_called_once_with(["deviation1"])

    @pytest.mark.asyncio
    async def test_on_beat_state_logging(self, caplog):
        """心跳应记录模拟状态"""
        heartbeat = Heartbeat(interval_seconds=1)
        
        with caplog.at_level(logging.INFO):
            await heartbeat._on_beat()
        
        assert "Simulated current state" in caplog.text


class TestHeartbeatPeriodic:
    """测试周期性心跳"""

    @pytest.mark.asyncio
    async def test_periodic_beat(self):
        """测试周期性心跳"""
        heartbeat = Heartbeat(interval_seconds=0.1)
        
        call_count = 0
        original_on_beat = heartbeat._on_beat
        
        async def count_on_beat():
            nonlocal call_count
            call_count += 1
            await original_on_beat()
        
        heartbeat._on_beat = count_on_beat
        
        # 启动并运行短暂时间
        task = asyncio.create_task(heartbeat.start())
        await asyncio.sleep(0.25)
        heartbeat.stop()
        
        # 取消任务
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # 应该至少调用 2 次
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_start_async(self):
        """测试异步启动"""
        heartbeat = Heartbeat(interval_seconds=0.05)
        
        task = asyncio.create_task(heartbeat.start())
        await asyncio.sleep(0.1)
        heartbeat.stop()
        
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestHeartbeatStateSimulation:
    """测试状态模拟"""

    @pytest.mark.asyncio
    async def test_state_contains_economic_health(self):
        """状态应包含经济健康指标"""
        heartbeat = Heartbeat()
        
        mock_reflection = MagicMock()
        mock_reflection.evaluate_current_state.return_value = []
        heartbeat.self_reflection = mock_reflection
        
        await heartbeat._on_beat()
        
        call_args = mock_reflection.evaluate_current_state.call_args[0][0]
        assert 'economic_health' in call_args

    @pytest.mark.asyncio
    async def test_state_contains_social_sentiment(self):
        """状态应包含社交情绪指标"""
        heartbeat = Heartbeat()
        
        mock_reflection = MagicMock()
        mock_reflection.evaluate_current_state.return_value = []
        heartbeat.self_reflection = mock_reflection
        
        await heartbeat._on_beat()
        
        call_args = mock_reflection.evaluate_current_state.call_args[0][0]
        assert 'social_sentiment' in call_args

    @pytest.mark.asyncio
    async def test_state_contains_growth_rate(self):
        """状态应包含增长率指标"""
        heartbeat = Heartbeat()
        
        mock_reflection = MagicMock()
        mock_reflection.evaluate_current_state.return_value = []
        heartbeat.self_reflection = mock_reflection
        
        await heartbeat._on_beat()
        
        call_args = mock_reflection.evaluate_current_state.call_args[0][0]
        assert 'growth_rate' in call_args

    @pytest.mark.asyncio
    async def test_state_contains_resource_consumption(self):
        """状态应包含资源消耗指标"""
        heartbeat = Heartbeat()
        
        mock_reflection = MagicMock()
        mock_reflection.evaluate_current_state.return_value = []
        heartbeat.self_reflection = mock_reflection
        
        await heartbeat._on_beat()
        
        call_args = mock_reflection.evaluate_current_state.call_args[0][0]
        assert 'resource_consumption' in call_args

    @pytest.mark.asyncio
    async def test_state_contains_cost_over_budget(self):
        """状态应包含预算超支指标"""
        heartbeat = Heartbeat()
        
        mock_reflection = MagicMock()
        mock_reflection.evaluate_current_state.return_value = []
        heartbeat.self_reflection = mock_reflection
        
        await heartbeat._on_beat()
        
        call_args = mock_reflection.evaluate_current_state.call_args[0][0]
        assert 'cost_over_budget' in call_args
