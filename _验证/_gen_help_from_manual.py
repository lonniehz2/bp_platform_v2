# -*- coding: utf-8 -*-
"""从用户说明书 docx 生成在线帮助 help.js（章节/公式/表格/FAQ）。"""
import io
import json
import os

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOCX = os.path.join(BASE, '租赁性保障用房管理平台_用户使用说明书_V1.0.docx')
OUT = os.path.join(BASE, 'frontend', 'src', 'content', 'help.js')

doc = Document(DOCX)


def cell_fill(cell):
    tcPr = cell._tc.tcPr
    if tcPr is None:
        return ''
    shd = tcPr.find(qn('w:shd'))
    return '' if shd is None else (shd.get(qn('w:fill')) or '')


def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)


sections = []
current = None
list_buf = []
list_type = None
skip_h1 = {'文档说明', '目录'}


def flush_list():
    global list_buf, list_type
    if list_buf:
        current['blocks'].append({'type': list_type, 'items': list_buf})
        list_buf = []
    list_type = None


for block in iter_block_items(doc):
    if isinstance(block, Paragraph):
        text = block.text.strip()
        style = block.style.name if block.style else ''
        if style == 'Heading 1':
            flush_list()
            if text in skip_h1:
                current = None
                continue
            import re as _re
            m = _re.match(r'(\d+)\u3000', text)
            sid = 'start' if text == '常见场景速查' else ('ch' + (m.group(1) if m else str(len(sections) + 1)))
            current = {'id': sid, 'title': text, 'blocks': []}
            sections.append(current)
            continue
        if current is None:
            continue
        if not text:
            continue
        if style in ('Heading 2', 'Heading 3'):
            flush_list()
            current['blocks'].append({'type': 'h3', 'text': text})
        elif style == 'List Bullet':
            if list_type not in (None, 'ul'):
                flush_list()
            list_type = 'ul'
            list_buf.append(text)
        elif style == 'List Number':
            if list_type not in (None, 'ol'):
                flush_list()
            list_type = 'ol'
            list_buf.append(text)
        else:
            flush_list()
            current['blocks'].append({'type': 'p', 'text': text})
    else:
        if current is None:
            continue
        flush_list()
        rows = block.rows
        cols = len(block.columns)
        if cols == 1 and len(rows) == 1:
            cell = rows[0].cells[0]
            txt = '\n'.join(p.text for p in cell.paragraphs if p.text.strip())
            fill = cell_fill(cell).upper()
            if not txt:
                continue
            if fill == 'F2F5F9' or ('=' in txt and '\n' in txt):
                current['blocks'].append({'type': 'code', 'text': txt})
            elif fill == 'FFF7E6':
                current['blocks'].append({'type': 'note', 'text': txt})
            else:
                current['blocks'].append({'type': 'p', 'text': txt})
            continue
        if len(rows) < 2:
            continue
        head = [c.text.strip() for c in rows[0].cells]
        body = []
        for r in rows[1:]:
            body.append([c.text.strip() for c in r.cells])
        # 跳过封面/文档信息表（一般不在章节内）
        current['blocks'].append({'type': 'table', 'head': head, 'rows': body})

flush_list()

# 章节内 FAQ：Q 标题 + 下一段答案 → faq 块
for sec in sections:
    if not sec['title'].startswith('11'):
        continue
    blocks = sec['blocks']
    out = []
    i = 0
    faqs = []
    while i < len(blocks):
        b = blocks[i]
        if b['type'] == 'h3' and b['text'].startswith('Q'):
            q = b['text']
            a = ''
            if i + 1 < len(blocks) and blocks[i + 1]['type'] == 'p':
                a = blocks[i + 1]['text']
                i += 1
            faqs.append({'q': q, 'a': a})
        else:
            if faqs:
                out.append({'type': 'faq', 'items': faqs})
                faqs = []
            out.append(b)
        i += 1
    if faqs:
        out.append({'type': 'faq', 'items': faqs})
    sec['blocks'] = out

route = '''const ROUTE_SECTION = {
  '/help': 'start', '/dashboard': 'ch1', '/todos': 'ch1', '/messages': 'ch1',
  '/persons': 'ch4', '/annual-reviews': 'ch4',
  '/applications': 'ch4', '/waitlist': 'ch4', '/allocations': 'ch4', '/publicities': 'ch4',
  '/contracts': 'ch5', '/contract-changes': 'ch5', '/exchanges': 'ch5',
  '/terminations': 'ch5',
  '/fee-items': 'ch6', '/bills': 'ch7', '/arrears': 'ch7', '/deposits': 'ch7',
  '/subsidies': 'ch7', '/cashflow': 'ch7',
  '/meter-readings': 'ch8', '/energy': 'ch8', '/energy-allocation': 'ch8',
  '/houses': 'ch3', '/spaces': 'ch3', '/house-calendar': 'ch5', '/short-rent': 'ch5',
  '/devices': 'ch9', '/device-bind': 'ch9', '/dev-events': 'ch9', '/access': 'ch9',
  '/keyring': 'ch9', '/grants': 'ch9',
  '/workorders': 'ch9', '/alerts': 'ch9', '/complaints': 'ch9', '/appeals': 'ch9',
  '/credits': 'ch9', '/visits': 'ch9',
  '/orgs': 'ch3', '/rbac': 'ch2', '/sys': 'ch3', '/open': 'ch9', '/gov': 'ch9',
  '/ops-center': 'ch9', '/ops-extras': 'ch9',
  '/platform-admin': 'ch10', '/platform-admin/login': 'ch10',
  '/platform-info': 'ch10',
  '/reports': 'ch9'
}

export function sectionForRoute(path) {
  if (!path) return 'start'
  if (ROUTE_SECTION[path]) return ROUTE_SECTION[path]
  const hit = Object.keys(ROUTE_SECTION)
    .filter((k) => k !== '/help' && path.startsWith(k))
    .sort((a, b) => b.length - a.length)[0]
  return hit ? ROUTE_SECTION[hit] : 'start'
}
'''

js = 'export const HELP_VERSION = \'v1.0（2026-10-31）\'\n'
js += 'export const HELP_PDF = \'/docs/user-manual.pdf\'\n\n'
js += 'export const HELP_SECTIONS = ' + json.dumps(sections, ensure_ascii=False, indent=2) + '\n\n'
js += route
io.open(OUT, 'w', encoding='utf-8', newline='').write(js)
print('help.js written:', len(js), 'sections', len(sections), '->', OUT)
