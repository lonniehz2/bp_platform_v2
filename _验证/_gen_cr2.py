# -*- coding: utf-8 -*-
"""生成信用记录服务 + 控制器（含限制申请校验）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/service/CreditService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.CreditCreateCmd;
import com.yundao.bp.biz.dto.CreditVO;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 信用惩戒服务。
 *
 * <p>⭐ <b>核心作用（决策 D30）</b>：失信记录必须能<b>真正阻止再申请</b>，
 * 否则惩戒形同虚设。申请受理前应调用 {@link #checkApplyBan} 校验。
 */
public interface CreditService {

    /** 记入失信（自动计算限制申请起止日）。 */
    CreditVO record(CreditCreateCmd cmd);

    CreditVO get(Long id);

    PageResult<CreditVO> page(long pageNum, long pageSize, Long personId, String violationType,
                              String status);

    /** 某人的全部信用记录。 */
    List<CreditVO> listByPerson(Long personId);

    /**
     * 校验是否处于限制申请期。
     *
     * @throws com.yundao.bp.common.exception.BizException 处于限制期则抛出（含解禁日期）
     */
    void checkApplyBan(Long personId);

    /** 当前是否处于限制申请期（不抛异常）。 */
    boolean isUnderBan(Long personId);

    /** 解除（期满）。 */
    CreditVO expire(Long id);

    /** 撤销（复议/纠错）。 */
    CreditVO revoke(Long id, String reason);

    /** 标记推送信用平台成功/失败。 */
    CreditVO markPushed(Long id, boolean success, String platform);

    /** 扫描已过限制期的记录置为已解除，返回处理数。 */
    int scanExpired();
}
'''

FILES['biz/service/impl/CreditServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

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

    /** 严重违规默认限制年限 */
    private static final int DEFAULT_SEVERE_BAN_YEARS = 5;
    /** 一般违规默认限制年限 */
    private static final int DEFAULT_BAN_YEARS = 1;

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
                    : (vt.severe() ? DEFAULT_SEVERE_BAN_YEARS : DEFAULT_BAN_YEARS);
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
'''

FILES['biz/controller/CreditController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.CreditCreateCmd;
import com.yundao.bp.biz.dto.CreditVO;
import com.yundao.bp.biz.service.CreditService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 信用惩戒接口（BC-05）。
 *
 * <p>⭐ 失信记录会真正限制再申请（{@code checkApplyBan}）。
 */
@RestController
@RequestMapping("/api/v1/credits")
public class CreditController {

    private final CreditService service;

    public CreditController(CreditService service) {
        this.service = service;
    }

    @PostMapping
    public R<CreditVO> record(@Valid @RequestBody CreditCreateCmd cmd) {
        return R.ok(service.record(cmd));
    }

    @GetMapping("/{id}")
    public R<CreditVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<CreditVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                        @RequestParam(defaultValue = "20") long pageSize,
                                        @RequestParam(required = false) Long personId,
                                        @RequestParam(required = false) String violationType,
                                        @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, personId, violationType, status));
    }

    @GetMapping("/by-person/{personId}")
    public R<List<CreditVO>> byPerson(@PathVariable Long personId) {
        return R.ok(service.listByPerson(personId));
    }

    /**
     * 申请前校验：是否处于限制申请期。
     *
     * <p>处于限制期返回 false 并给出解禁日期。
     */
    @GetMapping("/check-ban")
    public R<String> checkBan(@RequestParam Long personId) {
        if (service.isUnderBan(personId)) {
            service.checkApplyBan(personId);
        }
        return R.ok("未处于限制申请期，可正常申请");
    }

    /** 解除（期满）。 */
    @PostMapping("/{id}/expire")
    public R<CreditVO> expire(@PathVariable Long id) {
        return R.ok(service.expire(id));
    }

    /** 撤销（复议/纠错）。 */
    @PostMapping("/{id}/revoke")
    public R<CreditVO> revoke(@PathVariable Long id,
                              @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.revoke(id, cmd == null ? null : cmd.reason()));
    }

    /** 标记推送信用平台结果。 */
    @PostMapping("/{id}/push")
    public R<CreditVO> push(@PathVariable Long id,
                            @RequestBody(required = false) PushCmd cmd) {
        return R.ok(service.markPushed(id,
                cmd == null || cmd.success(),
                cmd == null ? null : cmd.platform()));
    }

    /** 期满扫描。 */
    @PostMapping("/scan-expired")
    public R<Integer> scanExpired() {
        return R.ok(service.scanExpired());
    }

    public record ReasonCmd(String reason) {
    }

    public record PushCmd(Boolean success, String platform) {
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('生成 %d 个文件' % count)
