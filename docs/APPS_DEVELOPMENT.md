# IntentOS 应用层开发指南

## 概述

应用层 (Layer 1) 是 3 层 7 级架构的最上层，负责：
- 领域意图包
- 用户交互
- 结果呈现

本指南教你如何基于应用层框架开发新应用。

---

## 快速开始

### 1. 创建应用类

```python
from intentos.apps import AppBase, AppContext, AppResult, app_metadata

@app_metadata(
    app_id="my_app",
    name="我的应用",
    description="应用描述",
    version="1.0.0",
    category="productivity",
    icon="🚀",
    author="你的名字"
)
class MyApp(AppBase):
    """我的应用"""
    
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        """执行应用"""
        # 实现你的逻辑
        return AppResult(
            success=True,
            message="✓ 完成",
            data={"result": "数据"},
        )
    
    def get_capabilities(self) -> list[str]:
        """获取能力列表"""
        return ["能力 1", "能力 2", "能力 3"]
```

### 2. 注册应用

```python
from intentos.apps import get_app_layer

layer = get_app_layer()

# 注册应用
app = MyApp()
layer.register_app(app)

# 注册意图模板
from intentos.apps import IntentTemplate

layer.register_template(IntentTemplate(
    id="my_intent",
    name="我的意图",
    description="描述",
    keywords=["关键词 1", "关键词 2"],
    category="my_app",
))
```

### 3. 使用应用

```python
# 执行意图
result = await layer.execute("安排会议")
print(result.message)
```

---

## 应用开发详解

### 应用元数据

```python
@app_metadata(
    app_id="unique_id",       # 唯一标识
    name="应用名称",           # 显示名称
    description="应用描述",     # 简短描述
    version="1.0.0",          # 版本号
    category="分类",           # 分类：productivity/analysis/creation 等
    icon="📱",                # 图标 emoji
    author="作者"              # 作者信息
)
```

### 生命周期方法

```python
class MyApp(AppBase):
    async def initialize(self, services) -> bool:
        """初始化时调用"""
        await super().initialize(services)
        # 加载配置、初始化资源等
        return True
    
    async def shutdown(self) -> None:
        """关闭时调用"""
        # 清理资源
        pass
```

### 执行方法

```python
async def execute(self, intent: str, context: AppContext) -> AppResult:
    """
    执行应用
    
    Args:
        intent: 用户输入的自然语言
        context: 应用上下文（用户信息、会话等）
    
    Returns:
        AppResult: 执行结果
    """
    # 1. 解析意图
    # 2. 执行逻辑
    # 3. 返回结果
    return AppResult(
        success=True,
        message="✓ 完成",
        data={"key": "value"},
        next_actions=["建议 1", "建议 2"],
    )
```

### 能力列表

```python
def get_capabilities(self) -> list[str]:
    """返回应用能做什么"""
    return [
        "能力 1 描述",
        "能力 2 描述",
    ]
```

---

## 意图模板

### 定义模板

```python
IntentTemplate(
    id="template_id",
    name="模板名称",
    description="模板描述",
    
    # 匹配规则
    patterns=[r"正则.*表达式"],
    keywords=["关键词 1", "关键词 2"],
    exact_matches=["精确匹配"],
    
    # 处理
    handler=self.my_handler,  # 直接绑定处理函数
    handler_name="my_handler",  # 或延迟绑定
    
    # 分类
    category="my_app",
    tags=["标签 1", "标签 2"],
    
    # 优先级
    priority=0,
)
```

### 匹配规则

```python
# 关键词匹配
keywords=["会议", "安排"]
# 匹配："安排会议"、"明天有会议"

# 正则匹配
patterns=[r"安排.*会议", r"预约.*时间"]
# 匹配："安排下午 3 点的会议"、"预约见面时间"

# 精确匹配
exact_matches=["你好", "帮助"]
# 只匹配："你好"、"帮助"
```

---

## 使用服务

### 日志服务

```python
self.log("info", "信息日志")
self.log("warning", "警告日志")
self.log("error", "错误日志")

# 快捷方法
self.info("信息")
self.debug("调试")
self.warning("警告")
self.error("错误")
```

### 配置服务

```python
# 获取配置
value = await self.get_config("key", default="default")

# 设置配置
await self.set_config("key", "value")
```

### 存储服务

```python
# 获取存储
value = await self.get_storage("key", default=None)

# 设置存储
await self.set_storage("key", {"data": "value"})

# 列出所有存储
all_data = await self.list_storage()
```

### LLM 服务

```python
# 调用 LLM
response = await self.services.call_llm(
    prompt="分析这个数据",
    system_prompt="你是数据分析助手"
)
```

---

## 完整示例

### 示例 1: 数据分析应用

```python
from intentos.apps import AppBase, AppContext, AppResult, app_metadata

@app_metadata(
    app_id="data_analyst",
    name="数据分析师",
    description="用自然语言分析数据",
    category="analysis",
    icon="📊"
)
class DataAnalystApp(AppBase):
    
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        # 调用 LLM 分析
        response = await self.services.call_llm(
            prompt=f"分析数据：{intent}"
        )
        
        return AppResult(
            success=True,
            message="✓ 分析完成",
            data={
                "analysis": response,
                "chart_url": "https://...",
            },
            next_actions=["下载报告", "分享给团队"],
        )
    
    def get_capabilities(self) -> list[str]:
        return [
            "自然语言查询",
            "自动图表生成",
            "趋势分析",
        ]
```

### 示例 2: 内容创作应用

```python
@app_metadata(
    app_id="content_creator",
    name="内容创作",
    description="生成文章、报告、文案",
    category="creation",
    icon="✍️"
)
class ContentCreatorApp(AppBase):
    
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        # 调用 LLM 创作
        content = await self.services.call_llm(
            prompt=f"创作内容：{intent}",
            system_prompt="你是专业内容创作者"
        )
        
        return AppResult(
            success=True,
            message="✓ 内容已生成",
            data={
                "word_count": len(content),
                "content": content,
            },
            next_actions=["编辑", "发布", "分享"],
        )
    
    def get_capabilities(self) -> list[str]:
        return [
            "文章生成",
            "文案优化",
            "多语言翻译",
        ]
```

---

## 最佳实践

### 1. 错误处理

```python
async def execute(self, intent: str, context: AppContext) -> AppResult:
    try:
        # 你的逻辑
        result = await self.do_something(intent)
        return AppResult(success=True, message="✓ 完成", data=result)
    except Exception as e:
        self.error(f"执行失败：{e}")
        return AppResult(
            success=False,
            message="执行失败",
            error=str(e),
        )
```

### 2. 权限检查

```python
async def execute(self, intent: str, context: AppContext) -> AppResult:
    # 检查权限
    if "admin" not in context.permissions:
        return AppResult(
            success=False,
            message="权限不足",
            error="permission_denied",
        )
    
    # 继续执行...
```

### 3. 上下文利用

```python
async def execute(self, intent: str, context: AppContext) -> AppResult:
    # 使用用户信息
    user_id = context.user_id
    
    # 使用会话历史
    history = context.conversation_history
    
    # 使用自定义数据
    custom_data = context.data.get("key")
```

---

## 调试技巧

### 1. 启用调试日志

```python
import logging
logging.getLogger("intentos.apps").setLevel(logging.DEBUG)
```

### 2. 测试应用

```python
async def test_app():
    app = MyApp()
    await app.initialize()
    
    result = await app.execute(
        "测试意图",
        AppContext(user_id="test_user")
    )
    
    print(result.to_dict())
```

---

## 总结

开发 IntentOS 应用的步骤：

1. **定义应用** - 继承 `AppBase`，使用`@app_metadata`
2. **实现逻辑** - 实现 `execute()`和`get_capabilities()`
3. **注册应用** - `layer.register_app(app)`
4. **注册模板** - `layer.register_template(template)`
5. **测试调试** - 使用测试工具验证

**现在就开始开发你的应用吧！** 🚀
