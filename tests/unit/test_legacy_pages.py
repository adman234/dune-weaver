"""Legacy page URLs (/, /led, /settings, ...) render the redirect page.

Starlette 1.x only accepts TemplateResponse(request, name, context); the old
(name, {"request": ...}) form raised "unhashable type: 'dict'" (HTTP 500).
"""

import pytest


@pytest.mark.parametrize("path", ["/", "/settings", "/playlists", "/image2sand", "/led", "/table_control"])
async def test_legacy_page_renders_redirect(async_client, path):
    response = await async_client.get(path, headers={"host": "weaver.local:8080"})
    assert response.status_code == 200
    assert "weaver.local" in response.text
