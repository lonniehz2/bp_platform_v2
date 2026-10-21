# -*- coding: utf-8 -*-
"""把配租公示硬校验接入签约（决策 D23 强制生效）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
p = os.path.join(BASE, r'biz\service\impl\AllocationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if 'publicityService' in s:
    print('已接入，跳过')
    raise SystemExit

# 1) import
s = s.replace('import com.yundao.bp.biz.service.AllocationService;',
              'import com.yundao.bp.biz.service.AllocationService;\n'
              'import com.yundao.bp.biz.service.PublicityService;', 1)

# 2) 字段
s = s.replace('''    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;''',
              '''    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;
    private final PublicityService publicityService;''', 1)

# 3) 构造器
s = s.replace('''                                 AssetHouseMapper houseMapper,
                                 SnowflakeIdGenerator idGen) {''',
              '''                                 AssetHouseMapper houseMapper,
                                 SnowflakeIdGenerator idGen,
                                 PublicityService publicityService) {''', 1)
s = s.replace('''        this.houseMapper = houseMapper;
        this.idGen = idGen;
    }''',
              '''        this.houseMapper = houseMapper;
        this.idGen = idGen;
        this.publicityService = publicityService;
    }''', 1)

# 4) sign() 加公示硬校验
old_sign = '''    public AllocationVO sign(Long id) {
        BizAllocation a = requireAllocation(id);
        transitionAllocation(a, AllocationStatus.SIGNED);'''
new_sign = '''    public AllocationVO sign(Long id) {
        BizAllocation a = requireAllocation(id);

        // ⭐ 合规硬校验（决策 D23）：配租结果必须完成公示（≥7 个自然日并已结束公示）才能签约
        BizBatch batch = batchMapper.selectById(a.getBatchId());
        Long checkOrgId = batch == null ? null : batch.getOrgId();
        if (!publicityService.hasCompletedAllocationPublicity(checkOrgId, LocalDate.now())) {
            throw BizException.stateConflict(
                    "配租结果尚未完成公示，不能签约。"
                            + "请先在「公示」中发布配租公示（不少于 7 个自然日）并结束公示后，再办理签约。"
                            + "（组织 orgId=" + checkOrgId + "）");
        }

        transitionAllocation(a, AllocationStatus.SIGNED);'''
assert old_sign in s, 'sign 锚点缺失'
s = s.replace(old_sign, new_sign, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ 签约已强制校验配租公示')
