"""
Kernel Watchdog Module Tests

测试语义自愈监视器的健康检查和自愈功能
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from intentos.kernel.watchdog import HealthStatus


class TestHealthStatus:
    """测试健康状态数据类"""

    def test_healthy_status(self):
        """创建健康状态"""
        status = HealthStatus(is_healthy=True)

        assert status.is_healthy is True
        assert isinstance(status.last_check, datetime)
        assert status.issues == []
        assert status.metrics == {}

    def test_unhealthy_status_with_issues(self):
        """创建不健康状态"""
        status = HealthStatus(
            is_healthy=False,
            issues=["issue1", "issue2"],
            metrics={"cpu": 0.9}
        )

        assert status.is_healthy is False
        assert len(status.issues) == 2
        assert status.metrics["cpu"] == 0.9

    def test_status_default_values(self):
        """测试默认值"""
        status = HealthStatus(is_healthy=True)
        
        assert status.last_check is not None
        assert len(status.issues) == 0
        assert len(status.metrics) == 0


class TestWatchdogHealthStatusDataclass:
    """测试健康状态数据类功能"""

    def test_status_with_empty_issues(self):
        """空问题列表"""
        status = HealthStatus(is_healthy=True, issues=[])
        assert status.issues == []

    def test_status_with_multiple_issues(self):
        """多个问题"""
        status = HealthStatus(
            is_healthy=False,
            issues=["issue1", "issue2", "issue3"],
            metrics={"cpu": 0.9, "memory": 0.8}
        )
        
        assert len(status.issues) == 3
        assert "issue1" in status.issues
        assert "issue2" in status.issues
        assert "issue3" in status.issues

    def test_status_metrics(self):
        """多个指标"""
        status = HealthStatus(
            is_healthy=True,
            metrics={"cpu": 0.5, "memory": 0.6, "disk": 0.7}
        )
        
        assert status.metrics["cpu"] == 0.5
        assert status.metrics["memory"] == 0.6
        assert status.metrics["disk"] == 0.7
