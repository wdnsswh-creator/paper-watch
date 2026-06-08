#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a thesis analysis draft from Zotero RIS, data tables, and figures."""
from __future__ import annotations
import csv, os, re
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, FIGS, ZOTERO, OUT = ROOT/'data', ROOT/'figures', ROOT/'zotero', ROOT/'outputs'
LOCAL_F = Path(r'F:\2026512玻璃缸')
OUT.mkdir(exist_ok=True)
GENE_PROCESS = {
 'pmoA-amoA':'硝化/氨氧化','pmoB-amoB':'硝化/氨氧化','pmoC-amoC':'硝化/氨氧化','amoA':'硝化/氨氧化','amoB':'硝化/氨氧化','amoC':'硝化/氨氧化','hao':'硝化/氨氧化',
 'napA':'反硝化','narG':'反硝化','narH':'反硝化','narI':'反硝化','nirK':'反硝化','nirS':'反硝化','norB':'反硝化','norC':'反硝化','nosZ':'反硝化',
 'nrfA':'DNRA','nrfH':'DNRA','nifD':'固氮','nifH':'固氮','nifK':'固氮','ureA':'尿素分解','ureB':'尿素分解','ureC':'尿素分解','glnA':'氨同化','gltB':'氨同化','gltD':'氨同化'}
THEMES = {
 '氮添加/氮沉降与微生物群落':'nitrogen addition|nitrogen deposition|fertilizer|n addition|氮添加|氮沉降',
 '土壤氮循环功能基因与宏基因组':'metagenom|functional gene|nitrogen-cycling|nitrogen cycling gene|宏基因组|功能基因',
 '硝化与氨氧化过程':'nitrification|ammonia oxidation|amoa|amoc|hao|硝化|氨氧化',
 '反硝化过程':'denitrification|nirk|nirs|norb|norc|nosz|反硝化',
 'DNRA 与硝酸盐还原过程':'dnra|dissimilatory nitrate|nrfa|nitrate reduction|硝酸盐还原',
 '固氮过程':'nitrogen fixation|nifh|nifd|nifk|固氮',
 '滨海湿地与盐沼生态系统':'coastal wetland|salt marsh|estuary|wetland|滨海湿地|盐沼|河口',
 '环境因子调控':'salinity|ph|ec|moisture|water content|environmental factor|盐度|含水率',
 '湿地植被与根际效应':'spartina|plant|vegetation|rhizosphere|root|互花米草|根际|植被',
 '微生物群落结构与共现网络':'microbial community|community structure|co-occurrence|network|beta diversity'}

def rel(p):
    try: return p.relative_to(ROOT).as_posix()
    except ValueError: return str(p)
def files(folder, suffixes=None):
    return sorted(p for p in folder.rglob('*') if p.is_file() and (suffixes is None or p.suffix.lower() in suffixes)) if folder.exists() else []
def local_files(suffixes):
    return files(LOCAL_F, suffixes) if os.getenv('READ_OPTIONAL_LOCAL_F') == '1' and LOCAL_F.exists() else []
def read_text(p):
    for enc in ('utf-8-sig','utf-8','gbk','latin1'):
        try: return p.read_text(encoding=enc, errors='ignore')
        except Exception: pass
    return ''
def year(s):
    m = re.search(r'(19|20)\d{2}', s or '')
    return m.group(0) if m else (s or '').strip()
def surname(a):
    a = a.strip(); return a.split(',',1)[0].strip() if ',' in a else (a.split()[-1] if a.split() else a)
def cite(authors, y):
    names = [surname(a) for a in authors if a.strip()]; y = year(y) or 'n.d.'
    if not names: return f'Anonymous, {y}'
    if len(names) == 1: return f'{names[0]}, {y}'
    if len(names) == 2: return f'{names[0]} and {names[1]}, {y}'
    return f'{names[0]} et al., {y}'
def parse_ris():
    recs=[]
    for p in files(ZOTERO,{'.ris'}) + local_files({'.ris'}):
        cur={'authors':[],'keywords':[]}
        for raw in read_text(p).splitlines():
            if '  -' not in raw[:8]: continue
            tag,val = raw.split('  -',1); tag=tag.strip(); val=val.strip()
            if tag=='TY': cur={'authors':[],'keywords':[]}
            elif tag in {'TI','T1'}: cur['title']=val
            elif tag=='AU': cur['authors'].append(val)
            elif tag in {'PY','Y1'} and not cur.get('year'): cur['year']=year(val)
            elif tag in {'JO','JF','T2'} and not cur.get('journal'): cur['journal']=val
            elif tag=='DO': cur['doi']=val
            elif tag in {'AB','N2'}: cur['abstract']=val
            elif tag in {'KW','N1'}: cur['keywords'].append(val)
            elif tag=='ER' and cur.get('title'):
                text=' '.join([cur.get('title',''),cur.get('abstract',''),cur.get('journal',''),' '.join(cur.get('keywords',[]))]).lower()
                cur['themes']=[k for k,v in THEMES.items() if re.search(v,text,re.I)] or ['背景文献']
                cur['citation']=cite(cur.get('authors',[]),cur.get('year',''))
                recs.append(cur)
    out={}
    for r in recs:
        k=(r.get('doi') or r.get('title') or '').lower().strip()
        if k and k not in out: out[k]=r
    return sorted(out.values(), key=lambda r:(-len(r['themes']), r.get('year',''), r.get('title','')))
def pick(refs, theme, n=2):
    out=[]
    for r in refs:
        if theme in r['themes'] and r['citation'] not in out: out.append(r['citation'])
        if len(out)>=n: break
    for r in refs:
        if len(out)>=n: break
        if r['citation'] not in out: out.append(r['citation'])
    return '；'.join(out) if out else '参考文献待补充'
def read_table(p):
    try:
        if p.suffix.lower()=='.csv':
            for enc in ('utf-8-sig','utf-8','gbk','latin1'):
                try: return pd.read_csv(p, encoding=enc)
                except Exception: pass
        if p.suffix.lower() in {'.xlsx','.xls'}: return pd.read_excel(p)
    except Exception: return None
    return None
def find_col(cols,pats):
    for c in cols:
        x=re.sub(r'[\s_-]+','',c.lower())
        for pat in pats:
            if re.sub(r'[\s_-]+','',pat.lower()) in x: return c
    return ''
def p_col(cols):
    for c in cols:
        x=c.lower().replace(' ','').replace('_','')
        if x in {'p','pvalue','p值'} or 'pvalue' in x or 'pr(>f)' in x or 'significancep' in x: return c
    return ''
def infer(df):
    cols=[str(c) for c in df.columns]
    return {'gene':find_col(cols,['gene_label','gene','功能基因','基因']),'process':find_col(cols,['process','module','功能模块','氮循环','过程']),'group':find_col(cols,['group_raw','group_label','group','treatment','处理']),'mean':find_col(cols,['mean','平均','均值','abundance']),'sd':find_col(cols,['sd','se','std','标准差','标准误']),'p':p_col(cols),'letter':find_col(cols,['letter','显著性字母'])}
def kind(p, cols):
    t=(p.name+' '+' '.join(cols)).lower()
    for key,label in [('permanova','PERMANOVA'),('anosim','ANOSIM'),('rda','RDA'),('alpha','Alpha 多样性'),('pcoa','Beta 多样性'),('nmds','Beta 多样性')]:
        if key in t: return label
    if 'correlation' in t or 'coefficient' in t or 'pvalue' in t: return '相关性热图'
    if 'module' in t or 'process' in t: return '氮循环模块'
    if 'gene' in t or '功能基因' in t: return '土壤氮循环功能基因丰度'
    return '待判定数据表'
def uniq(df,col,n=24):
    if not col or col not in df: return []
    out=[]
    for v in df[col].dropna().astype(str):
        v=v.strip()
        if v and v not in out: out.append(v)
        if len(out)>=n: break
    return out
def load_data():
    rows=[]; tables={}
    for p in files(DATA,{'.csv','.xlsx','.xls'}) + local_files({'.csv','.xlsx','.xls'}):
        df=read_table(p)
        if df is None:
            rows.append({'file':rel(p),'metrics':'','groups':'','genes':'','mean':'','sd':'','p':'','letter':'','usable':'否','note':'读取失败或格式暂不支持','kind':''}); continue
        df.columns=[str(c) for c in df.columns]; name=rel(p); tables[name]=df; c=infer(df); k=kind(p,df.columns.tolist())
        metrics=uniq(df,c['process']);
        if k not in metrics: metrics.insert(0,k)
        usable='是' if (c['mean'] or c['p'] or c['letter'] or k in {'RDA','PERMANOVA','ANOSIM','相关性热图'}) else '否'
        rows.append({'file':name,'metrics':'；'.join(metrics),'groups':'；'.join(uniq(df,c['group'])),'genes':'；'.join(uniq(df,c['gene'])),'mean':c['mean'],'sd':c['sd'],'p':c['p'],'letter':c['letter'],'usable':usable,'note':'可用于生成结果段' if usable=='是' else '未识别到均值、P 值或显著性字段，需人工核对','kind':k})
    return rows,tables
def table_like(tables, word):
    for name,df in tables.items():
        if word.lower() in name.lower(): return name,df
    return '',None
def sig(x):
    try: return float(x)<0.05
    except Exception: return False
def num(x,d=3):
    try: return '' if pd.isna(x) else f'{float(x):.{d}f}'
    except Exception: return str(x)
def fig_hint(words):
    figs=files(FIGS,None)+local_files({'.png','.jpg','.jpeg','.tif','.tiff','.pdf'}); labels={'alpha':'Alpha 多样性图','pcoa':'PCoA 排序图','nmds':'NMDS 排序图','rda':'RDA 排序图','correlation':'相关性热图','barplot':'土壤氮循环功能基因柱状图','module':'氮循环模块图','gene':'土壤氮循环功能基因图'}; best=''; score0=0
    for f in figs:
        n=f.name.lower(); score=sum(w.lower() in n for w in words)
        if score>score0: best=f"{next((v for k,v in labels.items() if k in n),'相应图表')}（{f.name}，图号待定）"; score0=score
    return best or '相应图表（图号待定）'
def gene_results(tables, refs):
    mean_name,mean_df=table_like(tables,'Nitrogen_Function_Barplot_Data'); _,p_df=table_like(tables,'Nitrogen_Function_Barplot_Pvalues')
    if mean_df is None: return ['当前上传数据中未识别到土壤氮循环功能基因丰度均值表，需补充对应数据表后进一步完善。']
    c=infer(mean_df)
    if not (c['gene'] and c['group'] and c['mean']): return ['当前上传数据中未识别到完整的 Gene、Group/Treatment 和 Mean 列，需补充对应数据表后进一步完善。']
    pmap=defaultdict(list)
    if p_df is not None:
        pc=infer(p_df)
        if pc['gene'] and pc['p']:
            for _,r in p_df.iterrows():
                if sig(r.get(pc['p'])): pmap[str(r.get(pc['gene']))].append((r.get('Control','对照'),r.get('Treatment','处理'),float(r[pc['p']])))
    out=[]; ctext=pick(refs,'土壤氮循环功能基因与宏基因组')
    for g,sub in mean_df.groupby(c['gene'],sort=False):
        g=str(g)
        if g not in GENE_PROCESS and g.replace('_related','') not in GENE_PROCESS: continue
        sub=sub.copy(); sub[c['mean']]=pd.to_numeric(sub[c['mean']],errors='coerce'); sub=sub.dropna(subset=[c['mean']])
        if sub.empty: continue
        hi,lo=sub.loc[sub[c['mean']].idxmax()],sub.loc[sub[c['mean']].idxmin()]; proc=GENE_PROCESS.get(g,GENE_PROCESS.get(g.replace('_related',''),'氮循环相关过程'))
        parts=[f'{t} 与 {ctrl} 间差异显著（P={p:.4f}）' for ctrl,t,p in pmap.get(g,[])]; letters=list(sub[c['letter']].dropna().unique()) if c['letter'] else []
        if parts or len(set(map(str,letters)))>1:
            stat='；'.join(parts) if parts else '不同处理的显著性字母不同，可作为显著差异判断依据'
            out.append(f"{g} 属于{proc}相关土壤氮循环功能基因。根据 {Path(mean_name).name}，该基因丰度在 {hi[c['group']]} 处理中最高（均值 {num(hi[c['mean']],2)}），在 {lo[c['group']]} 处理中最低（均值 {num(lo[c['mean']],2)}）。{stat}，说明该基因响应具有处理依赖性，相关结果可见{fig_hint(['gene','barplot'])}（{ctext}）。")
        else:
            out.append(f"{g} 属于{proc}相关土壤氮循环功能基因。根据 {Path(mean_name).name}，该基因丰度在 {hi[c['group']]} 处理中最高（均值 {num(hi[c['mean']],2)}），在 {lo[c['group']]} 处理中最低（均值 {num(lo[c['mean']],2)}），呈升高趋势，但当前表格未提供该比较的明确显著性依据，需进一步核对显著性，相关结果可见{fig_hint(['gene','barplot'])}（{ctext}）。")
        if len(out)>=10: break
    return out or ['当前上传数据中未识别到重点土壤氮循环功能基因的完整显著性结果，需补充对应数据表后进一步完善。']
def module_results(tables, refs):
    _,df=table_like(tables,'Figure_Process_Module_Abundance_Data')
    if df is None: return ['当前上传数据中未识别到氮循环模块丰度数据表，需补充对应数据表后进一步完善。']
    c=infer(df); out=[]; ctext=pick(refs,'土壤氮循环功能基因与宏基因组')
    if not (c['process'] and c['group'] and c['mean']): return ['当前上传数据中未识别到氮循环模块、处理和均值列，需补充对应数据表后进一步完善。']
    for proc,sub in df.groupby(c['process'],sort=False):
        sub=sub.copy(); sub[c['mean']]=pd.to_numeric(sub[c['mean']],errors='coerce'); sub=sub.dropna(subset=[c['mean']]); hi,lo=sub.loc[sub[c['mean']].idxmax()],sub.loc[sub[c['mean']].idxmin()]
        out.append(f"{proc} 模块在 {hi.get('Group_label',hi[c['group']])} 处理中均值最高（{num(hi[c['mean']],2)}），在 {lo.get('Group_label',lo[c['group']])} 处理中均值最低（{num(lo[c['mean']],2)}）。由于该模块表主要提供均值和离散程度，若无配套 P 值或显著性字母，本段仅表述为变化趋势，不能直接写作显著差异。该结果提示不同氮形态和添加水平对 {proc} 可能具有氮形态依赖性或氮添加水平依赖性，见氮循环模块图（图号待定）（{ctext}）。")
    return out
def alpha_beta(tables):
    out=[]; _,per=table_like(tables,'PERMANOVA'); _,ano=table_like(tables,'ANOSIM')
    if per is not None:
        r=per.iloc[0]; p=r.get(infer(per)['p'] or 'Pr(>F)',''); out.append(f"Beta 多样性或土壤氮循环功能基因整体组成的 PERMANOVA 结果显示，处理因子的解释率为 R2={num(r.get('R2',''),4)}，F={num(r.get('F',''))}，P={num(p,4)}，{'达到显著水平' if sig(p) else '未达到显著水平'}。若 P≥0.05，应表述为整体分离趋势不显著，不能写成处理显著改变整体结构，相关结果见 PCoA/NMDS 排序图（图号待定）。")
    if ano is not None:
        r=ano.iloc[0]; p=r.get('Significance_P',''); out.append(f"ANOSIM 结果显示 R={num(r.get('Statistic_R',''),4)}，P={num(p,4)}，{'达到显著水平' if sig(p) else '未达到显著水平'}。该结果说明组间差异强度有限，应进一步结合具体土壤氮循环功能基因和氮循环模块解释处理效应，见 NMDS 图（图号待定）。")
    return out or ['当前上传数据中未识别到 Alpha/Beta 多样性的完整统计结果，需补充对应数据表后进一步完善。']
def rda_result(tables):
    _,df=table_like(tables,'RDA')
    if df is None: return ['当前上传数据中未识别到 RDA 的完整统计结果，需补充对应数据表后进一步完善。']
    r=df.iloc[0]; p=r.get(infer(df)['p'] or 'Pr(>F)','')
    return [f"RDA 结果显示，环境因子对土壤氮循环功能基因矩阵的约束解释量为 {num(r.get('Variance',''),4)}，F={num(r.get('F',''))}，P={num(p,4)}，整体模型{'达到显著水平' if sig(p) else '未达到显著水平'}。因此，本研究只能表述为 MC、EC、pH、NH4+-N、NO3--N 等环境因子与土壤氮循环功能基因存在关联或可能参与调控，不能写作这些因子直接导致基因变化。相关结果见 RDA 排序图（图号待定）。"]
def corr_results(tables, refs):
    _,coef=table_like(tables,'Correlation_Coefficient'); _,pvals=table_like(tables,'Correlation_Pvalue')
    if coef is None or pvals is None: return ['当前上传数据中未识别到相关性系数表和 P 值表的配套结果，需补充对应数据表后进一步完善。']
    out=[]; ctext=pick(refs,'环境因子调控')
    for _,pr in pvals.iterrows():
        factor=str(pr[pvals.columns[0]])
        for g in pvals.columns[1:]:
            if g not in coef.columns or not sig(pr[g]): continue
            cr=coef[coef[coef.columns[0]].astype(str)==factor]
            if cr.empty: continue
            r=float(cr.iloc[0][g]); direction='正相关' if r>0 else '负相关'; proc=GENE_PROCESS.get(str(g),GENE_PROCESS.get(str(g).replace('_related',''),'氮循环相关过程'))
            out.append((float(pr[g]),f'{factor} 与 {g} 呈显著{direction}（r={r:.3f}，P={float(pr[g]):.4f}）。{g} 属于{proc}相关土壤氮循环功能基因，说明该环境因子可能参与调控 {proc} 过程，但该结果属于相关性证据，不能表述为因果关系。相关结果见相关性热图（图号待定）（{ctext}）。'))
    return [x[1] for x in sorted(out)[:12]] or ['相关性热图未识别到 P<0.05 的环境因子-基因关系，需进一步核对显著性。']
def lit_templates(refs):
    sentence_map={
    '氮添加/氮沉降与微生物群落':['外源氮输入能够改变土壤养分供给和微生物生态位，从而影响微生物群落组成与功能潜力。','氮添加效应通常受添加形态、添加水平和土壤背景共同制约，不同生态系统中微生物群落响应方向并不完全一致。','在讨论氮添加结果时，应区分 NH4+-N 与 NO3--N 的形态差异，并结合处理水平解释群落或功能变化。'],
    '土壤氮循环功能基因与宏基因组':['宏基因组和土壤氮循环功能基因丰度可用于表征微生物介导氮转化过程的潜在功能基础。','土壤氮循环功能基因的变化能够将群落结构差异与硝化、反硝化、DNRA 和固氮等过程联系起来。','相较于单一环境因子，土壤氮循环功能基因更适合解释外源氮输入对潜在氮转化路径的影响。'],
    '硝化与氨氧化过程':['pmoA-amoA、pmoB-amoB、pmoC-amoC 和 hao 等土壤氮循环功能基因常被用于指示硝化或氨氧化相关潜力。','NH4+-N 可作为氨氧化底物，因此其添加可能改变硝化相关土壤氮循环功能基因的丰度或组成。','当硝化相关基因仅呈趋势变化而缺少显著性时，应表述为潜在硝化过程可能发生响应，不能直接判断显著增强。'],
    '反硝化过程':['napA、nirK、nirS、norB、norC 和 nosZ 等土壤氮循环功能基因共同反映反硝化链条不同步骤的潜在变化。','反硝化过程受 NO3--N 供给、碳源、含水率和氧化还原环境共同影响，因此其响应具有明显环境依赖性。','若反硝化相关土壤氮循环功能基因在不同处理间方向不一致，可解释为氮形态或添加水平对反硝化链条存在分段调控。'],
    'DNRA 与硝酸盐还原过程':['nrfA 等土壤氮循环功能基因可用于指示 DNRA 或硝酸盐还原为铵的潜在过程。','DNRA 与反硝化同样依赖硝酸盐底物，但其相对优势可能受碳氮比和还原环境调节。','当 nrfA 或 nrfH 与无机氮、C:N 等因子相关时，可表述为这些因子可能参与 DNRA 过程调控。'],
    '固氮过程':['nifH、nifD 和 nifK 是表征固氮潜力的重要土壤氮循环功能基因。','外源氮输入可能降低微生物对固氮过程的依赖，但不同湿地土壤中该响应仍受环境背景限制。','若固氮相关基因在氮添加处理下下降，可从氮素供给增加削弱固氮需求的角度进行讨论，但需以显著性结果为依据。'],
    '滨海湿地与盐沼生态系统':['滨海湿地和盐沼位于陆海交互带，盐分、水分和植被格局共同影响土壤氮循环过程。','黄河三角洲滨海湿地的氮转化过程需要结合盐碱环境和潮滩水文背景进行解释。','湿地土壤中氮循环响应往往体现为环境梯度与微生物功能潜力共同作用的结果。'],
    '环境因子调控':['pH、EC、含水率和无机氮形态可通过改变底物供给与微生境条件影响土壤氮循环功能基因。','相关性或 RDA 结果只能说明环境因子与土壤氮循环功能基因存在关联或可能参与调控，不能直接证明因果关系。','在滨海湿地盐碱背景下，EC 和 pH 对反硝化、DNRA 或尿素分解相关基因的影响尤其需要结合过程机制解释。'],
    '湿地植被与根际效应':['湿地植被和根际过程能够通过有机碳输入、氧释放和微生境改变影响微生物群落与土壤氮循环功能基因。','互花米草入侵或植被演替可能改变滨海湿地土壤养分状态，并进一步影响氮转化相关微生物过程。','若样地存在不同植被类型，讨论中应将植被效应作为解释氮循环差异的重要背景因素。'],
    '微生物群落结构与共现网络':['微生物群落结构变化可与土壤氮循环功能基因丰度共同用于解释氮转化过程的潜在生态机制。','共现网络可用于描述微生物类群之间的关联结构，但网络关系不等同于直接互作或因果调控。','当群落排序结果不显著而部分基因显著变化时，应强调功能响应的局部性和过程选择性。']}
    out=['## 二、文献分析语言模板','']
    for i,theme in enumerate(THEMES,1):
        out += [f'### 2.{i} {theme}',''] + [f'- {s}（{pick(refs,theme)}）' for s in sentence_map[theme]] + ['']
    return out
def write_outputs(refs, data_rows, tables):
    with (OUT/'15_Zotero文献引用语言清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['题名','作者','年份','期刊','DOI','文献主题','推荐用途','引用标记']); w.writeheader()
        for r in refs:
            use='用于绪论、方法依据和讨论土壤氮循环功能基因机制' if '土壤氮循环功能基因与宏基因组' in r['themes'] else '用于背景综述或讨论补充'
            w.writerow({'题名':r.get('title',''),'作者':'; '.join(r.get('authors',[])),'年份':r.get('year',''),'期刊':r.get('journal',''),'DOI':r.get('doi',''),'文献主题':'；'.join(r['themes']),'推荐用途':use,'引用标记':r['citation']})
    with (OUT/'14_数据结果自动提取清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['数据文件名','识别到的指标','识别到的处理','识别到的功能基因','均值列','SE/SD 列','P 值列','显著性字母列','脚本能否用于写结果段','备注']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in data_rows: w.writerow({'数据文件名':r['file'],'识别到的指标':r['metrics'],'识别到的处理':r['groups'],'识别到的功能基因':r['genes'],'均值列':r['mean'],'SE/SD 列':r['sd'],'P 值列':r['p'],'显著性字母列':r['letter'],'脚本能否用于写结果段':r['usable'],'备注':r['note']})
    cnt=Counter(t for r in refs for t in r['themes']); md=['# 文献与数据综合分析初稿','','## 一、Zotero 文献总体概况','',f'本次共解析 Zotero RIS 文献 {len(refs)} 条。','']
    md.append('按主题自动分类后，主要文献类型包括：'+'；'.join(f'{k} {v} 条' for k,v in cnt.most_common(8))+'。'); md.append(''); md+=lit_templates(refs); md+=['## 三、数据文件识别结果','']
    md += [f"- {r['file']}：识别为 {r['kind']}；处理={r['groups'] or '未识别'}；基因={r['genes'] or '未识别'}；均值列={r['mean'] or '无'}；P 值列={r['p'] or '无'}；显著性字母列={r['letter'] or '无'}；可写结果段={r['usable']}。" for r in data_rows]
    for title,paras in [('四、土壤氮循环功能基因结果段初稿',gene_results(tables,refs)),('五、氮循环模块结果段初稿',module_results(tables,refs)),('六、Alpha/Beta 多样性结果段初稿',alpha_beta(tables)),('七、RDA 与环境因子关联结果段初稿',rda_result(tables)),('八、相关性热图结果段初稿',corr_results(tables,refs))]: md += ['',f'## {title}',''] + [p+'\n' for p in paras]
    md += ['## 九、讨论段可用语言','',f'- 不同氮添加处理对土壤氮循环功能基因的影响更突出地体现为特定氮转化过程的响应差异，应结合显著性和趋势变化进行讨论（{pick(refs,"土壤氮循环功能基因与宏基因组")}）。',f'- NH4+-N 与 NO3--N 添加产生差异响应时，可从底物形态和硝化-反硝化耦合关系解释，但不能在缺少过程速率数据时直接推断实际通量（{pick(refs,"硝化与氨氧化过程",1)}；{pick(refs,"反硝化过程",1)}）。',f'- RDA 或相关性热图只能支持环境因子与土壤氮循环功能基因之间存在关联或可能参与调控，不能直接写作导致（{pick(refs,"环境因子调控")}）。','','## 十、章节结尾段模板','','- 本节结果表明，不同氮添加处理对土壤氮循环功能基因的影响具有明显过程差异。部分基因或模块在特定氮形态和添加水平下呈升高或下降趋势，而整体排序检验并不一定达到显著水平。','- 这些结果提示，滨海湿地土壤氮转化过程并非对外源氮输入作出单一方向响应，而是在 NH4+-N 与 NO3--N 添加、低中高添加水平以及环境因子共同作用下表现出处理依赖性。','- 对于缺少显著性检验的数据，只能作为响应趋势讨论；对于 P<0.05 或显著性字母不同的结果，才可进一步提炼其生态意义并进入机制讨论。','','## 十一、需要人工核对的内容','','- 研究区具体采样地点、采样时间、土层深度、样本重复数和施氮量仍需人工补充。','- 若部分数据只有均值和 SD/SE，缺少 P 值或显著性字母，本文只能写作趋势，不能写作显著差异。','- 图号当前统一写作“图号待定”，正式论文排版时需根据图表顺序统一编号。','- 若需补充读取 F:\\2026512玻璃缸，可在本地运行前设置 READ_OPTIONAL_LOCAL_F=1；GitHub Actions 默认只读取仓库内文件。']
    (OUT/'13_文献数据综合分析初稿.md').write_text('\n'.join(md),encoding='utf-8')
def main():
    refs=parse_ris(); data_rows,tables=load_data(); write_outputs(refs,data_rows,tables)
    print('Wrote outputs/13_文献数据综合分析初稿.md'); print('Wrote outputs/14_数据结果自动提取清单.csv'); print('Wrote outputs/15_Zotero文献引用语言清单.csv')
if __name__ == '__main__': main()
