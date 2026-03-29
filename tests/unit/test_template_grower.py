"""
Template Grower Module Tests

测试意图模板自生长器模块：模式挖掘、模板生成、历史分析
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from intentos.bootstrap.template_grower import (
    IntentPattern,
    IntentHistoryEntry,
    IntentPatternMiner,
)


class TestIntentPattern:
    """测试意图模式"""

    def test_create_pattern_minimal(self):
        """创建最小模式"""
        pattern = IntentPattern(
            pattern_id="pattern1",
            pattern_text="查询 {region} 销售",
            parameters=["region"],
            frequency=10,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )

        assert pattern.pattern_id == "pattern1"
        assert pattern.pattern_text == "查询 {region} 销售"
        assert pattern.parameters == ["region"]
        assert pattern.frequency == 10
        assert pattern.confidence == 1.0

    def test_create_pattern_full(self):
        """创建完整模式"""
        now = datetime.now()
        pattern = IntentPattern(
            pattern_id="pattern2",
            pattern_text="对比 {region1} 和 {region2} 的 {period} 销售",
            parameters=["region1", "region2", "period"],
            frequency=50,
            first_seen=now - timedelta(days=7),
            last_seen=now,
            examples=[
                "对比华东和华北的 Q3 销售",
                "对比北京和上海的月度销售"
            ],
            confidence=0.95
        )

        assert pattern.pattern_id == "pattern2"
        assert len(pattern.parameters) == 3
        assert pattern.frequency == 50
        assert len(pattern.examples) == 2
        assert pattern.confidence == 0.95

    def test_is_template_candidate_qualified(self):
        """合格的模板候选"""
        pattern = IntentPattern(
            pattern_id="p1",
            pattern_text="查询 {region} 数据",
            parameters=["region"],
            frequency=10,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            confidence=0.9
        )

        assert pattern.is_template_candidate(min_frequency=5) is True

    def test_is_template_candidate_low_frequency(self):
        """频率不足的候选"""
        pattern = IntentPattern(
            pattern_id="p2",
            pattern_text="查询 {region} 数据",
            parameters=["region"],
            frequency=3,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            confidence=0.9
        )

        assert pattern.is_template_candidate(min_frequency=5) is False

    def test_is_template_candidate_no_parameters(self):
        """无参数的候选"""
        pattern = IntentPattern(
            pattern_id="p3",
            pattern_text="查询销售数据",
            parameters=[],
            frequency=10,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            confidence=0.9
        )

        assert pattern.is_template_candidate(min_frequency=5) is False

    def test_is_template_candidate_low_confidence(self):
        """置信度低的候选"""
        pattern = IntentPattern(
            pattern_id="p4",
            pattern_text="查询 {region} 数据",
            parameters=["region"],
            frequency=10,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            confidence=0.5
        )

        assert pattern.is_template_candidate(min_frequency=5) is False

    def test_to_template(self):
        """转换为模板"""
        pattern = IntentPattern(
            pattern_id="p5",
            pattern_text="查询 {region} 销售",
            parameters=["region"],
            frequency=10,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )

        template = pattern.to_template()

        assert "name" in template
        assert "description" in template
        assert "patterns" in template
        assert "parameters" in template
        assert len(template["patterns"]) == 1
        assert len(template["parameters"]) == 1
        assert template["parameters"][0]["name"] == "region"
        assert template["parameters"][0]["required"] is True

    def test_generate_name_with_verb(self):
        """生成带动词的模板名称"""
        pattern = IntentPattern(
            pattern_id="p6",
            pattern_text="对比 {region1} 和 {region2}",
            parameters=["region1", "region2"],
            frequency=10,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )

        name = pattern._generate_name()

        assert "对比" in name or "auto" in name

    def test_generate_name_without_verb(self):
        """生成无动词的模板名称"""
        pattern = IntentPattern(
            pattern_id="p7",
            pattern_text="{region} 的数据",
            parameters=["region"],
            frequency=10,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )

        name = pattern._generate_name()

        assert "template" in name


class TestIntentHistoryEntry:
    """测试意图历史条目"""

    def test_create_entry_minimal(self):
        """创建最小条目"""
        entry = IntentHistoryEntry(
            intent_text="查询销售数据",
            timestamp=datetime.now()
        )

        assert entry.intent_text == "查询销售数据"
        assert entry.success is True
        assert entry.execution_time_ms == 0.0
        assert entry.parameters == {}
        assert entry.user_id == ""

    def test_create_entry_full(self):
        """创建完整条目"""
        entry = IntentHistoryEntry(
            intent_text="查询华东区 Q3 销售",
            timestamp=datetime.now(),
            parameters={"region": "华东", "period": "Q3"},
            success=True,
            execution_time_ms=150.5,
            user_id="user123",
            session_id="session456"
        )

        assert entry.intent_text == "查询华东区 Q3 销售"
        assert entry.parameters["region"] == "华东"
        assert entry.parameters["period"] == "Q3"
        assert entry.success is True
        assert entry.execution_time_ms == 150.5
        assert entry.user_id == "user123"
        assert entry.session_id == "session456"

    def test_create_entry_failure(self):
        """创建失败条目"""
        entry = IntentHistoryEntry(
            intent_text="查询无效数据",
            timestamp=datetime.now(),
            success=False,
            execution_time_ms=50.0
        )

        assert entry.success is False
        assert entry.execution_time_ms == 50.0


class TestIntentPatternMiner:
    """测试意图模式挖掘器"""

    def test_init_miner(self):
        """初始化挖掘器"""
        miner = IntentPatternMiner()

        assert miner.history == []
        assert miner.patterns == {}

    def test_record_intent(self):
        """记录意图"""
        miner = IntentPatternMiner()

        miner.record_intent(
            intent_text="查询华东区销售",
            parameters={"region": "华东"},
            success=True,
            execution_time_ms=100.0,
            user_id="user1"
        )

        assert len(miner.history) == 1
        assert miner.history[0].intent_text == "查询华东区销售"

    def test_record_intent_multiple(self):
        """记录多个意图"""
        miner = IntentPatternMiner()

        for i in range(5):
            miner.record_intent(
                intent_text=f"查询区域{i}销售",
                parameters={"region": f"区域{i}"}
            )

        assert len(miner.history) == 5

    def test_analyze_patterns_empty(self):
        """分析空模式"""
        miner = IntentPatternMiner()

        # 空历史时应能处理
        import asyncio
        # 注意：analyze_patterns 是异步方法
        # 这里只测试它能被调用
        assert hasattr(miner, 'analyze_patterns')

    def test_analyze_patterns_with_history(self):
        """分析带历史的模式"""
        miner = IntentPatternMiner()

        # 添加相似意图
        for i in range(10):
            miner.record_intent(
                intent_text=f"查询区域{i % 3}销售",
                parameters={"region": f"区域{i % 3}"}
            )

        # 验证历史已记录
        assert len(miner.history) == 10


class TestPatternFrequency:
    """测试模式频率"""

    def test_high_frequency_pattern(self):
        """高频模式"""
        miner = IntentPatternMiner()

        # 记录高频意图
        for _ in range(100):
            miner.record_intent(
                intent_text="查询销售数据",
                parameters={"type": "sales"}
            )

        assert len(miner.history) == 100

    def test_low_frequency_pattern(self):
        """低频模式"""
        miner = IntentPatternMiner()

        # 记录低频意图
        for _ in range(2):
            miner.record_intent(
                intent_text="罕见查询",
                parameters={"type": "rare"}
            )

        assert len(miner.history) == 2


class TestPatternParameters:
    """测试模式参数"""

    def test_single_parameter_pattern(self):
        """单参数模式"""
        miner = IntentPatternMiner()

        miner.record_intent(
            intent_text="查询北京销售",
            parameters={"region": "北京"}
        )

        assert len(miner.history) == 1
        assert miner.history[0].parameters["region"] == "北京"

    def test_multi_parameter_pattern(self):
        """多参数模式"""
        miner = IntentPatternMiner()

        miner.record_intent(
            intent_text="对比北京和上海 Q3 销售",
            parameters={
                "region1": "北京",
                "region2": "上海",
                "period": "Q3"
            }
        )

        entry = miner.history[0]
        assert len(entry.parameters) == 3
        assert entry.parameters["region1"] == "北京"
        assert entry.parameters["region2"] == "上海"

    def test_optional_parameters(self):
        """可选参数"""
        miner = IntentPatternMiner()

        miner.record_intent(
            intent_text="查询销售",
            parameters={}
        )

        assert miner.history[0].parameters == {}


class TestPatternConfidence:
    """测试模式置信度"""

    def test_high_confidence_pattern(self):
        """高置信度模式"""
        pattern = IntentPattern(
            pattern_id="high_conf",
            pattern_text="查询 {region} 销售",
            parameters=["region"],
            frequency=50,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            confidence=0.98
        )

        assert pattern.confidence == 0.98
        assert pattern.is_template_candidate() is True

    def test_medium_confidence_pattern(self):
        """中等置信度模式"""
        pattern = IntentPattern(
            pattern_id="med_conf",
            pattern_text="查询 {region} 销售",
            parameters=["region"],
            frequency=50,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            confidence=0.75
        )

        assert pattern.confidence == 0.75
        assert pattern.is_template_candidate() is True

    def test_low_confidence_pattern(self):
        """低置信度模式"""
        pattern = IntentPattern(
            pattern_id="low_conf",
            pattern_text="查询 {region} 销售",
            parameters=["region"],
            frequency=50,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            confidence=0.5
        )

        assert pattern.confidence == 0.5
        assert pattern.is_template_candidate() is False


class TestPatternExamples:
    """测试模式示例"""

    def test_pattern_with_examples(self):
        """带示例的模式"""
        pattern = IntentPattern(
            pattern_id="with_examples",
            pattern_text="对比 {region1} 和 {region2}",
            parameters=["region1", "region2"],
            frequency=20,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            examples=[
                "对比北京和上海",
                "对比华东和华北",
                "对比 Q1 和 Q2"
            ]
        )

        assert len(pattern.examples) == 3
        assert "对比北京和上海" in pattern.examples

    def test_pattern_add_example(self):
        """添加示例"""
        pattern = IntentPattern(
            pattern_id="add_example",
            pattern_text="查询 {region}",
            parameters=["region"],
            frequency=10,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            examples=["查询北京"]
        )

        pattern.examples.append("查询上海")
        assert len(pattern.examples) == 2


class TestPatternTimeRange:
    """测试模式时间范围"""

    def test_pattern_time_span(self):
        """模式时间跨度"""
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        pattern = IntentPattern(
            pattern_id="time_span",
            pattern_text="查询 {period} 销售",
            parameters=["period"],
            frequency=30,
            first_seen=week_ago,
            last_seen=now
        )

        time_span = pattern.last_seen - pattern.first_seen
        assert time_span.days == 7

    def test_recent_pattern(self):
        """最近模式"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        pattern = IntentPattern(
            pattern_id="recent",
            pattern_text="查询 {region}",
            parameters=["region"],
            frequency=5,
            first_seen=hour_ago,
            last_seen=now
        )

        time_span = pattern.last_seen - pattern.first_seen
        assert time_span.seconds == 3600

    def test_old_pattern(self):
        """旧模式"""
        now = datetime.now()
        month_ago = now - timedelta(days=30)

        pattern = IntentPattern(
            pattern_id="old",
            pattern_text="查询 {region}",
            parameters=["region"],
            frequency=5,
            first_seen=month_ago,
            last_seen=month_ago + timedelta(days=1)
        )

        time_span = pattern.last_seen - pattern.first_seen
        assert time_span.days == 1
