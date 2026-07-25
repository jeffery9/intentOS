"""
测试 intentos.agent.compiler - 意图编译器 (优化版)

覆盖:
- PEF v1.0 (向后兼容)
- PEF v2.0 转换
- PEFCacheEntry
- PEF.to_dict() / to_v2()
"""

import pytest
from intentos.agent.compiler import PEF, PEFCacheEntry


class TestPEFV1:
    """PEF v1.0 (向后兼容) 测试"""

    def test_default_pef_creation(self):
        pef = PEF()
        assert pef.version == "1.0"
        assert pef.intent == ""
        assert pef.system_prompt == ""
        assert pef.user_prompt == ""
        assert pef.capabilities == []
        assert pef.constraints == {}
        assert pef.metadata == {}
        assert pef.token_count == 0

    def test_pef_with_values(self):
        pef = PEF(
            intent="分析销售数据",
            system_prompt="你是数据分析专家",
            user_prompt="请分析华东区Q3销售",
            capabilities=["query_sales", "analyze_data"],
            constraints={"max_tokens": 1000},
            metadata={"source": "cli"},
        )
        assert pef.intent == "分析销售数据"
        assert "数据分析专家" in pef.system_prompt
        assert len(pef.capabilities) == 2

    def test_pef_to_dict(self):
        pef = PEF(
            intent="test",
            system_prompt="sys",
            user_prompt="usr",
        )
        d = pef.to_dict()
        assert d["version"] == "1.0"
        assert d["intent"] == "test"
        assert d["system_prompt"] == "sys"
        assert d["user_prompt"] == "usr"
        assert d["capabilities"] == []
        assert d["token_count"] == 0

    def test_pef_to_v2(self):
        pef = PEF(
            intent="test",
            system_prompt="sys",
            user_prompt="usr",
        )
        v2 = pef.to_v2()
        assert v2 is not None

    def test_pef_unique_id(self):
        pef1 = PEF(intent="a")
        pef2 = PEF(intent="b")
        assert pef1.id != pef2.id


class TestPEFCacheEntry:
    """PEF 缓存条目测试"""

    def test_cache_entry_creation(self):
        pef = PEF(intent="cached_intent")
        entry = PEFCacheEntry(pef=pef)
        assert entry.pef.intent == "cached_intent"
        assert entry.access_count == 0

    def test_cache_entry_access_count(self):
        pef = PEF(intent="test")
        entry = PEFCacheEntry(pef=pef)
        entry.access_count += 1
        assert entry.access_count == 1
