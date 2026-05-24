"""Optional visa annotation — annotates a company name with LCA (H-1B) filing counts
from the DOL disclosure data.

Only loaded by /job-radar when profile.visa.enabled is true.

For citizens / permanent residents this module never runs. For visa users
(TN, H-1B, O-1, etc.), it provides a quick "is this company actually filing
work-auth paperwork?" signal.

To use, point LCA_DB at a SQLite database with at least:
  lca_filings(employer_normalized TEXT, decision_date TEXT, wage_rate_from REAL)

The DOL publishes the H-1B Disclosure Data quarterly:
  https://www.dol.gov/agencies/eta/foreign-labor/performance

You can build the SQLite file from the CSV/XLSX with the helper script:
  python3 visa/build_lca_db.py path/to/H-1B_Disclosure_Data_FYxxxx.csv
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path.home() / ".job-radar" / "lca.db"
DB_PATH = Path(os.environ.get("JOB_RADAR_LCA_DB", str(DEFAULT_DB)))


def annotate(company: str, years: int = 3) -> dict:
    """Return {count, avg_wage, verdict} for a company name.

    verdict ∈ {'STRONG' (50+), 'LIKELY' (5-49), 'UNVERIFIED' (<5), 'NO_DB' (db missing)}
    """
    if not DB_PATH.exists():
        return {"count": 0, "avg_wage": None, "verdict": "NO_DB"}

    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        f"""SELECT COUNT(*) AS n, ROUND(AVG(wage_rate_from), 0)
            FROM lca_filings
            WHERE employer_normalized LIKE '%' || lower(?) || '%'
              AND decision_date >= date('now','-{int(years)} years')""",
        (company.lower(),),
    ).fetchone()
    conn.close()

    n = row[0] or 0
    avg = int(row[1]) if row[1] else None
    if n >= 50:
        verdict = "STRONG"
    elif n >= 5:
        verdict = "LIKELY"
    else:
        verdict = "UNVERIFIED"
    return {"count": n, "avg_wage": avg, "verdict": verdict}


if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "Anthropic"
    print(annotate(company))
