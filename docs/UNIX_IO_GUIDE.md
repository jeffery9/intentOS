# Unix I/O 和 CLI 使用指南

> **任务 #2 完成**: 标准 Unix I/O 支持

## 概述

IntentOS 现在提供完整的标准 Unix I/O 支持，可以像传统 Unix 工具一样使用：

- ✅ 标准 stdin/stdout/stderr
- ✅ 标准 exit codes（0=成功，1=错误，2=权限拒绝等）
- ✅ 管道操作支持
- ✅ 结构化输出（JSON/YAML/Plain）
- ✅ 与 Rich TUI 共存

## 快速开始

### 1. 基本用法

```bash
# 启动内核（必须先执行）
intentos daemon

# 执行意图
intentos "分析销售数据"

# 从 stdin 读取
echo "分析销售数据" | intentos

# 从文件执行
intentos --file analysis.pef.yaml
```

### 2. 指定输出格式

```bash
# JSON 输出（程序友好）
intentos --json "分析销售数据"

# YAML 输出（人类可读）
intentos --yaml "分析销售数据"

# Plain 输出（纯文本）
intentos --plain "分析销售数据"
```

### 3. 管道操作

```bash
# 简单管道
intentos "查询销售数据" | intentos "分析趋势"

# 多段管道
intentos "查询数据" | intentos "分析趋势" | intentos "生成报告"

# 与 Unix 工具组合
intentos --json "查询数据" | jq '.data.sales' | intentos "分析这个数字"
```

### 4. 验证 PEF

```bash
# 验证 PEF 文件
intentos --validate analysis.pef.yaml

# 查看验证结果（JSON）
intentos --json --validate analysis.pef.yaml
```

## 标准 Exit Codes

IntentOS 遵循 Unix 惯例的标准退出码：

| Exit Code | 含义 | 说明 |
|-----------|------|------|
| **0** | SUCCESS | 成功 |
| **1** | GENERAL_ERROR | 一般错误 |
| **2** | PERMISSION_DENIED | 权限拒绝 |
| **3** | USAGE_ERROR | 使用错误（无效输入） |
| **4** | RESOURCE_UNAVAILABLE | 资源不可用 |
| **5** | TIMEOUT | 超时 |
| **6** | CONNECTION_FAILED | 连接失败 |
| **7** | COMPILE_ERROR | 编译错误 |
| **8** | EXECUTION_ERROR | 执行错误 |
| **9** | VALIDATION_ERROR | 验证错误 |
| **10** | FILE_NOT_FOUND | 文件未找到 |

### 使用示例

```bash
# 检查执行结果
intentos "分析销售数据"
if [ $? -eq 0 ]; then
    echo "执行成功"
else
    echo "执行失败"
fi

# 权限检查
intentos "删除生产数据"
if [ $? -eq 2 ]; then
    echo "权限不足，需要审批"
fi
```

## 输出格式详解

### Plain 模式（默认，非 TTY 自动切换）

```bash
# 纯文本输出
intentos --plain "分析销售数据"

# 输出示例
执行成功：华东区 Q3 销售额为 500 万，同比增长 15%
```

**特点**：
- 人类可读
- 适合终端显示
- 错误输出到 stderr
- 正常输出到 stdout

### JSON 模式

```bash
# JSON 输出
intentos --json "分析销售数据"

# 输出示例
{
  "status": "success",
  "message": "执行成功：华东区 Q3 销售额为 500 万",
  "command": "分析销售数据",
  "data": {
    "region": "华东",
    "sales": 5000000,
    "growth": 0.15
  },
  "exit_code": 0,
  "timestamp": "2026-04-05T14:30:25+08:00"
}
```

**特点**：
- 程序友好
- 结构化数据
- 易于解析
- 适合管道操作

### YAML 模式

```bash
# YAML 输出
intentos --yaml "分析销售数据"

# 输出示例
status: success
message: '执行成功：华东区 Q3 销售额为 500 万'
command: 分析销售数据
data:
  region: 华东
  sales: 5000000
  growth: 0.15
exit_code: 0
timestamp: '2026-04-05T14:30:25+08:00'
```

**特点**：
- 人类可读
- 程序可解析
- 适合版本控制
- 适合配置文件

## 环境变量

```bash
# 设置默认输出模式
export INTENTOS_OUTPUT_MODE=json
intentos "分析销售数据"  # 自动输出 JSON

export INTENTOS_OUTPUT_MODE=yaml
intentos "分析销售数据"  # 自动输出 YAML

export INTENTOS_OUTPUT_MODE=plain
intentos "分析销售数据"  # 纯文本输出
```

## 管道操作详解

### 示例 1: 查询 → 分析

```bash
# 第一步：查询数据（输出 JSON）
intentos --json "查询华东区 Q3 销售数据" > sales_data.json

# 第二步：分析数据（从 JSON 读取）
cat sales_data.json | intentos "分析这个销售数据"
```

### 示例 2: 多段管道

```bash
# 管道链
intentos "查询销售数据" \
  | intentos "分析趋势" \
  | intentos "生成报告" \
  > final_report.md
```

### 示例 3: 与 Unix 工具组合

```bash
# 使用 jq 处理 JSON 输出
intentos --json "查询销售数据" \
  | jq '.data.sales' \
  | intentos "分析这个数字"

# 使用 grep 过滤
intentos "查询日志" | grep "ERROR" | intentos "分析这些错误"

# 使用 awk 提取
intentos --json "查询数据" | awk -F: '/sales/{print $2}' | intentos "分析"
```

### 示例 4: Makefile 集成

```makefile
# Makefile
analyze-report:
	intentos "查询销售数据" > sales.json
	intentos --file sales.json > analysis.json
	intentos "从分析结果生成报告" < analysis.json > report.md

clean:
	rm -f *.json *.md
```

## 错误处理

### 标准错误输出

```bash
# 成功情况
intentos "分析销售数据" > result.json 2>error.log
echo $?  # 0

# 错误情况
intentos "删除生产数据" > result.json 2>error.log
echo $?  # 2 (权限拒绝)

# 查看错误
cat error.log
# {"status": "error", "error": "权限拒绝", "exit_code": 2, ...}
```

### Shell 脚本示例

```bash
#!/bin/bash

# 执行意图
intentos --json "分析销售数据" > result.json 2>error.log
exit_code=$?

# 检查退出码
case $exit_code in
    0)
        echo "执行成功"
        jq '.data' result.json
        ;;
    2)
        echo "权限拒绝，需要审批"
        jq '.error' error.log
        ;;
    6)
        echo "连接失败，检查内核是否运行"
        ;;
    *)
        echo "其他错误: $(cat error.log)"
        ;;
esac

exit $exit_code
```

## 高级用法

### 从 PEF 文件执行

```bash
# 执行 PEF 文件
intentos --file analysis.pef.yaml

# 指定输出格式
intentos --json --file analysis.pef.yaml

# 验证后执行
intentos --validate analysis.pef.yaml && intentos --file analysis.pef.yaml
```

### 批量处理

```bash
# 批量执行多个意图
for intent in "查询数据" "分析趋势" "生成报告"; do
    intentos --json "$intent" > "${intent}.json"
done

# 并行执行（使用 &）
intentos "查询华东数据" &
intentos "查询华南数据" &
wait
```

### 与 Git 集成

```bash
# 将 PEF 文件纳入版本控制
git add analysis.pef.yaml
git commit -m "添加销售分析 PEF"

# 查看 PEF 变更
git diff analysis.pef.yaml
```

## 编程接口

### Python API

```python
from intentos.interface.unix_io import (
    ExecutionResult,
    OutputMode,
    write_output,
    write_error,
)
from intentos.interface.exit_codes import ExitCode

# 创建结果
result = ExecutionResult(
    success=True,
    message="执行成功",
    command="分析销售数据",
    data={"sales": 5000000},
    exit_code=ExitCode.SUCCESS,
)

# 输出
write_output(result, OutputMode.JSON)
write_output(result, OutputMode.YAML)

# 错误处理
write_error("权限拒绝", OutputMode.JSON, ExitCode.PERMISSION_DENIED)
```

### 检测输出模式

```python
from intentos.interface.unix_io import detect_output_mode, OutputMode

# 自动检测（TTY -> Rich, 管道 -> Plain）
mode = detect_output_mode()

if mode == OutputMode.JSON:
    # 输出 JSON
    pass
elif mode == OutputMode.PLAIN:
    # 输出纯文本
    pass
```

## 与 Rich TUI 共存

IntentOS 智能检测运行环境：

- **交互式终端**：默认 Rich TUI 模式（美观的格式）
- **管道/重定向**：自动切换到 Plain 模式（Unix 友好）
- **显式参数**：`--json`/`--yaml`/`--plain` 强制指定模式

```bash
# 交互式（Rich TUI）
intentos cli

# 非交互式（自动 Plain）
intentos "分析数据" > output.txt

# 强制 JSON（即使 TTY）
intentos --json "分析数据"
```

## 最佳实践

### 1. 脚本中使用 JSON 输出

```bash
#!/bin/bash
# 推荐：使用 JSON 输出，易于解析
result=$(intentos --json "查询销售数据")
sales=$(echo "$result" | jq -r '.data.sales')
echo "销售额: $sales"
```

### 2. 错误处理

```bash
# 始终检查退出码和 stderr
intentos --json "执行操作" > result.json 2>error.log
if [ $? -ne 0 ]; then
    echo "执行失败: $(cat error.log)"
    exit 1
fi
```

### 3. 管道优化

```bash
# 使用 JSON 输出进行管道
intentos --json "查询数据" | intentos "分析"
# 而不是
intentos "查询数据" | intentos "分析"  # 可能格式不匹配
```

### 4. 日志记录

```bash
# 分离 stdout 和 stderr
intentos --json "执行任务" > result.json 2>task.log

# 或者合并
intentos --json "执行任务" > output.log 2>&1
```

## 故障排查

### 问题 1: 连接失败

```bash
# 检查内核是否运行
intentos cli status

# 启动内核
intentos daemon
```

### 问题 2: 输出格式不正确

```bash
# 显式指定格式
intentos --json "命令"

# 检查环境变量
echo $INTENTOS_OUTPUT_MODE
unset INTENTOS_OUTPUT_MODE  # 清除
```

### 问题 3: 管道不工作

```bash
# 确保上游命令输出正确格式
intentos --json "查询" | intentos "分析"

# 调试：查看中间结果
intentos --json "查询" | tee debug.json | intentos "分析"
```

## 参考文档

- [Exit Codes 定义](./intentos/interface/exit_codes.py)
- [Unix I/O 实现](./intentos/interface/unix_io.py)
- [Unix CLI 入口](./intentos/interface/unix_cli.py)
- [PEF v2.0 格式](./docs/PEF_FORMAT_SPEC.md)
- [改进提案](./docs/IMPROVEMENT_PROPOSAL.md)

## 总结

IntentOS 的 Unix I/O 支持使其能够：

✅ **像 Unix 工具一样使用** - stdin/stdout/stderr  
✅ **标准退出码** - 遵循 Unix 惯例  
✅ **管道操作** - 与其他 Unix 工具组合  
✅ **结构化输出** - JSON/YAML/Plain 多格式  
✅ **与 TUI 共存** - 智能检测运行环境  

正如改进提案所言：**"简单就是可靠"**，Unix I/O 支持让 IntentOS 获得了 Unix 的可靠性和组合性。
