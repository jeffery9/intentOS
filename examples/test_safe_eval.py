"""
安全条件评估器测试

测试用例覆盖：
1. 基础功能测试
2. 变量替换测试
3. 逻辑运算符测试
4. 算术运算符测试
5. 安全测试（阻止注入攻击）
6. 边界条件测试
"""

import pytest

from intentos.semantic_vm.safe_eval import SafeConditionEvaluator


class TestSafeConditionEvaluator:
    """SafeConditionEvaluator 测试类"""

    # =========================================================================
    # 基础功能测试
    # =========================================================================

    def test_empty_condition(self):
        """测试空条件"""
        assert SafeConditionEvaluator.evaluate("", {}) is True
        assert SafeConditionEvaluator.evaluate("   ", {}) is True

    def test_boolean_literals(self):
        """测试布尔字面量"""
        assert SafeConditionEvaluator.evaluate("True", {}) is True
        assert SafeConditionEvaluator.evaluate("False", {}) is False

    def test_numeric_comparison(self):
        """测试数值比较"""
        assert SafeConditionEvaluator.evaluate("1 == 1", {}) is True
        assert SafeConditionEvaluator.evaluate("1 == 2", {}) is False
        assert SafeConditionEvaluator.evaluate("1 < 2", {}) is True
        assert SafeConditionEvaluator.evaluate("2 > 1", {}) is True
        assert SafeConditionEvaluator.evaluate("1 <= 1", {}) is True
        assert SafeConditionEvaluator.evaluate("1 >= 1", {}) is True
        assert SafeConditionEvaluator.evaluate("1 != 2", {}) is True

    def test_string_comparison(self):
        """测试字符串比较"""
        assert SafeConditionEvaluator.evaluate("'abc' == 'abc'", {}) is True
        assert SafeConditionEvaluator.evaluate("'abc' == 'def'", {}) is False
        assert SafeConditionEvaluator.evaluate("'abc' < 'abd'", {}) is True
        assert SafeConditionEvaluator.evaluate("'xyz' > 'abc'", {}) is True

    # =========================================================================
    # 变量测试
    # =========================================================================

    def test_variable_substitution_dollar(self):
        """测试 ${var} 格式变量替换"""
        variables = {"x": 10, "y": 20}
        assert SafeConditionEvaluator.evaluate("${x} < ${y}", variables) is True
        assert SafeConditionEvaluator.evaluate("${x} == 10", variables) is True

    def test_variable_direct_reference(self):
        """测试直接变量引用"""
        variables = {"x": 10, "y": 20}
        assert SafeConditionEvaluator.evaluate("x < y", variables) is True
        assert SafeConditionEvaluator.evaluate("x == 10", variables) is True

    def test_string_variable(self):
        """测试字符串变量"""
        variables = {"name": "Alice"}
        assert SafeConditionEvaluator.evaluate("name == 'Alice'", variables) is True
        assert SafeConditionEvaluator.evaluate("${name} == 'Alice'", variables) is True

    def test_boolean_variable(self):
        """测试布尔变量"""
        variables = {"enabled": True}
        assert SafeConditionEvaluator.evaluate("enabled == True", variables) is True
        assert SafeConditionEvaluator.evaluate("enabled", variables) is True

    def test_undefined_variable(self):
        """测试未定义变量"""
        with pytest.raises(ValueError) as exc_info:
            SafeConditionEvaluator.evaluate("undefined_var == 1", {})
        assert "未定义变量" in str(exc_info.value)

    # =========================================================================
    # 逻辑运算符测试
    # =========================================================================

    def test_and_operator(self):
        """测试 AND 运算符"""
        assert SafeConditionEvaluator.evaluate("True and True", {}) is True
        assert SafeConditionEvaluator.evaluate("True and False", {}) is False
        assert SafeConditionEvaluator.evaluate("False and True", {}) is False

    def test_or_operator(self):
        """测试 OR 运算符"""
        assert SafeConditionEvaluator.evaluate("True or False", {}) is True
        assert SafeConditionEvaluator.evaluate("False or False", {}) is False
        assert SafeConditionEvaluator.evaluate("False or True", {}) is True

    def test_not_operator(self):
        """测试 NOT 运算符"""
        assert SafeConditionEvaluator.evaluate("not False", {}) is True
        assert SafeConditionEvaluator.evaluate("not True", {}) is False

    def test_complex_logical(self):
        """测试复杂逻辑表达式"""
        expr = "(a and b) or (c and not d)"
        variables = {"a": True, "b": False, "c": True, "d": False}
        # (True and False) or (True and True) = False or True = True
        assert SafeConditionEvaluator.evaluate(expr, variables) is True

    # =========================================================================
    # 算术运算符测试
    # =========================================================================

    def test_addition(self):
        """测试加法"""
        assert SafeConditionEvaluator.evaluate("1 + 2 == 3", {}) is True
        assert SafeConditionEvaluator.evaluate("1.5 + 2.5 == 4", {}) is True

    def test_subtraction(self):
        """测试减法"""
        assert SafeConditionEvaluator.evaluate("5 - 3 == 2", {}) is True

    def test_multiplication(self):
        """测试乘法"""
        assert SafeConditionEvaluator.evaluate("3 * 4 == 12", {}) is True

    def test_division(self):
        """测试除法"""
        assert SafeConditionEvaluator.evaluate("12 / 4 == 3", {}) is True

    def test_modulo(self):
        """测试取模"""
        assert SafeConditionEvaluator.evaluate("10 % 3 == 1", {}) is True

    def test_complex_arithmetic(self):
        """测试复杂算术"""
        expr = "(1 + 2) * 3 - 4 == 5"
        assert SafeConditionEvaluator.evaluate(expr, {}) is True

    def test_arithmetic_with_variables(self):
        """测试带变量的算术"""
        variables = {"x": 10, "y": 5}
        assert SafeConditionEvaluator.evaluate("x + y == 15", variables) is True
        assert SafeConditionEvaluator.evaluate("x * y == 50", variables) is True
        assert SafeConditionEvaluator.evaluate("x / y == 2", variables) is True

    # =========================================================================
    # 安全测试
    # =========================================================================

    def test_forbidden_import(self):
        """测试阻止 import"""
        with pytest.raises(ValueError) as exc_info:
            SafeConditionEvaluator.evaluate("__import__('os')", {})
        assert "安全错误" in str(exc_info.value) or "不支持" in str(exc_info.value)

    def test_forbidden_function_call(self):
        """测试阻止函数调用"""
        with pytest.raises(ValueError):
            SafeConditionEvaluator.evaluate("eval('1+1')", {})

    def test_forbidden_attribute_access(self):
        """测试阻止属性访问"""
        with pytest.raises(ValueError):
            SafeConditionEvaluator.evaluate("self.memory", {})

    def test_forbidden_dunder(self):
        """测试阻止双下划线"""
        with pytest.raises(ValueError):
            SafeConditionEvaluator.evaluate("__class__", {})

    def test_forbidden_exec(self):
        """测试阻止 exec"""
        with pytest.raises(ValueError):
            SafeConditionEvaluator.evaluate("exec('print(1)')", {})

    def test_is_safe_expression(self):
        """测试安全检查函数"""
        is_safe, msg = SafeConditionEvaluator.is_safe_expression("x > 0")
        assert is_safe is True

        is_safe, msg = SafeConditionEvaluator.is_safe_expression("__import__('os')")
        assert is_safe is False
        assert "禁止" in msg

    # =========================================================================
    # 边界条件测试
    # =========================================================================

    def test_none_value(self):
        """测试 None 值"""
        # 注意：'is' 操作符当前不支持，使用 == 比较
        assert SafeConditionEvaluator.evaluate("None == None", {}) is True
        variables = {"x": None}
        assert SafeConditionEvaluator.evaluate("x == None", variables) is True

    def test_large_numbers(self):
        """测试大数"""
        large_num = 10**100
        assert SafeConditionEvaluator.evaluate(f"{large_num} > 0", {}) is True

    def test_float_precision(self):
        """测试浮点精度"""
        # 浮点数有精度误差
        assert SafeConditionEvaluator.evaluate("0.1 + 0.2 == 0.3", {}) is False
        # 注意：abs() 函数不支持，这是设计决定（安全考虑）
        # 浮点精度测试仅验证基本行为
        assert SafeConditionEvaluator.evaluate("0.5 + 0.5 == 1.0", {}) is True

    def test_mixed_types(self):
        """测试混合类型"""
        variables = {"x": 10, "name": "test"}
        assert SafeConditionEvaluator.evaluate("x > 5 and name == 'test'", variables) is True

    def test_nested_parentheses(self):
        """测试嵌套括号"""
        expr = "((1 + 2) * (3 + 4)) == 21"
        assert SafeConditionEvaluator.evaluate(expr, {}) is True

    def test_complex_real_world(self):
        """测试真实场景"""
        variables = {
            "score": 85,
            "threshold": 60,
            "max_score": 100,
            "passed": False,
        }

        expr = "score >= threshold and score <= max_score and not passed"
        assert SafeConditionEvaluator.evaluate(expr, variables) is True


class TestSafeConditionEvaluatorErrors:
    """错误处理测试"""

    def test_syntax_error(self):
        """测试语法错误"""
        with pytest.raises(ValueError) as exc_info:
            SafeConditionEvaluator.evaluate("x == ", {})
        assert "语法错误" in str(exc_info.value)

    def test_invalid_operator(self):
        """测试无效操作符"""
        with pytest.raises(ValueError):
            SafeConditionEvaluator.evaluate("1 ** 2", {})  # 幂运算不支持

    def test_unsupported_type(self):
        """测试不支持的类型"""
        # 列表推导式不支持
        with pytest.raises(ValueError):
            SafeConditionEvaluator.evaluate("[x for x in range(10)]", {})
