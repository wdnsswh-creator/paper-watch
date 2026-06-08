#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Thesis Draft Generator

用途：
在 GitHub Actions 中读取 data/、figures/、zotero/、outputs/ 中的资料，
调用 OpenAI API 自动生成硕士论文初稿。

输出：
outputs/06_硕士论文初稿.md
outputs/07_结果段初稿.md
outputs/08_讨论段初稿.md
outputs/09_章节结尾段初稿.md
outputs/10_本次生成提示词备份.md
"""

from pathlib import Path
from datetime import date
import os
import pandas as pd
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIGURE_DIR = ROOT / "figures"
ZOTERO_DIR = ROOT / "zotero"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
MAX_TABLE_ROWS = 18
MAX_FILES_PER_GROUP = 30

PROJECT_PROFILE = """
用户论文主题：滨海湿地土壤氮转化过程对不同形态和水平氮素添加的响应及其调控机制。

研究对象：
- 黄河三角洲滨海湿地；
- 不同氮形态：NH4+-N 添加、NO3--N 添加；
- 不同氮添加水平：低、中、高；
- 土壤微生物群落；
- 土壤氮循环功能基因；
- 土壤环境因子：MC、EC、pH、NH4+-N、NO3--N 等。

固定术语：
- 涉及 functional genes 时，必须写作“土壤氮循环功能基因”。
- 不要写成泛泛的“功能基因”。

重点土壤氮循环功能基因：
pmoA-amoA、pmoB-amoB、pmoC-amoC、hao、napA、nirK、nirS、norC、norB、nosZ、nrfA、nifD、nifH、nifK。

重点氮循环过程：
硝化、反硝化、DNRA、固氮、氨氧化、硝酸盐还原。
"""

WRITING_STYLE_RULES = """
写作要求：
1. 使用中文学术论文语言，避免口语化。
2. 结果段要具体到处理、基因、过程和显著性。
3. 不要机械使用“综上所述”“总体而言”“由此可见”作为段落开头。
4. 章节结尾段不是普通总结，必须完成四件事：回顾当前章节形成的结果；提炼作者判断；回扣论文问题意识；轻轻引出下一步分析。
5. 不能夸大数据，不确定处明确写“待补充/需核对”。
6. 如果提到 P 值，只能使用数据表中确实存在的 P 值或显著性标注。
7. 不能虚构参考文献、DOI、期刊名。
8. 结果段要形成“处理差异—基因响应—氮循环过程含义”的逻辑链。
"""

def read_text(path: Path, max_chars: int = 12000) -> str:
    for enc in ["utf-8", "utf-8-sig", "gbk", "latin1"]:
        try:
            return path.read_text(encoding=enc, errors="ignore")[:max_chars]
        except Exception:
            pass
    return ""

def list_files(folder: Path, suffixes=None):
    if not folder.exists():
        return []
    out = []
    for p in folder.rglob("*"):
        if p.is_file() and (suffixes is None or p.suffix.lower() in suffixes):
            out.append(p)
    return sorted(out)

def read_table_preview(path: Path) -> str:
    try:
        if path.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(path, encoding="gbk")
        elif path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(path)
        else:
            return ""

        lines = []
        lines.append(f"文件：{path.relative_to(ROOT)}")
        lines.append(f"维度：{df.shape[0]} 行 × {df.shape[1]} 列")
        lines.append("列名：" + "；".join([str(c) for c in df.columns.tolist()]))

        key_cols = []
        for c in df.columns:
            cn = str(c).lower()
            if any(k in cn for k in [
                "gene", "process", "group", "treatment", "mean", "sd", "se",
                "p", "pvalue", "p_value", "letter", "significant", "anova",
                "rda", "env", "correlation", "coefficient"
            ]):
                key_cols.append(c)

        if key_cols:
            sub = df[key_cols[:12]].head(MAX_TABLE_ROWS)
        else:
            sub = df.head(MAX_TABLE_ROWS)

        lines.append("数据预览：")
        lines.append(sub.to_string(index=False))

        p_cols = [c for c in df.columns if "p" in str(c).lower()]
        if p_cols:
            lines.append("可能的显著性信息：")
            for pc in p_cols[:3]:
                try:
                    temp = df[pd.to_numeric(df[pc], errors="coerce") < 0.05].head(12)
                    if not temp.empty:
                        lines.append(f"{pc} < 0.05 的前几行：")
                        lines.append(temp.to_string(index=False))
                except Exception:
                    pass

        return "\n".join(lines)
    except Exception as e:
        return f"文件：{path.relative_to(ROOT)}\n读取失败：{e}"

def parse_ris_records(max_records=50) -> str:
    ris_files = list_files(ZOTERO_DIR, [".ris"])
    records = []
    for p in ris_files:
        text = read_text(p, max_chars=200000)
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
            elif line.startswith("AB  -"):
                cur["abstract"] = line.split("  -", 1)[-1].strip()
            elif line.startswith("ER  -"):
                if cur.get("title"):
                    records.append(cur)
                cur = {}

    lines = []
    for i, r in enumerate(records[:max_records], 1):
        authors = "; ".join(r.get("authors", [])[:5])
        lines.append(f"{i}. {r.get('title','')}（{r.get('year','')}，{r.get('journal','')}）")
        if authors:
            lines.append(f"   作者：{authors}")
        if r.get("abstract"):
            lines.append(f"   摘要：{r.get('abstract','')[:500]}")
    return "\n".join(lines) if lines else "未读取到 Zotero RIS 文献。"

def build_repository_context() -> str:
    parts = []

    parts.append("## outputs 文件内容摘要")
    output_files = list_files(OUTPUT_DIR, [".md", ".csv"])[:MAX_FILES_PER_GROUP]
    for p in output_files:
        if p.name.startswith(("06_", "07_", "08_", "09_", "10_")):
            continue
        if p.suffix.lower() == ".md":
            parts.append(f"\n### {p.relative_to(ROOT)}\n{read_text(p, max_chars=8000)}")
        elif p.suffix.lower() == ".csv":
            parts.append(f"\n### {p.relative_to(ROOT)}\n{read_table_preview(p)}")

    parts.append("\n## data 文件数据预览")
    data_files = list_files(DATA_DIR, [".csv", ".xlsx", ".xls"])[:MAX_FILES_PER_GROUP]
    for p in data_files:
        parts.append("\n" + read_table_preview(p))

    parts.append("\n## figures 文件清单")
    fig_files = list_files(FIGURE_DIR, [".png", ".jpg", ".jpeg", ".pdf", ".tif", ".tiff"])[:80]
    if fig_files:
        for p in fig_files:
            parts.append(f"- {p.relative_to(ROOT)}")
    else:
        parts.append("未上传图表文件。")

    parts.append("\n## Zotero 文献摘要")
    parts.append(parse_ris_records(max_records=50))

    return "\n".join(parts)[:65000]

def call_openai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY。请在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加 OPENAI_API_KEY。")

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )
    return response.output_text

def make_prompt(task_name: str, repository_context: str) -> str:
    if task_name == "full_draft":
        task = """
请根据资料生成“硕士论文初稿”。这不是最终论文，但要形成可继续修改的完整初稿。
结构至少包括：摘要初稿、绪论初稿、材料与方法初稿、结果初稿、讨论初稿、结论初稿。
数据不足的地方写“待补充/需核对”，不要虚构。
"""
    elif task_name == "results":
        task = """
请专门生成“结果段初稿”，重点写 Alpha/Beta 多样性、土壤氮循环功能模块、土壤氮循环功能基因丰度、RDA、相关性热图、PERMANOVA/ANOSIM。
模仿优秀文献结果段结构，但所有基因、处理、P 值、变化方向必须来自上传数据。
"""
    elif task_name == "discussion":
        task = """
请生成“讨论部分初稿”，重点讨论不同氮形态、不同氮添加水平、土壤氮循环功能基因、环境因子调控及与 Zotero 文献的衔接。
文献只能根据 Zotero 标题和摘要谨慎概括，不能编造具体结论。
"""
    elif task_name == "ending":
        task = """
请生成“章节/小节/文献述评结尾段模板初稿”，至少写 8 段，分别用于绪论文献综述、材料与方法、土壤环境因子、微生物群落结构、土壤氮循环功能基因、RDA/相关性分析、讨论章节结尾、全文结论前收束段。
每段都要回顾结果、提炼判断、回扣问题意识、引出下一步，不要用“综上所述”开头。
"""
    else:
        raise ValueError(task_name)

    return f"""{PROJECT_PROFILE}

{WRITING_STYLE_RULES}

下面是 GitHub 仓库中自动整理的数据、图表和 Zotero 文献资料：

{repository_context}

现在的写作任务：
{task}
"""

def main():
    repo_context = build_repository_context()

    prompts = {
        "full_draft": make_prompt("full_draft", repo_context),
        "results": make_prompt("results", repo_context),
        "discussion": make_prompt("discussion", repo_context),
        "ending": make_prompt("ending", repo_context),
    }

    prompt_backup = "# 本次生成提示词备份\n\n"
    for k, v in prompts.items():
        prompt_backup += f"\n\n## {k}\n\n```text\n{v[:20000]}\n```\n"
    (OUTPUT_DIR / "10_本次生成提示词备份.md").write_text(prompt_backup, encoding="utf-8")

    print("正在生成硕士论文初稿……")
    (OUTPUT_DIR / "06_硕士论文初稿.md").write_text(call_openai(prompts["full_draft"]), encoding="utf-8")

    print("正在生成结果段初稿……")
    (OUTPUT_DIR / "07_结果段初稿.md").write_text(call_openai(prompts["results"]), encoding="utf-8")

    print("正在生成讨论段初稿……")
    (OUTPUT_DIR / "08_讨论段初稿.md").write_text(call_openai(prompts["discussion"]), encoding="utf-8")

    print("正在生成章节结尾段初稿……")
    (OUTPUT_DIR / "09_章节结尾段初稿.md").write_text(call_openai(prompts["ending"]), encoding="utf-8")

    print("完成！已生成 outputs/06-10 号文件。")

if __name__ == "__main__":
    main()
