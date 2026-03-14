"""
语义 VM 模块

IntentOS 的核心：语义虚拟机
- 指令集：语义指令 (CREATE/MODIFY/QUERY/LOOP/WHILE/IF...)
- 处理器：LLM
- 内存：语义存储
- 图灵完备：是
"""

from .vm import (
    LLMProcessor,
    SemanticInstruction,
    SemanticMemory,
    SemanticOpcode,
    SemanticProgram,
    SemanticVM,
    create_instruction,
    create_program,
    create_semantic_vm,
)

__all__ = [
    "SemanticVM",
    "SemanticInstruction",
    "SemanticProgram",
    "SemanticMemory",
    "LLMProcessor",
    "SemanticOpcode",
    "create_semantic_vm",
    "create_program",
    "create_instruction",
]
