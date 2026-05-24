"""Generic lane scorer — config-driven.

Reads lane definitions, blocklist, and flag rules from profile.yml.
Score 0-100. Threshold from profile.output.shortlist_threshold.

Anything that classifies to no lane returns lane='unfit', score=10.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402


def _regex_score(text: str, rules: list[dict]) -> tuple[int, list[str]]:
    """rules is a list of {pattern, delta, label} dicts from profile.yml."""
    score = 0
    reasons = []
    t = (text or "").lower()
    for rule in rules or []:
        pattern = rule["pattern"]
        delta = rule["delta"]
        label = rule.get("label", pattern)
        if re.search(pattern, t, re.IGNORECASE):
            score += delta
            sign = "+" if delta > 0 else ""
            reasons.append(f"{sign}{delta} {label}")
    return score, reasons


def _count_phrases(text: str, phrases: list[str]) -> int:
    t = (text or "").lower()
    return sum(1 for p in phrases if p.lower() in t)


def classify_lane(role: str, description: str) -> tuple[str, list[str]]:
    """Title-first classification. The role title must match a lane signal —
    description alone is not enough."""
    role_l = (role or "").lower()
    desc_l = (description or "").lower()

    lanes_cfg = config.lanes()
    title_scores: dict[str, int] = {}
    title_hits: dict[str, list[str]] = {}

    for lane, cfg in lanes_cfg.items():
        patterns = cfg.get("title_signals", [])
        hits = [p for p in patterns if re.search(p, role_l, re.IGNORECASE)]
        title_scores[lane] = len(hits)
        title_hits[lane] = hits

    if not title_scores:
        return "unfit", ["no lanes defined in profile"]

    best = max(title_scores, key=title_scores.get)
    if title_scores[best] == 0:
        return "unfit", []

    boosts = lanes_cfg[best].get("desc_boosts", []) or []
    desc_hits = _count_phrases(desc_l, boosts)

    reasons = [f"title:{h}" for h in title_hits[best][:2]]
    if desc_hits:
        reasons.append(f"desc+{desc_hits}")
    return best, reasons


def score_posting(role: str, description: str, location: str = "") -> dict:
    role = role or ""
    description = description or ""
    location_l = (location or "").lower()

    # Hard title-blocklist
    for pattern in config.title_blocklist():
        if re.search(pattern, role, re.IGNORECASE):
            return {"lane": "unfit", "score": 0, "reasons": [f"title excluded: {pattern}"]}

    lane, lane_hits = classify_lane(role, description)

    if lane == "unfit":
        return {"lane": "unfit", "score": 10, "reasons": ["no lane match"] + lane_hits}

    score = 45  # baseline for a lane match
    reasons = [f"lane={lane}"] + [f"kw: {h}" for h in lane_hits]

    # Description red/green flags from profile
    red_rules = config.get("description_red_flags", []) or []
    green_rules = config.get("description_green_flags", []) or []
    r_score, r_reasons = _regex_score(description, red_rules)
    g_score, g_reasons = _regex_score(description, green_rules)
    score += r_score + g_score
    reasons.extend(r_reasons + g_reasons)

    # Location signals
    whitelist = [w.lower() for w in (config.get("location_whitelist", []) or [])]
    blacklist = [w.lower() for w in (config.get("location_blacklist", []) or [])]
    if any(b in location_l for b in blacklist):
        return {"lane": "unfit", "score": 0,
                "reasons": reasons + [f"-100 location blacklisted: {location_l[:40]}"]}
    if any(w in location_l for w in whitelist):
        score += 10
        reasons.append("+10 location ok")
    elif location_l:
        # Has a location but it doesn't match whitelist — soft penalty
        score -= 8
        reasons.append("-8 location off-whitelist")

    # Comp floor (only when posting includes comp signal)
    floor_amount = config.get("comp_floor.amount", 0) or 0
    if floor_amount > 0:
        comp_match = re.search(r"\$\s*(\d{2,3})[,.]?(\d{3})", description)
        if comp_match:
            try:
                comp_val = int(comp_match.group(1) + comp_match.group(2))
                if comp_val < floor_amount:
                    score -= 15
                    reasons.append(f"-15 comp ${comp_val:,} < floor ${floor_amount:,}")
            except (ValueError, AttributeError):
                pass

    score = max(0, min(100, score))
    return {"lane": lane, "score": score, "reasons": reasons}


if __name__ == "__main__":
    import json
    role = sys.argv[1] if len(sys.argv) > 1 else "Senior Revenue Operations Manager"
    desc = sys.argv[2] if len(sys.argv) > 2 else "Remote-friendly. 3-5 years. Salesforce admin experience required."
    loc = sys.argv[3] if len(sys.argv) > 3 else "Remote - US"
    print(json.dumps(score_posting(role, desc, loc), indent=2))
