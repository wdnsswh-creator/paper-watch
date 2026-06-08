#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Daily Literature Tracker

Purpose:
Search OpenAlex for papers related to wetland soil microorganisms,
nitrogen addition, different nitrogen forms, nitrogen addition levels,
nitrogen cycling processes, Spartina alterniflora / wetland vegetation,
and soil nitrogen cycling functional genes.

Outputs:
1. output/daily_papers.md
2. output/daily_papers.ris
3. output/seen_dois.txt

Safety:
- Does not download PDFs.
- Does not log in to Web of Science or any school account.
- Does not connect to Zotero API.
"""

import argparse
import datetime as dt
import html
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "keywords.yaml"
SKILL_PATH = ROOT / "skills" / "soil-nitrogen-literature-curation" / "SKILL.md"
OUTPUT_DIR = ROOT / "output"
SEEN_DOIS_PATH = OUTPUT_DIR / "seen_dois.txt"
MD_PATH = OUTPUT_DIR / "daily_papers.md"
RIS_PATH = OUTPUT_DIR / "daily_papers.ris"


EXCLUDE_TERMS = [
    # Medical / clinical / animal
    "human",
    "patient",
    "clinical",
    "tumor",
    "cancer",
    "diabetes",
    "insulin",
    "gut microbiome",
    "intestinal",
    "fecal",
    "mouse",
    "mice",
    "rat",
    "livestock",
    "poultry",
    "swine",
    "rumen",

    # Food / medicine / industrial fermentation
    "medicinal plant",
    "pharmaceutical",
    "traditional medicine",
    "milk",
    "dairy",
    "food",
    "beverage",
    "cell feed",
    "probiotic",

    # Clearly off-topic environmental / engineering directions
    "freshwater methane filter",
    "drinking water",
    "wastewater treatment plant",
    "activated sludge",
    "aquaculture",
    "hydroponic",

    # Off-topic organisms or settings observed in previous results
    "insulin plant",
    "costus igneus",
    "summer snowflake",
    "microbacterium algeriense",
]


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", str(value))
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_doi(doi: Optional[str]) -> str:
    if not doi:
        return ""
    doi = doi.strip()
    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    return doi.lower()


def load_keywords() -> List[str]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing required file: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    keywords: List[str] = []

    def collect(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                collect(v)
        elif isinstance(obj, list):
            for x in obj:
                collect(x)
        elif isinstance(obj, str):
            keywords.append(obj)

    collect(data)

    keywords = [x.strip() for x in keywords if x and x.strip()]
    if not keywords:
        raise ValueError("No keywords found in config/keywords.yaml")

    return list(dict.fromkeys(keywords))


def check_skill_file() -> None:
    if not SKILL_PATH.exists():
        print(f"Warning: skill file not found: {SKILL_PATH}")
        print("The script will continue with built-in relevance rules.")


def load_seen_dois() -> set:
    if not SEEN_DOIS_PATH.exists():
        return set()

    with open(SEEN_DOIS_PATH, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def save_seen_dois(dois: set) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SEEN_DOIS_PATH, "w", encoding="utf-8") as f:
        for doi in sorted(dois):
            f.write(doi + "\n")


def build_queries(keywords: List[str], max_queries: int = 45) -> List[str]:
    """
    Build broad but topic-focused search queries.

    The goal is not to find papers matching every single keyword.
    The goal is to retrieve similar papers around:
    wetland / salt marsh / soil / microorganisms / nitrogen addition /
    nitrogen forms / nitrogen cycling / functional genes / vegetation invasion.
    """

    preferred = [
        # Core topic: soil nitrogen cycling functional genes and metagenomics
        "soil nitrogen cycling functional genes",
        "nitrogen-cycle functional genes soil microorganisms",
        "soil microbial nitrogen cycling functional genes",
        "metagenomics nitrogen cycling functional genes",
        "soil metagenomic analysis nitrogen-cycle processes",
        "microorganisms involved in nitrogen-cycle processes",
        "carbon-nitrogen cycling functional genes microbial communities",

        # Wetland / coastal wetland / salt marsh / land-sea interface
        "coastal wetland soil nitrogen cycling",
        "wetland soil microbial nitrogen cycling",
        "salt marsh nitrogen cycling",
        "salt marsh microbial nitrogen cycling",
        "salt marsh sediment nitrogen cycling",
        "tidal wetland microbial nitrogen cycling",
        "estuarine wetland nitrogen cycling",
        "coastal saline wetland microbial community",
        "land sea interface nitrogen cycling",
        "Yellow River Delta wetland microbial community",
        "Yellow River Delta soil microbial nitrogen cycling",

        # Nitrogen addition / deposition / enrichment
        "nitrogen addition soil microbial community",
        "nitrogen addition soil nitrogen cycling functional genes",
        "nitrogen addition microbial functional genes",
        "nitrogen deposition microbial communities functional genes",
        "nitrogen deposition carbon-nitrogen cycling functional genes",
        "nitrogen enrichment wetland soil microbial community",
        "nitrogen loading salt marsh microbial community",
        "nutrient enrichment salt marsh microbial community",
        "long-term nitrogen addition soil microbial community",

        # Nitrogen forms and levels
        "ammonium addition soil microbial community",
        "nitrate addition soil microbial community",
        "ammonium addition soil nitrogen cycling",
        "nitrate addition soil nitrogen cycling",
        "ammonium versus nitrate soil microbial nitrogen cycling",
        "different nitrogen forms soil microbial community",
        "different nitrogen forms nitrogen cycling functional genes",
        "nitrogen addition gradient soil microbial community",
        "nitrogen addition levels soil microbial functional genes",
        "low medium high nitrogen addition soil microbial community",

        # Processes and genes
        "nitrification denitrification DNRA nitrogen fixation functional genes",
        "ammonia oxidation nitrate reduction denitrification wetland soil",
        "amoA hao nirK nirS norB norC nosZ nrfA nifH soil",
        "nrfA nosZ nirK nirS wetland soil nitrogen cycling",
        "KEGG nitrogen metabolism soil metagenomics",
        "FAPROTAX nitrogen cycling wetland soil microbial community",

        # Vegetation, invasion and rhizosphere
        "Spartina alterniflora invasion soil microbial community",
        "Spartina alterniflora invasion nitrogen cycling",
        "Spartina alterniflora soil nitrogen cycling functional genes",
        "salt marsh invasion Spartina alterniflora microbial community",
        "wetland plant invasion soil microbial community nitrogen cycling",
        "Phragmites australis soil microbial nitrogen cycling",
        "Suaeda salsa soil microbial community nitrogen cycling",
        "Tamarix chinensis soil microbial community",
        "halophyte rhizosphere soil nitrogen cycling",
        "salt-tolerant vegetation soil microbial community",

        # Environmental drivers
        "salinity gradient soil microbial community nitrogen cycling",
        "saline-alkali soil microbial community nitrogen cycling",
        "soil salinity nitrogen cycling functional genes",
        "soil pH salinity microbial nitrogen cycling",
        "soil moisture microbial nitrogen cycling wetland",
        "coastal salinity gradient microbial community",
    ]

    merged = preferred + keywords

    result = []
    for q in merged:
        q = q.strip()
        if q and q not in result:
            result.append(q)
        if len(result) >= max_queries:
            break

    return result


def inverted_abstract_to_text(index: Optional[Dict[str, List[int]]]) -> str:
    if not index:
        return ""

    words = []
    for word, positions in index.items():
        for pos in positions:
            words.append((pos, word))

    words.sort(key=lambda x: x[0])
    return clean_text(" ".join(word for _, word in words))


def search_openalex(query: str, mailto: Optional[str], days: int, limit: int) -> List[Dict]:
    from_date = (dt.date.today() - dt.timedelta(days=days)).isoformat()

    params = {
        "search": query,
        "filter": f"from_publication_date:{from_date},type:article",
        "per-page": min(limit, 200),
        "sort": "publication_date:desc",
    }

    if mailto:
        params["mailto"] = mailto

    url = "https://api.openalex.org/works"
    response = requests.get(url, params=params, timeout=40)
    response.raise_for_status()
    data = response.json()

    records = []

    for item in data.get("results", []):
        title = clean_text(item.get("title"))
        year = item.get("publication_year") or ""
        doi = normalize_doi(item.get("doi"))
        url_value = item.get("id") or ""

        journal = ""
        source = item.get("primary_location", {}).get("source")
        if source:
            journal = clean_text(source.get("display_name"))

        authors = []
        for auth in item.get("authorships", []):
            name = auth.get("author", {}).get("display_name")
            if name:
                authors.append(clean_text(name))

        abstract = inverted_abstract_to_text(item.get("abstract_inverted_index"))

        if not title:
            continue

        records.append(
            {
                "title": title,
                "authors": authors,
                "year": str(year),
                "journal": journal,
                "doi": doi,
                "abstract": abstract,
                "url": url_value,
                "query": query,
            }
        )

    return records


def classify_record(record: Dict) -> Tuple[str, str, str]:
    """
    Relevance classification based on weighted scoring.

    This version is intentionally broader than strict AND matching.
    It keeps papers that are similar to the user's topic, even if they do not
    contain every target keyword at the same time.
    """

    text = " ".join(
        [
            record.get("title", ""),
            record.get("abstract", ""),
            record.get("journal", ""),
            record.get("query", ""),
        ]
    ).lower()

    if any(term in text for term in EXCLUDE_TERMS):
        return (
            "D",
            "排除：主题更接近医学、食品、动物、工业或其他明显偏离土壤微生物/湿地氮循环方向的研究。",
            "08_低相关暂存",
        )

    ecosystem_terms = [
        "wetland",
        "coastal wetland",
        "salt marsh",
        "tidal marsh",
        "estuarine",
        "estuary",
        "coastal",
        "sediment",
        "saline",
        "salinity",
        "saline-alkali",
        "salt-affected",
        "yellow river delta",
        "land-sea",
        "land sea",
        "marsh",
    ]

    soil_terms = [
        "soil",
        "rhizosphere",
        "sediment",
        "sediments",
    ]

    microbe_terms = [
        "microbial",
        "microorganism",
        "microorganisms",
        "bacterial",
        "bacteria",
        "fungal",
        "fungi",
        "archaea",
        "microbiome",
        "microbial community",
        "bacterial community",
        "fungal community",
        "community structure",
        "microbial diversity",
    ]

    nitrogen_terms = [
        "nitrogen",
        "nitrogen cycling",
        "nitrogen cycle",
        "nitrogen transformation",
        "nitrification",
        "denitrification",
        "dnra",
        "dissimilatory nitrate reduction",
        "nitrate reduction",
        "nitrogen fixation",
        "ammonia oxidation",
        "ammonium",
        "nitrate",
        "nitrite",
        "nitrous oxide",
        "n2o",
        "mineralization",
    ]

    addition_terms = [
        "nitrogen addition",
        "nitrogen deposition",
        "nitrogen enrichment",
        "nitrogen loading",
        "nitrogen input",
        "nutrient enrichment",
        "fertilization",
        "fertilizer",
        "nitrate enrichment",
        "ammonium addition",
        "nitrate addition",
        "ammonium nitrate",
        "different nitrogen forms",
        "nitrogen forms",
        "nitrogen levels",
        "nitrogen gradient",
        "addition gradient",
        "long-term fertilization",
    ]

    function_terms = [
        "functional gene",
        "functional genes",
        "nitrogen cycling gene",
        "nitrogen cycling genes",
        "nitrogen-cycle functional genes",
        "metagenomic",
        "metagenomics",
        "shotgun",
        "kegg",
        "faprotax",
        "funguild",
        "functional potential",
        "functional prediction",
        "nitrogen metabolism",
        "carbon-nitrogen cycling",
        "c-n cycling",
        "amoa",
        "hao",
        "nirk",
        "nirs",
        "norb",
        "norc",
        "nosz",
        "nrfa",
        "nifh",
        "nifd",
        "nifk",
        "napa",
        "narg",
        "nxra",
        "nxrb",
        "urec",
    ]

    vegetation_terms = [
        "spartina alterniflora",
        "spartina",
        "phragmites australis",
        "phragmites",
        "suaeda salsa",
        "suaeda",
        "tamarix chinensis",
        "tamarix",
        "halophyte",
        "halophytes",
        "salt-tolerant vegetation",
        "plant invasion",
        "invasive plant",
        "invasion",
        "vegetation type",
        "rhizosphere",
    ]

    network_terms = [
        "co-occurrence network",
        "microbial network",
        "network complexity",
        "community assembly",
        "microbial interaction",
        "bacterial-fungal",
        "bacteria-fungi",
    ]

    ecosystem_score = sum(1 for term in ecosystem_terms if term in text)
    soil_score = sum(1 for term in soil_terms if term in text)
    microbe_score = sum(1 for term in microbe_terms if term in text)
    nitrogen_score = sum(1 for term in nitrogen_terms if term in text)
    addition_score = sum(1 for term in addition_terms if term in text)
    function_score = sum(1 for term in function_terms if term in text)
    vegetation_score = sum(1 for term in vegetation_terms if term in text)
    network_score = sum(1 for term in network_terms if term in text)

    total_score = (
        ecosystem_score * 2
        + soil_score * 2
        + microbe_score * 2
        + nitrogen_score * 3
        + addition_score * 3
        + function_score * 4
        + vegetation_score * 2
        + network_score * 1
    )

    # A 类：强相关，不要求所有条件同时满足
    if (
        total_score >= 12
        and nitrogen_score >= 1
        and (microbe_score >= 1 or soil_score >= 1)
        and (
            function_score >= 1
            or addition_score >= 1
            or ecosystem_score >= 2
            or vegetation_score >= 2
        )
    ):
        return (
            "A",
            "高度相关：与土壤微生物、氮循环、氮添加/氮沉降、土壤氮循环功能基因、湿地/盐沼或典型湿地植被中的多个方向高度重合，建议优先阅读。",
            "03_土壤氮循环功能基因",
        )

    # B 类：相似研究，适合讨论和扩展阅读
    if (
        total_score >= 8
        and (
            nitrogen_score >= 1
            or microbe_score >= 1
            or ecosystem_score >= 1
            or function_score >= 1
        )
    ):
        return (
            "B",
            "中等相关：与用户课题在湿地、土壤微生物、氮循环、氮添加、植被或功能基因中的部分方向相似，可用于讨论或补充阅读。",
            "07_讨论部分可引用文献",
        )

    # C 类：背景相关，先留下，不直接丢掉
    if total_score >= 5:
        return (
            "C",
            "间接相关：与湿地环境、微生物群落、氮循环、植被或土壤过程有一定联系，可作为背景文献暂存。",
            "08_低相关暂存",
        )

    return (
        "D",
        "排除：与湿地、土壤微生物、氮循环、氮添加或土壤氮循环功能基因的关联较弱。",
        "08_低相关暂存",
    )


def deduplicate_records(records: List[Dict]) -> List[Dict]:
    seen = set()
    output = []

    for r in records:
        key = r.get("doi") or r.get("title", "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(r)

    return output


def write_markdown(records: List[Dict], all_count: int) -> None:
    today = dt.date.today().isoformat()
    grouped = {"A": [], "B": [], "C": []}

    for r in records:
        if r["level"] in grouped:
            grouped[r["level"]].append(r)

    lines = []
    lines.append("# 今日文献追踪结果")
    lines.append("")
    lines.append(f"检索日期：{today}")
    lines.append("")
    lines.append(f"检索去重后文献总数：{all_count}")
    lines.append("")
    lines.append(f"写入结果文献数：{len(records)}")
    lines.append("")
    lines.append(f"A 类文献数量：{len(grouped['A'])}")
    lines.append("")
    lines.append(f"B 类文献数量：{len(grouped['B'])}")
    lines.append("")
    lines.append(f"C 类文献数量：{len(grouped['C'])}")
    lines.append("")

    section_names = {
        "A": "A 类：必须阅读",
        "B": "B 类：建议阅读",
        "C": "C 类：可选阅读",
    }

    for level in ["A", "B", "C"]:
        lines.append(f"## {section_names[level]}")
        lines.append("")

        if not grouped[level]:
            lines.append("今日暂无。")
            lines.append("")
            continue

        for i, r in enumerate(grouped[level], 1):
            lines.append(f"### {i}. {r.get('title', '')}")
            lines.append("")
            lines.append(f"- 作者：{', '.join(r.get('authors', [])[:6])}")
            lines.append(f"- 年份：{r.get('year', '')}")
            lines.append(f"- 期刊：{r.get('journal', '')}")
            lines.append(f"- DOI：{r.get('doi', '')}")
            lines.append(f"- URL：{r.get('url', '')}")
            lines.append(f"- 触发检索词：{r.get('query', '')}")
            lines.append(f"- 建议 Zotero collection：{r.get('collection', '')}")
            lines.append(f"- 推荐理由：{r.get('reason', '')}")

            abstract = r.get("abstract", "")
            if len(abstract) > 1200:
                abstract = abstract[:1200] + "..."

            lines.append(f"- 摘要核心内容：{abstract}")
            lines.append("")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def escape_ris(value: str) -> str:
    return clean_text(value).replace("\n", " ")


def write_ris(records: List[Dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = []

    for r in records:
        lines.append("TY  - JOUR")
        lines.append(f"TI  - {escape_ris(r.get('title', ''))}")

        for author in r.get("authors", [])[:20]:
            lines.append(f"AU  - {escape_ris(author)}")

        if r.get("journal"):
            lines.append(f"JO  - {escape_ris(r.get('journal', ''))}")
        if r.get("year"):
            lines.append(f"PY  - {escape_ris(r.get('year', ''))}")
        if r.get("doi"):
            lines.append(f"DO  - {escape_ris(r.get('doi', ''))}")
        if r.get("url"):
            lines.append(f"UR  - {escape_ris(r.get('url', ''))}")
        if r.get("abstract"):
            lines.append(f"AB  - {escape_ris(r.get('abstract', ''))}")

        lines.append("ER  -")
        lines.append("")

    with open(RIS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mailto",
        default="",
        help="Your email for polite OpenAlex API usage.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Search papers published in recent N days.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max records per query.",
    )

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    check_skill_file()
    keywords = load_keywords()
    queries = build_queries(keywords)

    seen_dois = load_seen_dois()
    all_records = []

    for query in queries:
        print(f"Searching OpenAlex: {query}")

        try:
            records = search_openalex(query, args.mailto, args.days, args.limit)
            all_records.extend(records)
            time.sleep(0.5)
        except Exception as exc:
            print(f"Warning: failed query: {query}")
            print(f"Reason: {exc}")

    all_records = deduplicate_records(all_records)

    new_records = []

    for record in all_records:
        doi = normalize_doi(record.get("doi"))

        if doi and doi in seen_dois:
            continue

        level, reason, collection = classify_record(record)
        record["level"] = level
        record["reason"] = reason
        record["collection"] = collection

        if level != "D":
            new_records.append(record)

        if doi:
            seen_dois.add(doi)

    write_markdown(new_records, len(all_records))
    write_ris(new_records)
    save_seen_dois(seen_dois)

    print("Done.")
    print(f"Markdown: {MD_PATH}")
    print(f"RIS: {RIS_PATH}")
    print(f"Seen DOIs: {SEEN_DOIS_PATH}")
    print(f"Records written: {len(new_records)}")


if __name__ == "__main__":
    main()
