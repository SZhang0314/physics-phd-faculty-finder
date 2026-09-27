"""Build the static, school-first Physics PhD faculty directory."""

from __future__ import annotations

import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "research" / "parsed.json"
ENRICHMENT = ROOT / "research" / "public_enrichment.json"
CHECKED = "2026-09-27"
SITE_URL = "https://szhang0314.github.io/physics-phd-faculty-finder"


SCHOOLS = [
    ("mit", "Massachusetts Institute of Technology", "MIT", "1", ["量子信息", "凝聚态", "粒子与宇宙"], [
        ("MIT Kavli Institute", "https://mki.mit.edu/", "天体物理与空间研究"),
        ("Center for Theoretical Physics", "https://ctp.mit.edu/", "粒子、核与量子理论"),
        ("Plasma Science and Fusion Center", "https://www.psfc.mit.edu/", "等离子体与聚变"),
    ]),
    ("stanford", "Stanford University", "Stanford", "=2", ["量子科学", "天体粒子", "材料物理"], [
        ("KIPAC", "https://kipac.stanford.edu/", "粒子天体物理与宇宙学"),
        ("Q-FARM", "https://qfarm.stanford.edu/", "量子基础、架构与器件"),
        ("GLAM", "https://glam.stanford.edu/", "材料与凝聚态研究"),
    ]),
    ("harvard", "Harvard University", "Harvard", "5", ["量子光学", "软物质", "高能与宇宙"], [
        ("Harvard Quantum Initiative", "https://quantum.harvard.edu/", "量子科学与工程"),
        ("Black Hole Initiative", "https://bhi.fas.harvard.edu/", "黑洞跨学科研究"),
        ("ITAMP", "https://itamp.harvard.edu/", "理论原子、分子与光学物理"),
    ]),
    ("caltech", "California Institute of Technology", "Caltech", "7", ["量子信息", "引力波", "高能理论"], [
        ("LIGO Laboratory", "https://www.ligo.caltech.edu/", "引力波探测"),
        ("IQIM", "https://iqim.caltech.edu/", "量子信息与物质"),
        ("Burke Institute", "https://burkeinstitute.caltech.edu/", "理论物理与天体物理"),
    ]),
    ("upenn", "University of Pennsylvania", "Penn", "15", ["量子材料", "宇宙学", "生物物理"], [
        ("LRSM", "https://www.lrsm.upenn.edu/", "材料结构与量子材料"),
        ("Penn Quantum Hardware Lab", "https://quantum.upenn.edu/", "量子科学与工程生态"),
        ("Singh Center for Nanotechnology", "https://www.nano.upenn.edu/", "纳米制造与表征"),
    ]),
    ("cornell", "Cornell University", "Cornell", "=16", ["凝聚态", "加速器", "天体与粒子"], [
        ("LASSP", "https://www.lassp.cornell.edu/", "固体与原子尺度物理"),
        ("CLASSE", "https://www.classe.cornell.edu/", "加速器科学与同步辐射"),
        ("LEPP", "https://www.lepp.cornell.edu/", "基本粒子物理"),
    ]),
    ("yale", "Yale University", "Yale", "=16", ["量子器件", "核与粒子", "宇宙学"], [
        ("Yale Quantum Institute", "https://quantuminstitute.yale.edu/", "量子信息与器件"),
        ("Wright Laboratory", "https://wlab.yale.edu/", "核、粒子与天体物理"),
        ("Yale Center for Astronomy & Astrophysics", "https://ycaa.yale.edu/", "天文与宇宙学"),
    ]),
    ("jhu", "Johns Hopkins University", "Johns Hopkins", "=20", ["宇宙学", "量子材料", "粒子理论"], [
        ("Center for Astrophysical Sciences", "https://cas.jhu.edu/", "天体物理与宇宙学"),
        ("Institute for Quantum Matter", "https://iqm.jhu.edu/", "量子材料"),
        ("Center for Quantum Information", "https://quantum.jhu.edu/", "量子信息研究"),
    ]),
    ("berkeley", "University of California, Berkeley", "UC Berkeley", "=20", ["量子科学", "高能物理", "凝聚态"], [
        ("Berkeley Quantum", "https://quantum.berkeley.edu/", "量子信息、材料与技术"),
        ("Berkeley Center for Theoretical Physics", "https://bctp.berkeley.edu/", "高能与宇宙理论"),
        ("Lawrence Berkeley National Laboratory", "https://www.lbl.gov/", "大型设施与跨学科物理"),
    ]),
    ("uchicago", "University of Chicago", "UChicago", "24", ["量子工程", "宇宙学", "软物质"], [
        ("Kavli Institute for Cosmological Physics", "https://kicp.uchicago.edu/", "宇宙学与天体粒子"),
        ("Enrico Fermi Institute", "https://efi.uchicago.edu/", "粒子、核与天体物理"),
        ("James Franck Institute", "https://jfi.uchicago.edu/", "凝聚态、AMO 与软物质"),
    ]),
    ("princeton", "Princeton University", "Princeton", "27", ["高能理论", "量子材料", "引力与宇宙"], [
        ("Princeton Center for Theoretical Science", "https://pcts.princeton.edu/", "跨领域理论科学"),
        ("Princeton Quantum Initiative", "https://quantum.princeton.edu/", "量子科学与工程"),
        ("Princeton Gravity Initiative", "https://gravity.princeton.edu/", "引力与相对论"),
    ]),
    ("columbia", "Columbia University", "Columbia", "=43", ["粒子与核", "量子材料", "宇宙学"], [
        ("Nevis Laboratories", "https://www.nevis.columbia.edu/", "粒子、核与天体物理"),
        ("Columbia Quantum Initiative", "https://quantum.columbia.edu/", "量子科学与技术"),
        ("Columbia Nano Initiative", "https://cni.columbia.edu/", "纳米科学与器件"),
    ]),
    ("northwestern", "Northwestern University", "Northwestern", "=45", ["天体与引力波", "量子器件", "软物质"], [
        ("CIERA", "https://ciera.northwestern.edu/", "天体物理跨学科研究"),
        ("CAPST", "https://capst.northwestern.edu/", "基础物理与宇宙研究"),
        ("NU Quantum", "https://quantum.northwestern.edu/", "量子信息与材料"),
    ]),
    ("ucla", "University of California, Los Angeles", "UCLA", "49", ["等离子体", "粒子物理", "天体与量子材料"], [
        ("Bhaumik Institute", "https://bhaumik-institute.physics.ucla.edu/", "理论物理"),
        ("Galactic Center Group", "https://www.galacticcenter.astro.ucla.edu/", "银河系中心与黑洞"),
        ("Basic Plasma Science Facility", "https://plasma.physics.ucla.edu/", "基础等离子体实验"),
    ]),
    ("michigan", "University of Michigan–Ann Arbor", "Michigan", "51", ["量子科学", "高能实验", "生物物理"], [
        ("Leinweber Center for Theoretical Physics", "https://lsa.umich.edu/lctp", "理论物理"),
        ("Michigan Quantum Research", "https://quantum.umich.edu/", "量子科学与工程"),
        ("Physics Research Areas", "https://lsa.umich.edu/physics/research.html", "院系研究方向入口"),
    ]),
    ("cmu", "Carnegie Mellon University", "Carnegie Mellon", "55", ["宇宙学", "粒子物理", "量子材料"], [
        ("McWilliams Center for Cosmology", "https://www.cmu.edu/cosmology/", "宇宙学与天体物理"),
        ("Pittsburgh Quantum Institute", "https://www.pqi.org/", "区域量子研究联盟"),
        ("CMU Physics Research", "https://www.cmu.edu/physics/research/index.html", "院系研究方向入口"),
    ]),
    ("nyu", "New York University", "NYU", "58", ["软物质", "宇宙与粒子", "量子现象"], [
        ("Center for Cosmology and Particle Physics", "https://cosmo.nyu.edu/", "宇宙学与粒子物理"),
        ("Center for Quantum Phenomena", "https://physics.nyu.edu/cqp/", "凝聚态与量子材料"),
        ("Center for Soft Matter Research", "https://physics.nyu.edu/softmatter/", "软物质与复杂系统"),
    ]),
    ("brown", "Brown University", "Brown", "66", ["高能理论", "凝聚态", "生物物理"], [
        ("Brown Theoretical Physics Center", "https://btpc.brown.edu/", "理论物理"),
        ("Brown Quantum Initiative", "https://quantum.brown.edu/", "量子科学与工程"),
        ("Physics Research", "https://physics.brown.edu/research", "院系研究方向入口"),
    ]),
    ("duke", "Duke University", "Duke", "70", ["量子信息", "核物理", "软物质"], [
        ("Duke Quantum Center", "https://quantum.duke.edu/", "量子计算与系统"),
        ("Triangle Universities Nuclear Laboratory", "https://tunl.duke.edu/", "低能核物理"),
        ("Center for Nonlinear and Complex Systems", "https://cncs.duke.edu/", "非线性与复杂系统"),
    ]),
    ("utaustin", "University of Texas at Austin", "UT Austin", "72", ["凝聚态", "高能理论", "等离子体"], [
        ("Weinberg Institute", "https://weinberg.utexas.edu/", "理论物理"),
        ("Texas Quantum Institute", "https://quantum.utexas.edu/", "量子科学与技术"),
        ("Institute for Fusion Studies", "https://ifs.utexas.edu/", "聚变与等离子体理论"),
    ]),
    ("uiuc", "University of Illinois Urbana-Champaign", "UIUC", "74", ["量子信息", "凝聚态", "高能物理"], [
        ("IQUIST", "https://iquist.illinois.edu/", "量子信息科学与技术"),
        ("Materials Research Laboratory", "https://mrl.illinois.edu/", "材料研究与表征"),
        ("Illinois Physics Research", "https://physics.illinois.edu/research", "院系研究方向入口"),
    ]),
    ("ucsd", "University of California, San Diego", "UC San Diego", "81", ["量子材料", "等离子体", "粒子与宇宙"], [
        ("Q-MEEN-C", "https://q-meen-c.ucsd.edu/", "量子材料与能源"),
        ("CASS", "https://cass.ucsd.edu/", "天体物理与空间科学"),
        ("UCSD Physics Research", "https://physics.ucsd.edu/research", "院系研究方向入口"),
    ]),
    ("pennstate", "Pennsylvania State University", "Penn State", "=92", ["引力与宇宙", "量子材料", "粒子物理"], [
        ("Institute for Gravitation and the Cosmos", "https://igc.psu.edu/", "引力、宇宙与基本物理"),
        ("Materials Research Institute", "https://www.mri.psu.edu/", "材料与量子物质"),
        ("2D Crystal Consortium", "https://www.mri.psu.edu/2d-crystal-consortium", "二维晶体材料"),
    ]),
    ("washington", "University of Washington", "Washington", "=92", ["核理论", "粒子实验", "量子物质"], [
        ("Institute for Nuclear Theory", "https://www.int.washington.edu/", "核理论"),
        ("CENPA", "https://cenpa.washington.edu/", "核与粒子天体物理"),
        ("QuantumX", "https://quantumx.washington.edu/", "量子科学跨学科平台"),
    ]),
    ("bu", "Boston University", "Boston University", "94", ["空间物理", "粒子实验", "凝聚态"], [
        ("Photonics Center", "https://www.bu.edu/photonics/", "光子学与器件"),
        ("Center for Space Physics", "https://www.bu.edu/csp/", "日地与空间物理"),
        ("BU Physics Research", "https://www.bu.edu/physics/research/", "院系研究方向入口"),
    ]),
    ("purdue", "Purdue University", "Purdue", "=100", ["量子科学", "粒子与核", "天体物理"], [
        ("Purdue Quantum Science and Engineering Institute", "https://www.purdue.edu/discoverypark/quantum/", "量子科学与工程"),
        ("PRIME Lab", "https://www.purdue.edu/prime-lab/", "加速器质谱"),
        ("Birck Nanotechnology Center", "https://www.purdue.edu/birck/", "纳米器件与材料"),
    ]),
    ("rice", "Rice University", "Rice", "122", ["量子模拟", "天体物理", "软物质"], [
        ("Smalley–Curl Institute", "https://sci.rice.edu/", "量子、材料与分子科学"),
        ("Rice Quantum Initiative", "https://quantum.rice.edu/", "量子信息与技术"),
        ("Rice Space Institute", "https://rsi.rice.edu/", "空间与天体物理"),
    ]),
    ("wisconsin", "University of Wisconsin–Madison", "Wisconsin", "=131", ["量子信息", "粒子天体", "等离子体"], [
        ("Wisconsin Quantum Institute", "https://quantum.wisc.edu/", "量子科学与工程"),
        ("WIPAC", "https://wipac.wisc.edu/", "粒子天体物理"),
        ("Wisconsin Plasma Physics", "https://plasma.physics.wisc.edu/", "等离子体与聚变"),
    ]),
    ("ucdavis", "University of California, Davis", "UC Davis", "137", ["宇宙学", "核物理", "凝聚态"], [
        ("Crocker Nuclear Laboratory", "https://cyclotron.crocker.ucdavis.edu/", "核物理与应用"),
        ("UC Davis Cosmology", "https://cosmos.ucdavis.edu/", "宇宙学与天体物理"),
        ("Condensed Matter Experiment", "https://cme.physics.ucdavis.edu/", "凝聚态实验"),
    ]),
    ("gatech", "Georgia Institute of Technology", "Georgia Tech", "=142", ["相对论天体", "软物质", "量子材料"], [
        ("Center for Relativistic Astrophysics", "https://cra.gatech.edu/", "相对论天体物理"),
        ("Georgia Tech Quantum Alliance", "https://quantum.gatech.edu/", "量子科学与工程"),
        ("Soft Matter Incubator", "https://soft-matter.gatech.edu/", "软物质与生物物理"),
    ]),
]


NYU_AREAS = {
    "Andrei Gruzinov": "天体物理与宇宙学", "David W Hogg": "天体物理与宇宙学",
    "Drummond Fielding": "天体物理与宇宙学", "Jeremy Tinker": "天体物理与宇宙学",
    "Michael Blanton": "天体物理与宇宙学", "Roman Scoccimarro": "天体物理与宇宙学",
    "Allen Mincer": "粒子、核与高能物理", "Gaston Enrique Giribet": "引力与数学物理",
    "Gregory Gabadadze": "粒子、核与高能物理", "Joshua Ruderman": "粒子、核与高能物理",
    "Ken Van Tilburg": "粒子、核与高能物理", "Massimo Porrati": "粒子、核与高能物理",
    "Matthew Kleban": "粒子、核与高能物理", "Yifan Wang": "粒子、核与高能物理",
    "Daniel L Stein": "凝聚态与量子材料", "Javad Shabani": "凝聚态与量子材料",
    "Kota Katsumi": "凝聚态与量子材料", "David G Grier": "生物、软物质与复杂系统",
    "David J Pine": "生物、软物质与复杂系统", "Jasna Brujic": "生物、软物质与复杂系统",
    "Katepalli Raju Sreenivasan": "生物、软物质与复杂系统", "Marc H Gershow": "生物、软物质与复杂系统",
    "Paul Chaikin": "生物、软物质与复杂系统",
}


DEPARTMENTS = {
    "mit": "Department of Physics",
    "stanford": "Department of Physics",
    "harvard": "Department of Physics",
    "caltech": "Division of Physics, Mathematics and Astronomy",
    "upenn": "Department of Physics and Astronomy",
    "cornell": "Department of Physics",
    "yale": "Department of Physics",
    "jhu": "Department of Physics and Astronomy",
    "berkeley": "Department of Physics",
    "uchicago": "Department of Physics",
    "princeton": "Department of Physics",
    "columbia": "Department of Physics",
    "northwestern": "Department of Physics and Astronomy",
    "ucla": "Department of Physics and Astronomy",
    "michigan": "Department of Physics",
    "cmu": "Department of Physics",
    "nyu": "Physics Department, Faculty of Arts and Science",
    "brown": "Department of Physics",
    "duke": "Department of Physics",
    "utaustin": "Department of Physics",
    "uiuc": "Department of Physics",
    "ucsd": "Department of Physics",
    "pennstate": "Department of Physics",
    "washington": "Department of Physics",
    "bu": "Department of Physics",
    "purdue": "Department of Physics and Astronomy",
    "rice": "Department of Physics and Astronomy",
    "wisconsin": "Department of Physics",
    "ucdavis": "Department of Physics and Astronomy",
    "gatech": "School of Physics",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def safe_title(value: str) -> str:
    if len(value) > 100 or "@" in value or re.search(r"\b(?:next|home|menu)\b", value, re.I):
        return "教授 / 研究人员"
    return value


JUNK_NAME_RE = re.compile(
    r"(?i)^(?:giving opportunit(?:y|ies)|giving opportunties|pappalardo fellowships|resources overview|our history|"
    r"tax information|job opportunities for physicists|diverse minds seminar series|film and media|"
    r"general resources|career information|careers seminar|alumni resources|purdue resources|employment opportunities|"
    r"resources for visitors|safety resources|skip to main content|important dates and deadlines|"
    r"concurrent enrollment & summer sessions|inaugural hans frauenfelder lecture|"
    r"independent study approval form|thin film fabrication and characterization|"
    r"x-ray imaging and spectroscopy|harvard-mit sps chilloquium|wright lab media|"
    r"molecular & optical atomic|nuclear & particle experiment|positions available|equity & inclusion|"
    r"follow us|quick links|secondary navigation|phd alumni|ladd observatory|our facilities|site navigation|"
    r"superconductivity milestones|campus map|keep in touch|herndon homepage|icecube homepage|"
    r"soares-furtado homepage|string theory|theory and practice|wipac homepage|wippl homepage|catalog navigation)$"
)


TOPIC_PATTERNS = [
    (r"gravitational[- ]wave", "引力波物理与天体物理"),
    (r"black hole", "黑洞物理"),
    (r"compact (?:object|binary|merger)|neutron star|cosmic explosion|transient", "致密天体与瞬变源"),
    (r"large[- ]scale structure", "宇宙大尺度结构"),
    (r"early[- ]universe|cosmic dawn|cosmolog", "宇宙学"),
    (r"galax", "星系形成与演化"),
    (r"stellar|stars?\b", "恒星天体物理"),
    (r"exoplanet|planetary", "系外行星与行星物理"),
    (r"observational astrophysics|radio astronomy|astroinformatics|sky surve", "观测天体物理与巡天"),
    (r"theoretical astrophysics|astroparticle|high[- ]energy astrophysics", "理论与高能天体物理"),
    (r"dark matter", "暗物质"),
    (r"dark energy", "暗能量"),
    (r"neutrino", "中微子物理"),
    (r"heavy[- ]ion|quark.gluon|\bqcd\b", "强相互作用与重离子物理"),
    (r"experimental (?:nuclear|particle|high energy)|collider|higgs", "实验粒子与核物理"),
    (r"theoretical (?:nuclear|particle|high energy)|quantum field theor", "理论粒子与高能物理"),
    (r"nuclear physics|nucleon|hadron", "核物理与强子物理"),
    (r"accelerator", "加速器物理"),
    (r"quantum gravity|holograph|black hole information", "量子引力与全息原理"),
    (r"string theory", "弦理论"),
    (r"quantum information|quantum comput|quantum measurement", "量子信息与计算"),
    (r"atomic,? molecular,? and optical|\bamo\b|atom optics", "原子分子光物理（AMO）"),
    (r"quantum optics|nanophotonic|photonics", "量子光学与光子学"),
    (r"ultracold|cold atoms?", "超冷原子与量子气体"),
    (r"theoretical condensed matter", "理论凝聚态物理"),
    (r"experimental condensed matter", "实验凝聚态物理"),
    (r"quantum material|quantum matter|electronic states? of matter", "量子材料与量子物态"),
    (r"topolog", "拓扑物态与拓扑材料"),
    (r"many[- ]body|strongly (?:interacting|correlated)|electron correlation", "强关联与量子多体物理"),
    (r"superconduct", "超导物理"),
    (r"mesoscopic|semiconductor|two-dimensional|\b2d\b", "介观与低维量子系统"),
    (r"plasma|nuclear fusion|\bfusion\b", "等离子体与聚变物理"),
    (r"biophys|biological", "生物物理"),
    (r"soft matter", "软物质物理"),
    (r"complex systems?|collective behavior|non-equilibrium", "复杂系统与非平衡物理"),
    (r"fluid|hydrodynamic", "流体与流体力学"),
    (r"machine learning|artificial intelligence|data[- ]driven", "机器学习与物理数据方法"),
    (r"instrumentation|detector", "物理仪器与探测技术"),
    (r"physics education|science teaching", "物理教育"),
]


def chinese_summary(item: dict) -> tuple[str, str, str]:
    """Create a cautious Chinese research synopsis and preserve a source excerpt."""
    original = re.sub(r"\s+", " ", item.get("summary", "")).strip()
    area = item.get("area") or "官网未细分 / 跨学科"
    area_label = "官网未细分 / 跨学科" if area == "跨学科与其他" else area

    if "公开名录将其归入" in original or "官方院系与研究中心信息归入" in original:
        return (
            f"{item['name']} 在当前官方目录中归入“{area_label}”方向。公开目录未提供足够详细的个人研究摘要，建议进入官方主页核对近期课题与论文。",
            "",
            "area",
        )

    lowered = original.lower()
    topics: list[str] = []
    for pattern, label in TOPIC_PATTERNS:
        if re.search(pattern, lowered, re.I) and label not in topics:
            topics.append(label)
    if topics:
        synopsis = f"当前来源页提及的研究关键词包括：{' · '.join(topics[:6])}。"
        if len(topics) > 6:
            synopsis += "还涵盖其他交叉方向。"
        excerpt = re.sub(r"^(?:官网列出的研究主题包括：|官网研究页：)", "", original)
        excerpt = re.sub(r"†\S+", "", excerpt).replace("* ", "").strip(" 。;")
        return synopsis, excerpt, "topics"

    if re.search(r"[\u4e00-\u9fff]", original) and not re.search(r"[A-Za-z]{4,}", original):
        return original, "", "translated"

    return (
        f"{item['name']} 在当前目录中归入“{area_label}”方向。来源页暂未提供可稳妥译写的详细研究摘要，请以其个人主页和近期论文为准。",
        original if re.search(r"[A-Za-z]{4,}", original) else "",
        "area",
    )


def faculty_initials(name: str) -> str:
    parts = re.findall(r"[A-Za-zÀ-ɏ]+", re.sub(r"\([^)]*\)", "", name))
    return ((parts[0][0] if parts else "φ") + (parts[-1][0] if len(parts) > 1 else "")).upper()


def area_counts(records: list[dict]) -> Counter:
    return Counter(item["area"] for item in records)


def top_areas(records: list[dict], limit: int = 4) -> list[tuple[str, int]]:
    counts = area_counts(records)
    items = [(area, count) for area, count in counts.most_common() if area != "跨学科与其他"]
    if counts.get("跨学科与其他"):
        items.append(("官网未细分 / 跨学科", counts["跨学科与其他"]))
    return items[:limit]


def page_shell(title: str, description: str, body: str, prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#071f33">
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="{prefix}assets/styles.css">
</head>
<body>
  <a class="skip-link" href="#main">跳到正文</a>
  <header class="site-header"><a class="brand" href="{prefix}index.html"><span class="brand-mark">φ</span><span>Physics PhD Atlas</span></a><a class="method-link" href="{prefix}methodology.html">口径与使用方法</a></header>
  {body}
  <footer><p>用于 PhD 选校与导师初筛 · 数据核验日期 {CHECKED} · 申请与招生状态请以学校官网及导师回复为准</p><p><a href="https://github.com/SZhang0314/physics-phd-faculty-finder">GitHub 源码与数据方法</a></p></footer>
  <script src="{prefix}assets/site.js" defer></script>
</body>
</html>
"""


def school_card(meta: dict, records: list[dict]) -> str:
    areas = top_areas(records, 3)
    area_html = "".join(f'<span class="chip">{esc(a)} · {n}</span>' for a, n in areas)
    lab_html = "".join(f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(name)}</a>' for name, url, _ in meta["labs"][:3])
    search_blob = " ".join([meta["name"], meta["short"], *meta["strengths"], *(a for a, _ in areas)]).lower()
    return f"""<article class="school-card" data-school-card data-search="{esc(search_blob)}" data-rank="{meta['order']}">
      <div class="school-card-head"><span class="rank">QS {esc(meta['rank'])}</span><span class="coverage">高覆盖名录</span></div>
      <h2><a href="schools/{meta['id']}.html">{esc(meta['name'])}</a></h2>
      <p class="school-short">{esc(meta['short'])} · 已收录 <strong>{len(records)}</strong> 名教授/研究人员</p>
      <div class="chips">{area_html}</div>
      <p class="strength-line"><b>突出方向</b>　{esc(' · '.join(meta['strengths']))}</p>
      <div class="lab-links"><b>重点平台</b>{lab_html}</div>
      <a class="card-cta" href="schools/{meta['id']}.html">查看学校详情与完整导师列表 <span>→</span></a>
    </article>"""


def faculty_card(item: dict, school_name: str) -> str:
    name = item["name"]
    area = item["area"]
    summary = item["summary_zh"]
    original_summary = item.get("summary_original", "")
    translation_mode = item.get("summary_translation_mode", "area")
    if area == "跨学科与其他":
        area_label = "官网未细分 / 跨学科"
    else:
        area_label = area
    scholar = f"https://scholar.google.com/scholar?q={quote_plus(name + ' ' + school_name + ' physics')}"
    profile = item.get("profile") or item["source"]
    education = item.get("education") or "未在已查官方页面公开完整学位院校与专业"
    education_source = item.get("education_source")
    education_html = esc(education)
    if education_source:
        education_html += f' <a href="{esc(education_source)}" target="_blank" rel="noopener">来源 ↗</a>'
    phd_history = item.get("phd_recruitment_history", [])
    summer_history = item.get("summer_research_history", [])
    backgrounds = item.get("group_student_backgrounds", [])

    def history_html(rows: list[dict], empty: str) -> str:
        if not rows:
            return esc(empty)
        rendered = []
        for row in rows:
            source_link = f'<a href="{esc(row["source"])}" target="_blank" rel="noopener">来源 ↗</a>' if row.get("source") else ""
            scope = f' · {esc(row["scope"])}' if row.get("scope") else ""
            note = f'<small>{esc(row["note"])}</small>' if row.get("note") else ""
            rendered.append(f'<span class="history-row"><b>{esc(row["year"])}</b>：{esc(row["count"])}{scope} {source_link}{note}</span>')
        return "".join(rendered)

    phd_text = history_html(phd_history, "未发现公开的历年个人名额（不等于 0 人）")
    summer_text = history_html(summer_history, "未发现公开的历年暑研人数（不等于 0 人）")
    if backgrounds:
        background_text = "；".join(row["text"] for row in backgrounds)
        background_html = "；".join(
            f'{esc(row["text"])}' + (f' <a href="{esc(row["source"])}" target="_blank" rel="noopener">来源 ↗</a>' if row.get("source") else "")
            for row in backgrounds
        )
    else:
        background_text = "未发现课题组官网公开的可核验汇总；不根据姓名推断国籍"
        background_html = esc(background_text)
    department = item.get("department", "")
    public_fields = []
    if item.get("education"):
        public_fields.append("education")
    if phd_history:
        public_fields.append("phd")
    if summer_history:
        public_fields.append("summer")
    if backgrounds:
        public_fields.append("group")
    completeness = len(public_fields)
    mode_label = {"topics": "研究关键词译写", "translated": "中文简介", "area": "保守方向摘要"}.get(translation_mode, "中文译写")
    original_html = ""
    if original_summary:
        original_html = f'      <details class="original-summary"><summary>查看来源页英文摘录</summary><p lang="en">{esc(original_summary)}</p></details>'
    blob = " ".join([name, area_label, item.get("mode", ""), summary, original_summary, education, department, background_text]).lower()
    return f"""<article class="faculty-card" data-faculty-card data-area="{esc(area_label)}" data-name="{esc(name.lower())}" data-public="{esc(' '.join(public_fields))}" data-completeness="{completeness}" data-search="{esc(blob)}">
      <div class="faculty-top"><div class="faculty-identity"><span class="faculty-avatar" aria-hidden="true">{esc(faculty_initials(name))}</span><div><h3>{esc(name)}</h3><p class="faculty-title">{esc(safe_title(item['title']))}</p><p class="faculty-department">{esc(department)}</p></div></div><span class="area-tag">{esc(area_label)}</span></div>
      <div class="bio-block"><div class="bio-label"><span>中文简介</span><small>{esc(mode_label)}</small></div><p class="faculty-summary">{esc(summary)}</p></div>
{original_html}
      <div class="faculty-meta"><span>{esc(item.get('mode', '综合 / 待核实'))}</span><span>官网来源可追溯</span></div>
      <details class="faculty-more"><summary>学位、招生与组内背景</summary><dl>
        <div><dt>所属院系</dt><dd>{esc(department)}</dd></div>
        <div><dt>职称</dt><dd>{esc(safe_title(item['title']))}</dd></div>
        <div><dt>公开学位信息</dt><dd>{education_html}</dd></div>
        <div><dt>PhD 历年招收计划</dt><dd>{phd_text}</dd></div>
        <div><dt>暑研历年招收人数</dt><dd>{summer_text}</dd></div>
        <div><dt>组内学生公开背景</dt><dd>{background_html}</dd></div>
      </dl><p class="evidence-note">仅记录学校、院系或实验室官网明确公开的信息；“未公开”不代表没有招生。</p></details>
      <div class="faculty-links"><a href="{esc(profile)}" target="_blank" rel="noopener">个人主页 / 官方名录 ↗</a><a href="{esc(scholar)}" target="_blank" rel="noopener">论文检索 ↗</a></div>
    </article>"""


def build_home(metadata: list[dict], parsed: dict[str, list[dict]]) -> None:
    total = sum(len(parsed[item["id"]]) for item in metadata)
    cards = "".join(school_card(item, parsed[item["id"]]) for item in metadata)
    options = "".join(f'<option value="{esc(s)}">{esc(s)}</option>' for s in sorted({x for m in metadata for x in m["strengths"]}))
    body = f"""<main id="main">
      <section class="hero home-hero"><div class="eyebrow">U.S. QS TOP 30 · PHYSICS PHD</div><h1>先选学校，再找与你匹配的物理导师</h1><p>30 所美国高校的学校级研究地图：先看强项与重点实验室，再进入独立页面筛选教授、方向和成果入口。</p>
        <div class="hero-stats"><div><strong>30</strong><span>所高校</span></div><div><strong>{total:,}</strong><span>名教授 / 研究人员</span></div><div><strong>90</strong><span>个重点平台入口</span></div></div>
      </section>
      <section class="home-tools" aria-label="学校筛选"><label>搜索学校、方向或实验室<input id="schoolSearch" type="search" placeholder="例如：量子信息、宇宙学、MIT"></label><label>突出方向<select id="strengthFilter"><option value="">全部方向</option>{options}</select></label><p id="schoolResultCount">显示 30 所学校</p></section>
      <section class="notice"><b>覆盖说明</b><p>以物理系官方在职教师名录、研究领域页和研究生培养名单为主，纳入官方列出的联合/关联研究人员；排除荣休、纯教学、访问与兼职岗位。不同学校官网口径不同，因此不以不可靠的百分比制造“精确覆盖率”，而逐校公开人数、来源和日期。</p></section>
      <section class="school-grid" id="schoolGrid">{cards}</section>
    </main>"""
    (DIST / "index.html").write_text(page_shell("美国 QS 前 30 物理 PhD 导师地图", "按学校浏览美国 QS 前 30 高校的物理教授、研究方向与重点实验室。", body), encoding="utf-8")


def build_school(meta: dict, records: list[dict]) -> None:
    areas = area_counts(records)
    area_options = []
    for area, count in areas.most_common():
        label = "官网未细分 / 跨学科" if area == "跨学科与其他" else area
        area_options.append((label, count))
    options = "".join(f'<option value="{esc(area)}">{esc(area)}（{count}）</option>' for area, count in area_options)
    bars = "".join(
        f'<div class="bar-row"><span>{esc(area)}</span><div><i style="width:{max(7, round(count / len(records) * 100))}%"></i></div><b>{count}</b></div>'
        for area, count in area_options
    )
    labs = "".join(f"""<article class="lab-card"><span>研究平台</span><h3>{esc(name)}</h3><p>{esc(desc)}</p><a href="{esc(url)}" target="_blank" rel="noopener">进入官方主页 ↗</a></article>""" for name, url, desc in meta["labs"])
    faculty = "".join(faculty_card(item, meta["name"]) for item in records)
    source = records[0]["source"] if records else "#"
    body = f"""<main id="main">
      <nav class="breadcrumb"><a href="../index.html">全部学校</a><span>／</span><span>{esc(meta['short'])}</span></nav>
      <section class="hero school-hero"><div><div class="eyebrow">QS 世界大学排名 {esc(meta['rank'])}</div><h1>{esc(meta['name'])}</h1><p>物理 PhD 研究生态与导师名录。突出方向：{esc('、'.join(meta['strengths']))}。</p><div class="hero-actions"><a class="primary" href="{esc(source)}" target="_blank" rel="noopener">官方教师名录 ↗</a><a href="#faculty">浏览 {len(records)} 名教师</a></div></div><div class="school-number"><strong>{len(records)}</strong><span>名在册教授 / 研究人员</span><small>官网口径 · 核验 {CHECKED}</small></div></section>
      <section class="detail-grid"><div><div class="section-kicker">研究版图</div><h2>方向分布</h2><div class="bars">{bars}</div></div><div><div class="section-kicker">申请观察</div><h2>适合重点关注</h2><div class="focus-chips">{''.join(f'<span>{esc(x)}</span>' for x in meta['strengths'])}</div><p class="muted">分布来自官网公开文字的规则分类；“官网未细分”不代表没有研究方向，应进入个人主页查看近期项目与论文。</p></div></section>
      <section class="labs-section"><div class="section-heading"><div><div class="section-kicker">LABS & CENTERS</div><h2>突出的实验室与研究平台</h2></div><p>优先用于判断学校的设备、合作网络与共同导师资源。</p></div><div class="labs-grid">{labs}</div></section>
      <section class="faculty-section" id="faculty"><div class="section-heading"><div><div class="section-kicker">FACULTY DIRECTORY</div><h2>教授与研究人员</h2></div><p>{len(records)} 条记录均配有中文简介；保留来源摘录和官网入口便于核对。</p></div>
        <aside class="translation-note"><span>译写说明</span><p>中文简介用于申请初筛。当来源页只有学科分类、职务或上下文不足时，页面会显示“保守方向摘要”，不补写具体成果。最终请以个人主页和近期论文为准。</p></aside>
        <div class="faculty-tools"><label>按姓名或关键词搜索<input id="facultySearch" type="search" placeholder="姓名、量子材料、引力波……"></label><label>细分方向<select id="areaFilter"><option value="">全部方向（{len(records)}）</option>{options}</select></label><label>公开资料<select id="publicFilter"><option value="">不限</option><option value="education">已公开学位信息</option><option value="phd">已公开 PhD 招收数</option><option value="summer">已公开暑研人数</option><option value="group">已公开组员背景</option></select></label><label>排序<select id="facultySort"><option value="name">姓名 A–Z</option><option value="completeness">公开资料较多优先</option></select></label><div class="faculty-tool-actions"><p id="facultyResultCount">显示 {len(records)} 名</p><button id="facultyReset" type="button">重置筛选</button></div></div>
        <div class="faculty-grid" id="facultyGrid">{faculty}</div>
      </section>
      <section class="source-box"><h2>本页口径</h2><p>收录范围以学校物理系官方在职名录为主，并保留官网明确列出的联合/关联研究人员；排除荣休、访问、兼职和纯教学岗位。研究方向摘要来自官方名录或研究领域页；若官网列表没有公开细分方向，会明确标为“官网未细分 / 跨学科”。</p><p>学位、PhD/暑研历年名额和学生背景只记录官方公开内容。学生国籍仅在本人或学校明确公开时记录，绝不根据姓名、照片或毕业学校推断。个人招聘意向但未给人数时也不会换算为“1 人”。</p><p><a href="{esc(source)}" target="_blank" rel="noopener">查看本校核心官方来源 ↗</a>　<a href="../methodology.html">查看完整方法与局限</a></p></section>
    </main>"""
    path = DIST / "schools" / f"{meta['id']}.html"
    path.write_text(page_shell(f"{meta['short']} 物理 PhD 导师与实验室", f"{meta['name']} 物理教授、研究方向和重点实验室。", body, "../"), encoding="utf-8")


def build_methodology(total: int) -> None:
    body = f"""<main id="main" class="prose-page"><nav class="breadcrumb"><a href="index.html">全部学校</a><span>／</span><span>口径与使用方法</span></nav><article><div class="eyebrow">METHODOLOGY</div><h1>数据口径与申请使用方法</h1><p class="lead">本项目的目标是帮助申请者建立候选学校与导师长名单，而不是替代学校官网、论文数据库或与导师的直接沟通。</p><h2>学校范围</h2><p>学校范围按 QS 世界大学综合排名中的美国高校顺序选取前 30 所；这是机构综合排名，不等同于物理学科排名。站内保留 QS 名次便于复现筛选口径。</p><h2>教师覆盖</h2><p>当前共整理 {total:,} 条教授/研究人员记录。优先使用物理系官方在职 faculty 页面、研究领域名单及研究生培养手册；官网明确列出的联合或关联研究人员会保留。排除荣休、纯教学、访问、兼职与博士后。由于学校对“faculty”的定义不同，页面公开实际收录人数与来源，不伪造跨校可比的精确百分比。</p><h2>研究方向、成果与中文译写</h2><p>研究方向先读取官方目录和研究领域页，再按统一物理子领域归类。英文条目会转换为中文研究关键词，并在有来源摘录时保留英文原文供对照。当公开页只有职务、学科分类或上下文不足时，只给出“保守方向摘要”，不自行补写具体成果。每位教师均提供官方主页/名录入口和 Google Scholar 论文检索；论文作者同名时请用单位与 ORCID 交叉核对。</p><h2>学位、招生和学生背景</h2><p>学位只采用官方简介、CV 或院系名录明确列出的学位、授予学校和专业；缺少任一项时不补猜。PhD 与暑研人数必须同时有年份、明确人数和官方来源，“正在招人”不能换算为人数。“未公开”不等于 0。学生国籍属于容易被误推断的信息，只有本人或学校明确公开时才记录；毕业学校也只来自官方实验室成员简介，不使用姓名、照片、社交媒体或第三方聚合站推断。</p><h2>推荐使用顺序</h2><ol><li>先在首页按强项筛出 6–10 所学校。</li><li>进入学校页，按细分方向形成 3–8 位导师长名单。</li><li>阅读最近 3–5 年论文、实验室新闻与招生说明。</li><li>核对是否招收 PhD、经费、轮转制度和截止日期。</li><li>最终按研究匹配度、培养模式与生活成本，而不是仅按排名排序。</li></ol><h2>时效性</h2><p>最后核验日期：{CHECKED}。教师流动和招生状态变化很快，申请前必须再次打开官网核实。</p><p><a class="primary inline-button" href="index.html">返回学校地图</a></p></article></main>"""
    (DIST / "methodology.html").write_text(page_shell("数据口径与使用方法", "物理 PhD 导师地图的数据来源、覆盖范围、局限与使用方法。", body), encoding="utf-8")


def main() -> None:
    parsed = json.loads(DATA.read_text(encoding="utf-8"))
    enrichment = json.loads(ENRICHMENT.read_text(encoding="utf-8")) if ENRICHMENT.exists() else {}
    for school_id, records in parsed.items():
        parsed[school_id] = [item for item in records if not JUNK_NAME_RE.match(item["name"].strip())]
    for item in parsed.get("nyu", []):
        if item["name"] in NYU_AREAS:
            item["area"] = NYU_AREAS[item["name"]]
            item["summary"] = f"根据 NYU 官方院系与研究中心信息归入“{item['area']}”；近期成果与招生状态请进入主页核实。"

    for school_id, records in parsed.items():
        for item in records:
            item["department"] = DEPARTMENTS[school_id]
            item.setdefault("education", "")
            if item.get("education"):
                item.setdefault("education_source", item.get("source", ""))
            else:
                item.setdefault("education_source", "")
            item.setdefault("phd_recruitment_history", [])
            item.setdefault("summer_research_history", [])
            item.setdefault("group_student_backgrounds", [])
            verified = enrichment.get(school_id, {}).get(item["name"], {})
            for field, value in verified.items():
                item[field] = value
            summary_zh, summary_original, summary_translation_mode = chinese_summary(item)
            item["summary_zh"] = summary_zh
            item["summary_original"] = summary_original
            item["summary_translation_mode"] = summary_translation_mode

    metadata = []
    for order, (sid, name, short, rank, strengths, labs) in enumerate(SCHOOLS, 1):
        metadata.append({"id": sid, "name": name, "short": short, "rank": rank, "order": order, "strengths": strengths, "labs": labs})

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    (DIST / "schools").mkdir()
    (DIST / "data").mkdir()
    shutil.copytree(ROOT / "site" / "assets", DIST / "assets", dirs_exist_ok=True)

    build_home(metadata, parsed)
    for meta in metadata:
        build_school(meta, parsed[meta["id"]])
    total = sum(len(parsed[m["id"]]) for m in metadata)
    build_methodology(total)

    export = []
    for meta in metadata:
        export.append({**meta, "faculty": parsed[meta["id"]]})
    (DIST / "data" / "schools.json").write_text(json.dumps(export, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    urls = [f"{SITE_URL}/", f"{SITE_URL}/methodology.html", *(f"{SITE_URL}/schools/{m['id']}.html" for m in metadata)]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{esc(url)}</loc></url>\n" for url in urls) + "</urlset>\n"
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"Built {len(metadata)} school pages with {total} faculty records")


if __name__ == "__main__":
    main()
