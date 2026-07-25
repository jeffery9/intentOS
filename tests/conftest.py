"""
测试配置和 Fixture

提供统一的测试基础设施:
- 自动 patch 外部依赖 (LLM API, 网络, 文件系统)
- 模拟能力注册中心
- 模拟上下文对象
- 清理临时资源
"""

import asyncio
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_capability_registry():
    """模拟能力注册中心"""
    registry = MagicMock()
    registry.list_capabilities.return_value = {}
    registry.get_capability.return_value = None
    return registry


@pytest.fixture
def mock_llm_backend():
    """模拟 LLM Backend (不发起网络请求)"""
    backend = MagicMock()
    backend.chat.return_value = MagicMock(content="模拟回复", finish_reason="stop")
    return backend


@dataclass
class MockContext:
    """模拟 AgentContext"""
    user_id: str = "test_user"
    permissions: list = None
    session_id: str = "session_test"

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ["*"]


@pytest.fixture
def mock_context():
    """模拟 AgentContext 实例"""
    return MockContext()


@pytest.fixture
def mock_semantic_vm():
    """模拟语义 VM"""
    vm = MagicMock()
    vm.execute = MagicMock(return_value=MagicMock(message="执行结果", data={"status": "ok"}))
    return vm


def run_async(coro):
    """运行异步测试"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture
def event_loop():
    """事件循环 fixture"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
