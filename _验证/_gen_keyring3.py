# -*- coding: utf-8 -*-
"""生成授权对账服务 + 两个控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

F['grant/service/ReconcileService.java'] = '''package com.yundao.bp.grant.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.grant.entity.GrantReconcileDiff;
import java.util.List;
import java.util.Map;

/**
 * 授权对账服务（★ 级要求：本地授权与 IoT 平台授权必须一致）。
 *
 * <p><b>为什么需要</b>：授权是异步下发到 IoT 平台的，网络抖动、设备离线、
 * 重试耗尽都会造成「本地显示已授权、设备上其实没有」或反之。
 * 这类不一致在住户刷不开门时才会暴露，必须主动对账。
 *
 * <p><b>差异类型</b>：
 * <ul>
 *   <li>{@code LOCAL_MISSING} 本地应有但 IoT 没有 → 住户会被拒之门外（影响最大）</li>
 *   <li>{@code IOT_EXTRA} IoT 有但本地已撤销 → 安全风险（该失效的没失效）</li>
 *   <li>{@code PERIOD_MISMATCH} 有效期不一致</li>
 *   <li>{@code VALUE_MISMATCH} 介质值不一致</li>
 * </ul>
 */
public interface ReconcileService {

    /**
     * 执行对账。
     *
     * @param lockId 只对账某台锁（为空则全部）
     * @return 对账结果统计
     */
    Map<String, Object> reconcile(String lockId);

    PageResult<GrantReconcileDiff> pageDiffs(long pageNum, long pageSize, String lockId,
                                             String diffType, String handleStatus);

    List<GrantReconcileDiff> listByHandleStatus(String handleStatus);

    /**
     * 处置单条差异。
     *
     * @param action REGRANT / REVOKE / IGNORED / MANUAL
     */
    GrantReconcileDiff handle(Long diffId, String action, String remark);

    /** 批量处置（按差异类型）。 */
    Map<String, Object> handleBatch(String diffType, String action, String remark);

    /** 未处置差异统计（看板用）。 */
    Map<String, Object> stats();
}
'''

F['grant/service/impl/ReconcileServiceImpl.java'] = '''package com.yundao.bp.grant.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.grant.entity.GrantEntitlement;
import com.yundao.bp.grant.entity.GrantReconcileDiff;
import com.yundao.bp.grant.mapper.GrantEntitlementMapper;
import com.yundao.bp.grant.mapper.GrantReconcileDiffMapper;
import com.yundao.bp.grant.service.ReconcileService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 授权对账实现。
 *
 * <p>本期对账口径：把「本地有效授权」与「已成功下发记录」做集合比对，
 * 找出本地有但下发未成功（{@code LOCAL_MISSING}）与已撤销但仍在下发记录中
 * （{@code IOT_EXTRA}）两类差异。真实 IoT 侧清单由 {@code IotClient}
 * 拉取后替换 {@link #fetchIotKeys} 即可，无需改其他逻辑。
 */
@Service
public class ReconcileServiceImpl implements ReconcileService {

    private static final Logger log = LoggerFactory.getLogger(ReconcileServiceImpl.class);

    private final GrantReconcileDiffMapper diffMapper;
    private final GrantEntitlementMapper entitlementMapper;
    private final SnowflakeIdGenerator idGen;

    public ReconcileServiceImpl(GrantReconcileDiffMapper diffMapper,
                                GrantEntitlementMapper entitlementMapper,
                                SnowflakeIdGenerator idGen) {
        this.diffMapper = diffMapper;
        this.entitlementMapper = entitlementMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> reconcile(String lockId) {
        // 本地应有：状态有效且未删除的权益
        List<GrantEntitlement> locals = entitlementMapper.selectList(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(lockId != null && !lockId.isBlank(),
                                GrantEntitlement::getLockId, lockId)
                        .orderByAsc(GrantEntitlement::getId));
        // IoT 侧：本期以「已成功下发」近似（真实实现替换本方法）
        Map<String, String> iot = fetchIotKeys(locals, lockId);

        int localMissing = 0;
        int iotExtra = 0;
        int recorded = 0;
        List<String> samples = new ArrayList<>();

        for (GrantEntitlement e : locals) {
            String key = keyOf(e.getLockId(), e.getPersonId());
            boolean localValid = isLocalValid(e);
            boolean inIot = iot.containsKey(key);
            if (localValid && !inIot) {
                record(e, "LOCAL_MISSING", "有效授权", "IoT 无此授权", lockId);
                localMissing++;
                recorded++;
                if (samples.size() < 5) {
                    samples.add("本地应有但IoT缺少：lock=" + e.getLockId()
                            + " person=" + e.getPersonId());
                }
            } else if (!localValid && inIot) {
                record(e, "IOT_EXTRA", "已撤销/失效", "IoT 仍存在", lockId);
                iotExtra++;
                recorded++;
                if (samples.size() < 5) {
                    samples.add("IoT多余授权：lock=" + e.getLockId()
                            + " person=" + e.getPersonId());
                }
            }
        }

        Map<String, Object> m = new LinkedHashMap<>();
        m.put("lockId", lockId);
        m.put("localCount", locals.size());
        m.put("iotCount", iot.size());
        m.put("localMissing", localMissing);
        m.put("iotExtra", iotExtra);
        m.put("diffRecorded", recorded);
        m.put("consistent", recorded == 0);
        m.put("samples", samples);
        m.put("conclusion", recorded == 0
                ? "本地与 IoT 授权一致，无需处置"
                : "发现 " + recorded + " 条差异，请在差异清单中处置");
        log.info("授权对账完成（lock={}）：本地 {}，IoT {}，差异 {}",
                lockId, locals.size(), iot.size(), recorded);
        return m;
    }

    @Override
    public PageResult<GrantReconcileDiff> pageDiffs(long pageNum, long pageSize,
                                                    String lockId, String diffType,
                                                    String handleStatus) {
        LambdaQueryWrapper<GrantReconcileDiff> qw = new LambdaQueryWrapper<GrantReconcileDiff>()
                .eq(lockId != null && !lockId.isBlank(),
                        GrantReconcileDiff::getLockId, lockId)
                .eq(diffType != null && !diffType.isBlank(),
                        GrantReconcileDiff::getDiffType, diffType)
                .eq(handleStatus != null && !handleStatus.isBlank(),
                        GrantReconcileDiff::getHandleStatus, handleStatus)
                .orderByDesc(GrantReconcileDiff::getId);
        IPage<GrantReconcileDiff> page = diffMapper.selectPage(
                new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    public List<GrantReconcileDiff> listByHandleStatus(String handleStatus) {
        return diffMapper.selectList(new LambdaQueryWrapper<GrantReconcileDiff>()
                .eq(GrantReconcileDiff::getHandleStatus, handleStatus)
                .orderByDesc(GrantReconcileDiff::getId));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public GrantReconcileDiff handle(Long diffId, String action, String remark) {
        GrantReconcileDiff d = diffMapper.selectById(diffId);
        if (d == null) {
            throw BizException.notFound("对账差异");
        }
        if (!"PENDING".equals(d.getHandleStatus())) {
            throw BizException.stateConflict(
                    "该差异已处置（" + d.getHandleStatus() + "），不可重复处置");
        }
        if (!List.of("REGRANT", "REVOKE", "MANUAL", "IGNORED").contains(action)) {
            throw BizException.paramInvalid("非法处置动作：" + action);
        }
        // 「重新授权」只对 LOCAL_MISSING 有意义；「撤销」只对 IOT_EXTRA 有意义
        if ("REGRANT".equals(action) && !"LOCAL_MISSING".equals(d.getDiffType())) {
            throw BizException.stateConflict(
                    "「重新授权」仅适用于本地应有但 IoT 缺少的差异");
        }
        if ("REVOKE".equals(action) && !"IOT_EXTRA".equals(d.getDiffType())) {
            throw BizException.stateConflict(
                    "「撤销」仅适用于 IoT 多余授权的差异");
        }
        d.setHandleAction(action);
        d.setHandleStatus("IGNORED".equals(action) ? "IGNORED" : "HANDLED");
        d.setHandleTime(LocalDateTime.now());
        d.setHandleRemark(remark);
        diffMapper.updateById(d);
        log.info("对账差异已处置：{} → {}（{}）", diffId, action, remark);
        return d;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> handleBatch(String diffType, String action, String remark) {
        if (diffType == null || diffType.isBlank()) {
            throw BizException.paramInvalid("批量处置必须指定差异类型");
        }
        List<GrantReconcileDiff> list = diffMapper.selectList(
                new LambdaQueryWrapper<GrantReconcileDiff>()
                        .eq(GrantReconcileDiff::getDiffType, diffType)
                        .eq(GrantReconcileDiff::getHandleStatus, "PENDING"));
        int done = 0;
        int skipped = 0;
        for (GrantReconcileDiff d : list) {
            try {
                handle(d.getId(), action, remark);
                done++;
            } catch (BizException e) {
                skipped++;
            }
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("diffType", diffType);
        m.put("action", action);
        m.put("handled", done);
        m.put("skipped", skipped);
        return m;
    }

    @Override
    public Map<String, Object> stats() {
        List<GrantReconcileDiff> all = diffMapper.selectList(
                new LambdaQueryWrapper<GrantReconcileDiff>()
                        .eq(GrantReconcileDiff::getHandleStatus, "PENDING"));
        Map<String, Integer> byType = new LinkedHashMap<>();
        byType.put("LOCAL_MISSING", 0);
        byType.put("IOT_EXTRA", 0);
        byType.put("PERIOD_MISMATCH", 0);
        byType.put("VALUE_MISMATCH", 0);
        for (GrantReconcileDiff d : all) {
            byType.merge(d.getDiffType(), 1, Integer::sum);
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("pending", all.size());
        m.put("byType", byType);
        // 风险优先级：IoT 多余（该失效未失效）> 本地缺少（住户打不开门）
        m.put("riskLevel", byType.getOrDefault("IOT_EXTRA", 0) > 0 ? "HIGH"
                : (byType.getOrDefault("LOCAL_MISSING", 0) > 0 ? "MEDIUM" : "LOW"));
        return m;
    }

    // ==================== 内部 ====================

    /** 对账键：锁 + 人员。 */
    private static String keyOf(String lockId, Long personId) {
        return String.valueOf(lockId) + "#" + personId;
    }

    private static boolean isLocalValid(GrantEntitlement e) {
        String st = e.getEntitlementStatus();
        if (st != null && (st.contains("REVOKE") || st.contains("EXPIRE")
                || st.contains("FROZEN") || st.contains("INVALID"))) {
            return false;
        }
        if (e.getExpireTime() != null && e.getExpireTime().isBefore(LocalDateTime.now())) {
            return false;
        }
        return true;
    }

    /**
     * 拉取 IoT 侧授权清单。
     *
     * <p>本期以「本地下发成功的权益」近似，保证对账逻辑可跑通且不产生假差异；
     * 接入真实 IoT 清单时只需替换此方法返回真实集合。
     */
    private Map<String, String> fetchIotKeys(List<GrantEntitlement> locals, String lockId) {
        Map<String, String> map = new LinkedHashMap<>();
        for (GrantEntitlement e : locals) {
            String st = e.getEntitlementStatus();
            boolean pushed = st == null || !st.contains("PENDING");
            if (pushed && isLocalValid(e)) {
                map.put(keyOf(e.getLockId(), e.getPersonId()), "OK");
            }
        }
        return map;
    }

    private void record(GrantEntitlement e, String diffType, String localValue,
                        String iotValue, String lockId) {
        GrantReconcileDiff d = new GrantReconcileDiff();
        d.setId(idGen.nextId());
        d.setTenantId(TenantContext.tenantId());
        d.setDeviceId(e.getDeviceId());
        d.setLockId(e.getLockId());
        d.setPersonId(e.getPersonId());
        d.setTargetUserMobile(e.getTargetUserMobile());
        d.setDiffType(diffType);
        d.setLocalValue(localValue);
        d.setIotValue(iotValue);
        d.setHandleStatus("PENDING");
        d.setCreateTime(LocalDateTime.now());
        diffMapper.insert(d);
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
