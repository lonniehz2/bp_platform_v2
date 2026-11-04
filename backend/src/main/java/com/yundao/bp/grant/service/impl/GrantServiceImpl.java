package com.yundao.bp.grant.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.grant.constant.GrantStatus;
import com.yundao.bp.grant.constant.GrantTaskStatus;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantTaskVO;
import com.yundao.bp.grant.dto.GrantVO;
import com.yundao.bp.grant.entity.GrantEntitlement;
import com.yundao.bp.grant.entity.GrantTask;
import com.yundao.bp.grant.entity.GrantTaskDetail;
import com.yundao.bp.grant.iot.IotGrantClient;
import com.yundao.bp.grant.iot.IotGrantRequest;
import com.yundao.bp.grant.iot.IotGrantResult;
import com.yundao.bp.grant.mapper.GrantEntitlementMapper;
import com.yundao.bp.grant.mapper.GrantTaskDetailMapper;
import com.yundao.bp.grant.mapper.GrantTaskMapper;
import com.yundao.bp.grant.mq.GrantDispatchProducer;
import com.yundao.bp.dev.service.DeviceBindingResolver;
import com.yundao.bp.grant.service.GrantAuditService;
import com.yundao.bp.grant.service.GrantService;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 授权编排实现。
 *
 * <p><b>闭环</b>：
 * <pre>
 * apply()  → 权益(EFFECTIVE) + 任务(PENDING) + 投递 MQ
 *             ↓（事务提交后）
 * MQ       → consumer → dispatch()
 *             ↓
 * dispatch()→ 任务(DISPATCHING) → IoT 下发 → 明细逐设备 → 任务(SUCCESS/PARTIAL/FAILED)
 * </pre>
 *
 * <p><b>幂等</b>：{@code idempotent_key = sha1(personId|spaceId|level|validStart|validEnd)}，
 * 库上有唯一索引；重复申请直接返回已有权益，不重复下发。
 */
@Service
public class GrantServiceImpl implements GrantService {
    /** 数据范围服务 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按组织/人员列限权；personCol 为 null 表示仅组织维度。 */
    private <T> void applyScope(
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
        if (scope.isSelf() && personCol != null) {
            qw.eq(personCol, scope.personId() == null ? -1L : scope.personId());
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty() && orgCol != null) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null && orgCol != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }


    private static final Logger log = LoggerFactory.getLogger(GrantServiceImpl.class);
    private static final int MAX_RETRY = 3;

    private final GrantEntitlementMapper entitlementMapper;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonMapper personMapper;
    private final GrantTaskMapper taskMapper;
    private final GrantTaskDetailMapper detailMapper;
    private final SnowflakeIdGenerator idGen;

    /** 授权审计（★ 级要求：授权操作必须可追溯） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private GrantAuditService grantAuditService;

    private void audit(String bizType, Long bizId, Long personId, Long spaceId,
                       String reason, String before, String after, String result) {
        if (grantAuditService == null) {
            return;
        }
        var u = com.yundao.bp.iam.security.LoginUser.get();
        grantAuditService.record(bizType, bizId, personId, spaceId,
                u == null ? null : u.userId(),
                u == null ? null : (u.realName() == null ? u.username() : u.realName()),
                reason, before, after, result);
    }

    private final GrantDispatchProducer producer;
    private final IotGrantClient iotClient;
    /** 设备-空间绑定解析（把空间锚点翻译成真实设备列表） */
    private final DeviceBindingResolver deviceResolver;


    /** 用户（操作人 → 人员映射） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamUserMapper userMapper;

    public GrantServiceImpl(GrantEntitlementMapper entitlementMapper,
                            GrantTaskMapper taskMapper,
                            GrantTaskDetailMapper detailMapper,
                            SnowflakeIdGenerator idGen,
                            GrantDispatchProducer producer,
                            IotGrantClient iotClient,
                            DeviceBindingResolver deviceResolver) {
        this.entitlementMapper = entitlementMapper;
        this.taskMapper = taskMapper;
        this.detailMapper = detailMapper;
        this.idGen = idGen;
        this.producer = producer;
        this.iotClient = iotClient;
        this.deviceResolver = deviceResolver;
    }

    // ==================== 申请 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public GrantVO apply(GrantApplyCmd cmd) {
        String tenantId = TenantContext.tenantId();

        // ---- 1) 基础校验 ----
        LocalDateTime start = cmd.validStart() != null ? cmd.validStart() : LocalDateTime.now();
        LocalDateTime end = cmd.validEnd();
        if (end != null && !end.isAfter(start)) {
            throw BizException.paramInvalid("失效时间必须晚于生效时间");
        }
        if (end == null && !"OWNERSHIP".equals(cmd.grantLevel())) {
            throw BizException.paramInvalid("仅 OWNERSHIP（所有权）允许不设失效时间");
        }

        // ---- 2) 幂等：同人+同空间+同层级+同有效期 只建一次 ----
        // ⚠️ 必须用 cmd 里"原始"的 validStart，不能用上面解析出的 start（=now()）
        //    否则每次申请 now() 都不同，幂等键永远不命中
        requireOwnershipForTransfer(cmd.grantLevel(), cmd.spaceId());
        String idemKey = idempotentKey(cmd.personId(), cmd.spaceId(), cmd.grantLevel(),
                cmd.validStart(), end);
        GrantTask existTask = taskMapper.selectOne(new LambdaQueryWrapper<GrantTask>()
                .eq(GrantTask::getIdempotentKey, idemKey)
                .last("LIMIT 1"));
        if (existTask != null && !GrantTaskStatus.FAILED.name().equals(existTask.getTaskStatus())) {
            log.info("授权幂等命中，返回已有任务 taskId={}", existTask.getId());
            GrantEntitlement e = entitlementMapper.selectById(existTask.getEntitlementId());
            audit("GRANT", null, cmd.personId(), cmd.spaceId(), "新增加权",
                null, "entitlement apply", "SUCCESS");
        return GrantVO.from(e);
        }

        // ---- 3) 建权益 ----
        long entId = idGen.nextId();
        GrantEntitlement e = new GrantEntitlement();
        e.setId(entId);
        e.setTenantId(tenantId);
        e.setGrantNo("G" + entId);
        e.setGrantLevel(cmd.grantLevel());
        e.setHolderType("PERSON");
        e.setPersonId(cmd.personId());
        e.setSpaceId(cmd.spaceId());
        e.setValidStart(start);
        e.setValidEnd(end);
        // 所有权不含开门权限（管理权才含），见 DDL 注释
        e.setAllowOpen("OWNERSHIP".equals(cmd.grantLevel()) ? 0 : 1);
        e.setAllowManage("OWNERSHIP".equals(cmd.grantLevel())
                || "MANAGEMENT".equals(cmd.grantLevel())
                || "SECONDARY_MANAGEMENT".equals(cmd.grantLevel()) ? 1 : 0);
        e.setAllowDelegate("OWNERSHIP".equals(cmd.grantLevel()) ? 1 : 0);
        e.setVisitLimitTimes("VISIT".equals(cmd.grantLevel()) ? 1 : null);
        e.setVisitUsedTimes(0);
        e.setSourceType(blankToNull(cmd.sourceType()) == null ? "MANUAL" : cmd.sourceType());
        e.setSourceId(cmd.sourceId());
        e.setGrantStatus(GrantStatus.EFFECTIVE.name());
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        entitlementMapper.insert(e);

        // ---- 4) 建任务 ----
        long taskId = idGen.nextId();
        GrantTask t = new GrantTask();
        t.setId(taskId);
        t.setTenantId(tenantId);
        t.setTaskNo("T" + taskId);
        t.setIdempotentKey(idemKey);
        t.setTaskType("GRANT");
        t.setPersonId(cmd.personId());
        t.setEntitlementId(entId);
        t.setKeyringIds(cmd.keyringIds() == null ? null
                : cmd.keyringIds().stream().map(String::valueOf).collect(Collectors.joining(",")));
        t.setLockCount(0);
        t.setSuccessCount(0);
        t.setFailCount(0);
        t.setValidStart(start);
        t.setValidEnd(end);
        t.setTaskStatus(GrantTaskStatus.PENDING.name());
        t.setRetryCount(0);
        t.setTriggerSource("MANUAL");
        t.setCreateTime(LocalDateTime.now());
        taskMapper.insert(t);

        // ---- 5) 投递 MQ（事务提交后生效）----
        producer.publishDispatch(taskId);

        return GrantVO.from(e);
    }

    // ==================== 查询 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int revokeBySource(String sourceType, Long sourceId, String reason) {
        List<GrantEntitlement> list = entitlementMapper.selectList(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(GrantEntitlement::getSourceType, sourceType)
                        .eq(GrantEntitlement::getSourceId, sourceId)
                        .in(GrantEntitlement::getGrantStatus,
                                List.of(GrantStatus.PENDING.name(),
                                        GrantStatus.EFFECTIVE.name(),
                                        GrantStatus.FROZEN.name())));
        int n = 0;
        for (GrantEntitlement e : list) {
            try {
                revoke(e.getId(), reason);
                n++;
            } catch (Exception ex) {
                log.warn("revoke source {}:{} failed: {}", sourceType, sourceId, ex.getMessage());
            }
        }
        return n;
    }

    @Override
    public GrantVO get(Long id) {
        GrantEntitlement e = entitlementMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("权益");
        }
        return GrantVO.from(e);
    }

    @Override
    public PageResult<GrantVO> page(long pageNum, long pageSize, Long personId, Long spaceId,
                                    String grantStatus) {
        LambdaQueryWrapper<GrantEntitlement> qw = new LambdaQueryWrapper<GrantEntitlement>()
                .eq(personId != null, GrantEntitlement::getPersonId, personId)
                .eq(spaceId != null, GrantEntitlement::getSpaceId, spaceId)
                .eq(grantStatus != null && !grantStatus.isBlank(),
                        GrantEntitlement::getGrantStatus, grantStatus)
                .orderByDesc(GrantEntitlement::getId);
        applyScope(qw, GrantEntitlement::getOrgId, GrantEntitlement::getPersonId);
        IPage<GrantEntitlement> page =
                entitlementMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<GrantVO> rows = fillPersonNames(page.getRecords());
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public GrantTaskVO task(Long taskId) {
        GrantTask t = taskMapper.selectById(taskId);
        if (t == null) {
            throw BizException.notFound("授权任务");
        }
        return GrantTaskVO.from(t);
    }

    /** 任务的逐设备明细。 */
    public List<GrantTaskDetail> details(Long taskId) {
        return detailMapper.selectList(new LambdaQueryWrapper<GrantTaskDetail>()
                .eq(GrantTaskDetail::getTaskId, taskId)
                .orderByAsc(GrantTaskDetail::getId));
    }

    // ==================== 撤销 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public GrantVO revoke(Long id, String reason) {
        GrantEntitlement e = entitlementMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("权益");
        }
        requireRevokeRight(e);
        GrantStatus cur = GrantStatus.valueOf(e.getGrantStatus());
        if (cur.isTerminal()) {
            throw BizException.stateConflict("权益已是终态（" + cur.label() + "），不可撤销");
        }
        if (!GrantStatus.nextOf(cur).contains(GrantStatus.REVOKED)) {
            throw BizException.stateConflict("权益状态 " + cur.label() + " 不允许撤销");
        }
        e.setGrantStatus(GrantStatus.REVOKED.name());
        e.setRevokeReason(reason);
        entitlementMapper.updateById(e);

        // 生成 REVOKE 任务
        long taskId = idGen.nextId();
        GrantTask t = new GrantTask();
        t.setId(taskId);
        t.setTenantId(e.getTenantId());
        t.setTaskNo("T" + taskId);
        t.setIdempotentKey("REVOKE-" + id + "-" + System.currentTimeMillis());
        t.setTaskType("REVOKE");
        t.setPersonId(e.getPersonId());
        t.setEntitlementId(e.getId());
        t.setLockCount(0);
        t.setSuccessCount(0);
        t.setFailCount(0);
        t.setTaskStatus(GrantTaskStatus.PENDING.name());
        t.setRetryCount(0);
        t.setTriggerSource("MANUAL");
        t.setCreateTime(LocalDateTime.now());
        taskMapper.insert(t);
        producer.publishRetry(taskId);

        audit("REVOKE", id, null, null, reason, "entitlement revoke",
                "revoked: " + id, "SUCCESS");
        return GrantVO.from(e);
    }

    // ==================== 下发（异步执行）====================

    @Override
    public void dispatch(Long taskId) {
        GrantTask t = taskMapper.selectById(taskId);
        if (t == null) {
            log.warn("授权任务不存在 taskId={}", taskId);
            return;
        }
        if (GrantTaskStatus.valueOf(t.getTaskStatus()).isFinished()) {
            return;   // 幂等：已结束不重发
        }
        if (t.getRetryCount() != null && t.getRetryCount() >= MAX_RETRY) {
            markFailed(t, "重试次数超过上限(" + MAX_RETRY + ")");
            return;
        }

        // 标记下发中
        t.setTaskStatus(GrantTaskStatus.DISPATCHING.name());
        t.setDispatchTime(LocalDateTime.now());
        t.setUpdateTime(LocalDateTime.now());
        taskMapper.updateById(t);

        try {
            // 目标设备：按权益的空间锚点解析（含向下继承 + 公有设备）
            List<String> lockIds = resolveTargetDevices(t);
            boolean isRevoke = "REVOKE".equals(t.getTaskType());
            if (lockIds.isEmpty()) {
                markRetryOrFail(t, "授权空间下没有可开门设备（请先把设备绑定到该空间）");
                return;
            }

            IotGrantRequest req = new IotGrantRequest(t.getPersonId(), null, null,
                    lockIds, t.getValidStart(), t.getValidEnd(), null, null);
            IotGrantResult r = isRevoke ? iotClient.revoke(req) : iotClient.grant(req);

            if (!r.success()) {
                markRetryOrFail(t, r.message());
                return;
            }

            // 保存 IoT 异步任务号
            if (r.iotTaskId() != null) {
                t.setIotTaskId(r.iotTaskId());
            }
            t.setLockCount(lockIds.size());

            // 逐设备写明细
            List<IotGrantResult.DeviceResult> devs = r.devices().isEmpty()
                    ? lockIds.stream().map(id -> new IotGrantResult.DeviceResult(
                            id, true, null, null, null)).toList()
                    : r.devices();
            int ok = 0;
            int fail = 0;
            LocalDateTime now = LocalDateTime.now();
            List<GrantTaskDetail> details = new ArrayList<>();
            for (IotGrantResult.DeviceResult d : devs) {
                GrantTaskDetail dt = new GrantTaskDetail();
                dt.setId(idGen.nextId());
                dt.setTenantId(t.getTenantId());
                dt.setTaskId(t.getId());
                // device_id 为 NOT NULL：现网门锁与设备 1:1，先用 lockId 兜底
                // TODO 接入 bp_dev_lock 后改为真实 device_id，与 lock_id 分离
                dt.setDeviceId(d.lockId() != null ? d.lockId() : "UNKNOWN");
                dt.setLockId(d.lockId());
                dt.setDetailStatus(d.success() ? "SUCCESS" : "FAILED");
                dt.setErrorCode(d.errorCode());
                dt.setErrorMsg(d.errorMsg());
                dt.setDurationMs(d.durationMs());
                dt.setCreateTime(now);
                dt.setUpdateTime(now);
                detailMapper.insert(dt);
                details.add(dt);
                if (d.success()) {
                    ok++;
                } else {
                    fail++;
                }
            }
            t.setSuccessCount(ok);
            t.setFailCount(fail);

            // 终态判定
            if (fail == 0) {
                t.setTaskStatus(GrantTaskStatus.SUCCESS.name());
                t.setFinishTime(now);
                t.setLastError(null);
            } else if (ok == 0) {
                markRetryOrFail(t, devs.isEmpty() ? "无目标设备" : "全部设备失败");
                return;
            } else {
                t.setTaskStatus(GrantTaskStatus.PARTIAL.name());
                t.setFinishTime(now);
            }
            t.setUpdateTime(now);
            taskMapper.updateById(t);
            log.info("授权任务完成 taskId={} status={} ok={} fail={}",
                    t.getId(), t.getTaskStatus(), ok, fail);

        } catch (Exception ex) {
            log.error("授权任务下发异常 taskId={}", taskId, ex);
            markRetryOrFail(t, ex.getMessage());
        }
    }

    // ==================== 内部 ====================

    /**
     * 解析任务的目标设备 ID。
     *
     * <p>授权与撤权都按<b>原权益的空间锚点</b>解析，保证"授权了哪些就撤哪些"，
     * 避免空间树变更后撤权遗漏。继承规则见 {@link DeviceBindingResolver}。
     */
    private List<String> resolveTargetDevices(GrantTask t) {
        Long entitlementId = t.getEntitlementId();
        if (entitlementId == null) {
            return List.of();
        }
        GrantEntitlement ent = entitlementMapper.selectById(entitlementId);
        if (ent == null || ent.getSpaceId() == null) {
            return List.of();
        }
        return deviceResolver.resolveDeviceIds(ent.getSpaceId());
    }

    private void markRetryOrFail(GrantTask t, String error) {
        int retry = (t.getRetryCount() == null ? 0 : t.getRetryCount()) + 1;
        t.setRetryCount(retry);
        t.setLastError(truncate(error, 900));
        t.setUpdateTime(LocalDateTime.now());
        if (retry >= MAX_RETRY) {
            t.setTaskStatus(GrantTaskStatus.FAILED.name());
            t.setFinishTime(LocalDateTime.now());
            log.warn("授权任务失败（已达重试上限）taskId={} err={}", t.getId(), error);
        } else {
            t.setTaskStatus(GrantTaskStatus.PENDING.name());
            log.warn("授权任务待重试 taskId={} retry={} err={}", t.getId(), retry, error);
        }
        taskMapper.updateById(t);
    }

    private void markFailed(GrantTask t, String error) {
        t.setTaskStatus(GrantTaskStatus.FAILED.name());
        t.setLastError(truncate(error, 900));
        t.setFinishTime(LocalDateTime.now());
        t.setUpdateTime(LocalDateTime.now());
        taskMapper.updateById(t);
    }

    /**
     * 幂等键：{@code sha1(personId|spaceId|level|validStart|validEnd)}。
     *
     * <p>⚠️ {@code validStart} 必须传<b>请求原始值</b>（可为 null），
     * 不能传"解析后的 now()"，否则每次调用键都不同，幂等失效。
     */
    public static String idempotentKey(Long personId, Long spaceId, String level,
                                LocalDateTime start, LocalDateTime end) {
        String raw = personId + "|" + spaceId + "|" + level + "|"
                + (start == null ? "" : start) + "|" + (end == null ? "" : end);
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            byte[] d = md.digest(raw.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(40);
            for (byte b : d) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception ex) {
            throw new IllegalStateException("幂等键计算失败", ex);
        }
    }

    private static String truncate(String s, int max) {
        if (s == null) {
            return null;
        }
        return s.length() <= max ? s : s.substring(0, max);
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }

    /**
     * 二级管理权的授予约束：
     * 只有在该空间上拥有 OWNERSHIP / MANAGEMENT 且 allowManage=1 的人，
     * 才能创建或删除 SECONDARY_MANAGEMENT；二级管理权本身不能再向下授予。
     */
    /**
     * 管理权转移约束（按业务确认口径）：
     * <ul>
     *   <li>设备初始绑定到某账号 → 该账号拥有所有权（OWNERSHIP，含管理能力）</li>
     *   <li><b>只有所有权者</b>可以把管理权转移给其他账号</li>
     *   <li>只有管理权（无所有权）的账号不能再转让，只能归还自己的管理权</li>
     * </ul>
     */
    private void requireOwnershipForTransfer(String grantLevel, Long spaceId) {
        if (!"MANAGEMENT".equals(grantLevel)
                && !"SECONDARY_MANAGEMENT".equals(grantLevel)) {
            return;
        }
        Long me = TenantContext.userId();
        if (me == null) {
            return;   // 系统任务/内部调用
        }
        if (isAdmin(me)) {
            return;   // 组织管理员可代为转移
        }
        java.util.List<Long> ids = idsForUser(me);
        Long owner = entitlementMapper.selectCount(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .in(GrantEntitlement::getPersonId, ids)
                        .eq(spaceId != null, GrantEntitlement::getSpaceId, spaceId)
                        .eq(GrantEntitlement::getGrantLevel, "OWNERSHIP")
                        .eq(GrantEntitlement::getAllowManage, 1)
                        .in(GrantEntitlement::getGrantStatus, java.util.List.of("ACTIVE", "PENDING")));
        if (owner != null && owner > 0) {
            return;
        }
        Long manager = entitlementMapper.selectCount(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .in(GrantEntitlement::getPersonId, ids)
                        .eq(spaceId != null, GrantEntitlement::getSpaceId, spaceId)
                        .eq(GrantEntitlement::getGrantLevel, "MANAGEMENT")
                        .in(GrantEntitlement::getGrantStatus, java.util.List.of("ACTIVE", "PENDING")));
        if (manager != null && manager > 0) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "只有所有权者可以转移管理权；管理权持有者只能归还自己的管理权");
        }
        throw com.yundao.bp.common.exception.BizException.stateConflict(
                "只有该空间的所有权者才能授予管理权");
    }

    /** 是否组织管理员（跨组织代管场景放行）。 */
    private boolean isAdmin(Long userId) {
        if (userMapper == null) {
            return false;
        }
        com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(userId);
        return u != null && ("PLATFORM".equals(u.getUserType())
                || "ADMIN".equals(u.getUserType()));
    }


    /**
     * 撤销/归还权限：
     * 所有权者可强制收回；权益持有者本人可归还；管理员可代操作。
     */
    private void requireRevokeRight(GrantEntitlement e) {
        Long me = TenantContext.userId();
        if (me == null || isAdmin(me)) {
            return;
        }
        java.util.List<Long> ids = idsForUser(me);
        if (e.getPersonId() != null && ids.contains(e.getPersonId())) {
            return;   // 本人归还
        }
        Long owner = entitlementMapper.selectCount(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .in(GrantEntitlement::getPersonId, ids)
                        .eq(e.getSpaceId() != null, GrantEntitlement::getSpaceId, e.getSpaceId())
                        .eq(GrantEntitlement::getGrantLevel, "OWNERSHIP")
                        .in(GrantEntitlement::getGrantStatus, java.util.List.of("ACTIVE", "PENDING")));
        if (owner == null || owner == 0) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "无权撤销：只有所有权者或权益持有人本人可以操作");
        }
    }

    @Override
    public int expireOverdue() {
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        java.util.List<GrantEntitlement> list = entitlementMapper.selectList(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(GrantEntitlement::getGrantStatus, "ACTIVE")
                        .isNotNull(GrantEntitlement::getValidEnd)
                        .lt(GrantEntitlement::getValidEnd, now));
        int n = 0;
        for (GrantEntitlement e : list) {
            if (e.getValidEnd() != null && e.getValidEnd().isBefore(now)) {
                e.setGrantStatus("EXPIRED");
                e.setRevokeReason("管理权到期自动归还");
                entitlementMapper.updateById(e);
                n++;
            }
        }
        if (n > 0) {
            log.info("权益到期归还：{} 条", n);
        }
        return n;
    }

    /** 账号可能在人员档案与账号两种 id 下建权益，这里同时匹配。 */
    private java.util.List<Long> idsForUser(Long userId) {
        java.util.List<Long> ids = new java.util.ArrayList<>();
        ids.add(userId);
        if (userMapper != null) {
            com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(userId);
            if (u != null && u.getPersonId() != null && !u.getPersonId().equals(userId)) {
                ids.add(u.getPersonId());
            }
        }
        return ids;
    }

    @Override
    public int markTimeout() {
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        java.util.List<GrantTask> tasks = taskMapper.selectList(
                new LambdaQueryWrapper<GrantTask>()
                        .in(GrantTask::getTaskStatus, java.util.List.of("PENDING", "RUNNING")));
        int n = 0;
        for (GrantTask t : tasks) {
            if (t.getCallbackTime() != null) {
                continue;   // 已回调
            }
            java.time.LocalDateTime deadline = t.getTimeoutAt();
            if (deadline == null && t.getCreateTime() != null) {
                // 兼容历史任务：按创建时间 + 3 分钟推算
                deadline = t.getCreateTime().plusMinutes(3);
            }
            if (deadline == null || deadline.isAfter(now)) {
                continue;
            }
            t.setTaskStatus("FAILED");
            t.setFailCount((t.getFailCount() == null ? 0 : t.getFailCount()) + 1);
            t.setLastError("超时未回调（超过 3 分钟），判定下发失败");
            taskMapper.updateById(t);
            n++;
        }
        if (n > 0) {
            log.warn("授权任务超时判定：{} 条置为失败", n);
        }
        return n;
    }

    /** 批量补人员姓名（列表展示用，避免前端显示人员ID）。 */
    private List<GrantVO> fillPersonNames(List<GrantEntitlement> list) {
        if (list == null || list.isEmpty() || personMapper == null) {
            return list == null ? List.of()
                    : list.stream().map(GrantVO::from).toList();
        }
        java.util.Set<Long> ids = new java.util.HashSet<>();
        for (GrantEntitlement e : list) {
            if (e.getPersonId() != null) {
                ids.add(e.getPersonId());
            }
        }
        java.util.Map<Long, String> nameOf = new java.util.HashMap<>();
        if (!ids.isEmpty()) {
            for (com.yundao.bp.person.entity.Person p
                    : personMapper.selectBatchIds(ids)) {
                nameOf.put(p.getId(), p.getPersonName());
            }
        }
        return list.stream()
                .map(e -> GrantVO.from(e, nameOf.get(e.getPersonId())))
                .toList();
    }
}
