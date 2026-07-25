"""
测试 intentos.bootstrap.self_reproduction - 自我繁殖模块

覆盖:
- CostEstimates (成本常量)
- SecurityConfig (安全配置)
"""

import pytest


class TestCostEstimates:
    """成本估算常量测试"""

    def test_base_costs(self):
        from intentos.bootstrap.self_reproduction import CostEstimates
        assert CostEstimates.CLONE_BASE == 50.0
        assert CostEstimates.FORK_BASE == 30.0
        assert CostEstimates.EVOLVE_BASE == 100.0

    def test_per_resource_costs(self):
        from intentos.bootstrap.self_reproduction import CostEstimates
        assert CostEstimates.PER_CONTAINER == 10.0
        assert CostEstimates.PER_VPC == 20.0
        assert CostEstimates.PER_REDIS == 15.0

    def test_region_multipliers(self):
        from intentos.bootstrap.self_reproduction import CostEstimates
        multipliers = CostEstimates.REGION_MULTIPLIERS
        assert "us-east-1" in multipliers
        assert multipliers["us-east-1"] == 1.0
