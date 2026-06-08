#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Thesis Assistant

功能：
1. 扫描 GitHub 仓库里的 data/、figures/、zotero/ 文件夹；
2. 读取 Zotero 导出的 RIS 文献；
3. 读取 CSV / Excel 的列名、行数和前几行；
4. 自动生成：
   - outputs/01_研究方案自动草案.md
   - outputs/02_硕士论文框架自动草案.md
   - outputs/03_数据与图表清单.md
   - outputs/04_Zotero文献分类清单.csv
   - outputs/05_章节结尾段_skill.md

注意：
这个脚本不调用 AI API，所以它能稳定免费跑。
它生成的是“结构化草案”和“清单”，不是最终论文正文。
"""

from pathlib import Path
from datetime import date
from typing import Dict, List
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIGURE_DIR = ROOT / "figures"
ZOTERO_DIR = ROOT / "zotero"
OUTPUT_DIR = ROOT / "outputs"

PROJECT_TITLE = "滨海湿地土壤氮转化过程对不同形态和水平氮素添加的响应及其调控机制"

TARGET_GENES = [
    "pmoA-amoA", "pmoB-amoB", "pmoC-amoC", "hao",
    "napA", "nirK", "nirS", "norC", "norB", "nosZ",
    "nrfA", "nifD", "nifH", "nifK"
]

PROCESS_MAP = {
    "硝化": ["pmoA-amoA", "pmoB-amoB", "pmoC-amoC", "hao"],
    "反硝化": ["napA", "nirK", "nirS", "norB", "norC", "nosZ"],
    "DNRA": ["nrfA"],
    "固氮": ["nifH", "nifD", "nifK"],
}

def ensure_dirs():
    OUTPUT_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    FIGURE_DIR.mkdir(exist_ok=True)
    ZOTERO_DIR.mkdir(exist_ok=True)

def read_text(path: Path) -> str:
    for enc in ["utf-8", "utf-8-sig", "gbk", "latin1"]:
        try:
            return path.read_text(encoding=enc, errors="ignore")
        except Exception:
            pass
    return ""

def parse_ris(path: Path) -> List[Dict[str, str]]:
    text = read_text(path)
    records = []
    cur = {}
    for line in text.splitlines():
        if line.startswith("TY  -"):
            cur = {}
        elif line.startswith("TI  -") or line.startswith("T1  -"):
            cur["title"] = line.split("  -", 1)[-1].strip()
        elif line.startswith("AU  -"):
            cur.setdefault("authors", [])
            cur["authors"].append(line.split("  -", 1)[-1].strip())
        elif line.startswith("PY  -"):
            cur["year"] = line.split("  -", 1)[-1].strip()
        elif line.startswith("JO  -") or line.startswith("JF  -"):
            cur["journal"] = line.split("  -", 1)[-1].strip()
        elif line.startswith("DO  -"):
            cur["doi"] = line.split("  -", 1)[-1].strip()
        elif line.startswith("AB  -"):
            cur["abstract"] = line.split("  -", 1)[-1].strip()
        elif line.startswith("ER  -"):
            if cur.get("title"):
                if isinstance(cur.get("authors"), list):
                    cur["authors"] = "; ".join(cur["authors"][:8])
                records.append(cur)
            cur = {}
    return records

def classify_lit(record: Dict[str, str]) -> str:
    text = " ".join([record.get("title",""), record.get("abstract",""), record.get("journal","")]).lower()
    tags = []
    if any(x in text for x in ["metagenomic", "metagenomics", "functional gene", "functional genes", "kegg", "faprotax"]):
        tags.append("宏基因组/功能基因")
    if any(x in text for x in ["nitrogen addition", "nitrogen deposition", "nitrogen enrichment", "fertilization", "nitrogen loading"]):
        tags.append("氮添加/氮沉降")
    if any(x in text for x in ["nitrification", "denitrification", "dnra", "nitrogen fixation", "ammonia oxidation", "nitrate reduction"]):
        tags.append("氮循环过程")
    if any(x in text for x in ["wetland", "salt marsh", "coastal", "estuarine", "tidal", "yellow river delta"]):
        tags.append("滨海湿地/盐沼")
    if any(x in text for x in ["spartina", "phragmites", "suaeda", "tamarix", "halophyte"]):
        tags.append("湿地植被/盐生植物")
    if any(x in text for x in ["microbial community", "bacterial community", "fungal community", "microbiome", "microorganism"]):
        tags.append("微生物群落")
    return "；".join(tags) if tags else "背景文献"

def load_zotero_records() -> List[Dict[str, str]]:
    records = []
    for path in ZOTERO_DIR.glob("*.ris"):
        records.extend(parse_ris(path))
    return records

def scan_files():
    files = []
    for folder_name, folder in [("data", DATA_DIR), ("figures", FIGURE_DIR), ("zotero", ZOTERO_DIR)]:
        for p in folder.rglob("*"):
            if p.is_file():
                files.append({
                    "folder": folder_name,
                    "filename": p.name,
                    "path": str(p.relative_to(ROOT)),
                    "suffix": p.suffix.lower(),
                    "size_kb": round(p.stat().st_size / 1024, 2),
                })
    return files

def preview_table(path: Path) -> Dict:
    out = {"file": str(path.relative_to(ROOT)), "shape": "", "columns": "", "preview": "", "error": ""}
    try:
        if path.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(path, encoding="gbk")
        elif path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(path)
        else:
            return out
        out["shape"] = str(df.shape)
        out["columns"] = "；".join(map(str, df.columns.tolist()))
        out["preview"] = df.head(5).to_string(index=False)
    except Exception as e:
        out["error"] = str(e)
    return out

def generate_research_plan(lit_records, file_rows):
    lit_count = len(lit_records)
    top_lits = "\n".join([f"- {r.get('title','')}（{r.get('year','')}；{r.get('tags','')}）" for r in lit_records[:20]])
    data_count = sum(1 for x in file_rows if x["folder"] == "data")
    fig_count = sum(1 for x in file_rows if x["folder"] == "figures")
    return f"""# 研究方案自动草案

生成日期：{date.today().isoformat()}

## 一、研究题目

{PROJECT_TITLE}

## 二、研究背景与问题提出

滨海湿地位于陆海交互带，盐度、水分、pH、无机氮形态和植被类型共同影响土壤微生物群落及其功能潜力。外源氮输入不仅改变土壤氮素供给，也可能通过不同氮形态和添加水平影响硝化、反硝化、DNRA 和固氮等过程。因此，本研究将不同氮形态、不同氮添加水平、土壤环境因子和土壤氮循环功能基因结合起来，用于解释滨海湿地氮转化过程的微生物调控机制。

## 三、研究目标

本研究围绕“不同形态和水平氮添加如何影响滨海湿地土壤氮转化过程及其微生物调控机制”这一核心问题，重点分析土壤氮循环功能基因、功能模块、微生物群落结构和环境因子之间的耦合关系。

## 四、科学问题

1. 不同氮形态添加是否改变土壤微生物群落结构和功能潜力？
2. 不同氮添加水平是否引起土壤氮循环功能基因的梯度响应？
3. NH4+-N 与 NO3--N 添加对硝化、反硝化、DNRA 和固氮相关基因的影响是否存在差异？
4. EC、pH、含水率、NH4+-N 和 NO3--N 是否调控关键土壤氮循环功能基因变化？
5. 土壤氮循环功能基因变化能否解释潜在氮转化过程差异？

## 五、研究内容

### 研究内容一：不同氮添加处理下土壤环境因子变化

分析 pH、EC、含水率、NH4+-N、NO3--N 等环境因子变化，为解释土壤氮循环功能基因响应提供背景。

### 研究内容二：不同氮添加处理下土壤微生物群落结构变化

结合 Alpha 多样性、Beta 多样性、群落结构和共现网络，判断氮添加是否改变微生物群落稳定性和结构分化。

### 研究内容三：土壤氮循环功能基因对不同氮添加处理的响应

围绕 {", ".join(TARGET_GENES)} 等基因，分析不同处理间的丰度变化、显著性差异和对应氮循环过程。

### 研究内容四：环境因子与土壤氮循环功能基因的耦合关系

结合相关性热图、RDA 或 Mantel 分析，阐明环境因子对关键土壤氮循环功能基因的潜在调控作用。

## 六、当前资料基础

- 已上传数据文件数量：{data_count}
- 已上传图表文件数量：{fig_count}
- 已读取 Zotero 文献数量：{lit_count}

## 七、Zotero 文献基础

{top_lits if top_lits else "尚未读取到 Zotero RIS 文献。请把 zotero_export.ris 上传到 zotero/ 文件夹。"}

## 八、技术路线

氮添加处理设置 → 土壤样品采集 → 理化性质测定 → 宏基因组/微生物数据分析 → 土壤氮循环功能基因筛选 → 差异分析 → 相关性/RDA 分析 → 机制解释 → 论文结果与讨论写作。
"""

def generate_outline():
    return """# 硕士论文框架自动草案

## 摘要

概述研究背景、研究目的、实验设计、主要方法、核心结果和结论。

## 第一章 绪论

### 1.1 研究背景
滨海湿地氮循环、外源氮输入、氮添加形态与水平、微生物介导氮转化过程。

### 1.2 国内外研究进展
#### 1.2.1 滨海湿地氮循环过程研究进展
#### 1.2.2 氮添加对土壤微生物群落的影响
#### 1.2.3 土壤氮循环功能基因研究进展
#### 1.2.4 不同氮形态和氮添加水平对氮循环过程的影响

### 1.3 研究目的与意义
### 1.4 研究内容与技术路线

## 第二章 材料与方法

### 2.1 研究区概况
### 2.2 实验设计与样品采集
### 2.3 土壤理化性质测定
### 2.4 宏基因组与功能基因分析方法
### 2.5 统计分析

## 第三章 不同氮添加处理下土壤环境因子变化

### 3.1 土壤含水率、pH 和 EC 的变化
### 3.2 土壤 NH4+-N 和 NO3--N 的变化
### 3.3 小结

## 第四章 不同氮添加处理下土壤微生物群落结构变化

### 4.1 Alpha 多样性变化
### 4.2 Beta 多样性变化
### 4.3 群落组成与共现网络变化
### 4.4 小结

## 第五章 土壤氮循环功能基因对不同氮添加处理的响应

### 5.1 土壤氮循环功能基因总体组成
### 5.2 硝化相关基因响应
### 5.3 反硝化相关基因响应
### 5.4 DNRA 和固氮相关基因响应
### 5.5 氮循环功能模块响应
### 5.6 小结

## 第六章 环境因子与土壤氮循环功能基因的耦合机制

### 6.1 环境因子与关键基因相关性
### 6.2 RDA 揭示的环境驱动因子
### 6.3 不同氮形态下功能基因响应机制
### 6.4 小结

## 第七章 讨论

### 7.1 不同氮形态对土壤氮循环功能基因的影响机制
### 7.2 不同氮添加水平对微生物介导氮转化过程的影响
### 7.3 滨海湿地盐碱环境的调节作用
### 7.4 研究不足与展望

## 第八章 结论
"""

def generate_file_report(file_rows):
    lines = ["# 数据与图表清单", "", f"生成日期：{date.today().isoformat()}", ""]
    if not file_rows:
        lines.append("尚未在 data/、figures/、zotero/ 中发现文件。")
        return "\n".join(lines)

    df = pd.DataFrame(file_rows)
    for folder in ["data", "figures", "zotero"]:
        sub = df[df["folder"] == folder]
        lines.append(f"## {folder} 文件夹")
        lines.append("")
        if sub.empty:
            lines.append("暂无文件。")
        else:
            for _, row in sub.iterrows():
                lines.append(f"- {row['filename']} | {row['suffix']} | {row['size_kb']} KB | {row['path']}")
        lines.append("")

    lines.append("## 数据表预览")
    lines.append("")
    for p in DATA_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in [".csv", ".xlsx", ".xls"]:
            info = preview_table(p)
            lines.append(f"### {info['file']}")
            lines.append("")
            lines.append(f"- 数据维度：{info['shape']}")
            lines.append(f"- 列名：{info['columns']}")
            if info["error"]:
                lines.append(f"- 读取错误：{info['error']}")
            else:
                lines.append("```text")
                lines.append(info["preview"])
                lines.append("```")
            lines.append("")
    return "\n".join(lines)

def generate_ending_skill():
    return """# 章节结尾段 skill

## 任务定位

用于硕士论文中章节、小节和文献述评后的结尾段。它不是普通总结器，也不是把前文压缩一遍。它需要完成四件事：回顾当前章节已经形成的结果，提炼作者判断，回扣论文问题意识，轻轻引出下一步分析。

## 写作规则

1. 不要机械使用“综上所述”“总体而言”“由此可见”作为开头。
2. 不要把前文标题重新排列成“一是、二是、三是”。
3. 不要只重复数据，要上升到“这些结果说明了什么”。
4. 不能夸大不显著结果。
5. 涉及用户论文时，必须写作“土壤氮循环功能基因”。

## 示例

本节结果表明，不同氮添加处理并非简单改变单一基因丰度，而是通过影响不同氮转化环节的关键土壤氮循环功能基因，表现出具有过程差异的功能响应。尤其是在 NH4+-N 与 NO3--N 添加之间，硝化、反硝化、DNRA 和固氮相关基因的变化方向并不完全一致，说明外源氮输入对滨海湿地土壤氮循环的影响具有明显的形态依赖性和过程选择性。由此，本研究的问题不应停留在氮添加是否改变功能基因丰度，而应进一步追问这种变化受到哪些环境因子的调控，以及不同基因响应如何共同指向潜在氮转化过程的改变。
"""

def main():
    ensure_dirs()
    file_rows = scan_files()

    lit_records = load_zotero_records()
    for r in lit_records:
        r["tags"] = classify_lit(r)

    pd.DataFrame(file_rows).to_csv(OUTPUT_DIR / "00_文件清单.csv", index=False, encoding="utf-8-sig")
    if lit_records:
        pd.DataFrame(lit_records).to_csv(OUTPUT_DIR / "04_Zotero文献分类清单.csv", index=False, encoding="utf-8-sig")

    (OUTPUT_DIR / "01_研究方案自动草案.md").write_text(generate_research_plan(lit_records, file_rows), encoding="utf-8")
    (OUTPUT_DIR / "02_硕士论文框架自动草案.md").write_text(generate_outline(), encoding="utf-8")
    (OUTPUT_DIR / "03_数据与图表清单.md").write_text(generate_file_report(file_rows), encoding="utf-8")
    (OUTPUT_DIR / "05_章节结尾段_skill.md").write_text(generate_ending_skill(), encoding="utf-8")

    print("完成！输出文件在 outputs/ 文件夹。")
    print("已生成：")
    print("outputs/00_文件清单.csv")
    print("outputs/01_研究方案自动草案.md")
    print("outputs/02_硕士论文框架自动草案.md")
    print("outputs/03_数据与图表清单.md")
    print("outputs/04_Zotero文献分类清单.csv")
    print("outputs/05_章节结尾段_skill.md")

if __name__ == "__main__":
    main()
