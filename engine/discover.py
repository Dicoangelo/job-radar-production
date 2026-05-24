"""Discovery pipeline — scrape ATS boards listed in profile.targets, score, persist.

Run: python3 discover.py [--verbose]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import db as db_mod  # noqa: E402
from adapters import ADAPTERS  # noqa: E402
from scorer import score_posting  # noqa: E402


def seed_target_companies(conn) -> int:
    targets = config.get("targets", []) or []
    n = 0
    for t in targets:
        conn.execute(
            """INSERT OR IGNORE INTO target_companies
               (name, ats_type, ats_slug, priority, lane) VALUES (?,?,?,?,?)""",
            (t["name"], t["ats_type"], t["ats_slug"], t.get("priority", 3), t.get("lane")),
        )
        n += 1
    conn.commit()
    return n


def upsert_posting(conn, company: str, posting: dict, score_result: dict) -> tuple[bool, int]:
    existing = conn.execute(
        "SELECT id FROM job_postings WHERE company=? AND external_id=? AND source=?",
        (company, posting["external_id"], posting["source"]),
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE job_postings SET last_seen_at=datetime('now'), score=?, score_reasons=?, lane=? WHERE id=?",
            (score_result["score"], json.dumps(score_result["reasons"]), score_result["lane"], existing[0]),
        )
        return False, existing[0]

    cur = conn.execute(
        """INSERT INTO job_postings
           (external_id, company, role, url, location, description_text,
            posted_at, source, lane, score, score_reasons, raw_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            posting["external_id"], company, posting["role"], posting["url"],
            posting.get("location", ""), posting.get("description_text", ""),
            posting.get("posted_at"), posting["source"],
            score_result["lane"], score_result["score"],
            json.dumps(score_result["reasons"]),
            json.dumps(posting.get("raw_metadata", {})),
        ),
    )
    return True, cur.lastrowid


def run(verbose: bool = False) -> dict:
    start = time.time()
    config.load()
    conn = db_mod.connect()
    seed_target_companies(conn)

    targets = config.get("targets", []) or []
    stats = {"fetched": 0, "new": 0, "updated": 0, "errors": []}

    for t in targets:
        adapter = ADAPTERS.get(t["ats_type"])
        if not adapter:
            if verbose:
                print(f"[{t['name']}] skip — no adapter for {t['ats_type']}")
            continue
        try:
            jobs = adapter(t["ats_slug"])
            if verbose:
                print(f"[{t['name']}] {len(jobs)} jobs via {t['ats_type']}")
            for j in jobs:
                stats["fetched"] += 1
                sr = score_posting(j.get("role", ""), j.get("description_text", ""), j.get("location", ""))
                is_new, _ = upsert_posting(conn, t["name"], j, sr)
                if is_new:
                    stats["new"] += 1
                else:
                    stats["updated"] += 1
            conn.execute("UPDATE target_companies SET last_checked=datetime('now') WHERE name=?", (t["name"],))
            conn.commit()
        except Exception as e:
            stats["errors"].append(f"{t['name']}: {type(e).__name__}: {e}")
            if verbose:
                print(f"[{t['name']}] ERROR: {e}")

    # Stale = not seen in 7 days
    conn.execute(
        """UPDATE job_postings SET status='stale'
           WHERE status='new' AND last_seen_at < datetime('now','-7 days')"""
    )

    duration_ms = int((time.time() - start) * 1000)
    conn.execute(
        """INSERT INTO radar_runs (postings_discovered, postings_new, errors, duration_ms)
           VALUES (?,?,?,?)""",
        (stats["fetched"], stats["new"], json.dumps(stats["errors"]), duration_ms),
    )
    conn.commit()
    conn.close()

    stats["duration_ms"] = duration_ms
    return stats


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    stats = run(verbose=verbose)
    print(json.dumps(stats, indent=2))
