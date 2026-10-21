# -*- coding: utf-8 -*-
"""列表页筛选统一：给「有查询但没清空」的页面补上「清空」按钮

做法：
  1. 用**括号配平**切出每个 <div class="toolbar">…</div>（非贪婪正则会被嵌套 div 骗到）
  2. 只处理「恰好一个 toolbar」且其中已有「查询」按钮的页面；多 tab 页面单独手改
  3. 在「查询」按钮后插入「清空」@click="resetQuery"
  4. 自动生成 resetQuery：
     · v-model="obj.field" → setup 时快照 + Object.assign 还原
     · v-model="name"      → name.value = ''
  5. 幂等：已有「清空/重置」或 resetQuery 的页面跳过

用法：
  python _codemod_filter_reset.py --dry
  python _codemod_filter_reset.py
"""
import io
import os
import re
import sys

DRY = '--dry' in sys.argv
VIEWS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')

QUERY_TEXT = re.compile(r'<el-button\b[^>]*>\s*查询\s*</el-button>', re.S)
RESET_TEXT = re.compile(r'<el-button\b[^>]*>\s*(清空|重置)\s*</el-button>')
CLICK = re.compile(r'@click="([A-Za-z_$][\w$]*)"')
REACTIVE = re.compile(r'const ([A-Za-z_$][\w$]*)\s*=\s*reactive\(')
REF = re.compile(r'const ([A-Za-z_$][\w$]*)\s*=\s*ref\(')
ON_MOUNTED = re.compile(r'\nonMounted\(')


def find_blocks(src, cls):
    """返回所有 <div class="cls">…</div> 的 (start, end) —— 括号配平。

    注意：`<div class="spacer" />` 这类**自闭合** div 不能计入深度，
    否则 block 会一路吃到文件末尾（会把弹窗、表格里的 v-model 也当成筛选条件）。
    """
    out = []
    for m in re.finditer(r'<div class="%s"' % re.escape(cls), src):
        i = m.start()
        depth = 0
        j = i
        while j < len(src):
            if src.startswith('<div', j):
                close = src.find('>', j)
                if close == -1:
                    break
                if src[close - 1] == '/':      # 自闭合，不增加深度
                    j = close + 1
                    continue
                depth += 1
                j = close + 1
                continue
            if src.startswith('</div>', j):
                depth -= 1
                j += 6
                if depth == 0:
                    out.append((i, j))
                    break
                continue
            j += 1
    return out


def gen_reset(toolbar_html, script, handler):
    models = re.findall(r'v-model(?:\.\w+)?="([^"]+)"', toolbar_html)
    models = [m for m in models if re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)?', m)]
    if not models:
        return None, 'toolbar 里没有可识别的 v-model'

    objs = sorted({m.split('.')[0] for m in models if '.' in m})
    plain = sorted({m for m in models if '.' not in m})

    for o in objs:
        if not REACTIVE.search(script):
            break
        names = REACTIVE.findall(script)
        if o not in names:
            return None, 'reactive 定义缺失：%s' % o
        return ('const {o}0 = JSON.parse(JSON.stringify({o}))\n'
                'function resetQuery() {{\n'
                '  Object.assign({o}, {o}0)\n'
                '  {h}()\n'
                '}}').format(o=o, h=handler), 'reactive 快照：%s' % o

    if plain:
        defined = set(REF.findall(script))
        bad = [p for p in plain if p not in defined]
        if bad:
            return None, 'ref 定义缺失：%s' % ','.join(bad)
        lines = ["  %s.value = ''" % p for p in plain]
        # 翻页状态一并回到第一页（若该页用独立 ref 管分页）
        if 'pageNum' in REF.findall(script) and 'pageNum' not in plain:
            lines.append('  pageNum.value = 1')
        body = '\n'.join(lines)
        return ('function resetQuery() {\n%s\n  %s()\n}' % (body, handler),
                'ref 置空：%s' % ','.join(plain))

    return None, '无法推断重置方式'


def main():
    changed, skipped = [], []
    for fn in sorted(os.listdir(VIEWS)):
        if not fn.endswith('.vue'):
            continue
        path = os.path.join(VIEWS, fn)
        src = io.open(path, encoding='utf-8').read()

        blocks = find_blocks(src, 'toolbar')
        if len(blocks) != 1:
            if blocks:
                skipped.append((fn, '多 toolbar（%d 个），多 tab 页面需手改' % len(blocks)))
            continue
        s, e = blocks[0]
        toolbar_html = src[s:e]
        if not QUERY_TEXT.search(toolbar_html):
            continue
        if RESET_TEXT.search(toolbar_html):
            skipped.append((fn, '已有清空/重置'))
            continue
        if 'resetQuery' in src:
            skipped.append((fn, '已存在 resetQuery'))
            continue

        script = src[e:]
        # 复用「查询」按钮自己的 handler，避免假设页面一定有 reload()
        qbtn = QUERY_TEXT.search(toolbar_html)
        hm = CLICK.search(qbtn.group(0))
        if not hm:
            skipped.append((fn, '查询按钮没有 @click，无法推断加载函数'))
            continue
        handler = hm.group(1)
        reset_impl, how = gen_reset(toolbar_html, script, handler)
        if not reset_impl:
            skipped.append((fn, how))
            continue

        # 插入「清空」：紧跟「查询」按钮
        q = qbtn
        line_start = toolbar_html.rfind('\n', 0, q.start()) + 1
        pad = re.match(r'[ \t]*', toolbar_html[line_start:]).group(0)
        ins = '\n' + pad + '<el-button @click="resetQuery">清空</el-button>'
        new_toolbar = toolbar_html[:q.end()] + ins + toolbar_html[q.end():]

        src2 = src[:s] + new_toolbar + src[e:]

        m = ON_MOUNTED.search(src2)
        if not m:
            skipped.append((fn, '未找到 onMounted，无法定位插入点'))
            continue
        src2 = src2[:m.start()] + '\n' + reset_impl + '\n' + src2[m.start():]

        if not DRY:
            io.open(path, 'w', encoding='utf-8', newline='').write(src2)
        changed.append((fn, how))

    print('%s：%d 个页面' % ('将修改' if DRY else '已修改', len(changed)))
    for fn, how in changed:
        print('  ✔ %-24s %s' % (fn, how))
    if skipped:
        print('\n跳过 %d 个：' % len(skipped))
        for fn, why in skipped:
            print('  - %-24s %s' % (fn, why))
    return 0


if __name__ == '__main__':
    sys.exit(main())
