# Paper Watch

这是一个面向 Zotero 导入的文献追踪小工具。当前版本根据用户论文 `查重版本.docx` 的主题，优先检索以下方向的论文：

- 黄河三角洲、滨海湿地、盐沼、河口湿地和盐碱土壤；
- Tamarix chinensis、Suaeda salsa、Phragmites australis 等湿地植被类型；
- 距海梯度、盐度梯度、EC、盐分含量、pH 等环境因子；
- 土壤细菌群落、土壤真菌群落、16S rRNA、ITS、高通量测序；
- alpha diversity、beta diversity、PCoA、NMDS、PERMANOVA、ANOSIM；
- FAPROTAX、FUNGuild、Saprotroph、Pathotroph、Symbiotroph 等功能预测。

本工具只检索公开论文元数据，不下载 PDF，不自动登录学校账号，不绕过数据库权限，也不直接连接 Zotero API。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 重新检索文献

如果想重新按当前关键词检索，并避免旧 DOI 去重影响，可以先备份旧记录：

```bash
copy output\seen_dois.txt output\seen_dois.backup.txt
del output\seen_dois.txt
```

然后运行：

```bash
python scripts/search_papers.py --days 3650 --limit 20 --max-queries 40 --mailto your-email@example.com
```

参数说明：

- `--days`：检索最近多少天的论文，`3650` 约等于最近 10 年。
- `--limit`：每个检索词在每个数据源最多返回多少条。
- `--max-queries`：最多使用多少个检索词，数值越大越慢。
- `--mailto`：建议填写邮箱，方便 OpenAlex 识别正常学术用途。

## 输出文件

脚本会生成：

- `output/daily_papers.md`：文献清单和推荐理由；
- `output/daily_papers.ris`：可导入 Zotero 的 RIS 文件；
- `output/seen_dois.txt`：已见 DOI，用于下次去重。

`daily_papers.md` 现在会额外标出每篇文献可参考的图件/方法类型，例如 EC/pH/Salt 理化性质图、alpha diversity、UpSet/Venn、PCoA/NMDS/PERMANOVA、门水平组成、LEfSe、环境因子相关性/随机森林、FAPROTAX/FUNGuild 等，并给出期刊质量提示。A 类会优先保留主题、方法和期刊规格都更合适的文献。

## 按摘要草稿检索文献摘要

如果目标是写论文摘要，而不是普通找文献，运行：

```bash
python scripts/search_abstract_papers.py --days 3650 --limit 10 --max-queries 24 --mailto your-email@example.com
```

默认会使用黄河三角洲滨海湿地、柽柳/碱蓬/芦苇、土壤细菌和真菌群落、高通量测序、共现网络和功能预测这一摘要模板。

如果你有自己的摘要草稿，先保存成 UTF-8 文本文件，例如 `work/abstract_draft.txt`，再运行：

```bash
python scripts/search_abstract_papers.py --abstract-file work/abstract_draft.txt --days 3650 --limit 10 --max-queries 24 --mailto your-email@example.com
```

输出文件：

- `output/abstract_papers.md`：按“背景句、问题句、对象句、方法句、意义句”标注文献摘要能支撑哪一部分。
- `output/abstract_papers.ris`：可导入 Zotero 的文献摘要 RIS。
- `output/abstract_seen_dois.txt`：摘要文献检索去重记录。

## 导入 Zotero

1. 打开 Zotero。
2. 选择 `文件` / `File`。
3. 选择 `导入` / `Import`。
4. 选择 `A file`。
5. 选择 `output/daily_papers.ris`。

建议在 Zotero 中新建 collection，例如：

- `01_黄河三角洲滨海湿地`
- `02_植被类型与土壤微生物`
- `03_盐度EC和环境因子`
- `04_细菌群落多样性`
- `05_真菌群落与FUNGuild`
- `06_FAPROTAX和功能预测`
- `07_测序与群落分析方法`

RIS 文件中会把推荐 collection 写入 Markdown 清单；Zotero 导入 RIS 后如未自动分 collection，可按 Markdown 中的建议手动移动。
