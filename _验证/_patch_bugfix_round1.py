# -*- coding: utf-8 -*-
"""修复：配置重复新增、轮候加分修改、批次房源重复入池、中签状态、参与人数、重复申请。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- 1) 系统参数：优先改已有全局行，避免新增重复 ----------
p = os.path.join(BE, 'sys', 'service', 'impl', 'ConfigServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
old = '''        SysConfig c = mapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                .eq(SysConfig::getTenantId, tenant)
                .eq(SysConfig::getConfigKey, key)
                .last("LIMIT 1"));
        LocalDateTime now = LocalDateTime.now();'''
new = '''        SysConfig c = mapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                .eq(SysConfig::getTenantId, tenant)
                .eq(SysConfig::getConfigKey, key)
                .last("LIMIT 1"));
        if (c == null) {
            // 兼容历史：先有全局默认行（tenant_id 为空），再改时就更新它，不再插一条
            c = mapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                    .and(w -> w.isNull(SysConfig::getTenantId)
                            .or().eq(SysConfig::getTenantId, ""))
                    .eq(SysConfig::getConfigKey, key)
                    .last("LIMIT 1"));
        }
        LocalDateTime now = LocalDateTime.now();'''
if new not in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('配置 set 已修复')

# ---------- 2) 轮候：重复入队改为更新附加分 ----------
p = os.path.join(BE, 'biz', 'service', 'impl', 'AllocationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
old = '''        // 同一申请单不可重复入轮候
        Long dup = waitingMapper.selectCount(new LambdaQueryWrapper<BizWaitingQueue>()
                .eq(BizWaitingQueue::getApplicationId, cmd.applicationId()));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("该申请单已在轮候库中");
        }'''
new = '''        // 同一申请单重复提交：视为「调整附加分」，更新原记录而不是报错
        if (cmd.applicationId() != null) {
            BizWaitingQueue exist = waitingMapper.selectOne(
                    new LambdaQueryWrapper<BizWaitingQueue>()
                            .eq(BizWaitingQueue::getApplicationId, cmd.applicationId())
                            .last("LIMIT 1"));
            if (exist != null) {
                if (!QueueStatus.WAITING.name().equals(exist.getQueueStatus())
                        && !QueueStatus.WON.name().equals(exist.getQueueStatus())) {
                    throw BizException.stateConflict(
                            "该申请单当前状态为「" + exist.getQueueStatus() + "」，不能调整");
                }
                BigDecimal p2 = cmd.priorityScore() == null
                        ? exist.getPriorityScore() : cmd.priorityScore();
                exist.setPriorityScore(p2.setScale(2, RoundingMode.HALF_UP));
                exist.setTotalScore(p2.setScale(2, RoundingMode.HALF_UP)
                        .add(BigDecimal.valueOf(exist.getWaitDays() == null ? 0 : exist.getWaitDays())
                                .multiply(new BigDecimal("0.1"))));
                if (cmd.validUntil() != null) {
                    exist.setValidUntil(cmd.validUntil());
                }
                exist.setUpdateTime(LocalDateTime.now());
                waitingMapper.updateById(exist);
                recalcRank(exist.getSecurityType(), exist.getOrgId());
                return WaitingVO.from(exist);
            }
        }'''
if '视为「调整附加分」' not in s:
    s = s.replace(old, new, 1)
    print('轮候加分调整已支持')

# ---------- 3) 批次加房源：跨批次重复入池校验 ----------
old = '''            Long dup = batchHouseMapper.selectCount(new LambdaQueryWrapper<BizBatchHouse>()
                    .eq(BizBatchHouse::getBatchId, batchId)
                    .eq(BizBatchHouse::getHouseId, hid));
            if (dup != null && dup > 0) {
                continue;
            }'''
new = '''            Long dup = batchHouseMapper.selectCount(new LambdaQueryWrapper<BizBatchHouse>()
                    .eq(BizBatchHouse::getBatchId, batchId)
                    .eq(BizBatchHouse::getHouseId, hid));
            if (dup != null && dup > 0) {
                continue;
            }
            // 同一房源不能同时在另一个未结束批次里
            List<BizBatchHouse> others = batchHouseMapper.selectList(
                    new LambdaQueryWrapper<BizBatchHouse>()
                            .eq(BizBatchHouse::getHouseId, hid)
                            .ne(BizBatchHouse::getBatchId, batchId));
            for (BizBatchHouse oh : others) {
                BizBatch ob = batchMapper.selectById(oh.getBatchId());
                if (ob == null) {
                    continue;
                }
                BatchStatus obs = batchStatusOf(ob);
                if (!obs.isTerminal()) {
                    throw BizException.stateConflict("房源「" + (h.getHouseName() == null
                            ? h.getHouseCode() : h.getHouseName())
                            + "」已在批次 " + ob.getBatchNo() + "（" + obs.label() + "）中，不能重复入池");
                }
            }'''
if '不能重复入池' not in s:
    s = s.replace(old, new, 1)
    print('重复入池校验已加')

# ---------- 4) 摇号后中签人员置 WON ----------
old = '''        // 落库种子与公证信息
        b.setLotterySeed(seed);'''
new = '''        // 中签人员移出「轮候中」，状态置「已中签」
        for (BizLotteryResult r : lotteryMapper.selectList(
                new LambdaQueryWrapper<BizLotteryResult>()
                        .eq(BizLotteryResult::getBatchId, batchId)
                        .eq(BizLotteryResult::getResultType, LotteryResultType.WON.name()))) {
            if (r.getWaitingId() != null) {
                BizWaitingQueue wq = waitingMapper.selectById(r.getWaitingId());
                if (wq != null) {
                    wq.setQueueStatus(QueueStatus.WON.name());
                    wq.setUpdateTime(now);
                    waitingMapper.updateById(wq);
                }
            }
        }

        // 落库种子与公证信息
        b.setLotterySeed(seed);'''
if '中签人员移出' not in s:
    s = s.replace(old, new, 1)
    print('中签状态已联动')

# ---------- 5) 参与人数按轮候池实时统计 ----------
old = '''        IPage<BizBatch> page = batchMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<BatchVO> rows = page.getRecords().stream().map(BatchVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);'''
new = '''        IPage<BizBatch> page = batchMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<BatchVO> rows = page.getRecords().stream().map(this::withLiveCount).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);'''
if 'withLiveCount' not in s:
    s = s.replace(old, new, 1)
    s = s.replace('''    @Override
    public BatchVO getBatch(Long id) {
        return BatchVO.from(requireBatch(id));
    }''', '''    @Override
    public BatchVO getBatch(Long id) {
        return withLiveCount(requireBatch(id));
    }

    /** 参与人数取「同组织 + 同保障类型 + 轮候中」的实时人数，避免入队后显示不更新。 */
    private BatchVO withLiveCount(BizBatch b) {
        BatchVO vo = BatchVO.from(b);
        if (vo == null) {
            return null;
        }
        Long n = waitingMapper.selectCount(new LambdaQueryWrapper<BizWaitingQueue>()
                .eq(BizWaitingQueue::getQueueStatus, QueueStatus.WAITING.name())
                .eq(b.getSecurityType() != null, BizWaitingQueue::getSecurityType, b.getSecurityType())
                .eq(b.getOrgId() != null, BizWaitingQueue::getOrgId, b.getOrgId()));
        int cnt = n == null ? 0 : n.intValue();
        return new BatchVO(vo.id(), vo.batchNo(), vo.batchName(), vo.orgId(), vo.securityType(),
                vo.batchType(), vo.houseCount(), cnt, vo.signupStart(), vo.signupEnd(),
                vo.lotteryTime(), vo.selectStart(), vo.selectEnd(), vo.lotterySeed(),
                vo.notaryInfo(), vo.batchStatus(), vo.batchStatusLabel(), vo.remark(),
                vo.createTime());
    }''', 1)
    print('参与人数实时统计已加')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
else:
    io.open(p, 'w', encoding='utf-8', newline='').write(s)

# ---------- 6) 申请：同组织不允许重复在途申请 ----------
p = os.path.join(BE, 'biz', 'service', 'impl', 'ApplicationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
old = '''        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizApplication e = new BizApplication();'''
new = '''        // 同一人员在同一组织只能有一张在途申请（草稿/受理/审核/补件）
        Long active = mapper.selectCount(new LambdaQueryWrapper<BizApplication>()
                .eq(BizApplication::getPersonId, cmd.personId())
                .eq(cmd.orgId() != null, BizApplication::getOrgId, cmd.orgId())
                .in(BizApplication::getApplicationStatus,
                        "DRAFT", "SUBMITTED", "ACCEPTED", "REVIEWING", "SUPPLEMENT"));
        if (active != null && active > 0) {
            throw BizException.stateConflict(
                    "该人员在本组织已有在途申请，请先在「申请受理」中处理，或撤回后再新建");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizApplication e = new BizApplication();'''
if '已有在途申请' not in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('重复申请校验已加')
