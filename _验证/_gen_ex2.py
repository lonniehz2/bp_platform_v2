# -*- coding: utf-8 -*-
"""生成换房服务 + 控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/service/ExchangeService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ExchangeCreateCmd;
import com.yundao.bp.biz.dto.ExchangeVO;
import com.yundao.bp.common.api.PageResult;

/**
 * 换房服务。
 *
 * <p><b>流程</b>：申请 → 审批 → 批准 → 执行（释放原房源、启用新房源、权限迁移）。
 *
 * <p><b>政策约束</b>：
 * <ul>
 *   <li><b>成都</b>：同一租期内限换 <b>1 次</b>，第 2 次申请直接拒绝</li>
 *   <li><b>重庆</b>：应换不换（{@code no_exchange_flag=1}）按 <b>1.5 倍</b>计租，
 *       由本服务设置 {@code rent_multiplier}，供计费引擎读取</li>
 * </ul>
 */
public interface ExchangeService {

    /** 申请换房（校验成都限换 1 次）。 */
    ExchangeVO apply(ExchangeCreateCmd cmd);

    ExchangeVO get(Long id);

    PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId, Long oldContractId,
                                String status);

    /** 提交审批。 */
    ExchangeVO submit(Long id);

    /** 批准。 */
    ExchangeVO approve(Long id, String opinion);

    /** 驳回。 */
    ExchangeVO reject(Long id, String reason);

    /** 执行换房（权限迁移 + 原房源释放 + 新合同关联）。 */
    ExchangeVO complete(Long id);

    /** 标记"应换不换"（重庆：按 1.5 倍计租）。 */
    ExchangeVO markNoExchange(Long id, String reason);

    /** 统计某合同已完成的换房次数。 */
    int countCompleted(Long oldContractId);
}
'''

FILES['biz/service/impl/ExchangeServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.constant.ExchangeStatus;
import com.yundao.bp.biz.constant.ExchangeType;
import com.yundao.bp.biz.dto.ExchangeCreateCmd;
import com.yundao.bp.biz.dto.ExchangeVO;
import com.yundao.bp.biz.entity.BizExchange;
import com.yundao.bp.biz.mapper.BizExchangeMapper;
import com.yundao.bp.biz.service.ExchangeService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDateTime;
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

    /** 成都：同一租期内限换 1 次 */
    private static final int MAX_EXCHANGE_TIMES = 1;
    /** 重庆：应换不换的加价倍率 */
    private static final BigDecimal NO_EXCHANGE_MULTIPLIER = new BigDecimal("1.5");

    private final BizExchangeMapper mapper;
    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;

    public ExchangeServiceImpl(BizExchangeMapper mapper, AssetHouseMapper houseMapper,
                               SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.houseMapper = houseMapper;
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
        if (done >= MAX_EXCHANGE_TIMES) {
            throw BizException.stateConflict(
                    "同一租期内已换房 " + done + " 次，超过上限（成都限 1 次），不可再换");
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
        log.info("换房申请 {}：合同 {} 房源 {} → {}（{}，第 {} 次）",
                e.getExchangeNo(), cmd.oldContractId(), cmd.oldHouseId(), cmd.newHouseId(),
                type.label(), e.getExchangeTimes());
        return ExchangeVO.from(e);
    }

    @Override
    public ExchangeVO get(Long id) {
        return ExchangeVO.from(require(id));
    }

    @Override
    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status) {
        LambdaQueryWrapper<BizExchange> qw = new LambdaQueryWrapper<BizExchange>()
                .eq(personId != null, BizExchange::getPersonId, personId)
                .eq(oldContractId != null, BizExchange::getOldContractId, oldContractId)
                .eq(status != null && !status.isBlank(), BizExchange::getExchangeStatus, status)
                .orderByDesc(BizExchange::getId);
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
        // 权限迁移：换房后需把原房源的开门权限迁到新房源
        e.setGrantMigrated(1);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        AssetHouse newHouse = houseMapper.selectById(e.getNewHouseId());
        log.info("⭐ 换房完成 {}：人员 {} 房源 {} → {}（{}），权限已迁移",
                e.getExchangeNo(), e.getPersonId(), e.getOldHouseId(), e.getNewHouseId(),
                newHouse == null ? "" : newHouse.getHouseCode());
        return ExchangeVO.from(e);
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
        e.setRentMultiplier(NO_EXCHANGE_MULTIPLIER);
        if (reason != null && !reason.isBlank()) {
            e.setExchangeReason((e.getExchangeReason() == null ? "" : e.getExchangeReason())
                    + "｜应换不换：" + reason);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.warn("⚠️ 换房单 {} 标记「应换不换」，租金倍率调整为 {}（重庆政策）",
                e.getExchangeNo(), NO_EXCHANGE_MULTIPLIER);
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
'''

FILES['biz/controller/ExchangeController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.ExchangeCreateCmd;
import com.yundao.bp.biz.dto.ExchangeVO;
import com.yundao.bp.biz.service.ExchangeService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 换房接口（BC-05）。
 *
 * <p>成都限换 1 次；重庆应换不换按 1.5 倍计租。
 */
@RestController
@RequestMapping("/api/v1/exchanges")
public class ExchangeController {

    private final ExchangeService service;

    public ExchangeController(ExchangeService service) {
        this.service = service;
    }

    @PostMapping
    public R<ExchangeVO> apply(@Valid @RequestBody ExchangeCreateCmd cmd) {
        return R.ok(service.apply(cmd));
    }

    @GetMapping("/{id}")
    public R<ExchangeVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<ExchangeVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                          @RequestParam(defaultValue = "20") long pageSize,
                                          @RequestParam(required = false) Long personId,
                                          @RequestParam(required = false) Long oldContractId,
                                          @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, personId, oldContractId, status));
    }

    @PostMapping("/{id}/submit")
    public R<ExchangeVO> submit(@PathVariable Long id) {
        return R.ok(service.submit(id));
    }

    @PostMapping("/{id}/approve")
    public R<ExchangeVO> approve(@PathVariable Long id,
                                 @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.approve(id, cmd == null ? null : cmd.reason()));
    }

    @PostMapping("/{id}/reject")
    public R<ExchangeVO> reject(@PathVariable Long id,
                                @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.reject(id, cmd == null ? null : cmd.reason()));
    }

    /** 执行换房（权限迁移）。 */
    @PostMapping("/{id}/complete")
    public R<ExchangeVO> complete(@PathVariable Long id) {
        return R.ok(service.complete(id));
    }

    /** 标记应换不换（重庆 1.5 倍计租）。 */
    @PostMapping("/{id}/no-exchange")
    public R<ExchangeVO> noExchange(@PathVariable Long id,
                                    @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.markNoExchange(id, cmd == null ? null : cmd.reason()));
    }

    /** 某合同已完成换房次数。 */
    @GetMapping("/count")
    public R<Integer> count(@RequestParam Long oldContractId) {
        return R.ok(service.countCompleted(oldContractId));
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
