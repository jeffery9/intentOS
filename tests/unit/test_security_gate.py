"""
测试 intentos.security.gate - Capability Gate 门控管线

覆盖:
- DenialTracker (熔断器)
- CapabilityGate (能力门控)
- PermissionMode (权限模式变换)
- GateResult/GateDecision
"""

import time

import pytest


class TestDenialTracker:
    """熔断器测试"""

    def test_initial_state(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker()
        assert not tracker.is_circuit_open("test_cap")

    def test_record_denial_increments_count(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker(consecutive_threshold=3, total_threshold=10)
        tracker.record_denial("cap_a")
        assert tracker.consecutive_denials["cap_a"] == 1

    def test_consecutive_threshold_triggers_circuit(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker(consecutive_threshold=3, total_threshold=10)
        for _ in range(3):
            tracker.record_denial("cap_a")
        assert tracker.is_circuit_open("cap_a")

    def test_total_threshold_triggers_circuit(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker(consecutive_threshold=100, total_threshold=5)
        for _ in range(5):
            tracker.record_denial("cap_b")
        assert tracker.is_circuit_open("cap_b")

    def test_allow_resets_consecutive(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker(consecutive_threshold=2, total_threshold=10)
        for _ in range(2):
            tracker.record_denial("cap_a")
        assert tracker.is_circuit_open("cap_a")

    def test_circuit_expires_after_duration(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker(consecutive_threshold=2, circuit_duration=0.1)
        for _ in range(2):
            tracker.record_denial("cap_x")
        assert tracker.is_circuit_open("cap_x")
        time.sleep(0.15)
        assert not tracker.is_circuit_open("cap_x")

    def test_reset_single_capability(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker()
        tracker.record_denial("cap_a")
        tracker.record_denial("cap_b")
        tracker.reset("cap_a")
        assert "cap_a" not in tracker.consecutive_denials
        assert "cap_b" in tracker.consecutive_denials

    def test_reset_all(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker()
        tracker.record_denial("cap_a")
        tracker.reset()
        assert not tracker.consecutive_denials


class TestCapabilityGate:
    """能力门控测试"""

    def test_deny_rule_blocks(self):
        from intentos.security.gate import CapabilityGate, GateDecision
        gate = CapabilityGate()
        gate.add_deny_rule("dangerous_op")
        result = gate.evaluate("dangerous_op", None, None)
        assert result.decision == GateDecision.DENY

    def test_remove_deny_rule_unblocks(self):
        from intentos.security.gate import CapabilityGate
        gate = CapabilityGate()
        gate.add_deny_rule("temp_blocked")
        gate.remove_deny_rule("temp_blocked")
        result = gate.evaluate("temp_blocked", None, None)
        assert result.decision != GateDecision.DENY

    def test_ask_rule_requires_confirmation(self):
        from intentos.security.gate import CapabilityGate, GateDecision
        gate = CapabilityGate()
        gate.add_ask_rule("sensitive_op")
        result = gate.evaluate("sensitive_op", None, None)
        assert result.decision == GateDecision.ASK

    def test_circuit_breaker_denies(self):
        from intentos.security.gate import CapabilityGate, GateDecision
        gate = CapabilityGate()
        gate.denial_tracker.circuit_open_until["flooded"] = time.time() + 300
        result = gate.evaluate("flooded", None, None)
        assert result.decision == GateDecision.DENY


class TestPermissionMode:
    """权限模式变换测试"""

    def test_dont_ask_mode_denies_ask(self):
        from intentos.security.gate import (
            CapabilityGate, GateDecision, GateResult, PermissionMode
        )
        gate = CapabilityGate()
        gate.mode = PermissionMode.DONT_ASK
        result = GateResult(GateDecision.ASK, "需要确认")
        transformed = gate.transform_decision(result)
        assert transformed.decision == GateDecision.DENY

    def test_dont_ask_allows_allow(self):
        from intentos.security.gate import (
            CapabilityGate, GateDecision, GateResult, PermissionMode
        )
        gate = CapabilityGate()
        gate.mode = PermissionMode.DONT_ASK
        result = GateResult(GateDecision.ALLOW, "允许")
        transformed = gate.transform_decision(result)
        assert transformed.decision == GateDecision.ALLOW


class TestGateExceptions:
    """门控异常测试"""

    def test_circuit_breaker_error_is_subclass(self):
        from intentos.security.gate import CapabilityGateError, CircuitBreakerError
        with pytest.raises(CapabilityGateError):
            raise CircuitBreakerError("熔断器触发")

    def test_permission_denied_error_is_subclass(self):
        from intentos.security.gate import CapabilityGateError, PermissionDeniedError
        with pytest.raises(CapabilityGateError):
            raise PermissionDeniedError("权限拒绝")


class TestCapabilityGateIntegration:
    """门控管线集成测试"""

    def test_deny_prioritized_over_everything(self):
        from intentos.security.gate import CapabilityGate, GateDecision
        gate = CapabilityGate()
        gate.add_deny_rule("blocked_op")
        result = gate.evaluate("blocked_op", None, None)
        assert result.decision == GateDecision.DENY

    def test_multiple_capabilities_independent(self):
        from intentos.security.gate import DenialTracker
        tracker = DenialTracker(consecutive_threshold=2)
        tracker.record_denial("cap_a")
        for _ in range(2):
            tracker.record_denial("cap_b")
        assert not tracker.is_circuit_open("cap_a")
        assert tracker.is_circuit_open("cap_b")
