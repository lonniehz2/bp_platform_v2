package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.asset.entity.AssetHouse;
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

    public AllocationServiceImpl(BizWaitingQueueMapper waitingMapper, BizBatchMapper batchMapper,
                                 BizBatchHouseMapper batchHouseMapper,
                                 BizLotteryResultMapper lotteryMapper,
                                 BizAllocationMapper allocationMapper,
                                 AssetHouseMapper houseMapper,
                                 SnowflakeIdGenerator idGen,
                                 PublicityService publicityService) {
        this.waitingMapper = waitingMapper;
        this.batchMapper = batchMapper;
        this.batchHouseMapper = batchHouseMapper;
        this.lotteryMapper = lotteryMapper;
        this.allocationMapper = allocationMapper;
        this.houseMapper = houseMapper;
        this.idGen = idGen;
        this.publicityService = publicityService;
    }

    // ==================== 轮候 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WaitingVO enterQueue(WaitingEnterCmd cmd) {
        String tenantId = TenantContext.tenantId();
        // 同一申请单不可重复入轮候
        Long dup = waitingMapper.selectCount(new LambdaQueryWrapper<BizWaitingQueue>()
                .eq(BizWaitingQueue::getApplicationId, cmd.applicationId()));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("该申请单已在轮候库中");
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

    public PageResult<WaitingVO> pageWaiting(long pageNum, long pageSize, String securityType,
                                             Long orgId, String status) {
        LambdaQueryWrapper<BizWaitingQueue> qw = new LambdaQueryWrapper<BizWaitingQueue>()
                .eq(securityType != null && !securityType.isBlank(),
                        BizWaitingQueue::getSecurityType, securityType)
                .eq(orgId != null, BizWaitingQueue::getOrgId, orgId)
                .eq(status != null && !status.isBlank(), BizWaitingQueue::getQueueStatus, status)
                .orderByAsc(BizWaitingQueue::getWaitingRank)
                .orderByAsc(BizWaitingQueue::getEnterTime);
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
        return BatchVO.from(requireBatch(id));
    }

    @Override
    public PageResult<BatchVO> pageBatch(long pageNum, long pageSize, Long orgId, String status) {
        LambdaQueryWrapper<BizBatch> qw = new LambdaQueryWrapper<BizBatch>()
                .eq(orgId != null, BizBatch::getOrgId, orgId)
                .eq(status != null && !status.isBlank(), BizBatch::getBatchStatus, status)
                .orderByDesc(BizBatch::getId);
        IPage<BizBatch> page = batchMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<BatchVO> rows = page.getRecords().stream().map(BatchVO::from).toList();
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
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!BatchStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "批次状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        b.setBatchStatus(target.name());
        b.setUpdateTime(LocalDateTime.now());
        batchMapper.updateById(b);
        return BatchVO.from(b);
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

    @Override
    @Transactional(rollbackFor = Exception.class)
    public List<LotteryResultVO> runLottery(LotteryRunCmd cmd) {
        BizBatch b = requireBatch(cmd.batchId());
        BatchStatus bs = batchStatusOf(b);
        if (!bs.canLottery()) {
            throw BizException.stateConflict(
                    "批次当前状态（" + bs.label() + "）不可摇号，需先发布/报名");
        }
        // 幂等：已摇过号不再重复
        Long exist = lotteryMapper.selectCount(new LambdaQueryWrapper<BizLotteryResult>()
                .eq(BizLotteryResult::getBatchId, cmd.batchId()));
        if (exist != null && exist > 0) {
            throw BizException.stateConflict("该批次已摇号，不可重复执行");
        }

        List<Long> houses = listBatchHouses(cmd.batchId(), "AVAILABLE");
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
            r.setBatchId(cmd.batchId());
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
        return out;
    }

    @Override
    public List<LotteryResultVO> listLotteryResults(Long batchId) {
        return lotteryMapper.selectList(new LambdaQueryWrapper<BizLotteryResult>()
                        .eq(BizLotteryResult::getBatchId, batchId)
                        .orderByAsc(BizLotteryResult::getSelectSeq)
                        .orderByAsc(BizLotteryResult::getId))
                .stream().map(LotteryResultVO::from).toList();
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

    @Override
    public PageResult<AllocationVO> pageAllocations(long pageNum, long pageSize, Long personId,
                                                    Long batchId, String status) {
        LambdaQueryWrapper<BizAllocation> qw = new LambdaQueryWrapper<BizAllocation>()
                .eq(personId != null, BizAllocation::getPersonId, personId)
                .eq(batchId != null, BizAllocation::getBatchId, batchId)
                .eq(status != null && !status.isBlank(), BizAllocation::getAllocationStatus, status)
                .orderByDesc(BizAllocation::getId);
        IPage<BizAllocation> page = allocationMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<AllocationVO> rows = page.getRecords().stream().map(AllocationVO::from).toList();
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
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
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
