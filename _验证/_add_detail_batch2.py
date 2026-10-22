# -*- coding: utf-8 -*-
"""第二批：剩余页面补详情入口 + 操作列宽度策略。

策略：
  · 表格列少（≤6 列）的页面：操作列加宽，保证按钮一行显示
  · 列多（≥8 列）的页面：本脚本只提示，交给下拉模式改造
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

IMPORT_LINE = "import DetailView from '@/components/DetailView.vue'"

STATE = '''
/** 通用详情弹窗（复用 DetailView） */
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

TABLE = [
    'Applications.vue', 'Bills.vue', 'Deposits.vue', 'Devices.vue', 'FeeItems.vue',
    'Allocations.vue', 'AnnualReviews.vue', 'Grants.vue', 'Messages.vue',
    'OpsCenter.vue', 'OpsExtras.vue',
]


def columns_count(s):
    return len(re.findall(r'<el-table-column', s))


def main():
    done, failed = [], []
    for fn in TABLE:
        p = os.path.join(V, fn)
        if not os.path.exists(p):
            failed.append(fn + '（不存在）')
            continue
        s = io.open(p, encoding='utf-8').read()

        # 1) 引入组件
        if 'DetailView' not in s:
            if "from 'vue'" in s:
                s = re.sub(r"(import \{[^}]*\} from 'vue')", r"\1\n" + IMPORT_LINE, s, count=1)
            else:
                s = s.replace('<script setup>', '<script setup>\n' + IMPORT_LINE, 1)

        # 2) 状态与函数
        if 'function openDetail' not in s:
            s = s.replace('<script setup>', '<script setup>' + STATE, 1)

        # 3) 弹窗
        if '<el-dialog v-model="dvVisible"' not in s:
            idx = s.rfind('</template>')
            s = s[:idx] + DIALOG + s[idx:]

        # 4) 详情按钮：插入操作列第一个按钮之前
        if not re.search(r'>\s*详\s*情\s*<', s):
            m = re.search(r'(<el-table-column[^>]*label="操作"[^>]*>\s*\n(\s*)<template #default="\{ row \}">)', s)
            if m:
                ind = m.group(2)
                btn = ('\n' + ind + '  <el-button link type="primary" '
                       '@click="openDetail(row)" data-testid="row-detail">详情</el-button>')
                s = s[:m.start()] + m.group(1) + btn + s[m.end():]
            else:
                # 操作列没有 template：整列替换
                m2 = re.search(r'<el-table-column[^>]*label="操作"[^>]*>[\s\S]{0,400}?</el-table-column>', s)
                if not m2:
                    failed.append(fn + '（未找到操作列）')
                    io.open(p, 'w', encoding='utf-8', newline='').write(s)
                    continue
                block = m2.group(0)
                block = re.sub(r'(<template #default="\{ row \}">)',
                               r'\1\n            <el-button link type="primary" '
                               r'@click="openDetail(row)" data-testid="row-detail">详情</el-button>',
                               block, count=1)
                s = s[:m2.start()] + block + s[m2.end():]

        # 5) 列少的页面：加宽操作列，让按钮一行放下
        cols = columns_count(s)
        btn_cnt = max(1, len(re.findall(r'<el-button[^>]*link', s)))
        if cols <= 7:
            need = min(360, 80 * btn_cnt + 40)
            m3 = re.search(r'(label="操作"[^>]*?)width="(\d+)"', s)
            if m3 and int(m3.group(2)) < need:
                s = s[:m3.start(2)] + 'width="%d"' % need + s[m3.end(2):]

        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        done.append('%s（列 %d，按钮 %d）' % (fn, cols, btn_cnt))

    print('已处理 %d 个：' % len(done))
    for x in done:
        print('   ', x)
    if failed:
        print('需人工处理：')
        for x in failed:
            print('   ', x)


if __name__ == '__main__':
    main()
