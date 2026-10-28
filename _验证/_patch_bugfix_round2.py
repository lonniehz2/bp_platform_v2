# -*- coding: utf-8 -*-
"""批次人数/总分/自动公示/删除校验/黑名单提示/日房态合同占用/续签开始日。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ============ 1) 批次参与人数：摇号后按结果数统计 ============
p = os.path.join(BE, 'biz', 'service', 'impl', 'AllocationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

old = '''        Long n = waitingMapper.selectCount(new LambdaQueryWrapper<BizWaitingQueue>()
                .eq(BizWaitingQueue::getQueueStatus, QueueStatus.WAITING.name())
                .eq(b.getSecurityType() != null, BizWaitingQueue::getSecurityType, b.getSecurityType())
                .eq(b.getOrgId() != null, BizWaitingQueue::getOrgId, b.getOrgId()));
        int cnt = n == null ? 0 : n.intValue();'''
new = '''        int cnt;
        BatchStatus bs = batchStatusOf(b);
        if (bs == BatchStatus.LOTTERY_DONE || bs == BatchStatus.SELECTING
                || bs == BatchStatus.ALLOCATED || bs == BatchStatus.CLOSED) {
            // 已摇号：参与人数 = 中签 + 未中签（含递补），来自本次摇号结果
            Long n = lotteryMapper.selectCount(new LambdaQueryWrapper<BizLotteryResult>()
                    .eq(BizLotteryResult::getBatchId, b.getId()));
            cnt = n == null ? 0 : n.intValue();
        } else {
            Long n = waitingMapper.selectCount(new LambdaQueryWrapper<BizWaitingQueue>()
                    .eq(BizWaitingQueue::getQueueStatus, QueueStatus.WAITING.name())
                    .eq(b.getSecurityType() != null, BizWaitingQueue::getSecurityType,
                            b.getSecurityType())
                    .eq(b.getOrgId() != null, BizWaitingQueue::getOrgId, b.getOrgId()));
            cnt = n == null ? 0 : n.intValue();
        }'''
if '已摇号：参与人数' not in s:
    s = s.replace(old, new, 1)
    print('参与人数统计已修')

# ============ 2) 结果页总分：VO 增加分数并回填 ============
pvo = os.path.join(BE, 'biz', 'dto', 'LotteryResultVO.java')
v = io.open(pvo, encoding='utf-8').read()
if 'totalScore' not in v:
    v = v.replace('''        String personName,
        String phoneMask
) {''', '''        String personName,
        String phoneMask,
        /** 优先附加分 */
        java.math.BigDecimal priorityScore,
        /** 轮候天数 */
        Integer waitDays,
        /** 总分 = 附加分 + 轮候天数 × 0.1 */
        java.math.BigDecimal totalScore
) {''', 1)
    # from() 末尾补三个 null
    v = v.replace('''                e.getPersonName(), e.getPhoneMask());''',
                  '''                e.getPersonName(), e.getPhoneMask(), null, null, null);''', 1)
    io.open(pvo, 'w', encoding='utf-8', newline='').write(v)
    print('LotteryResultVO 已加分数')

if 'withScores' not in s:
    s = s.replace('''    @Override
    public List<LotteryResultVO> listLotteryResults(Long batchId) {''', '''    /** 结果页补「附加分/轮候天数/总分」，来源是该次摇号对应的轮候记录。 */
    private LotteryResultVO withScores(LotteryResultVO r) {
        if (r == null) {
            return null;
        }
        BigDecimal priority = BigDecimal.ZERO;
        int waitDays = 0;
        if (r.waitingId() != null) {
            BizWaitingQueue w = waitingMapper.selectById(r.waitingId());
            if (w != null) {
                priority = w.getPriorityScore() == null ? BigDecimal.ZERO : w.getPriorityScore();
                waitDays = w.getWaitDays() == null ? 0 : w.getWaitDays();
            }
        }
        BigDecimal total = priority.add(BigDecimal.valueOf(waitDays)
                .multiply(new BigDecimal("0.1"))).setScale(2, java.math.RoundingMode.HALF_UP);
        return new LotteryResultVO(r.id(), r.batchId(), r.personId(), r.applicationId(),
                r.waitingId(), r.resultType(), r.resultTypeLabel(), r.lotterySeq(),
                r.selectSeq(), r.houseId(), r.spaceId(), r.selectTime(), r.resultStatus(),
                r.giveUpReason(), r.personName(), r.phoneMask(), priority, waitDays, total);
    }

    @Override
    public List<LotteryResultVO> listLotteryResults(Long batchId) {''', 1)
    s = s.replace('''                .stream().map(LotteryResultVO::from)''',
                  '''                .stream().map(LotteryResultVO::from).map(this::withScores)''', 1)
    print('结果页已回填总分')

# ============ 3) 摇号后自动生成配租公示 ============
if 'autoCreatePublicity' not in s:
    s = s.replace('''        out.sort(Comparator.comparing(LotteryResultVO::selectSeq,
                Comparator.nullsLast(Comparator.naturalOrder())));
        return out;''', '''        out.sort(Comparator.comparing(LotteryResultVO::selectSeq,
                Comparator.nullsLast(Comparator.naturalOrder())));
        try {
            autoCreatePublicity(b);
        } catch (Exception e) {
            log.warn("摇号后自动生成公示失败（批次 {}）：{}", b.getBatchNo(), e.getMessage());
        }
        return out;''', 1)
    s = s.replace('''    /** 结果页补「附加分/轮候天数/总分」''', '''    /**
     * 摇号完成自动生成配租公示（草稿），公示期默认满足系统参数 minDays。
     *
     * <p>已存在同批次公示则不重复生成。
     */
    private void autoCreatePublicity(BizBatch b) {
        if (publicityMapper == null) {
            return;
        }
        Long exists = publicityMapper.selectCount(
                new LambdaQueryWrapper<com.yundao.bp.biz.entity.BizPublicity>()
                        .eq(com.yundao.bp.biz.entity.BizPublicity::getBatchId, b.getId())
                        .eq(com.yundao.bp.biz.entity.BizPublicity::getPublicityType, "ALLOCATION"));
        if (exists != null && exists > 0) {
            return;
        }
        int minDays = 7;
        if (configService != null) {
            minDays = configService.getInt("biz.publicity.allocation.minDays", 7);
        }
        java.time.LocalDate start = java.time.LocalDate.now();
        java.time.LocalDate end = start.plusDays(Math.max(1, minDays) - 1);
        long id = idGen.nextId();
        com.yundao.bp.biz.entity.BizPublicity pb = new com.yundao.bp.biz.entity.BizPublicity();
        pb.setId(id);
        pb.setTenantId(TenantContext.tenantId());
        pb.setPublicityNo("PB" + id);
        pb.setPublicityType("ALLOCATION");
        pb.setOrgId(b.getOrgId());
        pb.setBatchId(b.getId());
        pb.setTitle(b.getBatchName() + "配租中签公示");
        pb.setContent("批次 " + b.getBatchNo() + " 摇号完成，中签名单见公示明细。");
        pb.setStartDate(start);
        pb.setEndDate(end);
        pb.setPublicityStatus("DRAFT");
        pb.setCreateTime(LocalDateTime.now());
        pb.setUpdateTime(LocalDateTime.now());
        publicityMapper.insert(pb);
        log.info("摇号后已自动生成公示 {}（{}~{}）", pb.getPublicityNo(), start, end);
    }

    /** 结果页补「附加分/轮候天数/总分」''', 1)
    # 注入依赖
    s = s.replace('''    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonGuaranteeProfileMapper guaranteeProfileMapper;''',
                  '''    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonGuaranteeProfileMapper guaranteeProfileMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizPublicityMapper publicityMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.sys.service.ConfigService configService;''', 1)
    print('自动公示已加')

# 黑名单/注销人员禁止入队
if '黑名单或已注销' not in s:
    s = s.replace('''            if (gp != null && "EXITED".equals(gp.getProfileStatus())) {
                throw BizException.stateConflict("该人员已退出保障，不能进入轮候队列");
            }''', '''            if (gp != null && "EXITED".equals(gp.getProfileStatus())) {
                throw BizException.stateConflict("该人员已退出保障，不能进入轮候队列");
            }
            com.yundao.bp.person.entity.Person person = personMapper.selectById(cmd.personId());
            if (person != null) {
                String ps = person.getPersonStatus();
                if ("BLACKLIST".equals(ps)) {
                    throw BizException.stateConflict("该人员为黑名单人员（限制申请期），不能进入轮候队列");
                }
                if ("CANCELLED".equals(ps) || "CANCELED".equals(ps) || "LOGOUT".equals(ps)) {
                    throw BizException.stateConflict("该人员已注销，不能进入轮候队列");
                }
            }''', 1)
    print('入队黑名单/注销拦截已加')

io.open(p, 'w', encoding='utf-8', newline='').write(s)

# ============ 2b) 递补文案改为未中签 ============
p = os.path.join(BE, 'biz', 'constant', 'LotteryResultType.java')
s = io.open(p, encoding='utf-8').read()
s = s.replace('WAITLIST("递补")', 'WAITLIST("未中签")')
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('递补文案已改未中签')

# ============ 8) 人员删除：实名核验后不允许 ============
p = os.path.join(BE, 'person', 'service', 'impl', 'PersonServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if '实名核验' not in s:
    s = s.replace('''        if ("BLACKLIST".equals(p.getPersonStatus())) {
            throw BizException.stateConflict("黑名单人员不允许删除，请先解除黑名单");
        }''', '''        if ("BLACKLIST".equals(p.getPersonStatus())) {
            throw BizException.stateConflict("黑名单人员不允许删除，请先解除黑名单");
        }
        if (p.getVerifyStatus() != null && !"NONE".equals(p.getVerifyStatus())
                && !"UNVERIFIED".equals(p.getVerifyStatus())
                && !"FAILED".equals(p.getVerifyStatus())) {
            throw BizException.stateConflict("该人员已完成实名核验，不允许删除；如确需删除请先走注销流程");
        }''', 1)
    print('人员删除校验已加')

# ============ 9) 申请创建：黑名单/注销提示 ============
p = os.path.join(BE, 'biz', 'service', 'impl', 'ApplicationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if '黑名单人员不能申请' not in s:
    s = s.replace('''        // 已退出保障的人员不能再申请''', '''        // 黑名单 / 注销人员
        com.yundao.bp.person.entity.Person applicant = personMapper.selectById(cmd.personId());
        if (applicant != null) {
            String ps = applicant.getPersonStatus();
            if ("BLACKLIST".equals(ps)) {
                throw BizException.stateConflict("该人员为黑名单人员（限制申请期），不能新建申请");
            }
            if ("CANCELLED".equals(ps) || "CANCELED".equals(ps) || "LOGOUT".equals(ps)) {
                throw BizException.stateConflict("该人员已注销，不能新建申请");
            }
        }

        // 已退出保障的人员不能再申请''', 1)
    print('申请黑名单/注销拦截已加')

# ============ 13) 续签保留原开始日 ============
p = os.path.join(BE, 'biz', 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'e.setLeaseStart(e.getLeaseEnd());' in s:
    s = s.replace('''        transition(e, ContractStatus.RENEWING);
        e.setLeaseStart(e.getLeaseEnd());
        e.setLeaseEnd(newLeaseEnd);''', '''        transition(e, ContractStatus.RENEWING);
        // 续签只延长结束日，开始日保持原合同起始日
        e.setLeaseEnd(newLeaseEnd);''', 1)
    print('续签开始日已保留')

# ============ 11) 日房态：合同区间显示已出租 ============
p = os.path.join(BE, 'asset', 'constant', 'DayStatus.java')
s = io.open(p, encoding='utf-8').read()
if 'LEASED' not in s:
    s = s.replace('''    OCCUPIED("已入住"),''', '''    OCCUPIED("已入住"),
    LEASED("已出租"),
    VACANT("空置"),''', 1)
    s = s.replace('''    public boolean occupied() {
        return this == BOOKED || this == OCCUPIED;
    }''', '''    public boolean occupied() {
        return this == BOOKED || this == OCCUPIED || this == LEASED;
    }''', 1)
    s = s.replace('''            case AVAILABLE -> Set.of(BOOKED, OCCUPIED, CLOSED, MAINTENANCE);''',
                  '''            case AVAILABLE -> Set.of(BOOKED, OCCUPIED, LEASED, CLOSED, MAINTENANCE);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('DayStatus 已加已出租/空置')
