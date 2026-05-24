"""Profile loader — single point of truth for all engine + skill behavior.

Resolves profile.yml in this order:
  1. $JOB_RADAR_PROFILE  (absolute path)
  2. ~/.job-radar/profile.yml
  3. ./profile.yml  (cwd)
  4. examples/profile.generic.yml  (last resort, with a stderr warning)

The profile is loaded once per process and cached. Skills that change profile
mid-session should restart the process.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print(
        "error: PyYAML is required. Install with: pip install pyyaml",
        file=sys.stderr,
    )
    raise

_PROFILE: dict | None = None
_PROFILE_PATH: Path | None = None


def _candidate_paths() -> list[Path]:
    paths = []
    env = os.environ.get("JOB_RADAR_PROFILE")
    if env:
        paths.append(Path(env).expanduser().resolve())
    paths.append(Path.home() / ".job-radar" / "profile.yml")
    paths.append(Path.cwd() / "profile.yml")
    paths.append(Path(__file__).resolve().parent.parent / "examples" / "profile.generic.yml")
    return paths


def load(force_reload: bool = False) -> dict:
    global _PROFILE, _PROFILE_PATH
    if _PROFILE is not None and not force_reload:
        return _PROFILE

    for candidate in _candidate_paths():
        if candidate.is_file():
            with candidate.open() as f:
                _PROFILE = yaml.safe_load(f) or {}
            _PROFILE_PATH = candidate
            if "generic" in candidate.name:
                print(
                    f"warning: using generic profile at {candidate}. "
                    "Copy examples/profile.*.yml to ~/.job-radar/profile.yml and edit.",
                    file=sys.stderr,
                )
            return _PROFILE

    print(
        "error: no profile.yml found. Looked in:\n  "
        + "\n  ".join(str(p) for p in _candidate_paths()),
        file=sys.stderr,
    )
    sys.exit(2)


def path() -> Path | None:
    """Return the path the active profile was loaded from."""
    if _PROFILE is None:
        load()
    return _PROFILE_PATH


def get(key: str, default: Any = None) -> Any:
    """Dotted-key access into the profile. e.g. get('comp_floor.amount')."""
    profile = load()
    cur: Any = profile
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def lanes() -> dict[str, dict]:
    return get("lanes", {}) or {}


def title_blocklist() -> list[str]:
    return get("title_blocklist", []) or []


def lane_names() -> list[str]:
    return list(lanes().keys())


if __name__ == "__main__":
    p = load()
    print(f"loaded profile: {path()}")
    print(f"identity: {p.get('identity', {}).get('name', '?')}")
    print(f"lanes: {', '.join(lane_names())}")
    print(f"targets: {len(p.get('targets', []))}")
