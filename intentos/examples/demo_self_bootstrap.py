"""
Self-Bootstrap 演示

演示 IntentOS 的自修改能力：
1. 元意图：修改解析规则
2. 元元意图：修改 Self-Bootstrap 策略
3. 自修改的自修改
"""

import asyncio
import json
from datetime import datetime


# =============================================================================
# 演示 1: 元意图 - 修改解析规则
# =============================================================================

async def demo_meta_modify_parse_prompt():
    """演示：元意图修改解析 Prompt"""
    
    print("=" * 70)
    print("演示 1: 元意图 - 修改解析规则")
    print("=" * 70)
    
    # 初始解析 Prompt
    INITIAL_PARSE_PROMPT = """
你是一个意图解析专家。请将用户的自然语言输入解析为结构化的意图。

## 输出格式
{
    "action": "动作 (analyze/query/generate/create/compare 等)",
    "target": "目标对象",
    "parameters": {},
    "confidence": 0.0-1.0
}
"""
    
    print(f"\n初始解析 Prompt:\n{INITIAL_PARSE_PROMPT[:200]}...")
    
    # 创建元意图：修改解析 Prompt
    from intentos.self_bootstrap import MetaIntent, MetaAction, TargetType
    
    meta_intent = MetaIntent(
        action=MetaAction.MODIFY,
        target_type=TargetType.CONFIG,
        target_id="PARSE_PROMPT",
        parameters={
            "new_value": """
你是一个更强大的意图解析专家。请将用户的自然语言输入解析为结构化的意图。

## 新增能力
1. 支持情感分析
2. 支持多轮对话
3. 支持模糊意图识别

## 输出格式
{
    "action": "动作 (analyze/query/generate/create/compare/forecast 等)",
    "target": "目标对象",
    "parameters": {},
    "confidence": 0.0-1.0,
    "sentiment": "positive/neutral/negative",
    "follow_up_questions": []
}
""",
        },
        created_by="admin",
    )
    
    print(f"\n元意图:\n{json.dumps(meta_intent.to_dict(), indent=2, ensure_ascii=False)}")
    
    # 执行元意图 (简化实现)
    system_config = {"PARSE_PROMPT": INITIAL_PARSE_PROMPT}
    
    print(f"\n执行元意图...")
    print(f"修改前 PARSE_PROMPT: {system_config['PARSE_PROMPT'][:100]}...")
    
    # 模拟执行
    system_config["PARSE_PROMPT"] = meta_intent.parameters["new_value"]
    
    print(f"修改后 PARSE_PROMPT: {system_config['PARSE_PROMPT'][:100]}...")
    
    print("\n✅ 元意图执行完成")
    print("解析规则已更新，系统现在支持情感分析和多轮对话")
    
    return system_config


# =============================================================================
# 演示 2: 元元意图 - 修改 Self-Bootstrap 策略
# =============================================================================

async def demo_meta_meta_modify_policy():
    """演示：元元意图修改 Self-Bootstrap 策略"""
    
    print("\n" + "=" * 70)
    print("演示 2: 元元意图 - 修改 Self-Bootstrap 策略")
    print("=" * 70)
    
    # 初始 Self-Bootstrap 策略
    INITIAL_POLICY = {
        "allow_self_modification": True,
        "require_approval_for": ["delete_all_templates"],
        "max_modifications_per_hour": 10,
    }
    
    print(f"\n初始 Self-Bootstrap 策略:\n{json.dumps(INITIAL_POLICY, indent=2)}")
    
    # 创建元元意图
    from intentos.self_bootstrap.meta_meta import (
        MetaMetaIntent,
        MetaAction,
        MetaTargetType,
        IntentLevel,
    )
    
    meta_meta = MetaMetaIntent(
        action=MetaAction.MODIFY,
        target_type=MetaTargetType.SELF_BOOTSTRAP_POLICY,
        parameters={
            "policy": {
                "allow_self_modification": True,
                "require_approval_for": [
                    "delete_all_templates",
                    "modify_audit_rules",
                    "disable_self_bootstrap",
                ],
                "max_modifications_per_hour": 20,
                "require_confidence_threshold": 0.8,
            },
        },
        level=IntentLevel.L2_META_META,
        created_by="super_admin",
    )
    
    print(f"\n元元意图:\n{json.dumps(meta_meta.to_dict(), indent=2, ensure_ascii=False)}")
    
    # 执行元元意图
    from intentos.self_bootstrap.meta_meta import MetaMetaExecutor
    
    system_config = {"SELF_BOOTSTRAP_POLICY": INITIAL_POLICY.copy()}
    executor = MetaMetaExecutor(system_config)
    
    context = {
        "user_id": "super_admin",
        "user_role": "super_admin",
        "permissions": ["super_admin"],
    }
    
    print(f"\n执行元元意图...")
    result = await executor.execute(meta_meta, context)
    
    print(f"\n执行结果:\n{json.dumps(result.to_dict(), indent=2, ensure_ascii=False)}")
    
    print(f"\n修改后的 Self-Bootstrap 策略:\n{json.dumps(system_config['SELF_BOOTSTRAP_POLICY'], indent=2)}")
    
    print("\n✅ 元元意图执行完成")
    print("Self-Bootstrap 策略已更新，新增了审计规则修改保护和置信度阈值")
    
    return system_config


# =============================================================================
# 演示 3: 自修改的自修改 (Meta-Meta-Self-Bootstrap)
# =============================================================================

async def demo_meta_meta_self_bootstrap():
    """演示：自修改的自修改"""
    
    print("\n" + "=" * 70)
    print("演示 3: 自修改的自修改 (Meta-Meta-Self-Bootstrap)")
    print("=" * 70)
    
    # 初始状态
    system_config = {
        "META_ACTIONS": ["CREATE", "MODIFY", "DELETE", "QUERY"],
        "SELF_BOOTSTRAP_POLICY": {
            "allow_self_modification": True,
        },
    }
    
    print(f"\n初始状态:")
    print(f"  META_ACTIONS: {system_config['META_ACTIONS']}")
    
    # 第 1 步：元元意图添加新的元动作
    from intentos.self_bootstrap.meta_meta import (
        MetaMetaIntent,
        MetaAction,
        MetaTargetType,
        IntentLevel,
        MetaMetaExecutor,
    )
    
    meta_meta_1 = MetaMetaIntent(
        action=MetaAction.MODIFY,
        target_type=MetaTargetType.META_ACTION_TYPES,
        parameters={
            "new_actions": ["FORECAST", "OPTIMIZE", "SIMULATE"],
        },
        level=IntentLevel.L2_META_META,
        created_by="super_admin",
    )
    
    print(f"\n步骤 1: 添加新的元动作")
    print(f"  元元意图：添加 FORECAST, OPTIMIZE, SIMULATE")
    
    executor = MetaMetaExecutor(system_config)
    context = {"user_id": "super_admin", "user_role": "super_admin"}
    
    result = await executor.execute(meta_meta_1, context)
    
    print(f"  结果：{result.changes_applied}")
    print(f"  当前 META_ACTIONS: {system_config['META_ACTIONS']}")
    
    # 第 2 步：用新添加的元动作创建元元意图
    # 注意：这里简化演示，实际应该动态扩展 MetaAction 枚举
    meta_meta_2 = MetaMetaIntent(
        action=MetaAction.MODIFY,  # 使用现有动作
        target_type=MetaTargetType.SYSTEM_CONFIG,
        parameters={
            "config": {
                "FORECAST_ENABLED": True,
                "FORECAST_DEFAULT_HORIZON": 90,
                "NEW_ACTIONS_ADDED": ["FORECAST", "OPTIMIZE", "SIMULATE"],
            },
        },
        level=IntentLevel.L2_META_META,
        created_by="super_admin",
    )
    
    print(f"\n步骤 2: 使用新添加的元动作配置")
    print(f"  元元意图：启用预测功能")
    
    result = await executor.execute(meta_meta_2, context)
    
    print(f"  结果：{result.changes_applied}")
    print(f"  当前系统配置：FORECAST_ENABLED={system_config.get('FORECAST_ENABLED')}")
    
    print("\n✅ 自修改的自修改演示完成")
    print("系统成功扩展了元动作类型，并使用新动作进行了自修改")
    
    return system_config


# =============================================================================
# 演示 4: 完整的 Self-Bootstrap 流程
# =============================================================================

async def demo_full_self_bootstrap():
    """演示：完整的 Self-Bootstrap 流程"""
    
    print("\n" + "=" * 70)
    print("演示 4: 完整的 Self-Bootstrap 流程")
    print("=" * 70)
    
    # 初始系统状态
    system_state = {
        "PARSE_PROMPT": "你是一个意图解析专家...",
        "META_ACTIONS": ["CREATE", "MODIFY", "DELETE", "QUERY"],
        "SELF_BOOTSTRAP_POLICY": {
            "allow_self_modification": True,
        },
        "TEMPLATES": {},
        "CAPABILITIES": {},
        "AUDIT_LOG": [],
    }
    
    print(f"\n初始系统状态:")
    print(f"  PARSE_PROMPT: {system_state['PARSE_PROMPT'][:50]}...")
    print(f"  META_ACTIONS: {system_state['META_ACTIONS']}")
    print(f"  模板数量：{len(system_state['TEMPLATES'])}")
    print(f"  能力数量：{len(system_state['CAPABILITIES'])}")
    
    # 流程 1: 用户创建意图模板
    print(f"\n--- 流程 1: 用户创建意图模板 ---")
    
    from intentos.self_bootstrap import MetaIntent, MetaAction, TargetType, CreateResult
    
    create_template_meta = MetaIntent(
        action=MetaAction.CREATE,
        target_type=TargetType.TEMPLATE,
        parameters={
            "name": "sales_forecast",
            "description": "销售预测模板",
            "steps": [
                {"capability": "query_historical_sales"},
                {"capability": "analyze_trends"},
                {"capability": "forecast_future"},
            ],
        },
        created_by="user_001",
    )
    
    print(f"元意图：创建销售预测模板")
    
    # 模拟执行
    system_state["TEMPLATES"]["sales_forecast"] = create_template_meta.parameters
    system_state["AUDIT_LOG"].append({
        "action": "create_template",
        "template": "sales_forecast",
        "user": "user_001",
        "timestamp": datetime.now().isoformat(),
    })
    
    print(f"✅ 模板已创建")
    
    # 流程 2: 管理员修改解析规则
    print(f"\n--- 流程 2: 管理员修改解析规则 ---")
    
    modify_parse_meta = MetaIntent(
        action=MetaAction.MODIFY,
        target_type=TargetType.CONFIG,
        target_id="PARSE_PROMPT",
        parameters={
            "new_value": "你是一个更强大的意图解析专家，支持预测分析...",
        },
        created_by="admin",
    )
    
    print(f"元意图：修改解析规则")
    
    # 模拟执行
    system_state["PARSE_PROMPT"] = modify_parse_meta.parameters["new_value"]
    system_state["AUDIT_LOG"].append({
        "action": "modify_parse_prompt",
        "user": "admin",
        "timestamp": datetime.now().isoformat(),
    })
    
    print(f"✅ 解析规则已修改")
    
    # 流程 3: 超级管理员扩展元动作
    print(f"\n--- 流程 3: 超级管理员扩展元动作 ---")
    
    from intentos.self_bootstrap.meta_meta import MetaMetaIntent, MetaTargetType, IntentLevel, MetaMetaExecutor
    
    extend_actions_meta_meta = MetaMetaIntent(
        action=MetaAction.MODIFY,
        target_type=MetaTargetType.META_ACTION_TYPES,
        parameters={
            "new_actions": ["FORECAST", "OPTIMIZE"],
        },
        level=IntentLevel.L2_META_META,
        created_by="super_admin",
    )
    
    print(f"元元意图：扩展元动作")
    
    # 模拟执行
    executor = MetaMetaExecutor(system_state)
    context = {"user_id": "super_admin", "user_role": "super_admin"}
    result = await executor.execute(extend_actions_meta_meta, context)
    
    print(f"✅ 元动作已扩展：{system_state['META_ACTIONS']}")
    
    # 最终系统状态
    print(f"\n--- 最终系统状态 ---")
    print(f"  PARSE_PROMPT: {system_state['PARSE_PROMPT'][:50]}...")
    print(f"  META_ACTIONS: {system_state['META_ACTIONS']}")
    print(f"  模板数量：{len(system_state['TEMPLATES'])}")
    print(f"  审计日志：{len(system_state['AUDIT_LOG'])} 条")
    
    print("\n✅ 完整的 Self-Bootstrap 流程演示完成")
    print("系统成功实现了：创建模板 → 修改规则 → 扩展元动作")
    
    return system_state


# =============================================================================
# 主函数
# =============================================================================

async def main():
    """运行所有演示"""
    
    print("\n" + "=" * 70)
    print("IntentOS Self-Bootstrap 演示")
    print("元意图 → 元元意图 → 自修改的自修改")
    print("=" * 70)
    
    # 演示 1: 元意图修改解析规则
    await demo_meta_modify_parse_prompt()
    
    # 演示 2: 元元意图修改 Self-Bootstrap 策略
    await demo_meta_meta_modify_policy()
    
    # 演示 3: 自修改的自修改
    await demo_meta_meta_self_bootstrap()
    
    # 演示 4: 完整的 Self-Bootstrap 流程
    await demo_full_self_bootstrap()
    
    print("\n" + "=" * 70)
    print("所有演示完成")
    print("=" * 70)
    
    print("\n🎯 关键洞察:")
    print("1. 只有 LLM 作为处理器，才能实现 Self-Bootstrap")
    print("2. 因为解析规则在 Prompt 中（可修改），而非硬编码代码")
    print("3. 元意图修改规则，元元意图修改元意图的规则")
    print("4. 这就是 Meta：系统用语言描述和管理自身")


if __name__ == "__main__":
    asyncio.run(main())
