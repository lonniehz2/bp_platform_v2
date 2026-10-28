# -*- coding: utf-8 -*-
"""退出保障：清轮候、禁入队/申请；资格判定加校验与说明。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- A. GuaranteeProfileServiceImpl：退出清轮候 + 资格判定校验 ----------
p = os.path.join(BE, 'person', 'service', 'impl', 'GuaranteeProfileServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if 'waitingQueueMapper' not in s:
    s = s.replace('''    public GuaranteeProfileServiceImpl(PersonGuaranteeProfileMapper mapper,
                                       SnowflakeIdGenerator idGen,
                                       com.yundao.bp.person.mapper.PersonMapper personMapper) {
        this.mapper = mapper;
        this.idGen = idGen;
        this.personMapper = personMapper;
    }''', '''    private final com.yundao.bp.biz.mapper.BizWaitingQueueMapper waitingQueueMapper;

    public GuaranteeProfileServiceImpl(PersonGuaranteeProfileMapper mapper,
                                       SnowflakeIdGenerator idGen,
                                       com.yundao.bp.person.mapper.PersonMapper personMapper,
                                       com.yundao.bp.biz.mapper.BizWaitingQueueMapper waitingQueueMapper) {
        this.mapper = mapper;
        this.idGen = idGen;
        this.personMapper = personMapper;
        this.waitingQueueMapper = waitingQueueMapper;
    }''', 1)
    print('档案服务已注入轮候 Mapper')

if '退出轮候' not in s:
    s = s.replace('''        e.setProfileStatus("EXITED");
        e.setExitDate(exitDate == null ? LocalDate.now() : exitDate);
        e.setExitReason(reason);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("保障档案已退出：人员 {}（{}）", personId, reason);
        return e;''', '''        e.setProfileStatus("EXITED");
        e.setExitDate(exitDate == null ? LocalDate.now() : exitDate);
        e.setExitReason(reason);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        // 退出保障即失效：把该人员仍在轮候/已中签的记录置为「已退出」，
        // 否则会出现“已退出保障却还在轮候池”的矛盾状态
        if (waitingQueueMapper != null) {
            java.util.List<com.yundao.bp.biz.entity.BizWaitingQueue> queues =
                    waitingQueueMapper.selectList(
                            new com.baomidou.mybatisplus.core.conditions.query
                                    .LambdaQueryWrapper<com.yundao.bp.biz.entity.BizWaitingQueue>()
                                    .eq(com.yundao.bp.biz.entity.BizWaitingQueue::getPersonId, personId)
                                    .in(com.yundao.bp.biz.entity.BizWaitingQueue::getQueueStatus,
                                            "WAITING", "WON", "FROZEN"));
            for (com.yundao.bp.biz.entity.BizWaitingQueue q : queues) {
                q.setQueueStatus("EXITED");
                q.setUpdateTime(LocalDateTime.now());
                waitingQueueMapper.updateById(q);
            }
            if (!queues.isEmpty()) {
                log.info("退出保障联动退出轮候：人员 {} 共 {} 条", personId, queues.size());
            }
        }
        log.info("保障档案已退出：人员 {}（{}）", personId, reason);
        return e;''', 1)
    print('退出保障已联动轮候')

if '不符合保障条件：' not in s:
    s = s.replace('''        int years = qualifyYears == null || qualifyYears <= 0 ? 1 : qualifyYears;
        LocalDate today = LocalDate.now();
        e.setProfileStatus("QUALIFIED");''', '''        // 资格判定：把档案事实变成硬性条件，逐条收集不通过原因
        java.util.List<String> issues = new java.util.ArrayList<>();
        if ("NORMAL".equals(e.getIncomeLevel())) {
            issues.add("家庭人均月收入超过中低收入线（档位：普通）");
        }
        int houses = e.getHouseCount() == null ? 0 : e.getHouseCount();
        if (houses > 0 && (e.getRemark() == null || e.getRemark().isBlank())) {
            issues.add("名下已有 " + houses + " 套住房，需在备注说明例外依据");
        }
        if (e.getTalentValidTo() != null
                && e.getTalentValidTo().isBefore(LocalDate.now())) {
            issues.add("人才认定已过期（有效期至 " + e.getTalentValidTo() + "）");
        }
        if (!issues.isEmpty()) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "资格判定不通过：" + String.join("；", issues));
        }

        int years = qualifyYears == null || qualifyYears <= 0 ? 1 : qualifyYears;
        LocalDate today = LocalDate.now();
        e.setProfileStatus("QUALIFIED");''', 1)
    print('资格判定已加校验')

io.open(p, 'w', encoding='utf-8', newline='').write(s)

# ---------- B. AllocationServiceImpl：退出保障人员禁止入队 ----------
p = os.path.join(BE, 'biz', 'service', 'impl', 'AllocationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if '已退出保障，不能进入轮候' not in s:
    s = s.replace('''    @Override
    @Transactional(rollbackFor = Exception.class)
    public WaitingVO enterQueue(WaitingEnterCmd cmd) {''', '''    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonGuaranteeProfileMapper guaranteeProfileMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WaitingVO enterQueue(WaitingEnterCmd cmd) {
        if (guaranteeProfileMapper != null && cmd.personId() != null) {
            com.yundao.bp.person.entity.PersonGuaranteeProfile gp =
                    guaranteeProfileMapper.selectOne(
                            new LambdaQueryWrapper<com.yundao.bp.person.entity.PersonGuaranteeProfile>()
                                    .eq(com.yundao.bp.person.entity.PersonGuaranteeProfile::getPersonId,
                                            cmd.personId())
                                    .last("LIMIT 1"));
            if (gp != null && "EXITED".equals(gp.getProfileStatus())) {
                throw BizException.stateConflict("该人员已退出保障，不能进入轮候队列");
            }
        }''', 1)
    print('入队已拦截退出保障人员')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)

# ---------- C. ApplicationServiceImpl.create：退出保障人员禁止申请 ----------
p = os.path.join(BE, 'biz', 'service', 'impl', 'ApplicationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if '已退出保障，不能新增申请' not in s:
    s = s.replace('''        // 同一人员在同一组织只能有一张在途申请（草稿/受理/审核/补件）''', '''        // 已退出保障的人员不能再申请
        if (guaranteeProfileService != null) {
            try {
                com.yundao.bp.person.entity.PersonGuaranteeProfile gp =
                        guaranteeProfileService.getByPerson(cmd.personId());
                if (gp != null && "EXITED".equals(gp.getProfileStatus())) {
                    throw BizException.stateConflict("该人员已退出保障，不能新增申请");
                }
            } catch (BizException be) {
                if (be.getMessage() != null && be.getMessage().contains("已退出保障")) {
                    throw be;
                }
                // 无档案不在这里拦（审核阶段会校验）
            }
        }

        // 同一人员在同一组织只能有一张在途申请（草稿/受理/审核/补件）''', 1)
    print('申请创建已拦截退出保障人员')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
