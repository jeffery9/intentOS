"""
LLM Executor 模块测试
"""

import pytest
from intentos.llm.executor import LLMExecutor, BackendStats


class TestBackendStats:
    """BackendStats 测试"""

    def test_stats_default(self):
        stats = BackendStats()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0

    def test_stats_with_values(self):
        stats = BackendStats(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            total_tokens=50000,
            avg_latency_ms=150.0
        )
        assert stats.total_requests == 100
        assert stats.success_rate == 0.95

    def test_stats_to_dict(self):
        stats = BackendStats(total_requests=10, successful_requests=8)
        data = stats.to_dict()
        assert "total_requests" in data
        assert "avg_latency_ms" in data


class TestLLMExecutor:
    """LLMExecutor 测试"""

    def test_executor_mock_creation(self):
        executor = LLMExecutor(provider="mock")
        assert executor._single_backend is not None

    def test_executor_mock_with_model(self):
        executor = LLMExecutor(provider="mock", model="custom-mock")
        assert executor._single_backend.model == "custom-mock"

    @pytest.mark.asyncio
    async def test_executor_mock_execute(self):
        executor = LLMExecutor(provider="mock")
        from intentos.llm.backends.base import Message
        messages = [Message.user("Hello")]
        response = await executor.execute(messages)
        assert response is not None

    def test_executor_create_backend_openai(self):
        executor = LLMExecutor.__new__(LLMExecutor)
        backend = executor._create_backend(provider="openai", model="gpt-4", api_key="test-key", base_url=None)
        assert backend is not None
        assert backend.model == "gpt-4"

    def test_executor_create_backend_anthropic(self):
        executor = LLMExecutor.__new__(LLMExecutor)
        backend = executor._create_backend(provider="anthropic", model="claude-3", api_key="test-key", base_url=None)
        assert backend is not None

    def test_executor_create_backend_ollama(self):
        executor = LLMExecutor.__new__(LLMExecutor)
        backend = executor._create_backend(provider="ollama", model="llama3", api_key=None, base_url="http://localhost:11434")
        assert backend is not None

    def test_executor_create_backend_unknown(self):
        executor = LLMExecutor.__new__(LLMExecutor)
        with pytest.raises(ValueError, match="未知提供商"):
            executor._create_backend(provider="unknown", model=None, api_key=None, base_url=None)


class TestLLMExecutorIntegration:
    """LLMExecutor 集成测试"""

    @pytest.mark.asyncio
    async def test_full_execution_workflow(self):
        executor = LLMExecutor(provider="mock")
        from intentos.llm.backends.base import Message
        messages = [Message.system("You are helpful"), Message.user("Hello")]
        response = await executor.execute(messages)
        assert response.content is not None
        assert response.usage is not None

    @pytest.mark.asyncio
    async def test_multiple_executions(self):
        executor = LLMExecutor(provider="mock")
        from intentos.llm.backends.base import Message
        for i in range(3):
            response = await executor.execute([Message.user(f"Message {i}")])
            assert response is not None
