"""
IO 能力层测试

测试:
- Skill IO 能力
- MCP IO 能力
- IO 能力层集成
- 语义 VM 集成
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from intentos.agent.registry import CapabilityRegistry
from intentos.agent.io_capabilities import (
    IOCapabilityLayer,
    SkillIOCapability,
    MCPIOCapability,
)


# =============================================================================
# Skill IO 能力测试
# =============================================================================


class TestSkillIOCapability:
    """Skill IO 能力测试"""

    @pytest.fixture
    def registry(self):
        """创建能力注册中心"""
        return CapabilityRegistry()

    @pytest.fixture
    def skill_io(self, registry):
        """创建 Skill IO 能力"""
        return SkillIOCapability(registry)

    def test_register_skill_io(self, skill_io, registry):
        """测试注册 Skill IO 能力"""
        skill_io.register()

        # 验证能力已注册
        caps = registry.list_capabilities()
        skill_io_cap = next((c for c in caps if c.id == "skill_io"), None)

        assert skill_io_cap is not None
        assert skill_io_cap.name == "Skill IO"
        assert skill_io_cap.source == "builtin"
        assert "io" in skill_io_cap.tags
        assert "skill" in skill_io_cap.tags

    def test_list_skills_empty(self, skill_io):
        """测试列出空 Skill 列表"""
        skills = skill_io.list_skills()
        assert skills == []

    def test_match_skills_empty(self, skill_io):
        """测试匹配空 Skill 列表"""
        matches = skill_io.match_skills("分析数据")
        assert matches == []


# =============================================================================
# MCP IO 能力测试
# =============================================================================


class TestMCPIOCapability:
    """MCP IO 能力测试"""

    @pytest.fixture
    def registry(self):
        """创建能力注册中心"""
        return CapabilityRegistry()

    @pytest.fixture
    def mcp_io(self, registry):
        """创建 MCP IO 能力"""
        return MCPIOCapability(registry)

    def test_register_mcp_io(self, mcp_io, registry):
        """测试注册 MCP IO 能力"""
        mcp_io.register()

        # 验证能力已注册
        caps = registry.list_capabilities()
        mcp_io_cap = next((c for c in caps if c.id == "mcp_io"), None)

        assert mcp_io_cap is not None
        assert mcp_io_cap.name == "MCP IO"
        assert mcp_io_cap.source == "builtin"
        assert "io" in mcp_io_cap.tags
        assert "mcp" in mcp_io_cap.tags

    def test_list_servers_empty(self, mcp_io):
        """测试列出空 MCP 服务器列表"""
        servers = mcp_io.list_servers()
        assert servers == []


# =============================================================================
# IO 能力层集成测试
# =============================================================================


class TestIOCapabilityLayer:
    """IO 能力层集成测试"""

    @pytest.fixture
    def registry(self):
        """创建能力注册中心"""
        return CapabilityRegistry()

    @pytest.fixture
    def io_layer(self, registry):
        """创建 IO 能力层"""
        return IOCapabilityLayer(registry)

    def test_register_all(self, io_layer, registry):
        """测试注册所有 IO 能力"""
        io_layer.register_all()

        caps = registry.list_capabilities()
        cap_ids = [c.id for c in caps]

        assert "skill_io" in cap_ids
        assert "mcp_io" in cap_ids
        assert len(caps) == 2

    def test_get_stats(self, io_layer):
        """测试获取统计信息"""
        stats = io_layer.get_stats()

        assert "skills" in stats
        assert "mcp_servers" in stats
        assert stats["skills"] == 0
        assert stats["mcp_servers"] == 0


# =============================================================================
# 语义 VM 集成测试
# =============================================================================


class TestSemanticVMIOIntegration:
    """语义 VM IO 集成测试"""

    @pytest.fixture
    def registry(self):
        """创建能力注册中心"""
        return CapabilityRegistry()

    @pytest.fixture
    def vm(self, registry):
        """创建语义 VM (带 IO 能力集成)"""
        from intentos.semantic_vm.vm import SemanticVM
        return SemanticVM(registry=registry)

    def test_vm_io_capabilities_initialized(self, vm):
        """测试 IO 能力已初始化"""
        assert vm.io_capabilities is not None
        assert vm.io_capabilities.skill_io is not None
        assert vm.io_capabilities.mcp_io is not None

    def test_vm_list_available_skills(self, vm):
        """测试 VM 列出可用 Skill"""
        skills = vm.io_capabilities.list_available_skills()
        assert isinstance(skills, list)

    def test_vm_match_skills(self, vm):
        """测试 VM 匹配 Skill"""
        matches = vm.io_capabilities.match_skills("分析数据")
        assert isinstance(matches, list)

    def test_vm_list_mcp_servers(self, vm):
        """测试 VM 列出 MCP 服务器"""
        servers = vm.io_capabilities.list_mcp_servers()
        assert isinstance(servers, list)


# =============================================================================
# 集成测试 - 完整流程
# =============================================================================


class TestIOCapabilityFullIntegration:
    """IO 能力完整集成测试"""

    @pytest.fixture
    def registry(self):
        """创建能力注册中心"""
        return CapabilityRegistry()

    @pytest.fixture
    def io_layer(self, registry):
        """创建 IO 能力层"""
        return IOCapabilityLayer(registry)

    def test_full_registration_flow(self, io_layer, registry):
        """测试完整注册流程"""
        # 注册 IO 能力
        io_layer.register_all()

        # 验证能力已注册
        caps = registry.list_capabilities()
        assert len(caps) == 2

        # 验证能力详情
        skill_io_cap = next(c for c in caps if c.id == "skill_io")
        mcp_io_cap = next(c for c in caps if c.id == "mcp_io")

        assert skill_io_cap.is_read_only is False
        assert skill_io_cap.is_concurrency_safe is False
        assert mcp_io_cap.is_read_only is False
        assert mcp_io_cap.is_concurrency_safe is False

    def test_stats_after_registration(self, io_layer):
        """测试注册后的统计信息"""
        io_layer.register_all()
        stats = io_layer.get_stats()

        assert stats["skills"] == 0  # 暂无 Skill
        assert stats["mcp_servers"] == 0  # 暂无 MCP 服务器
