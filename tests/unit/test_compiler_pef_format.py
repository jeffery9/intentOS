"""
测试 intentos.compiler.pef_format - PEF v2.0 格式

覆盖:
- PEF v2.0 创建和属性
- from_v1() 转换
- to_dict / from_dict
"""

import pytest


class TestPEFv2:
    """PEF v2.0 测试"""

    def test_create_pef_v2(self):
        from intentos.compiler.pef_format import PEF
        pef = PEF(
            name="销售数据分析",
            description="分析指定区域和时间的销售数据",
            system_prompt="你是数据分析专家",
            user_prompt="请分析华东区Q3的销售情况",
          )
        assert pef.name == "销售数据分析"

    def test_from_v1_conversion(self):
        from intentos.agent.compiler import PEF as PEFv1
        from intentos.compiler.pef_format import PEF as PEFv2
        v1 = PEFv1(
            intent="测试意图",
            system_prompt="系统提示",
            user_prompt="用户提示",
            capabilities=["cap_a"],
          )
        v2 = PEFv2.from_v1(v1)
        assert v2 is not None

    def test_to_dict(self):
        from intentos.compiler.pef_format import PEF
        pef = PEF(name="测试", description="描述")
        d = pef.to_dict()
        assert isinstance(d, dict)
        assert "name" in d

    def test_from_dict(self):
        from intentos.compiler.pef_format import PEF
        data = {"name": "从字典创建", "description": "测试描述"}
        pef = PEF.from_dict(data)
        assert pef.name == "从字典创建"
