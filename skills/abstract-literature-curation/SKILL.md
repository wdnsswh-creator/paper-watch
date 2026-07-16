---
name: abstract-literature-curation
description: 自动查找和筛选可支撑硕士论文摘要写作的相关文献摘要。Use when the user asks to find literature abstracts, abstract-writing references, background/problem/method/significance support, or wants papers whose abstracts resemble a Yellow River Delta coastal wetland soil bacterial/fungal community thesis abstract.
---

# Abstract Literature Curation

## 目标

围绕用户论文摘要写作，查找“摘要逻辑和研究对象相似”的文献，而不是泛泛找湿地微生物文献。优先寻找可以支撑以下摘要结构的论文摘要：

1. 背景句：黄河三角洲/滨海湿地受陆海相互作用影响，形成盐分、水分、植被或海陆空间梯度。
2. 问题句：环境梯度可能影响土壤细菌和真菌群落组成、生态功能、共现关系，但机制仍不清楚。
3. 对象句：以典型盐生植物柽柳、碱蓬、芦苇根际土壤，或相似湿地植被/盐度梯度土壤为对象。
4. 方法句：高通量测序、16S rRNA、ITS、alpha/beta diversity、PCoA/NMDS、PERMANOVA/ANOSIM、LEfSe、相关性、随机森林、FAPROTAX、FUNGuild。
5. 意义句：解释湿地土壤微生物群落对环境梯度和植被生境的响应，为滨海湿地生态功能、植物适应或盐碱地生态修复提供依据。

## 用户摘要写作模板

用户当前摘要风格类似：

> 黄河三角洲滨海湿地受陆海相互作用影响显著，形成了明显的盐分、水分和植被空间梯度，这些环境差异可能深刻影响土壤微生物群落组成及其生态功能。土壤细菌和真菌是湿地养分循环、植物适应和生态系统稳定的重要参与者，但不同盐生植物生境及海陆位置变化下微生物群落结构、功能和共现关系的响应机制仍不清楚。因此，本研究以黄河三角洲典型盐生植物柽柳、碱蓬和芦苇根际土壤为对象，采用高通量测序技术分析不同生境下土壤细菌和真菌群落多样性、组成结构、潜在功能及共现网络变化特征。

## 检索优先级

优先使用这些英文检索主题：

- Yellow River Delta coastal wetland soil microbial community abstract
- Yellow River Delta wetland bacterial fungal community
- coastal wetland vegetation soil bacterial fungal communities
- salinity gradient soil microbial community coastal wetland
- distance from coastline soil microbial diversity
- Tamarix chinensis Suaeda salsa Phragmites australis soil microbial community
- rhizosphere soil bacterial fungal community halophyte wetland
- high-throughput sequencing bacterial fungal communities saline wetland
- FAPROTAX FUNGuild wetland soil microbial community
- co-occurrence network bacterial fungal community coastal wetland
- environmental drivers soil microbial community salinity pH electrical conductivity

## 筛选规则

把候选文献分成 A/B/C/D。

### A 类：优先作为摘要写作支撑

满足两项以上：

- 研究区是黄河三角洲、滨海湿地、盐沼、河口湿地、潮滩湿地或盐碱湿地。
- 研究对象是土壤/沉积物细菌和真菌，或至少完整研究其中一类。
- 有植被类型、盐生植物、生境差异、距海梯度、盐度梯度或海陆梯度。
- 摘要中明确出现 soil microbial community、bacterial community、fungal community、diversity、composition、function、co-occurrence network、environmental drivers 等表达。
- 方法与用户图件相似：16S/ITS、高通量测序、alpha diversity、PCoA/NMDS、PERMANOVA/ANOSIM、LEfSe、相关性、random forest、FAPROTAX、FUNGuild。
- 期刊为生态学、微生物学、环境科学、土壤科学领域较可靠期刊，且 DOI、期刊、年份、摘要信息完整。

### B 类：可用于摘要背景或方法表达

满足一项以上：

- 不是黄河三角洲，但研究滨海湿地、盐沼、河口湿地、盐碱土或湿地植被-微生物关系。
- 摘要写法可借鉴，例如先讲环境梯度，再讲微生物群落重要性，再讲研究空白和方法。
- 方法类似但研究对象不是完全一致。
- 期刊质量较好，但主题贴合度中等。

### C 类：仅作背景暂存

- 普通土壤微生物、森林/草地/农田微生物，只有少量方法或表达可借鉴。
- 可用于学习摘要句式，但不作为核心引用。

### D 类：排除

- 医学、人体、动物肠道、食品、发酵、污水厂、反应器、纯作物产量研究。
- 只有图、表或 supporting information DOI。
- 无期刊、无 DOI、无摘要，或元数据明显不完整。
- 期刊来源明显不适合作为硕士论文重点引用，且主题贴合度不高。

## 输出格式

输出 Markdown，按以下结构：

```markdown
# 摘要支撑文献筛选结果

## 可直接支撑摘要逻辑的 A 类文献

### 1. Title
- 作者/年份/期刊/DOI：
- 摘要类型：背景句 / 问题句 / 对象方法句 / 结果功能句 / 意义句
- 与用户摘要的相似点：
- 可借鉴表达：
- 可支撑用户摘要中的哪一句：
- Zotero collection 建议：

## 可用于摘要背景或方法表达的 B 类文献

...

## 可借鉴的摘要句式

- 背景句：
- 问题句：
- 方法句：
- 意义句：
```

## 写作注意

- 不要编造摘要、DOI、期刊、年份或结果。
- 不要把文献摘要整段复制到用户论文中；只提炼逻辑和可改写表达。
- 优先保留研究对象和方法接近用户论文的摘要。
- 如果文献只像“盐度梯度”但不是土壤微生物，降低优先级。
- 如果文献只像“细菌/真菌群落”但没有湿地、盐度、植被或环境梯度，降低优先级。
- 输出时明确指出“这篇文献适合支撑摘要哪一类句子”，不要只列文献。
