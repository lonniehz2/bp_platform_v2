package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.CreditStatus;
import com.yundao.bp.biz.constant.SanctionType;
import com.yundao.bp.biz.constant.ViolationType;
import com.yundao.bp.biz.dto.CreditCreateCmd;
import com.yundao.bp.biz.dto.CreditVO;
import com.yundao.bp.biz.entity.BizCreditRecord;
import com.yundao.bp.biz.mapper.BizCreditRecordMapper;
import com.yundao.bp.biz.service.CreditService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.constant.ConfigKeys;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 信用惩戒实现。
 *
 * <p><b>限制申请年限</b>：严重违规默认 5 年（政策常见口径），
 * 由 {@code BAN_APPLY} 措施触发，起止日自动计算。
 */
@Service
public class CreditServiceImpl implements CreditService {

    private static final Logger log = LoggerFactory.getLogger(CreditServiceImpl.class);

    /** 严重违规默认限制年限（可被系统参数覆盖） */
    private static final int DEFAULT_SEVERE_BAN_YEARS = 5;
    /** 一般违规默认限制年限（可被系统参数覆盖） */
    private static final int DEFAULT_BAN_YEARS = 1;
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


    private final BizCreditRecordMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public CreditServiceImpl(BizCreditRecordMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CreditVO record(CreditCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        ViolationType vt;
        try {
            vt = ViolationType.valueOf(cmd.violationType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("违规类型不合法: " + cmd.violationType());
        }
        SanctionType sa;
        try {
            sa = SanctionType.valueOf(cmd.sanctionType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("惩戒措施不合法: " + cmd.sanctionType());
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizCreditRecord e = new BizCreditRecord();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setRecordNo("CR" + id);
        e.setPersonId(cmd.personId());
        e.setBizType(cmd.bizType());
        e.setBizId(cmd.bizId());
        e.setViolationType(vt.name());
        e.setViolationDesc(cmd.violationDesc());
        e.setEvidenceUrl(cmd.evidenceUrl());
        e.setSanctionType(sa.name());

        // 限制申请：计算年限与起止日
        if (sa.needsBanYears()) {
            int years = cmd.banYears() != null && cmd.banYears() > 0
                    ? cmd.banYears()
                    : (vt.severe()
                            ? cfgInt(ConfigKeys.CREDIT_BAN_YEARS_SEVERE,
                                    DEFAULT_SEVERE_BAN_YEARS)
                            : cfgInt(ConfigKeys.CREDIT_BAN_YEARS_NORMAL,
                                    DEFAULT_BAN_YEARS));
            LocalDate start = LocalDate.now();
            e.setBanYears(years);
            e.setBanStartDate(start);
            e.setBanEndDate(start.plusYears(years));
            log.info("信用惩戒：人员 {} 违规「{}」→ 限制申请 {} 年（至 {}）",
                    cmd.personId(), vt.label(), years, e.getBanEndDate());
        }

        // 推送信用平台
        boolean push = Boolean.TRUE.equals(cmd.pushToPlatform())
                || sa == SanctionType.CREDIT_PLATFORM;
        e.setPushStatus(push ? "PENDING" : "NONE");
        e.setPushPlatform(cmd.pushPlatform());

        e.setDecideOrgId(cmd.decideOrgId());
        e.setDecideUserId(cmd.decideUserId());
        e.setDecideTime(now);
        e.setLegalDocNo(cmd.legalDocNo());
        e.setStatus(CreditStatus.EFFECTIVE.name());
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        log.info("信用记录 {}：人员 {} 违规 {} 惩戒 {}", e.getRecordNo(), cmd.personId(),
                vt.label(), sa.label());
        return CreditVO.from(e);
    }

    @Override
    public CreditVO get(Long id) {
        return CreditVO.from(require(id));
    }

    @Override
    public PageResult<CreditVO> page(long pageNum, long pageSize, Long personId,
                                     String violationType, String status) {
        LambdaQueryWrapper<BizCreditRecord> qw = new LambdaQueryWrapper<BizCreditRecord>()
                .eq(personId != null, BizCreditRecord::getPersonId, personId)
                .eq(violationType != null && !violationType.isBlank(),
                        BizCreditRecord::getViolationType, violationType)
                .eq(status != null && !status.isBlank(), BizCreditRecord::getStatus, status)
                .orderByDesc(BizCreditRecord::getId);
        IPage<BizCreditRecord> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<CreditVO> rows = page.getRecords().stream().map(CreditVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public List<CreditVO> listByPerson(Long personId) {
        return mapper.selectList(new LambdaQueryWrapper<BizCreditRecord>()
                        .eq(BizCreditRecord::getPersonId, personId)
                        .orderByDesc(BizCreditRecord::getId))
                .stream().map(CreditVO::from).toList();
    }

    @Override
    public void checkApplyBan(Long personId) {
        if (personId == null) {
            return;
        }
        LocalDate today = LocalDate.now();
        List<BizCreditRecord> bans = mapper.selectList(
                new LambdaQueryWrapper<BizCreditRecord>()
                        .eq(BizCreditRecord::getPersonId, personId)
                        .eq(BizCreditRecord::getStatus, CreditStatus.EFFECTIVE.name())
                        .eq(BizCreditRecord::getSanctionType, SanctionType.BAN_APPLY.name())
                        .ge(BizCreditRecord::getBanEndDate, today));
        if (bans.isEmpty()) {
            return;
        }
        BizCreditRecord worst = bans.stream()
                .max((a, b) -> a.getBanEndDate().compareTo(b.getBanEndDate()))
                .orElse(bans.get(0));
        ViolationType vt = ViolationType.OTHER;
        try {
            vt = ViolationType.valueOf(worst.getViolationType());
        } catch (IllegalArgumentException ignored) {
            // 保持 OTHER
        }
        throw BizException.stateConflict(
                "该人员因「" + vt.label() + "」被限制申请，解禁日期 " + worst.getBanEndDate()
                        + "（信用记录 " + worst.getRecordNo() + "），暂不能申请保障房");
    }

    @Override
    public boolean isUnderBan(Long personId) {
        if (personId == null) {
            return false;
        }
        Long n = mapper.selectCount(new LambdaQueryWrapper<BizCreditRecord>()
                .eq(BizCreditRecord::getPersonId, personId)
                .eq(BizCreditRecord::getStatus, CreditStatus.EFFECTIVE.name())
                .eq(BizCreditRecord::getSanctionType, SanctionType.BAN_APPLY.name())
                .ge(BizCreditRecord::getBanEndDate, LocalDate.now()));
        return n != null && n > 0;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CreditVO expire(Long id) {
        BizCreditRecord e = require(id);
        transition(e, CreditStatus.EXPIRED);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return CreditVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CreditVO revoke(Long id, String reason) {
        BizCreditRecord e = require(id);
        transition(e, CreditStatus.REVOKED);
        if (reason != null && !reason.isBlank()) {
            e.setRemark((e.getRemark() == null ? "" : e.getRemark()) + "｜撤销原因：" + reason);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("信用记录 {} 已撤销：{}", e.getRecordNo(), reason);
        return CreditVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CreditVO markPushed(Long id, boolean success, String platform) {
        BizCreditRecord e = require(id);
        e.setPushStatus(success ? "PUSHED" : "FAILED");
        e.setPushTime(LocalDateTime.now());
        if (platform != null && !platform.isBlank()) {
            e.setPushPlatform(platform);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return CreditVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int scanExpired() {
        LocalDate today = LocalDate.now();
        List<BizCreditRecord> list = mapper.selectList(
                new LambdaQueryWrapper<BizCreditRecord>()
                        .eq(BizCreditRecord::getStatus, CreditStatus.EFFECTIVE.name())
                        .isNotNull(BizCreditRecord::getBanEndDate)
                        .lt(BizCreditRecord::getBanEndDate, today));
        int n = 0;
        for (BizCreditRecord e : list) {
            e.setStatus(CreditStatus.EXPIRED.name());
            e.setUpdateTime(LocalDateTime.now());
            mapper.updateById(e);
            n++;
        }
        if (n > 0) {
            log.info("信用限制期满解除 {} 条", n);
        }
        return n;
    }

    // ==================== 内部 ====================

    private BizCreditRecord require(Long id) {
        BizCreditRecord e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("信用记录");
        }
        return e;
    }

    private static void transition(BizCreditRecord e, CreditStatus target) {
        CreditStatus from;
        try {
            from = CreditStatus.valueOf(e.getStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("信用记录状态非法: " + e.getStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!CreditStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "信用记录状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setStatus(target.name());
    }
}
