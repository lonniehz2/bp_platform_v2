# -*- coding: utf-8 -*-
"""生成复议服务 + 控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/service/AppealService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.AppealCreateCmd;
import com.yundao.bp.biz.dto.AppealDecisionCmd;
import com.yundao.bp.biz.dto.AppealVO;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 申诉/异议（复议）服务。
 *
 * <p>⭐ <b>合规意义（决策 D28）</b>：保障房管理可作出「审核不通过 / 年审调租 / 年审退出」
 * 等不利决定，住户必须有<b>申诉与救济通道</b>，否则程序不合法。
 *
 * <p><b>流程</b>：提出 → 受理 → 调查 → 决定（异议成立 / 不成立）→ 告知。
 *
 * <p><b>结果影响</b>：{@code UPHELD} 时可选择恢复资格（RESTORE）、
 * 取消资格（CANCEL）、调整标准（ADJUST）或仅确认无影响（NONE）。
 */
public interface AppealService {

    /** 提出申诉/异议（超出期限拒绝）。 */
    AppealVO submit(AppealCreateCmd cmd);

    AppealVO get(Long id);

    PageResult<AppealVO> page(long pageNum, long pageSize, Long personId, String bizType,
                              String status);

    /** 某业务对象（如年审单）的申诉记录。 */
    List<AppealVO> listByBiz(String bizType, Long bizId);

    /** 受理。 */
    AppealVO accept(Long id, Long acceptUserId);

    /** 进入调查。 */
    AppealVO investigate(Long id, Long handleUserId);

    /** 作出决定（异议成立/不成立 + 结果影响）。 */
    AppealVO decide(Long id, AppealDecisionCmd cmd);

    /** 撤回。 */
    AppealVO withdraw(Long id, String reason);

    /** 标记已告知。 */
    AppealVO markNotified(Long id);

    /** 扫描并标记超期未受理的申诉，返回处理数。 */
    int markTimeout();
}
'''

FILES['biz/service/impl/AppealServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.AppealResultEffect;
import com.yundao.bp.biz.constant.AppealStatus;
import com.yundao.bp.biz.dto.AppealCreateCmd;
import com.yundao.bp.biz.dto.AppealDecisionCmd;
import com.yundao.bp.biz.dto.AppealVO;
import com.yundao.bp.biz.entity.BizAppeal;
import com.yundao.bp.biz.mapper.BizAppealMapper;
import com.yundao.bp.biz.service.AppealService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 申诉/异议实现。
 *
 * <p><b>期限控制</b>：{@code deadline_time} 之前未提出则置 {@code TIMEOUT}。
 * <b>同一业务对象同一申请人只能有一条未终结申诉</b>，防止重复申诉。
 */
@Service
public class AppealServiceImpl implements AppealService {

    private static final Logger log = LoggerFactory.getLogger(AppealServiceImpl.class);

    /** 默认申诉期限（自然日） */
    private static final int DEFAULT_DAYS = 10;

    private final BizAppealMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public AppealServiceImpl(BizAppealMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO submit(AppealCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        // 同业务对象 + 同申请人 只能有一条未终结申诉
        Long open = mapper.selectCount(new LambdaQueryWrapper<BizAppeal>()
                .eq(BizAppeal::getBizType, cmd.bizType())
                .eq(BizAppeal::getBizId, cmd.bizId())
                .eq(BizAppeal::getPersonId, cmd.personId())
                .in(BizAppeal::getAppealStatus, List.of(AppealStatus.SUBMITTED.name(),
                        AppealStatus.ACCEPTED.name(), AppealStatus.INVESTIGATING.name())));
        if (open != null && open > 0) {
            throw BizException.stateConflict("该业务对象已有处理中的申诉，请等待办结");
        }

        int days = cmd.daysFromNow() == null || cmd.daysFromNow() <= 0
                ? DEFAULT_DAYS : cmd.daysFromNow();
        LocalDateTime now = LocalDateTime.now();
        long id = idGen.nextId();
        BizAppeal e = new BizAppeal();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setAppealNo("AP" + id);
        e.setBizType(cmd.bizType());
        e.setBizId(cmd.bizId());
        e.setPersonId(cmd.personId());
        e.setOrgId(cmd.orgId());
        e.setAppealType(cmd.appealType());
        e.setAppealReason(cmd.appealReason());
        e.setAppealEvidence(cmd.appealEvidence());
        e.setDeadlineTime(now.plusDays(days));
        e.setAppealTime(now);
        e.setAppealStatus(AppealStatus.SUBMITTED.name());
        e.setNotifyStatus("PENDING");
        e.setIsDeleted(0);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        log.info("申诉 {} 提出：{} #{}（{}），期限 {}",
                e.getAppealNo(), cmd.bizType(), cmd.bizId(),
                "OBJECTION".equals(cmd.appealType()) ? "公示异议" : "申诉", e.getDeadlineTime());
        return AppealVO.from(e);
    }

    @Override
    public AppealVO get(Long id) {
        return AppealVO.from(require(id));
    }

    @Override
    public PageResult<AppealVO> page(long pageNum, long pageSize, Long personId, String bizType,
                                     String status) {
        LambdaQueryWrapper<BizAppeal> qw = new LambdaQueryWrapper<BizAppeal>()
                .eq(personId != null, BizAppeal::getPersonId, personId)
                .eq(bizType != null && !bizType.isBlank(), BizAppeal::getBizType, bizType)
                .eq(status != null && !status.isBlank(), BizAppeal::getAppealStatus, status)
                .orderByDesc(BizAppeal::getId);
        IPage<BizAppeal> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<AppealVO> rows = page.getRecords().stream().map(AppealVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public List<AppealVO> listByBiz(String bizType, Long bizId) {
        return mapper.selectList(new LambdaQueryWrapper<BizAppeal>()
                        .eq(BizAppeal::getBizType, bizType)
                        .eq(BizAppeal::getBizId, bizId)
                        .orderByDesc(BizAppeal::getId))
                .stream().map(AppealVO::from).toList();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO accept(Long id, Long acceptUserId) {
        BizAppeal e = require(id);
        // 超过期限不可受理
        if (e.getDeadlineTime() != null && LocalDateTime.now().isAfter(e.getDeadlineTime())) {
            throw BizException.stateConflict(
                    "已超过申诉期限（" + e.getDeadlineTime() + "），不予受理");
        }
        transition(e, AppealStatus.ACCEPTED);
        e.setAcceptTime(LocalDateTime.now());
        e.setAcceptUserId(acceptUserId);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO investigate(Long id, Long handleUserId) {
        BizAppeal e = require(id);
        transition(e, AppealStatus.INVESTIGATING);
        e.setHandleUserId(handleUserId);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO decide(Long id, AppealDecisionCmd cmd) {
        BizAppeal e = require(id);
        AppealStatus target;
        try {
            target = AppealStatus.valueOf(cmd.decision());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("决定结论不合法: " + cmd.decision());
        }
        if (target != AppealStatus.UPHELD && target != AppealStatus.REJECTED) {
            throw BizException.paramInvalid("决定结论只能是 UPHELD 或 REJECTED");
        }
        AppealResultEffect re;
        try {
            re = AppealResultEffect.valueOf(cmd.resultEffect());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("结果影响不合法: " + cmd.resultEffect());
        }
        // 异议不成立却要"恢复资格"是矛盾的
        if (target == AppealStatus.REJECTED && re.changesOutcome()) {
            throw BizException.paramInvalid(
                    "异议不成立时结果影响应为 NONE（不能恢复/取消资格或调整标准）");
        }

        transition(e, target);
        e.setHandleResult(cmd.handleResult());
        e.setReviewOpinion(cmd.reviewOpinion());
        e.setResultEffect(re.name());
        e.setHandleUserId(cmd.handleUserId() == null ? e.getHandleUserId() : cmd.handleUserId());
        e.setHandleTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("申诉 {} 决定：{}，影响 {}（{}）", e.getAppealNo(),
                target.label(), re.label(),
                cmd.reviewOpinion() == null ? "" : cmd.reviewOpinion());
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO withdraw(Long id, String reason) {
        BizAppeal e = require(id);
        transition(e, AppealStatus.WITHDRAWN);
        if (reason != null && !reason.isBlank()) {
            e.setReviewOpinion("撤回原因：" + reason);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO markNotified(Long id) {
        BizAppeal e = require(id);
        if (!appealStatusOf(e).isTerminal()) {
            throw BizException.stateConflict("申诉尚未办结，不能告知结果");
        }
        e.setNotifyStatus("SENT");
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int markTimeout() {
        List<BizAppeal> list = mapper.selectList(new LambdaQueryWrapper<BizAppeal>()
                .eq(BizAppeal::getAppealStatus, AppealStatus.SUBMITTED.name())
                .lt(BizAppeal::getDeadlineTime, LocalDateTime.now()));
        int n = 0;
        for (BizAppeal e : list) {
            e.setAppealStatus(AppealStatus.TIMEOUT.name());
            e.setUpdateTime(LocalDateTime.now());
            mapper.updateById(e);
            n++;
        }
        if (n > 0) {
            log.warn("申诉超期标记 {} 条", n);
        }
        return n;
    }

    // ==================== 内部 ====================

    private BizAppeal require(Long id) {
        BizAppeal e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("申诉单");
        }
        return e;
    }

    private static AppealStatus appealStatusOf(BizAppeal e) {
        try {
            return AppealStatus.valueOf(e.getAppealStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("申诉状态非法: " + e.getAppealStatus());
        }
    }

    private static void transition(BizAppeal e, AppealStatus target) {
        AppealStatus from = appealStatusOf(e);
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!AppealStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "申诉状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setAppealStatus(target.name());
    }
}
'''

FILES['biz/controller/AppealController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.AppealCreateCmd;
import com.yundao.bp.biz.dto.AppealDecisionCmd;
import com.yundao.bp.biz.dto.AppealVO;
import com.yundao.bp.biz.service.AppealService;
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
 * 申诉/异议（复议）接口（BC-05）。
 *
 * <p>⭐ 保障房法定救济通道：对审核、年审核查、公示、退出决定不服可申诉。
 */
@RestController
@RequestMapping("/api/v1/appeals")
public class AppealController {

    private final AppealService service;

    public AppealController(AppealService service) {
        this.service = service;
    }

    @PostMapping
    public R<AppealVO> submit(@Valid @RequestBody AppealCreateCmd cmd) {
        return R.ok(service.submit(cmd));
    }

    @GetMapping("/{id}")
    public R<AppealVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<AppealVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                        @RequestParam(defaultValue = "20") long pageSize,
                                        @RequestParam(required = false) Long personId,
                                        @RequestParam(required = false) String bizType,
                                        @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, personId, bizType, status));
    }

    /** 某业务对象的申诉记录。 */
    @GetMapping("/by-biz")
    public R<List<AppealVO>> byBiz(@RequestParam String bizType, @RequestParam Long bizId) {
        return R.ok(service.listByBiz(bizType, bizId));
    }

    @PostMapping("/{id}/accept")
    public R<AppealVO> accept(@PathVariable Long id,
                              @RequestBody(required = false) UserCmd cmd) {
        return R.ok(service.accept(id, cmd == null ? null : cmd.userId()));
    }

    @PostMapping("/{id}/investigate")
    public R<AppealVO> investigate(@PathVariable Long id,
                                   @RequestBody(required = false) UserCmd cmd) {
        return R.ok(service.investigate(id, cmd == null ? null : cmd.userId()));
    }

    /** 作出决定。 */
    @PostMapping("/{id}/decide")
    public R<AppealVO> decide(@PathVariable Long id,
                              @Valid @RequestBody AppealDecisionCmd cmd) {
        return R.ok(service.decide(id, cmd));
    }

    @PostMapping("/{id}/withdraw")
    public R<AppealVO> withdraw(@PathVariable Long id,
                                @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.withdraw(id, cmd == null ? null : cmd.reason()));
    }

    /** 告知结果。 */
    @PostMapping("/{id}/notify")
    public R<AppealVO> notifyResult(@PathVariable Long id) {
        return R.ok(service.markNotified(id));
    }

    /** 超期标记扫描。 */
    @PostMapping("/mark-timeout")
    public R<Integer> markTimeout() {
        return R.ok(service.markTimeout());
    }

    public record UserCmd(Long userId) {
    }

    public record ReasonCmd(String reason) {
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
