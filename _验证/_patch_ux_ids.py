# -*- coding: utf-8 -*-
"""把裸 ID 输入替换成组织/房源选择器。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')


def patch(fn, pairs, imports=()):
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  !', fn, '未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', fn, label)
    for imp in imports:
        if imp not in s:
            s = s.replace("import req from '@/api/request'",
                          "import req from '@/api/request'\n" + imp, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)


patch('Alerts.vue', [
    ('''<el-input v-model="form.orgId" /></el-form-item></el-col>''',
     '''<OrgSelect v-model="form.orgId" width="100%" /></el-form-item></el-col>''', 'org'),
    ('''<el-input v-model="form.houseId" /></el-form-item></el-col>''',
     '''<HouseSelect v-model="form.houseId" width="100%" /></el-form-item></el-col>''', 'house'),
], ("import OrgSelect from '@/components/OrgSelect.vue'",
    "import HouseSelect from '@/components/HouseSelect.vue'"))

patch('Complaints.vue', [
    ('''<el-input v-model="form.orgId" /></el-form-item></el-col>''',
     '''<OrgSelect v-model="form.orgId" width="100%" /></el-form-item></el-col>''', 'org'),
], ("import OrgSelect from '@/components/OrgSelect.vue'",))

patch('AnnualReviews.vue', [
    ('''<el-form-item label="组织ID"><el-input v-model="b.orgId" /></el-form-item>''',
     '''<el-form-item label="组织"><OrgSelect v-model="b.orgId" width="100%" /></el-form-item>''', 'org'),
], ("import OrgSelect from '@/components/OrgSelect.vue'",))

patch('Subsidies.vue', [
    ('''<el-form-item label="组织ID"><el-input v-model="bf.orgId" /></el-form-item>''',
     '''<el-form-item label="组织"><OrgSelect v-model="bf.orgId" width="100%" /></el-form-item>''', 'org'),
], ("import OrgSelect from '@/components/OrgSelect.vue'",))

patch('Waitlist.vue', [
    ('''<el-input v-model="ef.orgId" /></el-form-item>''',
     '''<OrgSelect v-model="ef.orgId" width="100%" /></el-form-item>''', 'org'),
], ("import OrgSelect from '@/components/OrgSelect.vue'",))

patch('HouseCalendar.vue', [
    ('''<el-input v-model="bf.houseId" placeholder="可从列表行点「预订」自动带入" />''',
     '''<HouseSelect v-model="bf.houseId" width="100%" placeholder="输入房源编号/名称搜索" />''', 'bf'),
    ('''<el-form-item label="房源 ID" required><el-input v-model="rf.houseId" /></el-form-item>''',
     '''<el-form-item label="房源" required><HouseSelect v-model="rf.houseId" width="100%" /></el-form-item>''', 'rf'),
    ('''<el-input v-model="rf2.houseId" placeholder="从列表行点「批量设置」自动带入" />''',
     '''<HouseSelect v-model="rf2.houseId" width="100%" placeholder="输入房源编号/名称搜索" />''', 'rf2'),
], ("import HouseSelect from '@/components/HouseSelect.vue'",))
