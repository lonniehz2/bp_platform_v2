# -*- coding: utf-8 -*-
"""抄表组织过滤、欠费处置组织与摘要、抄表记录 org。"""
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


# 1) 抄表组织过滤：按房源组织（历史人工录入 org_id 为空）
p = os.path.join(BE, 'fin', 'service', 'impl', 'MeterReadingServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
s = s.replace('''                .eq(orgId != null, FinMeterReading::getOrgId, orgId)''',
              '''                .apply(orgId != null, "house_id in (select id from bp_asset_house "
                        + "where org_id = {0})", orgId)''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('  ✔ 抄表组织过滤')

# 2) 人工录入补 org
s = io.open(p, encoding='utf-8').read()
if 'setOrgId(house == null' not in s:
    s = s.replace('''        e.setOrgId(null);''', '''        java.util.List<Long> orgIds = houseMapper == null || cmd.houseId() == null
                ? java.util.List.of()
                : java.util.List.of(); // 组织在下方按房源补
        e.setOrgId(null);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)

# 3) 欠费处置：org 字段
patch(os.path.join(BE, 'fin', 'dto', 'ArrearsActionCreateCmd.java'), [
    ('''        Integer overdueDays,''',
     '''        Integer overdueDays,

        /** 组织（为空时按合同补） */
        Long orgId,''', 'cmd org'),
])

p = os.path.join(BE, 'fin', 'service', 'impl', 'ArrearsActionServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'setOrgId(cmd.orgId())' not in s:
    s = s.replace('''        e.setContractId(cmd.contractId());
        e.setPersonId(cmd.personId());''', '''        e.setContractId(cmd.contractId());
        e.setPersonId(cmd.personId());
        e.setOrgId(cmd.orgId());''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 欠费处置 org')

# 4) 摘要接口
p = os.path.join(BE, 'fin', 'controller', 'ArrearsActionController.java')
s = io.open(p, encoding='utf-8').read()
if 'summary' not in s:
    s = s.replace('''    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:create")''', '''    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;

    /** 按合同或人员汇总欠费金额与最长逾期天数（新建处置自动带出）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @GetMapping("/summary")
    public R<java.util.Map<String, Object>> summary(
            @RequestParam(required = false) Long contractId,
            @RequestParam(required = false) Long personId) {
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        if (jdbc == null || (contractId == null && personId == null)) {
            return R.ok(out);
        }
        String where = contractId != null ? "contract_id = ?" : "person_id = ?";
        Long key = contractId != null ? contractId : personId;
        java.util.List<java.util.Map<String, Object>> rows = jdbc.queryForList(
                "select coalesce(sum(payable_amount),0) as amount, "
                        + "coalesce(max(datediff(curdate(), due_date)),0) as days, "
                        + "count(*) as bills, max(contract_id) as contract_id, "
                        + "max(person_id) as person_id, max(org_id) as org_id "
                        + "from bp_fin_bill where " + where + " and is_deleted = 0 "
                        + "and status in ('UNPAID','PARTIAL','OVERDUE')", key);
        if (!rows.isEmpty()) {
            out.putAll(rows.get(0));
        }
        return R.ok(out);
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:create")''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 欠费摘要接口')
