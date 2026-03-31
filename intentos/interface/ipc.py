"""
IntentOS IPC/RPC 通信层

提供进程间通信，支持 Shell、API 等客户端连接到运行中的 IntentOS 内核
"""

import asyncio
import json
import socket
import struct
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


# =============================================================================
# 协议定义
# =============================================================================


PROTOCOL_VERSION = 1
MAGIC_HEADER = b"INTENTOS"


@dataclass
class RPCRequest:
    """RPC 请求"""
    method: str
    params: dict = field(default_factory=dict)
    request_id: str = ""

    def to_bytes(self) -> bytes:
        """序列化为字节"""
        data = json.dumps({
            "version": PROTOCOL_VERSION,
            "id": self.request_id or datetime.now().isoformat(),
            "method": self.method,
            "params": self.params,
        }, ensure_ascii=False).encode("utf-8")
        # 头部：MAGIC(8) + 长度 (4) + 数据
        header = MAGIC_HEADER + struct.pack(">I", len(data))
        return header + data

    @classmethod
    def from_bytes(cls, data: bytes) -> "RPCRequest":
        """从字节反序列化"""
        obj = json.loads(data.decode("utf-8"))
        return cls(
            method=obj["method"],
            params=obj.get("params", {}),
            request_id=obj.get("id", ""),
        )


@dataclass
class RPCResponse:
    """RPC 响应"""
    request_id: str
    result: Any = None
    error: Optional[str] = None

    def to_bytes(self) -> bytes:
        """序列化为字节"""
        data = {
            "version": PROTOCOL_VERSION,
            "id": self.request_id,
        }
        if self.error:
            data["error"] = self.error
        else:
            data["result"] = self.result
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        header = MAGIC_HEADER + struct.pack(">I", len(payload))
        return header + payload

    @classmethod
    def from_bytes(cls, data: bytes) -> "RPCResponse":
        """从字节反序列化"""
        obj = json.loads(data.decode("utf-8"))
        return cls(
            request_id=obj["id"],
            result=obj.get("result"),
            error=obj.get("error"),
        )


# =============================================================================
# Socket 路径
# =============================================================================


def get_socket_path() -> str:
    """获取 Socket 文件路径"""
    # 使用固定的 /tmp 目录，方便客户端查找
    return "/tmp/intentos.sock"


# =============================================================================
# RPC 服务器
# =============================================================================


class RPCServer:
    """
    RPC 服务器

    监听 Unix Socket，处理客户端请求
    """

    def __init__(self, os_instance: Any, socket_path: Optional[str] = None):
        self.os = os_instance
        self.socket_path = socket_path or get_socket_path()
        self._server: Optional[asyncio.AbstractServer] = None
        self._running = False

    async def start(self) -> None:
        """启动服务器"""
        # 删除已存在的 socket 文件
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=self.socket_path
        )
        self._running = True
        print(f"✅ RPC Server listening on {self.socket_path}")

    async def stop(self) -> None:
        """停止服务器"""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        # 清理 socket 文件
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        print(f"✅ RPC Server stopped")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """处理客户端连接"""
        try:
            while self._running:
                # 读取头部
                header = await reader.readexactly(12)  # MAGIC(8) + 长度 (4)
                if len(header) < 12:
                    break

                # 验证魔术头
                if header[:8] != MAGIC_HEADER:
                    print("❌ Invalid magic header")
                    break

                # 读取数据长度
                data_len = struct.unpack(">I", header[8:])[0]

                # 读取数据
                data = await reader.readexactly(data_len)
                request = RPCRequest.from_bytes(data)

                # 处理方法
                result = await self._dispatch(request)

                # 发送响应
                response = RPCResponse(request_id=request.request_id, result=result)
                writer.write(response.to_bytes())
                await writer.drain()

        except asyncio.IncompleteReadError:
            pass  # 客户端断开
        except Exception as e:
            print(f"❌ Client error: {e}")
            # 发送错误响应
            try:
                response = RPCResponse(request_id=request.request_id if 'request' in locals() else "", error=str(e))
                writer.write(response.to_bytes())
                await writer.drain()
            except:
                pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def _dispatch(self, request: RPCRequest) -> Any:
        """分发请求到处理方法"""
        method_map = {
            "execute": self._handle_execute,
            "get_status": self._handle_get_status,
            "get_kernel_status": self._handle_get_kernel_status,
            "shutdown": self._handle_shutdown,
            "ping": self._handle_ping,
        }

        handler = method_map.get(request.method)
        if not handler:
            raise ValueError(f"Unknown method: {request.method}")

        return await handler(request.params)

    async def _handle_execute(self, params: dict) -> dict:
        """执行意图"""
        text = params.get("text", "")
        result = await self.os.execute(text)
        return {"result": result}

    async def _handle_get_status(self, params: dict) -> dict:
        """获取基本状态"""
        return {
            "running": self.os.is_running,
            "initialized": self.os._initialized,
        }

    async def _handle_get_kernel_status(self, params: dict) -> dict:
        """获取内核详细状态"""
        return await self.os.get_kernel_status()

    async def _handle_shutdown(self, params: dict) -> dict:
        """关闭系统"""
        self.os.shutdown()
        return {"status": "shutting_down"}

    async def _handle_ping(self, params: dict) -> dict:
        """心跳检测"""
        return {"pong": True, "timestamp": datetime.now().isoformat()}


# =============================================================================
# RPC 客户端
# =============================================================================


class RPCClient:
    """
    RPC 客户端

    连接到运行中的 IntentOS 内核
    """

    def __init__(self, socket_path: Optional[str] = None):
        self.socket_path = socket_path or get_socket_path()
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False

    async def connect(self) -> None:
        """连接到服务器"""
        try:
            self._reader, self._writer = await asyncio.open_unix_connection(self.socket_path)
            self._connected = True
        except FileNotFoundError:
            raise ConnectionError(
                f"无法连接到 IntentOS 内核。\n"
                f"Socket 文件不存在：{self.socket_path}\n"
                f"请先启动内核：python -m intentos daemon"
            )
        except Exception as e:
            raise ConnectionError(f"连接失败：{e}")

    async def disconnect(self) -> None:
        """断开连接"""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        self._connected = False

    async def _call(self, method: str, params: Optional[dict] = None) -> Any:
        """调用 RPC 方法"""
        if not self._connected:
            await self.connect()

        request = RPCRequest(method=method, params=params or {})
        self._writer.write(request.to_bytes())
        await self._writer.drain()

        # 读取响应
        header = await self._reader.readexactly(12)
        if header[:8] != MAGIC_HEADER:
            raise RuntimeError("Invalid response header")

        data_len = struct.unpack(">I", header[8:])[0]
        data = await self._reader.readexactly(data_len)
        response = RPCResponse.from_bytes(data)

        if response.error:
            raise RuntimeError(response.error)

        return response.result

    async def execute(self, text: str) -> str:
        """执行意图"""
        result = await self._call("execute", {"text": text})
        return result.get("result", "")

    async def get_status(self) -> dict:
        """获取状态"""
        return await self._call("get_status")

    async def get_kernel_status(self) -> dict:
        """获取内核详细状态"""
        return await self._call("get_kernel_status")

    async def ping(self) -> dict:
        """心跳检测"""
        return await self._call("ping")

    async def shutdown(self) -> None:
        """关闭内核"""
        await self._call("shutdown")


# =============================================================================
# 工具函数
# =============================================================================


def check_kernel_running() -> bool:
    """检查内核是否正在运行"""
    import os
    socket_path = get_socket_path()
    return os.path.exists(socket_path)


def wait_for_kernel(timeout: float = 10.0) -> bool:
    """等待内核启动"""
    import time
    start = time.time()
    while time.time() - start < timeout:
        if check_kernel_running():
            return True
        time.sleep(0.1)
    return False


# 延迟导入，避免循环引用
import os

# Any 类型提示需要
from typing import Any
