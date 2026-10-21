# -*- coding: utf-8 -*-
"""修正检查脚本：defineProps 括号配平解析 + 产物目录用 static"""
import io
import re

C = r'D:\Work\业务平台开发\_验证\_check_build.py'
s = io.open(C, encoding='utf-8').read()

# 1) 产物目录：本项目 outDir 指向 backend static，没有 frontend/dist
s = s.replace("DIST = os.path.join(ROOT, 'frontend', 'dist')",
              "DIST = os.path.join(ROOT, 'frontend', 'dist')\n"
              "# 本项目 vite outDir 指向 backend static，dist 可能不存在\n"
              "OUT_DIR = os.path.join(ROOT, 'backend', 'src', 'main', 'resources', 'static')")

s = s.replace("    if not os.path.isdir(DIST):\n"
              "        print('   ⚠ 未找到 dist（先执行 pnpm build）')\n"
              "    else:\n"
              "        assets = os.path.join(DIST, 'assets')",
              "    build_dir = DIST if os.path.isdir(DIST) else OUT_DIR\n"
              "    if not os.path.isdir(build_dir):\n"
              "        print('   ⚠ 未找到构建产物（先执行 pnpm build）')\n"
              "    else:\n"
              "        assets = os.path.join(build_dir, 'assets')")

s = s.replace("        dist_index = os.path.join(DIST, 'index.html')\n"
              "        static_index = os.path.join(STATIC, 'index.html')\n"
              "        if os.path.exists(dist_index) and os.path.exists(static_index):\n"
              "            a = os.path.getmtime(dist_index)\n"
              "            b = os.path.getmtime(static_index)\n"
              "            if a > b + 1:\n"
              "                print('   ⚠ dist 比 static 新（需重新打包 jar 才生效）')\n"
              "            else:\n"
              "                print('   ✔ dist 已同步到 static')",
              "        print('   ✔ 产物目录：%s' % os.path.relpath(build_dir, ROOT))")

# 2) defineProps：括号配平解析顶层键
old = """    # defineProps({ columns: ... }) 里的键也是可用标识符
    for m in re.finditer(r'defineProps(?:<[^>]*>)?\\s*\\(\\s*\\{([\\s\\S]{0,400}?)\\}', script):
        for k in re.findall(r'([A-Za-z_$][\\w$]*)\\s*:', m.group(1)):
            names.add(k)"""
new = """    # defineProps({ ... }) 里的顶层键也是可用标识符（用括号配平，支持多行与嵌套）
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
        for k in re.findall(r'^\\s{4}([A-Za-z_$][\\w$]*)\\s*:', block, re.M):
            names.add(k)
        for k in re.findall(r'([A-Za-z_$][\\w$]*)\\s*:\\s*\\{\\s*type:', block):
            names.add(k)"""
if old in s:
    s = s.replace(old, new, 1)
    print('  ✓ defineProps 改为括号配平解析')

io.open(C, 'w', encoding='utf-8').write(s)
print('  ✓ 产物目录改为 static')
