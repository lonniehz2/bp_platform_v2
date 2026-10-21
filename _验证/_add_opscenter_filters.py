# -*- coding: utf-8 -*-
"""给 OpsCenter 三个 tab 各加一行筛选（关键字 + 查询 + 清空）

三个列表接口（/persons、/houses、/workorders）都已支持 keyword，纯前端改动。
"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views', 'OpsCenter.vue')

BAR = '''        <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="filters.%s" placeholder="%s" clearable style="width:200px"
                    data-testid="oc-%s" @keyup.enter="loadAll" />
          <el-button type="primary" @click="loadAll">查询</el-button>
          <el-button @click="resetFilter('%s')">清空</el-button>
        </div>
'''

TARGETS = [
    ('person', '姓名 / 证件号 / 手机', '<el-table :data="persons"'),
    ('house', '房源编号 / 名称', '<el-table :data="houses"'),
    ('order', '工单号 / 标题', '<el-table :data="orders"'),
]

STATE = '''const filters = reactive({ person: '', house: '', order: '' })
function resetFilter(k) {
  filters[k] = ''
  loadAll()
}
'''


def main():
    s = io.open(V, encoding='utf-8').read()
    if 'const filters = reactive' in s:
        print('已改造，跳过')
        return 0
    for key, ph, anchor in TARGETS:
        if anchor not in s:
            print('未找到锚点:', anchor)
            return 1
        s = s.replace(anchor, (BAR % (key, ph, key, key)) + anchor, 1)
    # 注入状态
    if 'const tab = ref(' in s:
        i = s.index('const tab = ref(')
        j = s.index('\n', i) + 1
        s = s[:j] + STATE + s[j:]
    else:
        print('未找到 tab 定义')
        return 1
    # 三个请求带 keyword
    s = s.replace("req.get('/persons', { params: { pageNum: 1, pageSize: 20 } })",
                  "req.get('/persons', { params: { pageNum: 1, pageSize: 20, keyword: filters.person || undefined } })", 1)
    s = s.replace("req.get('/houses', { params: { pageNum: 1, pageSize: 20 } })",
                  "req.get('/houses', { params: { pageNum: 1, pageSize: 20, keyword: filters.house || undefined } })", 1)
    s = s.replace("req.get('/workorders', { params: { pageNum: 1, pageSize: 20 } })",
                  "req.get('/workorders', { params: { pageNum: 1, pageSize: 20, keyword: filters.order || undefined } })", 1)
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('已改造：3 个筛选行 + keyword 参数')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
