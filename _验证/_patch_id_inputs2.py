# -*- coding: utf-8 -*-
"""把常用'填 ID'输入换成名称搜索组件（整块替换）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

MAP = {
    '合同ID': ('ContractSelect', 'contract-select'),
    '合同 ID': ('ContractSelect', 'contract-select'),
    '人员ID': ('PersonPicker', 'picker'),
    '房源ID': ('HouseSelect', 'house-select'),
}

FILES = ['Arrears.vue', 'Deposits.vue', 'Terminations.vue',
         'AccessRecords.vue', 'OpsCenter.vue', 'Grants.vue']

for fname in FILES:
    p = os.path.join(VIEWS, fname)
    s = io.open(p, encoding='utf-8').read()
    changed = 0

    def repl(m):
        global changed
        block = m.group(0)
        ph = m.group(1)
        if ph not in MAP:
            return block
        comp, testid = MAP[ph]
        vm = re.search(r'v-model(?:\.number)?="([^"]+)"', block)
        if not vm:
            return block
        model = vm.group(1).replace('.number', '')
        width = '200px'
        sm = re.search(r'style="width:\s*([0-9]+px)', block)
        if sm:
            width = sm.group(1)
        changed += 1
        return '<%s v-model="%s" width="%s" testid="%s" />' % (comp, model, width, testid)

    s2 = re.sub(r'<el-input[^>]*placeholder="([^"]*ID[^"]*)"[^>]*/>', repl, s)
    if changed:
        for comp in {'ContractSelect', 'PersonPicker', 'HouseSelect'}:
            if ('<%s' % comp) in s2 and ("import " + comp) not in s2:
                s2 = s2.replace("import req from '@/api/request'",
                                "import req from '@/api/request'\nimport %s from '@/components/%s.vue'" % (comp, comp), 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(s2)
    print(fname, '替换', changed)
