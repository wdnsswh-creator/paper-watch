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
