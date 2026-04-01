# -*- coding: utf-8 -*-
"""
IntentOS Shadow Agent

影子 Agent - 对话回顾机制
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .models import MemoryEntry, MemoryContentType, Pattern, SessionMemory

logger = logging.getLogger(__name__)


@dataclass
class ShadowAgentConfig:
    """影子 Agent 配置"""
    # 是否自动回顾
    auto_review: bool = True
    # 回顾触发延迟（秒）
    review_delay: float = 1.0
    # 最小重要性评分（低于此值不记录）
    min_importance: float = 3.0
    # 成功模式关键词
    success_keywords: list[str] = None
    # 失败模式关键词
    failure_keywords: list[str] = None
    
    def __post_init__(self):
        if self.success_keywords is None:
            self.success_keywords = [
                "完成", "成功", "解决", "搞定", "好了", "正确", "通过",
                "success", "done", "completed", "fixed", "solved",
            ]
        if self.failure_keywords is None:
            self.failure_keywords = [
                "错误", "失败", "问题", "bug", "异常", "不行", "错了",
                "error", "fail", "issue", "bug", "exception", "wrong",
            ]


class ShadowAgent:
    """
    影子 Agent - 对话回顾
    
    在每次对话后自动回顾，提取值得记录的内容：
    - 成功做法（不仅记错误）
    - 失败教训
    - 识别的模式
    - 上下文信息
    """
    
    def __init__(self, session_id: str, config: Optional[ShadowAgentConfig] = None):
        self.session_id = session_id
        self.config = config or ShadowAgentConfig()
        self.memory = SessionMemory(session_id=session_id)
        self._reviewed = False
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息到会话"""
        self.memory.add_message(role, content)
    
    def end_session(self) -> None:
        """结束会话，触发回顾"""
        self.memory.end_session()
        
        if self.config.auto_review and not self._reviewed:
            self.review_conversation()
            self._reviewed = True
    
    def review_conversation(self) -> list[MemoryEntry]:
        """
        回顾对话，提取值得记录的内容
        
        Returns:
            生成的记忆条目列表
        """
        logger.info(f"ShadowAgent 开始回顾会话 {self.session_id}")
        
        entries = []
        
        # 1. 提取成功做法
        successes = self._extract_successes()
        for success in successes:
            entry = self._create_entry(
                memory_type=MemoryContentType.SUCCESS,
                content=success["content"],
                metadata={"context": success.get("context", "")},
                importance=success.get("importance", 6.0),
            )
            if entry:  # 可能因重要性不足被过滤
                entries.append(entry)
                self.memory.add_memory_entry(entry)
        
        # 2. 提取失败教训
        failures = self._extract_failures()
        for failure in failures:
            entry = self._create_entry(
                memory_type=MemoryContentType.FAILURE,
                content=failure["content"],
                metadata={
                    "error": failure.get("error", ""),
                    "solution": failure.get("solution", ""),
                },
                importance=failure.get("importance", 7.0),
            )
            if entry:
                entries.append(entry)
                self.memory.add_memory_entry(entry)
        
        # 3. 识别模式
        patterns = self._extract_patterns()
        for pattern in patterns:
            entry = self._create_entry(
                memory_type=MemoryContentType.PATTERN,
                content=pattern.description,
                patterns=[pattern],
                importance=5.0 + pattern.confidence * 5,  # 置信度越高越重要
            )
            if entry:
                entries.append(entry)
                self.memory.add_memory_entry(entry)
        
        # 4. 提取上下文（总是记录）
        context_entry = self._create_entry(
            memory_type=MemoryContentType.CONTEXT,
            content=self._summarize_context(),
            metadata=self._extract_context_metadata(),
            importance=3.0,
        )
        if context_entry:
            entries.append(context_entry)
            self.memory.add_memory_entry(context_entry)
        
        logger.info(f"ShadowAgent 回顾完成，生成 {len(entries)} 条记忆")
        return entries
    
    def _create_entry(
        self,
        memory_type: MemoryContentType,
        content: str,
        metadata: Optional[dict] = None,
        patterns: Optional[list[Pattern]] = None,
        importance: float = 5.0,
    ) -> Optional[MemoryEntry]:
        """创建记忆条目"""
        if importance < self.config.min_importance:
            return None  # 过滤低重要性记忆
        
        return MemoryEntry(
            session_id=self.session_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            patterns=patterns or [],
            importance=importance,
            tags=self._generate_tags(memory_type, content),
        )
    
    def _extract_successes(self) -> list[dict[str, Any]]:
        """提取成功做法"""
        successes = []
        
        # 分析对话，查找成功模式
        for i, msg in enumerate(self.memory.messages):
            if msg["role"] != "assistant":
                continue
            
            content = msg["content"]
            
            # 检查是否包含成功关键词
            if any(kw in content.lower() for kw in self.config.success_keywords):
                # 检查是否有用户正面反馈（下一条消息）
                has_positive_feedback = False
                if i + 1 < len(self.memory.messages):
                    next_msg = self.memory.messages[i + 1]
                    if next_msg["role"] == "user":
                        if any(kw in next_msg["content"] for kw in ["好", "对", "谢谢", "可以", "ok"]):
                            has_positive_feedback = True
                
                # 提取成功内容
                success_content = self._extract_key_content(content)
                if success_content:
                    successes.append({
                        "content": success_content,
                        "context": self._get_context(i),
                        "importance": 7.0 if has_positive_feedback else 5.0,
                    })
        
        return successes
    
    def _extract_failures(self) -> list[dict[str, Any]]:
        """提取失败教训"""
        failures = []
        
        for i, msg in enumerate(self.memory.messages):
            content = msg["content"]
            
            # 检查是否包含失败关键词
            if any(kw in content.lower() for kw in self.config.failure_keywords):
                # 尝试提取错误信息
                error_info = self._extract_error_info(content)
                
                # 尝试提取解决方案（如果有后续消息）
                solution = ""
                if i + 1 < len(self.memory.messages):
                    next_msg = self.memory.messages[i + 1]
                    if next_msg["role"] == "assistant":
                        solution = self._extract_solution(next_msg["content"])
                
                failures.append({
                    "content": self._extract_key_content(content),
                    "error": error_info,
                    "solution": solution,
                    "importance": 8.0 if solution else 6.0,  # 有解决方案的失败更重要
                })
        
        return failures
    
    def _extract_patterns(self) -> list[Pattern]:
        """识别模式"""
        patterns = []
        
        # 分析对话中的重复模式
        # 1. 检查重复出现的问题类型
        question_patterns = self._find_question_patterns()
        patterns.extend(question_patterns)
        
        # 2. 检查重复的解决路径
        solution_patterns = self._find_solution_patterns()
        patterns.extend(solution_patterns)
        
        # 3. 检查工作流模式
        workflow_patterns = self._find_workflow_patterns()
        patterns.extend(workflow_patterns)
        
        return patterns
    
    def _find_question_patterns(self) -> list[Pattern]:
        """查找问题模式"""
        # 简化实现：查找类似问题
        questions = [
            msg["content"]
            for msg in self.memory.messages
            if msg["role"] == "user" and ("?" in msg["content"] or "怎么" in msg["content"] or "如何" in msg["content"])
        ]
        
        if len(questions) >= 2:
            return [Pattern(
                name="用户提问模式",
                description=f"会话中包含 {len(questions)} 个问题",
                trigger_keywords=["怎么", "如何", "?"],
                confidence=min(1.0, len(questions) / 5),
                occurrences=len(questions),
            )]
        
        return []
    
    def _find_solution_patterns(self) -> list[Pattern]:
        """查找解决路径模式"""
        # 简化实现：查找代码块或步骤说明
        solutions = []
        for msg in self.memory.messages:
            if msg["role"] == "assistant":
                content = msg["content"]
                if "```" in content or "步骤" in content or "第一步" in content:
                    solutions.append(content)
        
        if solutions:
            return [Pattern(
                name="解决路径",
                description=f"提供了 {len(solutions)} 个解决方案",
                steps=[s[:200] for s in solutions[:3]],  # 只取前 3 个，每个 200 字
                confidence=min(1.0, len(solutions) / 3),
                occurrences=len(solutions),
            )]
        
        return []
    
    def _find_workflow_patterns(self) -> list[Pattern]:
        """查找工作流模式"""
        # 分析完整的任务执行链条
        workflow_steps = []
        for msg in self.memory.messages:
            if msg["role"] == "assistant":
                content = msg["content"]
                # 检测是否包含执行步骤
                if any(kw in content for kw in ["执行", "运行", "调用", "创建", "修改"]):
                    workflow_steps.append(content[:100])
        
        if len(workflow_steps) >= 2:
            return [Pattern(
                name="工作流",
                description=f"包含 {len(workflow_steps)} 步操作",
                steps=workflow_steps[:5],
                confidence=min(1.0, len(workflow_steps) / 5),
                occurrences=len(workflow_steps),
            )]
        
        return []
    
    def _extract_key_content(self, content: str) -> str:
        """提取关键内容"""
        # 提取代码块
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)
        if code_blocks:
            return "\n\n".join(code_blocks[:2])
        
        # 提取关键句子
        lines = content.split("\n")
        key_lines = [
            line.strip()
            for line in lines
            if len(line.strip()) > 10 and not line.strip().startswith("#")
        ]
        
        return "\n".join(key_lines[:5])
    
    def _extract_error_info(self, content: str) -> str:
        """提取错误信息"""
        # 查找错误堆栈或错误消息
        error_patterns = [
            r"Error:.*",
            r"错误：.*",
            r"Exception:.*",
            r"Traceback.*",
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)[:200]
        
        return content[:200]
    
    def _extract_solution(self, content: str) -> str:
        """提取解决方案"""
        # 查找解决方案关键词
        solution_keywords = ["修复", "解决", "修改", "改为", "fix", "solution"]
        
        lines = content.split("\n")
        for line in lines:
            if any(kw in line.lower() for kw in solution_keywords):
                return line.strip()[:200]
        
        return ""
    
    def _get_context(self, message_index: int) -> str:
        """获取上下文"""
        # 获取前后消息作为上下文
        start = max(0, message_index - 2)
        end = min(len(self.memory.messages), message_index + 3)
        
        context_messages = self.memory.messages[start:end]
        return "\n".join([f"{m['role']}: {m['content'][:100]}" for m in context_messages])
    
    def _summarize_context(self) -> str:
        """总结上下文"""
        return f"会话 {self.session_id} 包含 {len(self.memory.messages)} 条消息"
    
    def _extract_context_metadata(self) -> dict[str, Any]:
        """提取上下文元数据"""
        return {
            "message_count": len(self.memory.messages),
            "user_messages": sum(1 for m in self.memory.messages if m["role"] == "user"),
            "assistant_messages": sum(1 for m in self.memory.messages if m["role"] == "assistant"),
            "duration_seconds": (
                (self.memory.end_time - self.memory.start_time).total_seconds()
                if self.memory.end_time
                else 0
            ),
        }
    
    def _generate_tags(self, memory_type: MemoryType, content: str) -> list[str]:
        """生成标签"""
        tags = [memory_type.value]
        
        # 根据内容提取技术标签
        tech_keywords = {
            "python": ["python", "py", "def ", "import "],
            "shell": ["bash", "sh", "cmd", "$ ", "sudo"],
            "api": ["api", "http", "request", "response", "json"],
            "database": ["sql", "database", "query", "select"],
            "test": ["test", "assert", "pytest", "unittest"],
        }
        
        content_lower = content.lower()
        for tag, keywords in tech_keywords.items():
            if any(kw in content_lower for kw in keywords):
                tags.append(tag)
        
        return tags
    
    def get_memory(self) -> SessionMemory:
        """获取会话记忆"""
        return self.memory
