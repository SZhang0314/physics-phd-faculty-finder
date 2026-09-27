"""Print a compact DOM neighborhood around a known faculty name."""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from check_sources import HEADERS, SOURCES


def compact(value: str, limit: int = 900) -> str:
    value = " ".join(value.split())
    return value[:limit] + ("…" if len(value) > limit else "")


def inspect(key: str, needle: str) -> str:
    source_map = dict(SOURCES)
    last_error = None
    response = None
    for attempt in range(4):
        try:
            response = requests.get(
                source_map[key],
                headers={**HEADERS, "Connection": "close"},
                timeout=30,
                verify=False,
            )
            break
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            last_error = exc
            time.sleep(attempt + 1)
    if response is None:
        raise last_error  # type: ignore[misc]
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    hits = soup.find_all(string=lambda text: text and needle.lower() in text.lower())
    lines = [f"[{key}] hits={len(hits)} status={response.status_code} url={response.url}"]
    for index, hit in enumerate(hits[:3], start=1):
        node = hit.parent
        lines.append(
            f"\nHIT {index}: <{node.name} class={node.get('class')}> "
            f"{compact(node.get_text(' ', strip=True))}"
        )
        for level in range(1, 6):
            node = node.parent
            if node is None:
                break
            lines.append(
                f"  L{level}: <{node.name} class={node.get('class')} id={node.get('id')}> "
                f"{compact(node.get_text(' ', strip=True))}"
            )
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("key", nargs="?")
    parser.add_argument("needle", nargs="?")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    samples = {
        "stanford": "Tom Abel",
        "caltech": "Rana X. Adhikari",
        "upenn": "James Aguirre",
        "yale": "Yoram Alhassid",
        "berkeley": "Mina Aganagic",
        "cmu": "John Alison",
        "brown": "Vesna Mitrović",
        "duke": "Ayana T. Arce",
        "utaustin": "Allan MacDonald",
        "pennstate": "Zhen Bi",
        "washington": "Anton Andreev",
        "bu": "David Bishop",
        "purdue": "Tongcang Li",
        "rice": "Darin Acosta",
        "wisconsin": "Yang Bai",
        "gatech": "David Ballantyne",
    }

    if args.all:
        outputs: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(inspect, key, needle): key
                for key, needle in samples.items()
            }
            for future in as_completed(futures):
                key = futures[future]
                try:
                    outputs[key] = future.result()
                except Exception as exc:  # noqa: BLE001 - diagnostic script
                    outputs[key] = f"[{key}] ERROR {type(exc).__name__}: {exc}"
        for key in samples:
            print(outputs[key], "\n", flush=True)
        return

    if not args.key or not args.needle:
        parser.error("provide KEY NEEDLE or use --all")
    print(inspect(args.key, args.needle))


if __name__ == "__main__":
    main()
