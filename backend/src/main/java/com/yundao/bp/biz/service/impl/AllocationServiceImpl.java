package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.person.entity.Person;
import com.yundao.bp.person.mapper.PersonMapper;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.constant.AllocationStatus;
import com.yundao.bp.biz.constant.BatchStatus;
import com.yundao.bp.biz.constant.LotteryResultType;
import com.yundao.bp.biz.constant.QueueStatus;
import com.yundao.bp.biz.dto.AllocateCmd;
import com.yundao.bp.biz.dto.AllocationVO;
import com.yundao.bp.biz.dto.BatchCreateCmd;
import com.yundao.bp.biz.dto.BatchVO;
import com.yundao.bp.biz.dto.LotteryResultVO;
import com.yundao.bp.biz.dto.LotteryRunCmd;
import com.yundao.bp.biz.dto.WaitingEnterCmd;
import com.yundao.bp.biz.dto.WaitingVO;
import com.yundao.bp.biz.entity.BizAllocation;
import com.yundao.bp.biz.entity.BizBatch;
import com.yundao.bp.biz.entity.BizBatchHouse;
import com.yundao.bp.biz.entity.BizLotteryResult;
import com.yundao.bp.biz.entity.BizWaitingQueue;
import com.yundao.bp.biz.mapper.BizAllocationMapper;
import com.yundao.bp.biz.mapper.BizBatchHouseMapper;
import com.yundao.bp.biz.mapper.BizBatchMapper;
import com.yundao.bp.biz.mapper.BizLotteryResultMapper;
import com.yundao.bp.biz.mapper.BizWaitingQueueMapper;
import com.yundao.bp.biz.service.AllocationService;
import com.yundao.bp.biz.service.PublicityService;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 配租实现。
 *
 * <p><b>轮候打分（决策 D20）</b>：{@code 总分 = 优先分 + 轮候天数 × 0.1}。
 * 优先分由业务按政策核定（低保/残疾/优抚/见义勇为等），轮候时长体现"先来先得"，
 * 权重 0.1 保证"长期轮候"能逐步追上小幅优先分，避免优先分一票否决。
 *
 * <p><b>摇号（决策 D21）</b>：按总分降序、同分按入队时间升序排定顺序；
 * 仅当分数与入队时间都相同时用<b>种子伪随机</b>打散，种子落库可复现、可公证。
 * 中签数 = 批次房源数，其余为递补/未中签。
 *
 * <p><b>房源锁定（决策 D22）</b>：配租单生成即锁定房源，默认 72 小时未签约自动释放，
 * 防止"占房不签"长期占压房源。
 */
@Service
public class AllocationServiceImpl implements AllocationService {

    private static final Logger log = LoggerFactory.getLogger(AllocationServiceImpl.class);

    /** 每轮候一天折算的分数 */
    private static final BigDecimal DAY_WEIGHT = new BigDecimal("0.1");
    /** 默认锁定时长（小时） */
    private static final int DEFAULT_LOCK_HOURS = 72;

    private final BizWaitingQueueMapper waitingMapper;
    private final BizBatchMapper batchMapper;
    private final BizBatchHouseMapper batchHouseMapper;
    private final BizLotteryResultMapper lotteryMapper;
    private final BizAllocationMapper allocationMapper;
    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;
    private final PublicityService publicityService;
    private final PersonMapper personMapper;

    public AllocationServiceImpl(BizWaitingQueueMapper waitingMapper, BizBatchMapper batchMapper,
                                 BizBatchHouseMapper batchHouseMapper,
                                 BizLotteryResultMapper lotteryMapper,
                                 BizAllocationMapper allocationMapper,
                                 AssetHouseMapper houseMapper,
                                 SnowflakeIdGenerator idGen,
                                 PublicityService publicityService,
                                 PersonMapper personMapper) {
        this.waitingMapper = waitingMapper;
        this.batchMapper = batchMapper;
        this.batchHouseMapper = batchHouseMapper;
        this.lotteryMapper = lotteryMapper;
        this.allocationMapper = allocationMapper;
        this.houseMapper = houseMapper;
        this.idGen = idGen;
        this.publicityService = publicityService;
        this.personMapper = personMapper;
    }

    // ==================== 轮候 ====================

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonGuaranteeProfileMapper guaranteeProfileMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizPublicityMapper publicityMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.sys.service.ConfigService configService;

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
            com.yundao.bp.person.entity.Person person = personMapper.selectById(cmd.personId());
            if (person != null) {
                String ps = person.getPersonStatus();
                if ("BLACKLIST".equals(ps)) {
                    throw BizException.stateConflict("该人员为黑名单人员（限制申请期），不能进入轮候队列");
                }
                if ("CANCELLED".equals(ps) || "CANCELED".equals(ps) || "LOGOUT".equals(ps)) {
                    throw BizException.stateConflict("该人员已注销，不能进入轮候队列");
                }
            }
        }
        String tenantId = TenantContext.tenantId();
        // 同一申请单重复提交：视为「调整附加分」，更新原记录而不是报错
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
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BigDecimal priority = cmd.priorityScore() == null
                ? BigDecimal.ZERO : cmd.priorityScore();

        BizWaitingQueue e = new BizWaitingQueue();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setPersonId(cmd.personId());
        e.setApplicationId(cmd.applicationId());
        e.setSecurityType(cmd.securityType());
        e.setOrgId(cmd.orgId());
        e.setWaitingNo("WQ" + id);
        e.setPriorityScore(priority.setScale(2, RoundingMode.HALF_UP));
        e.setWaitDays(0);
        e.setTotalScore(priority.setScale(2, RoundingMode.HALF_UP));
        e.setEnterTime(now);
        e.setValidUntil(cmd.validUntil());
        e.setQueueStatus(QueueStatus.WAITING.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        waitingMapper.insert(e);

        // 入队后重算排名
        recalcRank(cmd.securityType(), cmd.orgId());
        BizWaitingQueue saved = waitingMapper.selectById(id);
        return WaitingVO.from(saved == null ? e : saved);
    }

    @Override
    public WaitingVO getWaiting(Long id) {
        return WaitingVO.from(requireWaiting(id));
    }

    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 轮候队列按人员维度限权：实体无 org 列，ORG 档不额外限制。 */
    private void applyWaitingScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                    <com.yundao.bp.biz.entity.BizWaitingQueue> qw) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            qw.eq(com.yundao.bp.biz.entity.BizWaitingQueue::getPersonId,
                    scope.personId() == null ? -1L : scope.personId());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(com.yundao.bp.biz.entity.BizWaitingQueue::getOrgId, scope.orgId());
        }
    }

    @Override
    public boolean isQueued(Long personId, String securityType) {
        if (personId == null || securityType == null) {
            return false;
        }
        Long n = waitingMapper.selectCount(new LambdaQueryWrapper<BizWaitingQueue>()
                .eq(BizWaitingQueue::getPersonId, personId)
                .eq(BizWaitingQueue::getSecurityType, securityType));
        return n != null && n > 0;
    }

    public PageResult<WaitingVO> pageWaiting(long pageNum, long pageSize, String securityType,
                                             Long orgId, String status, String keyword) {
        LambdaQueryWrapper<BizWaitingQueue> qw = new LambdaQueryWrapper<BizWaitingQueue>()
                .eq(securityType != null && !securityType.isBlank(),
                        BizWaitingQueue::getSecurityType, securityType)
                .eq(orgId != null, BizWaitingQueue::getOrgId, orgId)
                .eq(status != null && !status.isBlank(), BizWaitingQueue::getQueueStatus, status)
                .orderByAsc(BizWaitingQueue::getWaitingRank)
                .orderByAsc(BizWaitingQueue::getEnterTime);
        if (keyword != null && !keyword.isBlank()) {
            List<Long> pids = personMapper.selectList(new LambdaQueryWrapper<Person>()
                            .and(w -> w.like(Person::getPersonName, keyword)
                                    .or().like(Person::getPhone, keyword))
                            .last("LIMIT 500"))
                    .stream().map(Person::getId).toList();
            if (pids.isEmpty()) {
                return PageResult.of(0, pageNum, pageSize, List.of());
            }
            qw.in(BizWaitingQueue::getPersonId, pids);
        }
        applyWaitingScope(qw);
        IPage<BizWaitingQueue> page = waitingMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<WaitingVO> rows = page.getRecords().stream().map(WaitingVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int recalcRank(String securityType, Long orgId) {
        LambdaQueryWrapper<BizWaitingQueue> qw = new LambdaQueryWrapper<BizWaitingQueue>()
                .in(BizWaitingQueue::getQueueStatus, List.of(QueueStatus.WAITING.name(),
                        QueueStatus.WON.name(), QueueStatus.FROZEN.name()))
                .eq(securityType != null && !securityType.isBlank(),
                        BizWaitingQueue::getSecurityType, securityType)
                .eq(orgId != null, BizWaitingQueue::getOrgId, orgId);
        List<BizWaitingQueue> list = waitingMapper.selectList(qw);

        LocalDate today = LocalDate.now();
        LocalDateTime now = LocalDateTime.now();
        // 算分
        for (BizWaitingQueue w : list) {
            int days = w.getEnterTime() == null ? 0
                    : (int) ChronoUnit.DAYS.between(w.getEnterTime().toLocalDate(), today);
            w.setWaitDays(days);
            BigDecimal total = (w.getPriorityScore() == null ? BigDecimal.ZERO : w.getPriorityScore())
                    .add(DAY_WEIGHT.multiply(BigDecimal.valueOf(days)))
                    .setScale(2, RoundingMode.HALF_UP);
            w.setTotalScore(total);
        }
        // 排序：总分降序 + 入队时间升序
        list.sort(Comparator.comparing(BizWaitingQueue::getTotalScore).reversed()
                .thenComparing(BizWaitingQueue::getEnterTime,
                        Comparator.nullsLast(Comparator.naturalOrder())));
        int rank = 1;
        for (BizWaitingQueue w : list) {
            w.setWaitingRank(rank++);
            w.setUpdateTime(now);
            waitingMapper.updateById(w);
        }
        return list.size();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WaitingVO freezeWaiting(Long id, String reason) {
        BizWaitingQueue e = requireWaiting(id);
        QueueStatus from = queueStatusOf(e);
        if (!QueueStatus.nextOf(from).contains(QueueStatus.FROZEN)) {
            throw BizException.stateConflict("当前状态（" + from.label() + "）不可冻结");
        }
        e.setQueueStatus(QueueStatus.FROZEN.name());
        e.setFreezeReason(reason == null || reason.isBlank() ? "业务冻结" : reason);
        e.setUpdateTime(LocalDateTime.now());
        waitingMapper.updateById(e);
        return WaitingVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WaitingVO unfreezeWaiting(Long id) {
        BizWaitingQueue e = requireWaiting(id);
        if (queueStatusOf(e) != QueueStatus.FROZEN) {
            throw BizException.stateConflict("仅冻结状态可解冻");
        }
        e.setQueueStatus(QueueStatus.WAITING.name());
        e.setFreezeReason(null);
        e.setUpdateTime(LocalDateTime.now());
        waitingMapper.updateById(e);
        return WaitingVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WaitingVO exitWaiting(Long id, String reason) {
        BizWaitingQueue e = requireWaiting(id);
        QueueStatus from = queueStatusOf(e);
        if (from.isTerminal()) {
            throw BizException.stateConflict("轮候已" + from.label());
        }
        e.setQueueStatus(QueueStatus.EXITED.name());
        e.setFreezeReason(reason == null ? "主动退出轮候" : reason);
        e.setUpdateTime(LocalDateTime.now());
        waitingMapper.updateById(e);
        return WaitingVO.from(e);
    }

    // ==================== 批次 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BatchVO createBatch(BatchCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();

        BizBatch b = new BizBatch();
        b.setId(id);
        b.setTenantId(tenantId);
        b.setBatchNo("LB" + id);
        b.setBatchName(cmd.batchName());
        b.setOrgId(cmd.orgId());
        b.setSecurityType(cmd.securityType());
        b.setBatchType(cmd.batchType());
        b.setHouseCount(0);
        b.setApplicantCount(0);
        b.setSignupStart(cmd.signupStart());
        b.setSignupEnd(cmd.signupEnd());
        b.setLotteryTime(cmd.lotteryTime());
        b.setSelectStart(cmd.selectStart());
        b.setSelectEnd(cmd.selectEnd());
        b.setNotaryInfo(cmd.notaryInfo());
        b.setBatchStatus(BatchStatus.DRAFT.name());
        b.setRemark(cmd.remark());
        b.setIsDeleted(0);
        b.setCreateTime(now);
        b.setUpdateTime(now);
        batchMapper.insert(b);

        if (cmd.houseIds() != null && !cmd.houseIds().isEmpty()) {
            addHouses(id, cmd.houseIds());
        }
        BizBatch saved = batchMapper.selectById(id);
        return BatchVO.from(saved == null ? b : saved);
    }

    @Override
    public BatchVO getBatch(Long id) {
        return withLiveCount(requireBatch(id));
    }

    /** 参与人数取「同组织 + 同保障类型 + 轮候中」的实时人数，避免入队后显示不更新。 */
    private BatchVO withLiveCount(BizBatch b) {
        BatchVO vo = BatchVO.from(b);
        if (vo == null) {
            return null;
        }
        int cnt;
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
        }
        return new BatchVO(vo.id(), vo.batchNo(), vo.batchName(), vo.orgId(), vo.securityType(),
                vo.batchType(), vo.houseCount(), cnt, vo.signupStart(), vo.signupEnd(),
                vo.lotteryTime(), vo.selectStart(), vo.selectEnd(), vo.lotterySeed(),
                vo.notaryInfo(), vo.batchStatus(), vo.batchStatusLabel(), vo.remark(),
                vo.createTime());
    }

    @Override
    public PageResult<BatchVO> pageBatch(long pageNum, long pageSize, Long orgId, String status) {
        // scope:ignore 批次为组织级作业对象
        LambdaQueryWrapper<BizBatch> qw = new LambdaQueryWrapper<BizBatch>()
                .eq(orgId != null, BizBatch::getOrgId, orgId)
                .eq(status != null && !status.isBlank(), BizBatch::getBatchStatus, status)
                .orderByDesc(BizBatch::getId);
        IPage<BizBatch> page = batchMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<BatchVO> rows = page.getRecords().stream().map(this::withLiveCount).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int addHouses(Long batchId, List<Long> houseIds) {
        BizBatch b = requireBatch(batchId);
        BatchStatus bs = batchStatusOf(b);
        if (bs.isTerminal()) {
            throw BizException.stateConflict("批次已" + bs.label() + "，不可加房源");
        }
        String tenantId = TenantContext.tenantId();
        int added = 0;
        for (Long hid : houseIds) {
            AssetHouse h = houseMapper.selectById(hid);
            if (h == null) {
                continue;
            }
            Long dup = batchHouseMapper.selectCount(new LambdaQueryWrapper<BizBatchHouse>()
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
                // 已配租（ALLOCATED）属于历史，退房后可再次入池；只拦仍在报名/摇号/选房阶段的批次
                boolean activePool = obs == BatchStatus.DRAFT || obs == BatchStatus.PUBLISHED
                        || obs == BatchStatus.SIGNUP || obs == BatchStatus.LOTTERY
                        || obs == BatchStatus.LOTTERY_DONE || obs == BatchStatus.SELECTING;
                if (activePool) {
                    throw BizException.stateConflict("房源「" + (h.getHouseName() == null
                            ? h.getHouseCode() : h.getHouseName())
                            + "」已在批次 " + ob.getBatchNo() + "（" + obs.label() + "）中，不能重复入池");
                }
            }
            LocalDateTime now = LocalDateTime.now();
            BizBatchHouse bh = new BizBatchHouse();
            bh.setId(idGen.nextId());
            bh.setTenantId(tenantId);
            bh.setBatchId(batchId);
            bh.setHouseId(hid);
            bh.setSpaceId(h.getSpaceId());
            bh.setInPoolStatus("AVAILABLE");
            bh.setCreateTime(now);
            bh.setUpdateTime(now);
            batchHouseMapper.insert(bh);
            added++;
        }
        // 回填房源套数
        Long cnt = batchHouseMapper.selectCount(new LambdaQueryWrapper<BizBatchHouse>()
                .eq(BizBatchHouse::getBatchId, batchId));
        b.setHouseCount(cnt == null ? 0 : cnt.intValue());
        b.setUpdateTime(LocalDateTime.now());
        batchMapper.updateById(b);
        return added;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BatchVO transition(Long id, String targetStatus) {
        BizBatch b = requireBatch(id);
        BatchStatus from = batchStatusOf(b);
        BatchStatus target;
        try {
            target = BatchStatus.valueOf(targetStatus);
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("批次状态不合法: " + targetStatus);
        }
        if (from == target) {
            // 幂等：重复点击发布等场景直接返回当前状态，避免前端看到“状态变更失败”
            return BatchVO.from(b);
        }
        if (!BatchStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "批次状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        b.setBatchStatus(target.name());
        // 报名即轮候：进入报名/摇号阶段时，按同保障类型（同组织）统计参与人数
        if (target == BatchStatus.SIGNUP || target == BatchStatus.LOTTERY) {
            LambdaQueryWrapper<BizWaitingQueue> wq = new LambdaQueryWrapper<BizWaitingQueue>()
                    .eq(BizWaitingQueue::getSecurityType, b.getSecurityType())
                    .eq(BizWaitingQueue::getQueueStatus, QueueStatus.WAITING.name());
            if (b.getOrgId() != null) {
                wq.eq(BizWaitingQueue::getOrgId, b.getOrgId());
            }
            Long pool = waitingMapper.selectCount(wq);
            b.setApplicantCount(pool == null ? 0 : pool.intValue());
        }
        b.setUpdateTime(LocalDateTime.now());
        batchMapper.updateById(b);
        return BatchVO.from(b);
    }

    /**
     * 摇号完成后生成配租单：按中签顺序把批次房源池里的可用房源依次配给中签人。
     *
     * <p>每个中签人一张「待签约」配租单，房源在池内置为已选中；已有配租单的人员跳过。
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public java.util.Map<String, Object> generateAllocations(Long batchId) {
        BizBatch b = requireBatch(batchId);
        BatchStatus st = batchStatusOf(b);
        if (st != BatchStatus.LOTTERY_DONE && st != BatchStatus.ALLOCATED
                && st != BatchStatus.SELECTING) {
            throw BizException.stateConflict(
                    "批次当前为 " + st.label() + "，请先完成摇号再生成配租单");
        }
        List<BizLotteryResult> wins = lotteryMapper.selectList(
                new LambdaQueryWrapper<BizLotteryResult>()
                        .eq(BizLotteryResult::getBatchId, batchId)
                        .eq(BizLotteryResult::getResultType, LotteryResultType.WON.name())
                        .orderByAsc(BizLotteryResult::getSelectSeq)
                        .orderByAsc(BizLotteryResult::getLotterySeq));
        List<BizBatchHouse> pool = batchHouseMapper.selectList(
                new LambdaQueryWrapper<BizBatchHouse>()
                        .eq(BizBatchHouse::getBatchId, batchId)
                        .eq(BizBatchHouse::getInPoolStatus, "AVAILABLE")
                        .orderByAsc(BizBatchHouse::getId));
        int made = 0;
        int idx = 0;
        for (BizLotteryResult r : wins) {
            Long dup = allocationMapper.selectCount(new LambdaQueryWrapper<BizAllocation>()
                    .eq(BizAllocation::getBatchId, batchId)
                    .eq(BizAllocation::getPersonId, r.getPersonId()));
            if (dup != null && dup > 0) {
                continue;
            }
            if (idx >= pool.size()) {
                break;
            }
            BizBatchHouse house = pool.get(idx++);
            BizAllocation a = new BizAllocation();
            a.setId(idGen.nextId());
            a.setTenantId(TenantContext.tenantId());
            a.setAllocationNo("BA" + a.getId());
            a.setBatchId(batchId);
            a.setPersonId(r.getPersonId());
            a.setHouseId(house.getHouseId());
            a.setSpaceId(house.getSpaceId());
            a.setAllocationType("LOTTERY");
            a.setAllocationDate(LocalDate.now());
            a.setAllocationStatus(AllocationStatus.PENDING_SIGN.name());
            a.setLockExpireTime(LocalDateTime.now().plusHours(DEFAULT_LOCK_HOURS));
            a.setCreateTime(LocalDateTime.now());
            a.setUpdateTime(LocalDateTime.now());
            allocationMapper.insert(a);
            house.setInPoolStatus("SELECTED");
            house.setUpdateTime(LocalDateTime.now());
            batchHouseMapper.updateById(house);
            // 配租单生成即锁定房源，避免被其他批次重复配租
            AssetHouse asset = houseMapper.selectById(house.getHouseId());
            if (asset != null) {
                asset.setHouseStatus("LOCKED");
                asset.setUpdateTime(LocalDateTime.now());
                houseMapper.updateById(asset);
            }
            made++;
        }
        if (made > 0) {
            b.setUpdateTime(LocalDateTime.now());
            batchMapper.updateById(b);
        }
        Long existing = allocationMapper.selectCount(new LambdaQueryWrapper<BizAllocation>()
                .eq(BizAllocation::getBatchId, batchId));
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("generated", made);
        out.put("existing", existing == null ? 0 : existing.intValue());
        out.put("winners", wins.size());
        out.put("availableHouses", pool.size());
        boolean en = com.yundao.bp.common.i18n.LocaleContext.isEnglish();
        String msg;
        if (made > 0) {
            msg = en ? made + " allocations generated" : "本次生成 " + made + " 张配租单";
        } else if (existing != null && existing > 0) {
            msg = en ? "This batch already has " + existing + " allocations; no need to regenerate"
                    : "该批次已生成 " + existing + " 张配租单，无需重复生成";
        } else if (wins.isEmpty()) {
            msg = en ? "This batch has no lottery winners; run the lottery first"
                    : "该批次没有中签结果，请先完成摇号";
        } else {
            msg = en ? "No available housing (all selected or not added to the batch)"
                    : "没有可用房源（房源已全部选中或未加入批次）";
        }
        out.put("message", msg);
        log.info("批次 {} 生成配租单 {}（已有 {}，中签 {}，可用房源 {}）",
                b.getBatchNo(), made, out.get("existing"), wins.size(), pool.size());
        return out;
    }


    @Override
    public java.util.List<java.util.Map<String, Object>> listBatchHouseDetails(Long batchId) {
        java.util.List<BizBatchHouse> pool = batchHouseMapper.selectList(
                new LambdaQueryWrapper<BizBatchHouse>()
                        .eq(BizBatchHouse::getBatchId, batchId)
                        .orderByAsc(BizBatchHouse::getId));
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (BizBatchHouse bh : pool) {
            AssetHouse h = houseMapper.selectById(bh.getHouseId());
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("houseId", bh.getHouseId());
            m.put("inPoolStatus", bh.getInPoolStatus());
            m.put("houseCode", h == null ? null : h.getHouseCode());
            m.put("houseName", h == null ? null : h.getHouseName());
            m.put("houseStatus", h == null ? null : h.getHouseStatus());
            m.put("area", h == null ? null : h.getArea());
            out.add(m);
        }
        return out;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int removeHouses(Long batchId, java.util.List<Long> houseIds) {
        if (houseIds == null || houseIds.isEmpty()) {
            return 0;
        }
        BizBatch b = requireBatch(batchId);
        int removed = 0;
        for (Long hid : houseIds) {
            BizBatchHouse bh = batchHouseMapper.selectOne(
                    new LambdaQueryWrapper<BizBatchHouse>()
                            .eq(BizBatchHouse::getBatchId, batchId)
                            .eq(BizBatchHouse::getHouseId, hid)
                            .last("LIMIT 1"));
            if (bh == null) {
                continue;
            }
            if (!"AVAILABLE".equals(bh.getInPoolStatus())) {
                throw BizException.stateConflict(
                        "房源已参与摇号/配租，不能移除（状态：" + bh.getInPoolStatus() + "）");
            }
            batchHouseMapper.deleteById(bh.getId());
            removed++;
        }
        Long cnt = batchHouseMapper.selectCount(new LambdaQueryWrapper<BizBatchHouse>()
                .eq(BizBatchHouse::getBatchId, batchId));
        b.setHouseCount(cnt == null ? 0 : cnt.intValue());
        b.setUpdateTime(LocalDateTime.now());
        batchMapper.updateById(b);
        log.info("批次 {} 移除房源 {} 套，剩余 {}", b.getBatchNo(), removed, b.getHouseCount());
        return removed;
    }

    @Override
    public List<Long> listBatchHouses(Long batchId, String inPoolStatus) {
        return batchHouseMapper.selectList(new LambdaQueryWrapper<BizBatchHouse>()
                        .eq(BizBatchHouse::getBatchId, batchId)
                        .eq(inPoolStatus != null && !inPoolStatus.isBlank(),
                                BizBatchHouse::getInPoolStatus, inPoolStatus)
                        .orderByAsc(BizBatchHouse::getId))
                .stream().map(BizBatchHouse::getHouseId).toList();
    }

    // ==================== 摇号 ====================

    private static Long batchIdOf(Object v) {
        if (v == null) {
            return null;
        }
        if (v instanceof Number n) {
            return n.longValue();
        }
        if (v instanceof java.util.Map<?, ?> m) {
            Object id = m.containsKey("id") ? m.get("id") : m.get("batchId");
            return batchIdOf(id);
        }
        String s = String.valueOf(v).trim();
        try {
            return Long.valueOf(s);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public List<LotteryResultVO> runLottery(LotteryRunCmd cmd) {
        Long batchId = batchIdOf(cmd.batchId());
        BizBatch b = requireBatch(batchId);
        BatchStatus bs = batchStatusOf(b);
        if (!bs.canLottery()) {
            throw BizException.stateConflict(
                    "批次当前状态（" + bs.label() + "）不可摇号，需先发布/报名");
        }
        // 幂等：已摇过号不再重复
        Long exist = lotteryMapper.selectCount(new LambdaQueryWrapper<BizLotteryResult>()
                .eq(BizLotteryResult::getBatchId, batchId));
        if (exist != null && exist > 0) {
            throw BizException.stateConflict("该批次已摇号，不可重复执行");
        }

        List<Long> houses = listBatchHouses(batchId, "AVAILABLE");
        if (houses.isEmpty()) {
            throw BizException.stateConflict("批次无可配房源，无法摇号");
        }
        String seed = cmd.seed() == null || cmd.seed().isBlank()
                ? UUID.randomUUID().toString().replace("-", "") : cmd.seed();

        // 参与摇号：同保障类型 + 轮候中
        List<BizWaitingQueue> candidates = waitingMapper.selectList(
                new LambdaQueryWrapper<BizWaitingQueue>()
                        .eq(BizWaitingQueue::getSecurityType, b.getSecurityType())
                        .eq(BizWaitingQueue::getQueueStatus, QueueStatus.WAITING.name())
                        .eq(b.getOrgId() != null, BizWaitingQueue::getOrgId, b.getOrgId()));
        if (candidates.isEmpty()) {
            throw BizException.stateConflict("无轮候中的申请人，无法摇号");
        }

        // 排序：总分降序，同分按入队时间升序，完全相同时用种子决定
        candidates.sort((x, y) -> {
            int c = y.getTotalScore().compareTo(x.getTotalScore());
            if (c != 0) {
                return c;
            }
            int t = x.getEnterTime().compareTo(y.getEnterTime());
            if (t != 0) {
                return t;
            }
            return seedHash(seed, x.getId()).compareTo(seedHash(seed, y.getId()));
        });

        int houseN = houses.size();
        String tenantId = TenantContext.tenantId();
        LocalDateTime now = LocalDateTime.now();
        List<LotteryResultVO> out = new ArrayList<>();

        for (int i = 0; i < candidates.size(); i++) {
            BizWaitingQueue w = candidates.get(i);
            LotteryResultType type;
            if (i < houseN) {
                type = LotteryResultType.WON;
            } else if (i < houseN + 3) {
                // 房源数之后 3 名作为递补
                type = LotteryResultType.WAITLIST;
            } else {
                type = LotteryResultType.LOST;
            }
            BizLotteryResult r = new BizLotteryResult();
            r.setId(idGen.nextId());
            r.setTenantId(tenantId);
            r.setBatchId(batchId);
            r.setPersonId(w.getPersonId());
            r.setApplicationId(w.getApplicationId());
            r.setWaitingId(w.getId());
            r.setResultType(type.name());
            r.setLotterySeq(seedHash(seed, w.getId()).substring(0, 12));
            r.setSelectSeq(type == LotteryResultType.WON ? i + 1 : null);
            r.setResultStatus("PENDING");
            r.setCreateTime(now);
            r.setUpdateTime(now);
            lotteryMapper.insert(r);
            out.add(LotteryResultVO.from(r));
        }

        // 中签人员移出「轮候中」，状态置「已中签」
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
        b.setLotterySeed(seed);
        b.setLotteryAlgo("SORT_SCORE_THEN_SEED");
        if (cmd.notaryInfo() != null && !cmd.notaryInfo().isBlank()) {
            b.setNotaryInfo(cmd.notaryInfo());
        }
        b.setApplicantCount(candidates.size());
        b.setLotteryTime(now);
        b.setBatchStatus(BatchStatus.LOTTERY_DONE.name());
        b.setUpdateTime(now);
        batchMapper.updateById(b);

        log.info("批次 {} 摇号完成：候选 {} 房源 {} 中签 {} 递补 {} 种子 {}",
                b.getBatchNo(), candidates.size(), houseN, Math.min(houseN, candidates.size()),
                Math.max(0, Math.min(3, candidates.size() - houseN)), seed);

        out.sort(Comparator.comparing(LotteryResultVO::selectSeq,
                Comparator.nullsLast(Comparator.naturalOrder())));
        try {
            autoCreatePublicity(b);
        } catch (Exception e) {
            log.warn("摇号后自动生成公示失败（批次 {}）：{}", b.getBatchNo(), e.getMessage());
        }
        return out;
    }

    /**
     * 摇号完成自动生成配租公示（草稿），公示期默认满足系统参数 minDays。
     *
     * <p>已存在同批次公示则不重复生成。
     */
    private void autoCreatePublicity(BizBatch b) {
        // race:ignore 公示重复生成可接受（唯一影响是多一条草稿），且已有存在性检查兜底
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

    /** 结果页补「附加分/轮候天数/总分」，来源是该次摇号对应的轮候记录。 */
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
    public List<LotteryResultVO> listLotteryResults(Long batchId) {
        List<LotteryResultVO> rows = lotteryMapper.selectList(
                        new LambdaQueryWrapper<BizLotteryResult>()
                                .eq(BizLotteryResult::getBatchId, batchId)
                                .orderByAsc(BizLotteryResult::getSelectSeq)
                                .orderByAsc(BizLotteryResult::getId))
                .stream().map(LotteryResultVO::from).map(this::withScores)
                .sorted((a, b) -> {
                    boolean wa = "WON".equals(a.resultType());
                    boolean wb = "WON".equals(b.resultType());
                    if (wa != wb) {
                        return wa ? -1 : 1;
                    }
                    Integer sa = a.selectSeq() == null ? Integer.MAX_VALUE : a.selectSeq();
                    Integer sb = b.selectSeq() == null ? Integer.MAX_VALUE : b.selectSeq();
                    return Integer.compare(sa, sb);
                })
                .toList();
        java.util.Set<Long> pids = rows.stream().map(LotteryResultVO::personId)
                .filter(java.util.Objects::nonNull).collect(java.util.stream.Collectors.toSet());
        if (pids.isEmpty()) {
            return rows;
        }
        java.util.Map<Long, Person> pm = new java.util.HashMap<>();
        for (Person x : personMapper.selectBatchIds(pids)) {
            pm.put(x.getId(), x);
        }
        return rows.stream().map(v -> {
            Person x = pm.get(v.personId());
            return v.withPerson(x == null ? null : x.getPersonName(),
                    maskPhone(x == null ? null : x.getPhone()));
        }).toList();
    }

    // ==================== 配租 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AllocationVO allocate(AllocateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        BizBatch b = requireBatch(cmd.batchId());
        BatchStatus bs = batchStatusOf(b);
        if (bs != BatchStatus.LOTTERY_DONE && bs != BatchStatus.SELECTING) {
            throw BizException.stateConflict(
                    "批次当前状态（" + bs.label() + "）不可配租，需先完成摇号");
        }
        // 房源必须在池内且可选
        BizBatchHouse pool = batchHouseMapper.selectOne(new LambdaQueryWrapper<BizBatchHouse>()
                .eq(BizBatchHouse::getBatchId, cmd.batchId())
                .eq(BizBatchHouse::getHouseId, cmd.houseId())
                .last("LIMIT 1"));
        if (pool == null) {
            throw BizException.stateConflict("房源不在该批次房源池内");
        }
        if (!"AVAILABLE".equals(pool.getInPoolStatus())) {
            throw BizException.stateConflict("房源已被占用或移出（当前："
                    + pool.getInPoolStatus() + "）");
        }
        // 该人是否已有未终结的配租单
        Long dup = allocationMapper.selectCount(new LambdaQueryWrapper<BizAllocation>()
                .eq(BizAllocation::getPersonId, cmd.personId())
                .eq(BizAllocation::getAllocationStatus, AllocationStatus.PENDING_SIGN.name()));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("该承租人已有待签约的配租单");
        }

        // 反查摇号结果（校验资格）
        BizLotteryResult lr = null;
        if (cmd.lotteryResultId() != null) {
            lr = lotteryMapper.selectById(cmd.lotteryResultId());
        } else {
            lr = lotteryMapper.selectOne(new LambdaQueryWrapper<BizLotteryResult>()
                    .eq(BizLotteryResult::getBatchId, cmd.batchId())
                    .eq(BizLotteryResult::getPersonId, cmd.personId())
                    .last("LIMIT 1"));
        }
        if (lr != null) {
            LotteryResultType rt;
            try {
                rt = LotteryResultType.valueOf(lr.getResultType());
            } catch (IllegalArgumentException e) {
                rt = LotteryResultType.LOST;
            }
            if (!rt.canAllocate()) {
                throw BizException.stateConflict("该申请人摇号结果为" + rt.label() + "，不具备配租资格");
            }
        }

        int lockHours = cmd.lockHours() == null || cmd.lockHours() <= 0
                ? DEFAULT_LOCK_HOURS : cmd.lockHours();
        LocalDateTime now = LocalDateTime.now();

        BizAllocation a = new BizAllocation();
        a.setId(idGen.nextId());
        a.setTenantId(tenantId);
        a.setAllocationNo("BA" + a.getId());
        a.setBatchId(cmd.batchId());
        a.setPersonId(cmd.personId());
        a.setHouseId(cmd.houseId());
        a.setSpaceId(pool.getSpaceId());
        a.setAllocationType("LOTTERY");
        a.setAllocationDate(LocalDate.now());
        a.setPlanRentStart(cmd.planRentStart());
        a.setPlanRentEnd(cmd.planRentEnd());
        a.setAllocationStatus(AllocationStatus.PENDING_SIGN.name());
        a.setLockExpireTime(now.plusHours(lockHours));
        a.setCreateTime(now);
        a.setUpdateTime(now);
        allocationMapper.insert(a);

        // 锁定房源
        pool.setInPoolStatus("LOCKED");
        pool.setUpdateTime(now);
        batchHouseMapper.updateById(pool);

        // 更新摇号结果 + 轮候状态
        if (lr != null) {
            lr.setHouseId(cmd.houseId());
            lr.setSpaceId(pool.getSpaceId());
            lr.setSelectTime(now);
            lr.setUpdateTime(now);
            lotteryMapper.updateById(lr);
            if (lr.getWaitingId() != null) {
                BizWaitingQueue w = waitingMapper.selectById(lr.getWaitingId());
                if (w != null && queueStatusOf(w) == QueueStatus.WAITING) {
                    w.setQueueStatus(QueueStatus.WON.name());
                    w.setUpdateTime(now);
                    waitingMapper.updateById(w);
                }
            }
        }

        log.info("配租单 {} 生成：批次 {} 房源 {} → 承租人 {}，锁定至 {}",
                a.getAllocationNo(), cmd.batchId(), cmd.houseId(), cmd.personId(),
                a.getLockExpireTime());
        return AllocationVO.from(a);
    }

    @Override
    public AllocationVO getAllocation(Long id) {
        return AllocationVO.from(requireAllocation(id));
    }

    /** 配租记录按人员限权（SELF 只看本人）。 */
    private void applyAllocationScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                    <com.yundao.bp.biz.entity.BizAllocation> qw) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            qw.eq(com.yundao.bp.biz.entity.BizAllocation::getPersonId,
                    scope.personId() == null ? -1L : scope.personId());
        }
    }

    /** 人员姓名/手机号补全（配租单列表） */
    private java.util.List<AllocationVO> withPersons(java.util.List<AllocationVO> rows) {
        if (rows.isEmpty()) {
            return rows;
        }
        java.util.Set<Long> pids = rows.stream().map(AllocationVO::personId)
                .filter(java.util.Objects::nonNull).collect(java.util.stream.Collectors.toSet());
        java.util.Map<Long, Person> pm = new java.util.HashMap<>();
        if (!pids.isEmpty()) {
            for (Person x : personMapper.selectBatchIds(pids)) {
                pm.put(x.getId(), x);
            }
        }
        return rows.stream().map(v -> {
            Person x = pm.get(v.personId());
            return v.withPerson(x == null ? null : x.getPersonName(),
                    maskPhone(x == null ? null : x.getPhone()));
        }).toList();
    }

    private static String maskPhone(String phone) {
        if (phone == null || phone.length() < 7) {
            return phone;
        }
        return phone.substring(0, 3) + "****" + phone.substring(phone.length() - 4);
    }

    public PageResult<AllocationVO> pageAllocations(long pageNum, long pageSize, Long personId,
                                                    Long batchId, String status) {
        LambdaQueryWrapper<BizAllocation> qw = new LambdaQueryWrapper<BizAllocation>()
                .eq(personId != null, BizAllocation::getPersonId, personId)
                .eq(batchId != null, BizAllocation::getBatchId, batchId)
                .eq(status != null && !status.isBlank(), BizAllocation::getAllocationStatus, status)
                .orderByDesc(BizAllocation::getId);
        applyAllocationScope(qw);
        IPage<BizAllocation> page = allocationMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<AllocationVO> rows = withPersons(
                page.getRecords().stream().map(AllocationVO::from).toList());
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AllocationVO sign(Long id) {
        BizAllocation a = requireAllocation(id);

        // ⭐ 合规硬校验（决策 D23）：配租结果必须完成公示（≥7 个自然日并已结束公示）才能签约
        BizBatch batch = batchMapper.selectById(a.getBatchId());
        Long checkOrgId = batch == null ? null : batch.getOrgId();
        if (!publicityService.hasCompletedAllocationPublicity(checkOrgId, LocalDate.now())) {
            throw BizException.stateConflict(
                    "配租结果尚未完成公示，不能签约。"
                            + "请先在「公示」中发布配租公示（不少于 7 个自然日）并结束公示后，再办理签约。"
                            + "（组织 orgId=" + checkOrgId + "）");
        }

        transitionAllocation(a, AllocationStatus.SIGNED);
        a.setUpdateTime(LocalDateTime.now());
        allocationMapper.updateById(a);

        // 房源池置已选中
        BizBatchHouse pool = batchHouseMapper.selectOne(new LambdaQueryWrapper<BizBatchHouse>()
                .eq(BizBatchHouse::getBatchId, a.getBatchId())
                .eq(BizBatchHouse::getHouseId, a.getHouseId())
                .last("LIMIT 1"));
        if (pool != null) {
            pool.setInPoolStatus("SELECTED");
            pool.setUpdateTime(LocalDateTime.now());
            batchHouseMapper.updateById(pool);
        }
        log.info("配租单 {} 已签约（房源 {}）", a.getAllocationNo(), a.getHouseId());
        return AllocationVO.from(a);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AllocationVO giveUp(Long id, String reason) {
        BizAllocation a = requireAllocation(id);
        transitionAllocation(a, AllocationStatus.CANCELLED);
        a.setGiveUpReason(reason == null ? "承租人放弃" : reason);
        a.setUpdateTime(LocalDateTime.now());
        allocationMapper.updateById(a);
        releaseHousePool(a);
        return AllocationVO.from(a);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int releaseExpiredLocks() {
        List<BizAllocation> expired = allocationMapper.selectList(
                new LambdaQueryWrapper<BizAllocation>()
                        .eq(BizAllocation::getAllocationStatus,
                                AllocationStatus.PENDING_SIGN.name())
                        .lt(BizAllocation::getLockExpireTime, LocalDateTime.now()));
        int n = 0;
        for (BizAllocation a : expired) {
            a.setAllocationStatus(AllocationStatus.EXPIRED.name());
            a.setGiveUpReason("锁定超时未签约，系统自动释放");
            a.setUpdateTime(LocalDateTime.now());
            allocationMapper.updateById(a);
            releaseHousePool(a);
            n++;
        }
        if (n > 0) {
            log.info("释放超时未签约配租单 {} 个", n);
        }
        return n;
    }

    // ==================== 内部 ====================

    /** 释放房源回池（取消/超时）。 */
    private void releaseHousePool(BizAllocation a) {
        BizBatchHouse pool = batchHouseMapper.selectOne(new LambdaQueryWrapper<BizBatchHouse>()
                .eq(BizBatchHouse::getBatchId, a.getBatchId())
                .eq(BizBatchHouse::getHouseId, a.getHouseId())
                .last("LIMIT 1"));
        if (pool != null && !"REMOVED".equals(pool.getInPoolStatus())) {
            pool.setInPoolStatus("AVAILABLE");
            pool.setUpdateTime(LocalDateTime.now());
            batchHouseMapper.updateById(pool);
        }
        // 轮候状态回退为轮候中
        Long waitingId = lotteryMapper.selectList(new LambdaQueryWrapper<BizLotteryResult>()
                        .eq(BizLotteryResult::getBatchId, a.getBatchId())
                        .eq(BizLotteryResult::getPersonId, a.getPersonId()))
                .stream().findFirst().map(BizLotteryResult::getWaitingId).orElse(null);
        if (waitingId != null) {
            BizWaitingQueue w = waitingMapper.selectById(waitingId);
            if (w != null && queueStatusOf(w) == QueueStatus.WON) {
                w.setQueueStatus(QueueStatus.WAITING.name());
                w.setUpdateTime(LocalDateTime.now());
                waitingMapper.updateById(w);
            }
        }
    }

    private BizWaitingQueue requireWaiting(Long id) {
        BizWaitingQueue e = waitingMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("轮候记录");
        }
        return e;
    }

    private BizBatch requireBatch(Long id) {
        BizBatch e = batchMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("配租批次");
        }
        return e;
    }

    private BizAllocation requireAllocation(Long id) {
        BizAllocation e = allocationMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("配租单");
        }
        return e;
    }

    private static QueueStatus queueStatusOf(BizWaitingQueue e) {
        try {
            return QueueStatus.valueOf(e.getQueueStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("轮候状态非法: " + e.getQueueStatus());
        }
    }

    private static BatchStatus batchStatusOf(BizBatch e) {
        try {
            return BatchStatus.valueOf(e.getBatchStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("批次状态非法: " + e.getBatchStatus());
        }
    }

    private static void transitionAllocation(BizAllocation a, AllocationStatus target) {
        AllocationStatus from;
        try {
            from = AllocationStatus.valueOf(a.getAllocationStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("配租单状态非法: " + a.getAllocationStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("配租单已处于 " + target.label() + " 状态");
        }
        if (!AllocationStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "配租单状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        a.setAllocationStatus(target.name());
    }

    /** 种子加权哈希（确定性，可复现）。 */
    private static String seedHash(String seed, Long id) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] d = md.digest((seed + "|" + id).getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte x : d) {
                sb.append(String.format("%02x", x));
            }
            return sb.toString();
        } catch (Exception e) {
            throw new BizException(ErrorCode.SYSTEM_ERROR, "种子哈希计算失败");
        }
    }
}
