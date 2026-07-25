# -*- coding: utf-8 -*-
"""
Unit tests for Loop 5: Skill Apoptosis & Meditation Engine
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from intentos.skill import Skill, SkillTrigger
from intentos.meditation import SkillApoptosisEngine, SkillApoptosisResult
from intentos.llm.backends.base import LLMResponse, LLMUsage


@pytest.mark.anyio
async def test_skill_apoptosis_flow():
    # 1. 模拟两个高度重叠的技能 (A 和 B)
    skill_a = Skill(
        id="react_crud_maker",
        name="react_crud_maker",
        description="基于 React 模板创建增删改查前端页面",
        trigger=SkillTrigger(intent_pattern="创建 React CRUD"),
        steps=[],
        tags=["frontend", "react"]
    )
    
    skill_b = Skill(
        id="vue_crud_maker",
        name="vue_crud_maker",
        description="基于 Vue 模板创建增删改查前端页面",
        trigger=SkillTrigger(intent_pattern="创建 Vue CRUD"),
        steps=[],
        tags=["frontend", "vue"]
    )
    
    # 2. Mock 技能存储库 (SkillStore)
    # 通过 side_effect 模拟写盘：第一次返回 A 和 B，冥想删除后返回合并后的新高维技能
    mock_store = MagicMock()
    
    # 构造合并后的新技能，用于 side_effect 返回
    skill_merged = Skill(
        id="skill_apoptosis_12345",
        name="universal_frontend_crud_worker",
        description="融合了 React 和 Vue 模板的高维抽象前端增删改查页面生成技能",
        trigger=SkillTrigger(intent_pattern="在前端框架(React/Vue)中生成增删改查CRUD页面"),
        steps=[],
        tags=["merged", "abstract", "frontend"]
    )
    
    mock_store.list_skills.side_effect = [
        [skill_a, skill_b],  # 第一次扫描
        [skill_merged]       # 冥想修剪后的第二次扫描
    ]
    
    # 3. Mock LLM 执行器
    # 它的第一个回答判断“需要合并”
    # 第二个回答输出合并后的“全新高维技能 JSON”
    mock_executor = AsyncMock()
    
    response_1 = LLMResponse(
        content='{"is_redundant": true, "reason": "两个技能都是前端框架下的 CRUD 页面生成，功能重合度极高，属于低效的特定框架规则，应合并为高维统一的前端 CRUD 生成器。"}',
        model="mock-model",
        usage=LLMUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    )
    
    response_2 = LLMResponse(
        content='''{
            "name": "universal_frontend_crud_worker",
            "description": "融合了 React 和 Vue 模板的高维抽象前端增删改查页面生成技能",
            "level": "user",
            "tags": ["merged", "abstract", "frontend"],
            "trigger": {
                "intent": "在前端框架(React/Vue)中生成增删改查CRUD页面"
            },
            "steps": []
        }''',
        model="mock-model",
        usage=LLMUsage(prompt_tokens=200, completion_tokens=80, total_tokens=280)
    )
    
    mock_executor.execute.side_effect = [response_1, response_2]
    
    # 4. 初始化引擎
    engine = SkillApoptosisEngine(llm_executor=mock_executor, skill_store=mock_store)
    
    # 5. 执行数字冥想，触发细胞凋亡
    result = await engine.run_meditation()
    
    # 6. 深度断言：
    # ① 扫描了 2 个技能
    assert result.total_skills_scanned == 2
    # ② 找到了 1 组冗余对
    assert result.redundant_pairs_found == 1
    # ③ 物理合并了 1 个，凋亡了 2 个
    assert result.skills_merged == 1
    assert result.skills_pruned == 2
    # ④ 检验熵值是否降低
    assert result.final_entropy_score < result.original_entropy_score
    
    # ⑤ 检查物理存储是否发生了原子性的“新旧替换”
    mock_store.save_skill.assert_called_once()
    # 两个低阶旧 Skill 必须被删除（凋亡）
    mock_store.delete_skill.assert_any_call("react_crud_maker")
    mock_store.delete_skill.assert_any_call("vue_crud_maker")
    
    # 获取被注册的高维 Skill 详情并验证
    saved_skill = mock_store.save_skill.call_args[0][0]
    assert saved_skill.name == "universal_frontend_crud_worker"
    assert "merged" in saved_skill.tags
    assert "abstract" in saved_skill.tags
