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
        
        # ========== 系统工具 ==========
        
        # Shell 执行
        def shell_execute(command: str, timeout: int = 30, shell: str = "bash") -> dict:
            """执行 Shell 命令"""
            import subprocess
            import shlex
            
            try:
                # 安全处理命令
                if isinstance(command, str):
                    args = shlex.split(command)
                else:
                    args = command
                
                # 执行命令
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=(shell == "bash"),
                )
                
                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": command,
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"命令执行超时（{timeout}秒）",
                    "command": command,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "command": command,
                }
        
        self.register(
            id="shell",
            name="Shell 命令",
            description="执行 Shell 命令（支持 bash/zsh）",
            handler=shell_execute,
            tags=["system", "shell", "command"],
            params_schema={
                "command": {"type": "string", "description": "要执行的命令"},
                "timeout": {"type": "number", "default": 30, "description": "超时时间（秒）"},
                "shell": {"type": "string", "default": "bash", "description": "Shell 类型"},
            }
        )
        
        # ========== 计算工具 ==========
        
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
        
        # ========== 文件工具 ==========
        
        # 文件读取
        def file_read(path: str) -> dict:
            try:
                with open(path) as f:
                    content = f.read()
                return {"path": path, "content": content[:10000]}  # 限制 10KB
            except Exception as e:
                return {"error": str(e)}
        
        self.register(
            id="file_read",
            name="读取文件",
            description="读取文件内容",
            handler=file_read,
            tags=["file", "io"],
        )
        
        # 文件写入
        def file_write(path: str, content: str, mode: str = "w") -> dict:
            try:
                with open(path, mode) as f:
                    f.write(content)
                return {"path": path, "success": True, "bytes": len(content)}
            except Exception as e:
                return {"error": str(e)}
        
        self.register(
            id="file_write",
            name="写入文件",
            description="写入文件内容",
            handler=file_write,
            tags=["file", "io"],
        )
        
        # 文件列表
        def file_list(path: str = ".") -> dict:
            try:
                import os
                files = os.listdir(path)
                return {
                    "path": path,
                    "files": files,
                    "count": len(files),
                }
            except Exception as e:
                return {"error": str(e)}
        
        self.register(
            id="file_list",
            name="列出文件",
            description="列出目录中的文件",
            handler=file_list,
            tags=["file", "io"],
        )
        
        # ========== 网络工具 ==========
        
        # HTTP 请求
        def http_request(
            url: str,
            method: str = "GET",
            headers: dict = None,
            body: str = None,
            timeout: int = 30
        ) -> dict:
            """发送 HTTP 请求"""
            try:
                import urllib.request
                import urllib.error
                import json
                
                # 创建请求
                req = urllib.request.Request(url, method=method)
                
                if headers:
                    for key, value in headers.items():
                        req.add_header(key, value)
                
                if body and method in ["POST", "PUT", "PATCH"]:
                    if isinstance(body, dict):
                        body = json.dumps(body)
                    req.data = body.encode()
                
                # 发送请求
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    content = response.read().decode()
                    try:
                        content = json.loads(content)
                    except:
                        pass
                    
                    return {
                        "success": True,
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body": content,
                    }
            except urllib.error.HTTPError as e:
                return {
                    "success": False,
                    "status": e.code,
                    "error": str(e),
                }
            except Exception as e:
                return {"error": str(e)}
        
        self.register(
            id="http_request",
            name="HTTP 请求",
            description="发送 HTTP/HTTPS 请求",
            handler=http_request,
            tags=["network", "http", "api"],
        )
        
        # ========== 其他工具 ==========
        
        # 当前时间
        def get_current_time() -> dict:
            from datetime import datetime
            now = datetime.now()
            return {
                "datetime": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "timezone": "local",
            }
        
        self.register(
            id="current_time",
            name="当前时间",
            description="获取当前日期和时间",
            handler=get_current_time,
            tags=["system", "time"],
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
