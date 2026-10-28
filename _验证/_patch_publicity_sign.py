# -*- coding: utf-8 -*-
"""公示组织/签约状态、签约校验、房源组织列支撑。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---- VO 增加组织与配租状态 ----
p = os.path.join(BE, 'biz', 'dto', 'PublicityWinnerVO.java')
s = io.open(p, encoding='utf-8').read()
if 'orgName' not in s:
    s = s.replace('''        String resultType,
        String resultTypeLabel
) {''', '''        String resultType,
        String resultTypeLabel,
        /** 组织名称（公示列表/中签房源前展示） */
        String orgName,
        /** 配租单状态：PENDING_SIGN 待签约 / SIGNED 已签约 / 空 无配租单 */
        String allocationStatus,
        String allocationStatusLabel
) {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('WinnerVO 已加组织/签约状态')

# ---- winners 填充 ----
p = os.path.join(BE, 'biz', 'service', 'impl', 'PublicityServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'allocationStatus' not in s:
    s = s.replace('''    private com.yundao.bp.biz.mapper.BizBatchHouseMapper rHouseMapper;''',
                  '''    private com.yundao.bp.biz.mapper.BizBatchHouseMapper rHouseMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;''', 1)
    s = s.replace('''            String typeLabel = "WON".equals(type) ? "中签"
                    : ("WAITLIST".equals(type) ? "递补" : "未中签");''',
                  '''            String typeLabel = "WON".equals(type) ? "中签"
                    : ("WAITLIST".equals(type) ? "未中签" : "未中签");
            String orgName = null;
            String allocStatus = null;
            if (jdbc != null) {
                try {
                    if (house != null && house.getOrgId() != null) {
                        java.util.List<String> names = jdbc.queryForList(
                                "select org_name from bp_iam_org where id = ?",
                                String.class, house.getOrgId());
                        orgName = names.isEmpty() ? null : names.get(0);
                    }
                    if (r.getPersonId() != null && houseId != null) {
                        java.util.List<String> st = jdbc.queryForList(
                                "select allocation_status from bp_biz_allocation "
                                        + "where person_id = ? and house_id = ? "
                                        + "order by id desc limit 1",
                                String.class, r.getPersonId(), houseId);
                        allocStatus = st.isEmpty() ? null : st.get(0);
                    }
                } catch (Exception ignore) {
                    // 展示字段，失败不影响公示
                }
            }
            String allocLabel = "SIGNED".equals(allocStatus) ? "已签约"
                    : ("PENDING_SIGN".equals(allocStatus) ? "待签约" : null);''', 1)
    s = s.replace('''                    type,
                    typeLabel));''', '''                    type,
                    typeLabel,
                    orgName,
                    allocStatus,
                    allocLabel));''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('winners 已补组织/签约状态')

# ---- 签约前校验：按批次公示天数 ----
p = os.path.join(BE, 'biz', 'service', 'impl', 'AllocationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'publicityDaysForBatch' not in s:
    s = s.replace('''        if (!publicityService.hasCompletedAllocationPublicity(checkOrgId, LocalDate.now())) {''',
                  '''        if (!publicityDaysForBatch(a.getBatchId(), checkOrgId)) {''', 1)
    s = s.replace('''    @Override
    @Transactional(rollbackFor = Exception.class)
    public AllocationVO giveUp(Long id, String reason) {''', '''    /**
     * 签约前公示校验：优先看本批次公示（天数达到系统参数 minDays 且已结束），
     * 没有批次公示时回退到组织级校验。
     */
    private boolean publicityDaysForBatch(Long batchId, Long orgId) {
        if (publicityMapper != null && batchId != null) {
            com.yundao.bp.biz.entity.BizPublicity pb = publicityMapper.selectOne(
                    new LambdaQueryWrapper<com.yundao.bp.biz.entity.BizPublicity>()
                            .eq(com.yundao.bp.biz.entity.BizPublicity::getBatchId, batchId)
                            .eq(com.yundao.bp.biz.entity.BizPublicity::getPublicityType, "ALLOCATION")
                            .orderByDesc(com.yundao.bp.biz.entity.BizPublicity::getId)
                            .last("LIMIT 1"));
            if (pb != null) {
                int minDays = 7;
                if (configService != null) {
                    minDays = configService.getInt("biz.publicity.allocation.minDays", 7);
                }
                long days = java.time.temporal.ChronoUnit.DAYS.between(
                        pb.getStartDate(), pb.getEndDate()) + 1;
                return days >= minDays && pb.getEndDate().isBefore(LocalDate.now());
            }
        }
        return publicityService.hasCompletedAllocationPublicity(orgId, LocalDate.now());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AllocationVO giveUp(Long id, String reason) {''', 1)
    print('签约公示校验已按批次')

# ---- 合同创建：防止同一人重复在租 ----
p = os.path.join(BE, 'biz', 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if '已有在签/在租合同' not in s:
    s = s.replace('''        long id = idGen.nextId();''', '''        Long activeContracts = mapper.selectCount(
                new LambdaQueryWrapper<BizContract>()
                        .eq(BizContract::getPersonId, cmd.personId())
                        .in(BizContract::getContractStatus,
                                "SIGNING", "EFFECTIVE", "RENEWING"));
        if (activeContracts != null && activeContracts > 0) {
            throw BizException.stateConflict("该承租人已有在签/在租合同，不能重复签约");
        }

        long id = idGen.nextId();''', 1)
    print('合同重复签约拦截已加')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
