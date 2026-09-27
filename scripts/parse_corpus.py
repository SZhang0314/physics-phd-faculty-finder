"""Parse saved official directory text into a normalized faculty dataset.

The source files are line-preserving outputs from the web research tool. This
parser intentionally keeps conservative records: a candidate must be followed
by an academic title or a recognizable physics research area.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "research" / "sources"


SCHOOL_SOURCES = {
    "mit": "https://physics.mit.edu/faculty/",
    "stanford": "https://physics.stanford.edu/people/faculty",
    "harvard": "https://www.physics.harvard.edu/people/faculty",
    "caltech": "https://www.pma.caltech.edu/people?cat_one=all&cat_two=Physics",
    "upenn": "https://www.physics.upenn.edu/people/standing-faculty",
    "cornell": "https://physics.cornell.edu/faculty",
    "yale": "https://physics.yale.edu/people/faculty/primary-faculty",
    "jhu": "https://physics-astronomy.jhu.edu/people/",
    "berkeley": "https://physics.berkeley.edu/directory?role%5B%5D=11",
    "uchicago": "https://physics.uchicago.edu/people/",
    "princeton": "https://phy.princeton.edu/people/faculty",
    "columbia": "https://www.physics.columbia.edu/content/faculty",
    "northwestern": "https://physics.northwestern.edu/people/faculty/core-faculty/",
    "ucla": "https://hepconf.physics.ucla.edu/home2/faculty.html",
    "michigan": "https://lsa.umich.edu/physics/people/faculty.directory.html",
    "cmu": "https://www.cmu.edu/physics/people/faculty/index.html",
    "nyu": "https://physics.nyu.edu/people/faculty.html",
    "brown": "https://physics.brown.edu/about/people/faculty",
    "duke": "https://physics.duke.edu/people/other-faculty/primary-and-joint-faculty",
    "utaustin": "https://physics.utexas.edu/directory",
    "uiuc": "https://physics.illinois.edu/people/directory/faculty",
    "ucsd": "https://catalog.ucsd.edu/faculty/PHYS.html",
    "pennstate": "https://science.psu.edu/people?department=16&person_type=Faculty",
    "washington": "https://phys.washington.edu/people/faculty",
    "bu": "https://www.bu.edu/physics/people/faculty-lecturers/",
    "purdue": "https://www.physics.purdue.edu/people/faculty/",
    "rice": "https://ga.rice.edu/programs-study/departments-programs/natural-sciences/physics-astronomy/",
    "wisconsin": "https://www.physics.wisc.edu/people/faculty/",
    "ucdavis": "https://physics.ucdavis.edu/people/faculty",
    "gatech": "https://physics.gatech.edu/people/directory/1000?rid=4",
}


AREA_RULES = [
    (
        "天体物理与宇宙学",
        r"astrophys|astronom|cosmolog|galax|stellar|planet|black hole|cosmic microwave|\bcmb\b|gravitational wave",
    ),
    (
        "原子分子光学与量子信息",
        r"atomic|molecular|optical|\bamo\b|ultracold|cold atom|quantum information|quantum optics|quantum computing|quantum simulation",
    ),
    (
        "凝聚态与量子材料",
        r"condensed|materials?|superconduct|topolog|magnet|solid state|quantum matter|semiconductor|nanophoton|spintron|strongly correlated",
    ),
    (
        "粒子、核与高能物理",
        r"particle|high[- ]energy|nuclear|neutrino|standard model|string theory|field theory|collider|\bqcd\b|higgs|dark matter",
    ),
    (
        "生物、软物质与复杂系统",
        r"biophys|biological|soft matter|active matter|complex system|nonlinear|fluid|living system|statistical physics",
    ),
    (
        "等离子体、聚变与加速器",
        r"plasma|fusion|accelerator|beam physics",
    ),
    (
        "引力与数学物理",
        r"general relativity|quantum gravity|gravitation|mathematical physics",
    ),
    (
        "物理教育",
        r"physics education|pedagog|learning",
    ),
]


TITLE_RE = re.compile(
    r"professor|faculty|research scientist|researcher|investigator|department chair|director",
    re.I,
)
EXCLUDE_TITLE_RE = re.compile(
    r"emerit|in memoriam|lecturer|preceptor|teaching professor|professor of practice|visiting|adjunct",
    re.I,
)
AREA_RE = re.compile("|".join(pattern for _, pattern in AREA_RULES), re.I)
LINK_RE = re.compile(r"cite\d+†(.*?)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
STRICT_TITLE_RE = re.compile(r"professor|research scientist|distinguished scientist|investigator", re.I)


def split_source_lines(text: str) -> list[tuple[int, str, list[str]]]:
    matches = list(re.finditer(r"(?:^|\s)L(\d+)(?:@P[\d-]+)?:\s*", text, re.M))
    output: list[tuple[int, str, list[str]]] = []
    if not matches:
        for index, raw in enumerate(text.splitlines()):
            labels = LINK_RE.findall(raw)
            clean = LINK_RE.sub(lambda item: item.group(1), raw)
            clean = re.sub(r"\[(?:Input|Button).*?\]", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            output.append((index, clean, labels))
        return output
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw = text[start:end].strip()
        labels = LINK_RE.findall(raw)
        clean = LINK_RE.sub(lambda item: item.group(1), raw)
        clean = re.sub(r"\[(?:Input|Button).*?\]", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        output.append((int(match.group(1)), clean, labels))
    return output


def simplify_name(label: str) -> str:
    value = re.sub(r"^(?:Image|Photo|Headshot)(?::| of)?\s*", "", label, flags=re.I)
    value = re.sub(r"\s+(?:headshot|portrait|profile|photo)$", "", value, flags=re.I)
    value = re.sub(
        r"^(?:Director,?\s+)?(?:Distinguished\s+|Centennial\s+|Associate\s+|Assistant\s+)?Professor(?:\s+Emeritus)?\s+",
        "",
        value,
        flags=re.I,
    )
    if value.lower().startswith("lecturer in discipline"):
        value = re.sub(r"^.*?(?=[A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z'-]+$)", "", value)
    # Columbia labels sometimes repeat the name before the role, e.g.
    # "Elena Aprile Centennial Professor Elena Aprile".
    parts = re.split(r"(?:Centennial|Associate|Assistant|Distinguished|Pupin|Higgins|Ephraim|Professor)\s+", value)
    if len(parts) > 1 and 1 < len(parts[-1].split()) <= 6:
        value = parts[-1]
    value = re.sub(r"\s+", " ", value).strip(" -,:;")
    if value.count(",") == 1:
        last, first = [part.strip() for part in value.split(",", 1)]
        if last and first and len((first + " " + last).split()) <= 7:
            value = f"{first} {last}"
    return value


def looks_like_name(value: str) -> bool:
    if not 2 <= len(value.split()) <= 7:
        return False
    if len(value) > 70 or any(char.isdigit() for char in value):
        return False
    blocked = re.compile(
        r"department|faculty|professors?|professionals?|academic|postdoctoral|emeriti|students?|research|people|physics|program|center|laborator|university|school|directory|website|group|area|admission|graduate|undergraduate|contact|news|event|office|science|community|culture|degrees?|courses?|curricula|filters?|\bhome\b|\bchair\b",
        re.I,
    )
    if blocked.search(value):
        return False
    alpha = sum(char.isalpha() for char in value)
    return alpha >= max(4, len(value) // 2)


def classify_area(text: str) -> str:
    scores: list[tuple[int, int, str]] = []
    lowered = text.lower()
    for index, (name, pattern) in enumerate(AREA_RULES):
        score = len(re.findall(pattern, lowered, flags=re.I))
        scores.append((score, -index, name))
    score, _, name = max(scores)
    return name if score else "跨学科与其他"


def classify_mode(text: str) -> str:
    has_exp = bool(re.search(r"experiment|observ|instrument|measurement|fabricat|spectroscop", text, re.I))
    has_theory = bool(re.search(r"theor|comput|mathematical|simulation|phenomenolog", text, re.I))
    if has_exp and has_theory:
        return "实验 / 理论"
    if has_exp:
        return "实验 / 观测"
    if has_theory:
        return "理论 / 计算"
    return "综合 / 待官网核实"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value


def inferred_profile_url(school: str, name: str, fallback: str) -> str:
    slug = slugify(name)
    patterns = {
        "mit": f"https://physics.mit.edu/faculty/{slug}/",
        "stanford": f"https://physics.stanford.edu/people/{slug}",
        "caltech": f"https://www.pma.caltech.edu/people/{slug}",
        "cornell": f"https://physics.cornell.edu/{slug}",
        "yale": f"https://physics.yale.edu/profile/{slug}",
        "jhu": f"https://physics-astronomy.jhu.edu/directory/{slug}/",
        "berkeley": f"https://physics.berkeley.edu/people/faculty/{slug}",
        "uchicago": f"https://physics.uchicago.edu/people/profile/{slug}/",
        "princeton": f"https://phy.princeton.edu/people/{slug}",
        "northwestern": f"https://physics.northwestern.edu/people/faculty/core-faculty/{slug}.html",
        "cmu": f"https://www.cmu.edu/physics/people/faculty/{slug.split('-')[-1]}.html",
        "brown": f"https://physics.brown.edu/people/{slug}",
        "washington": f"https://phys.washington.edu/people/{slug}",
        "bu": f"https://www.bu.edu/physics/profile/{slug}/",
        "ucdavis": f"https://physics.ucdavis.edu/people/faculty/{slug}",
    }
    return patterns.get(school, fallback)


def find_title_and_block(
    lines: list[tuple[int, str, list[str]]], start: int
) -> tuple[str, list[str]] | None:
    block: list[str] = []
    title = ""
    for offset in range(1, 9):
        if start + offset >= len(lines):
            break
        _, content, labels = lines[start + offset]
        if not content:
            continue
        label_names = [simplify_name(label) for label in labels]
        if offset > 1 and any(looks_like_name(name) for name in label_names):
            break
        if not title and TITLE_RE.search(content):
            title = content[:180]
        block.append(content)
    if not title:
        return None
    return title, block


def build_record(
    school: str, name: str, title: str, block: list[str], profile: str | None = None
) -> dict[str, str]:
    raw = " ".join(block)
    area = classify_area(raw)
    return {
        "name": name,
        "title": title,
        "area": area,
        "mode": classify_mode(raw),
        "summary": choose_summary(name, title, block, area),
        "profile": profile or inferred_profile_url(school, name, SCHOOL_SOURCES[school]),
        "source": SCHOOL_SOURCES[school],
    }


def add_record(records: list[dict[str, str]], seen: set[str], record: dict[str, str]) -> None:
    key = re.sub(r"\W+", "", record["name"], flags=re.UNICODE).lower()
    if key and key not in seen:
        records.append(record)
        seen.add(key)


def parse_heading_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    """Parse directories whose people are emitted as Markdown headings."""
    for index, (_, content, labels) in enumerate(lines):
        match = HEADING_RE.match(content)
        if not match:
            continue
        name = simplify_name(LINK_RE.sub(lambda item: item.group(1), match.group(1)))
        if not looks_like_name(name):
            continue
        block: list[str] = []
        for _, item, _ in lines[index + 1 : index + 13]:
            if HEADING_RE.match(item):
                break
            if item:
                block.append(item)
        title = next((item for item in block if TITLE_RE.search(item)), "")
        if not title or EXCLUDE_TITLE_RE.search(" ".join(block)):
            continue
        add_record(records, seen, build_record(school, name, title[:180], block))


def parse_inline_labeled_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    """Parse table rows where the linked name and title share one source line."""
    for _, content, labels in lines:
        if len(labels) != 1:
            continue
        name = simplify_name(labels[0])
        if not looks_like_name(name) or not content.startswith(name):
            continue
        remainder = content[len(name) :].strip(" *|-:")
        if not STRICT_TITLE_RE.search(remainder) or EXCLUDE_TITLE_RE.search(remainder):
            continue
        title = re.split(r"\s{2,}|\s+\(?\d{3}\)?[- )]", remainder, maxsplit=1)[0]
        title = re.split(r"\s+[\w.+-]+@[\w.-]+", title, maxsplit=1)[0]
        add_record(records, seen, build_record(school, name, title[:180], [remainder]))


def parse_uchicago_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    """Decode UChicago link labels formatted as 'formal name display name role'."""
    if school != "uchicago":
        return
    role_re = re.compile(
        r"\b((?:(?:University|Assistant|Associate|Research|Part-time)\s+)?Professor(?:\s+Emeritus)?|CASE Senior Scientist|Research Scientist)$",
        re.I,
    )
    for _, _, labels in lines:
        for label in labels:
            match = role_re.search(label.strip())
            if not match or EXCLUDE_TITLE_RE.search(match.group(1)):
                continue
            prefix = label[: match.start()].strip()
            tokens = prefix.split()
            if len(tokens) < 4:
                continue
            last = tokens[-1].strip(".,").casefold()
            first_last_index = next(
                (index for index, token in enumerate(tokens[:-1]) if token.strip(".,").casefold() == last),
                -1,
            )
            if first_last_index < 1:
                continue
            name = " ".join(tokens[: first_last_index + 1])
            if not looks_like_name(name):
                continue
            add_record(records, seen, build_record(school, name, match.group(1), [match.group(1)]))


def parse_catalog_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    """Parse official catalogs that list names under professor rank headings."""
    current_title = ""
    rank_map = {
        "professors": "Professor",
        "associate professors": "Associate Professor",
        "assistant professors": "Assistant Professor",
    }
    for _, content, _ in lines:
        heading = HEADING_RE.match(content)
        if heading:
            current_title = rank_map.get(heading.group(1).strip().lower(), "")
            continue
        if not current_title or ", phd" not in content.lower():
            continue
        if re.search(r"emerit", content, re.I):
            continue
        name = re.sub(r",\s*PhD.*$", "", content, flags=re.I).strip()
        if not looks_like_name(name):
            continue
        block = [content]
        add_record(records, seen, build_record(school, name, current_title, block))


def parse_ranked_plain_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    """Parse catalogs whose rank sections contain one unadorned name per line."""
    current_title = ""
    rank_map = {
        "professors": "Professor",
        "associate professors": "Associate Professor",
        "assistant professors": "Assistant Professor",
        "research professor": "Research Professor",
        "assistant research professors": "Assistant Research Professor",
    }
    for _, content, _ in lines:
        heading = HEADING_RE.match(content)
        if heading:
            current_title = rank_map.get(heading.group(1).strip().lower(), "")
            continue
        if (
            not current_title
            or not looks_like_name(content)
            or TITLE_RE.search(content)
            or re.search(r",\s*PhD", content, re.I)
        ):
            continue
        add_record(records, seen, build_record(school, content, current_title, [content]))


def parse_nyu_bulletin_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    if school != "nyu":
        return
    for index, (_, content, _) in enumerate(lines):
        if "Physics Department, Faculty of Arts and Science" not in content or index < 2:
            continue
        name = re.sub(r"#+$", "", lines[index - 2][1]).strip()
        title = lines[index - 1][1].strip()
        if not looks_like_name(name) or not TITLE_RE.search(title) or EXCLUDE_TITLE_RE.search(title):
            continue
        add_record(records, seen, build_record(school, name, title, [title, content]))


def parse_sequential_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    """Parse card streams where a plain name is followed by title and interests."""
    if school not in {"pennstate"}:
        return
    for index, (_, content, _) in enumerate(lines):
        name = simplify_name(content)
        if not looks_like_name(name):
            continue
        block: list[str] = []
        for _, item, _ in lines[index + 1 : index + 14]:
            if item:
                block.append(item)
        if not block:
            continue
        title = block[0]
        if not STRICT_TITLE_RE.search(title) or EXCLUDE_TITLE_RE.search(title):
            continue
        add_record(records, seen, build_record(school, name, title[:180], block))


def parse_utaustin_handbook_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    if school != "utaustin":
        return
    starts: list[int] = []
    entry_re = re.compile(r"^([^,]+),\s+(.+?),\s+(?:Ph\.D\.|D\.Sc\.)", re.I)
    for index, (_, content, _) in enumerate(lines):
        if entry_re.match(content):
            starts.append(index)
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else min(len(lines), start + 16)
        block = [item for _, item, _ in lines[start:end] if item]
        raw = " ".join(block)
        match = entry_re.match(block[0]) if block else None
        if not match:
            continue
        name = f"{match.group(2).strip()} {match.group(1).strip()}"
        title_match = re.search(
            r"((?:Assistant|Associate|Research|Distinguished)?\s*Professor of Physics(?:\s*&\s*[A-Za-z ]+)?)",
            raw,
            re.I,
        )
        if not title_match or EXCLUDE_TITLE_RE.search(raw):
            continue
        title = title_match.group(1).strip()
        add_record(records, seen, build_record(school, name, title, block))


def parse_purdue_research_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    if school != "purdue":
        return
    current_area = ""
    in_faculty = False
    for _, content, labels in lines:
        if content.startswith("## ") and not content.startswith("### "):
            current_area = content.removeprefix("## ").strip()
            in_faculty = False
            continue
        if content.startswith("### Faculty Specializing"):
            in_faculty = True
            continue
        if content.startswith("### Research Groups"):
            in_faculty = False
            continue
        if not in_faculty or not current_area:
            continue
        candidates = labels[:1]
        if not candidates and re.match(r"^\s*\*\s+", content):
            candidates = [re.sub(r"^\s*\*\s+", "", content).split("(", 1)[0].strip()]
        for label in candidates:
            name = simplify_name(label)
            if not looks_like_name(name):
                continue
            area = classify_area(current_area)
            record = build_record(
                school,
                name,
                "Faculty / research-area roster",
                [current_area],
            )
            record["area"] = area
            record["summary"] = f"Purdue 官方研究领域页将其列入“{current_area}”方向；近期成果与招生信息请进入官方名录或个人主页核实。"
            add_record(records, seen, record)


def parse_wisconsin_research_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    if school != "wisconsin":
        return
    current_area = ""
    for _, content, _ in lines:
        if content.startswith("## ") and not content.startswith("### "):
            current_area = content.removeprefix("## ").strip()
            continue
        if content.startswith("### ") and "|" in content and current_area:
            left, topic = [item.strip() for item in content.removeprefix("### ").split("|", 1)]
            if not topic or re.search(r"homepage|group page|directory", left, re.I):
                continue
            names = [item.strip() for item in left.split(",")]
            for name in names:
                name = simplify_name(name)
                if not looks_like_name(name):
                    continue
                record = build_record(school, name, "Faculty / research profile", [current_area, topic])
                record["area"] = classify_area(current_area + " " + topic)
                record["summary"] = f"官网研究页：{topic.rstrip('.')}。"
                add_record(records, seen, record)
            continue
        affiliate = re.match(r"^\s*\*\s+([^|]+)\|\s*([^|]+)\|\s*(.+)$", content)
        if affiliate and current_area.lower().startswith("affiliate"):
            name = simplify_name(affiliate.group(1))
            topic = affiliate.group(3).strip()
            if looks_like_name(name):
                record = build_record(school, name, "Affiliated Faculty", [topic])
                record["summary"] = f"官网研究页：{topic.rstrip('.')}。"
                add_record(records, seen, record)


def parse_table_records(
    school: str, lines: list[tuple[int, str, list[str]]], records: list[dict[str, str]], seen: set[str]
) -> None:
    """Parse line-preserving Markdown tables such as Berkeley's directory."""
    for _, content, labels in lines:
        if content.count("|") < 3 or not labels:
            continue
        columns = [item.strip() for item in content.split("|")]
        name = simplify_name(labels[0])
        title = columns[1] if len(columns) > 1 else ""
        if not looks_like_name(name) or not TITLE_RE.search(title) or EXCLUDE_TITLE_RE.search(title):
            continue
        interests = columns[-1] if columns else ""
        add_record(records, seen, build_record(school, name, title[:180], [title, interests]))


def choose_summary(name: str, title: str, block: list[str], area: str) -> str:
    for item in block:
        candidate = re.sub(r"^#+\s*", "", item).strip()
        if candidate == title or len(candidate) < 55:
            continue
        if re.search(r"email|phone|address|office|website|education|ph\.d", candidate, re.I):
            continue
        if re.search(r"research|study|focus|interest|explor|develop|experiment|theor|observ", candidate, re.I):
            return candidate[:300].rstrip(" ,;:")
    area_terms = [
        re.sub(r"^#+\s*", "", item).strip()
        for item in block
        if AREA_RE.search(item) and len(item) < 180
    ]
    if area_terms:
        return f"官网列出的研究主题包括：{'; '.join(area_terms[:2])}。"
    return f"{name} 的公开名录将其归入“{area}”；具体课题、近期论文与招生状态请进入官方页面核实。"


def parse_school(school: str, text: str) -> list[dict[str, str]]:
    lines = split_source_lines(text)
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    parse_inline_labeled_records(school, lines, records, seen)
    parse_uchicago_records(school, lines, records, seen)
    for index, (_, _, labels) in enumerate(lines):
        if school == "uchicago":
            continue
        if not labels:
            continue
        for label in labels:
            if re.match(r"^(?:Image|Photo|Headshot)", label, re.I):
                # Some Columbia records encode role and name in an image alt.
                if school != "columbia":
                    continue
            name = simplify_name(label)
            if not looks_like_name(name):
                continue
            found = find_title_and_block(lines, index)
            if not found:
                continue
            title, block = found
            if EXCLUDE_TITLE_RE.search(title):
                continue
            context = [item for _, item, _ in lines[max(0, index - 10) : index] if item]
            add_record(records, seen, build_record(school, name, title, context + block))
            break
    parse_heading_records(school, lines, records, seen)
    parse_catalog_records(school, lines, records, seen)
    parse_ranked_plain_records(school, lines, records, seen)
    parse_nyu_bulletin_records(school, lines, records, seen)
    parse_sequential_records(school, lines, records, seen)
    parse_utaustin_handbook_records(school, lines, records, seen)
    parse_purdue_research_records(school, lines, records, seen)
    parse_wisconsin_research_records(school, lines, records, seen)
    parse_table_records(school, lines, records, seen)
    records.sort(key=lambda item: item["name"].casefold())
    return records


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result: dict[str, list[dict[str, str]]] = {}
    for school in SCHOOL_SOURCES:
        merged: dict[str, dict[str, str]] = {}
        for path in sorted(SOURCE_DIR.glob(f"{school}*.txt")):
            for record in parse_school(school, path.read_text(encoding="utf-8")):
                key = re.sub(r"\W+", "", record["name"], flags=re.UNICODE).lower()
                current = merged.get(key)
                if current is None:
                    merged[key] = record
                    continue
                if current["area"] == "跨学科与其他" and record["area"] != "跨学科与其他":
                    current["area"] = record["area"]
                    current["mode"] = record["mode"]
                    current["summary"] = record["summary"]
                if current["profile"] == SCHOOL_SOURCES[school] and record["profile"] != SCHOOL_SOURCES[school]:
                    current["profile"] = record["profile"]
        result[school] = sorted(merged.values(), key=lambda item: item["name"].casefold())

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    for school, records in result.items():
        areas: dict[str, int] = {}
        for record in records:
            areas[record["area"]] = areas.get(record["area"], 0) + 1
        print(f"{school:13} {len(records):3} {areas}")


if __name__ == "__main__":
    main()
