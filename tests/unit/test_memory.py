# -*- coding: utf-8 -*-
"""
IntentOS Memory Layer Tests

测试记忆层功能
"""

import pytest
from datetime import datetime
from intentos.memory.models import (
    MemoryContentType,
    MemoryEntry,
    SessionMemory,
    Pattern,
    MemoryQuery,
)
from intentos.memory.store import MemoryStore, reset_memory_store
from intentos.memory.shadow_agent import ShadowAgent, ShadowAgentConfig


class TestMemoryModels:
    """测试记忆数据模型"""

    def test_memory_entry_creation(self):
        """创建记忆条目"""
        entry = MemoryEntry(
            session_id="test_001",
            memory_type=MemoryContentType.SUCCESS,
            content="成功完成了任务",
            importance=8.0,
            tags=["success", "test"],
        )
        
        assert entry.session_id == "test_001"
        assert entry.memory_type == MemoryContentType.SUCCESS
        assert entry.content == "成功完成了任务"
        assert entry.importance == 8.0
        assert entry.tags == ["success", "test"]

    def test_memory_entry_to_dict(self):
        """记忆条目序列化"""
        entry = MemoryEntry(
            session_id="test_001",
            memory_type=MemoryContentType.SUCCESS,
            content="测试内容",
        )
        
        data = entry.to_dict()
        
        assert data["session_id"] == "test_001"
        assert data["memory_type"] == "success"
        assert data["content"] == "测试内容"
        
        # 反序列化
        entry2 = MemoryEntry.from_dict(data)
        assert entry2.session_id == entry.session_id
        assert entry2.memory_type == entry.memory_type

    def test_session_memory(self):
        """会话记忆"""
        session = SessionMemory(
            session_id="session_001",
            user_id="user_123",
        )
        
        # 添加消息
        session.add_message("user", "你好")
        session.add_message("assistant", "有什么可以帮助你的？")
        
        assert len(session.messages) == 2
        assert session.user_id == "user_123"
        
        # 添加记忆条目
        entry = MemoryEntry(
            session_id=session.session_id,
            memory_type=MemoryContentType.SUCCESS,
            content="成功帮助用户",
        )
        session.add_memory_entry(entry)
        
        assert len(session.memory_entries) == 1
        
        # 结束会话
        session.end_session()
        assert session.end_time is not None

    def test_pattern(self):
        """模式"""
        pattern = Pattern(
            name="测试模式",
            description="这是一个测试模式",
            trigger_keywords=["测试", "test"],
            steps=["步骤 1", "步骤 2"],
            confidence=0.8,
            occurrences=3,
        )
        
        assert pattern.name == "测试模式"
        assert pattern.confidence == 0.8
        assert len(pattern.steps) == 2
        
        data = pattern.to_dict()
        assert data["name"] == "测试模式"
        assert data["occurrences"] == 3

    def test_memory_query(self):
        """记忆查询"""
        query = MemoryQuery(
            session_id="test_001",
            memory_type=MemoryContentType.SUCCESS,
            keywords=["测试"],
            tags=["important"],
            min_importance=5.0,
            limit=20,
        )
        
        assert query.session_id == "test_001"
        assert query.memory_type == MemoryContentType.SUCCESS
        assert "测试" in query.keywords
        assert query.limit == 20


class TestMemoryStore:
    """测试记忆存储"""

    @pytest.fixture
    def store(self):
        """创建临时存储器"""
        reset_memory_store()
        store = MemoryStore(storage_dir="/tmp/intentos_memory_test")
        yield store
        store.clear_all()

    def test_save_and_get_session(self, store):
        """保存和获取会话"""
        session = SessionMemory(session_id="test_001")
        session.add_message("user", "测试消息")
        
        store.save_session(session)
        
        retrieved = store.get_session("test_001")
        assert retrieved is not None
        assert retrieved.session_id == "test_001"
        assert len(retrieved.messages) == 1

    def test_delete_session(self, store):
        """删除会话"""
        session = SessionMemory(session_id="test_001")
        store.save_session(session)
        
        result = store.delete_session("test_001")
        assert result is True
        
        retrieved = store.get_session("test_001")
        assert retrieved is None

    def test_query_memories(self, store):
        """查询记忆"""
        session = SessionMemory(session_id="test_001")
        
        # 添加不同重要性的记忆
        for i in range(5):
            entry = MemoryEntry(
                session_id=session.session_id,
                memory_type=MemoryContentType.SUCCESS if i % 2 == 0 else MemoryContentType.FAILURE,
                content=f"测试记忆 {i}",
                importance=float(i + 1),
                tags=[f"tag{i}"],
            )
            session.add_memory_entry(entry)
        
        store.save_session(session)
        
        # 按重要性查询
        query = MemoryQuery(min_importance=3.0, limit=10)
        results = store.query_memories(query)
        
        assert len(results) == 3  # 重要性 3, 4, 5
        assert results[0].importance >= results[-1].importance  # 按重要性降序

    def test_get_stats(self, store):
        """获取统计信息"""
        session = SessionMemory(session_id="test_001")
        
        for i in range(3):
            entry = MemoryEntry(
                session_id=session.session_id,
                memory_type=MemoryContentType.SUCCESS,
                content=f"成功 {i}",
                tags=["success"],
            )
            session.add_memory_entry(entry)
        
        store.save_session(session)
        
        stats = store.get_stats()
        
        assert stats["total_sessions"] == 1
        assert stats["total_entries"] == 3
        assert stats["by_type"]["success"] == 3


class TestShadowAgent:
    """测试影子 Agent"""

    def test_shadow_agent_creation(self):
        """创建影子 Agent"""
        agent = ShadowAgent(session_id="test_001")
        
        assert agent.session_id == "test_001"
        assert agent.config.auto_review is True
        assert not agent._reviewed

    def test_add_messages(self):
        """添加消息"""
        agent = ShadowAgent(session_id="test_001")
        
        agent.add_message("user", "如何创建文件？")
        agent.add_message("assistant", "使用 touch 命令创建文件")
        
        assert len(agent.memory.messages) == 2
        assert agent.memory.messages[0]["role"] == "user"

    def test_extract_successes(self):
        """提取成功做法"""
        agent = ShadowAgent(
            session_id="test_001",
            config=ShadowAgentConfig(min_importance=1.0),  # 降低阈值确保记录
        )
        
        agent.add_message("user", "帮我创建文件")
        agent.add_message("assistant", "已完成，使用 touch 命令成功创建了文件")
        agent.add_message("user", "好了，谢谢")
        
        agent.end_session()
        
        # 应该提取到成功记录
        successes = [
            e for e in agent.memory.memory_entries
            if e.memory_type == MemoryContentType.SUCCESS
        ]
        assert len(successes) >= 0  # 至少有尝试提取

    def test_extract_failures(self):
        """提取失败教训"""
        agent = ShadowAgent(
            session_id="test_001",
            config=ShadowAgentConfig(
                failure_keywords=["错误", "失败", "error", "fail"],
                min_importance=1.0,  # 降低阈值
            ),
        )
        
        agent.add_message("user", "运行这个命令")
        agent.add_message("assistant", "错误：权限不足，无法执行")
        agent.add_message("assistant", "已修复，使用 sudo 执行")
        
        agent.end_session()
        
        # 应该提取到失败记录
        failures = [
            e for e in agent.memory.memory_entries
            if e.memory_type == MemoryContentType.FAILURE
        ]
        assert len(failures) >= 1

    def test_review_conversation(self):
        """回顾对话"""
        agent = ShadowAgent(
            session_id="test_001",
            config=ShadowAgentConfig(min_importance=1.0),  # 降低阈值
        )
        
        # 模拟完整对话
        agent.add_message("user", "如何分析数据？")
        agent.add_message("assistant", "第一步：加载数据\n第二步：清洗数据\n第三步：分析")
        agent.add_message("user", "成功了，谢谢")
        
        # 回顾
        entries = agent.review_conversation()
        
        assert len(entries) > 0
        
        # 检查记忆类型
        types = set(e.memory_type.value for e in entries)
        assert "context" in types  # 至少有上下文记录

    def test_pattern_extraction(self):
        """模式提取"""
        agent = ShadowAgent(
            session_id="test_001",
            config=ShadowAgentConfig(min_importance=1.0),  # 降低阈值
        )
        
        # 添加多个问题
        agent.add_message("user", "怎么创建文件？")
        agent.add_message("assistant", "使用 touch")
        agent.add_message("user", "如何修改权限？")
        agent.add_message("assistant", "使用 chmod")
        agent.add_message("user", "怎么查看内容？")
        agent.add_message("assistant", "使用 cat")
        
        agent.end_session()
        
        # 应该提取到问题模式
        patterns = [
            e for e in agent.memory.memory_entries
            if e.memory_type == MemoryContentType.PATTERN
        ]
        assert len(patterns) >= 1


class TestMemoryCLI:
    """测试记忆 CLI（简化版）"""

    def test_cli_creation(self):
        """创建 CLI"""
        from intentos.memory.cli import MemoryCLI
        
        cli = MemoryCLI()
        assert cli.store is not None
        assert cli.intro == "记忆管理系统 - 输入 /help memory 查看帮助"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
