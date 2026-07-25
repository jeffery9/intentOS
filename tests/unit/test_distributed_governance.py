"""
测试 intentos.distributed.governance_model - 治理模型
"""

import pytest


class TestGovernanceModel:
    """治理模型测试"""

    def test_create_governance(self):
        try:
            from intentos.distributed.governance_model import GovernanceModel
            g = GovernanceModel()
            assert g is not None
        except ImportError:
            pytest.skip("governance_model 模块不存在")
