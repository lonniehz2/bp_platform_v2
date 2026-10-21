package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.SettleStatus;
import com.yundao.bp.biz.constant.TerminationStatus;
import com.yundao.bp.biz.constant.TerminationType;
import com.yundao.bp.biz.dto.TerminationCreateCmd;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.biz.entity.BizTermination;
import com.yundao.bp.biz.mapper.BizTerminationMapper;
import com.yundao.bp.biz.service.TerminationService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.constant.ConfigKeys;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 退租/腾退实现。
 */
@Service
public class TerminationServiceImpl implements TerminationService {

    private static final Logger log = LoggerFactory.getLogger(TerminationServiceImpl.class);

    /** 重庆：腾退过渡期默认 3 个月 */
    private static final int DEFAULT_TRANSITION_MONTHS = 3;
    /** 重庆：过渡期内租金倍率 1.5 */
    private static final BigDecimal DEFAULT_TRANSITION_MULTIPLIER = new BigDecimal("1.5");
    /** 成都：搬迁期上限 6 个月（可被系统参数覆盖） */
    private static final int DEFAULT_MAX_RELOCATION_MONTHS = 6;
    /** 系统参数（政策参数可配置） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.sys.service.ConfigService configService;

    private int cfgInt(String key, int def) {
        return configService == null ? def : configService.getInt(key, def);
    }

    private java.math.BigDecimal cfgDec(String key, String def) {
        return configService == null ? new java.math.BigDecimal(def)
                : configService.getDecimal(key, new java.math.BigDecimal(def));
    }

    /** 违规清退：5 年内不得再申请 */
    private static final int EXPEL_BAN_YEARS = 5;

    private final BizTerminationMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public TerminationServiceImpl(BizTerminationMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO apply(TerminationCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        TerminationType type;
        try {
            type = TerminationType.valueOf(cmd.terminationType());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("退租类型不合法");
        }

        int maxReloc = cfgInt(ConfigKeys.TERMINATION_RELOCATION_MAX_MONTHS,
                DEFAULT_MAX_RELOCATION_MONTHS);
        if (cmd.relocationMonths() != null && cmd.relocationMonths() > maxReloc) {
            throw BizException.paramInvalid(
                    "搬迁期不能超过 " + maxReloc + " 个月（成都政策）");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        LocalDate today = LocalDate.now();

        BizTermination e = new BizTermination();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setTerminationNo("BT" + id);
        e.setContractId(cmd.contractId());
        e.setHouseId(cmd.houseId());
        e.setPersonId(cmd.personId());
        e.setTerminationType(type.name());
        e.setApplyTime(now);
        e.setPlanExitDate(cmd.planExitDate() == null ? today.plusMonths(1) : cmd.planExitDate());
        e.setExitReason(cmd.exitReason());
        e.setInspectStatus("PENDING");
        e.setDamageAmount(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        e.setSettleAmount(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        e.setDepositRefund(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        e.setArrearsAmount(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        e.setSettleStatus(SettleStatus.PENDING.name());
        e.setTerminationStatus(TerminationStatus.APPLYING.name());
        e.setHouseReleased(0);
        e.setGrantRevoked(0);
        e.setEnforceFlag(0);
        e.setNotaryFlag(0);

        // 重庆：腾退过渡期。
        // 除腾退类（EXPEL/NORMAL）默认给过渡期外，
        // 显式传入 transitionMonths 时（如年审退出）也一律生效，
        // 避免"年审超标退出"这类政策性退出拿不到过渡期。
        if (type == TerminationType.EXPEL || type == TerminationType.NORMAL
                || cmd.transitionMonths() != null) {
            int months = cmd.transitionMonths() == null
                    ? DEFAULT_TRANSITION_MONTHS : cmd.transitionMonths();
            e.setTransitionStartDate(e.getPlanExitDate());
            e.setTransitionEndDate(e.getPlanExitDate().plusMonths(months));
            e.setTransitionMonths(months);
            e.setTransitionRentMultiplier(cmd.transitionRentMultiplier() == null
                    ? cfgDec(ConfigKeys.TERMINATION_TRANSITION_MULTIPLIER, "1.5")
                    : cmd.transitionRentMultiplier());
        }
        // 成都：搬迁期
        if (cmd.relocationMonths() != null && cmd.relocationMonths() > 0) {
            e.setRelocationStartDate(e.getPlanExitDate());
            e.setRelocationEndDate(e.getPlanExitDate().plusMonths(cmd.relocationMonths()));
        }
        // 违规清退：限制再申请
        if (type == TerminationType.EXPEL) {
            e.setBanReapplyEndDate(today.plusYears(EXPEL_BAN_YEARS));
        }

        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        return TerminationVO.from(e);
    }

    @Override
    public TerminationVO get(Long id) {
        return TerminationVO.from(require(id));
    }

    @Override
    public PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                          Long contractId, Long houseId, String keyword) {
        LambdaQueryWrapper<BizTermination> qw = new LambdaQueryWrapper<BizTermination>()
                .eq(type != null && !type.isBlank(), BizTermination::getTerminationType, type)
                .eq(status != null && !status.isBlank(),
                        BizTermination::getTerminationStatus, status)
                .eq(contractId != null, BizTermination::getContractId, contractId)
                .eq(houseId != null, BizTermination::getHouseId, houseId)
                .orderByDesc(BizTermination::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.like(BizTermination::getTerminationNo, keyword);
        }
        IPage<BizTermination> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<TerminationVO> rows = page.getRecords().stream().map(TerminationVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO submit(Long id) {
        BizTermination e = require(id);
        transition(e, TerminationStatus.APPROVING);
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO approve(Long id, String opinion) {
        BizTermination e = require(id);
        transition(e, TerminationStatus.APPROVED);
        e.setExitReason(e.getExitReason() == null ? opinion : e.getExitReason());
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO reject(Long id, String reason) {
        BizTermination e = require(id);
        transition(e, TerminationStatus.REJECTED);
        e.setExitReason(reason);
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO cancel(Long id, String reason) {
        BizTermination e = require(id);
        transition(e, TerminationStatus.CANCELLED);
        e.setExitReason(reason);
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO inspect(Long id, String inspectStatus, String inspectResult,
                                 BigDecimal damageAmount, String inspectImages) {
        BizTermination e = require(id);
        if (!(TerminationStatus.APPROVED.name().equals(e.getTerminationStatus())
                || TerminationStatus.APPROVING.name().equals(e.getTerminationStatus()))) {
            throw BizException.stateConflict("仅在审批中/已批准状态可验房");
        }
        if (!List.of("PENDING", "PASSED", "ABNORMAL").contains(inspectStatus)) {
            throw BizException.paramInvalid("验房状态不合法: " + inspectStatus);
        }
        e.setInspectStatus(inspectStatus);
        e.setInspectResult(inspectResult);
        e.setInspectImages(inspectImages);
        if (damageAmount != null) {
            if (damageAmount.compareTo(BigDecimal.ZERO) < 0) {
                throw BizException.paramInvalid("损坏赔偿金额不能为负");
            }
            e.setDamageAmount(damageAmount.setScale(2, RoundingMode.HALF_UP));
        }
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO settle(Long id, BigDecimal depositRefund, BigDecimal arrearsAmount) {
        BizTermination e = require(id);
        if (!TerminationStatus.APPROVED.name().equals(e.getTerminationStatus())) {
            throw BizException.stateConflict("仅在已批准状态可结算");
        }
        BigDecimal refund = nz(depositRefund);
        BigDecimal arrears = nz(arrearsAmount);
        BigDecimal damage = nz(e.getDamageAmount());
        // 结算金额 = 押金退还 - 欠费 - 损坏赔偿（正数退还，负数补缴）
        BigDecimal settle = refund.subtract(arrears).subtract(damage)
                .setScale(2, RoundingMode.HALF_UP);
        e.setDepositRefund(refund);
        e.setArrearsAmount(arrears);
        e.setSettleAmount(settle);
        e.setSettleStatus(SettleStatus.SETTLED.name());
        mapper.updateById(e);
        log.info("退租单 {} 结算完成：押金退还 {} - 欠费 {} - 损坏 {} = {}",
                e.getTerminationNo(), refund, arrears, damage, settle);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO markReleased(Long id, Boolean houseReleased, Boolean grantRevoked) {
        BizTermination e = require(id);
        if (houseReleased != null) {
            e.setHouseReleased(houseReleased ? 1 : 0);
        }
        if (grantRevoked != null) {
            e.setGrantRevoked(grantRevoked ? 1 : 0);
        }
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO complete(Long id, LocalDate actualExitDate) {
        BizTermination e = require(id);
        TerminationVO cur = TerminationVO.from(e);
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
        transition(e, TerminationStatus.COMPLETED);
        e.setActualExitDate(actualExitDate == null ? LocalDate.now() : actualExitDate);
        mapper.updateById(e);
        log.info("退租单 {} 办结，房源 {} 已释放、授权已回收", e.getTerminationNo(), e.getHouseId());
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO registerEnforce(Long id, LocalDate applyDate, String court,
                                         String itemHandlerName, String itemHandlerPhone,
                                         String notaryNo) {
        BizTermination e = require(id);
        if (applyDate != null) {
            e.setEnforceFlag(1);
            e.setEnforceApplyDate(applyDate);
        }
        if (court != null && !court.isBlank()) {
            e.setEnforceCourt(court);
        }
        if (itemHandlerName != null && !itemHandlerName.isBlank()) {
            e.setItemHandlerName(itemHandlerName);
            e.setItemHandlerPhone(itemHandlerPhone);
        }
        if (notaryNo != null && !notaryNo.isBlank()) {
            e.setNotaryFlag(1);
            e.setNotaryNo(notaryNo);
        }
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    // ==================== 内部 ====================

    private BizTermination require(Long id) {
        BizTermination e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("退租单");
        }
        return e;
    }

    private static void transition(BizTermination e, TerminationStatus target) {
        TerminationStatus from;
        try {
            from = TerminationStatus.valueOf(e.getTerminationStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("退租单状态非法: " + e.getTerminationStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!TerminationStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setTerminationStatus(target.name());
        e.setUpdateTime(LocalDateTime.now());
    }

    private static BigDecimal nz(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
