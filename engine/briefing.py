"""Daily briefing — produces a one-screen markdown briefing from the DB.

Reads profile.output for shortlist threshold and result counts. Lanes are
loaded dynamically from profile.yml, so the briefing groups by whatever lanes
the user defined (not hardcoded).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import db as db_mod  # noqa: E402


def q(conn, sql, params=()):
    return conn.execute(sql, params).fetchall()


def build_briefing() -> str:
    config.load()
    conn = db_mod.connect()
    today = datetime.now().strftime("%Y-%m-%d")
    threshold = int(config.get("output.shortlist_threshold", 60))
    lane_names = config.lane_names()
    lane_filter_csv = ",".join(f"'{n}'" for n in lane_names) or "''"

    # Mark stale (>7d)
    conn.execute(
        "UPDATE job_postings SET status='stale' "
        "WHERE status='new' AND last_seen_at < datetime('now','-7 day')"
    )
    stale_marked = conn.total_changes
    conn.commit()

    # Fresh (last 24h, score >= threshold)
    fresh = q(
        conn,
        f"""SELECT lane, company, role, location, score, url
            FROM job_postings
            WHERE lane IN ({lane_filter_csv})
              AND score >= ?
              AND discovered_at >= datetime('now','-1 day')
              AND date(last_seen_at) >= date('now','-1 day')
            ORDER BY lane, score DESC
            LIMIT 30""",
        (threshold,),
    )

    # Shortlist — score >= threshold+10, not yet applied, history-aware
    shortlist = q(
        conn,
        f"""WITH prior_app AS (
                SELECT LOWER(company) AS co_l,
                       MAX(CASE
                           WHEN status='rejected' THEN 25
                           WHEN status IN ('applied','screening','interviewing','preparing') THEN 100
                           WHEN status='ghosted' THEN 15
                           WHEN status='withdrawn' THEN 10
                           ELSE 0
                       END) AS penalty,
                       GROUP_CONCAT(DISTINCT status) AS statuses
                FROM applications
                GROUP BY LOWER(company)
            )
            SELECT p.lane, p.company, p.role, p.location,
                   p.score - COALESCE(pa.penalty, 0) AS effective_score,
                   p.score AS raw_score,
                   COALESCE(pa.statuses, '') AS prior,
                   p.url
            FROM job_postings p
            LEFT JOIN applications a
              ON LOWER(a.company)=LOWER(p.company) AND LOWER(a.role)=LOWER(p.role)
            LEFT JOIN prior_app pa ON pa.co_l = LOWER(p.company)
            WHERE p.lane IN ({lane_filter_csv})
              AND p.score >= ?
              AND a.id IS NULL
              AND p.status='new'
              AND date(p.last_seen_at) >= date('now','-2 day')
              AND (p.score - COALESCE(pa.penalty, 0)) >= ?
            ORDER BY effective_score DESC, p.score DESC
            LIMIT 20""",
        (threshold + 10, threshold),
    )

    # Recent application changes (last 2 days)
    status_changes = q(
        conn,
        """SELECT company, role, status, updated_at
           FROM applications
           WHERE updated_at >= datetime('now','-2 day')
             AND status NOT IN ('ghosted')
           ORDER BY updated_at DESC""",
    )

    # Stale apps (>14d)
    stale = q(
        conn,
        """SELECT company, role, status, updated_at
           FROM applications
           WHERE status IN ('applied','screening','interviewing')
             AND updated_at < datetime('now','-14 day')
           ORDER BY updated_at ASC
           LIMIT 15""",
    )

    # Last run
    last_run = q(
        conn,
        "SELECT postings_discovered, postings_new, errors, run_at FROM radar_runs ORDER BY id DESC LIMIT 1",
    )
    lane_counts = dict(
        q(conn, "SELECT lane, COUNT(*) FROM job_postings WHERE status='new' GROUP BY lane")
    )

    # Warm-line names for shortlist companies (best-effort)
    warm_by_company: dict[str, list] = {}
    for row in shortlist:
        company = row[1]
        if company in warm_by_company:
            continue
        warm_by_company[company] = q(
            conn,
            """SELECT name, role, linkedin FROM contacts
               WHERE LOWER(company) LIKE '%' || LOWER(?) || '%'
               ORDER BY last_contact DESC LIMIT 3""",
            (company,),
        )

    conn.close()

    # Render
    lines = [f"# Job Radar Briefing — {today}", ""]
    if last_run:
        pd, pn, errs, started = last_run[0]
        errs_list = json.loads(errs or "[]")
        lines += [
            f"**Last run:** {started} — {pd} postings scanned, {pn} new, {len(errs_list)} source errors. "
            f"{stale_marked} postings auto-marked stale (>7d unseen).",
            "",
        ]

    pipeline = " | ".join(f"{n}={lane_counts.get(n,0)}" for n in lane_names) or "(no lanes)"
    lines.append(f"**Pipeline:** {pipeline}")
    lines.append("")

    if fresh:
        lines += [f"## Fresh signal (last 24h, score >= {threshold})", ""]
        current_lane = None
        for lane, company, role, loc, score, url in fresh:
            if lane != current_lane:
                lines += ["", f"### {lane}"]
                current_lane = lane
            lines.append(f"- **{score}** · {company} — {role} · {loc or '—'}")
            if url:
                lines.append(f"  {url}")
        lines.append("")
    else:
        lines += ["## Fresh signal", f"_No new postings with score >= {threshold} in the last 24h._", ""]

    if shortlist:
        lines += [f"## Shortlist (effective score >= {threshold}, history-penalized)", ""]
        for lane, company, role, loc, eff_score, raw_score, prior, url in shortlist:
            history = f" · prior:{prior}" if prior else ""
            score_str = f"**{eff_score}**" if eff_score == raw_score else f"**{eff_score}** (raw {raw_score})"
            lines.append(f"- [{lane}] {score_str} · {company} — {role} · {loc or '—'}{history}")
            if url:
                lines.append(f"  {url}")
            warm = warm_by_company.get(company, [])
            if warm:
                names = " · ".join(f"{n}" + (f" ({r})" if r else "") for n, r, _ in warm)
                lines.append(f"  warm: {names}")
        lines.append("")

    if status_changes:
        lines += ["## Application updates", ""]
        for company, role, status, upd in status_changes:
            lines.append(f"- **{company}** — {role} → `{status}` on {upd}")
        lines.append("")

    if stale:
        lines += ["## Stale applications (>14d no update)", ""]
        for company, role, status, upd in stale:
            lines.append(f"- {company} — {role} · {status} · last update {upd}")
        lines.append("")

    # Persist briefing file
    out_dir = Path(config.get("output.briefing_dir", "~/.job-radar/briefings")).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{today}.md"
    briefing = "\n".join(lines)
    out_file.write_text(briefing)
    return briefing


if __name__ == "__main__":
    print(build_briefing())
