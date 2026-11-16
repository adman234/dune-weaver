#!/bin/bash
#
# Fresh install of Dune Weaver from the adman234 fork.
#
# Paste into an SSH session on the Pi (as your normal user, not root):
#
#   curl -fsSL https://raw.githubusercontent.com/adman234/dune-weaver/main/scripts/fork-install.sh | bash
#
# Pass setup-pi.sh options after "bash -s --":
#
#   curl -fsSL .../scripts/fork-install.sh | bash -s -- --no-hotspot
#
# Environment overrides:
#   DW_BRANCH=feature/xyz   install a branch instead of main
#   DW_REPO=<git url>       install from a different repo
#   DW_DIR=<path>           install somewhere other than ~/dune-weaver
#
# Already have Dune Weaver installed? Use scripts/fork-update.sh instead.

# Everything lives in main() so a half-downloaded script never runs.
main() {
    set -euo pipefail

    local repo="${DW_REPO:-https://github.com/adman234/dune-weaver.git}"
    local branch="${DW_BRANCH:-main}"
    local dir="${DW_DIR:-$HOME/dune-weaver}"

    say()  { echo -e "\033[0;34m==>\033[0m $*"; }
    die()  { echo -e "\033[0;31mERROR:\033[0m $*" >&2; exit 1; }

    [[ $EUID -ne 0 ]] || die "Run this as your normal user (e.g. pi), not root or sudo. It uses sudo itself where needed."
    command -v sudo >/dev/null || die "sudo is required."

    if [[ -e "$dir" ]]; then
        if [[ -f "$dir/main.py" ]]; then
            die "Dune Weaver is already installed at $dir.
       To switch it to the fork or update it (with a backup first), run:
       curl -fsSL https://raw.githubusercontent.com/adman234/dune-weaver/main/scripts/fork-update.sh | bash"
        fi
        die "$dir already exists and isn't a Dune Weaver install. Move it out of the way first."
    fi

    say "Installing git..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq git

    # Full clone (not --single-branch) so `dw checkout <branch>` works later.
    say "Cloning $repo ($branch) into $dir..."
    git clone --branch "$branch" "$repo" "$dir"
    cd "$dir"

    say "Running setup-pi.sh (installs Python env, nginx, service, dw CLI)..."
    # setup-pi.sh asks questions; read them from the terminal, not from the curl pipe.
    if [[ -r /dev/tty ]]; then
        bash setup-pi.sh "$@" < /dev/tty
    else
        bash setup-pi.sh "$@"
    fi
}

main "$@"
