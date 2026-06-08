Daily Literature Tracker
第一阶段每日文献追踪工具会根据 config/keywords.yaml 和 skills/soil-nitrogen-literature-curation/SKILL.md，从 OpenAlex 和 Crossref 检索与滨海湿地氮转化、氮添加、宏基因组、土壤氮循环功能基因相关的新论文元数据。

本阶段不会连接 Zotero API，不会下载 PDF，不会自动登录学校账号，也不会抓取受版权保护全文。

安装
pip install -r requirements.txt
运行
python scripts/search_papers.py
建议提供邮箱，方便 OpenAlex 和 Crossref 识别正常学术用途：

python scripts/search_papers.py --mailto your-email@example.com
默认会检索最近 7 天、每个数据源最多 50 条记录。可以调整：

python scripts/search_papers.py --days 14 --limit 100 --mailto your-email@example.com
输出文件
运行后会生成：

output/daily_papers.md：每日文献清单，包含 title、authors、year、journal、doi、abstract、url，以及与课题相关的原因。
output/daily_papers.ris：可导入 Zotero 的 RIS 文件，只包含 A、B、C 类文献。
output/seen_dois.txt：已出现过的 DOI，用来避免每天重复推荐。
分类规则
脚本会读取 skills/soil-nitrogen-literature-curation/SKILL.md 作为人工维护的分类依据，并用简单稳定的关键词规则执行第一阶段分类：

A：同时涉及滨海湿地/盐沼/河口、氮循环或氮转化，并且包含宏基因组/功能基因或氮添加信息。
B：与氮循环高度相关，并涉及功能基因、宏基因组、氮添加或滨海湿地中的至少一项。
C：与氮循环、功能基因或关键词配置有一定关系，但课题匹配度较弱。
D：弱相关或信息不足。D 类会写入 Markdown 方便人工查看，但不会写入 RIS。
自定义路径
python scripts/search_papers.py \
  --keywords config/keywords.yaml \
  --skill skills/soil-nitrogen-literature-curation/SKILL.md \
  --output output
如果 config/keywords.yaml 或技能文件不存在，脚本会停止并提示缺失文件路径。
