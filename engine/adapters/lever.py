"""Lever public postings API adapter.
Endpoint: https://api.lever.co/v0/postings/{slug}?mode=json
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
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for j in data:
        cats = j.get("categories") or {}
        desc = j.get("descriptionPlain") or _strip_html(j.get("description", ""))
        lists = "\n".join(
            f"{l.get('text','')}: " + _strip_html(l.get("content", ""))
            for l in (j.get("lists") or [])
        )
        out.append({
            "external_id": j.get("id"),
            "role": j.get("text", ""),
            "url": j.get("hostedUrl", "") or j.get("applyUrl", ""),
            "location": cats.get("location", ""),
            "description_text": (desc + "\n" + lists)[:8000],
            "posted_at": j.get("createdAt"),
            "source": "lever",
            "raw_metadata": {
                "team": cats.get("team"),
                "department": cats.get("department"),
                "commitment": cats.get("commitment"),
                "workplaceType": j.get("workplaceType"),
            },
            "departments": [cats.get("department")] if cats.get("department") else [],
        })
    return out


if __name__ == "__main__":
    import sys
    for job in fetch(sys.argv[1] if len(sys.argv) > 1 else "dbtlabs")[:3]:
        print(job["role"], "|", job["location"], "|", job["url"])
