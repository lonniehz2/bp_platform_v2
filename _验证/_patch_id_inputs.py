# -*- coding: utf-8 -*-
"""把常用'填 ID'输入换成名称搜索组件。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

edits = {
    'Arrears.vue': [
        ('<el-input v-model.number="af.contractId" placeholder="合同ID" clearable',
         '<ContractSelect v-model="af.contractId" width="200px" testid="arrears-contract" />\n        <!--'),
        ('<el-input v-model.number="af.personId" placeholder="人员ID" clearable',
         '<PersonPicker v-model="af.personId" width="200px" testid="arrears-person" />\n        <!--'),
    ],
    'Deposits.vue': [
        ('<el-input v-model="df.contractId" placeholder="合同 ID" clearable',
         '<ContractSelect v-model="df.contractId" width="200px" testid="deposit-contract" />\n        <!--'),
    ],
    'Terminations.vue': [
        ('<el-input v-model="tf.contractId" placeholder="合同 ID" clearable style="width:200px" />',
         '<ContractSelect v-model="tf.contractId" width="200px" testid="term-contract" />'),
    ],
    'AccessRecords.vue': [
        ('<el-input v-model="query.houseId" placeholder="房源ID" clearable',
         '<HouseSelect v-model="query.houseId" width="220px" testid="access-house" />\n        <!--'),
    ],
    'OpsCenter.vue': [
        ('<el-input v-model="pid" placeholder="人员ID" style="width:200px" />',
         '<PersonPicker v-model="pid" width="200px" testid="ops-person" />'),
        ('<el-input v-model="hid" placeholder="房源ID" style="width:200px" />',
         '<HouseSelect v-model="hid" width="220px" testid="ops-house" />'),
    ],
    'Grants.vue': [
        ('<el-input v-model.number="gq.personId" placeholder="人员ID" clearable',
         '<PersonPicker v-model="gq.personId" width="200px" testid="grant-person" />\n        <!--'),
        ('<el-input v-model.number="gf.personId" placeholder="人员ID" />',
         '<PersonPicker v-model="gf.personId" width="100%" testid="grant-form-person" />'),
    ],
}

imports = {
    'Arrears.vue': ["import PersonPicker from '@/components/PersonPicker.vue'",
                    "import ContractSelect from '@/components/ContractSelect.vue'"],
    'Deposits.vue': ["import ContractSelect from '@/components/ContractSelect.vue'"],
    'Terminations.vue': ["import ContractSelect from '@/components/ContractSelect.vue'"],
    'AccessRecords.vue': ["import HouseSelect from '@/components/HouseSelect.vue'"],
    'OpsCenter.vue': ["import PersonPicker from '@/components/PersonPicker.vue'",
                      "import HouseSelect from '@/components/HouseSelect.vue'"],
    'Grants.vue': ["import PersonPicker from '@/components/PersonPicker.vue'"],
}

for fname, pairs in edits.items():
    p = os.path.join(VIEWS, fname)
    s = io.open(p, encoding='utf-8').read()
    for old, new in pairs:
        if old not in s:
            print(fname, '未匹配:', old[:50])
            continue
        s = s.replace(old, new, 1)
        # 注释掉原来 el-input 剩余属性行（以 placeholder 后的续行）
    # 清理残留：形如  `<!-- ... />` 后接原 attributes 的多行
    s = re.sub(r'<!--\n\s*(?:clearable|style=|data-testid=|@keyup\.enter=)[^\n]*\n\s*/>?', '', s)
    # 添加 import
    for imp in imports.get(fname, []):
        name = imp.split('import ')[1].split(' from')[0]
        if ("import " + name) not in s:
            s = s.replace("import req from '@/api/request'",
                          "import req from '@/api/request'\n" + imp, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print(fname, '已处理')
