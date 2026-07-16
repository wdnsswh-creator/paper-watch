---
name: soil-nitrogen-literature-curation
description: 根据用户论文查重版本，检索、筛选并整理黄河三角洲滨海湿地土壤细菌/真菌群落、植被类型、距海梯度、盐度和功能预测相关文献。
---

# 任务定位

本 skill 用于帮助用户围绕当前 Word 文档主题重新筛选文献。它不是普通文献推荐器，也不是只按关键词机械抓取论文。它的任务是根据用户论文现有内容，对新论文进行相关度判断、去重、分类和阅读优先级排序，并输出可导入 Zotero 的 RIS 文件。

# 当前论文主题

用户当前论文方向为：黄河三角洲滨海湿地不同植被类型和距海梯度下土壤细菌与真菌群落结构、多样性、优势类群及功能预测特征。

核心对象包括：

- 黄河三角洲；
- 滨海湿地、盐沼、河口湿地、盐碱土壤；
- 距海梯度、coastal-inland gradient、salinity gradient；
- Tamarix chinensis、Suaeda salsa、Phragmites australis；
- 土壤 EC、盐度、pH、盐分含量等理化因子；
- 土壤细菌群落、土壤真菌群落、细菌和真菌多样性；
- 16S rRNA、ITS、高通量测序、OTU、alpha diversity、beta diversity；
- PCoA、NMDS、Bray-Curtis、UpSet、Venn、two-way ANOVA；
- Proteobacteria、Chloroflexi、Actinobacteriota、Bacteroidota、Gemmatimonadota、Acidobacteriota、Desulfobacterota；
- Ascomycota、Basidiomycota、Chytridiomycota、Rozellomycota；
- FAPROTAX、FUNGuild、Saprotroph、Pathotroph、Symbiotroph、Pathogen。

# 用户当前实验维度

优先寻找与以下实验维度相似的文献：

- 两个距海远近不同的采样点，或 coastal-inland gradient、distance from coastline、salinity gradient 等空间梯度设计；
- 三种植物或多种湿地植被类型比较；
- 同时研究土壤细菌和真菌，或至少对其中一类微生物群落有完整分析；
- 能够把土壤理化性质与微生物群落结构、多样性、差异类群或功能预测联系起来。

# 优先参考的图件结构

优先保留具有下列图件或分析类型的文献。这些图件不要求每篇文献全部具备，但相似的部分必须尽量像用户论文的分析方法。比如，如果文献用于参考 beta diversity，就最好同样使用 PCoA/NMDS/PERMANOVA/ANOSIM；如果用于参考功能预测，就最好同样使用 FAPROTAX 或 FUNGuild。

1. Figure 1：土壤理化性质图。EC、pH、Salt 或 salinity/salt content 的柱状图，用于交代环境梯度。
2. Figure 2：测序信息或 alpha diversity 图。Good's coverage、Sobs、Shannon、Simpson、Chao1 等。
3. Figure 3：OTU 共享图。细菌和真菌 shared/unique OTUs，UpSet 或 Venn。
4. Figure 4：beta diversity 图。PCoA、NMDS、Bray-Curtis、PERMANOVA 或 ANOSIM。
5. Figure 5：门水平群落组成图。细菌和真菌 phylum composition 堆叠柱状图。
6. Figure 6：LEfSe 差异类群图。LDA bar plot 或 cladogram。
7. Figure 7：环境因子驱动分析图。pH、EC、Salt 与主要门的相关性热图，以及 random forest 等环境驱动分析。
8. Figure 8：功能预测图。细菌 FAPROTAX 和真菌 FUNGuild 营养型/功能类群。

# 检索关键词

优先使用以下英文关键词组合：

- Yellow River Delta wetland microbial community
- Yellow River Delta coastal wetland soil microorganisms
- coastal wetland vegetation soil microbial community
- vegetation type soil bacterial fungal community
- distance from coastline soil microbial diversity
- salinity gradient soil microbial community
- soil electrical conductivity microbial community
- Tamarix chinensis Suaeda salsa Phragmites australis soil microbial community
- two sampling sites three vegetation types bacterial fungal community
- coastal inland sampling sites vegetation soil microbial community
- bacterial and fungal communities coastal wetland soil
- FAPROTAX FUNGuild wetland soil microbial community
- fungal trophic mode coastal wetland soil
- 16S ITS sequencing saline wetland soil microbial community
- LEfSe LDA cladogram wetland soil microbial community
- correlation heatmap random forest environmental drivers soil microbial community

# 文献相关度分级

将文献分为四级。

## A 类：必须阅读

满足以下条件之一：

- 直接研究黄河三角洲、滨海湿地、盐沼或河口湿地土壤细菌/真菌群落；
- 同时涉及植被类型或距海/盐度梯度与土壤微生物群落；
- 同时涉及土壤理化因子和细菌/真菌群落结构、多样性或优势类群；
- 同时包含 alpha diversity、beta diversity、群落组成、环境因子相关性或功能预测中的多个分析环节；
- 研究设计或图件结构可直接对标用户的 Figure 1-8 框架；
- 直接使用 FAPROTAX、FUNGuild 或类似方法解释滨海湿地土壤微生物功能预测；
- 研究对象包括 Tamarix chinensis、Suaeda salsa、Phragmites australis 等典型滨海湿地植被，并分析土壤微生物。
- 期刊规格较好，或至少为本领域常见、可正常引用的生态学、微生物学、环境科学、土壤科学期刊。

## B 类：建议阅读

满足以下条件之一：

- 研究其他滨海湿地、盐碱土、盐沼或河口生态系统中的土壤微生物群落；
- 涉及盐度、EC、pH、土壤理化性质对细菌或真菌群落的影响；
- 涉及 16S、ITS、高通量测序、alpha diversity、beta diversity、PCoA、NMDS 等方法，可为方法或讨论提供支持；
- 涉及湿地植被对土壤微生物群落的影响，但研究区不是黄河三角洲。

## C 类：可选阅读

满足以下条件之一：

- 只涉及普通土壤微生物多样性或群落组成；
- 只涉及湿地生态背景，但微生物部分较弱；
- 与盐度、植被或功能预测有间接关系；
- 可用于论文引言、方法或背景部分。
- 研究方法相似但期刊质量、摘要完整度或主题贴合度一般。

## D 类：排除

满足以下条件之一：

- 纯医学、人体、动物、肠道微生物研究；
- 纯食品、发酵、工业微生物或药用植物研究；
- 纯水处理、污水厂、饮用水或反应器研究；
- 只研究作物产量或农业生产，不涉及土壤微生物群落；
- 与湿地、盐碱土、植被梯度、细菌/真菌群落或功能预测无关；
- 没有 DOI、摘要或基本出处信息。
- 期刊来源明显不适合作为硕士论文重点引用文献，除非方法与用户论文高度一致且只作为方法参考。

# Zotero 分类规则

推荐 collection：

- 01_黄河三角洲滨海湿地
- 02_植被类型与土壤微生物
- 03_盐度EC和环境因子
- 04_细菌群落多样性
- 05_真菌群落与FUNGuild
- 06_FAPROTAX和功能预测
- 07_测序与群落分析方法
- 08_低相关暂存

# RIS 文件要求

生成 RIS 文件时，至少包含：

- TY  - JOUR
- TI  - 标题
- AU  - 作者
- JO  - 期刊
- PY  - 年份
- DO  - DOI
- AB  - 摘要
- UR  - URL
- ER  -

# 禁止事项

- 不得只根据标题判断相关性，必须尽量结合摘要。
- 不得把所有包含 microbial community 的文献都判定为高相关。
- 不得把医学、人体、动物肠道微生物文献误判为用户论文相关文献。
- 不得编造 DOI、期刊、年份或摘要。
- 不得自动批量下载受版权保护的全文。
- 不得模拟登录学校账号或绕过数据库访问限制。
- 当前主题不是氮添加论文时，不要把“土壤氮循环功能基因”作为筛选核心；只有文献同时有湿地微生物和氮循环背景时，才作为补充文献保留。
