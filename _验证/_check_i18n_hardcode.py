# -*- coding: utf-8 -*-
"""增量多语言门禁：只检查本次 diff 新增/修改行，避免存量中文一次性失败。

用法：
  python _验证/_check_i18n_hardcode.py
  python _验证/_check_i18n_hardcode.py --staged

规则：
- 新增/修改的前端页面、布局、组件、后端 Java 行中出现中文 → 失败；
- 允许：i18n 语言包、帮助内容、注释行、已有 $t()/t() 文案；
- 新建的 .vue/.js 文件只要含中文，直接失败（避免新页面继续硬编码）。
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ALLOW_PATHS = (
    'frontend/src/i18n/',
    'frontend/src/content/help.js',
    'backend/src/main/resources/i18n/',
    'backend/src/main/resources/static/',
)
ZH = re.compile(r'[\u4e00-\u9fff]')
COMMENT = re.compile(r'^\s*(//|/\*|\*|<!--|#)')
# 允许的文案调用：$t('...') / t('...')，但 key 本身不应含中文
T_CALL = re.compile(r"(\$t|\bt)\(\s*['\"]")


def rel(p):
    return os.path.relpath(p, ROOT).replace('\\', '/')


def allowed(path):
    return any(path.startswith(p) for p in ALLOW_PATHS)


def git(*args):
    return subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True,
                          text=True, encoding='utf-8', errors='replace')


def scan_diff(staged):
    args = ['diff', '--unified=0']
    if staged:
        args.append('--cached')
    args.append('HEAD')
    out = git(*args).stdout
    violations = []
    current = ''
    for raw in out.splitlines():
        if raw.startswith('+++ b/'):
            current = raw[6:]
        elif raw.startswith('+') and not raw.startswith('+++'):
            text = raw[1:].strip()
            if not text or COMMENT.match(text):
                continue
            if allowed(current) or not ZH.search(text):
                continue
            if T_CALL.search(text):
                # 参数里若还有中文，仍然失败；纯 key 放行
                after = text[text.find('(') + 1:]
                if not ZH.search(after):
                    continue
            violations.append((current, text[:160]))
    return violations


def scan_new_files():
    out = git('ls-files', '--others', '--exclude-standard').stdout
    violations = []
    for path in out.splitlines():
        if not path.endswith(('.vue', '.js', '.java')):
            continue
        if allowed(path):
            continue
        full = os.path.join(ROOT, path)
        try:
            text = open(full, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        bad = False
        for line in text.splitlines():
            t = line.strip()
            if not t or COMMENT.match(t) or not ZH.search(t):
                continue
            if T_CALL.search(t):
                after = t[t.find('(') + 1:]
                if not ZH.search(after):
                    continue
            bad = True
            break
        if bad:
            violations.append((path, '新建文件包含硬编码中文，应使用 t() / 语言包'))
    return violations


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--staged', action='store_true')
    args = ap.parse_args()
    violations = scan_diff(args.staged) + scan_new_files()
    if not violations:
        print('✔ 多语言增量门禁通过：本次 diff 未新增硬编码中文')
        return 0
    print('✗ 发现新增硬编码中文：')
    for path, text in violations[:50]:
        print('  %s: %s' % (path, text))
    print('\n请改为 t(\'domain.key\') 并补充 zh-CN / en-US 语言包。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
