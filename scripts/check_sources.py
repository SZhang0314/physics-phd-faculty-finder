"""Check availability and basic structure of official faculty directory sources."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import time

import requests
from bs4 import BeautifulSoup


SOURCES = [
    ("mit", "https://physics.mit.edu/faculty/"),
    ("stanford", "https://physics.stanford.edu/people/faculty"),
    ("harvard", "https://www.physics.harvard.edu/people/faculty"),
    ("caltech", "https://www.pma.caltech.edu/people?cat_one=all&cat_two=Physics"),
    ("upenn", "https://www.physics.upenn.edu/people/standing-faculty"),
    ("cornell", "https://physics.cornell.edu/faculty"),
    ("yale", "https://physics.yale.edu/people/faculty/primary-faculty"),
    ("jhu", "https://physics-astronomy.jhu.edu/people/"),
    ("berkeley", "https://physics.berkeley.edu/directory?role%5B%5D=11"),
    ("uchicago", "https://physics.uchicago.edu/people/"),
    ("princeton", "https://phy.princeton.edu/people/faculty"),
    ("columbia", "https://www.physics.columbia.edu/content/faculty"),
    ("northwestern", "https://physics.northwestern.edu/people/faculty/core-faculty/"),
    ("ucla", "https://www.pa.ucla.edu/faculty"),
    ("michigan", "https://lsa.umich.edu/physics/people/faculty.directory.html"),
    ("cmu", "https://www.cmu.edu/physics/people/faculty/index.html"),
    ("nyu", "https://physics.nyu.edu/people/faculty.html"),
    ("brown", "https://physics.brown.edu/about/people/faculty"),
    ("duke", "https://physics.duke.edu/people/other-faculty/primary-and-joint-faculty"),
    ("utaustin", "https://physics.utexas.edu/directory"),
    ("uiuc", "https://physics.illinois.edu/people/directory/faculty"),
    ("ucsd", "https://catalog.ucsd.edu/faculty/PHYS.html"),
    ("pennstate", "https://science.psu.edu/people?department=16&person_type=Faculty"),
    ("washington", "https://phys.washington.edu/people/faculty"),
    ("bu", "https://www.bu.edu/physics/people/faculty-lecturers/"),
    ("purdue", "https://www.physics.purdue.edu/people/faculty/"),
    ("rice", "https://physics.rice.edu/core-faculty"),
    ("wisconsin", "https://www.physics.wisc.edu/people/faculty/"),
    ("ucdavis", "https://physics.ucdavis.edu/people/faculty"),
    ("gatech", "https://physics.gatech.edu/people/directory/1000?rid=4"),
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/128.0 Safari/537.36"
    )
}


def check(source: tuple[str, str]) -> tuple[str, str]:
    key, url = source
    error = None
    for attempt in range(3):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=18,
                verify=False if key == "nyu" else True,
            )
            soup = BeautifulSoup(response.text, "html.parser")
            headings = [
                " ".join(tag.get_text(" ", strip=True).split())
                for tag in soup.select("main h2, main h3, main h4, article h2, article h3")
            ]
            headings = [item for item in headings if 2 <= len(item) <= 80]
            return key, (
                f"status={response.status_code} bytes={len(response.content)} "
                f"headings={len(headings)} final={response.url}\n"
                f"  sample={headings[:8]}"
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            error = exc
            time.sleep(0.6 * (attempt + 1))
    return key, f"ERROR {type(error).__name__}: {error}"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check, source): source[0] for source in SOURCES}
        for future in as_completed(futures):
            key, result = future.result()
            results[key] = result

    for key, _ in SOURCES:
        print(f"[{key}] {results[key]}", flush=True)


if __name__ == "__main__":
    main()
