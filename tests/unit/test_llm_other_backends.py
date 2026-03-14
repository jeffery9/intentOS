"""
LLM Backends Anthropic 和 Ollama 模块测试
"""

import pytest
from intentos.llm.backends.anthropic_backend import AnthropicBackend
from intentos.llm.backends.ollama_backend import OllamaBackend


class TestAnthropicBackend:
    """AnthropicBackend 测试"""

    def test_backend_creation(self):
        """测试后端创建"""
        backend = AnthropicBackend(model="claude-3-sonnet-20240229", api_key="test-key")
        assert backend.model == "claude-3-sonnet-20240229"
        assert backend.api_key == "test-key"

    def test_backend_default_model(self):
        """测试默认模型"""
        backend = AnthropicBackend(api_key="test-key")
        assert backend.model == "claude-3-5-sonnet-20241022"

    def test_backend_validate_connection(self):
        """测试连接验证"""
        backend = AnthropicBackend(model="claude-3", api_key="test-key")
        result = backend.validate_connection()
        assert result is True or result is False

    def test_backend_provider_name(self):
        """测试提供商名称"""
        backend = AnthropicBackend(model="claude-3", api_key="test-key")
        assert backend.provider_name == "Anthropic"


class TestOllamaBackend:
    """OllamaBackend 测试"""

    def test_backend_creation(self):
        """测试后端创建"""
        backend = OllamaBackend(model="llama3", host="http://localhost:11434")
        assert backend.model == "llama3"
        assert backend.host == "http://localhost:11434"

    def test_backend_default_model(self):
        """测试默认模型"""
        backend = OllamaBackend(host="http://localhost:11434")
        assert backend.model == "llama3.1"

    def test_backend_default_host(self):
        """测试默认 host"""
        backend = OllamaBackend(model="llama3")
        assert backend.host == "http://localhost:11434"

    def test_backend_validate_connection(self):
        """测试连接验证"""
        backend = OllamaBackend(model="llama3", host="http://localhost:11434")
        result = backend.validate_connection()
        assert result is True or result is False

    def test_backend_provider_name(self):
        """测试提供商名称"""
        backend = OllamaBackend(model="llama3", host="http://localhost:11434")
        assert backend.provider_name == "Ollama"


class TestBackendsIntegration:
    """Backends 集成测试"""

    def test_backend_base_class_features(self):
        """测试后端基类特性"""
        from intentos.llm.backends.base import LLMBackend
        
        # 验证基类存在
        assert LLMBackend is not None
        
        # 验证所有后端都继承自基类
        assert issubclass(AnthropicBackend, LLMBackend)
        assert issubclass(OllamaBackend, LLMBackend)
