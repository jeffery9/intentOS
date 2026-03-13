# IntentOS Examples

示例代码需要安装 intentos 包才能运行：

```bash
pip install -e .
```

## 示例列表

### 语义 VM 演示

```bash
python examples/demo_semantic_vm.py
```

演示语义 VM 的核心功能：
- 基础语义程序
- 循环程序 (图灵完备)
- 自修改程序 (Self-Bootstrap)

### 分布式语义 VM 演示

```bash
python examples/demo_distributed_semantic_vm.py
```

演示分布式语义 VM：
- 集群搭建
- 分布式程序执行
- 自我复制
- 自动扩缩容

### 完整 Self-Bootstrap 演示

```bash
python examples/demo_complete_bootstrap.py
```

演示完整的 Self-Bootstrap 流程：
- Level 1: 修改解析/执行规则
- Level 2: 扩展指令集/修改策略
- Level 3: 自我复制/自动扩缩容

## 测试

```bash
# 运行所有测试
python -m pytest examples/test_*.py -v

# 运行特定测试
python -m pytest examples/test_semantic_vm.py -v
```
