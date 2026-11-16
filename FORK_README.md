# Dune Weaver: adman234 fork

A maintained fork of [tuanchris/dune-weaver](https://github.com/tuanchris/dune-weaver)
(upstream has been quiet since July 2026). Everything below installs and
updates from **https://github.com/adman234/dune-weaver**.

Run every command over SSH on the Pi, **as your normal user (e.g. `pi`)**,
not as root. The scripts use `sudo` themselves when they need it.

---

## New Pi: install

Start from **Raspberry Pi OS 64-bit** with SSH enabled. Then paste:

```bash
curl -fsSL https://raw.githubusercontent.com/adman234/dune-weaver/main/scripts/fork-install.sh | bash
```

It installs git, clones the fork to `~/dune-weaver`, and runs `setup-pi.sh`.
That sets up the Python env, nginx, the service, WiFi hotspot and the `dw`
command. Answer its UART question (**yes** only if the controller is wired to
the GPIO pins, not USB) and let it reboot. Then open `http://<pi-ip>/`.

Options:

```bash
curl -fsSL https://raw.githubusercontent.com/adman234/dune-weaver/main/scripts/fork-install.sh | bash -s -- --no-hotspot
```

```bash
curl -fsSL https://raw.githubusercontent.com/adman234/dune-weaver/main/scripts/fork-install.sh | DW_BRANCH=feature/led-random-effect-options bash
```

## Existing Pi: back up, switch to the fork, update

This works on a stock upstream install, on one running a fork branch (like the
LED random-effect branch), and as the routine update for fork installs:

```bash
curl -fsSL https://raw.githubusercontent.com/adman234/dune-weaver/main/scripts/fork-update.sh | bash
```

What it does:

1. Fixes file ownership (updates started from the web UI leave root-owned files).
2. **Backs up** to `~/dw-backups/<date-time>/`:
   - settings, state, playlists;
   - uploaded patterns, custom logo, touch-app settings;
   - any hand edits you made to the code (saved as a patch);
   - the systemd and nginx configs;
   - a `RESTORE.txt` with exact undo commands.
3. Points `origin` at the fork and fetches all branches.
4. Stays on your current branch if the fork has it, otherwise uses `main`.
5. Runs `dw update`, which reinstalls Python packages, redeploys nginx/systemd and restarts the service.

Variations:

| Want to… | Run |
|---|---|
| Only make a backup | `curl -fsSL …/fork-update.sh \| DW_BACKUP_ONLY=1 bash` |
| Force a branch | `curl -fsSL …/fork-update.sh \| DW_BRANCH=main bash` |
| Install isn't in `~/dune-weaver` | `curl -fsSL …/fork-update.sh \| DW_DIR=/opt/dune-weaver bash` |

Once you're on the fork, a plain `dw update` also works. `fork-update.sh`
is just the safer version because it takes a backup first.

---

## Everyday commands

| Command | Does |
|---|---|
| `dw status` | service status |
| `dw logs` | follow the log (Ctrl+C to exit) |
| `dw restart` | restart the app |
| `dw update` | pull latest from your branch and redeploy |
| `dw checkout <branch>` | switch to another branch of the fork (backs up local edits first) |
| `dw wifi` | WiFi / hotspot status and tools |
| `dw touch install` | install the touch-screen app |

---

## Restoring a backup

Each backup folder has a `RESTORE.txt` with commands filled in for that
install. The short version:

```bash
dw stop
```

```bash
tar -xzf ~/dw-backups/<date-time>/user-data.tar.gz -C ~/dune-weaver && dw start
```

To go back to exactly the old code, follow the "roll back" section of
`RESTORE.txt`. It records the old remote and commit.

---

## Edge cases and fixes

**Forgot the security-mode password.**
Changing security settings now needs the current password. To reset it:
```bash
dw stop
```
```bash
cd ~/dune-weaver && sudo python3 -c "import json;p='settings.json';s=json.load(open(p));s['security_mode']='off';s['security_password_hash']='';json.dump(s,open(p,'w'),indent=2)" && dw start
```

**Browser or app on another network gets CORS errors.**
The API only accepts browser requests from LAN addresses (`192.168.*`, `10.*`,
`*.local`, and so on). To allow something else, such as a reverse-proxy domain,
add an override to the service and restart:
```bash
sudo systemctl edit dune-weaver
```
In the editor, add `[Service]` and
`Environment=DW_CORS_ORIGIN_REGEX=^https?://(dune\.example\.com|192\.168\.\d+\.\d+)(:\d+)?$`,
then run `dw restart`.

**Settings or playlists are missing.**
The fork writes its JSON files atomically. If an old corrupt file is found, it is
kept as `*.corrupt-<time>` next to the original. Restore from the newest
`~/dw-backups/*` folder (see above).

**`fatal: detected dubious ownership in repository`.**
```bash
git config --global --add safe.directory ~/dune-weaver
```

**Service won't start after an update.**
Read `dw logs`. Usually a Python package changed, so reinstall the requirements:
```bash
cd ~/dune-weaver && .venv/bin/pip install -r requirements.txt && dw restart
```
If that doesn't fix it, roll back using the newest backup's `RESTORE.txt`.

**UI looks unchanged after an update that changed the frontend.**
The Pi serves the prebuilt bundle in `static/dist`. Hard-refresh the browser
(Ctrl+Shift+R). On a phone, clear the site data because of the service worker.
If it's still old, the commit didn't include a rebuilt `static/dist`.

**Table won't connect to the controller.**
USB: check `ls /dev/ttyUSB* /dev/ttyACM*` and that the cable carries data, not
just power. GPIO/UART: the installer's UART answer must have been **yes**, and
the Pi needs a reboot afterwards. Then pick the port in Settings → Connection.

**Pi isn't on the network after a WiFi change.**
When no known network is in range, the autohotspot starts. Join the
**"Dune Weaver"** WiFi from a phone, open `http://10.42.0.1/`, and set the new
network there.

**`dw: Dune Weaver not found`.**
`dw` looks in `~/dune-weaver` (also the sudo user's home), `/home/pi/dune-weaver`
and the current folder. For an install anywhere else, `cd` into it first.

**Install was copied or unzipped rather than cloned (no `.git`).**
`fork-update.sh` backs it up and stops, then prints the three commands to move
it aside, fresh-install, and restore your data.

**Hand-edited code on the Pi.**
Updates overwrite tracked files. `fork-update.sh` saves your edits as
`local-changes.patch` in the backup. Re-apply with `git apply <patch>`, or
better, commit the change to the fork.

---

## Developing the fork

```bash
git clone https://github.com/adman234/dune-weaver.git && cd dune-weaver
```

- Backend tests: `pip install -r requirements-nonrpi.txt pyyaml pytest pytest-asyncio httpx`, then `python -m pytest tests/unit -q`. On Windows, `pip uninstall mock-serial` first.
- Frontend changes: `cd frontend && npm ci && npm run build`, and **commit `static/dist`**. The Pi doesn't build it.
- Releases: put `X.Y.Z` (numbers only, higher than 4.1.4) in `VERSION`, commit, `git tag vX.Y.Z`, push with `--tags`, then create a GitHub release.

Known bugs and the improvement list are in [FORK_TODO.md](FORK_TODO.md).
