"""
Compiler Optimizer 模块测试 - 修复版本
"""

import pytest
from intentos.compiler.optimizer import (
    CompilationStrategy,
    TokenOptimizer,
    ContextManager,
    PromptOptimizer,
)


class TestCompilationStrategy:
    """CompilationStrategy 测试"""

    def test_strategy_creation(self):
        strategy = CompilationStrategy(name="test", max_tokens=1000)
        assert strategy.name == "test"
        assert strategy.max_tokens == 1000

    def test_strategy_default_max_tokens(self):
        strategy = CompilationStrategy(name="default")
        assert strategy.max_tokens == 4096

    def test_strategy_to_dict(self):
        strategy = CompilationStrategy(name="dict_test", max_tokens=500)
        data = strategy.to_dict()
        assert data["name"] == "dict_test"
        assert data["max_tokens"] == 500


class TestTokenOptimizer:
    """TokenOptimizer 测试"""

    def test_optimizer_creation(self):
        optimizer = TokenOptimizer()
        assert optimizer is not None

    def test_count_tokens(self):
        optimizer = TokenOptimizer()
        count = optimizer.count_tokens("Hello world")
        assert count > 0

    def test_count_tokens_empty(self):
        optimizer = TokenOptimizer()
        count = optimizer.count_tokens("")
        assert count == 0

    def test_truncate_text(self):
        optimizer = TokenOptimizer()
        text = "word " * 100
        truncated = optimizer.truncate_text(text, max_tokens=10)
        assert len(truncated) < len(text)

    def test_truncate_text_short(self):
        optimizer = TokenOptimizer()
        text = "short"
        truncated = optimizer.truncate_text(text, max_tokens=100)
        assert truncated == text

    def test_estimate_tokens(self):
        optimizer = TokenOptimizer()
        estimate = optimizer.estimate_tokens("Hello world test")
        assert estimate > 0


class TestContextManager:
    """ContextManager 测试"""

    def test_manager_creation(self):
        manager = ContextManager()
        assert manager.context == {}

    def test_add_context(self):
        manager = ContextManager()
        manager.add_context("key", "value")
        assert manager.context["key"] == "value"

    def test_get_context(self):
        manager = ContextManager()
        manager.add_context("key", "value")
        value = manager.get_context("key")
        assert value == "value"

    def test_get_context_nonexistent(self):
        manager = ContextManager()
        value = manager.get_context("nonexistent")
        assert value is None

    def test_get_context_with_default(self):
        manager = ContextManager()
        value = manager.get_context("nonexistent", default="default")
        assert value == "default"

    def test_clear_context(self):
        manager = ContextManager()
        manager.add_context("key1", "value1")
        manager.clear()
        assert len(manager.context) == 0

    def test_remove_context(self):
        manager = ContextManager()
        manager.add_context("key", "value")
        manager.remove_context("key")
        assert "key" not in manager.context

    def test_has_context(self):
        manager = ContextManager()
        manager.add_context("key", "value")
        assert manager.has_context("key") is True
        assert manager.has_context("nonexistent") is False

    def test_get_all_context(self):
        manager = ContextManager()
        manager.add_context("key1", "value1")
        all_ctx = manager.get_all_context()
        assert len(all_ctx) == 1


class TestPromptOptimizer:
    """PromptOptimizer 测试"""

    def test_optimizer_creation(self):
        optimizer = PromptOptimizer()
        assert optimizer is not None

    def test_optimize_prompt(self):
        optimizer = PromptOptimizer()
        prompt = "Test prompt"
        optimized = optimizer.optimize(prompt)
        assert optimized is not None

    def test_optimize_empty_prompt(self):
        optimizer = PromptOptimizer()
        optimized = optimizer.optimize("")
        assert optimized is not None

    def test_apply_optimizations(self):
        optimizer = PromptOptimizer()
        prompt = "Test prompt"
        result = optimizer.apply_optimizations(prompt, ["remove_redundancy"])
        assert result is not None

    def test_get_optimization_suggestions(self):
        optimizer = PromptOptimizer()
        prompt = "Long prompt " * 50
        suggestions = optimizer.get_optimization_suggestions(prompt)
        assert isinstance(suggestions, list)


class TestOptimizerIntegration:
    """Optimizer 集成测试"""

    def test_full_optimization_workflow(self):
        optimizer = PromptOptimizer()
        token_opt = TokenOptimizer()
        context_mgr = ContextManager()
        
        context_mgr.add_context("user", "test")
        strategy = CompilationStrategy(name="integration", max_tokens=500)
        prompt = "Test optimization workflow"
        optimized = optimizer.optimize(prompt, strategy=strategy)
        token_count = token_opt.count_tokens(optimized)
        
        assert optimized is not None
        assert token_count > 0

    def test_context_and_token_optimizer(self):
        context_mgr = ContextManager()
        optimizer = TokenOptimizer()
        
        context_mgr.add_context("prompt", "Test prompt")
        prompt = context_mgr.get_context("prompt")
        tokens = optimizer.count_tokens(prompt)
        assert tokens > 0

    def test_strategy_and_prompt_optimizer(self):
        strategy = CompilationStrategy(name="test", max_tokens=1000)
        optimizer = PromptOptimizer()
        
        prompt = "Test with strategy"
        optimized = optimizer.optimize(prompt, strategy=strategy)
        assert len(optimized) <= len(prompt) * 2
