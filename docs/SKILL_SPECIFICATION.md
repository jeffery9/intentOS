# IntentOS Skill 规范

基于 Claude Skills 规范实现
https://github.com/anthropics/awesome-claude-skills

## 什么是 Skill

Skills 是模块化、自包含的包，通过提供专业知识、工作流和工具来扩展 AI 的能力。可以把它们想象成特定领域或任务的"入职指南"——将 AI 从通用助手转变为具备程序性知识的专业助手。

### Skill 提供什么

1. **专业工作流** - 特定领域的多步骤程序
2. **工具集成** - 使用特定文件格式或 API 的说明
3. **领域专业知识** - 公司特定知识、模式、业务逻辑
4. **捆绑资源** - 用于复杂重复任务的脚本、参考和资产

## Skill 结构

每个 Skill 由一个必需的 SKILL.md 文件和可选的捆绑资源组成：

```
skill-name/
├── SKILL.md (必需)
│   ├── YAML frontmatter metadata (必需)
│   │   ├── name: (必需)
│   │   └── description: (必需)
│   └── Markdown instructions (必需)
└── Bundled Resources (可选)
    ├── scripts/          - 可执行代码 (Python/Bash 等)
    ├── references/       - 按需加载到上下文的文档
    └── assets/           - 用于输出的文件 (模板、图标、字体等)
```

## SKILL.md (必需)

### YAML Frontmatter

```yaml
---
name: skill-name
description: 详细描述这个技能的用途。应该使用第三人称（例如"这个技能应该用于..."而不是"当...时使用这个技能"）。
license: MIT
---
```

**元数据质量：** YAML frontmatter 中的 `name` 和 `description` 决定 AI 何时使用这个技能。要具体说明技能做什么以及何时使用。

### Markdown 主体

SKILL.md 的 Markdown 部分应该包含：

1. **技能目的** - 用几句话说明
2. **使用时机** - 何时应该使用这个技能
3. **使用方法** - 实际上 AI 应该如何使用这个技能

**写作风格：** 使用**祈使/不定式形式**（动词优先的说明），而不是第二人称。使用客观、指导性的语言（例如"要完成 X，做 Y"而不是"你应该做 X"或"如果你需要做 X"）。

## 捆绑资源 (可选)

### Scripts (`scripts/`)

用于需要确定性可靠性或重复重写的任务的可执行代码（Python/Bash 等）。

**何时包含**：
- 当同一段代码被重复重写时
- 需要确定性可靠性时

**示例**：
- `scripts/rotate_pdf.py` - PDF 旋转任务
- `scripts/generate_report.py` - 报告生成

**优势**：
- Token 效率高
- 确定性
- 可以在不加载到上下文的情况下执行

**注意**：脚本可能仍需要被 AI 读取以进行修补或环境特定调整。

### References (`references/`)

文档和参考材料，用于按需加载到上下文中以告知 AI 的处理和思维。

**何时包含**：
- 用于 AI 工作时应该参考的文档

**示例**：
- `references/finance.md` - 财务模式
- `references/api_docs.md` - API 规范
- `references/policies.md` - 公司政策
- `references/schema.md` - 数据库模式

**用例**：
- 数据库模式
- API 文档
- 领域知识
- 公司政策
- 详细工作流指南

**优势**：
- 保持 SKILL.md 简洁
- 仅在 AI 确定需要时加载

**最佳实践**：
- 如果文件很大（>10k 词），在 SKILL.md 中包含 grep 搜索模式
- 避免重复：信息应该只在 SKILL.md 或 references 文件中，不要两者都有

### Assets (`assets/`)

不打算加载到上下文中，而是在 AI 生成的输出中使用的文件。

**何时包含**：
- 当技能需要在最终输出中使用的文件时

**示例**：
- `assets/logo.png` - 品牌资产
- `assets/slides.pptx` - PowerPoint 模板
- `assets/frontend-template/` - HTML/React 样板
- `assets/font.ttf` - 字体

**用例**：
- 模板
- 图片
- 图标
- 样板代码
- 字体
- 示例文档

**优势**：
- 将输出资源与文档分离
- 使 AI 能够使用文件而不必将它们加载到上下文中

## 渐进式披露设计原则

Skills 使用三级加载系统来有效管理上下文：

1. **元数据 (name + description)** - 始终在上下文中 (~100 词)
2. **SKILL.md 主体** - 当技能触发时 (<5k 词)
3. **捆绑资源** - 按需由 AI 加载 (无限*)

*无限是因为脚本可以在不读取到上下文窗口的情况下执行。

## 创建 Skill 的流程

### Step 1: 理解技能的具体示例

跳过此步骤的唯一情况是技能的用法模式已经清楚理解。

要创建有效的技能，清楚了解技能将如何使用的具体示例。这种理解可以来自直接用户示例或经用户反馈验证的生成示例。

例如，构建 image-editor 技能时，相关问题包括：

- "image-editor 技能应该支持什么功能？编辑、旋转，还有其他吗？"
- "你能举一些这个技能将如何使用的例子吗？"
- "我能想象用户会要求'从这张图片中去除红眼'或'旋转这张图片'。你还想象这个技能会以什么方式使用？"
- "用户会说什么来触发这个技能？"

### Step 2: 规划可重用的技能内容

要将具体示例转化为有效的技能，通过分析每个示例：

1. 考虑如何从头开始执行示例
2. 识别在重复执行这些工作流时什么脚本、参考和资产会有帮助

**示例**：构建 `pdf-editor` 技能来处理像"帮我旋转这个 PDF"这样的查询时，分析显示：

1. 旋转 PDF 需要每次都重写相同的代码
2. `scripts/rotate_pdf.py` 脚本会有帮助

**示例**：设计 `frontend-webapp-builder` 技能来处理像"给我构建一个 todo 应用"或"给我构建一个追踪步数的仪表板"这样的查询时，分析显示：

1. 编写前端 webapp 每次都需要相同的样板 HTML/React
2. 包含样板 HTML/React 项目文件的 `assets/hello-world/` 模板会有帮助

### Step 3: 初始化 Skill

使用 `init_skill.py` 脚本创建新的技能目录：

```bash
python -m intentos.integrations.init_skill <skill-name> --path <output-directory>
```

脚本会：
- 在指定路径创建技能目录
- 生成带有适当 frontmatter 和 TODO 占位符的 SKILL.md 模板
- 创建示例资源目录：`scripts/`、`references/` 和 `assets/`
- 在每个目录中添加示例文件，可以自定义或删除

### Step 4: 编辑 Skill

编辑（新生成或现有）技能时，记住技能是为另一个 AI 实例创建的。专注于包含对 AI 有益且非显而易见的信息。考虑什么程序性知识、领域特定细节或可重用资产会帮助另一个 AI 实例更有效地执行这些任务。

#### 从可重用的技能内容开始

开始实现时，从上面识别的可重用资源开始：`scripts/`、`references/` 和 `assets/` 文件。

#### 更新 SKILL.md

完成 SKILL.md，回答以下问题：

1. 技能的目的什么，用几句话说明？
2. 技能应该何时使用？
3. 实际上，AI 应该如何使用技能？上面开发的所有可重用技能内容都应该被引用，以便 AI 知道如何使用它们。

### Step 5: 打包 Skill

技能准备好后，应该打包到可分发的 zip 文件中与用户分享。打包过程首先自动验证技能以确保满足所有要求：

```bash
# 验证技能
python -m intentos.integrations.validate_skill <path/to/skill-folder>
```

如果验证通过，打包技能创建以技能命名的 zip 文件（例如 `my-skill.zip`），包含所有文件并保持适当的目录结构用于分发。

## 安装 Skill

将技能目录复制到 `~/.claude/skills/`：

```bash
cp -r my-skill ~/.claude/skills/
```

AI 会自动发现并加载已安装的 Skills。

## 示例 Skill

### 天气查询 Skill

```
weather-skill/
├── SKILL.md
├── scripts/
│   └── get_weather.py
├── references/
│   ├── api_docs.md
│   └── cities.json
└── assets/
    └── weather-icons/
```

### PDF 编辑器 Skill

```
pdf-editor/
├── SKILL.md
├── scripts/
│   ├── rotate_pdf.py
│   └── merge_pdfs.py
└── references/
    └── pdf_specification.md
```

### 品牌指南 Skill

```
brand-guidelines/
├── SKILL.md
├── references/
│   ├── logo_usage.md
│   └── color_palette.md
└── assets/
    ├── logo.png
    ├── templates/
    │   └── presentation.pptx
    └── fonts/
        └── brand-font.ttf
```

## 最佳实践

### 写作技巧

1. **使用第三人称** - "这个技能应该用于..."而不是"当...时使用这个技能"
2. **使用祈使形式** - "要完成 X，做 Y"而不是"你应该做 X"
3. **保持简洁** - SKILL.md 保持<5k 词，将详细信息移到 references
4. **包含具体示例** - 提供用户查询和预期响应的示例

### 资源组织

1. **避免重复** - 信息只在 SKILL.md 或 references 中，不要两者都有
2. **使用描述性名称** - 文件和目录名称应该清晰说明内容
3. **包含文档** - 为脚本和复杂资源提供文档
4. **测试资源** - 确保所有脚本和资产按预期工作

### 性能优化

1. **保持 SKILL.md 简洁** - 只包含核心程序性说明
2. **使用 references 存储详细信息** - 将大型文档移到 references 目录
3. **脚本优化** - 对于重复任务，使用脚本而不是重写代码
4. **资产分离** - 将输出资源与文档分离

## 验证

验证技能是否符合规范：

```bash
python -m intentos.integrations.validate_skill <path/to/skill>
```

检查项目：
- YAML frontmatter 格式和必需字段
- 技能命名约定和目录结构
- 描述完整性和质量
- 文件组织和资源引用

## 相关资源

- [Claude Skills 规范](https://github.com/anthropics/awesome-claude-skills)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [IntentOS 集成文档](./integrations/README.md)
