#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Daily Literature Tracker

This script searches OpenAlex for papers related to soil nitrogen cycling,
classifies them into A/B/C/D relevance levels, and exports:

1. output/daily_papers.md
2. output/daily_papers.ris
3. output/seen_dois.txt

It does not download PDFs.
It does not log in to Web of Science or any school account.
It does not connect to Zotero API.
"""

import argparse
import datetime as dt
import html
import os
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


A_TERMS = [
    "coastal wetland",
    "salt marsh",
    "saline wetland",
    "saline-alkali",
    "yellow river delta",
    "metagenomic",
    "metagenomics",
    "nitrogen cycling gene",
    "nitrogen cycling functional gene",
    "functional gene",
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
]

B_TERMS = [
    "nitrogen addition",
    "ammonium addition",
    "nitrate addition",
    "nh4",
    "no3",
    "nitrification",
    "denitrification",
    "dnra",
    "nitrogen fixation",
    "mineralization",
    "soil nitrogen",
    "wetland soil",
]

EXCLUDE_TERMS = [
    "human",
    "patient",
    "clinical",
    "tumor",
    "cancer",
    "gut microbiome",
    "intestinal",
    "mouse",
    "mice",
    "rat",
    "livestock",
    "poultry",
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


def build_queries(keywords: List[str], max_queries: int = 8) -> List[str]:
    preferred = [
        "coastal wetland nitrogen cycling",
        "soil nitrogen cycling functional genes",
        "metagenomics nitrogen cycling soil",
        "nitrogen addition wetland soil",
        "nitrification denitrification DNRA nitrogen fixation",
        "amoA nirK nirS nosZ nrfA nifH soil",
        "saline-alkali soil nitrogen cycling",
        "Yellow River Delta wetland nitrogen cycling",
    ]

    merged = preferred + keywords
    result = []
    for q in merged:
        if q not in result:
            result.append(q)
        if len(result) >= max_queries:
            break
    return result


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


def inverted_abstract_to_text(index: Optional[Dict[str, List[int]]]) -> str:
    if not index:
        return ""
    words = []
    for word, positions in index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort(key=lambda x: x[0])
    return clean_text(" ".join(word for _, word in words))


def classify_record(record: Dict) -> Tuple[str, str, str]:
    text = " ".join(
        [
            record.get("title", ""),
            record.get("abstract", ""),
            record.get("journal", ""),
            record.get("query", ""),
        ]
    ).lower()

    if any(term in text for term in EXCLUDE_TERMS):
        return "D", "排除：主题更接近医学、人体、动物或非土壤氮循环研究。", "08_低相关暂存"

    a_score = sum(1 for term in A_TERMS if term in text)
    b_score = sum(1 for term in B_TERMS if term in text)

    if a_score >= 2 and b_score >= 1:
        return (
            "A",
            "高度相关：同时涉及滨海/盐碱湿地、宏基因组或土壤氮循环功能基因，并与氮循环过程有关。",
            "03_土壤氮循环功能基因",
        )

    if a_score >= 1 and b_score >= 1:
        return (
            "B",
            "中等相关：涉及土壤氮循环、氮添加、硝化、反硝化、DNRA 或固氮过程，可用于讨论机制。",
            "07_讨论部分可引用文献",
        )

    if b_score >= 1:
        return (
            "C",
            "间接相关：与氮循环或土壤微生物过程有关，可作为引言或背景文献。",
            "08_低相关暂存",
        )

    return "D", "排除：与当前博士论文主题相关度较低。", "08_低相关暂存"


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
    lines.append(f"新增文献总数：{all_count}")
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
    parser.add_argument("--mailto", default="", help="Your email for polite OpenAlex API usage.")
    parser.add_argument("--days", type=int, default=14, help="Search papers published in recent N days.")
    parser.add_argument("--limit", type=int, default=50, help="Max records per query.")
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
            time.sleep(1)
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

    print(f"Done.")
    print(f"Markdown: {MD_PATH}")
    print(f"RIS: {RIS_PATH}")
    print(f"Seen DOIs: {SEEN_DOIS_PATH}")
    print(f"Records written: {len(new_records)}")


if __name__ == "__main__":
    main()
