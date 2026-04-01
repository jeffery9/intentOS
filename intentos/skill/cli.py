# -*- coding: utf-8 -*-
"""
IntentOS Skill CLI

/skillify 命令 - 将工作流提炼为技能
"""

from __future__ import annotations

import cmd
import logging
from typing import Optional

from ..memory.store import get_memory_store
from .models import Skill
from .skillifier import Skillifier, SkillifierConfig
from .store import get_skill_store

logger = logging.getLogger(__name__)


class SkillCLI(cmd.Cmd):
    """
    技能管理 CLI
    
    命令:
        /skillify <session_id>  - 将 session 提炼为技能
        /skill list             - 列出技能
        /skill search <query>   - 搜索技能
        /skill show <id>        - 显示技能详情
        /skill export <id>      - 导出技能
        /skill import <file>    - 导入技能
        /skill delete <id>      - 删除技能
        /help skill             - 显示帮助
    """
    
    intro = "技能管理系统 - 输入 /help skill 查看帮助"
    prompt = "(skill) "
    
    def __init__(self):
        super().__init__()
        self.skillifier = Skillifier()
        self.skill_store = get_skill_store()
        self.memory_store = get_memory_store()
    
    def do_skillify(self, arg: str) -> None:
        """将会话提炼为技能
        
        用法：/skillify <session_id>
        """
        session_id = arg.strip()
        
        if not session_id:
            print("请提供会话 ID")
            return
        
        # 获取会话记忆
        session = self.memory_store.get_session(session_id)
        if not session:
            print(f"未找到会话：{session_id}")
            return
        
        print(f"正在提炼会话 {session_id} 为技能...")
        
        # 执行提炼
        import asyncio
        skill = asyncio.run(self.skillifier.skillify(
            session_id,
            session.memory_entries,
        ))
        
        if not skill:
            print("无法提炼为技能（步骤不足或质量不够）")
            return
        
        # 保存技能
        self.skill_store.save_skill(skill)
        
        print(f"\n✓ 成功提炼技能:")
        print(f"  名称：{skill.name}")
        print(f"  描述：{skill.description}")
        print(f"  步骤：{len(skill.steps)} 步")
        print(f"  触发器：{len(skill.trigger.keywords)} 个关键词")
        print(f"  质量评分：{skill.success_rate:.2f}")
        print(f"  技能 ID: {skill.id}")
    
    def do_skill(self, arg: str) -> None:
        """技能管理命令
        
        子命令:
          list              - 列出技能
          search <query>    - 搜索技能
          show <id>         - 显示技能详情
          export <id>       - 导出技能为 YAML
          import <file>     - 从 YAML 导入技能
          delete <id>       - 删除技能
        """
        parts = arg.split(maxsplit=1)
        if not parts:
            print("请指定子命令：list, search, show, export, import, delete")
            return
        
        subcommand = parts[0]
        subargs = parts[1] if len(parts) > 1 else ""
        
        if subcommand == "list":
            self._do_skill_list(subargs)
        elif subcommand == "search":
            self._do_skill_search(subargs)
        elif subcommand == "show":
            self._do_skill_show(subargs)
        elif subcommand == "export":
            self._do_skill_export(subargs)
        elif subcommand == "import":
            self._do_skill_import(subargs)
        elif subcommand == "delete":
            self._do_skill_delete(subargs)
        else:
            print(f"未知子命令：{subcommand}")
    
    def _do_skill_list(self, arg: str) -> None:
        """列出技能"""
        skills = self.skill_store.list_skills(limit=20)
        
        if not skills:
            print("没有技能")
            return
        
        print(f"\n找到 {len(skills)} 个技能:\n")
        for skill in skills:
            print(f"  [{skill.level.value}] {skill.name}")
            print(f"    ID: {skill.id[:8]}...")
            print(f"    步骤：{len(skill.steps)}, 使用：{skill.usage_count}次")
            if skill.tags:
                print(f"    标签：{', '.join(skill.tags[:5])}")
            print()
    
    def _do_skill_search(self, query: str) -> None:
        """搜索技能"""
        if not query.strip():
            print("请提供搜索关键词")
            return
        
        skills = self.skill_store.search_skills(query.strip(), limit=10)
        
        if not skills:
            print(f"没有找到匹配 '{query}' 的技能")
            return
        
        print(f"\n找到 {len(skills)} 个匹配的技能:\n")
        for skill in skills:
            self._print_skill_brief(skill)
    
    def _do_skill_show(self, skill_id: str) -> None:
        """显示技能详情"""
        if not skill_id.strip():
            print("请提供技能 ID")
            return
        
        skill = self.skill_store.get_skill(skill_id.strip())
        if not skill:
            print(f"未找到技能：{skill_id}")
            return
        
        self._print_skill_full(skill)
    
    def _do_skill_export(self, skill_id: str) -> None:
        """导出技能"""
        if not skill_id.strip():
            print("请提供技能 ID")
            return
        
        yaml_content = self.skill_store.export_skill(skill_id.strip())
        if not yaml_content:
            print(f"未找到技能：{skill_id}")
            return
        
        print("\n--- 技能 YAML ---")
        print(yaml_content)
        print("--- END ---\n")
    
    def _do_skill_import(self, file_path: str) -> None:
        """导入技能"""
        if not file_path.strip():
            print("请提供 YAML 文件路径")
            return
        
        try:
            with open(file_path.strip(), "r", encoding="utf-8") as f:
                yaml_content = f.read()
            
            skill = self.skill_store.import_skill(yaml_content)
            if skill:
                print(f"✓ 成功导入技能：{skill.name}")
            else:
                print("导入失败")
        except Exception as e:
            print(f"导入失败：{e}")
    
    def _do_skill_delete(self, skill_id: str) -> None:
        """删除技能"""
        if not skill_id.strip():
            print("请提供技能 ID")
            return
        
        if self.skill_store.delete_skill(skill_id.strip()):
            print(f"✓ 技能已删除")
        else:
            print(f"未找到技能：{skill_id}")
    
    def _print_skill_brief(self, skill: Skill) -> None:
        """打印技能摘要"""
        print(f"  [{skill.level.value}] {skill.name}")
        print(f"    ID: {skill.id[:8]}...")
        print(f"    步骤：{len(skill.steps)}, 使用：{skill.usage_count}次")
        if skill.tags:
            print(f"    标签：{', '.join(skill.tags[:5])}")
        print()
    
    def _print_skill_full(self, skill: Skill) -> None:
        """打印技能详情"""
        print(f"\n{'='*60}")
        print(f"技能：{skill.name}")
        print(f"{'='*60}")
        print(f"ID: {skill.id}")
        print(f"描述：{skill.description}")
        print(f"版本：{skill.version}")
        print(f"等级：{skill.level.value}")
        print(f"来源：{skill.created_from}")
        print(f"使用：{skill.usage_count}次，成功率：{skill.success_rate:.1%}")
        
        print(f"\n触发器:")
        if skill.trigger.keywords:
            print(f"  关键词：{', '.join(skill.trigger.keywords)}")
        if skill.trigger.intent_pattern:
            print(f"  意图模式：{skill.trigger.intent_pattern}")
        
        print(f"\n参数:")
        if skill.params:
            for param in skill.params:
                req = "必填" if param.required else "可选"
                print(f"  {param.name} ({param.type}, {req}): {param.description}")
        else:
            print("  (无)")
        
        print(f"\n步骤 ({len(skill.steps)}):")
        for i, step in enumerate(skill.steps, 1):
            print(f"  {i}. [{step.action}] {step.name}")
            if step.description:
                print(f"     {step.description}")
        
        print(f"\n标签：{', '.join(skill.tags)}")
        print(f"{'='*60}\n")
    
    def do_exit(self, arg: str) -> bool:
        """退出 CLI"""
        return True
    
    def do_quit(self, arg: str) -> bool:
        """退出 CLI"""
        return True


def create_skill_cli() -> SkillCLI:
    """创建技能 CLI"""
    return SkillCLI()


if __name__ == "__main__":
    cli = create_skill_cli()
    cli.cmdloop()
