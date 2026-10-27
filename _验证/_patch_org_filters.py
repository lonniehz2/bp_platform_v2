# -*- coding: utf-8 -*-
"""合同/账单按组织筛选。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---- 后端：合同 service 接口 + 实现 + 控制器 ----
p = os.path.join(BK, 'service', 'ContractService.java')
s = io.open(p, encoding='utf-8').read()
if 'Long orgId' not in s:
    s = s.replace('''    PageResult<ContractVO> page(long pageNum, long pageSize, String contractType,''',
                  '''    PageResult<ContractVO> page(long pageNum, long pageSize, Long orgId, String contractType,''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('接口已加 orgId')

p = os.path.join(BK, 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'public PageResult<ContractVO> page(long pageNum, long pageSize, Long orgId' not in s:
    s = s.replace('''    public PageResult<ContractVO> page(long pageNum, long pageSize, String contractType,
                                       String status, Long houseId, Long lesseePersonId,
                                       String keyword) {''',
                  '''    public PageResult<ContractVO> page(long pageNum, long pageSize, Long orgId,
                                       String contractType, String status, Long houseId,
                                       Long lesseePersonId, String keyword) {''', 1)
    s = s.replace('''                .eq(houseId != null, BizContract::getHouseId, houseId)''',
                  '''                .eq(orgId != null, BizContract::getOrgId, orgId)
                .eq(houseId != null, BizContract::getHouseId, houseId)''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('实现已加 orgId')

p = os.path.join(BK, 'controller', 'ContractController.java')
s = io.open(p, encoding='utf-8').read()
if 'Long orgId' not in s:
    s = s.replace('''                                          @RequestParam(required = false) String contractType,''',
                  '''                                          @RequestParam(required = false) Long orgId,
                                          @RequestParam(required = false) String contractType,''', 1)
    s = s.replace('''        return R.ok(contractService.page(pageNum, pageSize, contractType, status, houseId,
                lesseePersonId, keyword));''',
                  '''        return R.ok(contractService.page(pageNum, pageSize, orgId, contractType, status,
                houseId, lesseePersonId, keyword));''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('控制器已加 orgId')

# ---- 前端：合同组织筛选 ----
p = os.path.join(VIEWS, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
if 'OrgSelect' in s and 'q.orgId' not in s:
    s = s.replace('''        <el-select v-model="q.contractStatus" placeholder="状态" clearable''',
                  '''        <OrgSelect v-model="q.orgId" width="200px" testid="contract-org-filter"
                   placeholder="组织名称" @update:model-value="reload" />
        <el-select v-model="q.contractStatus" placeholder="状态" clearable''', 1)
    s = s.replace("const q = reactive({", "const q = reactive({ orgId: '',", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('合同页已加组织筛选')

# 合同 load 传参
p = os.path.join(VIEWS, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
if 'orgId: q.orgId' not in s:
    import re
    s2 = re.sub(r"(contractApi\.page\(\{[^}]*?)(keyword: q\.keyword \|\| undefined)",
                r"\1orgId: q.orgId || undefined,\n      \2", s, count=1)
    if s2 != s:
        io.open(p, 'w', encoding='utf-8', newline='').write(s2)
        print('合同查询已带 orgId')

# ---- 前端：账单组织筛选 ----
p = os.path.join(VIEWS, 'Bills.vue')
s = io.open(p, encoding='utf-8').read()
if 'bill-org-filter' not in s:
    s = s.replace('''        <el-select v-model="q.billStatus" placeholder="状态" clearable''',
                  '''        <OrgSelect v-model="q.orgId" width="200px" testid="bill-org-filter"
                   placeholder="组织名称" @update:model-value="reload" />
        <el-select v-model="q.billStatus" placeholder="状态" clearable''', 1)
    if "import OrgSelect" not in s:
        s = s.replace("import req from '@/api/request'",
                      "import req from '@/api/request'\nimport OrgSelect from '@/components/OrgSelect.vue'", 1)
    s = s.replace("const q = reactive({", "const q = reactive({ orgId: '',", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('账单页已加组织筛选')
