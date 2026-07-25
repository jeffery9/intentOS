"""
测试 intentos.distributed.cost_monitor - 云成本监控
"""

import pytest


class TestCostMonitorInit:
    """成本监控初始化测试"""

    def test_default_initialization(self):
        from intentos.distributed.cost_monitor import CostMonitor
        cm = CostMonitor()
        assert cm.provider == "aws"
        assert cm.region == "us-east-1"

    def test_custom_provider_and_region(self):
        from intentos.distributed.cost_monitor import CostMonitor
        cm = CostMonitor(provider="gcp", region="asia-east1")
        assert cm.provider == "gcp"
        assert cm.region == "asia-east1"


class TestBudgetLoading:
    """预算管理测试"""

    def test_load_budget(self):
        from intentos.distributed.cost_monitor import CostMonitor
        cm = CostMonitor()
        cm.load_budget()
        assert cm.budget is not None


class TestCostEstimation:
    """成本估算测试"""

    def test_empty_plan(self):
        from intentos.distributed.cost_monitor import CostMonitor
        cm = CostMonitor()
        result = cm.get_plan_cost_estimate({"actions": []})
        assert result["total_monthly_cost"] == 0.0

    def test_ec2_instance_cost(self):
        from intentos.distributed.cost_monitor import CostMonitor
        cm = CostMonitor()
        plan = {"actions": [
            {"name": "web_server", "type": "compute", "details": {"instance_type": "t3.micro"}}
        ]}
        result = cm.get_plan_cost_estimate(plan)
        expected = round(0.0116 * 24 * 30, 2)
        assert result["total_monthly_cost"] == expected


class TestSpendChecking:
    """支出检查测试"""

    def test_no_budget_returns_true(self):
        from intentos.distributed.cost_monitor import CostMonitor
        cm = CostMonitor()
        result = cm.check_current_spend()
        assert result is True
