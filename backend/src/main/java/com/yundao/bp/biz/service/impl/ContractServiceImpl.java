package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.asset.service.OccupancyService;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.dto.ContractCreateCmd;
import com.yundao.bp.biz.dto.ContractVO;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.biz.service.ContractService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 合同服务实现。
 *
 * <p><b>三个自动计算</b>（不接受前端传值）：
 * <ol>
 *   <li>{@code leaseMonths = leaseStart ~ leaseEnd 的整月数}（向上取整）</li>
 *   <li>{@code actualPay = monthlyRent - subsidyAmount}（不得为负）</li>
 *   <li>{@code 押金/补贴} 为空时按 0 处理</li>
 * </ul>
 *
 * <p><b>自动授权开关</b>：合同生效时 {@code auto_grant=1} 应触发授权下发
 * （当前仅落库标记，实际调用在 grant 模块，需与合同事务解耦，见 TODO）。
 */
@Service
public class ContractServiceImpl implements ContractService {

    private static final Logger log = LoggerFactory.getLogger(ContractServiceImpl.class);

    private final BizContractMapper mapper;
    private final SnowflakeIdGenerator idGen;
    /** 合同状态变化驱动房源占用；与合同变更同事务 */
    private final OccupancyService occupancyService;


    /** 房源查询（快捷签约需要房源组织与地址） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper quickSignHouseMapper;

    /** 申请服务（快捷签约自动补线下受理申请单） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.service.ApplicationService quickSignApplicationService;

    /** 事务管理器：用于申请单补录的独立事务（失败不影响合同） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.transaction.PlatformTransactionManager quickSignTxManager;


    /** 人员查询（快捷签约补全承租人姓名与脱敏证件） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonMapper quickSignPersonMapper;


    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /**
     * 把当前用户的数据范围追加到查询条件上。
     *
     * @param qw       查询条件
     * @param orgCol   组织列（orgId）
     * @param personCol 人员列（SELF 范围用）
     */
    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            if (scope.personId() == null) {
                qw.eq(orgCol, -1L);      // 未绑定人员：不返回任何数据
            } else {
                qw.eq(personCol, scope.personId());
            }
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }

    public ContractServiceImpl(BizContractMapper mapper, SnowflakeIdGenerator idGen,
                               OccupancyService occupancyService) {
        this.mapper = mapper;
        this.idGen = idGen;
        this.occupancyService = occupancyService;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO create(ContractCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        if (!cmd.leaseEnd().isAfter(cmd.leaseStart())) {
            throw BizException.paramInvalid("止租日必须晚于起租日");
        }
        BigDecimal deposit = nz(cmd.depositAmount());
        BigDecimal subsidy = nz(cmd.subsidyAmount());
        BigDecimal actualPay = money(cmd.monthlyRent()).subtract(subsidy)
                .setScale(2, java.math.RoundingMode.HALF_UP);
        if (actualPay.compareTo(BigDecimal.ZERO) < 0) {
            throw BizException.paramInvalid("补贴不能超过月租金（实付为负）");
        }
        int months = monthCount(cmd.leaseStart(), cmd.leaseEnd());

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizContract e = new BizContract();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setContractNo("BC" + id);
        e.setContractType(cmd.contractType());
        e.setTemplateId(cmd.templateId());
        e.setAllocationId(cmd.allocationId());
        e.setOrgId(cmd.orgId());
        e.setLesseePersonId(cmd.lesseePersonId());
        e.setLesseeName(cmd.lesseeName());
        e.setLesseePhone(cmd.lesseePhone());
        e.setLesseeIdCardMask(cmd.lesseeIdCardMask());
        e.setLessorOrgId(cmd.lessorOrgId());
        e.setHouseId(cmd.houseId());
        e.setSpaceId(cmd.spaceId());
        e.setHouseAddress(cmd.houseAddress());
        e.setHouseArea(cmd.houseArea());
        e.setLeaseStart(cmd.leaseStart());
        e.setLeaseEnd(cmd.leaseEnd());
        e.setLeaseMonths(months);
        e.setRentPrice(cmd.rentPrice() == null ? null : money(cmd.rentPrice()));
        e.setRentUnit(blankToNull(cmd.rentUnit()) == null ? defaultRentUnit(cmd.contractType())
                : cmd.rentUnit());
        checkRentUnitForBizType(cmd.contractType(), e.getRentUnit());
        e.setMonthlyRent(money(cmd.monthlyRent()));
        e.setDepositAmount(deposit);
        e.setSubsidyAmount(subsidy);
        e.setActualPay(actualPay);
        e.setPayCycle(blankToNull(cmd.payCycle()) == null ? "MONTH" : cmd.payCycle());
        e.setPayDay(cmd.payDay() == null ? 1 : cmd.payDay());
        e.setLateFeeRate(cmd.lateFeeRate());
        e.setSignType(blankToNull(cmd.signType()) == null ? "ELECTRONIC" : cmd.signType());
        e.setContractStatus(ContractStatus.DRAFT.name());
        e.setParentContractId(cmd.parentContractId());
        e.setAutoGrant(1);
        e.setAutoExpire(1);
        e.setArrearsStop(1);
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        e.setCreateTime(now);
        mapper.insert(e);
        return ContractVO.from(e);
    }

    @Override
    public ContractVO get(Long id) {
        return ContractVO.from(require(id));
    }

    @Override
    public PageResult<ContractVO> page(long pageNum, long pageSize, String contractType,
                                       String status, Long houseId, Long lesseePersonId,
                                       String keyword) {
        LambdaQueryWrapper<BizContract> qw = new LambdaQueryWrapper<BizContract>()
                .eq(contractType != null && !contractType.isBlank(),
                        BizContract::getContractType, contractType)
                .eq(status != null && !status.isBlank(), BizContract::getContractStatus, status)
                .eq(houseId != null, BizContract::getHouseId, houseId)
                .eq(lesseePersonId != null, BizContract::getLesseePersonId, lesseePersonId)
                .orderByDesc(BizContract::getId);
        applyDataScope(qw, BizContract::getOrgId, BizContract::getLesseePersonId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(BizContract::getContractNo, keyword)
                    .or().like(BizContract::getLesseeName, keyword));
        }
        IPage<BizContract> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ContractVO> rows = page.getRecords().stream().map(ContractVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO submitSign(Long id) {
        BizContract e = require(id);
        transition(e, ContractStatus.PENDING_SIGN);
        mapper.updateById(e);
        return ContractVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO startSigning(Long id, String signVendor) {
        BizContract e = require(id);
        transition(e, ContractStatus.SIGNING);
        if (signVendor != null && !signVendor.isBlank()) {
            e.setSignVendor(signVendor);
        }
        mapper.updateById(e);
        return ContractVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO sign(Long id, String signFileUrl, String signFlowId) {
        BizContract pre = require(id);
        // 单机部署下按房源串行化签约，避免并发检查与写入之间的竞态
        Object lock = SIGN_LOCKS.computeIfAbsent(
                String.valueOf(pre.getHouseId()), k -> new Object());
        synchronized (lock) {
            return doSign(id, signFileUrl, signFlowId);
        }
    }

    /** 签约分片锁：key = houseId。 */
    private static final java.util.concurrent.ConcurrentHashMap<String, Object> SIGN_LOCKS
            = new java.util.concurrent.ConcurrentHashMap<>();

    private ContractVO doSign(Long id, String signFileUrl, String signFlowId) {
        BizContract e = require(id);
        // 防一房多签：同一房源已有生效合同时拒绝（并发场景由 DB 唯一性 + 本检查共同兜底）
        if (e.getHouseId() != null) {
            Long occupied = mapper.selectCount(new LambdaQueryWrapper<BizContract>()
                    .eq(BizContract::getHouseId, e.getHouseId())
                    .in(BizContract::getContractStatus,
                            List.of(ContractStatus.EFFECTIVE.name(),
                                    ContractStatus.RENEWING.name()))
                    .ne(BizContract::getId, e.getId()));
            if (occupied != null && occupied > 0) {
                throw com.yundao.bp.common.exception.BizException.paramInvalid(
                        "该房屋已有生效合同，不能重复签约（一房多签）");
            }
        }
        // 纸质合同可直接从 PENDING_SIGN 生效
        if (ContractStatus.PENDING_SIGN.name().equals(e.getContractStatus())
                && "PAPER".equals(e.getSignType())) {
            transition(e, ContractStatus.SIGNING);
        }
        transition(e, ContractStatus.EFFECTIVE);
        e.setSignTime(LocalDateTime.now());
        e.setEffectiveTime(LocalDateTime.now());
        e.setSignFileUrl(signFileUrl);
        e.setSignFlowId(signFlowId);
        mapper.updateById(e);
        // 合同生效即占房：写入占用流水并把房源推进到「已入住」
        occupancyService.occupyByContract(e.getId(), e.getHouseId(), e.getSpaceId(),
                e.getLesseePersonId(), e.getLeaseStart(), e.getLeaseEnd());
        log.info("合同 {} 已生效，autoGrant={}（授权下发需与合同事务解耦，待接入）",
                e.getContractNo(), e.getAutoGrant());
        return ContractVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO renew(Long id, LocalDate newLeaseEnd, BigDecimal newMonthlyRent) {
        BizContract e = require(id);
        if (newLeaseEnd == null || e.getLeaseEnd() == null
                || !newLeaseEnd.isAfter(e.getLeaseEnd())) {
            throw BizException.paramInvalid("新止租日必须晚于原止租日");
        }
        transition(e, ContractStatus.RENEWING);
        e.setLeaseStart(e.getLeaseEnd());
        e.setLeaseEnd(newLeaseEnd);
        if (newMonthlyRent != null) {
            e.setMonthlyRent(money(newMonthlyRent));
            e.setActualPay(money(newMonthlyRent).subtract(nz(e.getSubsidyAmount()))
                    .setScale(2, java.math.RoundingMode.HALF_UP));
            if (e.getActualPay().compareTo(BigDecimal.ZERO) < 0) {
                throw BizException.paramInvalid("补贴不能超过月租金（实付为负）");
            }
        }
        e.setLeaseMonths(monthCount(e.getLeaseStart(), newLeaseEnd));
        mapper.updateById(e);
        // 续签：同步延长占用结束日，避免合同还在履约而占用已过期
        occupancyService.extendByContract(e.getId(), newLeaseEnd);
        return ContractVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO terminate(Long id, String reason) {
        BizContract e = require(id);
        transition(e, ContractStatus.TERMINATED);
        e.setTerminateTime(LocalDateTime.now());
        e.setTerminateReason(reason);
        mapper.updateById(e);
        // 终止即退房：释放占用，房源回到空置
        occupancyService.releaseByContract(e.getId(), e.getTerminateTime().toLocalDate());
        log.info("合同 {} 已终止，autoExpire={}（撤权需与合同事务解耦，待接入）",
                e.getContractNo(), e.getAutoExpire());
        return ContractVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO cancel(Long id, String reason) {
        BizContract e = require(id);
        transition(e, ContractStatus.CANCELLED);
        e.setTerminateReason(reason);
        mapper.updateById(e);
        // 幂等兜底：已生效再作废时也要退房
        occupancyService.releaseByContract(e.getId(), LocalDate.now());
        return ContractVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int expireDue() {
        List<BizContract> due = mapper.selectList(new LambdaQueryWrapper<BizContract>()
                .in(BizContract::getContractStatus,
                        List.of(ContractStatus.EFFECTIVE.name(), ContractStatus.RENEWING.name()))
                .lt(BizContract::getLeaseEnd, LocalDate.now()));
        int n = 0;
        for (BizContract e : due) {
            e.setContractStatus(ContractStatus.EXPIRED.name());
            e.setTerminateTime(LocalDateTime.now());
            mapper.updateById(e);
            // 到期即退房
            occupancyService.releaseByContract(e.getId(), e.getLeaseEnd());
            n++;
        }
        if (n > 0) {
            log.info("合同到期扫描：{} 份合同置为 EXPIRED", n);
        }
        return n;
    }

    /**
     * 租期月数：按自然月计算，不足一个月按一个月。
     *
     * <p>⚠️ 不能用 {@code 天数 / 30} 向上取整：1 年 = 365 天 → 365/30 = 12.17 → 会算成 13 个月。
     * 正确做法是 {@link ChronoUnit#MONTHS} 取整月，再判断末尾是否有零头天数。
     *
     * <pre>
     *   2026-01-01 ~ 2027-01-01 → 12 个月（整年无零头）
     *   2026-01-01 ~ 2027-01-02 → 13 个月（12 个月 + 1 天零头）
     * </pre>
     */
    private static int monthCount(LocalDate start, LocalDate end) {
        if (start == null || end == null || !end.isAfter(start)) {
            return 1;
        }
        long full = ChronoUnit.MONTHS.between(start, end);
        long restDays = ChronoUnit.DAYS.between(start.plusMonths(full), end);
        int months = (int) full + (restDays > 0 ? 1 : 0);
        return Math.max(1, months);
    }

    private BizContract require(Long id) {
        BizContract e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("合同");
        }
        return e;
    }

    private static void transition(BizContract e, ContractStatus target) {
        ContractStatus from;
        try {
            from = ContractStatus.valueOf(e.getContractStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("合同状态非法: " + e.getContractStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ContractStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setContractStatus(target.name());
        e.setUpdateTime(LocalDateTime.now());
    }

    /** 空值归零，并统一金额为 2 位小数（含税金额规范）。 */
    /** 金额统一 2 位小数。 */
    /**
     * 按业态给出默认租金单位。
     *
     * <p>多业态扩展的第一个落点：不同业态的计价口径不同——
     * 宿舍按「床·月」、酒店/民宿按「套·夜」、保障房与公寓按「面积/套·月」。
     */
    private static String defaultRentUnit(String contractType) {
        if (contractType == null) {
            return "HOUSE_MONTH";
        }
        return switch (contractType) {
            case "DORMITORY" -> "BED_MONTH";
            case "SERVICE" -> "HOUSE_NIGHT";
            default -> "HOUSE_MONTH";
        };
    }

    /**
     * 校验租金单位与业态是否匹配（多业态约束）。
     *
     * <p>规则：
     * <ul>
     *   <li>宿舍 DORMITORY：只能按床·月或套·月（不能按面积、不能按夜）</li>
     *   <li>服务式公寓/日租 SERVICE：只能按套·夜</li>
     *   <li>其余（公租/保租/人才/租赁 LEASE）：按面积·月或套·月</li>
     * </ul>
     */
    private static void checkRentUnitForBizType(String contractType, String rentUnit) {
        if (contractType == null || rentUnit == null || rentUnit.isBlank()) {
            return;
        }
        java.util.Set<String> allowed = switch (contractType) {
            // 床位类（宿舍/青旅）：可按床·月，也可按床·夜
            case "DORMITORY" -> java.util.Set.of("BED_MONTH", "BED_NIGHT", "HOUSE_MONTH");
            // 按夜计价（酒店公寓/民宿/日租）：套·夜或床·夜
            case "SERVICE" -> java.util.Set.of("HOUSE_NIGHT", "BED_NIGHT");
            default -> java.util.Set.of("AREA_MONTH", "HOUSE_MONTH");
        };
        if (!allowed.contains(rentUnit)) {
            throw BizException.paramInvalid("业态 " + contractType + " 不支持租金单位 " + rentUnit
                    + "，可选：" + String.join("/", allowed));
        }
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, java.math.RoundingMode.HALF_UP);
    }

    private static BigDecimal nz(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, java.math.RoundingMode.HALF_UP);
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO updateContract(Long id,
            com.yundao.bp.biz.controller.ContractController.ContractUpdateCmd cmd) {
        BizContract e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("合同");
        }
        if (!"DRAFT".equals(e.getContractStatus())) {
            throw BizException.paramInvalid("仅草稿状态的合同可直接编辑，签约后请走合同变更");
        }
        if (cmd.rentPrice() != null) {
            e.setRentPrice(money(cmd.rentPrice()));
        }
        if (cmd.monthlyRent() != null) {
            e.setMonthlyRent(money(cmd.monthlyRent()));
        }
        if (cmd.depositAmount() != null) {
            e.setDepositAmount(money(cmd.depositAmount()));
        }
        if (cmd.subsidyAmount() != null) {
            e.setSubsidyAmount(money(cmd.subsidyAmount()));
        }
        if (cmd.leaseStart() != null) {
            e.setLeaseStart(cmd.leaseStart());
        }
        if (cmd.leaseEnd() != null) {
            e.setLeaseEnd(cmd.leaseEnd());
        }
        if (e.getLeaseStart() != null && e.getLeaseEnd() != null) {
            e.setLeaseMonths(monthCount(e.getLeaseStart(), e.getLeaseEnd()));
        }
        if (cmd.payDay() != null) {
            e.setPayDay(cmd.payDay());
        }
        if (cmd.payCycle() != null && !cmd.payCycle().isBlank()) {
            e.setPayCycle(cmd.payCycle());
        }
        if (cmd.remark() != null) {
            e.setRemark(cmd.remark());
        }
        mapper.updateById(e);
        return ContractVO.from(e);
    }

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public ContractVO quickSign(com.yundao.bp.biz.controller.ContractController.QuickSignCmd cmd) {
        com.yundao.bp.asset.entity.AssetHouse house =
                quickSignHouseMapper == null ? null : quickSignHouseMapper.selectById(cmd.houseId());
        if (house == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("房源");
        }
        Long orgId = house.getOrgId();
        if (orgId == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("房源缺少所属组织，无法签约");
        }
        String securityType = (cmd.securityType() == null || cmd.securityType().isBlank())
                ? "PUBLIC" : cmd.securityType();

        // 1) 自动补一张线下受理申请单。
        //    申请单创建走独立事务（REQUIRES_NEW）：即便补录失败也不会把合同事务标记为回滚。
        final Long fOrgId = orgId;
        final String fSecurityType = securityType;
        if (quickSignApplicationService != null && quickSignTxManager != null) {
            try {
                org.springframework.transaction.support.TransactionTemplate tt =
                        new org.springframework.transaction.support.TransactionTemplate(
                                quickSignTxManager);
                tt.setPropagationBehavior(
                        org.springframework.transaction.TransactionDefinition.PROPAGATION_REQUIRES_NEW);
                tt.execute(status -> {
                    com.yundao.bp.biz.dto.ApplicationCreateCmd app =
                            new com.yundao.bp.biz.dto.ApplicationCreateCmd(
                                    fOrgId, cmd.personId(), fSecurityType, "HOUSE", "OFFLINE",
                                    1, null, null, null,
                                    null, null, null, null, null,
                                    null, null, null, null, null,
                                    cmd.remark());
                    quickSignApplicationService.create(app);
                    return null;
                });
                log.info("快捷签约：已为人员 {} 自动补线下受理申请单", cmd.personId());
            } catch (Exception ex) {
                log.warn("快捷签约自动补申请单失败（合同仍创建）：{}", ex.getMessage());
            }
        }

        // 2) 查人员补齐承租人信息（合同文本需要姓名与脱敏证件）
        String lesseeName = null;
        String lesseePhone = null;
        String lesseeIdCardMask = null;
        if (quickSignPersonMapper != null) {
            com.yundao.bp.person.entity.Person person =
                    quickSignPersonMapper.selectById(cmd.personId());
            if (person != null) {
                lesseeName = person.getRealName();
                lesseePhone = person.getPhone();
                lesseeIdCardMask = person.getIdCardMask();
            }
        }

        // 3) 创建合同草稿（金额口径：actualPay 由服务端计算）
        java.math.BigDecimal rent = cmd.monthlyRent();
        String contractType = "AFFORDABLE".equals(securityType) ? "AFFORDABLE"
                : ("TALENT".equals(securityType) ? "TALENT" : "PUBLIC_RENTAL");
        com.yundao.bp.biz.dto.ContractCreateCmd create =
                new com.yundao.bp.biz.dto.ContractCreateCmd(
                        contractType,           // contractType
                        orgId,                  // orgId
                        orgId,                  // lessorOrgId
                        cmd.personId(),         // lesseePersonId
                        lesseeName,             // lesseeName（按人员补齐）
                        lesseePhone,            // lesseePhone
                        lesseeIdCardMask,       // lesseeIdCardMask（脱敏）
                        cmd.houseId(),          // houseId
                        house.getSpaceId(),     // spaceId
                        house.getHouseName(),   // houseAddress（房源名称作地址展示）
                        house.getArea(),        // houseArea
                        cmd.leaseStart(),       // leaseStart
                        cmd.leaseEnd(),         // leaseEnd
                        rent,                   // rentPrice
                        "HOUSE_MONTH",          // rentUnit
                        rent,                   // monthlyRent
                        cmd.depositAmount(),    // depositAmount
                        null,                   // subsidyAmount
                        "MONTH",                // payCycle
                        5,                      // payDay
                        null,                   // signType
                        null,                   // templateId
                        null,                   // allocationId
                        null,                   // parentContractId
                        null,                   // lateFeeRate
                        cmd.remark());          // remark
        return create(create);
    }
}
