#!/bin/bash
# Unix I/O 使用示例
# 展示 IntentOS 如何像 Unix 工具一样使用

set -e  # 遇到错误退出

echo "╔==========================================================╗"
echo "║           IntentOS Unix I/O 使用示例                  ║"
echo "╚==========================================================╝"
echo ""

# 检查内核是否运行
echo "ℹ️  检查内核状态..."
if ! python -m intentos cli status 2>/dev/null; then
    echo "⚠️  内核未运行，正在启动..."
    python -m intentos daemon &
    sleep 3
    echo "✅ 内核已启动"
fi

echo ""
echo "============================================================"
echo "示例 1: 基本用法"
echo "============================================================"

# 注意：这些示例需要实际运行内核，这里仅展示语法
echo "# 执行意图"
echo 'intentos "分析销售数据"'
echo ""
echo "# 从 stdin 读取"
echo 'echo "分析销售数据" | intentos'
echo ""
echo "# 从文件执行"
echo 'intentos --file examples/sales_analysis.pef.yaml'

echo ""
echo "============================================================"
echo "示例 2: 输出格式"
echo "============================================================"

echo "# JSON 输出"
echo 'intentos --json "分析销售数据"'
echo ""
echo "# YAML 输出"
echo 'intentos --yaml "分析销售数据"'
echo ""
echo "# Plain 输出"
echo 'intentos --plain "分析销售数据"'

echo ""
echo "============================================================"
echo "示例 3: 管道操作"
echo "============================================================"

echo "# 简单管道"
echo 'intentos "查询销售数据" | intentos "分析趋势"'
echo ""
echo "# 多段管道"
echo 'intentos "查询数据" | intentos "分析趋势" | intentos "生成报告"'
echo ""
echo "# 与 jq 组合"
echo 'intentos --json "查询数据" | jq \'.data.sales\' | intentos "分析"'

echo ""
echo "============================================================"
echo "示例 4: 错误处理"
echo "============================================================"

echo "# 检查退出码"
cat << 'EOF'
intentos --json "分析销售数据" > result.json 2>error.log
exit_code=$?

case $exit_code in
    0) echo "成功" ;;
    2) echo "权限拒绝" ;;
    6) echo "连接失败" ;;
    *) echo "其他错误" ;;
esac
EOF

echo ""
echo "============================================================"
echo "示例 5: 验证 PEF"
echo "============================================================"

echo "# 验证 PEF 文件"
echo 'intentos --validate examples/sales_analysis.pef.yaml'
echo ""
echo "# 验证并查看 JSON 结果"
echo 'intentos --json --validate examples/sales_analysis.pef.yaml'

echo ""
echo "============================================================"
echo "示例 6: Makefile 集成"
echo "============================================================"

cat << 'EOF'
# Makefile 示例
analyze-report:
	intentos "查询销售数据" > sales.json
	intentos --file sales.json > analysis.json
	intentos "生成报告" < analysis.json > report.md
EOF

echo ""
echo "============================================================"
echo "示例 7: 环境变量"
echo "============================================================"

echo "# 设置默认输出模式"
echo 'export INTENTOS_OUTPUT_MODE=json'
echo 'intentos "分析销售数据"  # 自动输出 JSON'
echo ""
echo 'export INTENTOS_OUTPUT_MODE=yaml'
echo 'intentos "分析销售数据"  # 自动输出 YAML'

echo ""
echo "============================================================"
echo "所有示例展示完成！"
echo "============================================================"
echo ""
echo "更多信息请参考: docs/UNIX_IO_GUIDE.md"
