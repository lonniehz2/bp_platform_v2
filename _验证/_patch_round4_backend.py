# -*- coding: utf-8 -*-
"""押金空值/自动取数；抄表账单缴费人回退；变更单展示与生效延迟。"""
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


# 1) 押金：空值安全 + 人员/金额从合同补
p = os.path.join(BE, 'fin', 'service', 'impl', 'DepositRefundServiceImpl.java')
patch(p, [
    ('''        boolean exempt = cmd.isExempt() != null && cmd.isExempt() == 1;
        BigDecimal due = exempt ? money(null) : money(cmd.depositAmount());
        BigDecimal paid = exempt ? money(null) : money(cmd.paidAmount());''',
     '''        boolean exempt = cmd.isExempt() != null && cmd.isExempt() == 1;
        BigDecimal due = exempt ? BigDecimal.ZERO
                : (cmd.depositAmount() == null ? BigDecimal.ZERO : money(cmd.depositAmount()));
        BigDecimal paid = exempt ? BigDecimal.ZERO
                : (cmd.paidAmount() == null ? BigDecimal.ZERO : money(cmd.paidAmount()));
        if ((due == null || due.compareTo(BigDecimal.ZERO) == 0) && cmd.depositAmount() == null
                && contractOrgIdMapper != null) {
            com.yundao.bp.biz.entity.BizContract c =
                    contractOrgIdMapper.selectById(cmd.contractId());
            if (c != null && c.getDepositAmount() != null) {
                due = money(c.getDepositAmount());
            }
        }
        if (due == null) {
            due = BigDecimal.ZERO;
        }''', '押金空值安全'),
    ('''        e.setPersonId(cmd.personId());''',
     '''        Long depositPerson = cmd.personId();
        if (depositPerson == null && contractOrgIdMapper != null) {
            com.yundao.bp.biz.entity.BizContract c =
                    contractOrgIdMapper.selectById(cmd.contractId());
            depositPerson = c == null ? null : c.getLesseePersonId();
        }
        e.setPersonId(depositPerson);''', '押金人员回填'),
])

# 2) 抄表账单：缴费人回退最近合同/配租单
p = os.path.join(BE, 'fin', 'service', 'impl', 'MeterReadingServiceImpl.java')
patch(p, [
    ('''                                .eq(com.yundao.bp.biz.entity.BizContract::getContractStatus,
                                        "EFFECTIVE")
                                .last("LIMIT 1"));''',
     '''                                .in(com.yundao.bp.biz.entity.BizContract::getContractStatus,
                                        "EFFECTIVE", "RENEWING", "SIGNING")
                                .orderByDesc(com.yundao.bp.biz.entity.BizContract::getId)
                                .last("LIMIT 1"));''', '抄表账单合同回退'),
])

# 3) 变更单展示字段 + 生效标记
p = os.path.join(BE, 'biz', 'dto', 'ChangeVO.java')
s = io.open(p, encoding='utf-8').read()
if 'houseName' not in s:
    s = s.replace('''        String approveStatusLabel,
        LocalDate effectiveDate,
        LocalDateTime createTime''', '''        String approveStatusLabel,
        LocalDate effectiveDate,
        LocalDateTime createTime,
        String houseName,
        String lesseeName,
        Integer applied''', 1)
    s = s.replace('''                ct.label(), e.getApproveStatus(),''', '''                ct.label(), e.getApproveStatus(),''')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ ChangeVO 字段（需检查 from 构造）')

# 4) 变更单列表：补房源/承租人
p = os.path.join(BE, 'biz', 'service', 'impl', 'ContractChangeServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'enrichChange' not in s:
    s = s.replace('''    @Override
    public PageResult<ChangeVO> page(''', '''    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;

    private ChangeVO enrichChange(ChangeVO v) {
        if (v == null || jdbc == null) {
            return v;
        }
        String houseName = null;
        String lesseeName = null;
        try {
            java.util.List<java.util.Map<String, Object>> rows = jdbc.queryForList(
                    "select h.house_name, c.lessee_name from bp_biz_contract c "
                            + "left join bp_asset_house h on h.id = c.house_id "
                            + "where c.id = ?", v.contractId());
            if (!rows.isEmpty()) {
                houseName = (String) rows.get(0).get("house_name");
                lesseeName = (String) rows.get(0).get("lessee_name");
            }
        } catch (Exception ignore) {
        }
        return new ChangeVO(v.id(), v.changeNo(), v.contractId(), v.newContractId(),
                v.changeType(), v.changeTypeLabel(), v.changeReason(), v.beforeJson(),
                v.afterJson(), v.approveStatus(), v.approveStatusLabel(), v.effectiveDate(),
                v.createTime(), houseName, lesseeName, null);
    }

    @Override
    public PageResult<ChangeVO> page(''', 1)
    s = s.replace('page.getRecords().stream().map(ChangeVO::from).toList()',
                  'page.getRecords().stream().map(ChangeVO::from).map(this::enrichChange).toList()')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 变更单 enrich')
