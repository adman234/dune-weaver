# Dune Weaver

[![Patreon](https://img.shields.io/badge/Patreon-F96854?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/cw/DuneWeaver)

![Dune Weaver](./static/og-image.jpg)

**An open-source kinetic sand art table that creates mesmerizing patterns using a ball controlled by precision motors.**

## Features

- **Modern React UI** — A responsive, touch-friendly web interface that installs as a PWA on any device
- **Pattern Library** — Browse, upload, and manage hundreds of sand patterns with auto-generated previews
- **Live Preview** — Watch your pattern come to life in real time with progress tracking
- **Playlists** — Queue up multiple patterns with configurable pause times and automatic clearing between drawings
- **LED Integration** — Synchronized lighting via native DW LEDs or WLED, with separate idle, playing, and scheduled modes
- **Still Sands Scheduling** — Set quiet hours so the table pauses automatically on your schedule
- **Multi-Table Support** — Control several sand tables from a single interface
- **Home Assistant Integration** — Connect to Home Assistant or other home automation systems using MQTT
- **Auto-Updates** — One-click software updates right from the settings page
- **Add-Ons** — Optional [Desert Compass](https://duneweaver.com/docs) for auto-homing and [DW Touch](https://duneweaver.com/docs) for dedicated touchscreen control

## How It Works

The system is split across two devices connected via USB:

```
┌─────────────────┐         USB          ┌─────────────────┐
│  Raspberry Pi   │ ◄──────────────────► │  DLC32 / ESP32  │
│  (Dune Weaver   │                      │  (FluidNC)      │
│   Backend)      │                      │                 │
└─────────────────┘                      └─────────────────┘
        │                                        │
        │ Wi-Fi                                  │ Motor signals
        ▼                                        ▼
   Web Browser                            Stepper Motors
   (Control UI)                           (Theta & Rho)
```

The **Raspberry Pi** runs the web UI, manages pattern files and playlists, and converts patterns into G-code. The **DLC32/ESP32** running [FluidNC](https://github.com/bdring/FluidNC) firmware receives that G-code and drives the stepper motors in real time.

## Hardware

Dune Weaver comes in three premium models:

| | [DW Pro](https://duneweaver.com/products/dwp) | [DW Mini Pro](https://duneweaver.com/products/dwmp) | [DW Gold](https://duneweaver.com/products/dwg) |
|---|---|---|---|
| **Size** | 75 cm (29.5") | 25 cm (10") | 45 cm (17") |
| **Enclosure** | IKEA VITTSJÖ table | IKEA BLANDA bowl | IKEA TORSJÖ side table |
| **Motors** | 2 × NEMA 17 | 2 × NEMA 17 | 2 × NEMA 17 |
| **Controller** | DLC32 | DLC32 | DLC32 |
| **Best for** | Living rooms | Desktops | Side-table accent piece |

All models run the same software with [FluidNC](https://github.com/bdring/FluidNC) firmware — only the mechanical parts differ.

Free 3D-printable models on MakerWorld: [DW OG](https://makerworld.com/en/models/841332-dune-weaver-a-3d-printed-kinetic-sand-table#profileId-787553) · [DW Mini](https://makerworld.com/en/models/896314-mini-dune-weaver-not-your-typical-marble-run#profileId-854412)

> **Build guides, BOMs, and wiring diagrams** are in the [Dune Weaver Docs](https://duneweaver.com/docs).

## Quick Start

> This is **[adman234/dune-weaver](https://github.com/adman234/dune-weaver)**, a maintained fork of
> [tuanchris/dune-weaver](https://github.com/tuanchris/dune-weaver). Install, update, backup and
> troubleshooting steps for the fork are in **[FORK_README.md](FORK_README.md)**.

On a fresh Raspberry Pi OS (64-bit), over SSH as your normal user:

```bash
curl -fsSL https://raw.githubusercontent.com/adman234/dune-weaver/main/scripts/fork-install.sh | bash
```

To move an existing install (upstream or fork) onto this fork, with a backup first:

```bash
curl -fsSL https://raw.githubusercontent.com/adman234/dune-weaver/main/scripts/fork-update.sh | bash
```

Once it finishes, open **http://\<pi-ip\>/** in your browser. Afterwards, `dw update` pulls the latest
from your branch and `dw checkout <branch>` switches branches.

### Fork changes

**v4.2.1**

- Pressing stop no longer leaves a queued move (move to center/perimeter, send coordinate) hanging forever.
- WiFi scan/connect/save no longer freeze the app while `nmcli` runs.

**v4.2.0**


- Updates, the update badge and the version check all use this fork, not upstream.
- `dw checkout` works on any install. The web UI update runs outside the service, so it no longer kills itself mid-update.
- Settings, state and playlists are written atomically, so a power cut can't corrupt them.
- Pattern endpoints reject paths outside the patterns folder.
- Security mode: passwords are salted (PBKDF2), changing them needs the current password, and CORS is limited to LAN origins.
- Pausing during Still Sands works. Homing can no longer hang forever. Restarting the connection doesn't block the server.
- CI checks the Python constraints, runs shellcheck, and checks that `static/dist` matches the frontend source.

### Polar coordinates

The sand table uses **polar coordinates** instead of the typical X-Y grid:

- **Theta (θ)** — the angle in radians (2π = one full revolution)
- **Rho (ρ)** — the distance from the center (0.0 = center, 1.0 = edge)

Patterns are stored as `.thr` text files — one coordinate pair per line:

```
# A simple four-point star
0.000 0.5
1.571 0.7
3.142 0.5
4.712 0.7
```

The same pattern file works on any table size thanks to the normalized coordinate system. You can create patterns by hand, generate them with code, or browse the built-in library.

## Documentation

Full setup instructions, hardware assembly, firmware flashing, and advanced configuration:

**[Dune Weaver Docs](https://duneweaver.com/docs)**

## Contributing

We welcome contributions! See the [Contributing Guide](CONTRIBUTING.md) for how to get started.

## License

Dune Weaver is available under a **dual license**:

### Open Source License (GPL-3.0)

For open-source projects and personal use, Dune Weaver is licensed under the [GNU General Public License v3.0](LICENSE-GPL-3.0).

You are free to use, modify, and distribute this software under GPL-3.0 terms, provided that derivative works are also licensed under GPL-3.0 and source code is made available.

### Commercial License

For commercial use, proprietary applications, OEM/embedded deployments, or if you cannot comply with GPL-3.0 requirements, a commercial license is available.

Contact: hello@duneweaver.com

See the [LICENSE](LICENSE) file for full details.

---

**Happy sand drawing!**
