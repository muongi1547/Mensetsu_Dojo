"""Wrap the page in the publish skeleton for local preview (plain and with mocked Claude features).

Usage: python3 -I mkpreview.py <dojo_dir>
"""
import os
import sys

d = sys.argv[1]
head = ('<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
body = open(os.path.join(d, 'site', 'index.html'), encoding='utf-8').read()
mock = open(os.path.join(d, 'tools', 'mockcaps.js'), encoding='utf-8').read()
os.makedirs(os.path.join(d, 'preview'), exist_ok=True)
open(os.path.join(d, 'preview', '_preview.html'), 'w', encoding='utf-8').write(head + body + '</body></html>')
open(os.path.join(d, 'preview', '_mock.html'), 'w', encoding='utf-8').write(head + '<script>' + mock + '</script>' + body + '</body></html>')
# the preview pages load data/ relative to themselves
link = os.path.join(d, 'preview', 'data')
if not os.path.exists(link):
    os.symlink(os.path.join('..', 'site', 'data'), link)
print('preview pages rebuilt')
