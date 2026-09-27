#!/usr/bin/env python3
"""合併 compilation.json + overrides.json + explanations.json → trade/official_data.js(window.OFFICIAL)"""
import json, os, re, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=os.path.join(ROOT,'data','itce-pack','official')
comp=json.load(open(os.path.join(D,'compilation.json'),encoding='utf-8'))
ov=json.load(open(os.path.join(D,'overrides.json'),encoding='utf-8'))
ex=json.load(open(os.path.join(D,'explanations.json'),encoding='utf-8')) if os.path.exists(os.path.join(D,'explanations.json')) else {}
bank={q['id']:q for q in json.load(open(os.path.join(ROOT,'data','itce-pack','question_bank.json'),encoding='utf-8'))['questions']}
PUA={'':'①','':'②','':'③','':'④','':'⑤','':'⑥','':'⑦','':"'"}
def clean(t): 
    for k,v in PUA.items(): t=t.replace(k,v)
    return t
qs={q['id']:q for q in comp['questions']}
for k,v in ov.items():
    if k.startswith('_'): continue
    if v.get('new'):
        r={kk:vv for kk,vv in v.items() if kk!='new'}; r['id']=k; r.setdefault('caseSet',None); qs[k]=r
    else:
        qs[k].update({kk:vv for kk,vv in v.items()})
out=[]
for q in qs.values():
    q['q']=clean(q['q']); q['o']=[clean(o) for o in q['o']]
    if q['chapter']==12 and q.get('caseSet') in (None,''):
        import re as _re; _m=_re.match(r'O12-S(\d)',q['id']); q['caseSet']=int(_m.group(1)) if _m else None
    if q.get('caseSet') is not None: q['caseSet']=int(q['caseSet'])
    e=ex.get(q['id'])
    if e: q['e']=e; q['eSrc']='own'
    elif q.get('sameAs') and q['sameAs'] in bank:
        b=bank[q['sameAs']]; q['e']=b['explanation']; q['eSrc']='same:'+q['sameAs']
        if b.get('note'): q['note']=b['note']
    elif q.get('solution'): q['e']='官方解答算式:\n'+q['solution']; q['eSrc']='official'
    else: q['e']=''; q['eSrc']=''
    if q.get('solution') and q['eSrc']!='official': q['e']=q['e'].rstrip()+'\n\n官方解答算式:\n'+q['solution']
    out.append(q)
def key(q): return (q['chapter'], q.get('caseSet') or 0, q['num'])
out.sort(key=key)
missing=[q['id'] for q in out if not q['e']]
print(f'題數 {len(out)};有解析 {len(out)-len(missing)};缺解析 {len(missing)}', missing[:20], '…' if len(missing)>20 else '')
# 附件影像:複製到 trade/assets
src=os.path.join(D,'assets'); dst=os.path.join(ROOT,'trade','assets'); os.makedirs(dst,exist_ok=True)
sets={}
for n,s in comp['caseSets'].items():
    pages=[]
    for p in s['pages']:
        fn=os.path.basename(p)
        if os.path.exists(os.path.join(src,fn)):
            import shutil; shutil.copyfile(os.path.join(src,fn),os.path.join(dst,fn)); pages.append('assets/'+fn)
    sets[n]={'pages':pages,'lc':s['lc'],'issue':s['issue']}
payload={'source':comp['source'],'questions':out,'caseSets':sets}
with open(os.path.join(ROOT,'trade','official_data.js'),'w',encoding='utf-8') as f:
    f.write('/* 由 tools/finalize_official.py 產生;來源:官方試題彙編(依命題方向分類之題庫);解析標示 own=本站編寫、same=沿用同題屆次解析、official=原卷解答算式;皆非主辦單位官方解析 */\nwindow.OFFICIAL=')
    json.dump(payload,f,ensure_ascii=False,separators=(',',':')); f.write(';\n')
print('已輸出 trade/official_data.js', os.path.getsize(os.path.join(ROOT,'trade','official_data.js'))//1024,'KB;附件',sum(len(s['pages']) for s in sets.values()),'張')
