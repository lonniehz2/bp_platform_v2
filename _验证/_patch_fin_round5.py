# -*- coding: utf-8 -*-
"""账务/抄表：余额、抄表筛选与批量出账、设备搜索、房源关键字、规则组织筛选。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return s


# 1) 资金流水：余额 = 之前流水 + 本次
patch(os.path.join(BE, 'fin', 'service', 'impl', 'CashFlowServiceImpl.java'), [
    ('''        e.setBalanceAfter(balanceAfter(now));''',
     '''        e.setBalanceAfter(balanceAfter(now).add(signed)
                .setScale(2, RoundingMode.HALF_UP));''', '流水余额'),

# 2) 抄表分页：组织 + 出账状态
    ('''    public PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId,
                                            Long feeItemId) {
        LambdaQueryWrapper<FinMeterReading> qw = new LambdaQueryWrapper<FinMeterReading>()
                .eq(houseId != null, FinMeterReading::getHouseId, houseId)
                .eq(feeItemId != null, FinMeterReading::getFeeItemId, feeItemId)
                .orderByDesc(FinMeterReading::getReadDate);''',
     '''    public PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId,
                                            Long feeItemId) {
        return page(pageNum, pageSize, houseId, feeItemId, null, null);
    }

    @Override
    public PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId,
                                            Long feeItemId, Long orgId, Boolean billed) {
        LambdaQueryWrapper<FinMeterReading> qw = new LambdaQueryWrapper<FinMeterReading>()
                .eq(houseId != null, FinMeterReading::getHouseId, houseId)
                .eq(feeItemId != null, FinMeterReading::getFeeItemId, feeItemId)
                .eq(orgId != null, FinMeterReading::getOrgId, orgId)
                .eq(billed != null, FinMeterReading::getBillStatus,
                        billed == null ? null : (billed ? "BILLED" : "UNBILLED"))
                .orderByDesc(FinMeterReading::getReadDate);''', '抄表分页筛选'),
])

# 3) 房源关键字：105房间 -> 105室
p = os.path.join(BE, 'asset', 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'roomKeyword' not in s:
    s = s.replace('''        if (keyword != null && !keyword.isBlank()) {''', '''        if (keyword != null && !keyword.isBlank()) {
            // 「105房间」这类口语输入转换为「105室」，与房源名称匹配
            String roomKeyword = keyword.trim().replace("房间", "室");''', 1)
    # 在关键字条件里加 roomKeyword like（若原条件存在则追加 or）
    s = s.replace('''                    .and(w -> w.like(AssetHouse::getHouseCode, keyword)
                            .or().like(AssetHouse::getHouseName, keyword))''',
                  '''                    .and(w -> w.like(AssetHouse::getHouseCode, keyword)
                            .or().like(AssetHouse::getHouseName, keyword)
                            .or().like(AssetHouse::getHouseName, roomKeyword))''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('房源关键字已兼容「房间」')
