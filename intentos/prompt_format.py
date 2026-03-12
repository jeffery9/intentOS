"""
IntentGarden v2.0 - Prompt 规范定义

Prompt 作为 IntentOS 的"可执行文件格式"
类似 PE/ELF，但采用 YAML/JSON 声明式格式
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import yaml
import json
from datetime import datetime


# =============================================================================
# Prompt 可执行文件格式规范 v1.0
# =============================================================================

class PromptSection(Enum):
    """Prompt 段定义 (类似 ELF Section)"""
    METADATA = "metadata"       # 元数据段
    INTENT = "intent"           # 意图声明段
    CONTEXT = "context"         # 上下文段
    CAPABILITIES = "capabilities"  # 能力绑定段
    CONSTRAINTS = "constraints" # 约束条件段
    WORKFLOW = "workflow"       # 工作流段 (DAG)
    OPS_MODEL = "ops_model"     # 运维模型段
    SAFETY = "safety"           # 安全策略段


class ExecutionMode(Enum):
    """执行模式"""
    SYNC = "sync"               # 同步执行
    ASYNC = "async"             # 异步执行
    STREAMING = "streaming"     # 流式执行
    DAG = "dag"                 # DAG 并行执行


class SafetyLevel(Enum):
    """安全等级"""
    LOW = "low"                 # 低风险，自动执行
    MEDIUM = "medium"           # 中风险，记录日志
    HIGH = "high"               # 高风险，需要人工审批
    CRITICAL = "critical"       # 关键操作，多人审批


@dataclass
class PromptMetadata:
    """
    元数据段 (类似 ELF Header)
    """
    version: str = "1.0.0"                  # Prompt 规范版本
    name: str = ""                          # Prompt 名称
    description: str = ""                   # 描述
    author: str = ""                        # 作者
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    checksum: str = ""                      # 校验和
    signature: str = ""                     # 数字签名 (可选)
    
    # 执行配置
    execution_mode: str = ExecutionMode.SYNC.value
    timeout_seconds: int = 300              # 超时时间
    retry_count: int = 3                    # 重试次数
    priority: int = 5                       # 优先级 (1-10)
    
    # 标签
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "checksum": self.checksum,
            "signature": self.signature,
            "execution_mode": self.execution_mode,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "priority": self.priority,
            "tags": self.tags,
        }


@dataclass
class IntentDeclaration:
    """
    意图声明段 (类似 PE 的导入表)
    声明"我要什么"
    """
    # 功能意图
    goal: str = ""                          # 目标描述
    intent_type: str = "functional"         # functional | operational
    expected_outcome: str = ""              # 期望结果
    
    # 操作性意图 (SLO/SLA)
    performance_targets: dict[str, Any] = field(default_factory=dict)
    # 示例:
    # latency_p99_ms: 100
    # availability: 99.9%
    # error_rate: 0.1%
    
    # 输入参数
    inputs: dict[str, Any] = field(default_factory=dict)
    
    # 输出格式
    output_format: str = "json"             # json | markdown | html | text
    
    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "intent_type": self.intent_type,
            "expected_outcome": self.expected_outcome,
            "performance_targets": self.performance_targets,
            "inputs": self.inputs,
            "output_format": self.output_format,
        }


@dataclass
class ContextBinding:
    """
    上下文绑定段
    多模态事件图
    """
    # 用户上下文
    user_id: str = ""
    user_role: str = ""
    session_id: str = ""
    
    # 业务上下文
    business_context: dict[str, Any] = field(default_factory=dict)
    
    # 技术上下文
    technical_context: dict[str, Any] = field(default_factory=dict)
    # 示例:
    # cluster: "prod-us-east-1"
    # namespace: "default"
    # service: "order-service"
    
    # 历史上下文 (多模态事件)
    event_graph: list[dict[str, Any]] = field(default_factory=list)
    # 示例:
    # - type: "metric", source: "prometheus", query: "rate(http_requests_total[5m])"
    # - type: "log", source: "elasticsearch", query: "level:ERROR service:order"
    # - type: "trace", source: "jaeger", trace_id: "abc123"
    # - type: "document", source: "confluence", page_id: "12345"
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_role": self.user_role,
            "session_id": self.session_id,
            "business_context": self.business_context,
            "technical_context": self.technical_context,
            "event_graph": self.event_graph,
        }


@dataclass
class CapabilityBinding:
    """
    能力绑定段 (类似 PE 的导入函数表)
    """
    name: str = ""
    version: str = "*"                      # 版本约束
    endpoint: str = ""                      # API 端点
    protocol: str = "http"                  # http | grpc | websocket | llm
    authentication: dict[str, str] = field(default_factory=dict)
    
    # LLM 特定配置
    llm_config: dict[str, Any] = field(default_factory=dict)
    # 示例:
    # model: "gpt-4o"
    # temperature: 0.7
    # max_tokens: 2000
    
    # 降级策略
    fallback: list[str] = field(default_factory=list)  # 备用能力
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "endpoint": self.endpoint,
            "protocol": self.protocol,
            "authentication": self.authentication,
            "llm_config": self.llm_config,
            "fallback": self.fallback,
        }


@dataclass
class ConstraintDefinition:
    """
    约束条件段
    """
    # 资源约束
    resource_limits: dict[str, Any] = field(default_factory=dict)
    # 示例:
    # max_tokens: 10000
    # max_api_calls: 100
    # budget_usd: 10.0
    
    # 时间约束
    time_constraints: dict[str, Any] = field(default_factory=dict)
    # 示例:
    # deadline: "2024-12-31T23:59:59Z"
    # business_hours_only: true
    
    # 合规约束
    compliance_rules: list[str] = field(default_factory=list)
    # 示例:
    # "GDPR: no_pii_in_logs"
    # "SOC2: audit_all_actions"
    
    def to_dict(self) -> dict:
        return {
            "resource_limits": self.resource_limits,
            "time_constraints": self.time_constraints,
            "compliance_rules": self.compliance_rules,
        }


@dataclass
class WorkflowStep:
    """
    工作流步骤 (DAG 节点)
    """
    id: str = ""
    name: str = ""
    capability: str = ""                    # 引用的能力名称
    depends_on: list[str] = field(default_factory=list)  # 依赖的步骤 ID
    condition: str = ""                     # 执行条件 (表达式)
    params: dict[str, Any] = field(default_factory=dict)
    output_var: str = ""                    # 输出变量名
    retry_policy: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "capability": self.capability,
            "depends_on": self.depends_on,
            "condition": self.condition,
            "params": self.params,
            "output_var": self.output_var,
            "retry_policy": self.retry_policy,
        }


@dataclass
class WorkflowDefinition:
    """
    工作流段 (DAG)
    定义任务执行顺序
    """
    steps: list[WorkflowStep] = field(default_factory=list)
    
    # 错误处理
    on_error: list[dict[str, Any]] = field(default_factory=list)
    # 示例:
    # - action: "retry", max_attempts: 3
    # - action: "fallback", use: "backup_capability"
    # - action: "notify", channel: "slack"
    
    # 成功条件
    success_condition: str = ""             # 表达式
    
    def to_dict(self) -> dict:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "on_error": self.on_error,
            "success_condition": self.success_condition,
        }


@dataclass
class OpsModel:
    """
    运维模型段
    定义 SLO、监控、告警策略
    """
    # SLO 定义
    slo_targets: dict[str, Any] = field(default_factory=dict)
    # 示例:
    # latency_p99_ms: 100
    # availability_percent: 99.9
    
    # 监控指标
    metrics_to_collect: list[str] = field(default_factory=list)
    # 示例:
    # - "execution_duration"
    # - "token_usage"
    # - "api_call_count"
    
    # 告警规则
    alert_rules: list[dict[str, Any]] = field(default_factory=list)
    # 示例:
    # - condition: "error_rate > 0.05", notify: "oncall-slack"
    
    # 自动修复策略
    auto_remediation: list[dict[str, Any]] = field(default_factory=list)
    # 示例:
    # - trigger: "model_timeout", action: "switch_to_backup_model"
    
    def to_dict(self) -> dict:
        return {
            "slo_targets": self.slo_targets,
            "metrics_to_collect": self.metrics_to_collect,
            "alert_rules": self.alert_rules,
            "auto_remediation": self.auto_remediation,
        }


@dataclass
class SafetyPolicy:
    """
    安全策略段
    Human-in-the-loop 审批
    """
    # 安全等级
    level: str = SafetyLevel.LOW.value
    
    # 需要审批的操作
    requires_approval_for: list[str] = field(default_factory=list)
    # 示例:
    # - "delete_production_data"
    # - "deploy_to_production"
    
    # 审批人
    approvers: list[str] = field(default_factory=list)
    
    # 审批超时
    approval_timeout_minutes: int = 60
    
    # 审计配置
    audit_config: dict[str, Any] = field(default_factory=dict)
    # 示例:
    # log_all_actions: true
    # retention_days: 365
    
    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "requires_approval_for": self.requires_approval_for,
            "approvers": self.approvers,
            "approval_timeout_minutes": self.approval_timeout_minutes,
            "audit_config": self.audit_config,
        }


# =============================================================================
# Prompt 可执行文件 (PEF - Prompt Executable Format)
# =============================================================================

@dataclass
class PromptExecutable:
    """
    Prompt 可执行文件
    完整的 Prompt 规范实现
    """
    metadata: PromptMetadata = field(default_factory=PromptMetadata)
    intent: IntentDeclaration = field(default_factory=IntentDeclaration)
    context: ContextBinding = field(default_factory=ContextBinding)
    capabilities: list[CapabilityBinding] = field(default_factory=list)
    constraints: ConstraintDefinition = field(default_factory=ConstraintDefinition)
    workflow: WorkflowDefinition = field(default_factory=WorkflowDefinition)
    ops_model: OpsModel = field(default_factory=OpsModel)
    safety: SafetyPolicy = field(default_factory=SafetyPolicy)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "metadata": self.metadata.to_dict(),
            "intent": self.intent.to_dict(),
            "context": self.context.to_dict(),
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "constraints": self.constraints.to_dict(),
            "workflow": self.workflow.to_dict(),
            "ops_model": self.ops_model.to_dict(),
            "safety": self.safety.to_dict(),
        }
    
    def to_yaml(self) -> str:
        """导出为 YAML"""
        return yaml.dump(self.to_dict(), allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def to_json(self, indent: int = 2) -> str:
        """导出为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> "PromptExecutable":
        """从 YAML 加载"""
        data = yaml.safe_load(yaml_str)
        return cls._from_dict(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "PromptExecutable":
        """从 JSON 加载"""
        data = json.loads(json_str)
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: dict) -> "PromptExecutable":
        """从字典构建"""
        # 简化实现，完整实现需要递归构建所有嵌套对象
        return cls(
            metadata=PromptMetadata(**data.get("metadata", {})),
            intent=IntentDeclaration(**data.get("intent", {})),
            context=ContextBinding(**data.get("context", {})),
            capabilities=[CapabilityBinding(**cap) for cap in data.get("capabilities", [])],
            constraints=ConstraintDefinition(**data.get("constraints", {})),
            workflow=WorkflowDefinition(**data.get("workflow", {})),
            ops_model=OpsModel(**data.get("ops_model", {})),
            safety=SafetyPolicy(**data.get("safety", {})),
        )
    
    def validate(self) -> list[str]:
        """验证 Prompt 有效性"""
        errors = []
        
        # 必填字段检查
        if not self.metadata.name:
            errors.append("metadata.name is required")
        
        if not self.intent.goal:
            errors.append("intent.goal is required")
        
        # 工作流验证
        step_ids = {step.id for step in self.workflow.steps}
        for step in self.workflow.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(f"Workflow step '{step.id}' depends on non-existent step '{dep}'")
        
        # 安全等级验证
        if self.safety.level == SafetyLevel.CRITICAL.value and not self.safety.approvers:
            errors.append("Critical safety level requires at least one approver")
        
        return errors


# =============================================================================
# 示例 Prompt 模板
# =============================================================================

def create_sales_analysis_prompt() -> PromptExecutable:
    """创建销售分析 Prompt 示例"""
    return PromptExecutable(
        metadata=PromptMetadata(
            name="sales_analysis_q3",
            description="分析 Q3 销售数据并生成报告",
            author="intentos",
            tags=["sales", "analysis", "report"],
            execution_mode=ExecutionMode.DAG.value,
        ),
        intent=IntentDeclaration(
            goal="分析华东和华南区域 Q3 销售表现，对比去年同期",
            intent_type="functional",
            expected_outcome="交互式分析报告，包含异常检测和归因分析",
            inputs={
                "regions": ["华东", "华南"],
                "period": "Q3",
                "compare_with": "last_year",
            },
            output_format="interactive_dashboard",
        ),
        context=ContextBinding(
            user_id="sales_manager_001",
            user_role="manager",
            business_context={
                "department": "sales",
                "fiscal_year": 2024,
            },
        ),
        capabilities=[
            CapabilityBinding(
                name="query_sales_data",
                protocol="http",
                endpoint="https://api.example.com/sales",
            ),
            CapabilityBinding(
                name="analyze_trends",
                protocol="llm",
                llm_config={"model": "gpt-4o", "temperature": 0.3},
            ),
            CapabilityBinding(
                name="generate_dashboard",
                protocol="http",
                endpoint="https://api.example.com/dashboard",
            ),
        ],
        workflow=WorkflowDefinition(
            steps=[
                WorkflowStep(
                    id="step1",
                    name="查询华东销售数据",
                    capability="query_sales_data",
                    params={"region": "华东", "period": "Q3"},
                    output_var="east_data",
                ),
                WorkflowStep(
                    id="step2",
                    name="查询华南销售数据",
                    capability="query_sales_data",
                    params={"region": "华南", "period": "Q3"},
                    output_var="south_data",
                    depends_on=["step1"],  # 可以并行，这里演示依赖
                ),
                WorkflowStep(
                    id="step3",
                    name="分析趋势",
                    capability="analyze_trends",
                    params={"data": "${east_data} + ${south_data}"},
                    depends_on=["step1", "step2"],
                    output_var="analysis",
                ),
                WorkflowStep(
                    id="step4",
                    name="生成仪表盘",
                    capability="generate_dashboard",
                    params={"analysis": "${analysis}"},
                    depends_on=["step3"],
                ),
            ],
            success_condition="all_steps_completed",
        ),
        ops_model=OpsModel(
            slo_targets={
                "latency_p99_ms": 5000,
                "availability_percent": 99.5,
            },
            metrics_to_collect=["execution_duration", "token_usage", "data_freshness"],
            alert_rules=[
                {"condition": "execution_duration > 30s", "notify": "team-slack"},
            ],
        ),
        safety=SafetyPolicy(
            level=SafetyLevel.MEDIUM.value,
            audit_config={"log_all_actions": True, "retention_days": 90},
        ),
    )


if __name__ == "__main__":
    # 创建示例 Prompt
    prompt = create_sales_analysis_prompt()
    
    print("=" * 60)
    print("Prompt Executable Format (PEF) 示例")
    print("=" * 60)
    print()
    print(prompt.to_yaml())
    
    # 验证
    errors = prompt.validate()
    if errors:
        print("\n验证错误:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\n✅ Prompt 验证通过")
