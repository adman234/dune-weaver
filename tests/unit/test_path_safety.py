"""Pattern endpoints must not read, write or delete files outside the patterns dir."""
import pytest

import main


@pytest.mark.parametrize("path", [
    "circle.thr", "custom_patterns/a.thr", "patterns/x/y.thr", "./patterns/z.thr",
])
def test_safe_paths_accepted(path):
    assert main.is_safe_relpath(main.normalize_file_path(path))


@pytest.mark.parametrize("path", [
    "", "../settings.json", "custom_patterns/../../main.py", "/etc/passwd",
    "C:/Windows/win.ini", "..\\state.json", "a\x00.thr",
])
def test_unsafe_paths_rejected(path):
    assert not main.is_safe_relpath(main.normalize_file_path(path))


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", [
    "/delete_theta_rho_file", "/get_theta_rho_coordinates", "/preview_thr",
])
async def test_endpoints_reject_traversal(async_client, endpoint, tmp_path, monkeypatch):
    victim = tmp_path / "settings.json"
    victim.write_text("{}")
    patterns = tmp_path / "patterns"
    patterns.mkdir()
    monkeypatch.setattr(main.pattern_manager, "THETA_RHO_DIR", str(patterns))

    response = await async_client.post(endpoint, json={"file_name": "../settings.json"})

    assert response.status_code == 400
    assert victim.exists()


@pytest.mark.asyncio
async def test_upload_strips_directories(async_client, tmp_path, monkeypatch):
    patterns = tmp_path / "patterns"
    (patterns / "custom_patterns").mkdir(parents=True)
    monkeypatch.setattr(main.pattern_manager, "THETA_RHO_DIR", str(patterns))

    async def no_preview(_):
        return True
    monkeypatch.setattr(main, "generate_image_preview", no_preview)

    files = {"file": ("../../evil.thr", b"0 0\n1 1\n", "text/plain")}
    response = await async_client.post("/upload_theta_rho", files=files)

    assert response.status_code == 200
    assert (patterns / "custom_patterns" / "evil.thr").exists()
    assert not (tmp_path / "evil.thr").exists()
