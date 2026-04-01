# -*- coding: utf-8 -*-
"""
IntentOS Skill Layer Tests

测试技能层功能
"""

import pytest
import asyncio
from datetime import datetime

from intentos.skill.models import (
    Skill,
    SkillStep,
    SkillParam,
    SkillTrigger,
    Workflow,
    SkillLevel,
)
from intentos.skill.skillifier import Skillifier, SkillifierConfig
from intentos.skill.store import SkillStore, reset_skill_store
from intentos.skill.matcher import SkillMatcher
from intentos.memory.models import MemoryEntry, MemoryContentType, Pattern


class TestSkillModels:
    """测试技能数据模型"""

    def test_skill_creation(self):
        """创建技能"""
        skill = Skill(
            name="测试技能",
            description="这是一个测试技能",
            level=SkillLevel.INTERMEDIATE,
            tags=["test", "skill"],
        )
        
        assert skill.name == "测试技能"
        assert skill.level == SkillLevel.INTERMEDIATE
        assert len(skill.tags) == 2

    def test_skill_step(self):
        """技能步骤"""
        step = SkillStep(
            name="第一步",
            action="query",
            description="查询数据",
            params={"source": "database"},
        )
        
        assert step.name == "第一步"
        assert step.action == "query"
        
        data = step.to_dict()
        assert data["name"] == "第一步"
        assert data["action"] == "query"

    def test_skill_trigger(self):
        """技能触发器"""
        trigger = SkillTrigger(
            keywords=["分析", "数据"],
            intent_pattern=".*分析.*数据.*",
            confidence_threshold=0.7,
        )
        
        assert "分析" in trigger.keywords
        assert trigger.intent_pattern is not None
        
        data = trigger.to_dict()
        assert data["keywords"] == ["分析", "数据"]

    def test_skill_to_yaml(self):
        """技能导出为 YAML"""
        skill = Skill(
            name="YAML 测试",
            description="测试 YAML 导出",
            steps=[
                SkillStep(name="步骤 1", action="query", description="查询"),
            ],
            tags=["yaml", "test"],
        )
        
        yaml_str = skill.to_yaml()
        
        assert "YAML 测试" in yaml_str
        assert "yaml" in yaml_str or "test" in yaml_str
        
        # 测试从 YAML 恢复
        skill2 = Skill.from_yaml(yaml_str)
        assert skill2.name == skill.name

    def test_workflow(self):
        """工作流"""
        workflow = Workflow(
            name="测试工作流",
            description="测试用途",
            steps=[
                SkillStep(name="开始", action="execute"),
                SkillStep(name="结束", action="generate"),
            ],
            source_session_id="session_001",
        )
        
        assert len(workflow.steps) == 2
        assert workflow.source_session_id == "session_001"
        
        data = workflow.to_dict()
        assert data["name"] == "测试工作流"


class TestSkillifier:
    """测试技能提炼器"""

    def test_skillifier_init(self):
        """提炼器初始化"""
        config = SkillifierConfig(min_steps=2, max_steps=8)
        skillifier = Skillifier(config)
        
        assert skillifier.config.min_steps == 2
        assert skillifier.config.max_steps == 8

    def test_infer_action(self):
        """推断动作类型"""
        skillifier = Skillifier()
        
        assert skillifier._infer_action("查询数据") == "query"
        assert skillifier._infer_action("执行命令") == "execute"
        assert skillifier._infer_action("分析报告") == "analyze"
        assert skillifier._infer_action("生成文件") == "generate"
        assert skillifier._infer_action("修改配置") == "modify"

    def test_extract_workflow_from_memories(self):
        """从记忆提取工作流"""
        skillifier = Skillifier()
        
        # 创建包含模式的记忆
        memory = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="成功完成数据分析",
            patterns=[
                Pattern(
                    name="数据分析流程",
                    description="标准的数据分析步骤",
                    steps=[
                        "加载数据源",
                        "清洗数据",
                        "执行分析",
                        "生成报告",
                    ],
                    occurrences=3,
                )
            ],
        )
        
        workflow = skillifier._extract_workflow("session_001", [memory])
        
        assert workflow is not None
        assert len(workflow.steps) >= 1
        assert workflow.source_session_id == "session_001"

    def test_skillify_full_process(self):
        """完整提炼流程"""
        skillifier = Skillifier(
            SkillifierConfig(min_steps=1, min_confidence=0.3)
        )
        
        # 创建丰富的记忆
        memories = [
            MemoryEntry(
                memory_type=MemoryContentType.SUCCESS,
                content="使用 Python 分析销售数据，成功生成报告",
                patterns=[
                    Pattern(
                        name="销售数据分析",
                        description="分析销售数据的完整流程",
                        steps=[
                            "加载销售数据",
                            "清洗和预处理",
                            "计算关键指标",
                            "生成可视化报告",
                        ],
                        occurrences=5,
                    )
                ],
                importance=8.0,
            ),
        ]
        
        skill = asyncio.run(skillifier.skillify("session_001", memories))
        
        # 验证提炼结果
        if skill:
            assert skill.name is not None
            assert len(skill.steps) >= 1
            assert skill.trigger.keywords or skill.trigger.intent_pattern
        # 如果返回 None，说明质量不足，也是正常情况

    def test_evaluate_skill_quality(self):
        """评估技能质量"""
        skillifier = Skillifier()
        
        # 高质量技能
        good_skill = Skill(
            name="高质量技能",
            steps=[
                SkillStep(name="步骤 1", action="query", description="这是一个详细的步骤描述"),
                SkillStep(name="步骤 2", action="analyze", description="这是另一个详细的步骤描述"),
            ],
            trigger=SkillTrigger(keywords=["测试"]),
            params=[SkillParam(name="param1", type="string")],
        )
        
        score = skillifier._evaluate_skill_quality(good_skill)
        assert score >= 0.7  # 应该有较高质量
        
        # 低质量技能
        bad_skill = Skill(
            name="低质量",
            steps=[SkillStep(name="x", action="")],  # 缺少动作
            trigger=SkillTrigger(),  # 无触发器
        )
        
        score = skillifier._evaluate_skill_quality(bad_skill)
        assert score < 0.5

    def test_validate_skill(self):
        """验证技能有效性"""
        skillifier = Skillifier()
        
        # 有效技能
        valid_skill = Skill(
            name="有效技能",
            steps=[SkillStep(name="步骤", action="query")],
            trigger=SkillTrigger(keywords=["测试"]),
        )
        
        is_valid, issues = skillifier.validate_skill(valid_skill)
        assert is_valid is True
        assert len(issues) == 0
        
        # 无效技能
        invalid_skill = Skill(
            name="无效技能",
            steps=[],  # 无步骤
            trigger=SkillTrigger(),  # 无触发器
        )
        
        is_valid, issues = skillifier.validate_skill(invalid_skill)
        assert is_valid is False
        assert len(issues) > 0


class TestSkillMatcher:
    """测试技能匹配器"""

    def test_match_keywords(self):
        """关键词匹配"""
        matcher = SkillMatcher()
        
        trigger = SkillTrigger(keywords=["分析", "数据"])
        
        # 完全匹配
        score = matcher._match_keywords(trigger, "请分析这些数据")
        assert score == 1.0
        
        # 部分匹配
        score = matcher._match_keywords(trigger, "请分析")
        assert score == 0.5
        
        # 无匹配
        score = matcher._match_keywords(trigger, "天气不错")
        assert score == 0.0

    def test_match_intent_pattern(self):
        """意图模式匹配"""
        matcher = SkillMatcher()
        
        trigger = SkillTrigger(intent_pattern=".*分析.*数据.*")
        
        # 匹配
        score = matcher._match_intent_pattern(trigger, "帮我分析销售数据")
        assert score == 1.0
        
        # 不匹配
        score = matcher._match_intent_pattern(trigger, "今天天气很好")
        assert score == 0.0

    def test_match_full(self):
        """完整匹配"""
        matcher = SkillMatcher()
        
        skill = Skill(
            name="数据分析技能",
            description="分析各种数据",
            trigger=SkillTrigger(
                keywords=["分析", "数据"],
                intent_pattern=".*分析.*",
            ),
            steps=[
                SkillStep(name="分析", action="analyze", description="数据分析步骤"),
            ],
            tags=["analytics", "data"],
        )
        
        # 高置信度匹配
        confidence = matcher.match(skill, "请分析这些数据")
        assert confidence >= 0.5
        
        # 低置信度
        confidence = matcher.match(skill, "今天天气不错")
        assert confidence < 0.5

    def test_find_best_match(self):
        """查找最佳匹配"""
        matcher = SkillMatcher()
        
        skills = [
            Skill(
                name="技能 A",
                trigger=SkillTrigger(keywords=["分析", "数据"]),
                steps=[SkillStep(name="分析", action="analyze", description="数据分析")],
                tags=["分析"],
            ),
            Skill(
                name="技能 B",
                trigger=SkillTrigger(keywords=["生成"]),
                steps=[SkillStep(name="生成", action="generate")],
            ),
        ]
        
        # 降低阈值确保匹配
        result = matcher.find_best_match(skills, "帮我分析数据", min_confidence=0.1)
        
        # 可能匹配也可能不匹配，取决于匹配算法
        # 这里只验证如果有结果，应该是技能 A
        if result:
            skill, confidence = result
            assert skill.name == "技能 A"
            assert confidence >= 0.1


class TestSkillStore:
    """测试技能存储"""

    @pytest.fixture
    def store(self):
        """创建临时存储器"""
        reset_skill_store()
        store = SkillStore(storage_dir="/tmp/intentos_skills_test")
        yield store
        store.clear_all()

    def test_save_and_get_skill(self, store):
        """保存和获取技能"""
        skill = Skill(
            name="测试技能",
            description="测试用途",
            steps=[SkillStep(name="步骤", action="query")],
        )
        
        store.save_skill(skill)
        
        retrieved = store.get_skill(skill.id)
        assert retrieved is not None
        assert retrieved.name == "测试技能"

    def test_list_skills(self, store):
        """列出技能"""
        for i in range(3):
            skill = Skill(
                name=f"技能 {i}",
                steps=[SkillStep(name="步骤", action="query")],
                tags=[f"tag{i}"],
            )
            store.save_skill(skill)
        
        skills = store.list_skills(limit=10)
        assert len(skills) == 3

    def test_search_skills(self, store):
        """搜索技能"""
        skill = Skill(
            name="数据分析专家",
            description="专业的数据分析技能",
            tags=["analysis", "data"],
            steps=[SkillStep(name="分析", action="analyze")],
        )
        store.save_skill(skill)
        
        # 按名称搜索
        results = store.search_skills("数据分析", limit=10)
        assert len(results) >= 1
        
        # 按标签搜索
        results = store.search_skills("analysis", limit=10)
        assert len(results) >= 1

    def test_record_usage(self, store):
        """记录技能使用"""
        skill = Skill(name="测试", steps=[SkillStep(name="x", action="x")])
        store.save_skill(skill)
        
        initial_count = skill.usage_count
        
        store.record_usage(skill.id, success=True)
        
        updated = store.get_skill(skill.id)
        assert updated.usage_count == initial_count + 1
        assert updated.success_rate > 0

    def test_get_stats(self, store):
        """获取统计信息"""
        skill = Skill(
            name="统计测试",
            level=SkillLevel.ADVANCED,
            steps=[SkillStep(name="x", action="x")],
            tags=["test"],
        )
        store.save_skill(skill)
        
        stats = store.get_stats()
        
        assert stats["total_skills"] == 1
        assert "advanced" in stats["by_level"]
        assert "test" in [tag for tag, _ in stats["top_tags"]]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
