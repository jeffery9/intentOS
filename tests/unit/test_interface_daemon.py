"""
测试 intentos.interface.daemon - 守护进程
"""

import pytest


class TestGetSocketPath:
    """Socket 路径测试"""

    def test_socket_path_default(self):
        from intentos.interface.daemon import get_socket_path
        path = get_socket_path()
        assert path == "/tmp/intentos.sock"


class TestIntentOSDaemon:
    """守护进程测试"""

    def test_create_daemon(self):
        from intentos.interface.daemon import IntentOSDaemon
        daemon = IntentOSDaemon()
        assert daemon.enable_api is False
        assert daemon.api_host == "localhost"
        assert daemon.api_port == 8080

    def test_daemon_with_api(self):
        from intentos.interface.daemon import IntentOSDaemon
        daemon = IntentOSDaemon(enable_api=True)
        assert daemon.enable_api is True

    def test_daemon_custom_config(self):
        from intentos.interface.daemon import IntentOSDaemon
        daemon = IntentOSDaemon(enable_api=True, api_host="0.0.0.0", api_port=9090)
        assert daemon.api_host == "0.0.0.0"
        assert daemon.api_port == 9090
