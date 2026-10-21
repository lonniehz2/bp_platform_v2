# -*- coding: utf-8 -*-
"""补：gQuery/vQuery 增加 keyword 字段，列表请求透传关键字，已通过的核验记录隐藏按钮。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Persons.vue')

s = io.open(P, encoding='utf-8').read()
done = []

s = s.replace("const gQuery = reactive({ pageNum: 1, pageSize: 20 })",
              "const gQuery = reactive({ pageNum: 1, pageSize: 20, keyword: '' })", 1)
s = s.replace("const vQuery = reactive({ pageNum: 1, pageSize: 20 })",
              "const vQuery = reactive({ pageNum: 1, pageSize: 20, keyword: '' })", 1)
if "gQuery = reactive({ pageNum: 1, pageSize: 20, keyword" in s:
    done.append('query.keyword')

# 保障档案分页请求：找到 loadProfiles 内的 params 传参
m = re.search(r'async function loadProfiles\(\)[\s\S]{0,900}?\n\}', s)
if m and 'gQuery.keyword' not in m.group(0):
    block = m.group(0)
    nb = block.replace('pageSize: gQuery.pageSize',
                       "pageSize: gQuery.pageSize, keyword: gQuery.keyword || undefined", 1)
    if nb == block:
        nb = block.replace('...', '...', 1)
    s = s[:m.start()] + nb + s[m.end():]
    done.append('loadProfiles')

m2 = re.search(r'async function loadVerifies\(\)[\s\S]{0,900}?\n\}', s)
if m2 and 'vQuery.keyword' not in m2.group(0):
    block = m2.group(0)
    nb = block.replace('pageSize: vQuery.pageSize',
                       "pageSize: vQuery.pageSize, keyword: vQuery.keyword || undefined", 1)
    s = s[:m2.start()] + nb + s[m2.end():]
    done.append('loadVerifies')

s = s.replace('''<el-button link type="primary" @click="openVerifyFor(row)">发起核签</el-button>''',
              '''<el-button v-if="Number(row.verifyPass) !== 1" link type="primary"
                         @click="openVerifyFor(row)">实名核验</el-button>
              <span v-else class="muted">已通过</span>''', 1)
if 'Number(row.verifyPass) !== 1' in s:
    done.append('已通过隐藏按钮')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用：', '、'.join(done))
print('关键字出现次数 g=%d v=%d' % (s.count('gQuery.keyword'), s.count('vQuery.keyword')))
