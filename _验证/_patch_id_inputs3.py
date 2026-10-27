# -*- coding: utf-8 -*-
"""剩余 ID 输入：空间/计费项/用户/房源 换选择器。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

MAP = {
    '空间ID': ('SpaceSelect', '空间名称搜索'),
    '计费项目 ID': ('FeeItemSelect', '计费项名称搜索'),
    '用户ID': ('UserSelect', '用户名/姓名搜索'),
    '房源ID': ('HouseSelect', '房源编号/名称搜索'),
}

FILES = ['Devices.vue', 'Grants.vue', 'FeeItems.vue', 'OpsExtras.vue']

for fname in FILES:
    p = os.path.join(VIEWS, fname)
    s = io.open(p, encoding='utf-8').read()
    count = 0

    def repl(m):
        global count
        block, ph = m.group(0), m.group(1)
        if ph not in MAP:
            return block
        comp, _ = MAP[ph]
        vm = re.search(r'v-model(?:\.number)?="([^"]+)"', block)
        if not vm:
            return block
        model = vm.group(1).replace('.number', '')
        width = '200px'
        sm = re.search(r'style="width:\s*([0-9]+px)', block)
        if sm:
            width = sm.group(1)
        count += 1
        return '<%s v-model="%s" width="%s" testid="%s" />' % (
            comp, model, width, comp.lower())

    s2 = re.sub(r'<el-input[^>]*placeholder="([^"]*ID[^"]*)"[^>]*/>', repl, s)
    if count:
        for comp in {'SpaceSelect', 'FeeItemSelect', 'UserSelect', 'HouseSelect'}:
            if ('<%s' % comp) in s2 and ('import ' + comp) not in s2:
                s2 = s2.replace("import req from '@/api/request'",
                                "import req from '@/api/request'\nimport %s from '@/components/%s.vue'" % (comp, comp), 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(s2)
    print(fname, '替换', count)
