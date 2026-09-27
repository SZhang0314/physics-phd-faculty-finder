"""Fast structural checks for the generated static site."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def main() -> None:
    pages = list(DIST.rglob("*.html"))
    data = json.loads((DIST / "data" / "schools.json").read_text(encoding="utf-8"))
    assert len(data) == 30
    assert len(list((DIST / "schools").glob("*.html"))) == 30
    assert sum(len(item["faculty"]) for item in data) >= 1200
    assert (DIST / "index.html").read_text(encoding="utf-8").count("data-school-card") == 30

    broken: list[tuple[str, str]] = []
    for page in pages:
        text = page.read_text(encoding="utf-8")
        assert "<title>" in text and "</html>" in text
        for url in re.findall(r'(?:href|src)="([^"]+)"', text):
            if url.startswith(("http://", "https://", "#")):
                continue
            target = (page.parent / url.split("#", 1)[0]).resolve()
            if not target.exists():
                broken.append((str(page.relative_to(ROOT)), url))
    assert not broken, broken[:20]
    print(f"OK: {len(pages)} HTML pages, 30 schools, {sum(len(item['faculty']) for item in data)} faculty, no broken internal links")


if __name__ == "__main__":
    main()
