#!/usr/bin/env python3
"""
把「國貿大會考題庫與教材參考套件」轉成網站可讀的 trade/past_data.js,並執行驗收。

用法:python3 tools/build_past.py <套件根目錄>
輸入:question_bank.json、curriculum.json、assets/(casePages 影像)
輸出:trade/past_data.js(window.PAST = {...})、trade/assets/(影像複製)
驗收基準(CODEX_HANDOFF.md):5 屆 × 100 題 = 500 題;每題 4 選項、1 原卷答案、非空解析;
12 個教材;15 張有效附件;教材 drills 題號皆能對應題庫。
"""
import json, os, re, shutil, sys, hashlib

if len(sys.argv) < 2:
    print(__doc__); sys.exit(1)
ALLOW_MISSING = '--allow-missing-assets' in sys.argv
SRC = os.path.abspath([a for a in sys.argv[1:] if not a.startswith('--')][0])
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JS = os.path.join(ROOT, 'trade', 'past_data.js')
OUT_ASSETS = os.path.join(ROOT, 'trade', 'assets')

def load(name):
    p = os.path.join(SRC, name)
    with open(p, encoding='utf-8') as f:
        return json.load(f)

qb = load('question_bank.json')
cur = load('curriculum.json')
errors, warns = [], []

# ---------- editions ----------
raw_ed = qb.get('editions', {})
editions = {}
if isinstance(raw_ed, list):
    for e in raw_ed:
        k = str(e.get('exam') or e.get('id') or e.get('edition'))
        editions[k] = e
else:
    editions = {str(k): v for k, v in raw_ed.items()}

# ---------- questions ----------
questions = qb.get('questions', [])
if not isinstance(questions, list):
    errors.append('questions 不是陣列')
norm_q = []
ids = set()
LETTER = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'Ａ': 0, 'Ｂ': 1, 'Ｃ': 2, 'Ｄ': 3}
for q in questions:
    qid = str(q.get('id', ''))
    if not qid or qid in ids:
        errors.append(f'題目 id 缺失或重複:{qid!r}')
    ids.add(qid)
    opts = q.get('options', [])
    if isinstance(opts, dict):
        opts = [opts.get(k, '') for k in ('A', 'B', 'C', 'D')]
    opts = [o if isinstance(o, str) else (o.get('text') if isinstance(o, dict) else str(o)) for o in opts]
    if len(opts) != 4:
        errors.append(f'{qid}:選項數 {len(opts)} ≠ 4')
    ans = q.get('answer', '')
    a_idx = LETTER.get(str(ans).strip().upper()[:1], -1) if isinstance(ans, str) else (int(ans) if isinstance(ans, int) else -1)
    if a_idx < 0 or a_idx > 3:
        errors.append(f'{qid}:原卷答案無法解析:{ans!r}')
    expl = (q.get('explanation') or '').strip()
    if not expl:
        errors.append(f'{qid}:解析為空')
    exam = str(q.get('exam', qid.split('-')[0]))
    number = q.get('number')
    try:
        number = int(number)
    except Exception:
        m = re.match(r'^\d+-(\d+)$', qid)
        number = int(m.group(1)) if m else 0
        warns.append(f'{qid}:number 缺失,由 id 推得 {number}')
    table = q.get('table')
    if table is not None:
        if not (isinstance(table, dict) and isinstance(table.get('headers'), list) and isinstance(table.get('rows'), list)):
            errors.append(f'{qid}:table 缺 headers/rows')
    norm_q.append({
        'id': qid, 'exam': exam, 'year': q.get('year'), 'number': number,
        'q': (q.get('question') or '').strip(), 'o': opts, 'a': a_idx, 'ans': str(ans),
        'e': expl, 'topic': q.get('topic'), 'page': q.get('page'),
        'table': table, 'context': q.get('context'), 'note': q.get('note'),
        'historical': bool(q.get('historical', False)),
    })

# per-edition counts
by_exam = {}
for q in norm_q:
    by_exam.setdefault(q['exam'], []).append(q)
for ex, qs in sorted(by_exam.items()):
    nums = sorted(x['number'] for x in qs)
    if len(qs) != 100:
        errors.append(f'第 {ex} 屆題數 {len(qs)} ≠ 100')
    if nums != list(range(1, 101)):
        missing = sorted(set(range(1, 101)) - set(nums))
        errors.append(f'第 {ex} 屆題號不連續,缺:{missing[:10]}{"…" if len(missing) > 10 else ""}')
if len(by_exam) != 5:
    errors.append(f'屆數 {len(by_exam)} ≠ 5(實際:{sorted(by_exam)})')
if len(norm_q) != 500:
    errors.append(f'總題數 {len(norm_q)} ≠ 500')

# ---------- assets / casePages ----------
os.makedirs(OUT_ASSETS, exist_ok=True)
asset_count = 0
ed_out = {}
for ex, e in editions.items():
    pages = e.get('casePages') or []
    if len(pages) != 3:
        errors.append(f'第 {ex} 屆 casePages 數 {len(pages)} ≠ 3')
    rel_out = []
    for p in pages:
        src = os.path.join(SRC, p)
        if not os.path.isfile(src):
            (warns if ALLOW_MISSING else errors).append(f'第 {ex} 屆附件不存在:{p}' + ('(暫以路徑保留)' if ALLOW_MISSING else ''))
            if ALLOW_MISSING: rel_out.append('assets/' + f'{ex}-' + os.path.basename(p))
            continue
        with open(src, 'rb') as f:
            head = f.read(4)
        if not (head[:3] == b'\xff\xd8\xff' or head[:4] == b'\x89PNG'):
            errors.append(f'第 {ex} 屆附件不是有效 JPEG/PNG:{p}')
            continue
        dst_name = f'{ex}-' + os.path.basename(p)
        shutil.copyfile(src, os.path.join(OUT_ASSETS, dst_name))
        rel_out.append('assets/' + dst_name)
        asset_count += 1
    ed_out[ex] = {'exam': ex, 'year': e.get('year'), 'pdf': e.get('pdf'), 'sourcePage': e.get('sourcePage'),
                  'sourceLabel': e.get('sourceLabel'), 'casePages': rel_out}
for ex in by_exam:
    if ex not in ed_out:
        errors.append(f'第 {ex} 屆缺少 editions 資料')
if asset_count != 15:
    (warns if ALLOW_MISSING else errors).append(f'有效附件 {asset_count} ≠ 15')

# ---------- curriculum ----------
topics = cur.get('topics') if isinstance(cur, dict) else cur
if isinstance(cur, dict) and topics is None:
    # 可能是 {id: {...}} 或 {curriculum:[...]}
    topics = cur.get('curriculum') or cur.get('lessons') or [dict(id=k, **v) for k, v in cur.items() if isinstance(v, dict)]
if not isinstance(topics, list):
    errors.append('curriculum.json 無法辨識教材陣列'); topics = []
if len(topics) != 12:
    errors.append(f'教材數 {len(topics)} ≠ 12')
topic_ids = set()
drill_missing = 0
for t in topics:
    tid = str(t.get('id', ''))
    topic_ids.add(tid)
    drills = t.get('drills') or []
    flat = []
    for d in drills:
        if isinstance(d, str): flat.append(d)
        elif isinstance(d, dict): flat.append(str(d.get('id') or d.get('question') or ''))
        elif isinstance(d, list): flat.extend(str(x) for x in d)
    for d in flat:
        if d and d not in ids:
            drill_missing += 1
            errors.append(f'教材 {tid} 的 drills 題號 {d} 不在題庫')
q_topic_unknown = [q['id'] for q in norm_q if q['topic'] is not None and str(q['topic']) not in topic_ids]
if q_topic_unknown:
    warns.append(f'{len(q_topic_unknown)} 題的 topic 不在 curriculum(例:{q_topic_unknown[:5]})')

# ---------- report ----------
print('=== 驗收結果 ===')
print(f'題數:{len(norm_q)}(屆:{", ".join(sorted(by_exam))});教材:{len(topics)};有效附件:{asset_count}')
for w in warns: print('⚠', w)
for e in errors: print('✗', e)
if errors:
    print(f'\n共 {len(errors)} 項錯誤,未輸出 past_data.js。請先修正或確認。')
    sys.exit(2)

# checksum of source for traceability
h = hashlib.sha256()
with open(os.path.join(SRC, 'question_bank.json'), 'rb') as f: h.update(f.read())
payload = {
    'updated': qb.get('updated'), 'exported': qb.get('exported'), 'sourceSha256': h.hexdigest()[:16],
    'editions': ed_out, 'questions': norm_q, 'curriculum': topics,
}
with open(OUT_JS, 'w', encoding='utf-8') as f:
    f.write('/* 由 tools/build_past.py 產生;來源:國貿大會考題庫與教材參考套件(解析為本站編寫,非官方解析) */\n')
    f.write('window.PAST = ')
    json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
    f.write(';\n')
print(f'✓ 全部通過。已輸出 {os.path.relpath(OUT_JS, ROOT)}({os.path.getsize(OUT_JS)//1024} KB)與 {asset_count} 張附件。')
