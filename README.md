# Paper Watch

这是一个面向论文写作和 Zotero 导入的文献追踪小工具。它只检索公开论文元数据和摘要，不下载 PDF，不自动登录学校账号，不绕过数据库权限，也不直接连接 Zotero API。

## 你现在最常用的功能

### 摘要文献策展

用途：根据你的摘要草稿，自动找能支撑“背景句、问题句、对象句、方法句、意义句”的相关论文摘要，并生成 Zotero 可导入 RIS。

输出文件：

- `output/abstract_papers.md`：文献清单、分类和为什么能支撑你的摘要
- `output/abstract_papers.ris`：可导入 Zotero 的 RIS 文件
- `output/abstract_seen_dois.txt`：已出现 DOI 记录

### 每日文献追踪器

用途：根据 `config/keywords.yaml` 和 `skills/soil-nitrogen-literature-curation/SKILL.md`，检索滨海湿地氮转化、氮添加、宏基因组和土壤氮循环功能基因相关论文。

输出文件：

- `output/daily_papers.md`
- `output/daily_papers.ris`
- `output/seen_dois.txt`

## 在 GitHub 网页上运行

打开仓库页面后：

1. 点上方 `Actions`。
2. 左侧选择你要运行的工作流。
3. 点右侧 `Run workflow`。
4. 填参数。
5. 再点绿色 `Run workflow`。
6. 等它运行完成后，回到 `Code` 页面查看 `output/` 或 `outputs/` 文件夹。

## 推荐先跑：摘要文献策展

在 `Actions` 左侧选择：

`摘要文献策展`

参数建议：

- `abstract_text`：可以粘贴你的摘要草稿；不填也可以，会使用默认的黄河三角洲滨海湿地模板。
- `mailto`：填你的邮箱，例如 `wdnsswh@gmail.com`。
- `days`：填 `3650`，表示约 10 年。
- `limit`：填 `10`。
- `max_queries`：填 `24`。
- `keep_seen`：第一次运行建议选 `false`；以后想避免重复旧 DOI，可以选 `true`。

运行成功后，把这个文件导入 Zotero：

`output/abstract_papers.ris`

## 每日文献追踪器

在 `Actions` 左侧选择：

`Daily Literature Tracker`

它会生成：

`output/daily_papers.ris`

如果你想改检索主题，优先改：

- `config/keywords.yaml`
- `skills/soil-nitrogen-literature-curation/SKILL.md`

## 在自己电脑上运行

先安装依赖：

```bash
pip install -r requirements.txt
```

运行摘要文献策展：

```bash
python scripts/search_abstract_papers.py --days 3650 --limit 10 --max-queries 24 --mailto your-email@example.com
```

如果你有自己的摘要草稿，可以保存成 `work/abstract_draft.txt`，然后运行：

```bash
python scripts/search_abstract_papers.py --abstract-file work/abstract_draft.txt --days 3650 --limit 10 --max-queries 24 --mailto your-email@example.com
```

运行每日文献追踪：

```bash
python scripts/search_papers.py --days 3650 --limit 20 --max-queries 40 --mailto your-email@example.com
```

## 导入 Zotero

1. 打开 Zotero。
2. 点 `文件`。
3. 点 `导入`。
4. 选择 `A file` 或“文件”。
5. 选择生成的 `.ris` 文件。

常用 RIS 文件：

- `output/abstract_papers.ris`
- `output/daily_papers.ris`

## 为什么有些工作流跑不了

`AI Thesis Draft` 是调用 OpenAI API 自动生成论文初稿的工作流。它需要你先在 GitHub 仓库里添加密钥：

`Settings -> Secrets and variables -> Actions -> New repository secret`

名称必须是：

`OPENAI_API_KEY`

如果没有这个密钥，`AI Thesis Draft` 会失败。找文献和生成 RIS 不需要这个密钥，直接用 `摘要文献策展` 或 `Daily Literature Tracker` 即可。

## 注意

- 本项目不会下载受版权保护的全文。
- 本项目不会自动登录学校账号。
- 本项目不会自动写入 Zotero，只生成 Zotero 可导入的 RIS。
- 如果 GitHub Actions 运行失败，先点失败任务里的红色步骤，复制报错信息，再让 Codex 帮你修。
