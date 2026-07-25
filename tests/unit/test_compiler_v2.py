"""
测试 intentos.compiler.compiler_v2 - 编译器 v2
"""

import pytest


class TestCompilerV2:
    """编译器 v2 测试"""

    def test_import(self):
        try:
            from intentos.compiler import compiler_v2
            assert compiler_v2 is not None
        except ImportError:
            pytest.skip("compiler_v2 模块不存在")
