# -*- coding: utf-8 -*-
"""合同/换房/退租：字段补全、筛选、验房状态、结算/办结、主动合同查询。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ================= 1. TerminationVO 增展示字段 =================
p = os.path.join(BE, 'biz', 'dto', 'TerminationVO.java')
s = io.open(p, encoding='utf-8').read()
if 'orgName' not in s:
    s = s.replace('''        Boolean overdueExit,
        LocalDateTime createTime''', '''        Boolean overdueExit,
        LocalDateTime createTime,
        /** 展示用：组织 */
        Long orgId,
        String orgName,
        /** 展示用：房源、承租人、租期、月租、押金 */
        String houseName,
        String lesseeName,
        LocalDate leaseStart,
        LocalDate leaseEnd,
        java.math.BigDecimal monthlyRent,
        java.math.BigDecimal depositAmount,
        String inspectStatusLabel''', 1)
    # from() 末尾补 null
    s = s.replace('''                e.getCreateTime());''', '''                e.getCreateTime(), null, null, null, null, null, null, null, null, null);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('TerminationVO 已加展示字段')

# ================= 2. 服务：充实字段、筛选、验房、结算、办结 =================
p = os.path.join(BE, 'biz', 'service', 'impl', 'TerminationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if 'jdbc' not in s:
    s = s.replace('''    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;''',
                  '''    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;''', 1)
    print('退租服务已注入 JdbcTemplate')

if 'private TerminationVO enrich' not in s:
    s = s.replace('''    // ==================== 内部 ====================''',
                  '''    /** 列表/详情补组织、房源、承租人、租期、月租、押金与验房状态中文。 */
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
                            + "left join bp_iam_org o on o.id = c.org_id "
                            + "where c.id = ?", v.contractId());
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
            // 展示字段，失败不影响主流程
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
        return o instanceof java.math.BigDecimal b ? b : new java.math.BigDecimal(String.valueOf(o));
    }

    // ==================== 内部 ====================''', 1)
    print('退租 enrich 已加')

# 返回处套 enrich
s = s.replace('return TerminationVO.from(e);', 'return enrich(TerminationVO.from(e));')
s = s.replace('rows = page.getRecords().stream().map(TerminationVO::from).toList();',
              'rows = page.getRecords().stream().map(TerminationVO::from).map(this::enrich).toList();')
s = s.replace('List<TerminationVO> rows = page.getRecords().stream().map(TerminationVO::from).toList();',
              'List<TerminationVO> rows = page.getRecords().stream().map(TerminationVO::from).map(this::enrich).toList();')

# 分页支持 orgId + 关键字（人员姓名）
s = s.replace('''    public PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                          Long contractId, Long houseId, String keyword) {''',
              '''    public PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                          Long contractId, Long houseId, String keyword,
                                          Long orgId) {''', 1)
s = s.replace('''        if (keyword != null && !keyword.isBlank()) {
            qw.like(BizTermination::getTerminationNo, keyword);
        }''', '''        if (orgId != null) {
            qw.apply("contract_id in (select id from bp_biz_contract where org_id = {0})", orgId);
        }
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(BizTermination::getTerminationNo, keyword)
                    .or().apply("person_id in (select id from bp_person where person_name like concat('%', {0}, '%'))",
                            keyword));
        }''', 1)

# 验房状态放宽
s = s.replace('''        if (!List.of("PENDING", "PASSED", "ABNORMAL").contains(inspectStatus)) {''',
              '''        if (!List.of("PENDING", "PASS", "PASSED", "REPAIR", "ABNORMAL", "DAMAGED")
                .contains(inspectStatus)) {''', 1)

# 结算：已查验才能结算 + 自动取押金/欠费
s = s.replace('''        if (!TerminationStatus.APPROVED.name().equals(e.getTerminationStatus())) {
            throw BizException.stateConflict("仅在已批准状态可结算");
        }
        BigDecimal refund = nz(depositRefund);''', '''        if (!TerminationStatus.APPROVED.name().equals(e.getTerminationStatus())) {
            throw BizException.stateConflict("仅在已批准状态可结算");
        }
        if (e.getInspectStatus() == null || "PENDING".equals(e.getInspectStatus())) {
            throw BizException.stateConflict("尚未完成退租查验，不能结算");
        }
        java.util.Map<String, Object> auto = settlePreview(e);
        BigDecimal refund = depositRefund == null
                ? (java.math.BigDecimal) auto.get("depositAmount") : depositRefund;''', 1)
s = s.replace('''        BigDecimal arrears = nz(arrearsAmount);''',
              '''        BigDecimal arrears = arrearsAmount == null
                ? (java.math.BigDecimal) auto.get("arrearsAmount") : arrearsAmount;''', 1)

# 办结：仅需已结算，自动释放房源与终止合同
s = s.replace('''        TerminationVO cur = TerminationVO.from(e);
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
        transition(e, TerminationStatus.COMPLETED);''', '''        // 办结前置：必须已结算
        if (!SettleStatus.SETTLED.name().equals(e.getSettleStatus())
                && !SettleStatus.WAIVED.name().equals(e.getSettleStatus())) {
            throw BizException.stateConflict("结算未完成，不能办结");
        }
        // 自动强制腾退 + 释放房源（不再要求人工点“释放房源/强制腾退”）
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
                log.warn("退租办结自动释放失败（退租单 {}）：{}", e.getTerminationNo(), ex.getMessage());
            }
        }
        transition(e, TerminationStatus.COMPLETED);''', 1)

# settle preview 方法
if 'settlePreview' not in s:
    s = s.replace('''    private TerminationVO enrich(TerminationVO v) {''',
                  '''    /** 结算预览：押金（合同）、欠费（未缴账单）、损坏赔偿（验房）、合计。 */
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

    private TerminationVO enrich(TerminationVO v) {''', 1)
    print('结算预览已加')

io.open(p, 'w', encoding='utf-8', newline='').write(s)

# ================= 3. 控制器：orgId + settle-preview =================
p = os.path.join(BE, 'biz', 'controller', 'TerminationController.java')
s = io.open(p, encoding='utf-8').read()
if 'settle-preview' not in s:
    s = s.replace('''                                             @RequestParam(required = false) String keyword) {
        return R.ok(service.page(pageNum, pageSize, type, status, contractId, houseId, keyword));''',
                  '''                                             @RequestParam(required = false) String keyword,
                                             @RequestParam(required = false) Long orgId) {
        return R.ok(service.page(pageNum, pageSize, type, status, contractId, houseId, keyword, orgId));''', 1)
    s = s.replace('''    @com.yundao.bp.iam.security.RequirePerm("biz:termination:submit")''',
                  '''    @com.yundao.bp.iam.security.RequirePerm("biz:termination:view")
    @org.springframework.web.bind.annotation.GetMapping("/{id}/settle-preview")
    public R<java.util.Map<String, Object>> settlePreview(@PathVariable Long id) {
        return R.ok(service.settlePreview(service.requireForPreview(id)));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:submit")''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('退租控制器已加预览')

# ================= 4. 合同的当前有效合同（按人员） =================
p = os.path.join(BE, 'biz', 'controller', 'ContractController.java')
s = io.open(p, encoding='utf-8').read()
if 'active-by-person' not in s:
    s = s.replace('''    @GetMapping("/{id}")''', '''    /** 人员当前有效合同（换房/退租表单自动带出）。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:contract:view")
    @GetMapping("/active-by-person/{personId}")
    public R<ContractVO> activeByPerson(@PathVariable Long personId) {
        return R.ok(contractService.activeByPerson(personId));
    }

    @GetMapping("/{id}")''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('按人员取合同接口已加')

# ================= 5. 换房分页：关键字/组织 =================
p = os.path.join(BE, 'biz', 'service', 'impl', 'ExchangeServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'orgId' not in s:
    s = s.replace('''    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status) {''',
                  '''    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status) {
        return page(pageNum, pageSize, personId, oldContractId, status, null, null);
    }

    @Override
    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status,
                                       String keyword, Long orgId) {''', 1)
    s = s.replace('''        applyDataScope(qw, BizExchange::getPersonId, BizExchange::getPersonId, false);''',
                  '''        if (orgId != null) {
            qw.apply("person_id in (select id from bp_person where org_id = {0})", orgId);
        }
        if (keyword != null && !keyword.isBlank()) {
            qw.apply("person_id in (select id from bp_person where person_name like concat('%', {0}, '%'))",
                    keyword);
        }
        applyDataScope(qw, BizExchange::getPersonId, BizExchange::getPersonId, false);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('换房分页筛选已加')
