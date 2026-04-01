# -*- coding: utf-8 -*-
"""
IntentOS Memory CLI

/memory 命令 - 查看和管理记忆
"""

from __future__ import annotations

import cmd
import logging
from typing import Any, Optional

from .models import MemoryQuery, MemoryContentType
from .store import MemoryStore, get_memory_store
from .shadow_agent import ShadowAgent

logger = logging.getLogger(__name__)


class MemoryCLI(cmd.Cmd):
    """
    记忆管理 CLI
    
    命令:
        /memory list       - 列出最近的记忆
        /memory search     - 搜索记忆
        /memory show       - 显示记忆详情
        /memory stats      - 显示统计信息
        /memory clear      - 清除记忆
        /memory session    - 查看会话详情
        /help memory       - 显示帮助
    """
    
    intro = "记忆管理系统 - 输入 /help memory 查看帮助"
    prompt = "(memory) "
    
    def __init__(self, store: Optional[MemoryStore] = None):
        super().__init__()
        self.store = store or get_memory_store()
        self.current_session: Optional[ShadowAgent] = None
    
    def do_list(self, arg: str) -> None:
        """列出最近的记忆
        
        用法：/memory list [limit=10] [type=success|failure|pattern]
        """
        args = self._parse_args(arg)
        limit = int(args.get("limit", 10))
        memory_type = args.get("type")
        
        query = MemoryQuery(limit=limit)
        if memory_type:
            try:
                query.memory_type = MemoryContentType(memory_type)
            except ValueError:
                print(f"无效的记忆类型：{memory_type}")
                return
        
        memories = self.store.query_memories(query)
        
        if not memories:
            print("没有找到记忆")
            return
        
        print(f"\n找到 {len(memories)} 条记忆:\n")
        for entry in memories:
            self._print_entry(entry)
    
    def do_search(self, arg: str) -> None:
        """搜索记忆
        
        用法：/memory search <关键词> [limit=20] [min_importance=0]
        """
        args = self._parse_args(arg, allow_positional=True)
        keywords = args.get("_positional", [])
        limit = int(args.get("limit", 20))
        min_importance = float(args.get("min_importance", 0))
        
        if not keywords:
            print("请提供搜索关键词")
            return
        
        query = MemoryQuery(
            keywords=keywords,
            limit=limit,
            min_importance=min_importance,
        )
        
        memories = self.store.query_memories(query)
        
        if not memories:
            print(f"没有找到匹配 '{' '.join(keywords)}' 的记忆")
            return
        
        print(f"\n找到 {len(memories)} 条匹配的记忆:\n")
        for entry in memories:
            self._print_entry(entry)
    
    def do_show(self, arg: str) -> None:
        """显示记忆详情
        
        用法：/memory show <entry_id>
        """
        entry_id = arg.strip()
        
        if not entry_id:
            print("请提供记忆 ID")
            return
        
        entry = self.store.get_memory_entry(entry_id)
        
        if not entry:
            print(f"未找到记忆：{entry_id}")
            return
        
        self._print_entry_full(entry)
    
    def do_stats(self, arg: str) -> None:
        """显示统计信息"""
        stats = self.store.get_stats()
        
        print("\n=== 记忆统计 ===\n")
        print(f"总会话数：{stats['total_sessions']}")
        print(f"总记忆数：{stats['total_entries']}")
        
        print(f"\n按类型:")
        for t, count in stats.get("by_type", {}).items():
            print(f"  {t}: {count}")
        
        print(f"\n热门标签:")
        for tag, count in stats.get("top_tags", []):
            print(f"  #{tag}: {count}")
    
    def do_clear(self, arg: str) -> None:
        """清除记忆
        
        用法：/memory clear --confirm
        """
        if "--confirm" not in arg:
            print("⚠️  危险操作！请添加 --confirm 参数确认清除")
            print("   这将删除所有记忆数据，不可恢复！")
            return
        
        self.store.clear_all()
        print("✓ 所有记忆已清除")
    
    def do_session(self, arg: str) -> None:
        """查看会话详情
        
        用法：/memory session <session_id>
        """
        session_id = arg.strip()
        
        if not session_id:
            # 列出最近的会话
            sessions = self.store.get_recent_sessions(5)
            if not sessions:
                print("没有会话记录")
                return
            
            print("\n最近的会话:\n")
            for session in sessions:
                print(f"  {session.session_id}")
                print(f"    开始：{session.start_time}")
                print(f"    消息：{len(session.messages)} 条")
                print(f"    记忆：{len(session.memory_entries)} 条")
                print()
            return
        
        session = self.store.get_session(session_id)
        if not session:
            print(f"未找到会话：{session_id}")
            return
        
        print(f"\n=== 会话 {session_id} ===\n")
        print(f"开始时间：{session.start_time}")
        print(f"结束时间：{session.end_time or '进行中'}")
        print(f"消息数：{len(session.messages)}")
        print(f"记忆数：{len(session.memory_entries)}")
        
        if session.memory_entries:
            print(f"\n记忆条目:")
            for entry in session.memory_entries:
                self._print_entry(entry)
    
    def do_exit(self, arg: str) -> bool:
        """退出 CLI"""
        return True
    
    def do_quit(self, arg: str) -> bool:
        """退出 CLI"""
        return True
    
    def _print_entry(self, entry: Any) -> None:
        """打印记忆条目摘要"""
        icon = {
            MemoryContentType.SUCCESS: "✓",
            MemoryContentType.FAILURE: "✗",
            MemoryContentType.PATTERN: "📋",
            MemoryContentType.CONTEXT: "ℹ",
            MemoryContentType.SKILL: "🛠",
        }.get(entry.memory_type, "•")
        
        print(f"{icon} [{entry.memory_type.value}] {entry.id[:8]}...")
        print(f"  重要性：{'★' * int(entry.importance / 2)} ({entry.importance:.1f})")
        print(f"  内容：{entry.content[:100]}...")
        if entry.tags:
            print(f"  标签：{' '.join(entry.tags)}")
        print()
    
    def _print_entry_full(self, entry: Any) -> None:
        """打印记忆条目详情"""
        print(f"\n{'='*60}")
        print(f"ID: {entry.id}")
        print(f"类型：{entry.memory_type.value}")
        print(f"时间：{entry.timestamp}")
        print(f"重要性：{'★' * int(entry.importance / 2)} ({entry.importance:.1f}/10)")
        print(f"会话：{entry.session_id}")
        print(f"标签：{', '.join(entry.tags)}")
        print(f"\n内容:\n{entry.content}")
        
        if entry.patterns:
            print(f"\n模式:")
            for p in entry.patterns:
                print(f"  - {p.name}: {p.description}")
        
        if entry.metadata:
            print(f"\n元数据:")
            for k, v in entry.metadata.items():
                print(f"  {k}: {v}")
        
        print(f"{'='*60}\n")
    
    def _parse_args(self, arg: str, allow_positional: bool = False) -> dict[str, Any]:
        """解析命令行参数"""
        args = {}
        positional = []
        
        parts = arg.split()
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                args[key.strip()] = value.strip()
            elif allow_positional:
                positional.append(part)
        
        if allow_positional:
            args["_positional"] = positional
        
        return args


def create_memory_cli() -> MemoryCLI:
    """创建记忆 CLI"""
    return MemoryCLI()


if __name__ == "__main__":
    cli = create_memory_cli()
    cli.cmdloop()
