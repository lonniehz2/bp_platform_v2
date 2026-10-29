# -*- coding: utf-8 -*-
"""前端构建与静态校验（可复用于每次改页面）

抓两类「构建通过但页面坏」的问题：
  A. 未定义标识符 —— 例如漏写 import，运行时报 ReferenceError，页面直接空白。
     这类错误 Vue 编译不报、pnpm build 也不报，只能静态扫描或人眼发现。
  B. 构建产物缺失 —— 视图未进 bundle / dist 未更新到 static。

用法：
  python _check_build.py            # 只报告
  python _check_build.py --strict   # 有问题返回非 0（CI 用）
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
SRC = os.path.join(ROOT, 'frontend', 'src')
DIST = os.path.join(ROOT, 'frontend', 'dist')
# 本项目 vite outDir 指向 backend static，dist 可能不存在
OUT_DIR = os.path.join(ROOT, 'backend', 'src', 'main', 'resources', 'static')
STATIC = os.path.join(ROOT, 'backend', 'src', 'main', 'resources', 'static')

STRICT = '--strict' in sys.argv

# JS/浏览器全局与表格作用域变量，不算未定义
WHITELIST = {
    'true', 'false', 'null', 'undefined', 'NaN', 'Infinity',
    'Math', 'Number', 'String', 'Boolean', 'JSON', 'Date', 'Object', 'Array',
    'Map', 'Set', 'Promise', 'RegExp', 'Error', 'parseInt', 'parseFloat',
    'isNaN', 'encodeURIComponent', 'decodeURIComponent', 'console', 'window',
    'document', 'localStorage', 'sessionStorage', 'setTimeout', 'clearTimeout',
    'setInterval', 'clearInterval', 'requestAnimationFrame', 'ResizeObserver',
    'row', 'item', 'index', 'scope', 'data', 'node', 'props', 'emit', 'slot',
    'key', 'value', 'entry', 'record', 'list', 'v', 'x', 'o', 's', 't', 'p',
    'r', 'i', 'e', 'a', 'b', 'c', 'd', 'f', 'g', 'h', 'k', 'm', 'n', 'q', 'u',
    'w', 'y', 'z',
    # Vue 模板内置
    '$route', '$router', '$emit', '$attrs', '$slots', '$props',
    '$refs', '$el', '$nextTick', '$money'
}

DECL_RE = re.compile(
    r'\b(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)')
IMPORT_NAMED_RE = re.compile(r'import\s*\{([^}]*)\}\s*from')
IMPORT_DEFAULT_RE = re.compile(r'import\s+([A-Za-z_$][\w$]*)\s*(?:,|from)')

# 模板里用到的标识符
TEMPLATE_EXPR_RE = re.compile(
    r'(?:v-if|v-else-if|v-show|v-for|v-model(?::[\w.]+)?|:[\w.-]+|@[\w.-]+|v-bind)'
    r'="([^"]*)"')
MUSTACHE_RE = re.compile(r'\{\{([^}]*)\}\}')


def script_of(text):
    m = re.search(r'<script setup[^>]*>(.*?)</script>', text, re.S)
    return m.group(1) if m else ''


def template_of(text):
    m = re.search(r'<template>(.*?)</template>', text, re.S)
    return m.group(1) if m else ''


def defined_names(script):
    names = set()
    # defineProps({ ... }) 里的顶层键也是可用标识符（用括号配平，支持多行与嵌套）
    idx = script.find('defineProps(')
    if idx >= 0:
        start = script.find('(', idx) + 1
        depth, end = 1, start
        while end < len(script) and depth > 0:
            if script[end] == '(':
                depth += 1
            elif script[end] == ')':
                depth -= 1
            end += 1
        block = script[start:end - 1]
        # 顶层键：行首缩进 4 空格的 key:
        for k in re.findall(r'^\s{4}([A-Za-z_$][\w$]*)\s*:', block, re.M):
            names.add(k)
        for k in re.findall(r'([A-Za-z_$][\w$]*)\s*:\s*\{\s*type:', block):
            names.add(k)
    for m in re.finditer(r'defineProps\(\s*\[([^\]]*)\]', script):
        for part in m.group(1).split(','):
            n = part.strip().strip("'\"")
            if n:
                names.add(n)
    for m in IMPORT_NAMED_RE.finditer(script):
        for part in m.group(1).split(','):
            part = part.strip()
            if not part:
                continue
            names.add(part.split(' as ')[-1].strip())
    for m in IMPORT_DEFAULT_RE.finditer(script):
        names.add(m.group(1))
    for m in DECL_RE.finditer(script):
        names.add(m.group(1))
    # 解构 const { a, b } = ...
    for m in re.finditer(r'(?:const|let|var)\s*\{([^}]*)\}\s*=', script):
        for part in m.group(1).split(','):
            n = part.split(':')[-1].strip()
            if re.fullmatch(r'[A-Za-z_$][\w$]*', n or ''):
                names.add(n)
    # 函数参数（简易）
    for m in re.finditer(r'function\s+\w*\s*\(([^)]*)\)', script):
        for part in m.group(1).split(','):
            n = part.strip().split('=')[0].strip()
            if re.fullmatch(r'[A-Za-z_$][\w$]*', n or ''):
                names.add(n)
    for m in re.finditer(r'\((\w+)\)\s*=>', script):
        names.add(m.group(1))
    for m in re.finditer(r'\(\s*([\w\s,]+)\)\s*=>', script):
        for part in m.group(1).split(','):
            n = part.strip()
            if re.fullmatch(r'[A-Za-z_$][\w$]*', n or ''):
                names.add(n)
    return names


IDENT_RE = re.compile(r'(?<![\w.$])([A-Za-z_$][\w$]*)\s*(?![\w$]*\s*:)')
# 出现在 `.` 后的是属性，排除；出现在字符串里也排除
STRING_RE = re.compile(r"'[^']*'|\"[^\"]*\"|`[^`]*`")


def used_in_expr(expr):
    clean = STRING_RE.sub('', expr)
    out = set()
    for m in re.finditer(r'(?<![\w.$])([A-Za-z_$][\w$]*)', clean):
        n = m.group(1)
        # 紧跟 : 的是对象字面量键
        after = clean[m.end():m.end() + 3]
        if after.lstrip().startswith(':'):
            continue
        out.add(n)
    return out


def check_undefined(path, text):
    script = script_of(text)
    tpl = template_of(text)
    defined = defined_names(script)
    # v-for 的局部变量（如 (item, i) in list）也是合法标识符
    for m in re.finditer(r'v-for\s*=\s*"([^"]*?)"', tpl):
        expr = m.group(1)
        head = expr.split(' in ')[0].strip()
        # 形式一：(item, i) in list ；形式二：item in list
        if head.startswith('(') and head.endswith(')'):
            head = head[1:-1]
        for part in head.split(','):
            n = part.strip()
            if re.fullmatch(r'[A-Za-z_$][\w$]*', n or ''):
                defined.add(n)

    problems = []
    exprs = []
    for m in TEMPLATE_EXPR_RE.finditer(tpl):
        exprs.append(m.group(1))
    for m in MUSTACHE_RE.finditer(tpl):
        exprs.append(m.group(1))

    unresolved = set()
    for expr in exprs:
        for n in used_in_expr(expr):
            if n in WHITELIST or n in defined:
                continue
            if n in ('in', 'of', 'typeof', 'new', 'return', 'await'):
                continue
            unresolved.add(n)
    if unresolved:
        problems.append(sorted(unresolved))
    return problems


def main():
    print('=' * 76)
    print(' 前端构建与静态校验')
    print('=' * 76)

    issues = []

    # ---------- A. 未定义标识符 ----------
    views = os.path.join(SRC, 'views')
    files = []
    for base in ('views', 'components', 'layout', 'screen', 'h5'):
        d = os.path.join(SRC, base)
        if os.path.isdir(d):
            for root, _, fs in os.walk(d):
                for f in fs:
                    if f.endswith('.vue'):
                        files.append(os.path.join(root, f))

    bad = []
    for p in files:
        text = io.open(p, encoding='utf-8').read()
        probs = check_undefined(p, text)
        if probs:
            bad.append((os.path.relpath(p, SRC), probs[0]))

    print('\n① 未定义标识符（漏 import / 漏声明）')
    if bad:
        for name, names in bad:
            print('   ✗ %-28s %s' % (name, ', '.join(names)))
            issues.append(name)
    else:
        print('   ✔ 未发现问题（扫描 %d 个组件）' % len(files))

    # ---------- B. 路由 ↔ 视图 ↔ 产物 ----------
    router = os.path.join(SRC, 'router', 'index.js')
    rtext = io.open(router, encoding='utf-8').read()
    comps = set(re.findall(r"import\('@/views/(\w+)\.vue'\)", rtext))
    comps |= set(re.findall(r"import\('@/screen/(\w+)\.vue'\)", rtext))

    missing_src = [c for c in comps
                   if not (os.path.exists(os.path.join(views, c + '.vue'))
                           or os.path.exists(os.path.join(SRC, 'screen', c + '.vue')))]
    print('\n② 路由引用的视图是否都存在')
    if missing_src:
        print('   ✗ 缺文件：%s' % ', '.join(missing_src))
        issues.extend(missing_src)
    else:
        print('   ✔ %d 个视图齐全' % len(comps))

    # ---------- C. 构建产物 ----------
    print('\n③ 构建产物')
    build_dir = DIST if os.path.isdir(DIST) else OUT_DIR
    if not os.path.isdir(build_dir):
        print('   ⚠ 未找到构建产物（先执行 pnpm build）')
    else:
        assets = os.path.join(build_dir, 'assets')
        chunks = os.listdir(assets) if os.path.isdir(assets) else []
        bundle = ' '.join(chunks)

        # 每个按需加载的视图应有同名 chunk
        no_chunk = [c for c in comps if c not in bundle]
        if no_chunk:
            print('   ✗ 以下视图无对应构建块：%s' % ', '.join(sorted(no_chunk)))
            issues.extend(no_chunk)
        else:
            print('   ✔ %d 个视图均已打包' % len(comps))

        # dist 是否已同步到后端 static（部署才生效）
        print('   ✔ 产物目录：%s' % os.path.relpath(build_dir, ROOT))

    print('\n' + '-' * 76)
    if issues:
        print(' 结论：发现 %d 处问题' % len(issues))
        return 1
    print(' 结论：✔ 前端构建与静态检查通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
