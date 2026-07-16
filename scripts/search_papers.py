#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Daily Literature Tracker

Purpose:
Search for papers similar to the user's research direction:
Yellow River Delta / coastal wetland soil microorganisms, vegetation types,
coastal-inland or salinity gradients, bacterial and fungal communities,
16S/ITS sequencing, FAPROTAX, FUNGuild, and environmental drivers such as EC,
salinity, salt content, and pH.

Main idea:
This is not a strict keyword intersection filter.
It is a similarity-oriented literature radar.

Sources:
1. OpenAlex API
2. Semantic Scholar Graph API
3. Crossref API

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


# 你认可的“方向样本”。这些不是必须完全同领域，但它们代表你想要的文献类型。
SEED_TITLES = [
    "Soil microbial community structure under different vegetation types in Yellow River Delta wetlands",
    "Bacterial and fungal communities in coastal wetland soils along a salinity gradient",
    "Vegetation and soil salinity shape bacterial and fungal communities in coastal wetlands",
    "Distance from coastline drives soil microbial diversity in coastal wetlands",
    "FAPROTAX and FUNGuild reveal microbial functional profiles in wetland soils",
    "Soil bacterial and fungal diversity in saline wetlands with different vegetation types",
    "Environmental factors shape soil microbial community composition in coastal wetlands",
    "Tamarix chinensis Suaeda salsa Phragmites australis soil microbial community",
]


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

    # Clearly off-topic engineering / treatment systems
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
    value = html.unescape(str(value))
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_doi(doi: Optional[str]) -> str:
    if not doi:
        return ""
    doi = doi.strip()
    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("doi:", "")
    return doi.lower()


def load_keywords() -> List[str]:
    if not CONFIG_PATH.exists():
        print(f"Warning: missing {CONFIG_PATH}. The script will use built-in seed titles and queries.")
        return []

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


def build_queries(keywords: List[str], max_queries: int = 60) -> List[str]:
    """
    Build search queries.

    This version intentionally mixes:
    1. seed-title-like queries,
    2. mechanism queries,
    3. ecosystem queries,
    4. gene/process queries.
    """

    preferred = [
        # Seed-title-like queries
        "Yellow River Delta wetland soil microbial community",
        "Yellow River Delta coastal wetland bacterial fungal community",
        "vegetation type soil bacterial fungal community coastal wetland",
        "distance from coastline soil microbial diversity coastal wetland",
        "salinity gradient bacterial fungal community coastal wetland soil",
        "FAPROTAX FUNGuild wetland soil microbial community",

        # Core topic
        "soil bacterial fungal community vegetation type saline wetland",
        "soil microbial community composition coastal saline wetland",
        "soil microbial diversity coastal inland gradient",
        "bacterial and fungal communities wetland soil salinity",
        "16S ITS sequencing saline wetland soil microbial community",
        "high-throughput sequencing soil bacterial fungal community wetland",

        # Wetland / coastal wetland / salt marsh / Yellow River Delta
        "coastal wetland soil microbial community",
        "wetland soil bacterial community fungal community",
        "salt marsh soil microbial community vegetation",
        "tidal wetland microbial community salinity",
        "estuarine wetland soil microbial diversity",
        "coastal saline wetland microbial community",
        "coastal soil microbial community salinity gradient",
        "Yellow River Delta wetland microbial community",
        "Yellow River Delta saline soil microbial community",

        # Vegetation and rhizosphere
        "Tamarix chinensis soil microbial community",
        "Suaeda salsa soil microbial community",
        "Phragmites australis soil microbial community",
        "Tamarix chinensis Suaeda salsa Phragmites australis soil microorganisms",
        "wetland vegetation soil microbial community coastal wetland",
        "halophyte rhizosphere soil microbial community",
        "salt-tolerant vegetation soil microbial community",
        "reed wetland soil fungal bacterial community",
        "tamarisk wetland soil microbial community",

        # Environmental drivers
        "soil salinity microbial community coastal wetland",
        "soil electrical conductivity microbial community",
        "soil EC salinity bacterial fungal community",
        "salt content soil microbial community wetland",
        "soil pH salinity microbial community wetland",
        "soil physicochemical properties bacterial fungal community",
        "vegetation salinity interaction soil microbial community",
        "site vegetation interaction soil microbial community",

        # Community statistics and functional prediction
        "alpha diversity beta diversity soil microbial community coastal wetland",
        "PCoA NMDS Bray-Curtis soil microbial community wetland",
        "PERMANOVA ANOSIM soil microbial community vegetation wetland",
        "UpSet Venn OTU bacterial fungal community wetland soil",
        "FAPROTAX predicted bacterial function wetland soil",
        "FUNGuild fungal trophic mode wetland soil",
        "saprotroph pathotroph symbiotroph coastal wetland soil fungi",
        "Ascomycota Basidiomycota wetland soil fungal community",
        "Proteobacteria Chloroflexi Actinobacteriota wetland soil bacterial community",

        # Supporting nitrogen context, not the main filter
        "wetland soil nitrogen cycling microbial community",
        "coastal wetland nitrogen cycling bacterial community",
        "salt marsh nitrogen cycling microbial community",
        "FAPROTAX nitrogen cycling wetland soil microbial community",
    ]

    merged = SEED_TITLES + preferred + keywords

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
    """
    Search OpenAlex by query.
    """

    from_date = (dt.date.today() - dt.timedelta(days=days)).isoformat()

    params = {
        "search": query,
        "filter": f"from_publication_date:{from_date},type:article",
        "per-page": min(limit, 200),
        "sort": "relevance_score:desc",
    }

    if mailto:
        params["mailto"] = mailto

    url = "https://api.openalex.org/works"
    response = requests.get(url, params=params, timeout=45)
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
                "source": "OpenAlex",
            }
        )

    return records


def search_semantic_scholar(query: str, days: int, limit: int) -> List[Dict]:
    """
    Search Semantic Scholar by query.
    Semantic Scholar is useful for semantically related papers.
    """

    current_year = dt.date.today().year
    min_year = current_year - max(1, int(days / 365)) - 1

    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,authors,year,venue,abstract,url,externalIds,publicationDate,citationCount,influentialCitationCount",
        "year": f"{min_year}-",
    }

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    try:
        response = requests.get(url, params=params, timeout=45)
        if response.status_code == 429:
            print("Warning: Semantic Scholar rate limit. Skipping this query.")
            return []
        response.raise_for_status()
    except Exception as exc:
        print(f"Warning: Semantic Scholar query failed: {query}")
        print(f"Reason: {exc}")
        return []

    data = response.json()
    records = []

    for item in data.get("data", []):
        title = clean_text(item.get("title"))
        if not title:
            continue

        external = item.get("externalIds") or {}
        doi = normalize_doi(external.get("DOI"))

        authors = []
        for author in item.get("authors", []) or []:
            name = author.get("name")
            if name:
                authors.append(clean_text(name))

        records.append(
            {
                "title": title,
                "authors": authors,
                "year": str(item.get("year") or ""),
                "journal": clean_text(item.get("venue") or ""),
                "doi": doi,
                "abstract": clean_text(item.get("abstract") or ""),
                "url": item.get("url") or "",
                "query": query,
                "source": "Semantic Scholar",
                "citation_count": item.get("citationCount") or 0,
                "influential_citation_count": item.get("influentialCitationCount") or 0,
            }
        )

    return records


def search_crossref_by_title(title: str, limit: int = 5) -> List[Dict]:
    """
    Use Crossref to complement exact or near-exact seed title search.
    """

    params = {
        "query.title": title,
        "rows": limit,
        "select": "title,author,published-print,published-online,container-title,DOI,abstract,URL",
    }

    url = "https://api.crossref.org/works"

    try:
        response = requests.get(url, params=params, timeout=45)
        response.raise_for_status()
    except Exception as exc:
        print(f"Warning: Crossref query failed: {title}")
        print(f"Reason: {exc}")
        return []

    data = response.json()
    items = data.get("message", {}).get("items", [])

    records = []

    for item in items:
        titles = item.get("title") or []
        record_title = clean_text(titles[0]) if titles else ""
        if not record_title:
            continue

        journal_list = item.get("container-title") or []
        journal = clean_text(journal_list[0]) if journal_list else ""

        year = ""
        for key in ["published-print", "published-online"]:
            date_parts = item.get(key, {}).get("date-parts")
            if date_parts and date_parts[0]:
                year = str(date_parts[0][0])
                break

        authors = []
        for a in item.get("author", []) or []:
            given = a.get("given", "")
            family = a.get("family", "")
            name = clean_text(f"{given} {family}")
            if name:
                authors.append(name)

        records.append(
            {
                "title": record_title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": normalize_doi(item.get("DOI")),
                "abstract": clean_text(item.get("abstract") or ""),
                "url": item.get("URL") or "",
                "query": title,
                "source": "Crossref",
            }
        )

    return records


def score_record(record: Dict) -> Tuple[int, Dict[str, int]]:
    """
    Score record by similarity to the user's research direction.
    This is intentionally broader than strict keyword matching.
    """

    text = " ".join(
        [
            record.get("title", ""),
            record.get("abstract", ""),
            record.get("journal", ""),
        ]
    ).lower()

    if any(term in text for term in EXCLUDE_TERMS):
        return -999, {"excluded": 1}

    seed_signal_terms = [
        "yellow river delta",
        "coastal wetland",
        "salinity gradient",
        "distance from coastline",
        "vegetation type",
        "bacterial and fungal communities",
        "soil microbial community",
        "faprotax",
        "funguild",
        "trophic mode",
    ]

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
        "desert steppe",
        "tea soil",
        "acidified tea soil",
        "yellow river delta",
        "coastal-inland",
        "coastal inland",
    ]

    soil_terms = [
        "soil",
        "soils",
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
        "bacterial diversity",
        "fungal diversity",
        "alpha diversity",
        "beta diversity",
        "otu",
        "otus",
        "16s",
        "16s rrna",
        "its",
        "amplicon sequencing",
        "high-throughput sequencing",
    ]

    nitrogen_terms = [
        "nitrogen",
        "nitrogen cycling",
        "nitrogen cycle",
        "nitrogen-cycle",
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
        "predicted bacterial function",
        "fungal guild",
        "fungal trophic",
        "trophic mode",
        "saprotroph",
        "pathotroph",
        "symbiotroph",
        "pathogen",
        "nitrogen metabolism",
        "carbon-nitrogen cycling",
        "c-n cycling",
        "carbon and nitrogen cycling",
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
        "wetland vegetation",
        "plant community",
        "reed",
        "tamarisk",
    ]

    network_terms = [
        "co-occurrence network",
        "microbial network",
        "network complexity",
        "community assembly",
        "microbial interaction",
        "bacterial-fungal",
        "bacteria-fungi",
        "pcoa",
        "nmds",
        "bray-curtis",
        "permanova",
        "anosim",
        "upset",
        "venn",
        "two-way anova",
    ]

    environment_terms = [
        "salinity",
        "salt content",
        "electrical conductivity",
        "soil ec",
        "ec",
        "ph",
        "physicochemical properties",
        "environmental factor",
        "environmental factors",
        "environmental driver",
        "environmental drivers",
        "distance from coastline",
        "coastline",
        "coastal-inland gradient",
        "salinity gradient",
    ]

    taxa_terms = [
        "proteobacteria",
        "chloroflexi",
        "actinobacteriota",
        "bacteroidota",
        "gemmatimonadota",
        "acidobacteriota",
        "desulfobacterota",
        "ascomycota",
        "basidiomycota",
        "chytridiomycota",
        "rozellomycota",
    ]

    counts = {
        "seed": sum(1 for term in seed_signal_terms if term in text),
        "ecosystem": sum(1 for term in ecosystem_terms if term in text),
        "soil": sum(1 for term in soil_terms if term in text),
        "microbe": sum(1 for term in microbe_terms if term in text),
        "nitrogen": sum(1 for term in nitrogen_terms if term in text),
        "addition": sum(1 for term in addition_terms if term in text),
        "function": sum(1 for term in function_terms if term in text),
        "vegetation": sum(1 for term in vegetation_terms if term in text),
        "network": sum(1 for term in network_terms if term in text),
        "environment": sum(1 for term in environment_terms if term in text),
        "taxa": sum(1 for term in taxa_terms if term in text),
    }

    score = (
        counts["seed"] * 8
        + counts["microbe"] * 5
        + counts["ecosystem"] * 4
        + counts["vegetation"] * 4
        + counts["environment"] * 4
        + counts["function"] * 3
        + counts["microbe"] * 3
        + counts["soil"] * 3
        + counts["taxa"] * 2
        + counts["network"] * 2
        + counts["nitrogen"] * 1
        + counts["addition"] * 1
    )

    # Bonus: title-level match is more important than query-only match
    title = record.get("title", "").lower()
    if "yellow river delta" in title:
        score += 12
    if "coastal wetland" in title or "salt marsh" in title or "wetland" in title:
        score += 8
    if "bacterial" in title and "fungal" in title:
        score += 8
    if "microbial community" in title or "microbial communities" in title:
        score += 6
    if "salinity" in title or "electrical conductivity" in title or "soil ec" in title:
        score += 6
    if "vegetation" in title or "tamarix" in title or "suaeda" in title or "phragmites" in title:
        score += 4
    if "faprotax" in title or "funguild" in title:
        score += 4

    return score, counts


def classify_record(record: Dict) -> Tuple[str, str, str, int, Dict[str, int]]:
    score, counts = score_record(record)

    if score < 0:
        return (
            "D",
            "排除：主题更接近医学、食品、动物、工业或其他明显偏离滨海湿地土壤微生物方向的研究。",
            "08_低相关暂存",
            score,
            counts,
        )

    # A 类：与种子文献或研究主题高度相似
    core_topic_signal = (
        counts.get("ecosystem", 0) >= 2
        or counts.get("vegetation", 0) >= 1
        or counts.get("seed", 0) >= 2
        or counts.get("function", 0) >= 2
    )

    if score >= 22 and core_topic_signal:
        collection = "01_黄河三角洲滨海湿地"
        if counts.get("function", 0) >= 2:
            collection = "06_FAPROTAX和功能预测"
        elif counts.get("vegetation", 0) >= 2:
            collection = "02_植被类型与土壤微生物"
        elif counts.get("environment", 0) >= 2:
            collection = "03_盐度EC和环境因子"
        return (
            "A",
            "高度相关：与当前论文在黄河三角洲/滨海湿地、植被类型、盐度或距海梯度、土壤细菌/真菌群落、多样性或功能预测等方向高度相似，建议优先阅读。",
            collection,
            score,
            counts,
        )

    # B 类：相似研究，适合讨论和扩展阅读
    if score >= 13:
        collection = "07_测序与群落分析方法"
        if counts.get("function", 0) >= 1:
            collection = "06_FAPROTAX和功能预测"
        elif counts.get("vegetation", 0) >= 1:
            collection = "02_植被类型与土壤微生物"
        elif counts.get("environment", 0) >= 1:
            collection = "03_盐度EC和环境因子"
        return (
            "B",
            "中等相关：与当前论文在土壤微生物、滨海/盐碱环境、植被影响、盐度 EC 或群落分析方法中的部分方向相似，可用于讨论或补充阅读。",
            collection,
            score,
            counts,
        )

    # C 类：背景相关
    if score >= 8:
        return (
            "C",
            "间接相关：与湿地环境、土壤微生物群落、植被、盐度梯度或功能预测有一定联系，可作为背景文献暂存。",
            "08_低相关暂存",
            score,
            counts,
        )

    return (
        "D",
        "排除：与黄河三角洲/滨海湿地、盐碱土、植被梯度、土壤细菌/真菌群落或功能预测的关联较弱。",
        "08_低相关暂存",
        score,
        counts,
    )


def deduplicate_records(records: List[Dict]) -> List[Dict]:
    seen = set()
    output = []

    for r in records:
        key = normalize_doi(r.get("doi")) or r.get("title", "").lower()
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

        # Sort by similarity score
        grouped[level].sort(key=lambda x: x.get("score", 0), reverse=True)

        for i, r in enumerate(grouped[level], 1):
            lines.append(f"### {i}. {r.get('title', '')}")
            lines.append("")
            lines.append(f"- 来源：{r.get('source', '')}")
            lines.append(f"- 相似度得分：{r.get('score', '')}")
            lines.append(f"- 作者：{', '.join(r.get('authors', [])[:6])}")
            lines.append(f"- 年份：{r.get('year', '')}")
            lines.append(f"- 期刊：{r.get('journal', '')}")
            lines.append(f"- DOI：{r.get('doi', '')}")
            lines.append(f"- URL：{r.get('url', '')}")
            lines.append(f"- 触发检索词：{r.get('query', '')}")
            lines.append(f"- 建议 Zotero collection：{r.get('collection', '')}")
            lines.append(f"- 推荐理由：{r.get('reason', '')}")
            lines.append(f"- 命中维度：{r.get('score_detail', {})}")

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

        # Put classification into notes
        if r.get("level") or r.get("score"):
            lines.append(f"N1  - Level: {r.get('level', '')}; Score: {r.get('score', '')}; Source: {r.get('source', '')}")

        lines.append("ER  -")
        lines.append("")

    with open(RIS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mailto", default="", help="Your email for polite API usage.")
    parser.add_argument("--days", type=int, default=1825, help="Search papers published in recent N days.")
    parser.add_argument("--limit", type=int, default=20, help="Max records per query per source.")
    parser.add_argument("--max-queries", type=int, default=60, help="Max queries to run.")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    check_skill_file()
    keywords = load_keywords()
    queries = build_queries(keywords, max_queries=args.max_queries)

    seen_dois = load_seen_dois()
    all_records = []

    # 1. Exact / near-exact seed title search through Crossref
    print("Searching seed titles through Crossref...")
    for title in SEED_TITLES:
        all_records.extend(search_crossref_by_title(title, limit=5))
        time.sleep(0.3)

    # 2. OpenAlex + Semantic Scholar
    for query in queries:
        print(f"Searching OpenAlex: {query}")
        try:
            records = search_openalex(query, args.mailto, args.days, args.limit)
            all_records.extend(records)
        except Exception as exc:
            print(f"Warning: OpenAlex failed query: {query}")
            print(f"Reason: {exc}")

        time.sleep(0.3)

        print(f"Searching Semantic Scholar: {query}")
        try:
            records = search_semantic_scholar(query, args.days, args.limit)
            all_records.extend(records)
        except Exception as exc:
            print(f"Warning: Semantic Scholar failed query: {query}")
            print(f"Reason: {exc}")

        time.sleep(0.6)

    all_records = deduplicate_records(all_records)

    new_records = []

    for record in all_records:
        doi = normalize_doi(record.get("doi"))

        if doi and doi in seen_dois:
            continue

        level, reason, collection, score, score_detail = classify_record(record)
        record["level"] = level
        record["reason"] = reason
        record["collection"] = collection
        record["score"] = score
        record["score_detail"] = score_detail

        if level != "D":
            new_records.append(record)

        if doi:
            seen_dois.add(doi)

    # Sort all retained records by score
    new_records.sort(key=lambda x: x.get("score", 0), reverse=True)

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
