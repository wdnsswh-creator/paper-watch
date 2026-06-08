---
name: soil-nitrogen-literature-curation
description: 每日检索、筛选并整理滨海湿地氮转化、氮添加、宏基因组和土壤氮循环功能基因相关文献。
---

# 任务定位

本 skill 用于帮助用户每天筛选与博士论文高度相关的新文献。它不是普通文献推荐器，也不是只按关键词机械抓取论文。它的任务是根据用户研究主题，对新论文进行相关度判断、去重、分类和阅读优先级排序。

# 用户研究主题

用户研究方向为：滨海湿地土壤氮转化过程对不同形态和水平氮素添加的响应及其调控机制。

核心对象包括：

- 滨海湿地；
- 盐碱土壤；
- NH4+-N 添加；
- NO3--N 添加；
- 土壤氮循环功能基因；
- 宏基因组；
- 硝化；
- 反硝化；
- DNRA；
- 固氮；
- amoA；
- hao；
- nirK；
- nirS；
- norB；
- norC；
- nosZ；
- nrfA；
- nifH；
- nifD；
- nifK。

# 检索关键词

优先使用以下英文关键词组合：

- coastal wetland nitrogen addition
- saline-alkali soil nitrogen cycling
- soil nitrogen transformation metagenomics
- nitrogen cycling functional genes
- soil nitrogen cycling genes
- nitrification denitrification DNRA nitrogen fixation
- ammonium nitrate addition wetland soil
- NH4 addition NO3 addition soil nitrogen cycling
- amoA hao nirK nirS norB nosZ nrfA nifH
- Yellow River Delta wetland nitrogen cycling

# 文献相关度分级

将文献分为四级。

## A 类：必须阅读

满足以下条件之一：

- 直接研究滨海湿地或盐碱湿地氮循环；
- 直接研究氮添加对土壤氮转化过程的影响；
- 同时涉及宏基因组和土壤氮循环功能基因；
- 涉及 amoA、hao、nirK、nirS、norB、norC、nosZ、nrfA、nifH、nifD、nifK 等关键基因，并与氮转化过程建立机制联系。

## B 类：建议阅读

满足以下条件之一：

- 研究湿地、农田、草地或森林土壤氮循环；
- 涉及硝化、反硝化、DNRA 或固氮；
- 可以为论文讨论部分提供机制支撑；
- 与氮添加、盐碱环境、微生物功能基因相关，但研究场景不是滨海湿地。

## C 类：可选阅读

满足以下条件之一：

- 只涉及微生物群落结构；
- 只涉及普通氮素响应；
- 与用户课题有间接关系；
- 可用于论文引言或背景部分。

## D 类：排除

满足以下条件之一：

- 纯医学、人体、动物、肠道微生物研究；
- 纯作物产量研究；
- 只研究水体氮污染但不涉及土壤或沉积物；
- 与氮循环无关；
- 只有方法学但无法支撑用户论文；
- 没有 DOI、摘要或基本出处信息。

# 输出格式

每天输出一个 Markdown 文件，格式如下：

## 今日文献追踪结果

检索日期：

新增文献总数：

去重后文献总数：

A 类文献数量：

B 类文献数量：

C 类文献数量：

## A 类：必须阅读

每篇文献必须包含：

- 标题；
- 作者；
- 年份；
- 期刊；
- DOI；
- 摘要核心内容；
- 与用户课题的相关理由；
- 建议放入 Zotero 的 collection；
- 是否建议优先阅读。

## B 类：建议阅读

格式同上。

## C 类：可选阅读

格式同上。

# Zotero 分类规则

推荐 collection：

- 01_滨海湿地氮循环
- 02_氮添加实验
- 03_土壤氮循环功能基因
- 04_宏基因组方法
- 05_硝化与反硝化
- 06_DNRA与固氮
- 07_讨论部分可引用文献
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
- ER  -

# 禁止事项

- 不得只根据标题判断相关性，必须结合摘要。
- 不得把所有包含 nitrogen 的文献都判定为高相关。
- 不得把医学、人体、动物肠道微生物文献误判为用户论文相关文献。
- 不得编造 DOI、期刊、年份或摘要。
- 不得自动批量下载受版权保护的全文。
- 不得模拟登录学校账号或绕过数据库访问限制。
- 不得把“functional genes”随意翻译成普通功能基因，涉及用户论文时必须写作“土壤氮循环功能基因”。
