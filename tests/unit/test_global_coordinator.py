# -*- coding: utf-8 -*-
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from intentos.distributed.global_coordinator import (
    BrainRegion, ThoughtFragment, GlobalCoordinator, RegionCoordinator, GlobalState
)

class TestBrainRegion:
    """BrainRegion 测试"""

    def test_to_dict(self):
        region = BrainRegion(id="reg1", location=(10.0, 20.0))
        d = region.to_dict()
        assert d["id"] == "reg1"
        assert d["location"] == (10.0, 20.0)
        assert "status" in d
        assert "nodes" in d

class TestThoughtFragment:
    """ThoughtFragment 测试"""

    def test_to_dict(self):
        fragment = ThoughtFragment(id="frag1", context={"key": "val"})
        d = fragment.to_dict()
        assert d["id"] == "frag1"
        assert d["context"] == {"key": "val"}
        assert "status" in d

class TestGlobalCoordinator:
    """GlobalCoordinator 测试"""

    @pytest.mark.asyncio
    async def test_select_best_region_by_location(self):
        """测试根据地理位置选择最佳区域"""
        coordinator = GlobalCoordinator()
        # Region in China (Beijing)
        r1 = BrainRegion(id="cn", location=(39.9, 116.4), status="active")
        # Region in US (LA)
        r2 = BrainRegion(id="us", location=(34.0, -118.2), status="active")
        coordinator.regions = {"cn": r1, "us": r2}
        
        # User in Shanghai
        ctx = {"user_location": (31.2, 121.5)}
        best = coordinator._select_best_region(None, ctx)
        assert best.id == "cn"

    @pytest.mark.asyncio
    async def test_select_best_region_by_load(self):
        """测试根据负载选择最佳区域"""
        coordinator = GlobalCoordinator()
        r1 = BrainRegion(id="r1", location=(0,0), status="active", load=0.8)
        r2 = BrainRegion(id="r2", location=(0,0), status="active", load=0.2)
        coordinator.regions = {"r1": r1, "r2": r2}
        
        best = coordinator._select_best_region(None, {})
        assert best.id == "r2"

    @pytest.mark.asyncio
    async def test_select_best_region_no_available(self):
        """测试无可用区域"""
        coordinator = GlobalCoordinator()
        with pytest.raises(RuntimeError, match="无可用区域"):
            coordinator._select_best_region(None, {})

    @pytest.mark.asyncio
    async def test_submit_thought(self):
        """测试提交思考"""
        coordinator = GlobalCoordinator()
        r1 = BrainRegion(id="r1", location=(0,0), status="active", nodes=["n1"])
        coordinator.regions = {"r1": r1}
        
        # Mock RegionCoordinator
        mock_rc = AsyncMock()
        coordinator.region_coordinators = {"r1": mock_rc}
        
        thought_id = await coordinator.submit_thought(None, {})
        assert thought_id in coordinator.active_thoughts
        assert coordinator.active_thoughts[thought_id].assigned_region == "r1"
        mock_rc.execute_fragment.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_global_state(self):
        """测试更新全球状态"""
        coordinator = GlobalCoordinator()
        r1 = BrainRegion(id="r1", location=(0,0), status="active", load=0.5)
        coordinator.regions = {"r1": r1}
        coordinator.active_thoughts = {"f1": MagicMock()}
        coordinator.completed_thoughts = {"f2": MagicMock()}
        
        await coordinator._update_global_state()
        assert coordinator.global_state.active_regions == 1
        assert coordinator.global_state.average_load == 0.5
        assert coordinator.global_state.total_thoughts == 2
        assert coordinator.global_state.active_thoughts == 1

    @pytest.mark.asyncio
    async def test_handle_failures(self):
        """测试处理失败 (超时)"""
        coordinator = GlobalCoordinator()
        f1 = ThoughtFragment(id="f1", status="running")
        # 模拟已运行超过 300 秒
        f1.started_at = datetime.now() - timedelta(seconds=600)
        coordinator.active_thoughts = {"f1": f1}
        
        await coordinator._handle_failures()
        assert f1.status == "failed"
        assert f1.error == "Thought execution timeout"

class TestRegionCoordinator:
    """RegionCoordinator 测试"""

    @pytest.mark.asyncio
    async def test_execute_fragment(self):
        """测试在区域中执行片段"""
        region = BrainRegion(id="r1", location=(0,0))
        rc = RegionCoordinator(region)
        
        # Mock node agent
        mock_node = MagicMock()
        mock_node.status = "healthy"
        mock_node.load = 0.1
        rc.nodes = {"n1": mock_node}
        
        fragment = ThoughtFragment(id="f1")
        await rc.execute_fragment(fragment)
        
        assert "f1" in rc.running_fragments
        assert len(rc.pending_fragments) == 0

    @pytest.mark.asyncio
    async def test_select_node_no_healthy(self):
        """测试无健康节点"""
        region = BrainRegion(id="r1", location=(0,0))
        rc = RegionCoordinator(region)
        
        mock_node = MagicMock()
        mock_node.status = "down"
        rc.nodes = {"n1": mock_node}
        
        node = await rc.select_node(None)
        assert node is None

    @pytest.mark.asyncio
    async def test_get_state(self):
        """测试获取区域状态"""
        region = BrainRegion(id="r1", location=(0,0))
        rc = RegionCoordinator(region)
        
        mock_node = AsyncMock()
        mock_node.get_state.return_value = {"status": "healthy", "load": 0.4}
        rc.nodes = {"n1": mock_node}
        
        state = await rc.get_state()
        assert state["region_id"] == "r1"
        assert state["load"] == 0.4
        assert state["healthy_nodes"] == 1
        assert state["status"] == "active"
