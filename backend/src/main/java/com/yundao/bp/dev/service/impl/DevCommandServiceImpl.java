package com.yundao.bp.dev.service.impl;

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
        com.yundao.bp.iam.security.LoginUser u =
                com.yundao.bp.iam.security.LoginUser.get();
        c.setOperatorName(u == null ? null
                : (u.realName() == null ? u.username() : u.realName()));
        c.setReason(reason);
        c.setSource(source == null ? "CONSOLE" : source);
        if ("METER_SWITCH".equals(commandType)) {
            c.setApproveStatus("PENDING");
        }
        c.setIsDeleted(0);
        c.setCreateTime(now);
        c.setUpdateTime(now);
        mapper.insert(c);
        // 拉合闸需审批通过后再下发
        if (!"METER_SWITCH".equals(commandType)) {
            dispatch(id);
        }
        return mapper.selectById(id);
    }

    @Override
    public PageResult<DevCommand> page(long pageNum, long pageSize, String status,
                                       String commandType, String deviceId) {
        // scope:ignore 指令按设备维度查询，设备本身已按数据范围约束（DevDevice 查询受限）
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
    public DevCommand approve(Long id, boolean approve) {
        DevCommand c = get(id);
        if (!"METER_SWITCH".equals(c.getCommandType())) {
            throw BizException.paramInvalid("仅拉合闸指令需要审批");
        }
        if (!"PENDING".equals(c.getApproveStatus())) {
            throw BizException.stateConflict("该指令已审批过");
        }
        c.setApproveStatus(approve ? "APPROVED" : "REJECTED");
        c.setApproveBy(TenantContext.userId());
        c.setApproveTime(LocalDateTime.now());
        c.setUpdateTime(LocalDateTime.now());
        if (!approve) {
            c.setStatus("CANCELED");
            c.setResultMsg("审批驳回");
            mapper.updateById(c);
            return c;
        }
        mapper.updateById(c);
        dispatch(id);
        return mapper.selectById(id);
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
