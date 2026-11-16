# Fork review: bugs, fixes and improvements

Review of `adman234/dune-weaver` on 16 Nov 2026. The fork's `main` is identical
to upstream `tuanchris/dune-weaver` (v4.1.4, last commit 19 Jul 2026). The
fork's only own work is `feature/led-random-effect-options` (2 commits, LED
random effect options), which is not merged into the fork's `main`.

Test status: `main` passes 109 unit tests; the feature branch passes 122.
`ruff check .` reports 786 findings, but CI ignores them (`continue-on-error: true`).

Install/update steps are in [FORK_README.md](FORK_README.md).

## Fix status (branch `fork-fixes`, v4.2.0)

**Fixed:** #1–#11, #13, #15–#17, #19, #20, plus the #18 lint/duplication cleanups.

**Not done / partial:**
- **#11:** passwords are now salted, changing security settings needs the
  current password, and CORS is limited to LAN origins. Security mode is still
  enforced in the UI only. A server-side session token on every write endpoint
  would break multi-table control, so it was left out.
- **#18:** splitting `main.py` into routers was not done.
- **#17:** the `custom_patterns` `.gitignore` item was a non-bug, so it was skipped.
- **#12** (run as non-root) and **#14** (motion stop drops futures) were not
  requested.
- **New:** `modules/wifi/manager.py` calls `subprocess.run` (10 s timeout)
  inside async functions, which can stall the event loop (ruff ASYNC221).

**Status key** (findings below): ✅ confirmed (reproduced or read directly in code) · ⚠️ likely (reasoned from code, not run on a Pi)

## Do these first

1. **#1–#3**: make the fork self-contained and ship the LED feature.
2. **#10, #11**: path traversal plus a wide-open API, on a service that runs as root.
3. **#4, #5, #9**: the update path and the data-loss risks you'll hit in normal use.

---

## 1. Making the fork independent

### #1 Point every upstream URL at the fork ✅
These still say `tuanchris/dune-weaver`:

| File | Line(s) | What |
|---|---|---|
| `setup-pi.sh` | 6, 9, 38 (`REPO_URL`), 55 | clone URL and help text |
| `dw` | 70, 86 | "please install" messages |
| `modules/core/version_manager.py` | 30 | `repo_owner` for the release check (see #2) |
| `frontend/src/pages/SettingsPage.tsx` | 2511 | release-notes link (rebuild `static/dist` afterwards) |
| `README.md` | 64 | install instructions |
| `CONTRIBUTING.md` | 18 | clone URL |

Better still, derive the URL once (e.g. `git -C "$INSTALL_DIR" remote get-url origin` in the
scripts) so a future fork or rename doesn't need edits.

### #2 Update check reads upstream's GitHub Releases ✅
`VersionManager` asks `api.github.com/repos/tuanchris/dune-weaver/releases/latest`.
Once the fork is ahead, the badge will never show an update. Upstream will only
show one if it ever releases again, and "Update" would then pull the **fork**,
not that release.
- Change `repo_owner` to `adman234`, or make it configurable (env var or setting).
- Better: parse owner/name from `git remote get-url origin`, so the check always matches what `dw update` pulls.
- Versions must stay plain `X.Y.Z`: `compare_versions` does `int()` on every part,
  and anything like `4.2.0-fork` silently compares as "equal" (it returns 0 on parse failure).

### #3 Merge the LED feature and cut the first fork release ✅
- Merge `feature/led-random-effect-options` → `main`. Tests pass, and the branch already includes a rebuilt `static/dist`.
- Bump `VERSION` to `4.2.0`, tag `v4.2.0`, and create a GitHub Release (FORK_README.md, "Developing the fork").
- Close or withdraw the matching upstream PR if it's still open, since upstream is inactive.

---

## 2. Install / update bugs

### #4 `dw checkout <branch>` fails on every normal install ✅ (reproduced)
The installer clones with `--single-branch`, so the fetch refspec only covers
`main`. `git fetch origin <branch>` then only writes `FETCH_HEAD`, never creates
`origin/<branch>`, and `git checkout -b <branch> origin/<branch>` fails:
```
fatal: 'origin/feature/led-random-effect-options' is not a commit ...
```
`dw update` on a non-main branch has the same problem: its `reset --hard origin/<branch>`
fails, or uses a stale ref.
**Fix (`dw` cmd_checkout and cmd_update):**
```bash
run_as_user git fetch origin "+refs/heads/$branch:refs/remotes/origin/$branch"
```

### #5 Updating from the web UI leaves root-owned files ⚠️
`POST /api/update` runs `dw update` from the service, which is `User=root`, with
no `SUDO_USER` set. In that context `run_as_user` runs git as root, and
`fix_repo_ownership` does nothing because it keys on `SUDO_USER`. New objects in
`.git/`, changed files and `update.log` end up owned by root, so the next
`dw update` from the `pi` shell fails with `Permission denied`.
**Fix:** in `dw`, work out the owner from the directory, not from `SUDO_USER`:
```bash
REPO_OWNER=$(stat -c %U "$INSTALL_DIR")
run_as_user() { if [[ $EUID -eq 0 && "$REPO_OWNER" != root ]]; then sudo -u "$REPO_OWNER" -- "$@"; else "$@"; fi; }
```
Do the same in `fix_repo_ownership`.

### #6 Remove the legacy update endpoints ✅
`GET /check_software_update` and `POST /update_software` (`main.py:2589-2600`,
`modules/update/update_manager.py`) are no longer used by the frontend. They:
- run `git pull` as root (same ownership problem as #5);
- skip the nginx/systemd/dw redeploy;
- run a blocking `git fetch` inside an `async` endpoint, which freezes the server while it runs;
- are still reachable by anything on the network.

Delete them and the module, or redirect them to the `/api/update` path.

### #7 Unpinned dependencies ⚠️
`requirements.txt` is all `>=` or unversioned, and includes a pre-release
(`Adafruit-Blinka-Raspberry-Pi5-Neopixel>=1.0.0rc1`). With no upstream watching,
a new FastAPI/pydantic/paho-mqtt/Blinka release can break `dw update` on a table
overnight.
- Freeze a known-good set from a working Pi (`.venv/bin/pip freeze > constraints.txt`) and install with `-c constraints.txt` in `setup-pi.sh` and `dw`.
- `requirements-nonrpi.txt` is missing **pyyaml** (`modules/connection/fluidnc_config.py` imports `yaml`), and `requirements.txt` is missing **zeroconf**, which the non-RPi file has. Make the two files consistent.

### #8 `setup-pi.sh` papercuts ⚠️
- The header and `--help` advertise `curl … | bash`, but `configure_uart` and the reboot prompt use `read`. Piped, those reads swallow the rest of the script. Use `read … < /dev/tty`, or drop the one-liner from the docs.
- `check_raspberry_pi` runs **after** the interactive UART prompt. Run it first.
- Writes both `dtoverlay=pi3-miniuart-bt` and `dtoverlay=miniuart-bt`, which are aliases of the same overlay. Keep one.
- `install_lgpio` hardcodes the `aarch64-linux-gnu` library path, so 32-bit OS installs break silently.
- `disable_wlan_powersave` relies on `iwconfig` (wireless-tools), which newer images don't ship. Use `iw dev wlan0 set power_save off` or NetworkManager's `wifi.powersave = 2`.

### #17 Smaller `dw` issues ⚠️
- `find_install_dir` only checks `$HOME/dune-weaver`, `/home/pi/dune-weaver` and `./`. Under `sudo` with a user other than `pi`, `$HOME` is `/root`, so the install isn't found. Also check `$(getent passwd "$SUDO_USER" | cut -d: -f6)/dune-weaver`.
- `dw update` does `git reset --hard` with no warning. Print `git status --short` first, and stash or abort if there are local changes.
- Under `set -e`, `nginx -t && systemctl restart nginx` ends the script quietly when `nginx -t` fails, without saying why. Make it explicit (`if ! nginx -t; then …`).
- Add `patterns/custom_patterns/` to `.gitignore`. Uploaded patterns are currently untracked but not ignored, so a fork commit containing a file of the same name would make `reset --hard` overwrite the user's file.

---

## 3. Security (LAN-exposed, runs as root)

### #10 Path traversal in file endpoints ✅
`normalize_file_path()` (`main.py:77`) only strips a `patterns/` prefix. It never
rejects `..` or absolute paths, and the result is passed straight to `os.path.join(THETA_RHO_DIR, …)`.
Because the service runs as **root**, anyone who can reach port 80 can:
- **delete any file**: `POST /delete_theta_rho_file {"file_name": "../../../etc/…"}` (`main.py:2124`);
- **write any file**: `POST /upload_theta_rho` with a multipart filename containing `../` (`main.py:1759`; `file.filename` is used verbatim);
- probably read or parse arbitrary files through the preview/coordinate endpoints (`main.py:1643, 1815, 1867, 2108, 2223, 2403, 2844, 2878, 3446`).

**Fix:** one helper, used everywhere a client-supplied name becomes a path:
```python
def safe_pattern_path(name: str) -> str:
    base = os.path.realpath(pattern_manager.THETA_RHO_DIR)
    p = os.path.realpath(os.path.join(base, normalize_file_path(name)))
    if os.path.commonpath([base, p]) != base:
        raise HTTPException(400, "Invalid file path")
    return p
```
For uploads, use `os.path.basename(file.filename)` and enforce a `.thr` extension.
Add a unit test that posts `../x` to each endpoint.

### #11 "Security mode" only exists in the UI ✅
- `security_mode` (lockdown / play_only) and its password are checked only by the frontend. No endpoint enforces them, and `PATCH /api/settings` can turn security off **without the password** (`main.py:1080-1091`).
- CORS is `allow_origins=["*"]` (`main.py:358`), so **any web page** opened by anyone on your LAN can call the API from their browser, including #10.
- The password is stored as unsalted SHA-256.

**Fix (in order of payoff):**
1. Restrict CORS to `http://<hostname>.local`, the Pi's IP, and your other tables (a settings list), instead of `*`.
2. When security mode isn't `off`, require a session token (issued by `/api/security/verify`) on mutating endpoints via a FastAPI dependency, and on any change to `security.*`.
3. Hash with `hashlib.scrypt` or `pbkdf2_hmac` plus a salt.

### #12 Consider not running as root (optional) ⚠️
`dune-weaver.service` has `User=root` mainly for NeoPixel GPIO access on a Pi 4.
If you use WLED, or the DW LEDs on SPI or a Pi 5, the service could run as `pi` with
`SupplementaryGroups=dialout gpio spi`. That shrinks the damage from #10 and
also fixes #5 and #6. If you need root for PWM NeoPixels, keep it, but fix #10
and #11 first.

---

## 4. Runtime bugs

### #9 Settings, playlists and caches can be wiped by a power cut ⚠️
`state.save()` (`modules/core/state.py:685`), `save_playlists()` and
`save_metadata_cache()` write with `open(path, "w")` directly. Sand tables get
unplugged at the wall, and a cut mid-write leaves a truncated file. Then:
- `settings.json`/`state.json` fail to parse → defaults load → the next save **overwrites** the real settings;
- `playlists.json` fails to parse → `load_playlists()` **deliberately resets it to `{}`** (`playlist_manager.py:36-38`). All playlists are lost.

`save()` also has no lock, while it's called both from the debounce `threading.Timer` and from request handlers.

**Fix:** a shared `atomic_write_json(path, data)` (write to `path.tmp`, `flush`, `os.fsync`, `os.replace`) behind a module lock. On a parse error, rename the bad file to `*.corrupt-<ts>` instead of overwriting it, and keep the previous good copy as `*.bak`.

### #13 Manual pause is ignored during Still Sands when "finish pattern first" is on ✅
`_execute_pattern_internal` (`modules/core/pattern_manager.py:~1304`) waits with
`while state.pause_requested or is_in_scheduled_pause_period():`. With
`scheduled_pause_finish_pattern` enabled, the pattern is meant to keep running
through the Still Sands window. But if you pause and resume manually during that
window, the loop stays stuck on `is_in_scheduled_pause_period()` until the
window ends. **Fix:** only include the scheduled-period term when finish-pattern-first is **off**:
```python
while state.pause_requested or (is_in_scheduled_pause_period() and not state.scheduled_pause_finish_pattern):
```
Add a unit test next to the existing Still Sands tests.

### #14 Motion "stop" drops queued moves without resolving their futures ✅
`MotionControlThread` handles `'stop'` (`pattern_manager.py:454-460`) by draining
the queue, and the futures of the drained `move` commands are never completed.
Pattern playback awaits one move at a time, so it rarely hits this. But a
`/move_to_center`, `/move_to_perimeter` or `/send_coordinate` request queued while
a stop is processed **hangs forever**. **Fix:** for each drained command, call
`command.future.get_loop().call_soon_threadsafe(command.future.cancel)`, or
`set_result(None)`.

### #15 `/restart_connection` blocks the server and ignores `port` ✅
`main.py:1439-1447` calls the synchronous `connection_manager.restart_connection()`
directly inside an `async def`. It contains `time.sleep`s and serial I/O, so the
whole web server and websockets freeze while it runs. It also validates
`request.port` and then never uses it. **Fix:** `await asyncio.to_thread(connection_manager.restart_connection, …)`,
and pass the port through, or drop the field.

### #16 `check_idle()` has no timeout ⚠️
The synchronous `check_idle()` (`modules/connection/connection_manager.py:1229`) loops
`while True` until the controller says `Idle`. It's used in the homing flow
(lines 1057-1169). If the controller sits in `Alarm`, or the serial link dies,
homing hangs forever and so does anything waiting on it. **Fix:** add a `timeout`
like `check_idle_async` has, and treat a timeout as homing failure.

---

## 5. Code health / maintenance

### #18 Cleanups
- `pattern_manager.py`: the "pause between patterns" and "pause between cycles" blocks (~1633-1668 and ~1690-1724) are near-copies. Extract one `_wait_between(pause_time)` helper.
- `main.py` is 4,245 lines. Split it into FastAPI `APIRouter`s (patterns, playlists, settings, LEDs, system/update, wifi). That makes #10 and #11 much easier to apply consistently.
- Ruff: run `ruff check --fix` for the 200 safe fixes, then make the CI lint job blocking for a small rule set (e.g. `E9,F63,F7,F82,F401,ASYNC`). The `ASYNC220/221` findings are real event-loop blockers worth reviewing.
- MQTT password is base64-"encoded" in `settings.json`. That's fine for a home device, but the comment should say it's obfuscation, not encryption.

### #19 CI
- Add a job that runs `npm ci && npm run build` and fails if `static/dist` differs from the commit, so a frontend change can't ship without its bundle.
- Run the tests on 3.11 **and** the Python of the current Raspberry Pi OS (3.11 on Bookworm, 3.13 on Trixie).
- `CODECOV_TOKEN` must be set as a secret on the fork, or remove the upload step.
- Add a Windows-safe test setup (skip `mock-serial` on Windows) if you develop from Windows.

### #20 Docs
- Replace the README install section with FORK_README.md, and add a "This is a maintained fork of tuanchris/dune-weaver" note with a changelog.
- Document `dw checkout` (after #4) as the way to try branches.

---

## Reviewed, no bug found
- `sys.exc_info()` in the pattern `finally` block works as intended.
- `random.shuffle(state.current_playlist)` mutates a list built fresh in `run_playlist`, not the saved playlist.
- Motion failure with an unknown machine position sets `stop_requested`, so `was_completed` correctly reports it as not completed.
- `check_idle_async` correctly runs serial I/O in a thread.
- `git reset --hard` in `dw update` keeps `settings.json`, `state.json`, `playlists.json` and uploaded patterns (all ignored or untracked).

## Not reviewed in depth
LED effect implementations (`modules/led/*effects*`, palettes), the WiFi manager, the
`dune-weaver-touch` Qt app, and most of the 17.6k-line React frontend got only a light pass or grep-level checks.
