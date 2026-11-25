(() => {
  const log = window.__log = [];
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const store = {
    'data/users/u_test/state': {v: 1, startDate: '2026-12-07', tasks: {w1t05: 1}, ratings: {q02: 4}, reflections: {}, bench: {}, checks: {}, last: {}, settings: {engine: 'auto', voice: '', rate: 1.0, hideModel: false, mockFast: true, mockVoice: true}},
    'data/users/u_test/a_q02': {text: '私の強みは粘り強さです。', at: 1},
  };
  const subs = [];
  const snap = prefix => {
    const docs = Object.keys(store).filter(p => p.startsWith(prefix + '/') && !p.slice(prefix.length + 1).includes('/'))
      .map(p => ({id: p.slice(prefix.length + 1), exists: true, data: () => JSON.parse(JSON.stringify(store[p])), metadata: {fromCache: false, hasPendingWrites: false}}));
    return {docs, size: docs.length, empty: !docs.length, metadata: {fromCache: false, hasPendingWrites: false}, docChanges: () => []};
  };
  const notify = prefix => subs.filter(s => s.prefix === prefix).forEach(s => setTimeout(() => s.next(snap(prefix)), 10));
  const db = {
    collection(path) {
      return {
        path,
        doc(id) { const p = path + '/' + id; return {id, path: p,
          async set(d) { await wait(40); store[p] = JSON.parse(JSON.stringify(d)); log.push('set ' + id); notify(path); },
          async delete() { await wait(20); delete store[p]; log.push('del ' + id); notify(path); },
          async get() { return {id, exists: p in store, data: () => store[p], metadata: {fromCache: false, hasPendingWrites: false}}; }}; },
        onSnapshot(next, err) { const s = {prefix: path, next}; subs.push(s); setTimeout(() => next(snap(path)), 120); return () => { subs.splice(subs.indexOf(s), 1); }; },
      };
    },
  };
  window.__store = store;
  const user = {async id() { return 'u_test'; }, async isOwner() { return true; }, async canEdit() { return true; }, async can() { return true; }, async me() { return {id: 'u_test'}; }};
  let lineH = null;
  const tts = {
    async speak(lines, opts) { log.push('tts ' + lines.length + ' ' + (opts && opts.language) + ' ' + (opts && opts.rate)); for (const l of lines) { if (lineH) lineH({line: 0, id: l.id}); await wait(15); } return {playedMs: 100}; },
    async stop() { log.push('tts stop'); }, active() { return false; }, async languages() { return ['en', 'ja']; },
    onLine(h) { lineH = h; return () => {}; }, onState() { return () => {}; }, async setRate() {},
  };
  let onP, onF, onS, active = false;
  const dictation = {
    start(o) { log.push('dict start ' + (o && o.language)); active = true; if (onS) onS({state: 'starting'});
      return new Promise(res => setTimeout(() => { if (onS) onS({state: 'listening'}); res();
        setTimeout(() => onP && onP({text: 'えーと、私は'}), 80);
        setTimeout(() => { onF && onF({text: 'えーと、私は〇〇と申します。'}); onP && onP({text: ''}); }, 200);
        setTimeout(() => onF && onF({text: ' 夜間の歩行者検出を研究しています。'}), 350); }, 80)); },
    async stop() { if (!active) return; active = false; if (onS) onS({state: 'finishing'}); await wait(80); if (onF) onF({text: ' よろしくお願いいたします。'}); if (onS) onS({state: 'idle', reason: 'stopped'}); },
    active() { return active; }, onPartial(h) { onP = h; return () => {}; }, onFinal(h) { onF = h; return () => {}; }, onState(h) { onS = h; return () => {}; },
  };
  const sample = async (input, opts) => {
    opts = opts || {};
    log.push('sample turns:' + (Array.isArray(input) ? input.length : 'str') + ' tier:' + opts.modelTier + ' cache:' + opts.cache + ' last:' + (Array.isArray(input) ? input[input.length - 1].role : ''));
    const n = Array.isArray(input) ? input.length : 0;
    const text = n >= 5 ? 'ありがとうございました。本日の面接は以上です。[END]' : (n === 1 ? '本日はお越しいただきありがとうございます。それでは、自己紹介をお願いします。' : 'ありがとうございます。では、その研究で一番苦労したことは何ですか。');
    await wait(120);
    if (opts.onText) opts.onText({text: text.slice(0, 10), delta: text.slice(0, 10)});
    await wait(80);
    if (opts.onText) opts.onText({text, delta: text.slice(10)});
    return {text, truncated: false, modelTierApplied: opts.modelTier || 'default'};
  };
  sample.json = async (prompt, opts) => {
    log.push('json ' + (prompt.includes('TRANSCRIPT') ? 'report' : 'check') + ' tier:' + (opts && opts.modelTier));
    await wait(150);
    if (prompt.includes('Do NOT write the answer')) { log.push('json hint'); return {targetSec: 45, steps: [{labelJa: '結論', labelEn: 'Conclusion', sayEn: 'Say your name and university.', starterJa: '〜大学大学院の〜と申します。'}, {labelJa: '研究', labelEn: 'Research', sayEn: 'One sentence on your research.', starterJa: '現在、〜を研究しております。'}, {labelJa: '締め', labelEn: 'Close', sayEn: 'Close politely.', starterJa: '本日はよろしくお願いいたします。'}], tipEn: 'Do not run over one minute.'}; }
    if (prompt.includes('TRANSCRIPT')) return {overall: 3, scores: {content: 3, structure: 4, japanese: 3, keigo: 2, fluency: 3, motivation: 4}, summary: 'Good start.', strengths: ['Clear'], topFixes: ['Keigo'], answers: [{question: '自己紹介をお願いします。', answer: '私は〇〇です', better: '〇〇と申します。よろしくお願いいたします。', notes: 'Use と申します.'}], phrases: [{ja: '恐れ入りますが', en: 'Excuse me, but'}]};
    return {overall: 3, scores: {content: 3, structure: 3, japanese: 2, keigo: 3}, summary: 'Clear but stiff.', corrected: '〇〇と申します。本日はよろしくお願いいたします。', fixes: [{original: 'よろしくお願いします', better: 'よろしくお願いいたします', why: 'More polite.'}], contentTips: ['Add your research.'], followUp: 'なぜ日本で働きたいのですか。'};
  };
  sample.limits = async () => ({maxPromptBytes: 262144});
  const downloads = {async save(r) { log.push('save ' + r.filename + ' ' + r.data.length); return {status: 'saved'}; }};
  const caps = {db, user, tts, dictation, sample, downloads};
  window.claude = {use: name => new Promise(r => setTimeout(() => r(caps[name] || null), 40))};
})();
