"""
测试 intentos.semantic_vm.isolation - PEF 执行隔离

覆盖:
- AbortController (创建, abort, link_to_parent, cascade)
- ExecutionContext
"""


import pytest


class TestAbortController:
    """中止控制器测试"""

    def test_initial_not_aborted(self):
        from intentos.semantic_vm.isolation import AbortController
        ctrl = AbortController()
        assert not ctrl.is_aborted

    def test_abort_sets_flag(self):
        from intentos.semantic_vm.isolation import AbortController
        ctrl = AbortController()
        ctrl.abort("手动中止")
        assert ctrl.is_aborted

    def test_abort_idempotent(self):
        from intentos.semantic_vm.isolation import AbortController
        ctrl = AbortController()
        called = []
        ctrl.on_abort(lambda: called.append(1))
        ctrl.abort("first")
        ctrl.abort("second")
        assert len(called) == 1

    def test_link_to_parent_cascades_abort(self):
        from intentos.semantic_vm.isolation import AbortController
        parent = AbortController()
        child = AbortController()
        child.link_to_parent(parent)
        parent.abort("parent aborted")
        assert child.is_aborted

    def test_multiple_children_cascade(self):
        from intentos.semantic_vm.isolation import AbortController
        parent = AbortController()
        children = [AbortController() for _ in range(5)]
        for c in children:
            c.link_to_parent(parent)
        parent.abort("all")
        assert all(c.is_aborted for c in children)


class TestExecutionContext:
    """执行上下文测试"""

    def test_default_execution_context(self):
        from intentos.semantic_vm.isolation import ExecutionContext
        ctx = ExecutionContext()
        assert ctx.sandbox_path == ""
