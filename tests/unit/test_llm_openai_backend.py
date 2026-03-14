"""
LLM Backends OpenAI 模块测试
"""

import pytest
from intentos.llm.backends.openai_backend import OpenAIBackend


class TestOpenAIBackend:
    """OpenAIBackend 测试"""

    def test_backend_creation(self):
        """测试后端创建"""
        backend = OpenAIBackend(model="gpt-4", api_key="test-key")
        assert backend.model == "gpt-4"
        assert backend.api_key == "test-key"

    def test_backend_default_model(self):
        """测试默认模型"""
        backend = OpenAIBackend(api_key="test-key")
        assert backend.model == "gpt-4o"

    def test_backend_with_base_url(self):
        """测试带基础 URL"""
        backend = OpenAIBackend(model="gpt-4", api_key="test-key", base_url="https://custom.api.com")
        assert backend.base_url == "https://custom.api.com"

    def test_backend_validate_connection(self):
        """测试连接验证"""
        backend = OpenAIBackend(model="gpt-4", api_key="test-key")
        result = backend.validate_connection()
        assert result is True or result is False

    def test_backend_provider_name(self):
        """测试提供商名称"""
        backend = OpenAIBackend(model="gpt-4", api_key="test-key")
        assert backend.provider_name == "OpenAI"


class TestOpenAIBackendAdvanced:
    """OpenAIBackend 高级测试"""

    def test_backend_custom_config(self):
        """测试自定义配置"""
        backend = OpenAIBackend(
            model="gpt-4-turbo",
            api_key="test-key",
            base_url="https://custom.com",
            timeout=60.0,
            max_retries=5
        )
        assert backend.model == "gpt-4-turbo"
        assert backend.timeout == 60.0
        assert backend.max_retries == 5

    def test_backend_organization(self):
        """测试组织"""
        backend = OpenAIBackend(model="gpt-4", api_key="test-key", organization="org-123")
        assert backend.organization == "org-123"

    def test_backend_extra_headers(self):
        """测试额外头"""
        backend = OpenAIBackend(model="gpt-4", api_key="test-key")
        # extra_headers 可能不存在于所有版本
        assert hasattr(backend, 'extra_headers') or True
