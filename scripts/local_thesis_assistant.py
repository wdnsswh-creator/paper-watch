#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Local Thesis Assistant

这个脚本用于把本地数据、图表和 Zotero 文献整合成硕士论文写作材料。

功能：
1. 扫描 F:/2026512玻璃缸 下的数据文件和图片文件；
2. 读取 Zotero 导出的 RIS 或 BibTeX 文件；
3. 根据用户研究方向生成：
   - 研究方案
   - 论文框架
   - 数据分析写作提示
   - 章节/小节/文献述评结尾段 skill
4. 输出到 F:/2026512玻璃缸/thesis_outputs/

使用前提：
- 你需要先从 Zotero 导出一个 RIS 或 BibTeX 文件，放到 F:/2026512玻璃缸/
- 文件名建议叫：zotero_export.ris 或 zotero_export.bib
"""

import os
import re
import json
from pathlib import Path
from datetime import date
from typing import List, Dict, Any

import pandas as pd


# =========================
# 1. 用户路径设置
# =========================

BASE_DIR = Path(r"F:\2026512玻璃缸")
OUTPUT_DIR = BASE_DIR / "thesis_outputs"

ZOTERO_RIS = BASE_DIR / "zotero_export.ris"
ZOTERO_BIB = BASE_DIR / "zotero_export.bib"


# =========================
# 2. 用户研究主题设置
# =========================

PROJECT_INFO = {
    "研究题目": "滨海湿地土壤氮转化过程对不同形态和水平氮素添加的响应及其调控机制",
    "研究对象": "滨海湿地土壤微生物群落与土壤氮循环功能基因",
    "研究区域": "黄河三角洲滨海湿地",
    "实验处理": "不同氮形态和不同氮添加水平，包括 NH4+-N 添加、NO3--N 添加及其梯度处理",
    "核心指标": [
        "土壤氮循环功能基因",
        "微生物群落结构",
        "氮循环模块",
        "土壤理化性质",
        "氮转化过程",
        "共现网络",
        "RDA/相关性分析",
    ],
    "重点功能基因": [
        "pmoA-amoA",
        "pmoB-amoB",
        "pmoC-amoC",
        "hao",
        "napA",
        "nirK",
        "nirS",
        "norC",
        "norB",
        "nosZ",
        "nrfA",
        "nifD",
        "nifH",
        "nifK",
    ],
    "氮循环过程": [
        "硝化",
        "反硝化",
        "DNRA",
        "固氮",
        "氨氧化",
        "硝酸盐还原",
        "氮矿化",
    ],
}


# =========================
# 3. 基础工具函数
# =========================

def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            return path.read_text(encoding="gbk", errors="ignore")
        except Exception:
            return ""


def safe_preview_dataframe(path: Path, max_rows: int = 8) -> Dict[str, Any]:
    result = {
        "file": str(path),
        "columns": [],
        "shape": None,
        "preview": "",
        "error": "",
    }

    try:
        if path.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(path, encoding="utf-8")
            except Exception:
                df = pd.read_csv(path, encoding="gbk")
        elif path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(path)
        else:
            return result

        result["columns"] = list(df.columns)
        result["shape"] = df.shape
        result["preview"] = df.head(max_rows).to_string(index=False)
    except Exception as e:
        result["error"] = str(e)

    return result


# =========================
# 4. 扫描本地数据和图表
# =========================

def scan_project_files() -> Dict[str, List[Path]]:
    if not BASE_DIR.exists():
        raise FileNotFoundError(f"找不到路径：{BASE_DIR}")

    file_groups = {
        "data_files": [],
        "figure_files": [],
        "document_files": [],
        "other_files": [],
    }

    data_ext = [".csv", ".xlsx", ".xls", ".txt"]
    fig_ext = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"]
    doc_ext = [".docx", ".doc", ".md"]

    for path in BASE_DIR.rglob("*"):
        if not path.is_file():
            continue

        # 跳过输出文件夹
        if "thesis_outputs" in str(path):
            continue

        ext = path.suffix.lower()

        if ext in data_ext:
            file_groups["data_files"].append(path)
        elif ext in fig_ext:
            file_groups["figure_files"].append(path)
        elif ext in doc_ext:
            file_groups["document_files"].append(path)
        else:
            file_groups["other_files"].append(path)

    return file_groups


# =========================
# 5. 读取 Zotero 导出文献
# =========================

def parse_ris(path: Path) -> List[Dict[str, str]]:
    text = read_text_file(path)
    if not text.strip():
        return []

    records = []
    current = {}

    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue

        if line.startswith("TY  -"):
            current = {"type": line.replace("TY  -", "").strip()}
        elif line.startswith("TI  -"):
            current["title"] = line.replace("TI  -", "").strip()
        elif line.startswith("T1  -"):
            current["title"] = line.replace("T1  -", "").strip()
        elif line.startswith("AU  -"):
            current.setdefault("authors", [])
            current["authors"].append(line.replace("AU  -", "").strip())
        elif line.startswith("PY  -"):
            current["year"] = line.replace("PY  -", "").strip()
        elif line.startswith("JO  -") or line.startswith("JF  -"):
            current["journal"] = line.split("  -", 1)[-1].strip()
        elif line.startswith("DO  -"):
            current["doi"] = line.replace("DO  -", "").strip()
        elif line.startswith("AB  -"):
            current["abstract"] = line.replace("AB  -", "").strip()
        elif line.startswith("ER  -"):
            if current:
                if isinstance(current.get("authors"), list):
                    current["authors"] = "; ".join(current["authors"])
                records.append(current)
            current = {}

    return records


def parse_bib(path: Path) -> List[Dict[str, str]]:
    text = read_text_file(path)
    if not text.strip():
        return []

    entries = re.split(r"\n@", text)
    records = []

    for entry in entries:
        if not entry.strip():
            continue

        item = {}
        title = re.search(r"title\s*=\s*[{'\"](.+?)[}'\"],?\s*\n", entry, re.S | re.I)
        year = re.search(r"year\s*=\s*[{'\"]?(\d{4})", entry, re.I)
        journal = re.search(r"journal\s*=\s*[{'\"](.+?)[}'\"],?\s*\n", entry, re.S | re.I)
        doi = re.search(r"doi\s*=\s*[{'\"](.+?)[}'\"],?\s*\n", entry, re.S | re.I)
        abstract = re.search(r"abstract\s*=\s*[{'\"](.+?)[}'\"],?\s*\n", entry, re.S | re.I)
        author = re.search(r"author\s*=\s*[{'\"](.+?)[}'\"],?\s*\n", entry, re.S | re.I)

        if title:
            item["title"] = re.sub(r"\s+", " ", title.group(1)).strip()
        if year:
            item["year"] = year.group(1).strip()
        if journal:
            item["journal"] = re.sub(r"\s+", " ", journal.group(1)).strip()
        if doi:
            item["doi"] = doi.group(1).strip()
        if abstract:
            item["abstract"] = re.sub(r"\s+", " ", abstract.group(1)).strip()
        if author:
            item["authors"] = re.sub(r"\s+", " ", author.group(1)).strip()

        if item.get("title"):
            records.append(item)

    return records


def load_zotero_records() -> List[Dict[str, str]]:
    if ZOTERO_RIS.exists():
        return parse_ris(ZOTERO_RIS)

    if ZOTERO_BIB.exists():
        return parse_bib(ZOTERO_BIB)

    return []


# =========================
# 6. 文献主题分析
# =========================

def classify_literature(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    classified = []

    for r in records:
        text = " ".join([
            r.get("title", ""),
            r.get("abstract", ""),
            r.get("journal", ""),
        ]).lower()

        tags = []

        if any(x in text for x in ["metagenomic", "metagenomics", "shotgun", "functional gene", "functional genes"]):
            tags.append("宏基因组/功能基因")

        if any(x in text for x in ["nitrogen addition", "nitrogen deposition", "nitrogen enrichment", "fertilization"]):
            tags.append("氮添加/氮沉降")

        if any(x in text for x in ["nitrification", "denitrification", "dnra", "nitrogen fixation", "ammonia oxidation", "nitrate reduction"]):
            tags.append("氮循环过程")

        if any(x in text for x in ["wetland", "salt marsh", "coastal", "estuarine", "tidal"]):
            tags.append("滨海湿地/盐沼")

        if any(x in text for x in ["spartina", "phragmites", "suaeda", "tamarix", "halophyte"]):
            tags.append("湿地植被/盐生植物")

        if any(x in text for x in ["microbial community", "bacterial community", "fungal community", "microbiome"]):
            tags.append("微生物群落结构")

        if not tags:
            tags.append("背景文献")

        r2 = dict(r)
        r2["tags"] = "；".join(tags)
        classified.append(r2)

    return classified


# =========================
# 7. 自动生成研究方案
# =========================

def generate_research_plan(records: List[Dict[str, str]], file_groups: Dict[str, List[Path]]) -> str:
    today = date.today().isoformat()

    key_lit_titles = "\n".join(
        [f"- {r.get('title', '')}（{r.get('year', '')}，{r.get('tags', '')}）" for r in records[:20]]
    )

    data_files = "\n".join([f"- {p.name}" for p in file_groups["data_files"][:50]])
    figure_files = "\n".join([f"- {p.name}" for p in file_groups["figure_files"][:80]])

    text = f"""# 研究方案自动草案

生成日期：{today}

## 一、研究题目

{PROJECT_INFO["研究题目"]}

## 二、研究背景与问题提出

滨海湿地是陆海相互作用强烈的生态系统，土壤盐度、水分、pH、无机氮形态和植被类型共同塑造微生物群落结构及其功能潜力。外源氮输入不仅改变土壤氮素供给水平，还可能通过不同氮形态对硝化、反硝化、DNRA 和固氮等关键氮转化过程产生差异影响。因此，将氮添加形态、添加水平、土壤微生物群落与土壤氮循环功能基因结合起来分析，有助于揭示滨海湿地氮循环过程对外源氮输入的响应机制。

## 三、研究目标

本研究拟围绕“不同形态和水平氮添加如何影响滨海湿地土壤氮转化过程及其微生物调控机制”这一核心问题，结合土壤理化性质、微生物群落结构、土壤氮循环功能基因丰度、功能模块和环境因子关联分析，系统阐明不同氮添加处理下土壤氮循环功能基因和氮转化过程的响应特征。

## 四、科学问题

1. 不同氮形态添加是否会改变滨海湿地土壤微生物群落结构和功能潜力？
2. 不同氮添加水平是否会引起土壤氮循环功能基因丰度的梯度响应？
3. NH4+-N 与 NO3--N 添加对硝化、反硝化、DNRA 和固氮相关基因的影响是否存在差异？
4. 土壤环境因子，尤其是 NH4+-N、NO3--N、EC、pH 和含水率，是否参与调控土壤氮循环功能基因的变化？
5. 土壤氮循环功能基因变化能否解释不同氮添加处理下潜在氮转化过程的差异？

## 五、研究内容

### 研究内容一：不同氮添加处理下土壤理化性质变化

重点分析不同氮形态和氮添加水平对土壤含水率、EC、pH、NH4+-N、NO3--N 等环境因子的影响，为解释土壤氮循环功能基因变化提供环境背景。

### 研究内容二：不同氮添加处理下土壤微生物群落结构变化

结合 Alpha 多样性、Beta 多样性、群落组成和差异分析，判断氮添加是否显著改变微生物群落多样性和结构。

### 研究内容三：土壤氮循环功能基因对不同氮形态和水平添加的响应

围绕 pmoA-amoA、pmoB-amoB、pmoC-amoC、hao、napA、nirK、nirS、norB、norC、nosZ、nrfA、nifH、nifD、nifK 等基因，分析其在不同处理间的变化趋势和显著性差异。

### 研究内容四：环境因子与土壤氮循环功能基因的耦合关系

通过相关性热图、RDA、Mantel 或回归分析，揭示 NH4+-N、NO3--N、EC、pH、MC 等因子与关键土壤氮循环功能基因之间的关系。

### 研究内容五：不同氮添加处理下氮循环过程的潜在机制解释

结合功能基因、氮循环模块和环境因子，构建“氮形态/添加水平—环境因子—土壤氮循环功能基因—氮转化过程”的解释框架。

## 六、已有数据和图表基础

### 数据文件

{data_files if data_files else "当前未扫描到数据文件。"}

### 图表文件

{figure_files if figure_files else "当前未扫描到图表文件。"}

## 七、Zotero 文献基础

当前已读取 Zotero 导出文献 {len(records)} 篇。前 20 篇文献如下：

{key_lit_titles if key_lit_titles else "当前未读取到 Zotero 导出文献。请先从 Zotero 导出 RIS 或 BibTeX 文件到 F:/2026512玻璃缸。"}

## 八、预期创新点

1. 将不同氮形态和氮添加水平同时纳入滨海湿地土壤氮循环研究框架；
2. 从土壤氮循环功能基因角度解释氮转化过程变化；
3. 将土壤环境因子、微生物群落和功能基因响应进行耦合分析；
4. 为理解滨海湿地外源氮输入背景下氮循环稳定性和生态功能变化提供机制依据。

## 九、技术路线

氮添加处理设置 → 土壤样品采集 → 土壤理化性质测定 → 宏基因组/微生物数据分析 → 土壤氮循环功能基因筛选 → Alpha/Beta 多样性分析 → 功能模块与关键基因差异分析 → 环境因子关联分析 → 构建氮转化调控机制模型。
"""

    return text


# =========================
# 8. 自动生成论文框架
# =========================

def generate_thesis_outline() -> str:
    text = f"""# 硕士论文框架自动草案

## 摘要

概述研究背景、研究目的、实验设计、主要方法、核心结果和结论。

## 第一章 绪论

### 1.1 研究背景

围绕滨海湿地氮循环、外源氮输入、氮添加形态与水平、微生物介导的氮转化过程展开。

### 1.2 国内外研究进展

#### 1.2.1 滨海湿地氮循环过程研究进展

重点讨论滨海湿地盐度、水分、植被和氧化还原环境对氮循环过程的影响。

#### 1.2.2 氮添加对土壤微生物群落的影响

重点讨论氮添加、氮沉降和氮富集对土壤微生物群落结构与功能的影响。

#### 1.2.3 土壤氮循环功能基因研究进展

重点讨论硝化、反硝化、DNRA 和固氮相关功能基因，包括 pmoA-amoA、hao、nirK、nirS、norB、nosZ、nrfA 和 nifH 等。

#### 1.2.4 不同氮形态和氮添加水平对氮循环过程的影响

突出 NH4+-N 与 NO3--N 添加可能通过底物供给差异影响不同氮转化过程。

### 1.3 研究目的与意义

提出本研究旨在揭示不同氮形态和水平添加下滨海湿地土壤氮转化过程及土壤氮循环功能基因的响应机制。

### 1.4 研究内容与技术路线

概述实验设计、分析指标和技术路线。

## 第二章 材料与方法

### 2.1 研究区概况

介绍黄河三角洲滨海湿地自然地理、气候、土壤盐碱特征和植被背景。

### 2.2 实验设计与样品采集

介绍氮添加形态、氮添加水平、处理设置和样品采集方法。

### 2.3 土壤理化性质测定

介绍 pH、EC、含水率、NH4+-N、NO3--N 等指标测定方法。

### 2.4 微生物和宏基因组分析方法

介绍测序、质控、注释、土壤氮循环功能基因筛选和功能模块分析。

### 2.5 统计分析

介绍差异显著性分析、Alpha/Beta 多样性分析、RDA、相关性分析和可视化方法。

## 第三章 不同氮添加处理下土壤环境因子变化

### 3.1 土壤含水率、pH 和 EC 的变化

### 3.2 土壤 NH4+-N 和 NO3--N 的变化

### 3.3 不同氮形态和水平对土壤环境因子的综合影响

### 3.4 小结

## 第四章 不同氮添加处理下土壤微生物群落结构变化

### 4.1 土壤微生物 Alpha 多样性变化

### 4.2 土壤微生物 Beta 多样性变化

### 4.3 微生物群落组成及差异分析

### 4.4 微生物共现网络变化

### 4.5 小结

## 第五章 土壤氮循环功能基因对不同氮添加处理的响应

### 5.1 土壤氮循环功能基因总体组成

### 5.2 硝化相关基因对氮添加的响应

重点分析 pmoA-amoA、pmoB-amoB、pmoC-amoC 和 hao。

### 5.3 反硝化相关基因对氮添加的响应

重点分析 napA、nirK、nirS、norB、norC 和 nosZ。

### 5.4 DNRA 和固氮相关基因对氮添加的响应

重点分析 nrfA、nifH、nifD 和 nifK。

### 5.5 氮循环功能模块响应特征

分析硝化、反硝化、DNRA 和固氮模块的变化。

### 5.6 小结

## 第六章 环境因子与土壤氮循环功能基因的耦合机制

### 6.1 环境因子与关键土壤氮循环功能基因的相关性

### 6.2 RDA 揭示的环境驱动因子

### 6.3 不同氮形态下土壤氮循环功能基因响应机制

### 6.4 不同氮添加水平下氮转化过程的潜在调控路径

### 6.5 小结

## 第七章 讨论

### 7.1 不同氮形态对土壤氮循环功能基因的影响机制

### 7.2 不同氮添加水平对微生物介导氮转化过程的影响

### 7.3 滨海湿地盐碱环境对氮循环功能响应的调节作用

### 7.4 土壤微生物群落结构与功能基因之间的关系

### 7.5 研究不足与展望

## 第八章 结论

总结主要发现，回应研究问题，提出后续研究方向。
"""

    return text


# =========================
# 9. 数据分析写作提示
# =========================

def generate_result_writing_guide(file_groups: Dict[str, List[Path]]) -> str:
    data_previews = []

    for path in file_groups["data_files"][:20]:
        info = safe_preview_dataframe(path)
        data_previews.append(info)

    preview_texts = []

    for info in data_previews:
        preview_texts.append(
            f"""## 文件：{Path(info['file']).name}

- 路径：{info['file']}
- 数据维度：{info['shape']}
- 列名：{info['columns']}
- 预览：

```text
{info['preview']}
