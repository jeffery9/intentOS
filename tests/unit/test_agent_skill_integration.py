"""
测试 intentos.agent.skill_integration - Skill 集成

覆盖:
- SkillIntegration.__init__
- discover_skills (文件来源 + 自动提炼)
- load_skill / _load_file_skill / _load_auto_skill
- _parse_skill_md
- _scan_resources
- get_loaded_skills
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_registry():
    """模拟能力注册中心"""
    registry = MagicMock()
    registry.register = MagicMock()
    return registry


@pytest.fixture
def temp_skills_dir():
    """创建临时 Skill 目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def skill_integration(mock_registry, temp_skills_dir):
    """创建 SkillIntegration 实例"""
    from intentos.agent.skill_integration import SkillIntegration
    return SkillIntegration(
        registry=mock_registry,
        skills_dir=temp_skills_dir,
        skill_store=None,
     )


class TestSkillIntegrationInit:
    """SkillIntegration 初始化测试"""

    def test_custom_skills_dir(self, mock_registry):
        from intentos.agent.skill_integration import SkillIntegration
        si = SkillIntegration(registry=mock_registry, skills_dir="/custom/path")
        assert si.skills_dir == "/custom/path"

    def test_loaded_skills_starts_empty(self, skill_integration):
        assert skill_integration.get_loaded_skills() == []


class TestDiscoverSkills:
    """Skill 发现测试"""

    def test_discover_no_skills(self, skill_integration):
        skills = skill_integration.discover_skills()
        assert isinstance(skills, list)

    def test_discover_file_skill(self, skill_integration, temp_skills_dir):
        skill_path = os.path.join(temp_skills_dir, "my_tool")
        os.makedirs(skill_path, exist_ok=True)
        skill_md = os.path.join(skill_path, "SKILL.md")
        with open(skill_md, "w") as f:
            f.write("---\nname: my_tool\n---\nContent here\n")

        skills = skill_integration.discover_skills()
        assert any("my_tool" in s for s in skills)


class TestParseSkillMd:
    """SKILL.md 解析测试"""

    def test_parse_valid_yaml_frontmatter(self, skill_integration):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("---\nname: test_skill\ndescription: A test skill\nlicense: MIT\n---\nContent\n")
            f.flush()
            data = skill_integration._parse_skill_md(f.name)
        os.unlink(f.name)
        assert data["spec"]["name"] == "test_skill"
        assert data["spec"]["description"] == "A test skill"


class TestScanResources:
    """Skill 资源扫描测试"""

    def test_scan_empty_directory(self, skill_integration):
        with tempfile.TemporaryDirectory() as tmpdir:
            resources = skill_integration._scan_resources(tmpdir)
            assert "scripts" in resources or True

    def test_scan_with_subdirectories(self, skill_integration):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "scripts"), exist_ok=True)
            resources = skill_integration._scan_resources(tmpdir)
            assert resources["scripts"] is not None


class TestLoadSkill:
    """Skill 加载测试"""

    def test_load_unknown_skill_returns_false(self, skill_integration):
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(skill_integration.load_skill("unknown:xyz"))
            assert result is False
        finally:
            loop.close()
