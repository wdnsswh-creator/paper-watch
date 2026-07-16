---
name: abstract-literature-curation
description: 自动查找、筛选和整理可支撑硕士论文摘要写作的相关文献摘要，并生成 Zotero 可导入 RIS。Use when the user asks to find literature abstracts, abstract-writing references, background/problem/method/significance support, or wants papers whose abstracts resemble a Yellow River Delta coastal wetland soil bacterial/fungal community thesis abstract.
---

# Abstract Literature Curation

## 目标

围绕用户论文摘要写作，查找“摘要逻辑、研究对象和分析方法相似”的文献，而不是泛泛查找湿地微生物文献。优先寻找可以支撑以下摘要结构的论文摘要：

1. 背景句：黄河三角洲滨海湿地是陆海相互作用强烈的典型生态过渡区，受潮汐、盐分、水分和植被分布等因素影响，土壤环境具有空间异质性。
2. 问题句：土壤微生物连接植物生长、养分循环和湿地生态功能，但不同盐生植物及其空间位置共同作用下，细菌和真菌群落结构、潜在功能及互作网络变化仍认识有限。
3. 对象句：以柽柳、碱蓬和芦苇等典型盐生植物根际土壤，或相似滨海湿地、盐沼、河口湿地植被土壤为对象。
4. 方法句：使用 16S rRNA、ITS、高通量测序、alpha/beta diversity、PCoA/NMDS、PERMANOVA/ANOSIM、LEfSe、相关性、随机森林、FAPROTAX、FUNGuild 和共现网络分析。
5. 意义句：揭示滨海湿地微生物群落对不同生境条件的响应规律，为理解微生物群落组装、植物适应、养分循环和滨海湿地生态功能维持提供依据。

## 当前摘要模板

用户当前摘要风格类似：

> 黄河三角洲滨海湿地是陆海相互作用强烈的典型生态过渡区，受潮汐、盐分、水分和植被分布等因素共同影响，土壤环境具有明显的空间异质性。土壤微生物作为连接植物生长、养分循环和湿地生态功能的重要生物因子，对环境梯度变化十分敏感，但目前关于不同盐生植物及其空间位置共同作用下细菌和真菌群落结构、潜在功能及互作网络变化的认识仍较有限。基于此，本研究选取黄河三角洲滨海湿地中三种典型盐生植物柽柳、碱蓬和芦苇，比较其不同空间位置根际土壤细菌和真菌群落组成、功能预测及共现网络特征，以揭示滨海湿地微生物群落对不同生境条件的响应规律。

## 检索优先级

优先使用这些英文检索主题：

- Yellow River Delta coastal wetland soil microbial community
- Yellow River Delta wetland bacterial fungal community
- Yellow River Delta rhizosphere soil bacteria fungi vegetation
- Tamarix chinensis Suaeda salsa Phragmites australis soil microbial community
- coastal wetland vegetation soil bacterial fungal communities
- coastal wetland soil microbial community spatial heterogeneity
- salinity gradient soil microbial community coastal wetland
- distance from coastline soil microbial diversity
- rhizosphere soil bacterial fungal community halophyte wetland
- high-throughput sequencing bacterial fungal communities saline wetland
- co-occurrence network bacterial fungal community coastal wetland
- FAPROTAX FUNGuild wetland soil microbial community
- environmental drivers soil microbial community salinity pH electrical conductivity

## 筛选规则

把候选文献分成 A/B/C/D。

### A 类：优先作为摘要写作支撑

满足两项以上：

- 研究区是黄河三角洲、滨海湿地、盐沼、河口湿地、潮滩湿地或盐碱湿地。
- 研究对象是土壤或沉积物细菌和真菌，或至少完整研究其中一类。
- 包含植被类型、盐生植物、生境差异、距海梯度、盐度梯度、海陆空间梯度或空间异质性。
- 摘要中明确出现 soil microbial community、bacterial community、fungal community、diversity、composition、function、co-occurrence network、environmental drivers 等表达。
- 方法与用户图件相似：16S/ITS、高通量测序、alpha diversity、PCoA/NMDS、PERMANOVA/ANOSIM、LEfSe、相关性、random forest、FAPROTAX、FUNGuild 或 network analysis。
- 期刊为生态学、微生物学、环境科学、土壤科学领域较可靠期刊，且 DOI、期刊、年份、摘要信息完整。

### B 类：可用于摘要背景或方法表达

满足一项以上：

- 不是黄河三角洲，但研究滨海湿地、盐沼、河口湿地、盐碱土或湿地植被与微生物关系。
- 摘要写法可借鉴，例如先讲环境梯度，再讲微生物群落重要性，再讲研究空白和方法。
- 方法类似但研究对象不完全一致。
- 期刊质量较好，但主题贴合度中等。

### C 类：仅作背景暂存

- 普通土壤微生物、森林、草地或农田微生物，只有少量方法或表达可借鉴。
- 可用于学习摘要句式，但不作为核心引用。

### D 类：排除

- 医学、人体、动物肠道、食品、发酵、污水厂、反应器、纯作物产量研究。
- 只有图、表或 supporting information DOI。
- 无期刊、无 DOI、无摘要，或元数据明显不完整。
- 期刊来源明显不适合作为硕士论文重点引用，且主题贴合度不高。

## 输出要求

输出 Markdown 时必须说明：

- 文献属于 A/B/C 哪一类。
- 可支撑摘要中的哪一类句子：背景句、问题句、对象句、方法句、意义句。
- 与用户摘要相似在哪里。
- 可以借鉴的表达逻辑，但不要整段复制原文摘要。
- Zotero collection 建议。

同时生成 Zotero 可导入 RIS。D 类不写入 RIS。

## 写作注意

- 不要编造摘要、DOI、期刊、年份或结果。
- 不要把文献摘要整段复制到用户论文中；只提炼逻辑和可改写表达。
- 优先保留研究对象和方法接近用户论文的摘要。
- 如果文献只像“盐度梯度”但不是土壤微生物，降低优先级。
- 如果文献只像“细菌/真菌群落”但没有湿地、盐度、植被或环境梯度，降低优先级。
- 输出时明确指出“这篇文献适合支撑摘要哪一类句子”，不要只列文献。
