"""Make a standalone copy of the page that any static host can serve (GitHub Pages, python -m http.server, ...).

On claude.ai the page is wrapped in an HTML skeleton at publish time. Elsewhere it needs the skeleton in the
file itself: without <meta charset> the Japanese text can be decoded wrongly, and without a doctype the page
renders in quirks mode.

Usage: python3 -I export.py <dojo_dir> <out_dir>
Writes <out_dir>/index.html, <out_dir>/data/*.json and <out_dir>/.nojekyll. Other files in <out_dir> are left alone.
"""
import os
import shutil
import sys

d, out = sys.argv[1], sys.argv[2]
src = open(os.path.join(d, 'site', 'index.html'), encoding='utf-8').read()
cut = src.find('<header class="topbar">')
if cut < 0:
    sys.exit('could not find where the page body starts')
head, body = src[:cut].strip(), src[cut:].strip()

base = ('<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>\n')
page = '<!doctype html>\n<html lang="en">\n<head>\n' + base + head + '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n'

src_data = os.path.join(d, 'site', 'data')
out_data = os.path.join(out, 'data')
os.makedirs(out_data, exist_ok=True)
with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(page)
names = sorted(n for n in os.listdir(src_data) if n.endswith('.json'))
for n in names:
    shutil.copyfile(os.path.join(src_data, n), os.path.join(out_data, n))
for n in os.listdir(out_data):  # drop data files that no longer exist in the source
    if n.endswith('.json') and n not in names:
        os.remove(os.path.join(out_data, n))
open(os.path.join(out, '.nojekyll'), 'w').close()
print('index.html: %d bytes; data: %s' % (len(page.encode('utf-8')), ', '.join(names)))
