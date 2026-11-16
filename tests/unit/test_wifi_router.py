"""WiFi endpoints shell out to nmcli (up to ~65 s); they must not block the event loop."""
import asyncio
import threading
import time

import pytest

from modules.wifi import manager


@pytest.mark.asyncio
async def test_slow_scan_does_not_block_event_loop(async_client, monkeypatch):
    loop_thread = threading.get_ident()
    seen = {}

    def slow_scan():
        seen["thread"] = threading.get_ident()
        time.sleep(0.5)
        return [{"ssid": "home"}]

    monkeypatch.setattr(manager, "scan_networks", slow_scan)

    ticks = 0

    async def ticker():
        nonlocal ticks
        while True:
            await asyncio.sleep(0.05)
            ticks += 1

    t = asyncio.create_task(ticker())
    try:
        response = await async_client.get("/api/wifi/networks")
    finally:
        t.cancel()

    assert response.status_code == 200
    assert response.json() == [{"ssid": "home"}]
    assert seen["thread"] != loop_thread
    assert ticks >= 5  # loop kept running during the 0.5 s scan


@pytest.mark.asyncio
async def test_connect_runs_in_thread(async_client, monkeypatch):
    loop_thread = threading.get_ident()
    seen = {}

    def fake_connect(ssid, password):
        seen["thread"] = threading.get_ident()
        return {"success": True, "message": f"Connected to '{ssid}'."}

    monkeypatch.setattr(manager, "connect_to_network", fake_connect)

    response = await async_client.post("/api/wifi/connect", json={"ssid": "home", "password": "pw123456"})

    assert response.status_code == 200
    assert seen["thread"] != loop_thread
