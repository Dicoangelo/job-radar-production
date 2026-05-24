"""Ashby public job board API adapter.
Endpoint: https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true
"""
import urllib.request
import json
import re
from html import unescape

UA = "Mozilla/5.0 (job-radar/1.0)"
TIMEOUT = 20


def _strip_html(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def fetch(slug: str) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for j in data.get("jobs", []):
        comp = j.get("compensation") or {}
        summary = comp.get("compensationTierSummary", "")
        desc = _strip_html(j.get("descriptionHtml", "")) or j.get("descriptionPlain", "")
        out.append({
            "external_id": j.get("id"),
            "role": j.get("title", ""),
            "url": j.get("jobUrl", ""),
            "location": j.get("locationName", ""),
            "description_text": desc[:8000],
            "posted_at": j.get("publishedAt"),
            "source": "ashby",
            "raw_metadata": {
                "team": j.get("teamName"),
                "employmentType": j.get("employmentType"),
                "isRemote": j.get("isRemote"),
                "comp_summary": summary,
            },
            "departments": [j.get("departmentName")] if j.get("departmentName") else [],
        })
    return out


if __name__ == "__main__":
    import sys
    for job in fetch(sys.argv[1] if len(sys.argv) > 1 else "linear")[:3]:
        print(job["role"], "|", job["location"], "|", job["url"])
