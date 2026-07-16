#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Search literature abstracts that can support thesis abstract writing.

This script:
- reads a user's abstract draft or uses a built-in Yellow River Delta wetland template;
- searches Crossref, OpenAlex, and Semantic Scholar for related paper metadata;
- scores papers by abstract-writing usefulness, method similarity, topic fit, and metadata quality;
- writes output/abstract_papers.md and output/abstract_papers.ris for Zotero import.

Safety:
- does not download PDFs;
- does not log in to any school account;
- does not connect to the Zotero API.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
MD_PATH = OUTPUT_DIR / "abstract_papers.md"
RIS_PATH = OUTPUT_DIR / "abstract_papers.ris"
SEEN_PATH = OUTPUT_DIR / "abstract_seen_dois.txt"


DEFAULT_ABSTRACT_DRAFT = """
黄河三角洲滨海湿地受陆海相互作用影响显著，形成了明显的盐分、水分和植被空间梯度，这些环境差异可能深刻影响土壤微生物群落组成及其生态功能。
土壤细菌和真菌是湿地养分循环、植物适应和生态系统稳定的重要参与者，但不同盐生植物生境及海陆位置变化下微生物群落结构、功能和共现关系的响应机制仍不清楚。
因此，本研究以黄河三角洲典型盐生植物柽柳、碱蓬和芦苇根际土壤为对象，采用高通量测序技术分析不同生境下土壤细菌和真菌群落多样性、组成结构、潜在功能及共现网络变化特征。
"""


SEED_QUERIES = [
    "Yellow River Delta coastal wetland soil microbial community",
    "Yellow River Delta wetland bacterial fungal community",
    "Phragmites australis soil microbial community Yellow River Delta",
    "Tamarix chinensis Suaeda salsa Phragmites australis soil microbial community",
    "coastal wetland vegetation soil bacterial fungal communities",
    "salinity gradient soil microbial community coastal wetland",
    "distance from coastline soil microbial diversity",
    "rhizosphere soil bacterial fungal community halophyte wetland",
    "high-throughput sequencing bacterial fungal communities saline wetland",
    "co-occurrence network bacterial fungal community coastal wetland",
    "FAPROTAX FUNGuild wetland soil microbial community",
    "environmental drivers soil microbial community salinity pH electrical conductivity",
    "Shifts in Soil Microbial Community Composition Function and Co-occurrence Network of Phragmites australis in the Yellow River Delta",
    "Shifts in the soil bacterial community along a salinity gradient in the Yellow River Delta",
    "Environmental Filtering by pH and Salinity Jointly Drives Prokaryotic Community Assembly in Coastal Wetland Sediments",
]


CLEAN_DEFAULT_ABSTRACT_DRAFT = """
黄河三角洲滨海湿地受陆海相互作用影响显著，形成了明显的盐分、水分和植被空间梯度，这些环境差异可能深刻影响土壤微生物群落组成及其生态功能。
土壤细菌和真菌是湿地养分循环、植物适应和生态系统稳定的重要参与者，但不同盐生植物生境及海陆位置变化下微生物群落结构、功能和共现关系的响应机制仍不清楚。
因此，本研究以黄河三角洲典型盐生植物柽柳、碱蓬和芦苇根际土壤为对象，采用高通量测序技术分析不同生境下土壤细菌和真菌群落多样性、组成结构、潜在功能及共现网络变化特征。
"""


LATEST_ABSTRACT_DRAFT = """
黄河三角洲滨海湿地是陆海相互作用强烈的典型生态过渡区，受潮汐、盐分、水分和植被分布等因素共同影响，土壤环境具有明显的空间异质性。
土壤微生物作为连接植物生长、养分循环和湿地生态功能的重要生物因子，对环境梯度变化十分敏感，但目前关于不同盐生植物及其空间位置共同作用下细菌和真菌群落结构、潜在功能及互作网络变化的认识仍较有限。
基于此，本研究选取黄河三角洲滨海湿地中三种典型盐生植物柽柳、碱蓬和芦苇，比较其不同空间位置根际土壤细菌和真菌群落组成、功能预测及共现网络特征，以揭示滨海湿地微生物群落对不同生境条件的响应规律。
"""


EXCLUDE_TERMS = [
    "human",
    "patient",
    "clinical",
    "tumor",
    "cancer",
    "gut microbiome",
    "intestinal",
    "fecal",
    "mouse",
    "mice",
    "rat",
    "livestock",
    "rumen",
    "food",
    "dairy",
    "probiotic",
    "wastewater treatment plant",
    "activated sludge",
    "drinking water",
    "reactor",
    "hydroponic",
    "bees",
    "apis mellifera",
    "insect",
    "insects",
    "propolis",
    "hive",
    "hives",
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
    doi = doi.strip().lower()
    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("doi:", "")
    return doi


def read_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {normalize_doi(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def write_seen(path: Path, dois: Iterable[str]) -> None:
    path.write_text("\n".join(sorted(set(dois))) + "\n", encoding="utf-8")


def inverted_abstract_to_text(index: Optional[Dict[str, List[int]]]) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        words.extend((pos, word) for pos in positions)
    return clean_text(" ".join(word for _, word in sorted(words)))


def extract_draft_queries(draft: str) -> list[str]:
    queries = list(SEED_QUERIES)

    signals = {
        "黄河三角洲": "Yellow River Delta wetland soil microbial community",
        "滨海湿地": "coastal wetland soil microbial community",
        "盐分": "soil salinity microbial community coastal wetland",
        "水分": "soil moisture wetland microbial community",
        "植被": "vegetation type soil microbial community wetland",
        "柽柳": "Tamarix chinensis soil microbial community",
        "碱蓬": "Suaeda salsa soil microbial community",
        "芦苇": "Phragmites australis soil microbial community",
        "细菌": "soil bacterial community coastal wetland",
        "真菌": "soil fungal community coastal wetland",
        "共现": "co-occurrence network bacterial fungal community soil",
        "高通量测序": "high-throughput sequencing soil microbial community wetland",
        "FAPROTAX": "FAPROTAX wetland soil microbial community",
        "FUNGuild": "FUNGuild wetland soil fungal community",
    }

    for zh, query in signals.items():
        if zh in draft and query not in queries:
            queries.append(query)

    return queries


def search_crossref(query: str, days: int, limit: int) -> list[dict]:
    from_date = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    params = {
        "query.bibliographic": query,
        "filter": f"from-pub-date:{from_date},type:journal-article",
        "rows": min(limit, 20),
        "sort": "relevance",
        "order": "desc",
        "select": "title,author,published-print,published-online,published,container-title,DOI,abstract,URL",
    }
    response = requests.get("https://api.crossref.org/works", params=params, timeout=45)
    response.raise_for_status()
    items = response.json().get("message", {}).get("items", [])
    records = []
    for item in items:
        titles = item.get("title") or []
        title = clean_text(titles[0]) if titles else ""
        if not title:
            continue
        journal_list = item.get("container-title") or []
        journal = clean_text(journal_list[0]) if journal_list else ""
        year = ""
        for key in ["published-print", "published-online", "published"]:
            parts = item.get(key, {}).get("date-parts")
            if parts and parts[0]:
                year = str(parts[0][0])
                break
        authors = []
        for author in item.get("author", []) or []:
            name = clean_text(f"{author.get('given', '')} {author.get('family', '')}")
            if name:
                authors.append(name)
        records.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": normalize_doi(item.get("DOI")),
                "abstract": clean_text(item.get("abstract") or ""),
                "url": item.get("URL") or "",
                "query": query,
                "source": "Crossref",
            }
        )
    return records


def search_openalex(query: str, days: int, limit: int, mailto: str = "") -> list[dict]:
    from_date = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    params = {
        "search": query,
        "filter": f"from_publication_date:{from_date},type:article",
        "per-page": min(limit, 200),
        "sort": "relevance_score:desc",
    }
    if mailto:
        params["mailto"] = mailto
    response = requests.get("https://api.openalex.org/works", params=params, timeout=45)
    response.raise_for_status()
    records = []
    for item in response.json().get("results", []):
        title = clean_text(item.get("title"))
        if not title:
            continue
        source = item.get("primary_location", {}).get("source") or {}
        records.append(
            {
                "title": title,
                "authors": [
                    clean_text(a.get("author", {}).get("display_name"))
                    for a in item.get("authorships", [])
                    if a.get("author", {}).get("display_name")
                ],
                "year": str(item.get("publication_year") or ""),
                "journal": clean_text(source.get("display_name") or ""),
                "doi": normalize_doi(item.get("doi")),
                "abstract": inverted_abstract_to_text(item.get("abstract_inverted_index")),
                "url": item.get("id") or "",
                "query": query,
                "source": "OpenAlex",
            }
        )
    return records


def search_semantic_scholar(query: str, days: int, limit: int) -> list[dict]:
    current_year = dt.date.today().year
    min_year = current_year - max(1, int(days / 365)) - 1
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,authors,year,venue,abstract,url,externalIds,citationCount",
        "year": f"{min_year}-",
    }
    response = requests.get("https://api.semanticscholar.org/graph/v1/paper/search", params=params, timeout=45)
    if response.status_code == 429:
        return []
    response.raise_for_status()
    records = []
    for item in response.json().get("data", []):
        title = clean_text(item.get("title"))
        if not title:
            continue
        external = item.get("externalIds") or {}
        records.append(
            {
                "title": title,
                "authors": [clean_text(a.get("name")) for a in item.get("authors", []) if a.get("name")],
                "year": str(item.get("year") or ""),
                "journal": clean_text(item.get("venue") or ""),
                "doi": normalize_doi(external.get("DOI")),
                "abstract": clean_text(item.get("abstract") or ""),
                "url": item.get("url") or "",
                "query": query,
                "source": "Semantic Scholar",
                "citation_count": item.get("citationCount") or 0,
            }
        )
    return records


def metadata_exclusion_reason(record: dict) -> str:
    title = clean_text(record.get("title", ""))
    title_lower = title.lower()
    doi = normalize_doi(record.get("doi"))
    journal = clean_text(record.get("journal"))
    abstract = clean_text(record.get("abstract"))
    full_text = " ".join([title_lower, abstract.lower(), journal.lower()])

    if any(term in full_text for term in EXCLUDE_TERMS):
        return "主题偏离：医学、动物、食品、污水处理或其他非土壤湿地微生物方向。"
    if re.match(r"^(figure|fig\.?|table)\s+\d*", title_lower):
        return "元数据不是论文：疑似图或表的 DOI。"
    if re.search(r"/(fig|figure|table)-?\d*$", doi) or doi.endswith(".s001"):
        return "元数据不是论文：疑似 supporting information、图或表 DOI。"
    if not journal:
        return "期刊信息缺失。"
    if not abstract or len(abstract) < 80:
        return "摘要缺失或过短，不能支撑摘要写作。"
    return ""


def detect_sentence_support(record: dict) -> list[str]:
    text = " ".join([record.get("title", ""), record.get("abstract", "")]).lower()
    support = []
    if any(t in text for t in ["coastal wetland", "yellow river delta", "salinity gradient", "estuarine", "salt marsh"]):
        support.append("背景句")
    if any(t in text for t in ["unclear", "little is known", "poorly understood", "unknown", "mechanism"]):
        support.append("问题句")
    if any(t in text for t in ["tamarix", "suaeda", "phragmites", "vegetation", "rhizosphere", "habitat"]):
        support.append("对象句")
    if any(t in text for t in ["high-throughput", "16s", "its", "sequencing", "pcoa", "nmds", "lefse", "faprotax", "funguild", "co-occurrence"]):
        support.append("方法句")
    if any(t in text for t in ["provide insights", "suggest", "indicate", "understanding", "ecological", "ecosystem"]):
        support.append("意义句")
    return support


def journal_quality_score(record: dict) -> tuple[int, str]:
    journal = clean_text(record.get("journal")).lower()
    strong = [
        "frontiers in microbiology",
        "frontiers in marine science",
        "land degradation & development",
        "soil biology and biochemistry",
        "applied and environmental microbiology",
        "environmental microbiology",
        "fems microbiology ecology",
        "new phytologist",
        "molecular ecology",
        "environmental research",
        "science of the total environment",
        "journal of environmental management",
    ]
    caution = ["microorganisms", "plants"]
    if any(x in journal for x in strong):
        return 10, "期刊规格较好，可作为重点候选。"
    if any(x in journal for x in caution):
        return -4, "期刊争议度较高，建议作为补充线索。"
    return 0, "期刊需人工核对。"


def score_record(record: dict) -> tuple[int, dict]:
    text = " ".join([record.get("title", ""), record.get("abstract", ""), record.get("journal", "")]).lower()
    topic_terms = [
        "yellow river delta",
        "coastal wetland",
        "salt marsh",
        "estuarine",
        "salinity",
        "wetland",
        "soil",
        "sediment",
    ]
    microbe_terms = ["microbial community", "bacterial community", "fungal community", "bacteria", "fungi", "diversity", "composition"]
    plant_terms = ["tamarix", "suaeda", "phragmites", "vegetation", "halophyte", "rhizosphere", "habitat"]
    method_terms = ["high-throughput", "16s", "its", "sequencing", "alpha", "beta", "pcoa", "nmds", "lefse", "co-occurrence", "faprotax", "funguild"]
    abstract_logic_terms = ["little is known", "poorly understood", "unclear", "aimed", "investigated", "provide insights", "suggest"]

    counts = {
        "topic": sum(1 for t in topic_terms if t in text),
        "microbe": sum(1 for t in microbe_terms if t in text),
        "plant": sum(1 for t in plant_terms if t in text),
        "method": sum(1 for t in method_terms if t in text),
        "abstract_logic": sum(1 for t in abstract_logic_terms if t in text),
    }
    support = detect_sentence_support(record)
    quality, _ = journal_quality_score(record)
    score = (
        counts["topic"] * 5
        + counts["microbe"] * 5
        + counts["plant"] * 4
        + counts["method"] * 4
        + counts["abstract_logic"] * 3
        + len(support) * 6
        + quality
    )
    counts["support_types"] = len(support)
    counts["journal_quality"] = quality
    return score, counts


def classify_record(record: dict) -> tuple[str, str, str, int, dict]:
    exclusion = metadata_exclusion_reason(record)
    if exclusion:
        score, counts = score_record(record)
        return "D", f"排除：{exclusion}", "08_低相关暂存", score, counts

    score, counts = score_record(record)
    support = detect_sentence_support(record)
    quality, quality_note = journal_quality_score(record)

    topic_ok = counts["topic"] >= 2 and counts["microbe"] >= 2
    abstract_ok = len(support) >= 3
    method_ok = counts["method"] >= 1

    if score >= 65 and topic_ok and abstract_ok and quality >= 0:
        return "A", f"高度适合摘要写作支撑：研究对象、摘要逻辑和方法表达均较接近。{quality_note}", "01_摘要核心支撑文献", score, counts
    if score >= 38 and (topic_ok or method_ok or quality >= 10):
        return "B", f"可用于摘要背景、方法或意义表达：与用户摘要有部分结构或主题相似。{quality_note}", "02_摘要背景与方法文献", score, counts
    if score >= 25:
        return "C", f"间接相关：可暂存为句式或背景参考。{quality_note}", "08_低相关暂存", score, counts
    return "D", "排除：与摘要主题和写作逻辑的关联较弱。", "08_低相关暂存", score, counts


def classify_record_v2(record: dict) -> tuple[str, str, str, int, dict]:
    exclusion = metadata_exclusion_reason(record)
    if exclusion:
        score, counts = score_record(record)
        return "D", f"排除：{exclusion}", "08_低相关暂存", score, counts

    score, counts = score_record(record)
    support = detect_sentence_support(record)
    quality, quality_note = journal_quality_score(record)
    text = " ".join([record.get("title", ""), record.get("abstract", ""), record.get("journal", "")]).lower()

    topic_ok = counts["topic"] >= 2 and counts["microbe"] >= 2
    abstract_ok = len(support) >= 3
    method_ok = counts["method"] >= 1
    core_topic_ok = any(
        term in text
        for term in [
            "yellow river delta",
            "coastal wetland",
            "salt marsh",
            "estuarine",
            "tidal flat",
            "salinity",
            "saline",
            "halophyte",
            "tamarix",
            "suaeda",
            "phragmites",
            "rhizosphere",
        ]
    )

    if score >= 65 and topic_ok and core_topic_ok and abstract_ok and quality >= 0:
        return "A", f"高度适合摘要写作支撑：研究区、盐生植物/生境梯度、微生物对象和方法表达均较接近。{quality_note}", "01_摘要核心支撑文献", score, counts
    if score >= 38 and (topic_ok or method_ok or quality >= 10):
        return "B", f"可用于摘要背景、方法或意义表达：与用户摘要有部分结构、环境梯度或方法相似，但主题贴合度低于 A 类。{quality_note}", "02_摘要背景与方法文献", score, counts
    if score >= 25:
        return "C", f"间接相关：可暂存为句式或背景参考，不建议作为核心引用。{quality_note}", "08_低相关暂存", score, counts
    return "D", "排除：与摘要主题和写作逻辑的关联较弱。", "08_低相关暂存", score, counts


def dedupe(records: list[dict]) -> list[dict]:
    seen = set()
    output = []
    for record in records:
        key = normalize_doi(record.get("doi")) or record.get("title", "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(record)
    return output


def truncate(text: str, max_len: int = 1000) -> str:
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def write_markdown(records: list[dict], all_count: int, draft: str) -> None:
    grouped = {"A": [], "B": [], "C": []}
    for record in records:
        if record["level"] in grouped:
            grouped[record["level"]].append(record)

    lines = [
        "# 摘要支撑文献筛选结果",
        "",
        f"检索日期：{dt.date.today().isoformat()}",
        "",
        f"检索去重后文献总数：{all_count}",
        f"写入结果文献数：{len(records)}",
        f"A 类文献数量：{len(grouped['A'])}",
        f"B 类文献数量：{len(grouped['B'])}",
        f"C 类文献数量：{len(grouped['C'])}",
        "",
        "## 用户摘要草稿",
        "",
        truncate(draft, 1200),
        "",
    ]

    section_names = {
        "A": "可直接支撑摘要逻辑的 A 类文献",
        "B": "可用于摘要背景或方法表达的 B 类文献",
        "C": "仅作背景暂存的 C 类文献",
    }

    for level in ["A", "B", "C"]:
        lines.extend([f"## {section_names[level]}", ""])
        if not grouped[level]:
            lines.extend(["暂无。", ""])
            continue
        grouped[level].sort(key=lambda x: x.get("score", 0), reverse=True)
        for i, record in enumerate(grouped[level], 1):
            support = detect_sentence_support(record)
            quality_note = journal_quality_score(record)[1]
            lines.extend(
                [
                    f"### {i}. {record.get('title', '')}",
                    "",
                    f"- 作者/年份/期刊/DOI：{', '.join(record.get('authors', [])[:6])}；{record.get('year', '')}；{record.get('journal', '')}；{record.get('doi', '')}",
                    f"- 来源：{record.get('source', '')}",
                    f"- 相似度得分：{record.get('score', '')}",
                    f"- 摘要类型：{', '.join(support) if support else '需人工判断'}",
                    f"- 与用户摘要的相似点：{record.get('reason', '')}",
                    f"- 可支撑用户摘要中的哪一句：{', '.join(support) if support else '背景或方法表达需人工核对'}",
                    f"- Zotero collection 建议：{record.get('collection', '')}",
                    f"- 期刊质量提示：{quality_note}",
                    f"- 触发检索词：{record.get('query', '')}",
                    f"- URL：{record.get('url', '')}",
                    "- 摘要核心内容：",
                    "",
                    truncate(record.get("abstract", ""), 1400),
                    "",
                ]
            )

    lines.extend(
        [
            "## 可借鉴的摘要句式",
            "",
            "- 背景句：滨海湿地/黄河三角洲受陆海相互作用、盐度梯度和植被差异影响，是研究土壤微生物群落响应的重要区域。",
            "- 问题句：不同生境下细菌和真菌群落结构、潜在功能及共现关系的响应机制仍需进一步阐明。",
            "- 方法句：可采用高通量测序结合群落多样性、组成结构、环境因子相关性和功能预测分析。",
            "- 意义句：相关结果可为理解滨海湿地微生物群落组装、植物适应和生态功能维持提供依据。",
            "",
        ]
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def ris_escape(value: str) -> str:
    return clean_text(value).replace("\n", " ")


def write_ris(records: list[dict]) -> None:
    lines = []
    for record in records:
        lines.append("TY  - JOUR")
        lines.append(f"TI  - {ris_escape(record.get('title', ''))}")
        for author in record.get("authors", [])[:20]:
            lines.append(f"AU  - {ris_escape(author)}")
        if record.get("journal"):
            lines.append(f"JO  - {ris_escape(record.get('journal', ''))}")
        if record.get("year"):
            lines.append(f"PY  - {ris_escape(record.get('year', ''))}")
        if record.get("doi"):
            lines.append(f"DO  - {ris_escape(record.get('doi', ''))}")
        if record.get("url"):
            lines.append(f"UR  - {ris_escape(record.get('url', ''))}")
        if record.get("abstract"):
            lines.append(f"AB  - {ris_escape(record.get('abstract', ''))}")
        lines.append(f"N1  - Level: {record.get('level', '')}; Score: {record.get('score', '')}; Abstract support: {', '.join(detect_sentence_support(record))}; Source: {record.get('source', '')}")
        lines.append("ER  -")
        lines.append("")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RIS_PATH.write_text("\n".join(lines), encoding="utf-8")


def load_draft(args: argparse.Namespace) -> str:
    if args.abstract_file:
        return Path(args.abstract_file).read_text(encoding="utf-8")
    if args.abstract_text:
        return args.abstract_text
    return LATEST_ABSTRACT_DRAFT


def main() -> None:
    parser = argparse.ArgumentParser(description="Search related literature abstracts for thesis abstract writing.")
    parser.add_argument("--abstract-file", help="Path to a UTF-8 text file containing the thesis abstract draft.")
    parser.add_argument("--abstract-text", help="Abstract draft text. If omitted, a built-in Yellow River Delta template is used.")
    parser.add_argument("--days", type=int, default=3650, help="Search recent N days. Default: 3650.")
    parser.add_argument("--limit", type=int, default=10, help="Max records per source per query.")
    parser.add_argument("--max-queries", type=int, default=24, help="Max queries to run.")
    parser.add_argument("--mailto", default="", help="Optional email for polite OpenAlex API usage.")
    parser.add_argument("--keep-seen", action="store_true", help="Use output/abstract_seen_dois.txt to avoid repeated DOI results.")
    args = parser.parse_args()

    draft = load_draft(args)
    queries = extract_draft_queries(draft)[: args.max_queries]
    seen_dois = read_seen(SEEN_PATH) if args.keep_seen else set()
    all_records: list[dict] = []

    for query in queries:
        print(f"Searching Crossref: {query}")
        try:
            all_records.extend(search_crossref(query, args.days, args.limit))
        except Exception as exc:
            print(f"Warning: Crossref failed: {exc}")
        time.sleep(0.8)

        print(f"Searching OpenAlex: {query}")
        try:
            all_records.extend(search_openalex(query, args.days, args.limit, args.mailto))
        except Exception as exc:
            print(f"Warning: OpenAlex failed: {exc}")
        time.sleep(1.2)

        print(f"Searching Semantic Scholar: {query}")
        try:
            all_records.extend(search_semantic_scholar(query, args.days, args.limit))
        except Exception as exc:
            print(f"Warning: Semantic Scholar failed: {exc}")
        time.sleep(1.5)

    all_records = dedupe(all_records)
    output_records = []
    updated_seen = set(seen_dois)

    for record in all_records:
        doi = normalize_doi(record.get("doi"))
        if doi and doi in seen_dois:
            continue
        level, reason, collection, score, detail = classify_record_v2(record)
        record["level"] = level
        record["reason"] = reason
        record["collection"] = collection
        record["score"] = score
        record["score_detail"] = detail
        if level != "D":
            output_records.append(record)
        if doi:
            updated_seen.add(doi)

    output_records.sort(key=lambda x: x.get("score", 0), reverse=True)
    write_markdown(output_records, len(all_records), draft)
    write_ris(output_records)
    write_seen(SEEN_PATH, updated_seen)

    print("Done.")
    print(f"Markdown: {MD_PATH}")
    print(f"RIS: {RIS_PATH}")
    print(f"Records written: {len(output_records)}")


if __name__ == "__main__":
    main()
