#!/usr/bin/env python3
"""
把 questions/edition_XX_YYYY.md(逐屆 Markdown 全文)轉成 question_bank.json。
用法:python3 tools/md_to_bank.py <套件根目錄>
輸出:<套件根目錄>/question_bank.json(若已存在正式版,請勿覆蓋——本工具僅在缺檔時使用)
"""
import json, os, re, sys, glob

SRC = os.path.abspath(sys.argv[1])
cur = json.load(open(os.path.join(SRC, 'curriculum.json'), encoding='utf-8'))
title2id = {t['title']: t['id'] for t in cur}

def parse_table(lines):
    rows = [l.strip() for l in lines if l.strip().startswith('|')]
    cells = [[c.strip() for c in r.strip('|').split('|')] for r in rows]
    cells = [c for c in cells if not all(re.fullmatch(r':?-+:?', x) for x in c)]
    return {'headers': cells[0], 'rows': cells[1:]} if cells else None

editions, questions = {}, []
for path in sorted(glob.glob(os.path.join(SRC, 'questions', 'edition_*.md'))):
    text = open(path, encoding='utf-8').read().replace('\r', '')
    m = re.search(r'^# 第(\d+)屆.*?（(\d{4})）', text, re.M)
    exam, year = m.group(1), int(m.group(2))
    pdf = re.search(r'\[原始試卷 PDF\]\((.*?)\)', text)
    pages = re.findall(r'\]\(\.\./(assets/[^)]+)\)', text)
    editions[exam] = {'exam': exam, 'year': year, 'pdf': pdf.group(1) if pdf else None,
                      'sourceLabel': f'第{exam}屆({year})原卷', 'casePages': pages}
    blocks = re.split(r'^## ', text, flags=re.M)[1:]
    for b in blocks:
        lines = b.split('\n')
        head = lines[0]
        hm = re.match(r'Q(\d+)｜(\d+-\d+)｜(.+)$', head.strip())
        if not hm: raise SystemExit('題頭無法解析:' + head)
        number, qid, topic_title = int(hm.group(1)), hm.group(2), hm.group(3).strip()
        topic = title2id.get(topic_title)
        if not topic: raise SystemExit(f'{qid}:題型「{topic_title}」不在 curriculum')
        q = {'id': qid, 'exam': exam, 'year': year, 'number': number, 'question': '', 'options': [],
             'answer': None, 'explanation': '', 'topic': topic, 'page': None}
        stem, tbl = [], []
        i = 1
        # 題幹(到第一個選項為止),中間可能有表格
        while i < len(lines) and not re.match(r'^- \*\*[A-D]\*\* ', lines[i]):
            l = lines[i]
            cm = re.match(r'^\*\*題目補充：\*\*\s*(.+)$', l.strip())
            if cm: q['context'] = cm.group(1).strip()
            elif l.strip().startswith('|'): tbl.append(l)
            elif l.strip(): stem.append(l.strip())
            i += 1
        q['question'] = ' '.join(stem)
        if tbl: q['table'] = parse_table(tbl)
        while i < len(lines) and re.match(r'^- \*\*[A-D]\*\* ', lines[i]):
            q['options'].append(re.sub(r'^- \*\*[A-D]\*\* ', '', lines[i]).strip()); i += 1
        rest = '\n'.join(lines[i:])
        def grab(label):
            mm = re.search(r'\*\*' + label + r'：\*\*\s*(.+?)(?=\n\n|\Z)', rest, re.S)
            return mm.group(1).strip() if mm else None
        am = re.search(r'\*\*原卷答案：([A-D])\*\*', rest)
        q['answer'] = am.group(1) if am else None
        q['explanation'] = grab('學習解析') or ''
        note = grab('校核註記');  hist = grab('歷史時事提醒');  ctx = grab('題目補充')
        if note: q['note'] = note
        if hist: q['historical'] = True
        if ctx: q['context'] = ctx
        pm = re.search(r'來源：原卷PDF第(\d+)頁', rest)
        q['page'] = int(pm.group(1)) if pm else None
        questions.append(q)

out = {'updated': '2026-09-24', 'exported': '2026-09-27', 'editions': editions, 'questions': questions,
       'note': '由 questions/*.md 轉換;原題與原卷答案取自試卷,解析為本站編寫、非官方解析。'}
dst = os.path.join(SRC, 'question_bank.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'寫入 {dst}:{len(questions)} 題,{len(editions)} 屆;table {sum(1 for q in questions if "table" in q)}、context {sum(1 for q in questions if "context" in q)}、note {sum(1 for q in questions if "note" in q)}、historical {sum(1 for q in questions if q.get("historical"))}')
