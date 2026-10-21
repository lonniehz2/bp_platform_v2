# -*- coding: utf-8 -*-
"""生成 biz 合同模块（服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/service/ContractService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ContractCreateCmd;
import com.yundao.bp.biz.dto.ContractVO;
import com.yundao.bp.common.api.PageResult;
import java.time.LocalDate;

/**
 * 合同服务。
 *
 * <p>生命周期：起草 → 待签约 → 签约中 → 履约中 →（续签 / 到期 / 终止）。
 */
public interface ContractService {

    /** 起草合同（DRAFT）。 */
    ContractVO create(ContractCreateCmd cmd);

    ContractVO get(Long id);

    PageResult<ContractVO> page(long pageNum, long pageSize, String contractType,
                                String status, Long houseId, Long lesseePersonId, String keyword);

    /** 提交签约：DRAFT → PENDING_SIGN。 */
    ContractVO submitSign(Long id);

    /** 发起签署：PENDING_SIGN → SIGNING。 */
    ContractVO startSigning(Long id, String signVendor);

    /** 签署完成：SIGNING → EFFECTIVE（创建时需签，纸质/PAPER 可直接生效）。 */
    ContractVO sign(Long id, String signFileUrl, String signFlowId);

    /** 续签：EFFECTIVE → RENEWING，并修订止租日与金额。 */
    ContractVO renew(Long id, LocalDate newLeaseEnd, java.math.BigDecimal newMonthlyRent);

    /** 终止（退租）：EFFECTIVE/RENEWING → TERMINATED。 */
    ContractVO terminate(Long id, String reason);

    /** 作废：DRAFT/PENDING_SIGN/SIGNING → CANCELLED。 */
    ContractVO cancel(Long id, String reason);

    /** 到期扫描：把已过止租日的履约中合同置为 EXPIRED，返回处理条数。 */
    int expireDue();
}
'''

FILES['biz/service/impl/ContractServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
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

    public ContractServiceImpl(BizContractMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
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
        BigDecimal actualPay = cmd.monthlyRent().subtract(subsidy);
        if (actualPay.compareTo(BigDecimal.ZERO) < 0) {
            throw BizException.paramInvalid("补贴不能超过月租金（实付为负）");
        }
        // 整月数（向上取整，跨月按满月算）
        long days = ChronoUnit.DAYS.between(cmd.leaseStart(), cmd.leaseEnd());
        int months = (int) Math.max(1, Math.ceil(days / 30.0));

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
        e.setRentPrice(cmd.rentPrice());
        e.setRentUnit(blankToNull(cmd.rentUnit()) == null ? "HOUSE_MONTH" : cmd.rentUnit());
        e.setMonthlyRent(cmd.monthlyRent());
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
        BizContract e = require(id);
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
            e.setMonthlyRent(newMonthlyRent);
            e.setActualPay(newMonthlyRent.subtract(nz(e.getSubsidyAmount())));
            if (e.getActualPay().compareTo(BigDecimal.ZERO) < 0) {
                throw BizException.paramInvalid("补贴不能超过月租金（实付为负）");
            }
        }
        long days = ChronoUnit.DAYS.between(e.getLeaseStart(), newLeaseEnd);
        e.setLeaseMonths((int) Math.max(1, Math.ceil(days / 30.0)));
        mapper.updateById(e);
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
            n++;
        }
        if (n > 0) {
            log.info("合同到期扫描：{} 份合同置为 EXPIRED", n);
        }
        return n;
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

    private static BigDecimal nz(BigDecimal v) {
        return v == null ? BigDecimal.ZERO : v;
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
'''

FILES['biz/controller/ContractController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.ContractCreateCmd;
import com.yundao.bp.biz.dto.ContractVO;
import com.yundao.bp.biz.service.ContractService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.time.LocalDate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 合同接口（BC-05 业务办理）。
 *
 * <p>生命周期：起草 → 提交签约 → 发起签署 → 签署生效 →（续签 / 到期 / 终止）。
 */
@RestController
@RequestMapping("/api/v1/contracts")
public class ContractController {

    private final ContractService contractService;

    public ContractController(ContractService contractService) {
        this.contractService = contractService;
    }

    @PostMapping
    public R<ContractVO> create(@Valid @RequestBody ContractCreateCmd cmd) {
        return R.ok(contractService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<ContractVO> get(@PathVariable Long id) {
        return R.ok(contractService.get(id));
    }

    @GetMapping
    public R<PageResult<ContractVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                          @RequestParam(defaultValue = "20") long pageSize,
                                          @RequestParam(required = false) String contractType,
                                          @RequestParam(required = false) String status,
                                          @RequestParam(required = false) Long houseId,
                                          @RequestParam(required = false) Long lesseePersonId,
                                          @RequestParam(required = false) String keyword) {
        return R.ok(contractService.page(pageNum, pageSize, contractType, status, houseId,
                lesseePersonId, keyword));
    }

    @PostMapping("/{id}/submit-sign")
    public R<ContractVO> submitSign(@PathVariable Long id) {
        return R.ok(contractService.submitSign(id));
    }

    @PostMapping("/{id}/start-signing")
    public R<ContractVO> startSigning(@PathVariable Long id,
                                      @RequestBody(required = false) SignCmd cmd) {
        return R.ok(contractService.startSigning(id, cmd == null ? null : cmd.signVendor()));
    }

    /** 签署生效。 */
    @PostMapping("/{id}/sign")
    public R<ContractVO> sign(@PathVariable Long id, @RequestBody(required = false) SignCmd cmd) {
        return R.ok(contractService.sign(id,
                cmd == null ? null : cmd.signFileUrl(),
                cmd == null ? null : cmd.signFlowId()));
    }

    /** 续签。 */
    @PostMapping("/{id}/renew")
    public R<ContractVO> renew(@PathVariable Long id, @RequestBody RenewCmd cmd) {
        return R.ok(contractService.renew(id, cmd.newLeaseEnd(), cmd.newMonthlyRent()));
    }

    /** 终止（退租）。 */
    @PostMapping("/{id}/terminate")
    public R<ContractVO> terminate(@PathVariable Long id,
                                   @RequestBody(required = false) SignCmd cmd) {
        return R.ok(contractService.terminate(id, cmd == null ? null : cmd.reason()));
    }

    @PostMapping("/{id}/cancel")
    public R<ContractVO> cancel(@PathVariable Long id,
                                @RequestBody(required = false) SignCmd cmd) {
        return R.ok(contractService.cancel(id, cmd == null ? null : cmd.reason()));
    }

    /** 到期扫描（可挂定时任务）。 */
    @PostMapping("/expire-due")
    public R<Integer> expireDue() {
        return R.ok(contractService.expireDue());
    }

    public record SignCmd(String signVendor, String signFileUrl, String signFlowId, String reason) {
    }

    public record RenewCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate newLeaseEnd,
            BigDecimal newMonthlyRent) {
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
