package com.yundao.bp.grant.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.grant.entity.GrantEntitlement;
import com.yundao.bp.grant.entity.GrantReconcileDiff;
import com.yundao.bp.grant.entity.GrantTaskDetail;
import com.yundao.bp.grant.mapper.GrantEntitlementMapper;
import com.yundao.bp.grant.mapper.GrantReconcileDiffMapper;
import com.yundao.bp.grant.mapper.GrantTaskDetailMapper;
import com.yundao.bp.grant.service.ReconcileService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 授权对账实现。
 *
 * <p><b>对账口径</b>：把「本地有效权益」与「下发明细中已成功的锁」做集合比对。
 *
 * <ul>
 *   <li>权益 {@code EFFECTIVE} 且未过期，但某台锁没有 SUCCESS 下发记录
 *       → {@code LOCAL_MISSING}（住户刷不开门，影响最大）</li>
 *   <li>权益已 {@code REVOKED} 或已过期，但某台锁仍有 SUCCESS 下发记录
 *       → {@code IOT_EXTRA}（该失效的没失效，安全风险）</li>
 * </ul>
 *
 * <p>设计说明：权益是<b>空间级</b>授权，一台空间可能对应多把门锁，
 * 因此「本地应有」要按 空间→锁 展开后再与下发明细比对。
 */
// Bean 名显式指定：与另一模块的同名实现类区分，避免运行期 BeanDefinition 冲突
// 类名与 fin 模块的 ReconcileServiceImpl 区分：
// MyBatis 的类型别名扫描把 Service 也注册了别名，同名类会导致
// "The alias 'X' is already mapped to" 启动失败
@Service("grantReconcileService")
public class GrantReconcileServiceImpl implements ReconcileService {

    private static final Logger log = LoggerFactory.getLogger(GrantReconcileServiceImpl.class);

    /** 下发成功的明细状态 */
    private static final Set<String> PUSH_OK = Set.of("SUCCESS", "SENT", "DONE");

    private final GrantReconcileDiffMapper diffMapper;
    private final GrantEntitlementMapper entitlementMapper;
    private final GrantTaskDetailMapper taskDetailMapper;
    private final SnowflakeIdGenerator idGen;

    public GrantReconcileServiceImpl(GrantReconcileDiffMapper diffMapper,
                                GrantEntitlementMapper entitlementMapper,
                                GrantTaskDetailMapper taskDetailMapper,
                                SnowflakeIdGenerator idGen) {
        this.diffMapper = diffMapper;
        this.entitlementMapper = entitlementMapper;
        this.taskDetailMapper = taskDetailMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> reconcile(String lockId) {
        List<GrantEntitlement> ents = entitlementMapper.selectList(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(GrantEntitlement::getIsDeleted, 0)
                        .orderByAsc(GrantEntitlement::getId));
        LambdaQueryWrapper<GrantTaskDetail> dq = new LambdaQueryWrapper<GrantTaskDetail>();
        if (lockId != null && !lockId.isBlank()) {
            dq.eq(GrantTaskDetail::getLockId, lockId);
        }
        List<GrantTaskDetail> details = taskDetailMapper.selectList(dq);

        // 已成功下发：空间#锁 集合（同空间可能多锁，故按 lockId 维度收）
        Set<String> pushedBySpaceLock = new LinkedHashSet<>();
        Map<String, GrantTaskDetail> detailBySpaceLock = new LinkedHashMap<>();
        for (GrantTaskDetail d : details) {
            if (d.getDetailStatus() == null || !PUSH_OK.contains(d.getDetailStatus())) {
                continue;
            }
            String k = d.getSpaceId() + "#" + d.getLockId();
            pushedBySpaceLock.add(k);
            detailBySpaceLock.putIfAbsent(k, d);
        }

        int localMissing = 0;
        int iotExtra = 0;
        int recorded = 0;
        List<String> samples = new ArrayList<>();

        // 1) 有效权益但锁上没有 → LOCAL_MISSING
        for (GrantEntitlement e : ents) {
            if (!isEffective(e) || e.getSpaceId() == null) {
                continue;
            }
            // 该空间成功下发过的锁
            Set<String> locksForSpace = locksOf(pushedBySpaceLock, e.getSpaceId());
            if (locksForSpace.isEmpty()) {
                record(e, null, "LOCAL_MISSING",
                        "权益 " + e.getGrantNo() + " 生效（空间 " + e.getSpaceId() + "）",
                        "该空间无任何成功下发记录");
                localMissing++;
                recorded++;
                if (samples.size() < 5) {
                    samples.add("有效授权未下发：grant=" + e.getGrantNo()
                            + " space=" + e.getSpaceId());
                }
            }
        }

        // 2) 权益已失效但锁上仍有 → IOT_EXTRA
        for (GrantEntitlement e : ents) {
            if (isEffective(e) || e.getSpaceId() == null) {
                if (isEffective(e)) {
                    continue;
                }
            }
            if (isEffective(e)) {
                continue;
            }
            Set<String> locksForSpace = locksOf(pushedBySpaceLock, e.getSpaceId());
            for (String lock : locksForSpace) {
                record(e, lock, "IOT_EXTRA",
                        "权益 " + e.getGrantNo() + " 已失效（"
                                + (e.getGrantStatus() == null ? "?" : e.getGrantStatus())
                                + "）",
                        "锁 " + lock + " 仍存在该人授权");
                iotExtra++;
                recorded++;
                if (samples.size() < 5) {
                    samples.add("失效授权仍在锁上：grant=" + e.getGrantNo()
                            + " lock=" + lock);
                }
            }
        }

        Map<String, Object> m = new LinkedHashMap<>();
        m.put("lockId", lockId);
        m.put("entitlementCount", ents.size());
        m.put("pushedDetailCount", pushedBySpaceLock.size());
        m.put("localMissing", localMissing);
        m.put("iotExtra", iotExtra);
        m.put("diffRecorded", recorded);
        m.put("consistent", recorded == 0);
        m.put("samples", samples);
        m.put("conclusion", recorded == 0
                ? "本地权益与 IoT 下发记录一致，无需处置"
                : "发现 " + recorded + " 条差异，请在差异清单中处置");
        log.info("授权对账完成（lock={}）：权益 {}，已下发 {}，差异 {}",
                lockId, ents.size(), pushedBySpaceLock.size(), recorded);
        return m;
    }

    @Override
    public PageResult<GrantReconcileDiff> pageDiffs(long pageNum, long pageSize,
                                                    String lockId, String diffType,
                                                    String handleStatus) {
        LambdaQueryWrapper<GrantReconcileDiff> qw =
                new LambdaQueryWrapper<GrantReconcileDiff>()
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
        // scope:ignore 对账差异按状态查询
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
        if ("REGRANT".equals(action) && !"LOCAL_MISSING".equals(d.getDiffType())) {
            throw BizException.stateConflict(
                    "「重新授权」仅适用于本地有效但 IoT 未下发的差异");
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
        // 风险优先级：IoT 多余（该失效未失效，可能被越权开门）> 本地缺少（打不开门）
        m.put("riskLevel", byType.getOrDefault("IOT_EXTRA", 0) > 0 ? "HIGH"
                : (byType.getOrDefault("LOCAL_MISSING", 0) > 0 ? "MEDIUM" : "LOW"));
        return m;
    }

    // ==================== 内部 ====================

    /** 权益是否有效：状态 EFFECTIVE 且未过期（且已生效）。 */
    private static boolean isEffective(GrantEntitlement e) {
        if (!"EFFECTIVE".equals(e.getGrantStatus())) {
            return false;
        }
        LocalDateTime now = LocalDateTime.now();
        if (e.getValidStart() != null && e.getValidStart().isAfter(now)) {
            return false;
        }
        return e.getValidEnd() == null || !e.getValidEnd().isBefore(now);
    }

    /** 取某空间已成功下发过的锁集合。 */
    private static Set<String> locksOf(Set<String> spaceLockPairs, Long spaceId) {
        Set<String> out = new LinkedHashSet<>();
        String prefix = spaceId + "#";
        for (String k : spaceLockPairs) {
            if (k.startsWith(prefix)) {
                out.add(k.substring(prefix.length()));
            }
        }
        return out;
    }

    private void record(GrantEntitlement e, String lockId, String diffType,
                        String localValue, String iotValue) {
        GrantReconcileDiff d = new GrantReconcileDiff();
        d.setId(idGen.nextId());
        d.setTenantId(TenantContext.tenantId());
        d.setLockId(lockId);
        d.setPersonId(e.getPersonId());
        d.setDiffType(diffType);
        d.setLocalValue(localValue);
        d.setIotValue(iotValue);
        d.setHandleStatus("PENDING");
        d.setCreateTime(LocalDateTime.now());
        diffMapper.insert(d);
    }
}
