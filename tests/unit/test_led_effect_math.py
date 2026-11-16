"""Regression tests for the WLED-port effect math (modules/led/dw_leds)."""

import pytest

from modules.led.dw_leds.effects import basic_effects
from modules.led.dw_leds.segment import Segment
from modules.led.dw_leds.utils.colors import sin8


def test_sin8_is_one_full_sine_period():
    # The old version mirrored the rising half, so it never went below 128
    # and every wave-based effect only used the top half of its blend range.
    assert sin8(0) == 128
    assert sin8(64) == 255
    assert sin8(128) == 128
    assert sin8(192) < 5
    assert min(sin8(x) for x in range(256)) < 5
    assert sin8(256 + 64) == sin8(64)


class _FakePixels:
    def __init__(self, n):
        self.buf = [(0, 0, 0)] * n

    def __setitem__(self, i, v):
        self.buf[i] = v

    def __getitem__(self, i):
        return self.buf[i]

    def __len__(self):
        return len(self.buf)


def _make_segment(n):
    return Segment(_FakePixels(n), 0, n)


@pytest.mark.parametrize("n", [75, 132])
def test_palette_flow_maps_ring_onto_palette_once(monkeypatch, n):
    # Palette Flow computes a 0-255 palette position itself; it must not be
    # rescaled as an LED index (that wrapped the palette ~3x with a hard seam).
    seen = []
    seg = _make_segment(n)
    seg.speed = 0
    seg.intensity = 255
    monkeypatch.setattr(seg, "now", lambda: 0)

    def record(index, use_index=True, brightness=255):
        seen.append(index if not use_index else index * 255 // (n - 1))
        return 0

    monkeypatch.setattr(seg, "color_from_palette", record)
    basic_effects.mode_palette_flow(seg)
    assert len(seen) == n
    assert seen == sorted(seen)
    assert seen[-1] <= 255


def test_color_wipe_soft_edge_wraps_like_wled(monkeypatch):
    # WLED keeps rem as uint16; without the wrap the soft edge was always 255.
    seg = _make_segment(100)
    seg.speed = 128
    seg.intensity = 255
    cycle = 750 + (255 - seg.speed) * 150
    now = cycle // 7  # forward pass, (prog * len * 2) overflows 16 bits here
    monkeypatch.setattr(seg, "now", lambda: now)
    prog = (now * 65535) // cycle
    expected = (((prog * seg.length) * 2) & 0xFFFF) // (seg.intensity + 1)
    assert expected < 255
    blends = []
    real_blend = basic_effects.color_blend

    def spy(a, b, amt, *args, **kwargs):
        blends.append(amt)
        return real_blend(a, b, amt, *args, **kwargs)

    monkeypatch.setattr(basic_effects, "color_blend", spy)
    basic_effects.mode_color_wipe(seg)
    assert blends == [expected]
