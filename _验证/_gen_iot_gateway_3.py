# -*- coding: utf-8 -*-
"""补字段/配置/放行，并生成指令模块。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def write(rel, body):
    path = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print('跳过(已存在)', rel)
        return
    io.open(path, 'w', encoding='utf-8', newline='').write(body)
    print('创建', rel)


def patch(rel, old, new):
    path = os.path.join(BK, rel)
    s = io.open(path, encoding='utf-8', errors='replace').read()
    if new in s:
        print('已包含', rel)
        return
    if old not in s:
        print('!! 未找到锚点', rel)
        return
    io.open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new, 1))
    print('已修改', rel)


# 1) DevEvent 增加 eventId
patch('dev/entity/DevEvent.java',
      '    private String deviceId;',
      '''    private String deviceId;

    /** IoT 事件唯一号（幂等键） */
    private String eventId;''')

# 2) IotSettings 增加回调相关默认值
patch('iot/config/IotSettings.java',
      '        DEFAULTS.put("iot.callback.signAlgorithm", "v2-hmac-sha256");',
      '''        DEFAULTS.put("iot.callback.signAlgorithm", "v2-hmac-sha256");
        DEFAULTS.put("iot.callback.appId", "bp-test-app");
        DEFAULTS.put("iot.callback.appSecret", "bp-test-secret");
        DEFAULTS.put("iot.callback.verify", "true");
        DEFAULTS.put("iot.callback.defaultTenant", "350600");''')

# 3) 登录拦截器放行回调
patch('iam/security/AuthInterceptor.java',
      '        // 放行：登录、健康检查',
      '''        // 放行：IoT 回调（改用 HMAC 验签 + Nonce 防重放）
        if (path.startsWith("/api/callback/")) {
            return true;
        }
        // 放行：登录、健康检查''')

# ---------------- 指令服务 ----------------
write('dev/service/DevCommandService.java', '''package com.yundao.bp.dev.service;

import com.yundao.bp.dev.entity.DevCommand;
import com.yundao.bp.common.api.PageResult;

/** 设备指令（开锁/重启/校时/拉合闸）。 */
public interface DevCommandService {

    DevCommand create(String commandType, String deviceId, String lockId, String meterNo,
                      String reason, String paramsJson, String source);

    PageResult<DevCommand> page(long pageNum, long pageSize, String status, String commandType,
                                String deviceId);

    DevCommand get(Long id);

    DevCommand retry(Long id);

    DevCommand cancel(Long id);

    /** 下发（供创建后与超时重试 Job 调用）。 */
    void dispatch(Long id);
}
''')

write('dev/service/impl/DevCommandServiceImpl.java', '''package com.yundao.bp.dev.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.dev.entity.DevCommand;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.iot.DeviceCommandClient;
import com.yundao.bp.dev.mapper.DevCommandMapper;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.dev.service.DevCommandService;
import com.yundao.bp.iot.config.IotSettings;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DevCommandServiceImpl implements DevCommandService {

    private static final Logger log = LoggerFactory.getLogger(DevCommandServiceImpl.class);

    private final DevCommandMapper mapper;
    private final DevDeviceMapper deviceMapper;
    private final DeviceCommandClient client;
    private final IotSettings settings;
    private final SnowflakeIdGenerator idGen;

    public DevCommandServiceImpl(DevCommandMapper mapper, DevDeviceMapper deviceMapper,
                                 DeviceCommandClient client, IotSettings settings,
                                 SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.deviceMapper = deviceMapper;
        this.client = client;
        this.settings = settings;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DevCommand create(String commandType, String deviceId, String lockId, String meterNo,
                             String reason, String paramsJson, String source) {
        if (commandType == null || commandType.isBlank()) {
            throw BizException.paramInvalid("指令类型不能为空");
        }
        DevDevice d = null;
        if (deviceId != null && !deviceId.isBlank()) {
            d = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceId, deviceId).last("LIMIT 1"));
            if (d == null) {
                throw BizException.notFound("设备");
            }
        }
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        DevCommand c = new DevCommand();
        c.setId(id);
        c.setTenantId(TenantContext.tenantId());
        c.setCommandNo("CMD" + id);
        c.setCommandType(commandType);
        c.setDeviceId(deviceId != null ? deviceId : (d == null ? null : d.getDeviceId()));
        c.setLockId(lockId != null ? lockId : c.getDeviceId());
        c.setMeterNo(meterNo);
        c.setRequestId("REQ" + id);
        c.setParamsJson(paramsJson);
        c.setStatus("PENDING");
        c.setRetryCount(0);
        c.setMaxRetry(settings.commandMaxRetry());
        c.setTimeoutAt(now.plusSeconds(settings.commandTimeoutSeconds()));
        c.setOperatorId(TenantContext.userId());
        c.setOperatorName(null);
        c.setReason(reason);
        c.setSource(source == null ? "CONSOLE" : source);
        if ("METER_SWITCH".equals(commandType)) {
            c.setApproveStatus("PENDING");
        }
        c.setIsDeleted(0);
        c.setCreateTime(now);
        c.setUpdateTime(now);
        mapper.insert(c);
        dispatch(id);
        return mapper.selectById(id);
    }

    @Override
    public PageResult<DevCommand> page(long pageNum, long pageSize, String status,
                                       String commandType, String deviceId) {
        LambdaQueryWrapper<DevCommand> qw = new LambdaQueryWrapper<DevCommand>()
                .eq(status != null && !status.isBlank(), DevCommand::getStatus, status)
                .eq(commandType != null && !commandType.isBlank(),
                        DevCommand::getCommandType, commandType)
                .like(deviceId != null && !deviceId.isBlank(), DevCommand::getDeviceId, deviceId)
                .orderByDesc(DevCommand::getCreateTime);
        Page<DevCommand> p = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(p.getTotal(), pageNum, pageSize, p.getRecords());
    }

    @Override
    public DevCommand get(Long id) {
        DevCommand c = mapper.selectById(id);
        if (c == null) {
            throw BizException.notFound("设备指令");
        }
        return c;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DevCommand retry(Long id) {
        DevCommand c = get(id);
        if ("SUCCESS".equals(c.getStatus()) || "CANCELED".equals(c.getStatus())) {
            throw BizException.stateConflict("该指令已结束，不能重试");
        }
        c.setStatus("PENDING");
        c.setRetryCount((c.getRetryCount() == null ? 0 : c.getRetryCount()) + 1);
        c.setTimeoutAt(LocalDateTime.now().plusSeconds(settings.commandTimeoutSeconds()));
        c.setUpdateTime(LocalDateTime.now());
        mapper.updateById(c);
        dispatch(id);
        return mapper.selectById(id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DevCommand cancel(Long id) {
        DevCommand c = get(id);
        if (!"PENDING".equals(c.getStatus())) {
            throw BizException.stateConflict("仅待下发状态可取消");
        }
        c.setStatus("CANCELED");
        c.setResultMsg("人工取消");
        c.setUpdateTime(LocalDateTime.now());
        mapper.updateById(c);
        return c;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispatch(Long id) {
        DevCommand c = mapper.selectById(id);
        if (c == null || "SUCCESS".equals(c.getStatus()) || "CANCELED".equals(c.getStatus())) {
            return;
        }
        c.setStatus("SENT");
        c.setDispatchTime(LocalDateTime.now());
        c.setUpdateTime(LocalDateTime.now());
        mapper.updateById(c);
        try {
            DeviceCommandClient.CommandResult r = client.send(
                    new DeviceCommandClient.CommandRequest(c.getRequestId(), c.getCommandType(),
                            c.getLockId(), c.getMeterNo(), c.getParamsJson()));
            if (r == null) {
                return;
            }
            if (r.success()) {
                // 同步返回成功：等待回执确认；mock 场景直接置成功
                c.setResultCode(r.code());
                c.setResultMsg(r.message());
                c.setCostMs(r.costMs());
                c.setAckTime(LocalDateTime.now());
                c.setStatus("SUCCESS");
            } else {
                c.setResultCode(r.code());
                c.setResultMsg(r.message());
                c.setStatus("FAILED");
                c.setAckTime(LocalDateTime.now());
            }
            c.setUpdateTime(LocalDateTime.now());
            mapper.updateById(c);
        } catch (Exception e) {
            log.error("指令下发失败 {}: {}", c.getRequestId(), e.getMessage());
            c.setResultMsg(e.getMessage());
            c.setStatus("FAILED");
            c.setUpdateTime(LocalDateTime.now());
            mapper.updateById(c);
        }
    }

    /** 超时扫描：由 Job 调用。 */
    public int sweepTimeout() {
        List<DevCommand> list = mapper.selectList(new LambdaQueryWrapper<DevCommand>()
                .in(DevCommand::getStatus, List.of("PENDING", "SENT"))
                .lt(DevCommand::getTimeoutAt, LocalDateTime.now()));
        int n = 0;
        for (DevCommand c : list) {
            int retry = c.getRetryCount() == null ? 0 : c.getRetryCount();
            if (retry >= (c.getMaxRetry() == null ? 3 : c.getMaxRetry())) {
                c.setStatus("TIMEOUT");
                c.setResultMsg("超时且已超过最大重试次数");
                c.setUpdateTime(LocalDateTime.now());
                mapper.updateById(c);
            } else {
                c.setStatus("PENDING");
                c.setRetryCount(retry + 1);
                c.setTimeoutAt(LocalDateTime.now()
                        .plusSeconds(settings.commandTimeoutSeconds()));
                c.setUpdateTime(LocalDateTime.now());
                mapper.updateById(c);
                dispatch(c.getId());
            }
            n++;
        }
        return n;
    }
}
''')

write('dev/controller/DevCommandController.java', '''package com.yundao.bp.dev.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.dev.entity.DevCommand;
import com.yundao.bp.dev.service.DevCommandService;
import com.yundao.bp.iam.security.RequirePerm;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 设备指令：远程开锁 / 重启 / 校时 / 拉合闸（经 IoT 平台下发）。 */
@RestController
@RequestMapping("/api/v1/dev-commands")
public class DevCommandController {

    private final DevCommandService service;

    public DevCommandController(DevCommandService service) {
        this.service = service;
    }

    @RequirePerm("dev:command:create")
    @PostMapping
    public R<DevCommand> create(@RequestBody CommandCmd cmd) {
        return R.ok(service.create(cmd.commandType(), cmd.deviceId(), cmd.lockId(),
                cmd.meterNo(), cmd.reason(), cmd.paramsJson(), cmd.source()));
    }

    @RequirePerm("dev:command:view")
    @GetMapping
    public R<PageResult<DevCommand>> page(@RequestParam(defaultValue = "1") long pageNum,
                                          @RequestParam(defaultValue = "20") long pageSize,
                                          @RequestParam(required = false) String status,
                                          @RequestParam(required = false) String commandType,
                                          @RequestParam(required = false) String deviceId) {
        return R.ok(service.page(pageNum, pageSize, status, commandType, deviceId));
    }

    @RequirePerm("dev:command:view")
    @GetMapping("/{id}")
    public R<DevCommand> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @RequirePerm("dev:command:retry")
    @PostMapping("/{id}/retry")
    public R<DevCommand> retry(@PathVariable Long id) {
        return R.ok(service.retry(id));
    }

    @RequirePerm("dev:command:retry")
    @PostMapping("/{id}/cancel")
    public R<DevCommand> cancel(@PathVariable Long id) {
        return R.ok(service.cancel(id));
    }

    public record CommandCmd(String commandType, String deviceId, String lockId,
                             String meterNo, String reason, String paramsJson, String source) {
    }
}
''')

write('dev/job/DevCommandTimeoutJob.java', '''package com.yundao.bp.dev.job;

import com.yundao.bp.dev.service.impl.DevCommandServiceImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/** 每 30 秒扫描超时指令：重试或置 TIMEOUT。 */
@Component
public class DevCommandTimeoutJob {

    private static final Logger log = LoggerFactory.getLogger(DevCommandTimeoutJob.class);

    private final DevCommandServiceImpl service;

    public DevCommandTimeoutJob(DevCommandServiceImpl service) {
        this.service = service;
    }

    @Scheduled(initialDelay = 45_000, fixedDelay = 30_000)
    public void sweep() {
        try {
            int n = service.sweepTimeout();
            if (n > 0) {
                log.info("指令超时扫描处理 {} 条", n);
            }
        } catch (Exception e) {
            log.warn("指令超时扫描失败: {}", e.getMessage());
        }
    }
}
''')

print('指令模块完成')
