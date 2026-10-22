# -*- coding: utf-8 -*-
"""批量为「已引入 DetailView 但表格没有详情入口」的页面补齐「详情」按钮与弹窗。

做法：
  1. 在「操作」列的 <template #default="{ row }"> 之后插入详情按钮
  2. 在 </template> 前插入详情弹窗（复用 DetailView）
  3. 在 <script setup> 内补状态与打开函数（用 dv 前缀避免与页面已有变量冲突）
只处理已 import DetailView 的页面；没有该组件的页面留待下一批。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

STATE = '''
/** 通用详情弹窗（复用 DetailView，字段与中文名来自后端字段字典） */
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}
'''

DIALOG = '''
    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
'''


def process(fn):
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    if '<DetailView' not in s or re.search(r'>\s*详\s*情\s*<', s):
        return None
    # 1) 找操作列
    m = re.search(r'label="操作"[^>]*>\s*\n(\s*)<template #default="\{ row \}">', s)
    if not m:
        # 兼容操作列没有 template 直接放按钮的情况
        m2 = re.search(r'(label="操作"[^>]*>)', s)
        if not m2:
            return None
        return None
    indent = m.group(1)
    insert = (m.group(0) + '\n' + indent + '  <el-button link type="primary" '
              '@click="openDetail(row)" data-testid="row-detail">详情</el-button>')
    s = s[:m.start()] + insert + s[m.end():]

    # 2) 弹窗
    idx = s.rfind('</template>')
    s = s[:idx] + DIALOG + s[idx:]

    # 3) 状态与函数：插在 <script setup> 之后
    if 'function openDetail' not in s:
        s = s.replace('<script setup>', '<script setup>' + STATE, 1)

    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return fn


def main():
    done = []
    skipped = []
    for fn in sorted(os.listdir(V)):
        if not fn.endswith('.vue'):
            continue
        r = process(fn)
        if r:
            done.append(fn)
        else:
            s = io.open(os.path.join(V, fn), encoding='utf-8').read()
            if '<DetailView' in s:
                skipped.append(fn)
    print('已补详情入口 %d 个：' % len(done))
    for fn in done:
        print('   ', fn)
    if skipped:
        print('跳过（未匹配操作列或已有入口）%d 个：' % len(skipped))
        for fn in skipped:
            print('   ', fn)


if __name__ == '__main__':
    main()
