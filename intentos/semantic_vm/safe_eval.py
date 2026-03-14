"""
安全条件评估器

替代危险的 eval()，防止代码注入攻击

设计文档：docs/private/001-eval-security-fix.md
"""

from __future__ import annotations

import ast
import operator
from typing import Any


# 支持的操作符映射
SAFE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.Not: operator.not_,
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}


class SafeConditionEvaluator:
    """
    安全条件评估器
    
    使用 AST 解析和评估条件表达式，防止代码注入
    
    支持的语法:
    - 比较：a == b, a > b, a <= b
    - 逻辑：a and b, a or b, not a
    - 算术：a + b, a - b, a * b, a / b
    - 变量：${var_name} 或直接使用变量名
    - 字面量：字符串、数字、布尔值、None
    
    禁止的:
    - 函数调用
    - 属性访问
    - import 语句
    - 双下划线魔法方法
    """
    
    @staticmethod
    def evaluate(condition: str, variables: dict[str, Any]) -> bool:
        """
        安全评估条件表达式
        
        Args:
            condition: 条件表达式字符串
            variables: 变量字典
            
        Returns:
            评估结果 (bool)
            
        Raises:
            ValueError: 表达式包含不安全操作或语法错误
        """
        if not condition or condition.strip() == "":
            return True
        
        try:
            # 1. 变量替换 ${var_name} -> value
            processed = SafeConditionEvaluator._substitute_variables(
                condition, variables
            )
            
            # 2. 解析 AST
            tree = ast.parse(processed, mode='eval')
            
            # 3. 安全验证 + 求值
            return SafeConditionEvaluator._eval_node(tree.body, variables)
            
        except SyntaxError as e:
            raise ValueError(f"语法错误：{e}")
        except ValueError as e:
            raise ValueError(f"安全错误：{e}")
        except Exception as e:
            raise ValueError(f"评估失败：{e}")
    
    @staticmethod
    def _substitute_variables(condition: str, variables: dict[str, Any]) -> str:
        """替换 ${var_name} 格式的变量"""
        result = condition
        for key, value in variables.items():
            placeholder = f"${{{key}}}"
            if isinstance(value, str):
                # 字符串值加引号
                escaped = value.replace("'", "\\'")
                result = result.replace(placeholder, f"'{escaped}'")
            elif isinstance(value, bool):
                result = result.replace(placeholder, str(value).lower())
            elif value is None:
                result = result.replace(placeholder, "None")
            else:
                result = result.replace(placeholder, str(value))
        return result
    
    @staticmethod
    def _eval_node(node: ast.AST, variables: dict[str, Any]) -> Any:
        """递归评估 AST 节点"""
        
        # 字面量 (Python 3.8+)
        if isinstance(node, ast.Constant):
            return node.value
        
        # 兼容 Python 3.7
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.NameConstant):
            return node.value
        
        # 变量引用
        elif isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            elif node.id == 'True':
                return True
            elif node.id == 'False':
                return False
            elif node.id == 'None':
                return None
            else:
                raise ValueError(f"未定义变量：{node.id}")
        
        # 二元操作符
        elif isinstance(node, ast.BinOp):
            left = SafeConditionEvaluator._eval_node(node.left, variables)
            right = SafeConditionEvaluator._eval_node(node.right, variables)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](left, right)
            else:
                raise ValueError(f"不支持的操作符：{op_type.__name__}")
        
        # 比较操作符
        elif isinstance(node, ast.Compare):
            left = SafeConditionEvaluator._eval_node(node.left, variables)
            comparators = [
                SafeConditionEvaluator._eval_node(c, variables) 
                for c in node.comparators
            ]
            ops = [type(op) for op in node.ops]
            
            result = True
            current = left
            for op_type, comparator in zip(ops, comparators):
                if op_type not in SAFE_OPERATORS:
                    raise ValueError(f"不支持的比较操作符：{op_type.__name__}")
                op = SAFE_OPERATORS[op_type]
                result = result and op(current, comparator)
                current = comparator
            return result
        
        # 布尔操作符
        elif isinstance(node, ast.BoolOp):
            values = [
                SafeConditionEvaluator._eval_node(v, variables) 
                for v in node.values
            ]
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"不支持的布尔操作符：{op_type.__name__}")
            op = SAFE_OPERATORS[op_type]
            
            result = values[0]
            for value in values[1:]:
                result = op(result, value)
            return result
        
        # 一元操作符 (not)
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                operand = SafeConditionEvaluator._eval_node(node.operand, variables)
                return not operand
            else:
                raise ValueError(f"不支持的一元操作符：{type(node.op).__name__}")
        
        else:
            raise ValueError(f"不支持的表达式类型：{type(node).__name__}")
    
    @classmethod
    def is_safe_expression(cls, condition: str) -> tuple[bool, str]:
        """
        预检查表达式是否安全
        
        Returns:
            (是否安全，错误信息)
        """
        forbidden_patterns = [
            '__',  # 双下划线（魔法方法）
            'import',
            'exec',
            'eval',
            'compile',
            'open',
            'file',
            'os.',
            'sys.',
            'subprocess',
            'lambda',
            'def ',
            'class ',
            '(',  # 函数调用
        ]
        
        for pattern in forbidden_patterns:
            if pattern in condition:
                return False, f"包含禁止的模式：{pattern}"
        
        return True, ""
