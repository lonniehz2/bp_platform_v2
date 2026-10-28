# -*- coding: utf-8 -*-
"""退租：字段补全/验房状态/结算预览/办结释放（严格校验替换）。"""
import io
import os


def patch(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(path, 'w', encoding='utf-8', newline='').write(s)


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- VO ----------
patch(os.path.join(BE, 'biz', 'dto', 'TerminationVO.java'), [
    ('''        Boolean overdueExit,
        LocalDateTime createTime
) {''', '''        Boolean overdueExit,
        LocalDateTime createTime,
        Long orgId,
        String orgName,
        String houseName,
        String lesseeName,
        LocalDate leaseStart,
        LocalDate leaseEnd,
        java.math.BigDecimal monthlyRent,
        java.math.BigDecimal depositAmount,
        String inspectStatusLabel
) {''', 'VO 字段'),
    ('''                e.getCreateTime());''', '''                e.getCreateTime(), null, null, null, null, null, null, null, null, null);''',
     'VO from 构造'),
])

# ---------- Service ----------
p = os.path.join(BE, 'biz', 'service', 'impl', 'TerminationServiceImpl.java')
patch(p, [
    ('''    private final BizTerminationMapper mapper;
    private final SnowflakeIdGenerator idGen;''',
     '''    private final BizTerminationMapper mapper;
    private final SnowflakeIdGenerator idGen;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;''', '注入 jdbc'),

    ('''    // ==================== 内部 ====================''',
     '''    /** 列表/详情补组织、房源、承租人、租期、月租、押金、验房结果中文。 */
    private TerminationVO enrich(TerminationVO v) {
        if (v == null || jdbc == null) {
            return v;
        }
        Long orgId = null;
        String orgName = null;
        String houseName = null;
        String lesseeName = null;
        java.time.LocalDate leaseStart = null;
        java.time.LocalDate leaseEnd = null;
        java.math.BigDecimal rent = null;
        java.math.BigDecimal deposit = null;
        try {
            java.util.List<java.util.Map<String, Object>> rows = jdbc.queryForList(
                    "select c.org_id, c.lessee_name, c.lease_start, c.lease_end, c.monthly_rent, "
                            + "c.deposit_amount, h.house_name, o.org_name "
                            + "from bp_biz_contract c "
                            + "left join bp_asset_house h on h.id = c.house_id "
                            + "left join bp_iam_org o on o.id = c.org_id where c.id = ?",
                    v.contractId());
            if (!rows.isEmpty()) {
                java.util.Map<String, Object> r = rows.get(0);
                orgId = r.get("org_id") instanceof Number n ? n.longValue() : null;
                orgName = (String) r.get("org_name");
                houseName = (String) r.get("house_name");
                lesseeName = (String) r.get("lessee_name");
                leaseStart = toDate(r.get("lease_start"));
                leaseEnd = toDate(r.get("lease_end"));
                rent = toDecimal(r.get("monthly_rent"));
                deposit = toDecimal(r.get("deposit_amount"));
            }
        } catch (Exception ignore) {
            // 展示字段失败不影响主流程
        }
        String inspectLabel = switch (String.valueOf(v.inspectStatus())) {
            case "PENDING" -> "待查验";
            case "PASS", "PASSED" -> "合格";
            case "REPAIR", "ABNORMAL" -> "需维修";
            case "DAMAGED" -> "有损坏";
            default -> v.inspectStatus();
        };
        return new TerminationVO(v.id(), v.terminationNo(), v.contractId(), v.houseId(),
                v.personId(), v.terminationType(), v.applyTime(), v.planExitDate(),
                v.actualExitDate(), v.exitReason(), v.inspectStatus(), v.inspectResult(),
                v.damageAmount(), v.settleAmount(), v.depositRefund(), v.arrearsAmount(),
                v.settleStatus(), v.settleStatusLabel(), v.terminationStatus(),
                v.terminationStatusLabel(), v.houseReleased(), v.grantRevoked(),
                v.transitionStartDate(), v.transitionEndDate(), v.transitionMonths(),
                v.transitionRentMultiplier(), v.relocationStartDate(), v.relocationEndDate(),
                v.enforceFlag(), v.enforceCourt(), v.itemHandlerName(), v.notaryFlag(),
                v.notaryNo(), v.banReapplyEndDate(), v.readyToComplete(), v.overdueExit(),
                v.createTime(), orgId, orgName, houseName, lesseeName, leaseStart, leaseEnd,
                rent, deposit, inspectLabel);
    }

    private static java.time.LocalDate toDate(Object o) {
        if (o == null) {
            return null;
        }
        if (o instanceof java.sql.Date d) {
            return d.toLocalDate();
        }
        if (o instanceof java.time.LocalDate d) {
            return d;
        }
        try {
            return java.time.LocalDate.parse(String.valueOf(o).substring(0, 10));
        } catch (Exception e) {
            return null;
        }
    }

    private static java.math.BigDecimal toDecimal(Object o) {
        if (o == null) {
            return null;
        }
        return o instanceof java.math.BigDecimal b ? b
                : new java.math.BigDecimal(String.valueOf(o));
    }

    @Override
    public java.util.Map<String, Object> settlePreview(Long id) {
        return settlePreview(require(id));
    }

    /** 结算预览：押金（合同）、欠费（未缴账单）、损坏（验房）、应退合计。 */
    public java.util.Map<String, Object> settlePreview(BizTermination e) {
        java.math.BigDecimal deposit = java.math.BigDecimal.ZERO;
        java.math.BigDecimal arrears = java.math.BigDecimal.ZERO;
        if (jdbc != null) {
            try {
                java.util.List<java.math.BigDecimal> d = jdbc.queryForList(
                        "select deposit_amount from bp_biz_contract where id = ?",
                        java.math.BigDecimal.class, e.getContractId());
                if (!d.isEmpty() && d.get(0) != null) {
                    deposit = d.get(0);
                }
                java.util.List<java.math.BigDecimal> a = jdbc.queryForList(
                        "select coalesce(sum(bill_amount - paid_amount - waived_amount),0) "
                                + "from bp_fin_bill where house_id = ? and status in "
                                + "('UNPAID','PARTIAL','OVERDUE') and is_deleted = 0",
                        java.math.BigDecimal.class, e.getHouseId());
                if (!a.isEmpty() && a.get(0) != null) {
                    arrears = a.get(0);
                }
            } catch (Exception ignore) {
            }
        }
        java.math.BigDecimal damage = nz(e.getDamageAmount());
        java.math.BigDecimal total = deposit.subtract(arrears).subtract(damage)
                .setScale(2, java.math.RoundingMode.HALF_UP);
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("depositAmount", deposit);
        out.put("arrearsAmount", arrears);
        out.put("damageAmount", damage);
        out.put("totalAmount", total);
        out.put("formula", "应退合计 = 押金 − 欠费 − 损坏赔偿");
        return out;
    }

    // ==================== 内部 ====================''', 'enrich + 预览'),

    ('''        if (!List.of("PENDING", "PASSED", "ABNORMAL").contains(inspectStatus)) {''',
     '''        if (!List.of("PENDING", "PASS", "PASSED", "REPAIR", "ABNORMAL", "DAMAGED")
                .contains(inspectStatus)) {''', '验房状态放宽'),

    ('''        if (!TerminationStatus.APPROVED.name().equals(e.getTerminationStatus())) {
            throw BizException.stateConflict("仅在已批准状态可结算");
        }
        BigDecimal refund = nz(depositRefund);
        BigDecimal arrears = nz(arrearsAmount);''',
     '''        if (!TerminationStatus.APPROVED.name().equals(e.getTerminationStatus())) {
            throw BizException.stateConflict("仅在已批准状态可结算");
        }
        if (e.getInspectStatus() == null || "PENDING".equals(e.getInspectStatus())) {
            throw BizException.stateConflict("尚未完成退租查验，不能结算");
        }
        java.util.Map<String, Object> auto = settlePreview(e);
        BigDecimal refund = depositRefund == null
                ? (java.math.BigDecimal) auto.get("depositAmount") : depositRefund;
        BigDecimal arrears = arrearsAmount == null
                ? (java.math.BigDecimal) auto.get("arrearsAmount") : arrearsAmount;''',
     '结算前置与自动取值'),

    ('''        TerminationVO cur = TerminationVO.from(e);
        // 四个前置校验
        if (!"PASSED".equals(e.getInspectStatus())) {
            throw BizException.stateConflict("验房未通过，不能办结");
        }
        if (!SettleStatus.SETTLED.name().equals(e.getSettleStatus())
                && !SettleStatus.WAIVED.name().equals(e.getSettleStatus())) {
            throw BizException.stateConflict("结算未完成，不能办结");
        }
        if (cur.houseReleased() == null || !cur.houseReleased()) {
            throw BizException.stateConflict("房源未释放回可配池，不能办结");
        }
        if (cur.grantRevoked() == null || !cur.grantRevoked()) {
            throw BizException.stateConflict("授权未回收，不能办结");
        }
        transition(e, TerminationStatus.COMPLETED);''',
     '''        // 办结前置：必须已结算
        if (!SettleStatus.SETTLED.name().equals(e.getSettleStatus())
                && !SettleStatus.WAIVED.name().equals(e.getSettleStatus())) {
            throw BizException.stateConflict("结算未完成，不能办结");
        }
        if (e.getInspectStatus() == null || "PENDING".equals(e.getInspectStatus())) {
            throw BizException.stateConflict("尚未完成退租查验，不能办结");
        }
        // 办结自动腾退：终止合同、释放房源、清占用
        e.setHouseReleased(1);
        e.setGrantRevoked(1);
        if (jdbc != null) {
            try {
                jdbc.update("update bp_biz_contract set contract_status='TERMINATED', "
                        + "terminate_time=now(), terminate_reason='退租办结自动终止' "
                        + "where id = ? and contract_status in ('EFFECTIVE','RENEWING','SIGNING')",
                        e.getContractId());
                jdbc.update("update bp_asset_house set house_status='VACANT' where id = ?",
                        e.getHouseId());
                jdbc.update("delete from bp_asset_occupancy where contract_id = ?",
                        e.getContractId());
            } catch (Exception ex) {
                log.warn("退租办结自动释放失败（{}）：{}", e.getTerminationNo(), ex.getMessage());
            }
        }
        transition(e, TerminationStatus.COMPLETED);''', '办结自动释放'),
])
