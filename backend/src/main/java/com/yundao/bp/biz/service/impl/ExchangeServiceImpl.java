package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.constant.HouseStatus;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.constant.ExchangeStatus;
import com.yundao.bp.biz.constant.ExchangeType;
import com.yundao.bp.biz.dto.ExchangeCreateCmd;
import com.yundao.bp.biz.dto.ExchangeVO;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizExchange;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.biz.mapper.BizExchangeMapper;
import com.yundao.bp.biz.service.ExchangeService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.constant.ConfigKeys;
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
 * 换房实现。
 *
 * <p><b>成都限换 1 次</b>（决策 D26）：同一租期（原合同）内已完成换房 ≥1 次则拒绝再申请。
 *
 * <p><b>重庆应换不换</b>（决策 D27）：{@code no_exchange_flag=1} 时
 * {@code rent_multiplier=1.5}，计费按 1.5 倍租金执行（由计费引擎读取该倍率）。
 */
@Service
public class ExchangeServiceImpl implements ExchangeService {

    private static final Logger log = LoggerFactory.getLogger(ExchangeServiceImpl.class);

    /** 成都：同一租期内限换次数（可被系统参数覆盖） */
    private static final int DEFAULT_MAX_EXCHANGE_TIMES = 1;
    /** 重庆：应换不换的加价倍率默认值 */
    private static final String DEFAULT_NO_EXCHANGE_MULTIPLIER = "1.5";
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


    private final BizExchangeMapper mapper;
    private final AssetHouseMapper houseMapper;
    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;


    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol,
            boolean full) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            if (scope.personId() == null) {
                qw.eq(personCol, -1L);
            } else {
                qw.eq(personCol, scope.personId());
            }
            return;
        }
        if (!full) {
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

    /** 仅组织维度的数据范围（实体无人员列时使用）。 */
    private <T> void applyDataScopeOrg(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            qw.eq(orgCol, -1L);   // 仅本人角色无组织级数据
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

    public ExchangeServiceImpl(BizExchangeMapper mapper, AssetHouseMapper houseMapper,
                               BizContractMapper contractMapper,
                               SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.houseMapper = houseMapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExchangeVO apply(ExchangeCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        if (cmd.newHouseId().equals(cmd.oldHouseId())) {
            throw BizException.paramInvalid("新房源不能与原房源相同");
        }
        if (houseMapper.selectById(cmd.newHouseId()) == null) {
            throw BizException.notFound("新房源");
        }
        ExchangeType type;
        try {
            type = ExchangeType.valueOf(cmd.exchangeType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("换房类型不合法: " + cmd.exchangeType());
        }
        // 成都：限换 1 次
        int done = countCompleted(cmd.oldContractId());
        int maxTimes = cfgInt(ConfigKeys.EXCHANGE_MAX_TIMES, DEFAULT_MAX_EXCHANGE_TIMES);
        if (done >= maxTimes) {
            throw BizException.stateConflict(
                    "同一租期内已换房 " + done + " 次，超过上限（成都限 "
                            + maxTimes + " 次），不可再换");
        }
        // 同合同不允许有未完成的换房单
        Long pending = mapper.selectCount(new LambdaQueryWrapper<BizExchange>()
                .eq(BizExchange::getOldContractId, cmd.oldContractId())
                .in(BizExchange::getExchangeStatus, List.of(
                        ExchangeStatus.APPLYING.name(), ExchangeStatus.APPROVING.name(),
                        ExchangeStatus.APPROVED.name())));
        if (pending != null && pending > 0) {
            throw BizException.stateConflict("该合同已有处理中的换房单，请先办结");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizExchange e = new BizExchange();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setExchangeNo("EX" + id);
        e.setPersonId(cmd.personId());
        e.setOldContractId(cmd.oldContractId());
        e.setOldHouseId(cmd.oldHouseId());
        e.setNewHouseId(cmd.newHouseId());
        e.setExchangeType(type.name());
        e.setExchangeReason(cmd.exchangeReason());
        e.setExchangeStatus(ExchangeStatus.APPLYING.name());
        e.setGrantMigrated(0);
        e.setExchangeTimes(done + 1);
        e.setIsForced(Boolean.TRUE.equals(cmd.forceExchange()) ? 1 : 0);
        e.setNoExchangeFlag(0);
        e.setFamilySizeBefore(cmd.familySizeBefore());
        e.setFamilySizeAfter(cmd.familySizeAfter());
        e.setExchangeReasonCode(cmd.exchangeReasonCode());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        log.info("换房申请 {}：合同 {} 房源 {} → {}（{}，本租期第 {} 次，剩余次数 {}）",
                e.getExchangeNo(), cmd.oldContractId(), cmd.oldHouseId(), cmd.newHouseId(),
                type.label(), e.getExchangeTimes(),
                Math.max(0, maxTimes - done - 1));
        return ExchangeVO.from(e);
    }

    @Override
    public ExchangeVO get(Long id) {
        return ExchangeVO.from(require(id));
    }

    @Override
    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status) {
        return page(pageNum, pageSize, personId, oldContractId, status, null, null);
    }

    @Override
    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status,
                                       String keyword, Long orgId) {
        LambdaQueryWrapper<BizExchange> qw = new LambdaQueryWrapper<BizExchange>()
                .eq(personId != null, BizExchange::getPersonId, personId)
                .eq(oldContractId != null, BizExchange::getOldContractId, oldContractId)
                .eq(status != null && !status.isBlank(), BizExchange::getExchangeStatus, status)
                .orderByDesc(BizExchange::getId);
        if (orgId != null) {
            qw.apply("person_id in (select id from bp_person where org_id = {0})", orgId);
        }
        if (keyword != null && !keyword.isBlank()) {
            qw.apply("person_id in (select id from bp_person "
                    + "where person_name like concat('%', {0}, '%'))", keyword);
        }
        applyDataScope(qw, BizExchange::getPersonId, BizExchange::getPersonId, false);
        IPage<BizExchange> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ExchangeVO> rows = page.getRecords().stream().map(ExchangeVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExchangeVO submit(Long id) {
        BizExchange e = require(id);
        transition(e, ExchangeStatus.APPROVING);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ExchangeVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExchangeVO approve(Long id, String opinion) {
        BizExchange e = require(id);
        // 申请中可直接批准：内部先流转到审批中，再批准
        if (ExchangeStatus.APPLYING.name().equals(e.getExchangeStatus())) {
            transition(e, ExchangeStatus.APPROVING);
        }
        transition(e, ExchangeStatus.APPROVED);
        if (opinion != null && !opinion.isBlank()) {
            e.setExchangeReason((e.getExchangeReason() == null ? "" : e.getExchangeReason())
                    + "｜审批意见：" + opinion);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ExchangeVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExchangeVO reject(Long id, String reason) {
        BizExchange e = require(id);
        transition(e, ExchangeStatus.REJECTED);
        if (reason != null && !reason.isBlank()) {
            e.setExchangeReason((e.getExchangeReason() == null ? "" : e.getExchangeReason())
                    + "｜驳回原因：" + reason);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ExchangeVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExchangeVO complete(Long id) {
        BizExchange e = require(id);
        transition(e, ExchangeStatus.COMPLETED);

        BizContract oldCt = e.getOldContractId() == null ? null
                : contractMapper.selectById(e.getOldContractId());
        AssetHouse newHouse = houseMapper.selectById(e.getNewHouseId());
        if (newHouse == null) {
            throw BizException.notFound("新房源");
        }

        // ① 生成新合同（延续原止租日、换到新房源、直接生效）
        Long newContractId = null;
        if (oldCt != null) {
            newContractId = createNewContract(e, oldCt, newHouse);
            e.setNewContractId(newContractId);

            // ② 原合同终止（换房退出）
            oldCt.setContractStatus(ContractStatus.TERMINATED.name());
            oldCt.setTerminateReason("换房退出（换房单 " + e.getExchangeNo() + "）");
            oldCt.setUpdateTime(LocalDateTime.now());
            contractMapper.updateById(oldCt);

            // ③ 旧房源回可配池
            AssetHouse oldHouse = houseMapper.selectById(e.getOldHouseId());
            if (oldHouse != null) {
                oldHouse.setHouseStatus(HouseStatus.VACANT.name());
                oldHouse.setUpdateTime(LocalDateTime.now());
                houseMapper.updateById(oldHouse);
            }
        }

        // ④ 新房源置已入住
        newHouse.setHouseStatus(HouseStatus.OCCUPIED.name());
        newHouse.setUpdateTime(LocalDateTime.now());
        houseMapper.updateById(newHouse);

        // ⑤ 权限迁移
        e.setGrantMigrated(1);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        log.info("⭐⭐ 换房完成 {}：人员 {} 房源 {} → {}，新合同 {}，原合同已终止，旧房源已回池",
                e.getExchangeNo(), e.getPersonId(), e.getOldHouseId(), e.getNewHouseId(),
                newContractId);
        return ExchangeVO.from(e);
    }

    /**
     * 生成换房后的新合同。
     *
     * <p>规则：<b>延续原合同的止租日与租金</b>，只换房源与空间；
     * 租期起始日为换房当日。新合同 {@code parentContractId} 指向原合同，便于追溯链条。
     */
    private Long createNewContract(BizExchange e, BizContract oldCt, AssetHouse newHouse) {
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizContract nc = new BizContract();
        nc.setId(id);
        nc.setTenantId(oldCt.getTenantId());
        nc.setContractNo("BC" + id);
        nc.setContractType(oldCt.getContractType());
        nc.setTemplateId(oldCt.getTemplateId());
        nc.setOrgId(oldCt.getOrgId());
        nc.setAccountSetId(oldCt.getAccountSetId());
        nc.setLesseePersonId(oldCt.getLesseePersonId());
        nc.setLesseeName(oldCt.getLesseeName());
        nc.setLesseePhone(oldCt.getLesseePhone());
        nc.setLesseeIdCardMask(oldCt.getLesseeIdCardMask());
        nc.setLessorOrgId(oldCt.getLessorOrgId());

        // 换房核心：房源与空间换成新的
        nc.setHouseId(e.getNewHouseId());
        nc.setSpaceId(newHouse.getSpaceId());
        nc.setHouseAddress(newHouse.getHouseName());
        nc.setHouseArea(newHouse.getArea());

        // 延续止租日，起始日为换房当日
        LocalDate start = LocalDate.now();
        LocalDate end = oldCt.getLeaseEnd();
        nc.setLeaseStart(start);
        nc.setLeaseEnd(end);
        if (end != null && end.isAfter(start)) {
            long months = ChronoUnit.MONTHS.between(start, end);
            nc.setLeaseMonths((int) Math.max(1, months));
        } else {
            nc.setLeaseMonths(1);
        }

        nc.setRentPrice(oldCt.getRentPrice());
        nc.setRentUnit(oldCt.getRentUnit());
        nc.setMonthlyRent(oldCt.getMonthlyRent());
        nc.setDepositAmount(oldCt.getDepositAmount());
        nc.setSubsidyAmount(oldCt.getSubsidyAmount());
        nc.setActualPay(oldCt.getActualPay());
        nc.setPayCycle(oldCt.getPayCycle());
        nc.setPayDay(oldCt.getPayDay());
        nc.setLateFeeRate(oldCt.getLateFeeRate());
        nc.setSignType(oldCt.getSignType());

        // 换房非新签，直接履约中
        nc.setContractStatus(ContractStatus.EFFECTIVE.name());
        nc.setParentContractId(oldCt.getId());
        nc.setAutoGrant(oldCt.getAutoGrant());
        nc.setAutoExpire(oldCt.getAutoExpire());
        nc.setArrearsStop(oldCt.getArrearsStop());
        nc.setRemark("换房生成（换房单 " + e.getExchangeNo() + "）");
        nc.setIsDeleted(0);
        nc.setCreateTime(now);
        nc.setUpdateTime(now);
        contractMapper.insert(nc);
        log.info("换房生成新合同 {}：房源 {} 租期 {}~{}", nc.getContractNo(),
                e.getNewHouseId(), start, end);
        return id;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExchangeVO markNoExchange(Long id, String reason) {
        BizExchange e = require(id);
        if (e.getIsForced() == null || e.getIsForced() != 1) {
            throw BizException.stateConflict(
                    "仅「应当换房」的单据可标记应换不换（当前未标记为应换房）");
        }
        e.setNoExchangeFlag(1);
        BigDecimal mult = cfgDec(ConfigKeys.EXCHANGE_NO_EXCHANGE_MULTIPLIER,
                DEFAULT_NO_EXCHANGE_MULTIPLIER);
        e.setRentMultiplier(mult);
        if (reason != null && !reason.isBlank()) {
            e.setExchangeReason((e.getExchangeReason() == null ? "" : e.getExchangeReason())
                    + "｜应换不换：" + reason);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.warn("⚠️ 换房单 {} 标记「应换不换」，租金倍率调整为 {}（重庆政策）",
                e.getExchangeNo(), e.getRentMultiplier());
        return ExchangeVO.from(e);
    }

    @Override
    public int countCompleted(Long oldContractId) {
        Long n = mapper.selectCount(new LambdaQueryWrapper<BizExchange>()
                .eq(BizExchange::getOldContractId, oldContractId)
                .eq(BizExchange::getExchangeStatus, ExchangeStatus.COMPLETED.name()));
        return n == null ? 0 : n.intValue();
    }

    // ==================== 内部 ====================

    private BizExchange require(Long id) {
        BizExchange e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("换房单");
        }
        return e;
    }

    private static void transition(BizExchange e, ExchangeStatus target) {
        ExchangeStatus from;
        try {
            from = ExchangeStatus.valueOf(e.getExchangeStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("换房单状态非法: " + e.getExchangeStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ExchangeStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "换房状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setExchangeStatus(target.name());
    }
}
