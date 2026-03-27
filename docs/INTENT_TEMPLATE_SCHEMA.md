# IntentOS 意图模板参数化 Schema 规范

**版本**: 1.0  
**日期**: 2026-03-27  
**状态**: ✅ 完成

---

## 📋 概述

意图模板 (Intent Template) 是 IntentOS 中**从模糊自然语言转向结构化任务规划**的核心机制。通过参数化 Schema 定义，系统能够将用户输入的自然语言解析为包含精确参数的结构化指令。

### 核心洞察

```
自然语言输入 → [意图模板解析] → 结构化参数 → [任务规划] → DAG → [能力绑定] → PEF 执行
```

---

## 🎯 意图模板的四个层次

### Level 1: 动作与目标识别

```yaml
intents:
  - name: "query_sales"
    action: "query"        # 动作类型
    target: "sales_data"   # 操作对象
    description: "查询销售数据"
```

**动作类型枚举**:
- `query`: 查询数据
- `analyze`: 分析趋势
- `compare`: 对比差异
- `generate`: 生成内容
- `execute`: 执行操作
- `monitor`: 监控状态

### Level 2: 参数提取 Schema

```yaml
intents:
  - name: "query_sales"
    parameters:
      # 必需参数
      - name: "region"
        type: "string"
        required: true
        extraction:
          patterns: ["{region}", "在{region}", "{region}地区"]
          synonyms: ["区域", "地区", "大区"]
          enum: ["华东", "华南", "华北", "华西"]
      
      # 可选参数
      - name: "period"
        type: "string"
        required: false
        default: "本月"
        extraction:
          patterns: ["{period}", "{period}的", "从{start}到{end}"]
          synonyms: ["时间", "周期", "期间"]
```

### Level 3: 任务规划映射

```yaml
intents:
  - name: "query_sales"
    task_plan:
      # 任务 DAG 定义
      - step: 1
        action: "validate_params"
        inputs:
          - region
          - period
      
      - step: 2
        action: "load_data"
        capability: "data_loader"
        inputs:
          region: "${region}"
          period: "${period}"
        depends_on: [1]
      
      - step: 3
        action: "format_result"
        inputs:
          data: "${step2.output}"
        depends_on: [2]
```

### Level 4: IO 能力绑定

```yaml
intents:
  - name: "query_sales"
    capability_bindings:
      - capability: "data_loader"
        parameters:
          - source: "region"
            target: "region"
            required: true
          - source: "period"
            target: "time_range"
            required: true
      
      - capability: "result_formatter"
        parameters:
          - source: "step2.output"
            target: "data"
            required: true
```

---

## 📝 参数化 Schema 详细规范

### 参数定义结构

```yaml
parameters:
  - name: "parameter_name"      # 参数名称（唯一标识）
    type: "string"              # 参数类型
    description: "参数描述"       # 参数说明
    required: true              # 是否必需
    default: "default_value"    # 默认值（可选参数）
    
    # 提取规则
    extraction:
      patterns: []              # 提取模式
      synonyms: []              # 同义词
      regex: "regex_pattern"    # 正则表达式（可选）
    
    # 约束条件
    constraints:
      enum: []                  # 枚举值
      min: 0                    # 最小值（数字类型）
      max: 100                  # 最大值（数字类型）
      min_length: 1             # 最小长度（字符串）
      max_length: 100           # 最大长度（字符串）
      pattern: "regex"          # 模式匹配（字符串）
    
    # 验证规则
    validation:
      rules: []                 # 验证规则列表
      error_message: "错误提示"  # 验证失败提示
    
    # 参数转换
    transform:
      type: "uppercase"         # 转换类型
      mapping: {}               # 值映射
```

### 参数类型系统

| 类型 | 说明 | 示例 |
|------|------|------|
| `string` | 字符串 | `"华东"` |
| `number` | 数字（整数/浮点） | `100`, `3.14` |
| `integer` | 整数 | `42` |
| `boolean` | 布尔值 | `true`, `false` |
| `array` | 数组 | `["华东", "华南"]` |
| `object` | 对象 | `{"region": "华东"}` |
| `enum` | 枚举值 | `"Q1"` |
| `date` | 日期 | `"2026-03-27"` |
| `datetime` | 日期时间 | `"2026-03-27T10:00:00"` |
| `time_range` | 时间范围 | `{"start": "2026-01-01", "end": "2026-03-31"}` |

---

## 🔧 参数提取机制

### 1. 模式匹配提取

```yaml
intents:
  - name: "query_sales"
    patterns:
      - "查询 {region} {period} 的销售数据"
      - "{region} {period} 卖得怎么样"
      - "看看{region}的{period}业绩"
    
    parameters:
      - name: "region"
        type: "string"
        extraction:
          patterns:
            - "{region}"
            - "在{region}"
            - "{region}地区"
          synonyms:
            - "区域"
            - "地区"
            - "大区"
```

**提取过程**:
```
用户输入："查询华东区 Q1 的销售数据"
     ↓
模式匹配："查询 {region} {period} 的销售数据"
     ↓
参数提取：region="华东区", period="Q1"
     ↓
验证：region ∈ ["华东", "华南", "华北", "华西"] ✓
     ↓
标准化：region="华东", period="Q1"
```

### 2. 正则表达式提取

```yaml
parameters:
  - name: "email"
    type: "string"
    extraction:
      regex: "([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})"
    
  - name: "phone"
    type: "string"
    extraction:
      regex: "(1[3-9]\\d{9})"
```

### 3. 上下文提取

```yaml
intents:
  - name: "compare_sales"
    parameters:
      - name: "region1"
        type: "string"
        extraction:
          context: "previous_region"  # 从上下文获取
      
      - name: "region2"
        type: "string"
        required: true
```

---

## 🗺️ 任务规划映射

### DAG 生成规则

```yaml
intents:
  - name: "analyze_sales"
    task_plan:
      # 步骤 1: 参数验证
      - id: "validate"
        type: "validation"
        inputs:
          - region
          - period
          - metrics
        
      # 步骤 2: 数据加载
      - id: "load_data"
        type: "capability_call"
        capability: "data_loader"
        inputs:
          region: "${region}"
          period: "${period}"
        depends_on: ["validate"]
        
      # 步骤 3: 数据分析
      - id: "analyze"
        type: "capability_call"
        capability: "data_analyzer"
        inputs:
          data: "${load_data.output}"
          metrics: "${metrics}"
        depends_on: ["load_data"]
        
      # 步骤 4: 结果格式化
      - id: "format"
        type: "transformation"
        inputs:
          analysis_result: "${analyze.output}"
        depends_on: ["analyze"]
```

### 条件分支

```yaml
task_plan:
  - id: "check_cache"
    type: "condition"
    condition: "cache.exists(${region}, ${period})"
    
  - id: "load_from_cache"
    type: "capability_call"
    capability: "cache_loader"
    inputs:
      key: "${region}_${period}"
    depends_on: ["check_cache"]
    condition: "check_cache.result == true"
  
  - id: "load_from_db"
    type: "capability_call"
    capability: "data_loader"
    inputs:
      region: "${region}"
      period: "${period}"
    depends_on: ["check_cache"]
    condition: "check_cache.result == false"
```

---

## 🔗 IO 能力参数绑定

### 绑定规则

```yaml
intents:
  - name: "query_sales"
    capability_bindings:
      # 绑定 data_loader 能力
      - capability: "data_loader"
        description: "加载销售数据"
        parameters:
          # 参数映射
          - source: "region"           # 意图参数
            target: "region"           # 能力参数
            required: true
            transform: "normalize_region"  # 转换函数
          
          - source: "period"
            target: "time_range"
            required: true
            transform: "parse_period"
        
        # 输出映射
        output:
          - source: "data"
            target: "sales_data"
            transform: "validate_data"
```

### Loop 机制驱动

```
┌─────────────────────────────────────────────────────────┐
│  LLM 执行循环 (Loop Mechanism)                           │
├─────────────────────────────────────────────────────────┤
│  1. 接收 PEF 指令流                                      │
│  2. 解析意图参数：region="华东", period="Q1"            │
│  3. 判断是否需要调用能力 → 是                            │
│  4. 查找能力绑定：data_loader                           │
│  5. 填充能力参数：                                       │
│     - region: "华东" (来自意图参数)                      │
│     - time_range: "2026-01-01~2026-03-31" (转换后)      │
│  6. 执行能力调用 → 返回数据                              │
│  7. 继续执行后续指令                                     │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ 验证与约束

### Schema 验证

```yaml
validation:
  # 参数级别验证
  parameters:
    - name: "region"
      rules:
        - type: "required"
          message: "区域参数不能为空"
        - type: "enum"
          values: ["华东", "华南", "华北", "华西"]
          message: "区域必须是有效值"
    
    - name: "period"
      rules:
        - type: "pattern"
          pattern: "^Q[1-4]$|^(本月 | 上月 | 本年)$"
          message: "时间周期格式不正确"
  
  # 跨参数验证
  cross_parameter:
    - rule: "region != '全国' or period.length <= 2"
      message: "全国范围只能查询单个季度"
  
  # 业务规则验证
  business_rules:
    - rule: "has_permission(user, region)"
      message: "用户没有该区域的访问权限"
```

### 形式化验证

```python
# 验证示例
def validate_intent_template(template: dict) -> ValidationResult:
    errors = []
    
    # 1. 检查参数唯一性
    param_names = [p["name"] for p in template["parameters"]]
    if len(param_names) != len(set(param_names)):
        errors.append("参数名称必须唯一")
    
    # 2. 检查能力引用有效性
    for binding in template.get("capability_bindings", []):
        if not capability_exists(binding["capability"]):
            errors.append(f"能力 {binding['capability']} 未注册")
    
    # 3. 检查任务 DAG 有效性
    dag = template.get("task_plan", [])
    if has_cycle(dag):
        errors.append("任务规划存在循环依赖")
    
    # 4. 检查参数类型匹配
    for binding in template.get("capability_bindings", []):
        for param in binding.get("parameters", []):
            if not type_matches(param["source"], param["target"]):
                errors.append(f"参数类型不匹配：{param['source']} -> {param['target']}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )
```

---

## 📊 资源配额管理

### 基于参数的配额计算

```yaml
quota:
  # 基础配额
  base:
    max_execution_time: 30  # 秒
    max_token_usage: 5000   # tokens
    max_memory: "256MB"     # 内存
  
  # 参数化调整
  adjustments:
    - parameter: "region"
      condition: "region == '全国'"
      multiplier: 3.0  # 全国范围配额 x3
    
    - parameter: "include_details"
      condition: "include_details == true"
      multiplier: 2.0  # 包含详情配额 x2
  
  # 动态配额
  dynamic:
    formula: "base + (data_size * 0.1) + (complexity * 100)"
    variables:
      data_size: "${load_data.output.size}"
      complexity: "${analyze.complexity_score}"
```

### 用量计量

```yaml
metering:
  metrics:
    - name: "execution_count"
      type: "counter"
      labels:
        - intent_name
        - region
        - status
    
    - name: "token_usage"
      type: "counter"
      labels:
        - intent_name
        - model_type
    
    - name: "execution_time"
      type: "histogram"
      labels:
        - intent_name
        - data_size
      buckets: [100, 500, 1000, 5000, 10000]  # ms
```

---

## 🎯 完整示例

### 查询销售数据意图模板

```yaml
intents:
  - name: "query_sales"
    description: "查询指定区域和时间的销售数据"
    action: "query"
    target: "sales_data"
    
    # 自然语言模式
    patterns:
      - "查询 {region} {period} 的销售数据"
      - "{region} {period} 卖得怎么样"
      - "看看{region}的{period}业绩"
    
    # 参数定义
    parameters:
      - name: "region"
        type: "string"
        description: "销售区域"
        required: true
        extraction:
          patterns:
            - "{region}"
            - "在{region}"
          synonyms:
            - "区域"
            - "地区"
        constraints:
          enum: ["华东", "华南", "华北", "华西", "全国"]
        transform:
          mapping:
            "华东区": "华东"
            "华南区": "华南"
            "华北区": "华北"
            "华西区": "华西"
      
      - name: "period"
        type: "string"
        description: "时间周期"
        required: true
        default: "本月"
        extraction:
          patterns:
            - "{period}"
            - "{period}的"
        constraints:
          pattern: "^Q[1-4]$|^(本月 | 上月 | 本年)$"
        transform:
          type: "uppercase"
    
    # 任务规划
    task_plan:
      - id: "validate"
        type: "validation"
        inputs: [region, period]
      
      - id: "check_cache"
        type: "condition"
        condition: "cache.exists(region, period)"
        depends_on: ["validate"]
      
      - id: "load_from_cache"
        type: "capability_call"
        capability: "cache_loader"
        inputs:
          key: "${region}_${period}"
        depends_on: ["check_cache"]
        condition: "check_cache.result == true"
      
      - id: "load_from_db"
        type: "capability_call"
        capability: "data_loader"
        inputs:
          region: "${region}"
          period: "${period}"
        depends_on: ["check_cache"]
        condition: "check_cache.result == false"
      
      - id: "merge_results"
        type: "transformation"
        inputs:
          cache_data: "${load_from_cache.output|optional}"
          db_data: "${load_from_db.output|optional}"
        depends_on: ["load_from_cache", "load_from_db"]
      
      - id: "format_result"
        type: "capability_call"
        capability: "result_formatter"
        inputs:
          data: "${merge_results.output}"
          format: "json"
        depends_on: ["merge_results"]
    
    # 能力绑定
    capability_bindings:
      - capability: "cache_loader"
        parameters:
          - source: "region"
            target: "region"
          - source: "period"
            target: "period"
      
      - capability: "data_loader"
        parameters:
          - source: "region"
            target: "region"
            transform: "normalize_region"
          - source: "period"
            target: "time_range"
            transform: "parse_period"
      
      - capability: "result_formatter"
        parameters:
          - source: "merge_results.output"
            target: "data"
    
    # 验证规则
    validation:
      parameters:
        - name: "region"
          rules:
            - type: "required"
            - type: "enum"
              values: ["华东", "华南", "华北", "华西", "全国"]
      
      business_rules:
        - rule: "has_permission(user, region)"
          message: "用户没有该区域的访问权限"
    
    # 资源配额
    quota:
      base:
        max_execution_time: 30
        max_token_usage: 5000
      adjustments:
        - parameter: "region"
          condition: "region == '全国'"
          multiplier: 3.0
```

---

## 📚 相关文档

- [Intent Package Specification](./INTENT_PACKAGE_SPEC.md) - 意图包完整规范
- [Development Guide](./INTENT_PACKAGE_DEVELOPMENT_GUIDE.md) - 开发者指南
- [Architecture Blueprint](./ARCHITECTURE.md) - 架构蓝图

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-27  
**维护者**: IntentOS Team
