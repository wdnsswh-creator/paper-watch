#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
读取 zotero/*.ris，生成带参考文献标记的分析语言模板。
不需要 OpenAI API。
"""

from pathlib import Path
import re
import csv
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[1]
ZOTERO_DIR = ROOT / "zotero"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

OUT_MD = OUTPUT_DIR / "11_Zotero文献分析语言模板.md"
OUT_CSV = OUTPUT_DIR / "12_Zotero文献主题分类清单.csv"

THEMES = {
    "氮添加/氮沉降影响微生物群落": [
        "nitrogen addition", "nitrogen deposition", "nitrogen enrichment",
        "nitrogen input", "fertilization", "fertilizer", "n addition",
        "n deposition", "nutrient enrichment"
    ],
    "土壤氮循环功能基因/宏基因组": [
        "functional gene", "functional genes", "nitrogen cycling gene",
        "metagenomic", "metagenomics", "shotgun", "kegg",
        "functional potential", "nitrogen metabolism",
        "carbon-nitrogen cycling", "nitrogen-cycle processes"
    ],
    "硝化/氨氧化过程": [
        "nitrification", "ammonia oxidation", "ammonia-oxidizing",
        "amoa", "hao", "aob", "aoa"
    ],
    "反硝化过程": [
        "denitrification", "nirk", "nirs", "norb", "norc",
        "nosz", "nitrous oxide", "n2o"
    ],
    "DNRA/硝酸盐还原": [
        "dnra", "dissimilatory nitrate reduction", "nitrate reduction",
        "nrfa", "nitrate ammonification"
    ],
    "固氮过程": [
        "nitrogen fixation", "nifh", "nifd", "nifk", "diazotroph"
    ],
    "湿地/盐沼/滨海生态系统": [
        "wetland", "salt marsh", "coastal wetland", "estuarine",
        "tidal", "sediment", "coastal", "marsh", "yellow river delta"
    ],
    "盐度/pH/环境因子调控": [
        "salinity", "saline", "saline-alkali", "electrical conductivity",
        " ec ", "ph", "soil moisture", "water content", "environmental factor"
    ],
    "互花米草/湿地植被/根际": [
        "spartina", "spartina alterniflora", "phragmites", "suaeda",
        "tamarix", "halophyte", "plant invasion", "invasive plant",
        "rhizosphere", "vegetation"
    ],
    "微生物网络/群落结构": [
        "microbial community", "bacterial community", "fungal community",
        "community structure", "microbial diversity", "co-occurrence",
        "network", "community assembly", "microbiome"
    ],
}

def read_text(path):
    for enc in ["utf-8", "utf-8-sig", "gbk", "latin1"]:
        try:
            return path.read_text(encoding=enc, errors="ignore")
        except Exception:
            pass
    return ""

def clean(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def parse_ris(path):
    text = read_text(path)
    records = []
    cur = {}
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("TY  -"):
            cur = {"source_file": path.name, "authors": []}
        elif line.startswith("TI  -") or line.startswith("T1  -"):
            cur["title"] = clean(line.split("  -", 1)[-1])
        elif line.startswith("AU  -"):
            cur.setdefault("authors", []).append(clean(line.split("  -", 1)[-1]))
        elif line.startswith("PY  -") or line.startswith("Y1  -"):
            year = clean(line.split("  -", 1)[-1])
            m = re.search(r"\d{4}", year)
            cur["year"] = m.group(0) if m else year
        elif line.startswith("JO  -") or line.startswith("JF  -") or line.startswith("T2  -"):
            cur["journal"] = clean(line.split("  -", 1)[-1])
        elif line.startswith("DO  -"):
            cur["doi"] = clean(line.split("  -", 1)[-1])
        elif line.startswith("AB  -") or line.startswith("N2  -"):
            cur["abstract"] = clean(line.split("  -", 1)[-1])
        elif line.startswith("KW  -"):
            cur.setdefault("keywords", []).append(clean(line.split("  -", 1)[-1]))
        elif line.startswith("ER  -"):
            if cur.get("title"):
                cur["authors_text"] = "; ".join(cur.get("authors", []))
                cur["keywords_text"] = "; ".join(cur.get("keywords", []))
                records.append(cur)
            cur = {}
    return records

def author_year(record):
    authors = record.get("authors", [])
    year = record.get("year", "n.d.")
    if not authors:
        return f"Anonymous, {year}"
    first = authors[0]
    surname = first.split(",", 1)[0].strip() if "," in first else (first.split()[-1] if first.split() else first)
    if len(authors) >= 3:
        return f"{surname} et al., {year}"
    if len(authors) == 2:
        second = authors[1]
        surname2 = second.split(",", 1)[0].strip() if "," in second else (second.split()[-1] if second.split() else second)
        return f"{surname} and {surname2}, {year}"
    return f"{surname}, {year}"

def classify_record(record):
    text = " ".join([record.get("title",""), record.get("abstract",""), record.get("keywords_text",""), record.get("journal","")]).lower()
    matched = []
    for theme, keywords in THEMES.items():
        if any(k in text for k in keywords):
            matched.append(theme)
    return matched or ["背景文献"]

def pick_refs(theme_records, n=4):
    scored = []
    for r in theme_records:
        score = 0
        if r.get("abstract"): score += 2
        if r.get("year"): score += 1
        if r.get("doi"): score += 1
        score += min(len(r.get("title","")) / 100, 1)
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:n]]

def refs_str(records):
    out = []
    for r in records:
        c = author_year(r)
        if c not in out:
            out.append(c)
    return "；".join(out)

def keyword_counter(records):
    words = ["nitrogen", "microbial", "soil", "wetland", "metagenomic", "functional genes",
             "nitrification", "denitrification", "dnra", "nitrogen fixation", "salinity",
             "spartina", "rhizosphere", "carbon-nitrogen", "deposition", "addition"]
    c = Counter()
    for r in records:
        text = " ".join([r.get("title",""), r.get("abstract","")]).lower()
        for w in words:
            if w in text:
                c[w] += 1
    return c

def theme_sentences(theme, recs):
    cite = refs_str(pick_refs(recs, 4)) or "参考文献待补充"
    bank = {
        "氮添加/氮沉降影响微生物群落": [
            f"已有研究表明，外源氮输入能够改变土壤氮素供给状态，并进一步影响微生物群落结构及其功能潜力，这为分析不同氮添加处理下微生物介导的氮转化过程提供了重要依据（{cite}）。",
            f"氮添加或氮沉降对土壤微生物的影响并不只表现为养分增加，还可能通过改变底物供给、酸碱环境和群落组成，进一步影响土壤氮循环功能基因的丰度格局（{cite}）。"
        ],
        "土壤氮循环功能基因/宏基因组": [
            f"宏基因组和土壤氮循环功能基因分析能够从功能潜力层面揭示微生物参与氮转化过程的机制，比单纯群落组成分析更能反映氮循环过程的潜在变化（{cite}）。",
            f"已有文献通常将氮循环相关基因与微生物群落变化结合讨论，用以解释外源氮输入背景下硝化、反硝化、DNRA 和固氮等过程的响应差异（{cite}）。"
        ],
        "硝化/氨氧化过程": [
            f"硝化和氨氧化过程是无机氮转化的重要环节，相关基因的变化通常被用于指示氨态氮向硝态氮转化的潜在能力（{cite}）。",
            f"当氨氧化相关基因在氮添加处理中升高时，通常说明外源氮输入可能增强氨氧化或硝化过程的功能潜力，但这一判断仍需结合底物浓度和环境因子共同解释（{cite}）。"
        ],
        "反硝化过程": [
            f"反硝化过程涉及多个连续还原步骤，因此 nirK、nirS、norB、norC 和 nosZ 等基因的差异响应可反映反硝化链条不同环节的调节特征（{cite}）。",
            f"相关研究表明，反硝化功能并不一定随氮输入同步增强，不同还原步骤相关基因可能表现出方向不一致的响应，这提示反硝化过程具有明显的环节差异性（{cite}）。"
        ],
        "DNRA/硝酸盐还原": [
            f"DNRA 与反硝化同样以硝酸盐或亚硝酸盐为底物，但其生态效应更偏向氮素保留，因此 nrfA 等基因的变化可用于判断硝酸盐还原途径是否发生转向（{cite}）。",
            f"在湿地或高水分环境中，DNRA 过程可能与反硝化过程共同竞争硝酸盐底物，其相关基因响应有助于解释氮素保留与氮损失之间的潜在平衡（{cite}）。"
        ],
        "固氮过程": [
            f"固氮相关基因通常反映微生物从大气氮获得氮源的潜在能力，而外源氮输入可能通过降低氮限制程度削弱固氮过程的生态需求（{cite}）。",
            f"当 nifH、nifD 或 nifK 等固氮相关基因在氮添加处理中下降时，通常可解释为外源氮供应缓解了微生物对生物固氮的依赖（{cite}）。"
        ],
        "湿地/盐沼/滨海生态系统": [
            f"滨海湿地和盐沼处于陆海交互带，盐度、水分和氧化还原条件变化强烈，这些环境特征使其氮循环过程具有明显的空间异质性和过程耦合特征（{cite}）。",
            f"湿地沉积物和土壤中的微生物群落是驱动氮转化过程的重要生物基础，其对外源氮输入的响应常受到盐度、潮汐和植被条件的共同调节（{cite}）。"
        ],
        "盐度/pH/环境因子调控": [
            f"盐度、pH 和水分条件能够通过改变微生物生境和底物有效性影响土壤氮循环功能基因，因此环境因子常被视为解释功能基因差异的重要调控变量（{cite}）。",
            f"在盐碱化或滨海湿地土壤中，EC 和 pH 的变化可能对氮循环微生物产生筛选作用，从而进一步影响硝化、反硝化和 DNRA 等过程的功能潜力（{cite}）。"
        ],
        "互花米草/湿地植被/根际": [
            f"湿地植被能够通过根系输入、根际氧化还原环境和有机碳供给改变微生物群落结构，进而影响土壤氮循环功能基因的分布和表达潜力（{cite}）。",
            f"互花米草等入侵植物可能通过改变土壤理化性质和根际微生物环境影响氮循环过程，因此植被因素应被纳入滨海湿地氮循环机制解释框架（{cite}）。"
        ],
        "微生物网络/群落结构": [
            f"微生物群落结构和共现网络可反映不同处理下微生物相互作用和群落稳定性的变化，为解释功能基因响应提供群落生态学背景（{cite}）。",
            f"当氮添加改变微生物群落组成或网络复杂性时，土壤氮循环功能基因的变化可能不仅源于底物供给差异，也与功能类群之间的相互作用重组有关（{cite}）。"
        ],
        "背景文献": [
            f"相关研究为理解土壤微生物过程和生态系统功能变化提供了背景依据，但其与本研究主题的对应关系仍需结合具体研究对象和指标进一步筛选（{cite}）。"
        ]
    }
    return bank.get(theme, bank["背景文献"])

def generate_md(by_theme, total, kc):
    lines = []
    lines.append("# Zotero 文献分析语言模板")
    lines.append("")
    lines.append("本文件由 GitHub 脚本自动读取 `zotero/*.ris` 生成。每句话末尾均给出参考文献标记。")
    lines.append("")
    lines.append(f"- 读取文献总数：{total}")
    if kc:
        lines.append("- 高频主题词：" + "；".join([f"{k}（{v}篇）" for k, v in kc.most_common(12)]))
    lines.append("")
    lines.append("## 一、按主题整理的分析语言")
    lines.append("")
    for theme, recs in by_theme.items():
        lines.append(f"### {theme}")
        lines.append("")
        for s in theme_sentences(theme, recs):
            lines.append(f"- {s}")
        lines.append("")
    # 杂糅模板
    cite_func = refs_str(pick_refs(by_theme.get("土壤氮循环功能基因/宏基因组", []), 3)) or "参考文献待补充"
    cite_n = refs_str(pick_refs(by_theme.get("氮添加/氮沉降影响微生物群落", []), 3)) or "参考文献待补充"
    cite_wetland = refs_str(pick_refs(by_theme.get("湿地/盐沼/滨海生态系统", []), 3)) or "参考文献待补充"
    cite_env = refs_str(pick_refs(by_theme.get("盐度/pH/环境因子调控", []), 3)) or "参考文献待补充"
    lines.append("## 二、适用于本研究结果解释的杂糅模板")
    lines.append("")
    templates = [
        f"与对照相比，不同氮添加处理对土壤氮循环功能基因的影响表现出明显的过程差异性，说明外源氮输入并非均一地增强或削弱全部氮转化环节，而是更可能通过改变特定功能类群和关键基因丰度来影响氮循环功能潜力（{cite_func}）。",
        f"当 pmoA-amoA、pmoB-amoB、pmoC-amoC 或 hao 等基因丰度升高时，可将其解释为氨氧化和硝化过程潜力增强；但若统计结果未达到显著水平，应表述为“呈升高趋势”，而不能直接写作显著促进（{cite_func}）。",
        f"nirK、nirS、norB、norC 和 nosZ 等基因分别对应反硝化链条中的不同还原环节，因此这些基因在不同氮形态处理下的差异响应，可用于说明反硝化过程内部存在环节选择性，而不是简单地整体增强或整体减弱（{cite_func}）。",
        f"nrfA 的变化可用于指示 DNRA 过程的潜在响应，若其在特定处理下升高，说明硝酸盐还原途径可能更偏向氮素保留；若其下降，则可能提示 DNRA 功能潜力减弱或受到其他氮转化途径竞争（{cite_func}）。",
        f"nifH、nifD 和 nifK 等固氮相关基因的变化应与外源氮供应背景共同解释；在氮添加条件下，如果固氮相关基因下降，通常可理解为氮限制缓解后微生物固氮需求降低（{cite_n}）。",
        f"不同氮形态可能通过底物供给差异影响土壤氮循环功能基因：NH4+-N 更直接关联氨氧化和硝化过程，而 NO3--N 则更可能影响硝酸盐还原、反硝化和 DNRA 等过程（{cite_n}）。",
        f"滨海湿地土壤同时受到盐度、水分、pH 和氧化还原条件的共同影响，因此本研究中土壤氮循环功能基因的变化不能仅从氮添加本身解释，还应结合 EC、pH、MC、NH4+-N 和 NO3--N 等环境因子进行综合分析（{cite_wetland}；{cite_env}）。",
        f"如果 RDA 或相关性分析显示某些环境因子与关键土壤氮循环功能基因相关，应表述为“关联”或“可能参与调控”，而不能直接写作“导致”，以避免超出统计分析能够支持的因果范围（{cite_env}）。",
    ]
    for t in templates:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("## 三、章节结尾段模板")
    lines.append("")
    ending_refs = refs_str(pick_refs(by_theme.get("土壤氮循环功能基因/宏基因组", []), 2) + pick_refs(by_theme.get("氮添加/氮沉降影响微生物群落", []), 2)) or "参考文献待补充"
    endings = [
        f"本节结果表明，不同氮添加处理并非简单改变单一基因丰度，而是通过影响不同氮转化环节的关键土壤氮循环功能基因，表现出具有过程差异的功能响应（{ending_refs}）。",
        f"从论文核心问题看，本节结果的意义不在于简单判断氮添加是否改变了基因丰度，而在于揭示不同氮形态和添加水平如何通过关键土壤氮循环功能基因影响潜在氮转化过程（{ending_refs}）。",
        f"基于上述结果，后续分析有必要进一步结合土壤环境因子和排序分析，判断 EC、pH、含水率及无机氮形态是否参与塑造土壤氮循环功能基因的差异化响应（{ending_refs}）。",
    ]
    for e in endings:
        lines.append(f"- {e}")
    lines.append("")
    lines.append("## 四、文献清单与主题归类")
    lines.append("")
    for theme, recs in by_theme.items():
        lines.append(f"### {theme}（{len(recs)} 篇）")
        for r in recs[:20]:
            lines.append(f"- {r.get('title','')}（{author_year(r)}；{r.get('journal','')}）")
        lines.append("")
    return "\n".join(lines)

def main():
    ris_files = sorted(ZOTERO_DIR.glob("*.ris"))
    records = []
    for p in ris_files:
        records.extend(parse_ris(p))
    if not records:
        OUT_MD.write_text("# Zotero 文献分析语言模板\n\n未在 `zotero/` 文件夹中读取到 RIS 文献。请先上传 Zotero 导出的 `.ris` 文件。\n", encoding="utf-8")
        return
    by_theme = defaultdict(list)
    for r in records:
        themes = classify_record(r)
        r["themes"] = "；".join(themes)
        r["citation"] = author_year(r)
        for th in themes:
            by_theme[th].append(r)
    ordered = {}
    for th in THEMES.keys():
        if th in by_theme:
            ordered[th] = by_theme[th]
    if "背景文献" in by_theme:
        ordered["背景文献"] = by_theme["背景文献"]
    OUT_MD.write_text(generate_md(ordered, len(records), keyword_counter(records)), encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title","authors_text","year","journal","doi","citation","themes","source_file"])
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in ["title","authors_text","year","journal","doi","citation","themes","source_file"]})
    print("完成！已生成：")
    print(OUT_MD)
    print(OUT_CSV)

if __name__ == "__main__":
    main()
