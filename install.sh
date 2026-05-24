#!/usr/bin/env bash
# job-radar-production installer
#
# Usage:
#   bash install.sh                    # interactive install
#   bash install.sh --skills-only      # only copy skills to ~/.claude/commands/
#   bash install.sh --engine-only      # only set up ~/.job-radar/engine/
#   bash install.sh --no-skills        # set up everything except Claude Code skills
#   bash install.sh --target /path     # override skills target (default: ~/.claude/commands/)
#   bash install.sh --uninstall        # remove ~/.job-radar/ and skills (keeps profile.yml backup)
#
# What this does:
#   1. Verifies Python 3.10+ and PyYAML
#   2. Creates ~/.job-radar/ data dir
#   3. Copies the engine to ~/.job-radar/engine/
#   4. Applies the SQLite schema
#   5. Copies skills to ~/.claude/commands/ (so Claude Code picks them up)
#   6. Prompts you to copy an example profile and edit it
#
# Idempotent: re-running upgrades the engine + skills in place.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$HOME/.job-radar"
SKILLS_TARGET="$HOME/.claude/commands"
DO_SKILLS=1
DO_ENGINE=1
UNINSTALL=0

for arg in "$@"; do
    case "$arg" in
        --skills-only) DO_ENGINE=0 ;;
        --engine-only) DO_SKILLS=0 ;;
        --no-skills)   DO_SKILLS=0 ;;
        --target=*)    SKILLS_TARGET="${arg#--target=}" ;;
        --target)      shift; SKILLS_TARGET="$1" ;;
        --uninstall)   UNINSTALL=1 ;;
        -h|--help)
            grep -E "^# " "$0" | sed 's/^# //'
            exit 0
            ;;
    esac
done

say() { printf "\033[1m[install]\033[0m %s\n" "$*"; }
warn() { printf "\033[33m[warn]\033[0m %s\n" "$*"; }
die() { printf "\033[31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

uninstall() {
    say "Uninstalling job-radar..."
    if [ -f "$DATA_DIR/profile.yml" ]; then
        cp "$DATA_DIR/profile.yml" "$HOME/job-radar-profile.backup.yml"
        say "Saved profile.yml backup to ~/job-radar-profile.backup.yml"
    fi
    rm -rf "$DATA_DIR"
    for skill in job-radar job-radar-linkedin job-radar-firecrawl warm-line apply; do
        rm -f "$SKILLS_TARGET/$skill.md"
    done
    say "Uninstalled. ~/.job-radar/ removed; skills removed from $SKILLS_TARGET."
    say "Profile backup at ~/job-radar-profile.backup.yml (if you had one)."
    exit 0
}

if [ "$UNINSTALL" = 1 ]; then
    uninstall
fi

# 1. Python check
say "Checking Python 3.10+..."
if ! command -v python3 >/dev/null 2>&1; then
    die "python3 not found. Install Python 3.10+ first (https://python.org)."
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJ=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MIN=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJ" -lt 3 ] || { [ "$PY_MAJ" = 3 ] && [ "$PY_MIN" -lt 10 ]; }; then
    die "Python 3.10+ required (you have $PY_VERSION)"
fi
say "Python $PY_VERSION OK"

# 2. PyYAML
say "Checking PyYAML..."
if ! python3 -c 'import yaml' >/dev/null 2>&1; then
    warn "PyYAML not installed. Attempting pip install..."
    if command -v pip3 >/dev/null 2>&1; then
        pip3 install --user pyyaml || die "pip3 install pyyaml failed"
    else
        die "PyYAML missing and pip3 not found. Install manually: pip3 install pyyaml"
    fi
fi
say "PyYAML OK"

# 3. Engine
if [ "$DO_ENGINE" = 1 ]; then
    say "Setting up engine at $DATA_DIR/engine/..."
    mkdir -p "$DATA_DIR"
    rm -rf "$DATA_DIR/engine"
    cp -R "$REPO_DIR/engine" "$DATA_DIR/engine"
    cp -R "$REPO_DIR/visa" "$DATA_DIR/visa" 2>/dev/null || true

    # Apply schema (db.py auto-applies on first connect, but explicit is friendlier)
    python3 "$DATA_DIR/engine/db.py" >/dev/null
    say "Engine installed."
fi

# 4. Skills
if [ "$DO_SKILLS" = 1 ]; then
    say "Installing skills to $SKILLS_TARGET/..."
    if [ ! -d "$SKILLS_TARGET" ]; then
        mkdir -p "$SKILLS_TARGET"
    fi
    for skill in "$REPO_DIR"/skills/*.md; do
        cp "$skill" "$SKILLS_TARGET/"
    done
    say "Skills installed: $(ls "$REPO_DIR"/skills/ | tr '\n' ' ')"
fi

# 5. Profile bootstrap
if [ ! -f "$DATA_DIR/profile.yml" ]; then
    say ""
    say "No profile.yml found at $DATA_DIR/profile.yml"
    say "Available starters:"
    for example in "$REPO_DIR"/examples/profile.*.yml; do
        say "  $(basename "$example")"
    done
    say ""
    say "Pick one and copy it, then edit identity + targets. For example:"
    say "  cp $REPO_DIR/examples/profile.revops.yml $DATA_DIR/profile.yml"
    say "  \$EDITOR $DATA_DIR/profile.yml"
else
    say "Profile already exists at $DATA_DIR/profile.yml (preserved)."
fi

say ""
say "Done. Next steps:"
say "  1. Edit $DATA_DIR/profile.yml with your details"
say "  2. Open Claude Code in any directory and try:  /job-radar"
say "  3. (Optional) For LinkedIn alert ingest, ensure Claude Code Gmail MCP is auth'd"
say ""
say "DB lives at $DATA_DIR/radar.db (SQLite, your data)."
say "Briefings persist at $DATA_DIR/briefings/."
