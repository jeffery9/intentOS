# -*- coding: utf-8 -*-
import pytest
from datetime import datetime, timedelta
from intentos.distributed.autoscaler import (
    ScalingPolicy, Metrics, AutoScaler, ScaleDirection, SpotInstanceManager, ResourceReclaimer
)

class TestScalingPolicy:
    """ScalingPolicy 测试"""

    def test_default_policy(self):
        policy = ScalingPolicy.default()
        assert policy.min_replicas == 1
        assert policy.max_replicas == 10000

    def test_aggressive_policy(self):
        policy = ScalingPolicy.aggressive()
        assert policy.max_replicas == 50000
        assert policy.scale_up_stabilization_seconds == 0

    def test_conservative_policy(self):
        policy = ScalingPolicy.conservative()
        assert policy.min_replicas == 3
        assert policy.scale_down_stabilization_seconds == 600

class TestMetrics:
    """Metrics 测试"""

    def test_metrics_to_dict(self):
        metrics = Metrics(cpu_utilization=50.0, memory_utilization=60.0, requests_per_second=100)
        d = metrics.to_dict()
        assert d["cpu_utilization"] == 50.0
        assert d["memory_utilization"] == 60.0
        assert d["requests_per_second"] == 100
        assert "timestamp" in d

class TestAutoScaler:
    """AutoScaler 测试"""

    def test_no_change(self):
        scaler = AutoScaler(current_replicas=10)
        metrics = Metrics(cpu_utilization=70.0, requests_per_second=1000)
        direction, target = scaler.decide_scaling(metrics)
        assert direction == ScaleDirection.NO_CHANGE
        assert target == 10

    def test_scale_up_cpu(self):
        scaler = AutoScaler(current_replicas=10)
        metrics = Metrics(cpu_utilization=140.0) # 2x target
        direction, target = scaler.decide_scaling(metrics)
        assert direction == ScaleDirection.SCALE_UP
        # target_replicas = int(10 * 140 / 70) = 20
        assert target == 20

    def test_scale_down_cpu(self):
        scaler = AutoScaler(current_replicas=10)
        # target_cpu is 70. 0.5 * 70 = 35. 17.5 is below 35.
        metrics = Metrics(cpu_utilization=17.5) 
        direction, target = scaler.decide_scaling(metrics)
        assert direction == ScaleDirection.SCALE_DOWN
        # scale_factor = 17.5 / 35 = 0.5
        # target = int(10 * 0.5) = 5
        assert target == 5

    def test_scale_up_rps(self):
        scaler = AutoScaler(current_replicas=10)
        metrics = Metrics(cpu_utilization=70.0, requests_per_second=2000) # 2x target
        direction, target = scaler.decide_scaling(metrics)
        assert direction == ScaleDirection.SCALE_UP
        assert target == 20

    def test_scale_up_combined(self):
        scaler = AutoScaler(current_replicas=10)
        # Both CPU and RPS demand 2x
        metrics = Metrics(cpu_utilization=140.0, requests_per_second=2000)
        direction, target = scaler.decide_scaling(metrics)
        assert direction == ScaleDirection.SCALE_UP
        # CPU makes it 20, RPS doubles that to 40? 
        # Looking at code:
        # scale_factor = 140/70 = 2, target = 20
        # rps_factor = 2000/1000 = 2, target = 20 * 2 = 40
        assert target == 20 # Wait, let me re-read the code.
        # Oh, if direction is already SCALE_UP, it multiplies.
        # But there is also max_increase: current * scale_up_rate_percent (100%) = 10.
        # So max target is 10 + 10 = 20.
        assert target == 20 

    def test_stabilization_window(self):
        policy = ScalingPolicy(scale_up_stabilization_seconds=60)
        scaler = AutoScaler(policy=policy, current_replicas=10)
        
        metrics = Metrics(cpu_utilization=140.0)
        direction, target = scaler.decide_scaling(metrics)
        assert direction == ScaleDirection.SCALE_UP
        
        # Immediate second call should be blocked by stabilization
        direction2, target2 = scaler.decide_scaling(metrics)
        assert direction2 == ScaleDirection.NO_CHANGE

    def test_update_replicas(self):
        scaler = AutoScaler(current_replicas=10)
        scaler.update_replicas(20)
        assert scaler.current_replicas == 20

    def test_get_status(self):
        scaler = AutoScaler(current_replicas=10)
        status = scaler.get_status()
        assert status["current_replicas"] == 10
        assert status["scale_up_cooldown"] is None

class TestSpotInstanceManager:
    """SpotInstanceManager 测试"""

    def test_mix(self):
        mgr = SpotInstanceManager()
        mix = mgr.get_optimal_instance_mix()
        assert mix["spot"] == pytest.approx(0.8)
        assert mix["on_demand"] == pytest.approx(0.2)

    def test_interruption(self):
        mgr = SpotInstanceManager()
        res = mgr.handle_spot_interruption("inst1", 10)
        assert res["action"] == "replace_with_on_demand"
        assert res["instance_id"] == "inst1"

class TestResourceReclaimer:
    """ResourceReclaimer 测试"""

    @pytest.mark.asyncio
    async def test_reclaim_idle(self):
        reclaimer = ResourceReclaimer()
        now = datetime.now()
        resources = [
            {"id": "r1", "last_used": now - timedelta(seconds=1000)}, # Idle > 900
            {"id": "r2", "last_used": now - timedelta(seconds=100)},  # Not idle
        ]
        count = await reclaimer.reclaim_idle_resources(resources)
        assert count == 1

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        reclaimer = ResourceReclaimer()
        count = await reclaimer.cleanup_expired_data(None)
        assert count == 0
