#!/usr/bin/env python3
"""解析官方《國際貿易大會考試題彙編》PDF(依命題方向分類的 350 題 + 第十二章信用狀實例)
用法:python3 tools/parse_compilation.py <pdf> <out.json>"""
import fitz, re, sys, json
pdf, out = sys.argv[1], sys.argv[2]
doc = fitz.open(pdf)
TOPIC_RE = re.compile(r'^(二|三|四|五|六|七|八|九|十|十一|十二)、\s*(.+?)\s*$')
CN = {'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'十一':11,'十二':12}
ANS_RE = re.compile(r'^\(([A-D])\)\s*$')
SUB_RE = re.compile(r'^(\d{1,2})\.?\s+([^\(（]{2,30})\s*$')   # 子標題:如「2. 貿易相關機構」
QSTART_RE = re.compile(r'^(\d{1,3})\s*(.*)$')
CASE_INTRO = '請依據後附信用狀及單據'
CASE_PAGES = {1:(58,60),2:(63,65),3:(68,70),4:(73,75),5:(78,80)}   # 附件實體頁

def page_lines(i):
    lines = doc[i].get_text().split('\n')
    # 去掉頁首頁碼
    while lines and (lines[0].strip()=='' or lines[0].strip().isdigit()):
        lines.pop(0)
    return [l.rstrip() for l in lines]

questions = []
SUBNAMES=set()
for _i in range(2,len(doc)):
    for _l in doc[_i].get_text().split('\n'):
        _m=SUB_RE.match(_l.strip())
        if _m and not re.search(r'[，。？；：]',_l): SUBNAMES.add(_m.group(2).strip())
topic_no, topic_name, sub_name, case_set = None, None, None, 0
pending_ans = None
cur = None          # 當前題目 dict
mode = None         # 'stem' | 'opts' | 'sol'
MARK = re.compile(r'\(\s*([A-D])\s*\)')
def valid_marks(text):
    out=[]
    for m in MARK.finditer(text):
        pre=text[max(0,m.start()-4):m.start()]
        if m.start()==0 or pre.endswith('\n') or re.search(r'\s{2}$',pre): out.append(m); continue
        if re.search(r'[A-Za-z]$',pre) or pre.endswith('ICC ') or pre.endswith('ICC'): continue
        out.append(m)
    return out
def split_opts(raw):
    ms=valid_marks(raw); opts={}
    for k,m in enumerate(ms):
        end=ms[k+1].start() if k+1<len(ms) else len(raw)
        L=m.group(1); opts[L]=(opts.get(L,'')+' '+raw[m.end():end]).strip()
    return [re.sub(r'\s+',' ',opts.get(L,'')) for L in 'ABCD']
def flush():
    global cur
    if cur:
        # 分割選項
        raw = '\n'.join(cur.pop('_opts', [])).strip()
        cur['options'] = split_opts(raw)
        for sn in SUBNAMES:
            for k in range(4):
                cur['options'][k]=re.sub(r'\s*\d{1,2}\.?\s*'+re.escape(sn)+r'\s*$','',cur['options'][k]).strip()
        cur['question'] = re.sub(r'\s+', ' ', ' '.join(cur.pop('_stem', []))).strip()
        sol = cur.pop('_sol', [])
        if sol: cur['solution'] = '\n'.join(l for l in sol if l.strip())
        questions.append(cur); cur = None

for i in range(2, len(doc)):            # 第 3 頁起(索引 2)
    pno = i + 1
    for l in page_lines(i):
        s = l.strip()
        if not s: continue
        m = TOPIC_RE.match(s)
        if m and mode != 'stem':
            flush(); topic_no, topic_name, sub_name = CN[m.group(1)], m.group(2), None; continue
        if mode == 'opts' and not valid_marks(s):
            ms = SUB_RE.match(s)
            if ms and not re.search(r'[，。？；：]', s):
                flush(); sub_name = ms.group(2).strip(); continue
        if re.match(r'^附件\s*[:：]', s):
            flush(); mode=None; continue
        if s.startswith(CASE_INTRO):
            flush(); case_set += 1; sub_name = f'實例{case_set}'; continue
        if s.startswith('解答算式') or s.startswith('解答'):
            if cur: mode = 'sol'; cur['_sol'] = []; continue
        m = ANS_RE.match(s)
        if m:
            flush(); pending_ans = m.group(1); mode = None; continue
        if pending_ans is None and cur is None:
            m = SUB_RE.match(s)
            if m: sub_name = m.group(2).strip(); continue
            continue   # 其他雜訊
        if pending_ans is not None and cur is None:
            m = QSTART_RE.match(s)
            if not m: continue
            num = int(m.group(1)); rest = m.group(2).strip()
            cur = {'topic_no': topic_no, 'topic': topic_name, 'sub': sub_name, 'num': num, 'answer': pending_ans,
                   'page': pno, 'case_set': case_set if topic_no==12 else None, '_stem': [], '_opts': [], '_sol': []}
            pending_ans = None; mode = 'stem'
            s = rest
            if not s: continue
        if cur is None: continue
        if mode == 'sol':
            cur['_sol'].append(s); continue
        if mode == 'stem':
            ma=[m for m in valid_marks(s) if m.group(1)=='A']
            if ma:
                mode = 'opts'; m=ma[0]
                if s[:m.start()].strip(): cur['_stem'].append(s[:m.start()].strip())
                cur['_opts'].append(s[m.start():]); continue
        if mode == 'stem': cur['_stem'].append(s)
        elif mode == 'opts': cur['_opts'].append(s)
flush()

# 檢查
bad = [q for q in questions if any(not o for o in q['options'])]
print(f'共解析 {len(questions)} 題;選項不完整 {len(bad)} 題')
from collections import Counter
print('各章題數:', dict(sorted(Counter((q['topic_no'], q['topic']) for q in questions).items())))
print('有解答算式:', sum(1 for q in questions if q.get('solution')))
for q in bad[:8]: print('  BAD', q['topic_no'], q['num'], q['question'][:40], q['options'])
json.dump({'questions': questions, 'case_pages': CASE_PAGES}, open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
