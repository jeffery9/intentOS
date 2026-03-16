"""
IntentOS 意图界面层
提供人类与 IntentOS 交互的接口
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..core import Context, Intent
from ..engine import ExecutionEngine
from ..parser import IntentParser
from ..registry import IntentRegistry


@dataclass
class ConversationTurn:
    """对话轮次"""

    role: str  # "user" or "system"
    content: str
    intent: Optional[Intent] = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)


from ..kernel.core import PrivilegeLevel

class IntentInterface:
    """
    意图界面
    人类与 IntentOS 交互的主接口
    """

    def __init__(self, registry: Optional[IntentRegistry] = None, mode: PrivilegeLevel = PrivilegeLevel.USER):
        self.registry = registry or IntentRegistry()
        self.parser = IntentParser(self.registry)
        self.engine = ExecutionEngine(self.registry)
        self.context = Context(user_id="anonymous")
        self.conversation_history: list[ConversationTurn] = []
        self.mode = mode

    def set_mode(self, mode: PrivilegeLevel) -> None:
        """设置执行模式"""
        self.mode = mode

    def set_user(
        self, user_id: str, role: str = "user", permissions: Optional[list[str]] = None
    ) -> None:
        """设置当前用户"""
        self.context = Context(
            user_id=user_id,
            user_role=role,
            permissions=permissions or [],
            history=[t.content for t in self.conversation_history],
        )
        
        # 自动切换模式：admin 角色进入内核态
        if role == "admin":
            self.mode = PrivilegeLevel.KERNEL
        else:
            self.mode = PrivilegeLevel.USER

    async def chat(self, text: str) -> str:
        """
        与 IntentOS 对话

        Args:
            text: 用户输入

        Returns:
            系统响应
        """
        # 记录用户输入
        self.conversation_history.append(
            ConversationTurn(
                role="user",
                content=text,
            )
        )

        # 解析意图
        intent = self.parser.parse(text, self.context)

        # 更新上下文历史
        self.context.history.append(text)

        # 执行意图 (传递执行模式)
        result = await self.engine.execute(intent, mode=self.mode)

        # 生成响应
        response = self._generate_response(intent, result)

        # 记录系统响应
        self.conversation_history.append(
            ConversationTurn(
                role="system",
                content=response,
                intent=intent,
            )
        )

        return response

    def _generate_response(self, intent: Intent, result: Any) -> str:
        """生成响应文本"""
        if result.success:
            return f"✅ 已完成：{intent.name}\n结果：{result.result}"
        else:
            return f"❌ 执行失败：{result.error}"

    def get_history(self) -> list[ConversationTurn]:
        """获取对话历史"""
        return self.conversation_history

    def clear_history(self) -> None:
        """清除对话历史"""
        self.conversation_history.clear()
        self.context.history.clear()


class IntentOS:
    """
    IntentOS 主类
    统一的系统入口
    """

    def __init__(self, llm_executor: Any = None):
        from ..bootstrap.executor import create_bootstrap_executor
        from ..distributed.vm import create_distributed_vm

        self.registry = IntentRegistry()
        self.vm = create_distributed_vm(llm_executor)
        self.bootstrap = create_bootstrap_executor(self.vm)
        self.interface = IntentInterface(self.registry)
        self._initialized = False
        self._running = False
        self._background_tasks: list = []

    def initialize(self) -> None:
        """初始化系统"""
        self._register_builtin_capabilities()
        self._register_builtin_templates()
        self._initialized = True
        self._running = True

    def shutdown(self) -> None:
        """关闭系统"""
        self._running = False
        # 清理后台任务
        for task in self._background_tasks:
            if hasattr(task, 'cancel'):
                task.cancel()
        self._background_tasks.clear()

    @property
    def is_running(self) -> bool:
        """检查系统是否正在运行"""
        return self._running

    async def _watchdog_task(self) -> None:
        """语义自愈监控任务"""
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("Semantic Watchdog started")
        while self._running:
            try:
                # 1. 检查 VM 状态
                if not self.vm or not self.vm.local_vm:
                    logger.error("VM or Local VM is missing!")
                    # 尝试恢复 (此处简化为记录)
                
                # 2. 检查内存一致性
                memory_state = self.vm.local_vm.memory.get_state()
                if memory_state["audit_log_count"] > 10000:
                    # 定期清理过大的审计日志
                    self.vm.local_vm.memory.audit_log = self.vm.local_vm.memory.audit_log[-1000:]
                    logger.info("Cleaned up old audit logs")

                # 3. 检查并清理僵尸进程 (分布式)
                # await self.vm.cleanup_zombie_processes()
                
                # 每 60 秒检查一次
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                await asyncio.sleep(10)

    async def start_background_services(self) -> None:
        """启动后台服务"""
        import asyncio
        if not self._running:
            return
            
        # 启动自愈监控
        watchdog = asyncio.create_task(self._watchdog_task())
        self._background_tasks.append(watchdog)
        
        # 启动其他云原生服务 (监控、心跳等)
        print("✅ Background services (Watchdog) started")

    def run_daemon(self) -> None:
        """
        以守护进程模式运行 OS
        持续运行直到被中断
        """
        import signal
        import sys

        def signal_handler(sig, frame):
            print("\n🛑 Shutting down IntentOS...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print("✅ IntentOS is running as a daemon process")
        print("Press Ctrl+C to stop")

        # 保持运行
        try:
            import asyncio
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            self.shutdown()

    async def get_kernel_status(self) -> dict:
        """获取详细内核状态"""
        cluster_status = await self.vm.get_cluster_status()
        memory_state = self.vm.local_vm.memory.get_state()
        bootstrap_history = self.bootstrap.get_bootstrap_history(limit=5)
        processes = await self.vm.ps()

        return {
            "cluster": cluster_status,
            "memory": memory_state,
            "processes": [p.to_dict() for p in processes],
            "bootstrap": [r.to_dict() for r in bootstrap_history],
            "registry": self.registry.introspect(),
        }

    def _register_builtin_capabilities(self) -> None:
        """注册内置能力"""
        from ..core import Capability

        # 示例能力：数据查询
        def query_data(context: Context, source: str, **filters) -> dict:
            return {
                "source": source,
                "filters": filters,
                "data": [],  # 模拟数据
                "count": 0,
            }

        query_cap = Capability(
            name="query_data",
            description="查询数据源",
            input_schema={"source": "string", "**filters": "any"},
            output_schema={"data": "array", "count": "number"},
            func=query_data,
            tags=["data", "query"],
        )
        self.registry.register_capability(query_cap)

        # 示例能力：生成报告
        def generate_report(context: Context, title: str, content: str) -> dict:
            return {
                "title": title,
                "content": content,
                "format": "text",
                "generated_at": "now",
            }

        report_cap = Capability(
            name="generate_report",
            description="生成报告",
            input_schema={"title": "string", "content": "string"},
            output_schema={"title": "string", "content": "string"},
            func=generate_report,
            tags=["report", "output"],
        )
        self.registry.register_capability(report_cap)

        # 示例能力：分析数据
        def analyze_data(context: Context, data: list, method: str = "default") -> dict:
            return {
                "method": method,
                "insights": ["分析完成"],
                "summary": "无异常",
            }

        analyze_cap = Capability(
            name="analyze_data",
            description="分析数据",
            input_schema={"data": "array", "method": "string"},
            output_schema={"insights": "array", "summary": "string"},
            func=analyze_data,
            tags=["analysis", "ai"],
        )
        self.registry.register_capability(analyze_cap)

    def _register_builtin_templates(self) -> None:
        """注册内置意图模板"""
        from ..core import IntentStep, IntentTemplate, IntentType

        # 数据分析模板
        analysis_template = IntentTemplate(
            name="analyze_sales",
            description="分析销售数据",
            intent_type=IntentType.COMPOSITE,
            params_schema={
                "region": "string",
                "period": "string",
            },
            steps=[
                IntentStep(
                    capability_name="query_data",
                    params={"source": "sales", "region": "{{region}}", "period": "{{period}}"},
                    output_var="sales_data",
                ),
                IntentStep(
                    capability_name="analyze_data",
                    params={"data": "${sales_data}", "method": "trend"},
                    output_var="analysis_result",
                ),
                IntentStep(
                    capability_name="generate_report",
                    params={"title": "销售分析报告", "content": "${analysis_result}"},
                    output_var="report",
                ),
            ],
            tags=["sales", "analysis"],
        )
        self.registry.register_template(analysis_template)

        # 元意图模板：注册新能力
        register_cap_template = IntentTemplate(
            name="register_capability",
            description="注册新能力",
            intent_type=IntentType.META,
            params_schema={
                "name": "string",
                "description": "string",
            },
            steps=[
                IntentStep(
                    capability_name="meta_register_capability",
                    params={"name": "{{name}}", "description": "{{description}}"},
                ),
            ],
            tags=["meta", "system"],
        )
        self.registry.register_template(register_cap_template)

    async def execute(self, text: str) -> str:
        """
        执行自然语言指令

        Args:
            text: 用户输入的自然语言

        Returns:
            执行结果
        """
        if not self._initialized:
            self.initialize()

        return await self.interface.chat(text)

    @property
    def context(self) -> Context:
        """获取当前上下文"""
        return self.interface.context

    @property
    def registry_introspect(self) -> dict:
        """查看系统注册信息"""
        return self.registry.introspect()
