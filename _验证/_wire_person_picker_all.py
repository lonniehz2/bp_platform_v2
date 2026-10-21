# -*- coding: utf-8 -*-
"""把人员查询输入框统一替换为 PersonPicker（远程搜索 + 重名可区分）。

规则：
  - 匹配 v-model="xxx.personId" / v-model="personId" 的 <el-input ...>
  - 多行标签（<el-input 开头，以 /> 结尾）整体替换
  - 保留原 data-testid（若在属性里）以便既有测试继续可用
  - 自动补 import PersonPicker（若文件里还没有）
  - Persons.vue 内的「人员ID查询」保留原生输入（该页需要按精确 ID 定位，且已单独处理）

排除：Persons.vue（刻意保留精确 ID 输入）
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

SKIP_FILES = {'Persons.vue'}

# <el-input ... v-model="X.personId" ... />  （允许跨行，自闭合）
INPUT_RE = re.compile(
    r'<el-input\b[^>]*?v-model="([\w.]*personId)"[^>]*?/>',
    re.S,
)


def main():
    changed = []
    for fn in sorted(os.listdir(V)):
        if not fn.endswith('.vue') or fn in SKIP_FILES:
            continue
        p = os.path.join(V, fn)
        s = io.open(p, encoding='utf-8').read()
        if 'personId' not in s:
            continue

        def repl(m):
            model = m.group(1)
            return ('<PersonPicker v-model="%s" width="240px" testid="person-picker" />'
                    % model)

        new, n = INPUT_RE.subn(repl, s)
        if n == 0:
            continue

        # 已在模板中使用 PersonPicker 但没导入 → 补导入
        if 'PersonPicker' in new and "from '@/components/PersonPicker.vue'" not in new:
            m = re.search(r"^import .*from 'vue'\s*$", new, re.M)
            if m:
                new = new[:m.end()] + "\nimport PersonPicker from '@/components/PersonPicker.vue'" + new[m.end():]
            else:
                # 没有 vue 导入时，插到 <script setup> 之后
                new = new.replace('<script setup>',
                                  "<script setup>\nimport PersonPicker from '@/components/PersonPicker.vue'", 1)

        io.open(p, 'w', encoding='utf-8', newline='').write(new)
        changed.append((fn, n))

    total = sum(n for _, n in changed)
    for fn, n in changed:
        print('%-26s %d 处' % (fn, n))
    print('\n合计替换 %d 处，涉及 %d 个文件' % (total, len(changed)))


if __name__ == '__main__':
    main()
