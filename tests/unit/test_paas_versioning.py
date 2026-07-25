"""
测试 intentos.paas.versioning - App 版本管理

覆盖:
- VersionStatus / ReleaseChannel 枚举
- VersionInfo (创建, to_dict)
"""

import pytest


class TestVersionStatus:
    def test_all_statuses(self):
        from intentos.paas.versioning import VersionStatus
        assert VersionStatus.DRAFT.value == "draft"
        assert VersionStatus.BETA.value == "beta"
        assert VersionStatus.STABLE.value == "stable"


class TestReleaseChannel:
    def test_all_channels(self):
        from intentos.paas.versioning import ReleaseChannel
        channels = [c.value for c in ReleaseChannel]
        assert "nightly" in channels
        assert "lts" in channels


class TestVersionInfo:
    def test_create_version_info(self):
        from intentos.paas.versioning import VersionInfo, VersionStatus, ReleaseChannel
        vi = VersionInfo(
            app_id="app_1",
            version="1.0.0",
            status=VersionStatus.STABLE,
            channel=ReleaseChannel.STABLE,
            manifest_hash="abc123",
           )
        assert vi.version == "1.0.0"

    def test_to_dict(self):
        from intentos.paas.versioning import VersionInfo, VersionStatus, ReleaseChannel
        vi = VersionInfo(
            app_id="app_2",
            version="2.0.0",
            status=VersionStatus.BETA,
            channel=ReleaseChannel.BETA,
            manifest_hash="def456",
           )
        d = vi.to_dict()
        assert d["version"] == "2.0.0"
        assert d["status"] == "beta"
