"""Rebuild working files from the session records (Write/Edit tool calls), in time order.

Usage: python3 -I recover.py <project_dir> <session_id> <dojo_dir>
"""
import glob
import io
import json
import os
import re
import sys
import contextlib

proj, sid, dojo = sys.argv[1], sys.argv[2], sys.argv[3]
SCRATCH_MARK = '/scratchpad/'


def events_from(path, label):
    """Yield (ts, order, label, tool, input, tool_use_id) and collect results."""
    out, results, seen = [], {}, set()
    last_ts = ''
    for n, line in enumerate(open(path, encoding='utf-8')):
        try:
            x = json.loads(line)
        except Exception:
            continue
        ts = x.get('timestamp') or last_ts
        last_ts = ts
        content = (x.get('message') or {}).get('content')
        if not isinstance(content, list):
            continue
        for k, b in enumerate(content):
            if not isinstance(b, dict):
                continue
            if b.get('type') == 'tool_use':
                tid = b.get('id')
                if tid in seen:
                    continue
                seen.add(tid)
                out.append((ts, n, k, label, b.get('name'), b.get('input') or {}, tid))
            elif b.get('type') == 'tool_result':
                c = b.get('content')
                txt = c if isinstance(c, str) else ' '.join(t.get('text', '') for t in (c or []) if isinstance(t, dict))
                results[b.get('tool_use_id')] = (bool(b.get('is_error')), txt)
    return out, results


all_events, all_results = [], {}
# sub-agents of the workflows
for wf in sorted(glob.glob(os.path.join(proj, sid, 'subagents', 'workflows', '*'))):
    labels = {}
    jp = os.path.join(wf, 'journal.jsonl')
    if os.path.exists(jp):
        for line in open(jp, encoding='utf-8'):
            try:
                x = json.loads(line)
            except Exception:
                continue
            if x.get('type') == 'started':
                labels[x.get('agentId')] = x.get('label')
    for f in sorted(glob.glob(os.path.join(wf, 'agent-*.jsonl'))):
        aid = os.path.basename(f)[len('agent-'):-len('.jsonl')]
        ev, res = events_from(f, labels.get(aid, aid))
        all_events += ev
        all_results.update(res)
# main session
ev, res = events_from(os.path.join(proj, sid + '.jsonl'), 'main')
all_events += ev
all_results.update(res)
all_events.sort(key=lambda e: (e[0], e[3], e[1], e[2]))


def rel(path):
    i = path.find(SCRATCH_MARK)
    return path[i + len(SCRATCH_MARK):] if i >= 0 else None


WANT = re.compile(r'^(content/[^/]+\.json|site/index\.html|build\.py|check_guides\.py|mockcaps\.js|mkpreview\.py)$')
state, log = {}, []


def run_patch(body, target):
    tmp = os.path.join(dojo, 'tools', '_patch_target.tmp')
    open(tmp, 'w', encoding='utf-8').write(state[target])
    argv = sys.argv
    sys.argv = ['-', tmp]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(body, 'patch', 'exec'), {'__name__': '__patch__'})
    finally:
        sys.argv = argv
    state[target] = open(tmp, encoding='utf-8').read()
    os.remove(tmp)
    return buf.getvalue().strip()


for ts, n, k, label, tool, inp, tid in all_events:
    err, txt = all_results.get(tid, (None, ''))
    if tool in ('Write', 'Edit'):
        r = rel(inp.get('file_path', ''))
        if not r or not WANT.match(r):
            continue
        if err is None:
            log.append(f'{ts} {label} {tool} {r}: no result recorded, skipped')
            continue
        if err:
            log.append(f'{ts} {label} {tool} {r}: original call failed, skipped')
            continue
        if tool == 'Write':
            state[r] = inp.get('content', '')
        else:
            old, new = inp.get('old_string', ''), inp.get('new_string', '')
            cur = state.get(r)
            if cur is None:
                log.append(f'{ts} {label} Edit {r}: no base content!')
                continue
            cnt = cur.count(old)
            if inp.get('replace_all'):
                state[r] = cur.replace(old, new)
            elif cnt == 1:
                state[r] = cur.replace(old, new, 1)
            else:
                log.append(f'{ts} {label} Edit {r}: old_string found {cnt} times (expected 1); ' + ('applied to first' if cnt else 'NOT APPLIED'))
                if cnt:
                    state[r] = cur.replace(old, new, 1)
    elif tool == 'Bash' and label == 'main':
        cmd = inp.get('command', '')
        # files created with: cat > "$SP/name" <<'EOF'
        for m in re.finditer(r'cat > "\$SP/([\w./]+)" <<\'EOF\'\n(.*?)\nEOF(?:\n|$)', cmd, re.S):
            if WANT.match(m.group(1)) and not err:
                state[m.group(1)] = m.group(2) + '\n'
        # in-place python patches: python3 -I - "$SP/name" <<'EOF'
        for m in re.finditer(r'python3 -I - "\$SP/([\w./]+)" <<\'EOF\'\n(.*?)\nEOF(?:\n|$)', cmd, re.S):
            target = m.group(1)
            if WANT.match(target) and target in state and not err:
                try:
                    out = run_patch(m.group(2), target)
                    log.append(f'{ts} main patch {target}: {out}')
                except Exception as e:  # noqa: BLE001
                    log.append(f'{ts} main patch {target}: FAILED {e!r}')

for r, text in sorted(state.items()):
    dst = os.path.join(dojo, r if r.startswith(('content/', 'site/')) else os.path.join('tools', r))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w', encoding='utf-8').write(text)
    ok = ''
    if r.endswith('.json'):
        try:
            json.loads(text)
            ok = 'valid JSON'
        except Exception as e:  # noqa: BLE001
            ok = f'INVALID JSON: {e}'
    print(f'{r}: {len(text.encode("utf-8")):,} bytes {ok}')
print('--- notes')
for line in log:
    print(line)

# research reports from the first workflow's journal
jp = os.path.join(proj, sid, 'subagents', 'workflows', 'wf_37df9d55-5bb', 'journal.jsonl')
labels = {}
for line in open(jp, encoding='utf-8'):
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get('type') == 'started':
        labels[d['key']] = d.get('label', '?')
    if d.get('type') == 'result' and labels.get(d['key'], '').startswith('research') and isinstance(d.get('result'), str):
        name = labels[d['key']].replace(':', '_') + '.md'
        open(os.path.join(dojo, 'research', name), 'w', encoding='utf-8').write(d['result'])
        print('research/' + name, len(d['result']))
