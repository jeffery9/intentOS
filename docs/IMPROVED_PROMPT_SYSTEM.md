# IntentOS 提示词系统改进文档

> **基于 Claude Code 提示词设计优化**

**版本**: v1.0  
**创建日期**: 2026-04-01  
**状态**: Released

---

## 概述

本次改进借鉴 Claude Code 的提示词设计，为 IntentOS 引入了：
- 静态/动态部分分离（缓存优化）
- 数值化输出约束
- 详细代码风格原则
- 风险控制机制
- 可配置输出风格

---

## 架构设计

### 提示词分层结构

```
┌─────────────────────────────────────────────────────────────┐
│                    系统提示词架构                            │
├─────────────────────────────────────────────────────────────┤
│  静态部分（可缓存）                                          │
│  ├── Intro: 身份定位和核心职责                               │
│  ├── System: 系统指令和行为规范                              │
│  ├── Tools: 工具使用规范                                     │
│  ├── Code Style: 代码风格原则 (9 条)                          │
│  ├── Actions: 风险控制指南                                   │
│  ├── Tone: 语气和风格                                        │
│  └── Efficiency: 输出效率约束                                │
├─────────────────────────────────────────────────────────────┤
│  动态边界标记：__INTENTOS_PROMPT_DYNAMIC_BOUNDARY__          │
├─────────────────────────────────────────────────────────────┤
│  动态部分（每回合可变）                                      │
│  ├── Language: 语言设置                                      │
│  ├── Environment: 环境信息                                   │
│  ├── Token Budget: Token 预算配置（可选）                     │
│  └── Output Style: 输出风格（concise/detailed/verbose）      │
└─────────────────────────────────────────────────────────────┘
```

### 模块结构

```
intentos/semantic_vm/prompts/
├── __init__.py           # 模块导出
├── builder.py            # 提示词构建器
├── sections.py           # 章节生成器
└── test_prompts.py       # 单元测试
```

---

## 核心改进点

### 1. 静态/动态分离

**设计**: 使用边界标记分隔静态和动态内容

```python
from intentos.semantic_vm.prompts import (
    build_system_prompt,
    SYSTEM_PROMPT_BOUNDARY,
    compute_prompt_cache_key,
)

sections = build_system_prompt(config)
cache_key = compute_prompt_cache_key(sections)
# 缓存键：4a0ea231619651ba1fbc01c3d7e4f45e (32 字符十六进制)
```

**优势**:
- LLM API 缓存优化（相同提示词复用响应）
- 减少 Token 消耗
- 提升响应速度

### 2. 数值化输出约束

**改进前**: "保持简洁"（定性描述）

**改进后**:
```
## 数值化约束
- 工具调用间文本 ≤ 50 字
- 最终回复 ≤ 200 字（除非任务需要更多细节）
```

**优势**: 更一致的输出质量，便于评估

### 3. 代码风格原则（9 条）

```python
# Code style
- 不要添加未请求的功能、重构或'改进'
- 不要添加注释、文档字符串或类型注解，除非逻辑不明显
- 不要创建一次性工具函数。三行相似代码好过早抽象
- 只验证系统边界（用户输入、外部 API）
- 不要添加错误处理、回退或验证不可能发生的场景
- 不要使用特性标志或向后兼容的 shims
- 默认不写注释。只在 WHY 不明显时添加
- 不要解释代码做什么（well-named identifier 已说明）
- 不要删除现有注释，除非你正在删除它们描述的代码
```

**优势**: 减少过度工程，保持代码简洁

### 4. 风险控制机制

**分类列表**:
- **破坏性操作**: 删除文件、分支、数据库表
- **难以撤销的操作**: 强制推送、`git reset --hard`
- **影响共享状态的操作**: PR、Issue、消息发送
- **上传到第三方**: pastebins、gists

**原则**: "measure twice, cut once"

### 5. 可配置输出风格

```python
config = PromptConfig(
    language="zh-CN",
    output_style="concise",  # concise | detailed | verbose
    token_budget=50000,
)
```

**风格模式**:
- **concise**: 直接答案，最小化解释
- **detailed**: 完整解释，包含背景
- **verbose**: 详尽分析，多种角度

---

## 使用指南

### 基础使用

```python
from intentos.semantic_vm.prompts import (
    PromptConfig,
    build_system_prompt,
    join_prompt_sections,
)

# 默认配置
config = PromptConfig()
sections = build_system_prompt(config)
full_prompt = join_prompt_sections(sections)

print(f"提示词：{len(full_prompt):,} 字符")
```

### 自定义配置

```python
config = PromptConfig(
    language="en-US",
    output_style="detailed",
    token_budget=100000,
    additional_dirs=["/data", "/models"],
    keep_coding_instructions=False,  # 禁用代码风格部分
)

sections = build_system_prompt(config)
```

### 编译器集成

```python
from intentos.compiler import IntentCompiler
from intentos.semantic_vm.prompts import PromptConfig

# 创建编译器（启用缓存）
compiler = IntentCompiler(
    prompt_config=PromptConfig(language="zh-CN"),
    enable_cache=True,
)

# 编译意图
compiled = compiler.compile(intent)

# 查看统计
stats = compiler.get_stats()
print(f"缓存命中率：{stats['cache_hits']/stats['compilations']*100:.1f}%")
```

---

## 性能对比

| 指标 | 改进前 | 改进后 | 提升 |
|------|--------|--------|------|
| 提示词结构 | 单一模板 | 静态/动态分离 | - |
| 缓存支持 | 无 | Blake2b 哈希键 | - |
| 代码风格 | 简单说明 | 9 条详细原则 | +900% |
| 风险控制 | 基础警告 | 分类详细列表 | +400% |
| 输出风格 | 单一模式 | 3 种模式 | +200% |
| Token 预算 | 无 | 可配置 | - |

---

## 演示示例

运行演示:
```bash
cd /Users/jeffery/_project/IntentOS
python examples/demo_improved_prompts.py
```

运行测试:
```bash
# 使用 pytest
pytest tests/unit/test_prompts.py -v

# 或直接运行
python tests/unit/test_prompts.py
```

---

## 参考文档

- [Claude Code System Prompt](../../Downloads/prompts.text) - 原始设计
- [架构文档](./docs/ARCHITECTURE.md) - IntentOS 完整架构
- [编译器 API](./docs/06-api/02-compiler-api.md) - 编译器接口

---

## 后续优化

1. **MCP 服务器指令集成**: 动态加载 MCP 服务器指令
2. **技能发现指导**: 集成 Skill Discovery 机制
3. **验证代理**: 非平凡修改需独立验证
4. **子代理协作**: Fork/Explore/Verify 模式

---

**最后更新**: 2026-04-01  
**版本**: v1.0.0
