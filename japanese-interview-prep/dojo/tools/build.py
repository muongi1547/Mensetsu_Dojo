"""Merge workflow content files into the page's data folder and validate them.

Usage: python3 -I build.py <content_dir> <site_data_dir>
"""
import json
import os
import re
import sys

content, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
problems = []


def load(name):
    p = os.path.join(content, name)
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def warn(msg):
    problems.append(msg)


EXPECTED = {
    'q01': 1, 'q02': 2, 'q03': 2, 'q04': 2, 'q05': 2, 'q06': 2, 'q07': 2, 'q08': 2,
    'q10': 3, 'q11': 3, 'q12': 3, 'q13': 3, 'q14': 3, 'q40': 3,
    'q20': 4, 'q21': 4, 'q22': 4, 'q23': 4, 'q24': 4, 'q25': 4, 'q26': 4,
    'q30': 1, 'q31': 1, 'q32': 1, 'q33': 6, 'q34': 6, 'q35': 6,
    'q41': 5, 'q42': 5, 'q43': 5, 'q44': 5, 'q45': 5, 'q51': 5, 'q52': 5,
    'q46': 6, 'q47': 6, 'q48': 6, 'q49': 6, 'q50': 6,
    'q60': 7, 'q61': 7, 'q70': 7, 'q71': 7, 'q72': 7, 'q73': 7, 'q74': 7,
}
Q_KEYS = ['id', 'category', 'week', 'questionJa', 'variantsJa', 'questionEn', 'intentEn', 'timeTarget', 'structure',
          'modelAnswerJa', 'modelAnswerEn', 'shortAnswerJa', 'keyPhrases', 'followUps', 'pitfallsEn']
PH_BAD = re.compile(r'【[^】：]*:[^】]*】')  # half-width colon inside a placeholder


def speech_len(t):
    t = re.sub(r'【([^】：:]*)[：:]([^】]*)】', r'\2', t)
    t = re.sub(r'【([^】]*)】', r'\1', t)
    return len(re.sub(r'\s', '', t))


questions = []
vocab = []
for name in ['questions_core.json', 'questions_fpt.json', 'questions_tech.json']:
    try:
        d = load(name)
    except Exception as e:  # noqa: BLE001
        warn(f'{name}: cannot load ({e})')
        continue
    for q in d.get('questions', []):
        questions.append(q)
    if name == 'questions_tech.json':
        vocab = d.get('vocab', [])

seen = {}
for q in questions:
    qid = q.get('id')
    if qid in seen:
        warn(f'duplicate question id {qid}')
    seen[qid] = q
    for k in Q_KEYS:
        if k not in q or q[k] in (None, '', []):
            warn(f'{qid}: missing {k}')
    if qid in EXPECTED and q.get('week') != EXPECTED[qid]:
        warn(f'{qid}: week {q.get("week")} != {EXPECTED[qid]}; fixing')
        q['week'] = EXPECTED[qid]
    for field in ('modelAnswerJa', 'shortAnswerJa'):
        if PH_BAD.search(q.get(field, '') or ''):
            warn(f'{qid}: half-width colon in a placeholder in {field}')
missing = sorted(set(EXPECTED) - set(seen))
extra = sorted(set(seen) - set(EXPECTED))
if missing:
    warn('missing questions: ' + ', '.join(missing))
if extra:
    warn('unexpected questions: ' + ', '.join(extra))
questions.sort(key=lambda q: q.get('id', ''))

lengths = [(q['id'], speech_len(q.get('modelAnswerJa', '')), speech_len(q.get('shortAnswerJa', ''))) for q in questions]

plan = None
try:
    plan = load('plan.json')
    weeks = plan.get('weeks', [])
    if len(weeks) != 8:
        warn(f'plan: {len(weeks)} weeks')
    ids = set()
    for w in weeks:
        for t in w.get('tasks', []):
            if t.get('id') in ids:
                warn(f'plan: duplicate task id {t.get("id")}')
            ids.add(t.get('id'))
            if t.get('day') not in ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Daily'):
                warn(f'plan: bad day {t.get("day")} in {t.get("id")}')
            if t.get('type') not in ('speak', 'write', 'listen', 'vocab', 'research', 'mock', 'feedback', 'review'):
                warn(f'plan: bad type {t.get("type")} in {t.get("id")}')
        for qid in w.get('focusQuestions', []) + w.get('reviewQuestions', []):
            if qid not in EXPECTED:
                warn(f'plan: week {w.get("week")} references unknown {qid}')
    for r in plan.get('resources', []):
        if not str(r.get('url', '')).startswith('https://'):
            warn(f'plan: resource without https url: {r.get("name")}')
    for k in ('weekday', 'weekend', 'light'):
        total = sum(int(b.get('min', 0) or 0) for b in plan.get('dailyRoutine', {}).get(k, []))
        print(f'routine {k}: {total} min')
except Exception as e:  # noqa: BLE001
    warn(f'plan.json: {e}')

language = None
try:
    language = load('language.json')
    print('language:', {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in language.items()})
except Exception as e:  # noqa: BLE001
    warn(f'language.json: {e}')

fpt = None
try:
    fpt = load('fpt.json')
    nfacts = sum(len(s.get('facts', [])) for s in fpt.get('sections', []))
    print('fpt: sections', len(fpt.get('sections', [])), 'facts', nfacts, 'reverseQuestions', len(fpt.get('reverseQuestions', [])))
    for s in fpt.get('sections', []):
        for f in s.get('facts', []):
            if not str(f.get('source', '')).startswith('https://'):
                warn(f'fpt: fact without https source in {s.get("id")}: {str(f.get("text"))[:60]}')
except Exception as e:  # noqa: BLE001
    warn(f'fpt.json: {e}')


def write_lines(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('[\n' + ',\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n]\n')


def write_obj(path, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


# ---- what-to-say guides -------------------------------------------------
def norm(t):
    return re.sub(r'\s', '', t or '')


guides = []
for name in ['guides_core.json', 'guides_fpt.json', 'guides_tech.json']:
    try:
        guides.extend(load(name).get('guides', []))
    except Exception as e:  # noqa: BLE001
        warn(f'{name}: cannot load ({e})')
gseen = {}
aligned = 0
for g in guides:
    gid = g.get('id')
    if gid in gseen:
        warn(f'duplicate guide {gid}')
    gseen[gid] = g
    steps = g.get('steps', [])
    if not 3 <= len(steps) <= 5:
        warn(f'guide {gid}: {len(steps)} steps')
    total = sum(int(s.get('sec', 0) or 0) for s in steps)
    if g.get('targetSec') and total != g.get('targetSec'):
        warn(f'guide {gid}: sec sum {total} != targetSec {g.get("targetSec")}; using the sum')
        g['targetSec'] = total
    for s in steps:
        for k in ('labelJa', 'labelEn', 'sayEn', 'starterJa'):
            if not s.get(k):
                warn(f'guide {gid}: step missing {k}')
        if PH_BAD.search(s.get('starterJa', '') or ''):
            warn(f'guide {gid}: half-width colon in a starter placeholder')
    if gid in seen and any(s.get('exampleJa') for s in steps):
        joined = norm(''.join(s.get('exampleJa', '') for s in steps))
        if joined == norm(seen[gid].get('modelAnswerJa', '')):
            aligned += 1
        else:
            warn(f'guide {gid}: step examples do not add up to the model answer; examples removed')
            for s in steps:
                s.pop('exampleJa', None)
gmissing = sorted(set(EXPECTED) - set(gseen))
if gmissing:
    warn('questions without a guide: ' + ', '.join(gmissing))
guides.sort(key=lambda g: g.get('id', ''))
write_lines(os.path.join(out, 'guides.json'), guides)
print('guides:', len(guides), 'with step examples aligned to the model answer:', aligned)

write_lines(os.path.join(out, 'questions.json'), questions)
write_lines(os.path.join(out, 'vocab.json'), vocab)
if plan is not None:
    write_obj(os.path.join(out, 'plan.json'), plan)
if language is not None:
    write_obj(os.path.join(out, 'language.json'), language)
if fpt is not None:
    write_obj(os.path.join(out, 'fpt.json'), fpt)

print('questions:', len(questions), 'vocab:', len(vocab))
print('model answer chars (min/max):', min((x[1] for x in lengths), default=0), max((x[1] for x in lengths), default=0))
long_ones = [f'{i}:{m}' for i, m, s in lengths if m > 360]
short_long = [f'{i}:{s}' for i, m, s in lengths if s > 170]
if long_ones:
    print('long model answers:', ', '.join(long_ones))
if short_long:
    print('long short-answers:', ', '.join(short_long))
for name in sorted(os.listdir(out)):
    print(f'{name}: {os.path.getsize(os.path.join(out, name)):,} bytes')
print('PROBLEMS:' if problems else 'No problems found.')
for p in problems:
    print(' -', p)
