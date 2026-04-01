# -*- coding: utf-8 -*-
"""
IntentOS Evolution Layer Tests

测试进化层（记忆 - 冥想 - 技能集成）
"""

import pytest
import asyncio
from datetime import datetime

from intentos.evolution.evolution_engine import EvolutionEngine, EvolutionConfig, EvolutionStats
from intentos.evolution.session_manager import SessionManager, SessionContext
from intentos.memory.models import MemoryEntry, MemoryContentType, Pattern


class TestEvolutionConfig:
    """测试进化配置"""

    def test_default_config(self):
        """默认配置"""
        config = EvolutionConfig()
        
        assert config.meditation_threshold == 5
        assert config.skill_min_quality == 0.6
        assert config.auto_review is True
        assert config.auto_meditate is True

    def test_custom_config(self):
        """自定义配置"""
        config = EvolutionConfig(
            meditation_threshold=3,
            skill_min_quality=0.8,
            auto_review=False,
        )
        
        assert config.meditation_threshold == 3
        assert config.skill_min_quality == 0.8
        assert config.auto_review is False


class TestEvolutionStats:
    """测试进化统计"""

    def test_stats_creation(self):
        """创建统计"""
        stats = EvolutionStats()
        
        assert stats.total_sessions == 0
        assert stats.created_at is not None
    
    def test_stats_to_dict(self):
        """统计序列化"""
        stats = EvolutionStats(
            total_sessions=10,
            completed_sessions=8,
            skills_created=3,
        )
        
        data = stats.to_dict()
        
        assert data["total_sessions"] == 10
        assert data["completed_sessions"] == 8
        assert data["skills_created"] == 3


class TestEvolutionEngine:
    """测试进化引擎"""

    @pytest.fixture
    def engine(self):
        """创建测试引擎"""
        config = EvolutionConfig(
            meditation_threshold=2,  # 降低阈值便于测试
            auto_meditate=False,  # 测试时不自动冥想
            auto_skillify=False,
        )
        engine = EvolutionEngine(config)
        yield engine
    
    def test_engine_init(self, engine):
        """引擎初始化"""
        assert engine.stats is not None
        assert engine.memory_store is not None
        assert engine.skill_store is not None
    
    def test_start_session(self, engine):
        """开始会话"""
        session_id = engine.start_session(user_id="test_user")
        
        assert session_id is not None
        assert engine.current_session_id == session_id
        assert engine.stats.total_sessions == 1
    
    def test_add_message(self, engine):
        """添加消息"""
        engine.start_session()
        
        engine.add_message("user", "你好")
        engine.add_message("assistant", "有什么可以帮助你的？")
        
        assert len(engine.current_session.memory.messages) == 2
    
    def test_end_session(self, engine):
        """结束会话"""
        session_id = engine.start_session()
        
        engine.add_message("user", "测试消息")
        
        result = engine.end_session()
        
        assert result["session_id"] == session_id
        assert result["memories_created"] >= 0
        assert engine.current_session is None
        assert engine.stats.completed_sessions == 1
    
    def test_full_session_cycle(self, engine):
        """完整会话周期"""
        # 开始会话
        session_id = engine.start_session(user_id="test_user")
        
        # 添加对话
        engine.add_message("user", "如何分析数据？")
        engine.add_message("assistant", "第一步：加载数据")
        engine.add_message("assistant", "第二步：清洗数据")
        engine.add_message("assistant", "第三步：执行分析")
        engine.add_message("user", "成功了，谢谢")
        
        # 结束会话
        result = engine.end_session()
        
        assert result["session_id"] == session_id
        assert engine.stats.completed_sessions == 1
    
    def test_find_matching_skills(self, engine):
        """查找匹配技能"""
        # 没有技能时返回空
        results = engine.find_matching_skills("分析数据")
        assert isinstance(results, list)
    
    def test_get_stats(self, engine):
        """获取统计"""
        engine.start_session()
        engine.add_message("user", "测试")
        engine.end_session()
        
        stats = engine.get_stats()
        
        assert "total_sessions" in stats
        assert "memory" in stats
        assert "skills" in stats


class TestSessionManager:
    """测试会话管理器"""

    @pytest.fixture
    def manager(self):
        """创建会话管理器"""
        return SessionManager()
    
    def test_create_session(self, manager):
        """创建会话"""
        context = manager.create_session(user_id="user_001")
        
        assert context.session_id is not None
        assert context.user_id == "user_001"
        assert context.is_active is True
    
    def test_get_session(self, manager):
        """获取会话"""
        context = manager.create_session(user_id="user_001")
        
        retrieved = manager.get_session(context.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == context.session_id
    
    def test_add_message(self, manager):
        """添加消息"""
        context = manager.create_session(user_id="user_001")
        
        manager.add_message(context.session_id, "user", "你好")
        manager.add_message(context.session_id, "assistant", "你好！")
        
        assert len(context.messages) == 2
    
    def test_end_session(self, manager):
        """结束会话"""
        context = manager.create_session(user_id="user_001")
        
        result = manager.end_session(context.session_id)
        
        assert result is True
        assert context.is_active is False
        assert context.end_time is not None
        assert context.session_id not in manager.active_sessions
    
    def test_get_user_sessions(self, manager):
        """获取用户会话列表"""
        # 创建多个会话
        for i in range(3):
            manager.create_session(user_id="user_001")
        
        sessions = manager.get_user_sessions("user_001", limit=10)
        
        assert len(sessions) == 3
    
    def test_get_active_session_count(self, manager):
        """获取活跃会话数"""
        manager.create_session(user_id="user_001")
        manager.create_session(user_id="user_002")
        
        count = manager.get_active_session_count()
        
        assert count == 2
    
    def test_session_context_methods(self):
        """测试会话上下文方法"""
        context = SessionContext(
            session_id="test_001",
            user_id="user_001",
        )
        
        # 添加消息
        context.add_message("user", "测试")
        assert len(context.messages) == 1
        
        # 添加记忆
        context.add_memory("memory_001")
        assert "memory_001" in context.memory_ids
        
        # 添加技能
        context.add_skill("skill_001")
        assert "skill_001" in context.skills_used
        
        # 结束会话
        context.end()
        assert context.is_active is False
        assert context.end_time is not None
    
    def test_get_stats(self, manager):
        """获取统计"""
        manager.create_session(user_id="user_001")
        manager.create_session(user_id="user_002")
        
        stats = manager.get_stats()
        
        assert stats["active_sessions"] == 2
        assert stats["total_sessions"] == 2
        assert stats["users"] == 2


class TestEvolutionIntegration:
    """进化层集成测试"""

    def test_memory_meditation_skill_flow(self):
        """记忆 - 冥想 - 技能完整流程"""
        config = EvolutionConfig(
            meditation_threshold=2,
            auto_meditate=False,  # 手动控制
            auto_skillify=False,
        )
        engine = EvolutionEngine(config)
        
        # 会话 1
        session1 = engine.start_session(user_id="test")
        engine.add_message("user", "如何分析数据？")
        engine.add_message("assistant", "使用 Python pandas 加载数据")
        engine.add_message("assistant", "执行 describe() 获取统计")
        engine.end_session()
        
        # 会话 2
        session2 = engine.start_session(user_id="test")
        engine.add_message("user", "数据可视化怎么做？")
        engine.add_message("assistant", "使用 matplotlib 绘制图表")
        engine.end_session()
        
        # 检查冥想是否被触发（应该达到阈值）
        assert engine.meditation_engine.get_pending_count() == 2
        
        # 手动执行冥想
        result = asyncio.run(engine.meditate())
        
        assert result.sessions_processed == 2
        assert engine.stats.meditations_triggered == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
