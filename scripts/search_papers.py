from __future__ import annotations

import argparse
import datetime as dt
import re
import textwrap
import time
from pathlib import Path
from typing import Any

import requests
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KEYWORDS = ROOT / "config" / "keywords.yaml"
DEFAULT_SKILL = ROOT / "skills" / "soil-nitrogen-literature-curation" / "SKILL.md"
DEFAULT_OUTPUT = ROOT / "output"


def load_keywords(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing keyword config: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    terms: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, str):
            terms.append(value)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, dict):
            for item in value.values():
                collect(item)

    collect(data)
    cleaned = [term.strip() for term in terms if term and term.strip()]
    if not cleaned:
        raise ValueError(f"No keywords found in {path}")
    return list(dict.fromkeys(cleaned))


def load_skill_rules(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing curation skill: {path}")
    return path.read_text(encoding="utf-8")


def normalize_doi(doi: str | None) -> str:
    if not doi:
        return ""
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi


def inverted_index_to_text(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        words.extend((position, word) for position in positions)
    return " ".join(word for _, word in sorted(words))


def as_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item)
    if value is None:
        return ""
    return str(value)


def build_query(keywords: list[str], max_terms: int = 16) -> str:
    priority_terms = keywords[:max_terms]
    return " OR ".join(f'"{term}"' if " " in term else term for term in priority_terms)


def fetch_openalex(keywords: list[str], days: int, limit: int, mailto: str | None) -> list[dict[str, Any]]:
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    query = build_query(keywords)
    params = {
        "search": query,
        "filter": f"from_publication_date:{since},type:article",
        "per-page": min(limit, 200),
        "sort": "publication_date:desc",
    }
    if mailto:
        params["mailto"] = mailto

    response = requests.get("https://api.openalex.org/works", params=params, timeout=30)
    response.raise_for_status()
    works = response.json().get("results", [])

    papers = []
    for work in works:
        authors = [
