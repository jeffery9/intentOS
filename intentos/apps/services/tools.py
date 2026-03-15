"""
工具注册系统

为 AI Agent 提供外部工具调用能力
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional
from dataclasses import dataclass, field


@dataclass
class ToolDefinition:
    """工具定义"""
    id: str
    name: str
    description: str
    handler: Callable
    params_schema: dict[str, Any] = field(default_factory=dict)
    returns_schema: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    enabled: bool = True


class ToolRegistry:
    """
    工具注册表
    
    注册和管理可调用的工具
    """
    
    _instance: Optional["ToolRegistry"] = None
    
    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.tools: dict[str, ToolDefinition] = {}
        self._register_builtin_tools()
        self._initialized = True
    
    def register(
        self,
        id: str,
        name: str,
        description: str,
        handler: Callable,
        params_schema: dict = None,
        tags: list[str] = None
    ) -> ToolDefinition:
        """注册工具"""
        tool = ToolDefinition(
            id=id,
            name=name,
            description=description,
            handler=handler,
            params_schema=params_schema or {},
            tags=tags or [],
        )
        
        self.tools[id] = tool
        return tool
    
    def unregister(self, tool_id: str) -> bool:
        """注销工具"""
        if tool_id in self.tools:
            del self.tools[tool_id]
            return True
        return False
    
    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """获取工具"""
        return self.tools.get(tool_id)
    
    def list_tools(self, tags: list[str] = None) -> list[ToolDefinition]:
        """列出工具"""
        tools = list(self.tools.values())
        
        if tags:
            tools = [
                t for t in tools
                if any(tag in t.tags for tag in tags)
            ]
        
        return [t for t in tools if t.enabled]
    
    async def call(
        self,
        tool_id: str,
        **kwargs
    ) -> Any:
        """调用工具"""
        tool = self.get_tool(tool_id)
        
        if not tool:
            return {"error": f"工具不存在：{tool_id}"}
        
        if not tool.enabled:
            return {"error": f"工具已禁用：{tool_id}"}
        
        try:
            # 调用处理函数
            result = tool.handler(**kwargs)
            
            # 如果是协程，等待结果
            if asyncio.iscoroutine(result):
                result = await result
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        
        # 计算器
        def calculator(expression: str) -> dict:
            try:
                result = eval(expression, {"__builtins__": {}}, {})
                return {"expression": expression, "result": result}
            except Exception as e:
                return {"error": str(e)}
        
        self.register(
            id="calculator",
            name="计算器",
            description="执行数学计算",
            handler=calculator,
            tags=["math", "calculation"],
        )
        
        # 天气查询（Mock）
        def weather(city: str) -> dict:
            return {
                "city": city,
                "temperature": "25°C",
                "condition": "晴",
                "humidity": "60%",
            }
        
        self.register(
            id="weather",
            name="天气查询",
            description="查询天气信息",
            handler=weather,
            tags=["weather", "query"],
        )
        
        # 新闻查询（Mock）
        def news(category: str = "tech") -> dict:
            return {
                "category": category,
                "headlines": [
                    "AI 技术新突破",
                    "科技公司发展动态",
                    "行业趋势分析",
                ],
            }
        
        self.register(
            id="news",
            name="新闻查询",
            description="查询最新新闻",
            handler=news,
            tags=["news", "query"],
        )
        
        # 文件操作
        def file_read(path: str) -> dict:
            try:
                with open(path) as f:
                    content = f.read()
                return {"path": path, "content": content[:1000]}
            except Exception as e:
                return {"error": str(e)}
        
        self.register(
            id="file_read",
            name="读取文件",
            description="读取文件内容",
            handler=file_read,
            tags=["file", "io"],
        )
        
        # 网页搜索（Mock）
        def web_search(query: str) -> dict:
            return {
                "query": query,
                "results": [
                    {"title": f"结果 1: {query}", "url": "https://example.com/1"},
                    {"title": f"结果 2: {query}", "url": "https://example.com/2"},
                ],
            }
        
        self.register(
            id="web_search",
            name="网页搜索",
            description="搜索网页内容",
            handler=web_search,
            tags=["search", "web"],
        )


# ========== 便捷函数 ==========

def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例"""
    return ToolRegistry()


def register_tool(
    id: str,
    name: str,
    description: str,
    tags: list[str] = None
):
    """
    工具注册装饰器
    
    用法:
        @register_tool("my_tool", "我的工具", "描述")
        def my_tool_handler(param1: str) -> dict:
            ...
    """
    def decorator(handler: Callable) -> Callable:
        registry = get_tool_registry()
        registry.register(
            id=id,
            name=name,
            description=description,
            handler=handler,
            tags=tags,
        )
        return handler
    return decorator
