"""Check that a guides file lines up with its questions file.

Usage: python3 -I check_guides.py <questions_X.json> <guides_X.json>
Prints one line per problem and ends with "ALL OK" when there are none.
"""
import json
import re
import sys

qpath, gpath = sys.argv[1], sys.argv[2]
questions = {q['id']: q for q in json.load(open(qpath, encoding='utf-8'))['questions']}
guides = json.load(open(gpath, encoding='utf-8'))['guides']


def norm(t):
    return re.sub(r'\s', '', t or '')


def target_range(time_target):
    t = time_target or ''
    if '分半' in t:
        return 75, 90
    m = re.search(r'(\d+)\s*[〜~～]\s*(\d+)\s*分', t)
    if m:
        return int(m.group(1)) * 60, int(m.group(2)) * 60
    m = re.search(r'(\d+)\s*[〜~～]\s*(\d+)\s*秒', t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'(\d+)\s*分', t)
    if m:
        return int(m.group(1)) * 60, int(m.group(1)) * 60
    m = re.search(r'(\d+)\s*秒', t)
    if m:
        return int(m.group(1)), int(m.group(1))
    return 30, 90


problems = []
seen = set()
for g in guides:
    gid = g.get('id')
    if gid in seen:
        problems.append(f'{gid}: duplicate guide')
    seen.add(gid)
    q = questions.get(gid)
    if not q:
        problems.append(f'{gid}: no such question in the questions file')
        continue
    steps = g.get('steps', [])
    if not 3 <= len(steps) <= 5:
        problems.append(f'{gid}: {len(steps)} steps (need 3-5)')
    if not 3 <= len(g.get('thinkFirstEn', [])) <= 4:
        problems.append(f'{gid}: thinkFirstEn needs 3-4 items')
    if not g.get('approachEn'):
        problems.append(f'{gid}: approachEn is empty')
    total = sum(int(s.get('sec', 0) or 0) for s in steps)
    if total != g.get('targetSec'):
        problems.append(f'{gid}: sec values add up to {total}, targetSec is {g.get("targetSec")}')
    lo, hi = target_range(q.get('timeTarget'))
    if not lo - 5 <= (g.get('targetSec') or 0) <= hi + 15:
        problems.append(f'{gid}: targetSec {g.get("targetSec")} does not fit timeTarget {q.get("timeTarget")} ({lo}-{hi}s)')
    for i, s in enumerate(steps, 1):
        for k in ('labelJa', 'labelEn', 'sayEn', 'starterJa', 'exampleJa'):
            if not s.get(k):
                problems.append(f'{gid} step {i}: {k} is empty')
        for k in ('starterJa', 'exampleJa'):
            if re.search(r'【[^】：]*:[^】]*】', s.get(k, '') or ''):
                problems.append(f'{gid} step {i}: half-width colon inside a placeholder in {k}')
        if len(s.get('starterJa', '') or '') > 60:
            problems.append(f'{gid} step {i}: starterJa is longer than 60 characters')
    joined = norm(''.join(s.get('exampleJa', '') or '' for s in steps))
    model = norm(q.get('modelAnswerJa'))
    if joined != model:
        # show the first point of difference to make fixing easy
        n = 0
        while n < min(len(joined), len(model)) and joined[n] == model[n]:
            n += 1
        problems.append(f'{gid}: step examples do not reproduce modelAnswerJa (first difference at character {n}: '
                        f'examples "{joined[n:n + 25]}" vs model "{model[n:n + 25]}")')
for qid in questions:
    if qid not in seen:
        problems.append(f'{qid}: guide is missing')

for p in problems:
    print('PROBLEM', p)
print('ALL OK' if not problems else f'{len(problems)} problem(s)')
