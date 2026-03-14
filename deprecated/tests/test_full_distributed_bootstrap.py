import asyncio

from intentos.bootstrap import (
    create_bootstrap_executor,
)
from intentos.distributed import (
    DistributedOpcode,
    create_distributed_vm,
)
from intentos.semantic_vm import (
    create_instruction,
)


# Mock LLM Executor
class MockLLMExecutor:
    async def execute(self, messages: list[dict]) -> any:
        content = messages[-1]["content"]

        # Simple rule-based response for testing
        if "PARSE_PROMPT" in content:
            return type('obj', (object,), {'content': '{"operation": "modify_config", "parameters": {"key": "PARSE_PROMPT", "value": "new_parsed_prompt"}, "success": true}'})

        return type('obj', (object,), {'content': '{"operation": "mock", "success": true}'})

async def test_full_implementation():
    print("=" * 80)
    print("IntentOS - Distributed & Self-Bootstrap Complete Implementation Test")
    print("=" * 80)

    llm_executor = MockLLMExecutor()

    # 1. Initialize local VM (Port 8000)
    vm1 = create_distributed_vm(llm_executor)

    # 2. Test Distributed Memory (Hash Ring)
    print("\n[1] Testing Distributed Memory (Hash Ring)...")
    vm1.memory.add_node(type('obj', (object,), {'node_id': 'node2', 'host': 'localhost', 'port': 8001, 'status': 'active', 'load': 0.0}))

    store = "VARIABLE"
    key = "distributed_key"

    # This should hash to one of the nodes
    node = vm1.memory._get_node_for_key(f"{store}:{key}")
    print(f"  Key '{key}' mapped to node: {node.node_id if node else 'None'}")

    # 3. Test Distributed Processor (Opcodes)
    print("\n[2] Testing Distributed Opcodes (REPLICATE)...")
    await vm1.local_vm.memory.set("VARIABLE", "test_var", "test_value")

    instr = create_instruction(
        DistributedOpcode.REPLICATE,
        target="VARIABLE",
        target_name="test_var",
        node="node2"
    )

    result = await vm1.local_vm.processor.execute(instr, vm1.local_vm.memory)
    print(f"  REPLICATE result: {result}")

    # 4. Test Self-Bootstrap (Modification)
    print("\n[3] Testing Self-Bootstrap (Config Modification)...")
    bootstrap = create_bootstrap_executor(vm1)

    # Execute a bootstrap program
    record = await bootstrap.execute_bootstrap(
        action="modify_config",
        target="CONFIG.PARSE_PROMPT",
        new_value="new_parsed_prompt",
        context={"user": "admin"}
    )

    print(f"  Bootstrap Action: {record.action}")
    print(f"  Status: {record.status}")
    print(f"  New Value: {await vm1.local_vm.memory.get('CONFIG', 'PARSE_PROMPT')}")

    # 5. Test Dynamic Instruction Extension
    print("\n[4] Testing Dynamic Instruction Extension...")
    await bootstrap.execute_bootstrap(
        action="extend_instruction",
        target="INSTRUCTION_SET.SCAN",
        new_value="scan_logic",
        context={}
    )

    # Check if the handler was added
    has_handler = hasattr(vm1.local_vm.processor, "_handle_scan")
    print(f"  New handler _handle_scan added: {has_handler}")

    print("\n" + "=" * 80)
    print("Test Completed Successfully!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_full_implementation())
