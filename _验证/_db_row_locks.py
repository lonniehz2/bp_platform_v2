# -*- coding: utf-8 -*-
"""多实例并发准备：在 JVM 锁之外增加数据库行锁（SELECT ... FOR UPDATE）。

保留 JVM 分片锁作为同实例快速路径；跨实例时由数据库行锁兜底：
  · 合同签约   → 锁 bp_asset_house 行
  · 账单核销   → 锁 bp_fin_bill 行
  · 退租申请   → 锁 bp_biz_contract 行
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- 1) 三个 Mapper 加行锁方法 ----------
MAPPERS = [
    ('asset/mapper/AssetHouseMapper.java', 'AssetHouse',
     'bp_asset_house', 'AssetHouseMapper'),
    ('fin/mapper/FinBillMapper.java', 'FinBill', 'bp_fin_bill', 'FinBillMapper'),
    ('biz/mapper/BizContractMapper.java', 'BizContract', 'bp_biz_contract', 'BizContractMapper'),
]

for rel, entity, table, name in MAPPERS:
    p = os.path.join(J, *rel.split('/'))
    if not os.path.exists(p):
        print('%s 不存在，跳过' % rel)
        continue
    s = io.open(p, encoding='utf-8').read()
    if 'lockForUpdate' in s:
        print('%s 已含 lockForUpdate' % name)
        continue
    method = '''
    /**
     * 行级排他锁：返回主键即代表当前事务已持有该行锁。
     *
     * <p>用于跨实例并发保护（JVM 锁只在单实例有效）。必须在事务内调用。
     */
    @org.apache.ibatis.annotations.Select("select id from %s where id = #{id} for update")
    Long lockForUpdate(@org.apache.ibatis.annotations.Param("id") Long id);
''' % table
    i = s.rstrip().rfind('}')
    s = s[:i] + method + s[i:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s：已加 lockForUpdate' % name)

# ---------- 2) 三处调用 ----------
# 2.1 合同签约：在 doSign 校验前锁房源
P = os.path.join(J, 'biz', 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(P, encoding='utf-8').read()
if 'houseRowLock' not in s:
    s = s.replace('''    private ContractVO doSign(Long id, String signFileUrl, String signFlowId) {
        BizContract e = require(id);''',
                  '''    private ContractVO doSign(Long id, String signFileUrl, String signFlowId) {
        BizContract e = require(id);
        // 数据库行锁：跨实例并发时保证同一房源串行（JVM 锁只覆盖本实例）
        if (e.getHouseId() != null) {
            Long houseRowLock = houseMapper == null ? null
                    : houseMapper.lockForUpdate(e.getHouseId());
            if (houseRowLock == null) {
                throw com.yundao.bp.common.exception.BizException.notFound("房源");
            }
        }''', 1)
    # 注入房源 mapper（若无）
    if 'private com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper' not in s:
        inject = '''
    /** 房源（签约前加行锁，跨实例并发保护） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper;
'''
        j = s.find('    public ContractServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('ContractServiceImpl：签约已加房源行锁')

# 2.2 账单核销：doAllocate 开头锁账单行
B = os.path.join(J, 'fin', 'service', 'impl', 'BillingServiceImpl.java')
s = io.open(B, encoding='utf-8').read()
if 'billRowLock' not in s:
    s = s.replace('''    private BillVO doAllocate(Long paymentId, Long billId, BigDecimal amount) {''',
                  '''    private BillVO doAllocate(Long paymentId, Long billId, BigDecimal amount) {
        // 数据库行锁：跨实例并发核销保护
        Long billRowLock = billMapper == null ? null : billMapper.lockForUpdate(billId);
        if (billRowLock == null) {
            throw BizException.notFound("账单");
        }''', 1)
    io.open(B, 'w', encoding='utf-8', newline='').write(s)
    print('BillingServiceImpl：核销已加账单行锁')

# 2.3 退租申请：doApply 开头锁合同行
T = os.path.join(J, 'biz', 'service', 'impl', 'TerminationServiceImpl.java')
s = io.open(T, encoding='utf-8').read()
if 'contractRowLock' not in s:
    s = s.replace('''    private TerminationVO doApply(TerminationCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();''',
                  '''    private TerminationVO doApply(TerminationCreateCmd cmd) {
        // 数据库行锁：跨实例并发申请保护
        Long contractRowLock = contractMapper == null ? null
                : contractMapper.lockForUpdate(cmd.contractId());
        if (contractRowLock == null) {
            throw BizException.notFound("合同");
        }
        String tenantId = TenantContext.tenantId();''', 1)
    if 'private com.yundao.bp.biz.mapper.BizContractMapper contractMapper' not in s:
        inject = '''
    /** 合同（退租申请前加行锁） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizContractMapper contractMapper;
'''
        j = s.find('    public TerminationServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]
    io.open(T, 'w', encoding='utf-8', newline='').write(s)
    print('TerminationServiceImpl：退租已加合同行锁')

print('完成')
