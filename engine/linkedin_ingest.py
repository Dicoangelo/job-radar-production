#!/usr/bin/env python3
"""LinkedIn job-alert ingest — turns LinkedIn alert emails into scored,
deduped rows in radar.db's job_postings table.

Gmail extraction is done by the /job-radar-linkedin skill (Claude orchestrates
the Gmail MCP). This script is the durable half: it takes the extracted job
cards as JSON on stdin and owns normalization, scoring, dedup, and DB writes.

Reuses scorer.py — one scoring brain, no drift between LinkedIn-sourced rows
and ATS-scraped ones.

Input  (stdin): JSON array of
  {"company","role","posted","alert","location"?,"easy_apply"?,
   "connections"?,"named_connection"?,"url"?}
Output (stdout): one-screen radar-format shortlist.

Exit 0 always (discovery tool, not a gate).
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db as db_mod  # noqa: E402
from scorer import score_posting  # noqa: E402

SOURCE = "linkedin_alert"
TODAY = date.today().isoformat()

_SUFFIX = re.compile(
    r"[\s,]*\b(inc|llc|corp|corporation|ltd|limited|co|gmbh|sa|ag|plc)\.?$",
    re.I,
)


def norm_company(c: str) -> str:
    c = (c or "").strip()
    prev = None
    while prev != c:
        prev = c
        c = _SUFFIX.sub("", c).strip()
    return c


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def ext_id(company: str, role: str) -> str:
    return hashlib.sha1(f"{_key(company)}|{_key(role)}".encode()).hexdigest()[:16]


def role_is_dup(role_a: str, role_b: str) -> bool:
    a, b = _key(role_a), _key(role_b)
    if not a or not b:
        return False
    if a == b:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.92


def load_applied(conn) -> list[tuple[str, str]]:
    # ALL-TIME, ALL-STATUS dedup. Once applied to (any status), never re-surface.
    rows = conn.execute("SELECT company, role FROM applications").fetchall()
    return [(norm_company(c), r or "") for c, r in rows]


def already_applied(applied: list[tuple[str, str]], company: str, role: str) -> bool:
    ck = _key(company)
    for ac, ar in applied:
        if _key(ac) == ck and role_is_dup(role, ar):
            return True
    return False


def upsert_posting(conn, company: str, role: str, card: dict, sr: dict) -> str:
    eid = ext_id(company, role)
    row = conn.execute(
        "SELECT id, status FROM job_postings WHERE company=? AND external_id=? AND source=?",
        (company, eid, SOURCE),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE job_postings SET last_seen_at=datetime('now'), "
            "score=?, score_reasons=?, lane=? WHERE id=?",
            (sr["score"], json.dumps(sr["reasons"]), sr["lane"], row[0]),
        )
        return "seen"
    conn.execute(
        """INSERT INTO job_postings
           (external_id, company, role, url, location, remote_policy,
            lane, score, score_reasons, posted_at, source, status, raw_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?, 'new', ?)""",
        (
            eid, company, role,
            card.get("url") or f"https://www.linkedin.com/jobs/search/?keywords={role.replace(' ', '%20')}",
            card.get("location"), card.get("remote_policy"),
            sr["lane"], sr["score"], json.dumps(sr["reasons"]),
            card.get("posted"), SOURCE, json.dumps(card),
        ),
    )
    return "new"


def upsert_contact(conn, name: str, company: str, role: str) -> None:
    name = (name or "").strip()
    if not name:
        return
    exists = conn.execute(
        "SELECT id FROM contacts WHERE lower(name)=lower(?) AND lower(COALESCE(company,''))=lower(?)",
        (name, company),
    ).fetchone()
    if exists:
        return
    conn.execute(
        """INSERT INTO contacts (name, company, relationship, context, last_contact, notes)
           VALUES (?,?, 'linkedin_connection', ?, ?, ?)""",
        (
            name, company,
            f"Surfaced via LinkedIn job alert on the '{role}' posting",
            TODAY,
            f"[linkedin-ingest {TODAY}] connection visible on {company} - {role}. "
            f"Warm-line candidate, verify degree/strength before outreach.",
        ),
    )


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("no input on stdin (expected JSON array of job cards)", file=sys.stderr)
        return 0
    cards = json.loads(raw)

    conn = db_mod.connect()
    applied = load_applied(conn)

    new_rows: list[dict] = []
    seen_rows: list[dict] = []
    done_rows: list[dict] = []
    blocked_rows: list[dict] = []
    warm_added = 0
    batch_seen: dict[str, str] = {}

    for card in cards:
        company = norm_company(card.get("company", ""))
        role = (card.get("role") or "").strip()
        if not company or not role:
            continue

        bk = ext_id(company, role)
        if bk in batch_seen:
            continue
        batch_seen[bk] = role

        sr = score_posting(role, "", card.get("location", "") or "")
        rec = {
            "company": company, "role": role, "lane": sr["lane"],
            "score": sr["score"], "alert": card.get("alert", ""),
            "posted": card.get("posted", ""), "loc": card.get("location", ""),
            "conn": card.get("named_connection", ""),
            "easy": bool(card.get("easy_apply")),
        }

        if already_applied(applied, company, role):
            done_rows.append(rec)
            continue
        if sr["lane"] == "unfit":
            blocked_rows.append(rec)
            continue

        status = upsert_posting(conn, company, role, card, sr)
        (new_rows if status == "new" else seen_rows).append(rec)

        if rec["conn"]:
            before = conn.total_changes
            upsert_contact(conn, rec["conn"], company, role)
            if conn.total_changes > before:
                warm_added += 1

    conn.commit()
    conn.close()

    # Output
    out: list[str] = []
    out.append(f"JOB RADAR — LINKEDIN INGEST {TODAY}")
    out.append("")
    out.append("PIPELINE")
    out.append(f"  Cards parsed:        {len(cards)}")
    out.append(f"  New postings:        {len(new_rows)}")
    out.append(f"  Already seen:        {len(seen_rows)}")
    out.append(f"  Already applied:     {len(done_rows)} (suppressed)")
    out.append(f"  Off-lane/blocked:    {len(blocked_rows)} (suppressed)")
    out.append(f"  Warm-line contacts:  +{warm_added} into contacts")
    out.append("")

    ranked = sorted(new_rows + seen_rows, key=lambda r: -r["score"])
    if ranked:
        out.append("SHORTLIST (new + still-open, score-ranked)")
        for r in ranked:
            warm = f" · WARM:{r['conn']}" if r["conn"] else ""
            easy = " · EasyApply (find direct ATS)" if r["easy"] else ""
            out.append(
                f"  [{r['score']:>3}] {r['lane']:<14} {r['company']} - {r['role']}{warm}{easy}"
            )
            out.append(
                f"        alert='{r['alert']}' · posted {r['posted']} · {r['loc'] or 'loc n/a'}"
            )
        out.append("")

    if done_rows:
        out.append("ALREADY APPLIED (dedup, not re-surfaced)")
        for r in done_rows:
            out.append(f"  [done] {r['company']} - {r['role']}")
        out.append("")

    if blocked_rows:
        out.append("OFF-LANE / BLOCKLIST (suppressed)")
        for r in blocked_rows:
            out.append(f"  [skip] {r['company']} - {r['role']}")
        out.append("")

    out.append("NEXT")
    out.append("  Top picks are in job_postings (source=linkedin_alert, status=new).")
    out.append("  /job-radar ranks them with warm-line joins.")
    out.append("  LinkedIn EasyApply has near-zero response. Resolve each role to its")
    out.append("  direct ATS (company careers page / Greenhouse / Lever / Ashby) before applying.")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
