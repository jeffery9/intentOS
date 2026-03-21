# -*- coding: utf-8 -*-
"""
Code Generator Demo App

代码生成工具 - 根据需求生成代码，支持多种编程语言。
计费模式：按 Token 消耗 $0.02/1K tokens
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

logger: logging.Logger = logging.getLogger(__name__)


class CodeGeneratorApp:
    """
    代码生成工具 App

    功能：
    - 代码生成（Python/JS/Java 等）
    - 代码审查
    - Bug 修复
    - 单元测试生成
    - 代码解释

    计费：$0.02/1K tokens
    """

    def __init__(self) -> None:
        self.name: str = "code_generator"
        self.version: str = "1.0.0"
        self.description: str = "代码生成工具"
        self.icon: str = "💻"
        self.pricing: dict[str, Any] = {
            "model": "pay_per_token",
            "price_per_1k_tokens": 0.02,  # $0.02/1K tokens
        }
        logger.info(f"代码生成工具 App 初始化：{self.name}")

    def build_package(self) -> dict[str, Any]:
        """构建意图包"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": "IntentOS Team",
            "icon": self.icon,
            "intents": {
                "code_generation": {
                    "id": "code_generation",
                    "name": "代码生成",
                    "description": "根据需求生成代码",
                    "patterns": [
                        ".*写.*代码.*",
                        ".*生成.*代码.*",
                        ".*实现.*功能.*",
                        ".*create.*function.*",
                        ".*write.*code.*",
                    ],
                    "required_capabilities": ["code_generator", "language_detector"],
                    "pricing": self.pricing,
                },
                "code_review": {
                    "id": "code_review",
                    "name": "代码审查",
                    "description": "审查代码质量",
                    "patterns": [
                        ".*审查.*代码.*",
                        ".*code.*review.*",
                        ".*检查.*代码.*",
                        ".*优化.*代码.*",
                    ],
                    "required_capabilities": ["code_analyzer", "best_practices_checker"],
                    "pricing": self.pricing,
                },
                "bug_fix": {
                    "id": "bug_fix",
                    "name": "Bug 修复",
                    "description": "修复代码错误",
                    "patterns": [
                        ".*修复.*bug.*",
                        ".*fix.*bug.*",
                        ".*错误.*",
                        ".*报错.*",
                        ".*exception.*",
                        ".*error.*",
                    ],
                    "required_capabilities": ["bug_detector", "code_fixer"],
                    "pricing": self.pricing,
                },
                "test_generation": {
                    "id": "test_generation",
                    "name": "测试生成",
                    "description": "生成单元测试",
                    "patterns": [
                        ".*测试.*",
                        ".*unit.*test.*",
                        ".*写测试.*",
                        ".*generate.*test.*",
                    ],
                    "required_capabilities": ["test_generator", "code_generator"],
                    "pricing": self.pricing,
                },
                "code_explanation": {
                    "id": "code_explanation",
                    "name": "代码解释",
                    "description": "解释代码功能",
                    "patterns": [
                        ".*解释.*代码.*",
                        ".*这段代码.*",
                        ".*什么意思.*",
                        ".*explain.*code.*",
                    ],
                    "required_capabilities": ["code_explainer", "language_detector"],
                    "pricing": self.pricing,
                },
            },
            "capabilities": {
                "code_generator": {
                    "id": "code_generator",
                    "name": "代码生成器",
                    "description": "生成多种编程语言代码",
                    "tags": ["code", "generation"],
                    "pricing": {"model": "included"},
                },
                "language_detector": {
                    "id": "language_detector",
                    "name": "语言检测",
                    "description": "检测编程语言",
                    "tags": ["detection", "language"],
                    "pricing": {"model": "free"},
                },
                "code_analyzer": {
                    "id": "code_analyzer",
                    "name": "代码分析器",
                    "description": "分析代码质量",
                    "tags": ["analysis", "quality"],
                    "pricing": {"model": "included"},
                },
                "best_practices_checker": {
                    "id": "best_practices_checker",
                    "name": "最佳实践检查",
                    "description": "检查代码规范",
                    "tags": ["quality", "standards"],
                    "pricing": {"model": "included"},
                },
                "bug_detector": {
                    "id": "bug_detector",
                    "name": "Bug 检测",
                    "description": "检测代码问题",
                    "tags": ["debug", "analysis"],
                    "pricing": {"model": "included"},
                },
                "code_fixer": {
                    "id": "code_fixer",
                    "name": "代码修复",
                    "description": "修复代码错误",
                    "tags": ["fix", "debug"],
                    "pricing": {"model": "included"},
                },
                "test_generator": {
                    "id": "test_generator",
                    "name": "测试生成器",
                    "description": "生成单元测试",
                    "tags": ["test", "generation"],
                    "pricing": {"model": "included"},
                },
                "code_explainer": {
                    "id": "code_explainer",
                    "name": "代码解释器",
                    "description": "解释代码功能",
                    "tags": ["explanation", "education"],
                    "pricing": {"model": "included"},
                },
            },
            "pricing": self.pricing,
        }

    async def generate_code(
        self,
        requirement: str,
        language: str = "python",
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        生成代码

        Args:
            requirement: 需求描述
            language: 编程语言
            context: 上下文信息

        Returns:
            生成的代码和计费信息
        """
        logger.info(f"生成代码：{requirement}, 语言：{language}")

        # 模拟代码生成
        import time
        start_time = time.time()

        # 模拟处理
        await asyncio.sleep(0.3)

        generated_code = self._generate_sample_code(requirement, language)
        tokens_used = self._estimate_tokens(generated_code)
        cost = self._calculate_cost(tokens_used)

        response = {
            "success": True,
            "requirement": requirement,
            "language": language,
            "code": generated_code,
            "explanation": self._explain_code(generated_code),
            "tokens_used": tokens_used,
            "billing": {
                "amount": cost,
                "currency": "USD",
                "description": f"代码生成 ({tokens_used} tokens)",
                "breakdown": {
                    "rate": "$0.02/1K tokens",
                    "tokens_charged": tokens_used,
                },
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return response

    def _generate_sample_code(self, requirement: str, language: str) -> str:
        """生成示例代码（模拟）"""
        if "排序" in requirement or "sort" in requirement.lower():
            if language == "python":
                return '''def quick_sort(arr):
    """快速排序"""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# 测试
print(quick_sort([3, 6, 8, 10, 1, 2, 1]))'''
            elif language == "javascript":
                return '''function quickSort(arr) {
    // 快速排序
    if (arr.length <= 1) return arr;
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const middle = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    return [...quickSort(left), ...middle, ...quickSort(right)];
}

// 测试
console.log(quickSort([3, 6, 8, 10, 1, 2, 1]));'''

        elif "文件" in requirement or "file" in requirement.lower():
            if language == "python":
                return '''def read_file(path):
    """读取文件内容"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    """写入文件内容"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)'''

        return f'''# {requirement} 的实现
def solution():
    # TODO: 实现具体功能
    pass

if __name__ == "__main__":
    solution()'''

    def _estimate_tokens(self, code: str) -> int:
        """估算 Token 数量"""
        # 简单估算：每 4 个字符约 1 个 token
        return len(code) // 4

    def _calculate_cost(self, tokens: int) -> float:
        """计算费用"""
        return (tokens / 1000) * self.pricing["price_per_1k_tokens"]

    def _explain_code(self, code: str) -> str:
        """解释代码（模拟）"""
        if "quick_sort" in code or "quickSort" in code:
            return "这是一个快速排序实现，使用分治法：1) 选择基准值 2) 将数组分为小于、等于、大于基准的三部分 3) 递归排序左右部分"
        return "代码已生成，请检查实现是否符合需求。"

    async def review_code(
        self,
        code: str,
        language: str = "python",
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        代码审查

        Args:
            code: 待审查的代码
            language: 编程语言
            context: 上下文信息

        Returns:
            审查结果
        """
        logger.info(f"代码审查：{len(code)} 字符，语言：{language}")

        # 模拟审查
        review_result = {
            "success": True,
            "code_length": len(code),
            "language": language,
            "issues": self._find_issues(code),
            "suggestions": self._generate_suggestions(code),
            "score": self._calculate_score(code),
            "billing": {
                "amount": 0.02,  # 模拟费用
                "currency": "USD",
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return review_result

    def _find_issues(self, code: str) -> list[dict[str, Any]]:
        """查找问题（模拟）"""
        issues = []
        if "TODO" in code:
            issues.append({
                "type": "warning",
                "message": "发现 TODO 注释，建议完成实现",
                "line": 1,
            })
        if "print(" in code:
            issues.append({
                "type": "info",
                "message": "发现 print 语句，生产环境建议使用 logging",
                "line": 1,
            })
        return issues

    def _generate_suggestions(self, code: str) -> list[str]:
        """生成建议（模拟）"""
        return [
            "建议添加类型注解提高代码可读性",
            "建议添加 docstring 说明函数功能",
            "考虑添加异常处理增强健壮性",
        ]

    def _calculate_score(self, code: str) -> dict[str, float]:
        """计算代码评分（模拟）"""
        return {
            "overall": 85.0,
            "readability": 80.0,
            "maintainability": 85.0,
            "performance": 90.0,
            "security": 85.0,
        }

    async def submit_to_intentos(
        self,
        intentos_url: str = "http://localhost:8080",
        api_key: Optional[str] = None
    ) -> dict[str, Any]:
        """提交到 IntentOS"""
        from intentos.agent.submission import IntentOSConnector

        connector = IntentOSConnector(intentos_url, api_key)

        async with connector:
            builder = connector.builder
            pkg = self.build_package()

            builder.create_package(
                name=pkg["name"],
                version=pkg["version"],
                description=pkg["description"],
                author=pkg["author"],
            )

            # 添加意图
            for intent_id, intent in pkg["intents"].items():
                builder.add_intent(
                    intent_id=intent_id,
                    name=intent["name"],
                    description=intent["description"],
                    patterns=intent["patterns"],
                    required_capabilities=intent["required_capabilities"],
                    pricing=intent["pricing"],
                )

            # 注册能力
            for cap_id, cap in pkg["capabilities"].items():
                builder.register_capability(
                    cap_id=cap_id,
                    name=cap["name"],
                    description=cap["description"],
                    tags=cap["tags"],
                    pricing=cap["pricing"],
                )

            errors = builder.validate()
            if errors:
                raise ValueError(f"App 验证失败：{', '.join(errors)}")

            result = await connector.submit(wait_for_approval=False)
            logger.info(f"代码生成工具 App 已提交：{result['app_id']}")

            return result


# 便捷创建函数
def create_code_generator() -> CodeGeneratorApp:
    """创建代码生成工具 App"""
    return CodeGeneratorApp()
