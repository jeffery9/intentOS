"""
IntentOS 内核执行引擎

AI Agent 通过内核执行，而不是独立运行
"""

from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass, field

from ..core import Intent, Context, IntentType
from ..semantic_vm import SemanticVM
from ..engine import ExecutionEngine
from ..registry import IntentRegistry


@dataclass
class ExecutionRequest:
    """执行请求"""
    intent: str
    context: Context
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResponse:
    """执行响应"""
    success: bool
    result: Any
    message: str
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


from ..kernel.core import KernelMode, UserMode, PrivilegeLevel

class KernelEngine:
    """
    内核执行引擎
    
    AI Agent 通过内核执行意图：
    1. 用户输入 → TUI
    2. TUI → Kernel Engine
    3. Kernel Engine → IntentOS 内核 (Semantic VM)
    4. 结果 → TUI
    """
    
    def __init__(self):
        self.registry = IntentRegistry()
        self.vm = SemanticVM()
        self.engine = ExecutionEngine(self.registry)
        
        # 内核/用户隔离
        self.kernel = KernelMode()
        self.user_space = UserMode(self.kernel)
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化内核"""
        # 注册内置能力
        self._register_builtin_capabilities()
        
        # 初始化语义 VM
        await self.vm.initialize()
        
        self._initialized = True
    
    def _register_builtin_capabilities(self) -> None:
        """注册内置能力"""
        from ..core import Capability
        
        # 日程管理能力
        def schedule_capability(context: Context, **kwargs):
            return {
                "success": True,
                "action": "schedule",
                "data": kwargs,
            }
        
        self.registry.register_capability(Capability(
            name="schedule",
            description="安排日程",
            input_schema={"time": "string", "event": "string"},
            func=schedule_capability,
        ))
        
        # 数据分析能力
        def analysis_capability(context: Context, **kwargs):
            return {
                "success": True,
                "action": "analysis",
                "data": kwargs,
            }
        
        self.registry.register_capability(Capability(
            name="analysis",
            description="数据分析",
            input_schema={"data": "string", "type": "string"},
            func=analysis_capability,
        ))
        
        # 内容创作能力
        def writing_capability(context: Context, **kwargs):
            return {
                "success": True,
                "action": "writing",
                "data": kwargs,
            }
        
        self.registry.register_capability(Capability(
            name="writing",
            description="内容创作",
            input_schema={"topic": "string", "type": "string"},
            func=writing_capability,
        ))
    
    async def execute(
        self,
        request: ExecutionRequest
    ) -> ExecutionResponse:
        """
        执行请求
        
        流程:
        1. 解析意图
        2. 编译为 PEF
        3. 通过语义 VM 执行
        4. 返回结果
        """
        try:
            # 1. 创建意图对象
            intent = Intent(
                name="user_request",
                intent_type=IntentType.ATOMIC,
                goal=request.intent,
                context=request.context,
                params=request.metadata,
            )
            
            # 2. 通过内核执行
            result = await self.engine.execute(intent)
            
            return ExecutionResponse(
                success=True,
                result=result,
                message="执行成功",
                metadata={"intent_type": intent.intent_type.value},
            )
            
        except Exception as e:
            return ExecutionResponse(
                success=False,
                result=None,
                message=str(e),
                error=type(e).__name__,
            )
    
    def get_status(self) -> dict[str, Any]:
        """获取内核状态"""
        return {
            "initialized": self._initialized,
            "registry": {
                "capabilities": len(self.registry.list_capabilities()),
                "templates": len(self.registry.list_templates()),
            },
            "vm": {
                "status": "running" if self._initialized else "stopped",
            },
        }


# ========== 单例 ==========

_kernel: Optional[KernelEngine] = None


def get_kernel() -> KernelEngine:
    """获取内核单例"""
    global _kernel
    if _kernel is None:
        _kernel = KernelEngine()
    return _kernel


async def initialize_kernel() -> KernelEngine:
    """初始化内核"""
    kernel = get_kernel()
    await kernel.initialize()
    return kernel
