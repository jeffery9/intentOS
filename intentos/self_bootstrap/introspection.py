"""
系统自省 API

系统了解自身状态的能力：
- 查询意图模板
- 查询能力注册
- 查询执行历史
- 查询系统状态
"""

from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from . import IntentRegistry, ExecutionEngine


class SystemIntrospection:
    """
    系统自省 API
    
    提供查询系统自身状态的能力
    """
    
    def __init__(
        self,
        registry: IntentRegistry,
        engine: ExecutionEngine,
    ):
        self.registry = registry
        self.engine = engine
    
    # =========================================================================
    # 意图模板查询
    # =========================================================================
    
    async def query_templates(
        self,
        tags: Optional[list[str]] = None,
        search: Optional[str] = None,
        intent_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        查询意图模板
        
        Args:
            tags: 标签过滤
            search: 搜索关键词
            intent_type: 意图类型过滤
        
        Returns:
            模板列表
        """
        templates = []
        
        # 获取所有模板
        if tags:
            all_templates = self.registry.list_templates(tags=tags)
        else:
            all_templates = self.registry.list_templates()
        
        # 过滤
        for template in all_templates:
            # 类型过滤
            if intent_type and template.intent_type.value != intent_type:
                continue
            
            # 搜索过滤
            if search:
                search_lower = search.lower()
                if (search_lower not in template.name.lower() and
                    search_lower not in template.description.lower()):
                    continue
            
            templates.append({
                "name": template.name,
                "description": template.description,
                "intent_type": template.intent_type.value,
                "version": template.version,
                "tags": template.tags,
                "steps_count": len(template.steps),
            })
        
        return templates
    
    async def get_template(self, name: str) -> Optional[dict[str, Any]]:
        """
        获取特定模板
        
        Args:
            name: 模板名称
        
        Returns:
            模板详情，如果不存在返回 None
        """
        template = self.registry.get_template(name)
        
        if not template:
            return None
        
        return {
            "name": template.name,
            "description": template.description,
            "intent_type": template.intent_type.value,
            "version": template.version,
            "tags": template.tags,
            "params_schema": template.params_schema,
            "steps": [
                {
                    "capability": step.capability_name,
                    "params": step.params,
                    "depends_on": step.depends_on,
                    "condition": step.condition,
                    "output_var": step.output_var,
                }
                for step in template.steps
            ],
            "constraints": template.constraints,
            "required_permissions": template.required_permissions,
        }
    
    async def list_templates(self) -> list[dict[str, Any]]:
        """列出所有模板"""
        return await self.query_templates()
    
    async def count_templates(self) -> int:
        """统计模板数量"""
        return len(self.registry.list_templates())
    
    # =========================================================================
    # 能力注册查询
    # =========================================================================
    
    async def list_capabilities(
        self,
        tags: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        列出所有能力
        
        Args:
            tags: 标签过滤
        
        Returns:
            能力列表
        """
        capabilities = []
        
        all_caps = self.registry.list_capabilities(tags=tags)
        
        for cap in all_caps:
            capabilities.append({
                "name": cap.name,
                "description": cap.description,
                "tags": cap.tags,
                "requires_permissions": cap.requires_permissions,
            })
        
        return capabilities
    
    async def get_capability(self, name: str) -> Optional[dict[str, Any]]:
        """
        获取特定能力
        
        Args:
            name: 能力名称
        
        Returns:
            能力详情，如果不存在返回 None
        """
        cap = self.registry.get_capability(name)
        
        if not cap:
            return None
        
        return {
            "name": cap.name,
            "description": cap.description,
            "input_schema": cap.input_schema,
            "output_schema": cap.output_schema,
            "requires_permissions": cap.requires_permissions,
            "tags": cap.tags,
        }
    
    async def search_capabilities(self, query: str) -> list[dict[str, Any]]:
        """
        搜索能力
        
        Args:
            query: 搜索关键词
        
        Returns:
            匹配的能力列表
        """
        results = self.registry.search(query)
        
        capabilities = []
        for cap_name in results.get("capabilities", []):
            cap = self.registry.get_capability(cap_name)
            if cap:
                capabilities.append({
                    "name": cap.name,
                    "description": cap.description,
                    "tags": cap.tags,
                })
        
        return capabilities
    
    async def count_capabilities(self) -> int:
        """统计能力数量"""
        return len(self.registry.list_capabilities())
    
    # =========================================================================
    # 执行历史查询
    # =========================================================================
    
    async def get_execution_history(
        self,
        intent_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        获取执行历史
        
        Args:
            intent_id: 意图 ID 过滤
            limit: 返回数量限制
        
        Returns:
            执行历史记录
        """
        history = self.engine.get_execution_history(limit=limit)
        
        records = []
        for record in history:
            # 过滤 intent_id
            if intent_id and record.intent_id != intent_id:
                continue
            
            records.append({
                "intent_id": record.intent_id,
                "success": record.success,
                "error": record.error,
                "started_at": record.started_at.isoformat(),
                "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                "execution_trace": record.execution_trace,
            })
        
        return records
    
    async def get_execution_stats(
        self,
        time_range: str = "24h",
    ) -> dict[str, Any]:
        """
        获取执行统计
        
        Args:
            time_range: 时间范围 (24h, 7d, 30d)
        
        Returns:
            执行统计信息
        """
        # 解析时间范围
        if time_range.endswith("h"):
            hours = int(time_range[:-1])
        elif time_range.endswith("d"):
            hours = int(time_range[:-1]) * 24
        else:
            hours = 24
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 获取历史记录
        history = self.engine.get_execution_history(limit=10000)
        
        # 过滤时间范围
        recent_history = [
            r for r in history
            if r.started_at >= cutoff_time
        ]
        
        # 统计
        total = len(recent_history)
        success = sum(1 for r in recent_history if r.success)
        failed = total - success
        
        # 平均耗时
        durations = [
            r.completed_at.timestamp() - r.started_at.timestamp()
            for r in recent_history
            if r.completed_at
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "time_range": time_range,
            "total_executions": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate": success / total if total > 0 else 0,
            "avg_duration_seconds": avg_duration,
        }
    
    # =========================================================================
    # 系统状态查询
    # =========================================================================
    
    async def get_status(self) -> dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        from intentos import __version__
        
        return {
            "version": __version__,
            "templates_count": await self.count_templates(),
            "capabilities_count": await self.count_capabilities(),
            "timestamp": datetime.now().isoformat(),
        }
    
    async def introspect(self) -> dict[str, Any]:
        """
        完整系统自省
        
        Returns:
            完整系统信息
        """
        return {
            "status": await self.get_status(),
            "templates": await self.list_templates(),
            "capabilities": await self.list_capabilities(),
            "stats": await self.get_execution_stats("24h"),
        }


# =============================================================================
# 便捷函数
# =============================================================================

async def query_templates(
    introspection: SystemIntrospection,
    **kwargs,
) -> list[dict[str, Any]]:
    """便捷函数：查询模板"""
    return await introspection.query_templates(**kwargs)


async def get_template(
    introspection: SystemIntrospection,
    name: str,
) -> Optional[dict[str, Any]]:
    """便捷函数：获取模板"""
    return await introspection.get_template(name)


async def list_capabilities(
    introspection: SystemIntrospection,
    **kwargs,
) -> list[dict[str, Any]]:
    """便捷函数：列出能力"""
    return await introspection.list_capabilities(**kwargs)


async def get_status(
    introspection: SystemIntrospection,
) -> dict[str, Any]:
    """便捷函数：获取系统状态"""
    return await introspection.get_status()
