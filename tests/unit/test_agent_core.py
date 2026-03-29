"""
Agent Core Module Tests

测试 Agent 核心配置、上下文和结果处理
"""

import pytest
from datetime import datetime

from intentos.agent.core import (
    AgentConfig,
    AgentContext,
    AgentResult,
    Agent,
)


class TestAgentConfig:
    """测试 Agent 配置"""

    def test_default_config(self):
        """默认配置"""
        config = AgentConfig()
        
        assert config.name == "IntentOS Agent"
        assert config.version == "1.0.0"
        assert config.description == "AI 智能助理"
        assert config.capabilities == []
        assert config.max_iterations == 10
        assert config.timeout == 300
        assert config.enable_mcp is True
        assert config.enable_skills is True

    def test_custom_config(self):
        """自定义配置"""
        config = AgentConfig(
            name="Custom Agent",
            version="2.0.0",
            description="Custom description",
            capabilities=["shell", "file"],
            max_iterations=20,
            timeout=600,
            enable_mcp=False,
            enable_skills=False
        )
        
        assert config.name == "Custom Agent"
        assert config.version == "2.0.0"
        assert config.description == "Custom description"
        assert len(config.capabilities) == 2
        assert config.max_iterations == 20
        assert config.timeout == 600
        assert config.enable_mcp is False
        assert config.enable_skills is False

    def test_config_capabilities(self):
        """配置能力列表"""
        config = AgentConfig(capabilities=["cap1", "cap2", "cap3"])
        
        assert len(config.capabilities) == 3
        assert "cap1" in config.capabilities


class TestAgentContext:
    """测试 Agent 上下文"""

    def test_create_context(self):
        """创建上下文"""
        context = AgentContext(user_id="user123")
        
        assert context.user_id == "user123"
        assert context.session_id == ""
        assert context.conversation_history == []
        assert context.variables == {}
        assert context.created_at is not None

    def test_context_with_session(self):
        """带会话的上下文"""
        context = AgentContext(
            user_id="user123",
            session_id="session456",
            variables={"key": "value"}
        )
        
        assert context.session_id == "session456"
        assert context.variables["key"] == "value"

    def test_context_with_history(self):
        """带历史记录的上下文"""
        context = AgentContext(
            user_id="user123",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ]
        )
        
        assert len(context.conversation_history) == 2

    def test_context_to_dict(self):
        """上下文转换为字典"""
        context = AgentContext(
            user_id="user123",
            session_id="session456"
        )
        
        data = context.to_dict()
        
        assert isinstance(data, dict)
        assert data["user_id"] == "user123"
        assert data["session_id"] == "session456"
        assert "conversation_history" in data
        assert "variables" in data
        assert "created_at" in data


class TestAgentResult:
    """测试 Agent 结果"""

    def test_success_result(self):
        """成功结果"""
        result = AgentResult(
            success=True,
            message="操作成功",
            data={"key": "value"}
        )
        
        assert result.success is True
        assert result.message == "操作成功"
        assert result.data["key"] == "value"
        assert result.error is None

    def test_failure_result(self):
        """失败结果"""
        result = AgentResult(
            success=False,
            message="操作失败",
            error="ErrorType: Something went wrong"
        )
        
        assert result.success is False
        assert result.message == "操作失败"
        assert result.error is not None
        assert "ErrorType" in result.error

    def test_result_with_artifacts(self):
        """带产物的结果"""
        result = AgentResult(
            success=True,
            message="完成",
            artifacts=[
                {"type": "file", "path": "/tmp/test.txt"},
                {"type": "data", "content": "result"}
            ]
        )
        
        assert len(result.artifacts) == 2

    def test_result_with_next_actions(self):
        """带后续动作的结果"""
        result = AgentResult(
            success=True,
            message="部分完成",
            next_actions=["step1", "step2", "step3"]
        )
        
        assert len(result.next_actions) == 3

    def test_result_to_dict(self):
        """结果转换为字典"""
        result = AgentResult(
            success=True,
            message="成功",
            data={"result": "data"},
            artifacts=["artifact1"],
            next_actions=["action1"]
        )
        
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["success"] is True
        assert data["message"] == "成功"
        assert data["data"]["result"] == "data"
        assert len(data["artifacts"]) == 1
        assert len(data["next_actions"]) == 1


class TestAgentBase:
    """测试 Agent 基类"""

    def test_agent_initialization(self):
        """Agent 初始化"""
        from unittest.mock import MagicMock
        
        class MockAgent(Agent):
            async def execute(self, intent: str, context: AgentContext) -> AgentResult:
                return AgentResult(success=True, message="Mock")
        
        agent = MockAgent()
        
        assert agent._initialized is False
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_agent_initialize(self):
        """Agent 初始化方法"""
        from unittest.mock import MagicMock
        
        class MockAgent(Agent):
            async def execute(self, intent: str, context: AgentContext) -> AgentResult:
                return AgentResult(success=True, message="Mock")
        
        agent = MockAgent()
        result = await agent.initialize()
        
        assert result is True
        assert agent._initialized is True

    @pytest.mark.asyncio
    async def test_agent_execute(self):
        """Agent 执行"""
        from unittest.mock import MagicMock
        
        class MockAgent(Agent):
            async def execute(self, intent: str, context: AgentContext) -> AgentResult:
                return AgentResult(
                    success=True,
                    message=f"Executed: {intent}",
                    data={"intent": intent}
                )
        
        agent = MockAgent()
        context = AgentContext(user_id="test")
        result = await agent.execute("test intent", context)
        
        assert result.success is True
        assert "test intent" in result.message

    def test_agent_with_custom_config(self):
        """使用自定义配置的 Agent"""
        from unittest.mock import MagicMock
        
        class MockAgent(Agent):
            async def execute(self, intent: str, context: AgentContext) -> AgentResult:
                return AgentResult(success=True, message="Mock")
        
        config = AgentConfig(
            name="Test Agent",
            max_iterations=5,
            enable_mcp=False
        )
        agent = MockAgent(config=config)
        
        assert agent.config.name == "Test Agent"
        assert agent.config.max_iterations == 5
        assert agent.config.enable_mcp is False

    @pytest.mark.asyncio
    async def test_agent_double_initialize(self):
        """Agent 重复初始化"""
        from unittest.mock import MagicMock
        
        class MockAgent(Agent):
            async def execute(self, intent: str, context: AgentContext) -> AgentResult:
                return AgentResult(success=True, message="Mock")
        
        agent = MockAgent()
        
        await agent.initialize()
        assert agent._initialized is True
        
        # 再次初始化
        await agent.initialize()
        assert agent._initialized is True


class TestAgentContextVariables:
    """测试上下文变量"""

    def test_context_variable_assignment(self):
        """上下文变量赋值"""
        context = AgentContext(user_id="user1")
        context.variables["temp"] = 25
        context.variables["location"] = "Beijing"
        
        assert context.variables["temp"] == 25
        assert context.variables["location"] == "Beijing"

    def test_context_variable_update(self):
        """上下文变量更新"""
        context = AgentContext(
            user_id="user1",
            variables={"count": 1}
        )
        
        context.variables["count"] = 2
        context.variables["new_var"] = "value"
        
        assert context.variables["count"] == 2
        assert context.variables["new_var"] == "value"


class TestAgentResultEdgeCases:
    """测试 Agent 结果边界情况"""

    def test_empty_result(self):
        """空结果"""
        result = AgentResult(
            success=True,
            message=""
        )
        
        assert result.success is True
        assert result.message == ""
        assert result.data is None

    def test_none_data_result(self):
        """None 数据结果"""
        result = AgentResult(
            success=True,
            message="No data",
            data=None
        )
        
        assert result.data is None

    def test_empty_artifacts(self):
        """空产物列表"""
        result = AgentResult(
            success=True,
            message="Done",
            artifacts=[]
        )
        
        assert len(result.artifacts) == 0

    def test_empty_next_actions(self):
        """空后续动作列表"""
        result = AgentResult(
            success=True,
            message="Done",
            next_actions=[]
        )
        
        assert len(result.next_actions) == 0

    def test_result_to_dict_empty_fields(self):
        """空字段的字典转换"""
        result = AgentResult(
            success=True,
            message="Done"
        )
        
        data = result.to_dict()
        
        assert data["data"] is None
        assert data["error"] is None
        assert data["artifacts"] == []
        assert data["next_actions"] == []
