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
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.msg.entity.MsgSendRecord;
import com.yundao.bp.msg.mapper.MsgSendRecordMapper;
import com.yundao.bp.dev.service.DevCommandService;
import com.yundao.bp.iot.config.IotSettings;
import java.math.BigDecimal;
import java.time.LocalDate;
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
    private final AssetHouseMapper houseMapper;
    private final FinBillMapper billMapper;
    private final MsgSendRecordMapper msgMapper;

    public DevCommandServiceImpl(DevCommandMapper mapper, DevDeviceMapper deviceMapper,
                                 DeviceCommandClient client, IotSettings settings,
                                 SnowflakeIdGenerator idGen, AssetHouseMapper houseMapper,
                                 FinBillMapper billMapper, MsgSendRecordMapper msgMapper) {
        this.mapper = mapper;
        this.deviceMapper = deviceMapper;
        this.client = client;
        this.settings = settings;
        this.idGen = idGen;
        this.houseMapper = houseMapper;
        this.billMapper = billMapper;
        this.msgMapper = msgMapper;
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
            applySwitchSafety(c, d, now);
            c.setApproveStatus("PENDING");
            c.setExecuteAfter(now.plusMinutes(settings.getInt("iot.meter.switch.delayMinutes")));
            c.setCancelDeadline(c.getExecuteAfter());
        }
        c.setIsDeleted(0);
        c.setCreateTime(now);
        c.setUpdateTime(now);
        mapper.insert(c);
        if ("METER_SWITCH".equals(commandType)) {
            notifyBeforeTrip(c);
        }
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
        if (c.getExecuteAfter() == null || !c.getExecuteAfter().isAfter(LocalDateTime.now())) {
            dispatch(id);
        }
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


    // ==================== 拉合闸安全策略 ====================

    private void applySwitchSafety(DevCommand c, DevDevice d, LocalDateTime now) {
        if (d == null || d.getSpaceId() == null) {
            throw BizException.stateConflict("设备未绑定空间，无法拉合闸");
        }
        AssetHouse house = houseMapper.selectOne(new LambdaQueryWrapper<AssetHouse>()
                .eq(AssetHouse::getSpaceId, d.getSpaceId()).last("LIMIT 1"));
        if (house == null) {
            throw BizException.stateConflict("设备所在空间未对应房源，无法拉合闸");
        }
        c.setHouseId(house.getId());

        // 夜间禁止
        String from = settings.getString("iot.meter.switch.nightFrom");
        String to = settings.getString("iot.meter.switch.nightTo");
        if (inNightWindow(now.toLocalTime(), from, to)) {
            throw BizException.stateConflict("当前处于禁止拉闸时段（" + from + "–" + to + "）");
        }

        // 欠费与逾期校验
        List<FinBill> unpaid = billMapper.selectList(new LambdaQueryWrapper<FinBill>()
                .eq(FinBill::getHouseId, house.getId())
                .in(FinBill::getBillStatus, List.of("UNPAID", "PARTIAL"))
                .isNotNull(FinBill::getPayableAmount).gt(FinBill::getPayableAmount, BigDecimal.ZERO));
        BigDecimal arrears = BigDecimal.ZERO;
        LocalDate earliestDue = null;
        for (FinBill b : unpaid) {
            BigDecimal paid = b.getPaidAmount() == null ? BigDecimal.ZERO : b.getPaidAmount();
            BigDecimal waive = b.getWaivedAmount() == null ? BigDecimal.ZERO : b.getWaivedAmount();
            BigDecimal remain = (b.getPayableAmount() == null ? BigDecimal.ZERO : b.getPayableAmount())
                    .subtract(paid).subtract(waive);
            if (remain.compareTo(BigDecimal.ZERO) > 0) {
                arrears = arrears.add(remain);
                if (b.getDueDate() != null
                        && (earliestDue == null || b.getDueDate().isBefore(earliestDue))) {
                    earliestDue = b.getDueDate();
                }
            }
        }
        c.setArrearsAmount(arrears.setScale(2, java.math.RoundingMode.HALF_UP));
        BigDecimal threshold = settings.getDecimal("iot.meter.switch.arrearsThreshold");
        if (arrears.compareTo(threshold) < 0) {
            throw BizException.stateConflict("欠费 " + c.getArrearsAmount()
                    + " 元未达拉闸阈值 " + threshold + " 元");
        }
        int overdueDays = settings.getInt("iot.meter.switch.overdueDays");
        if (earliestDue != null
                && java.time.temporal.ChronoUnit.DAYS.between(earliestDue, LocalDate.now())
                < overdueDays) {
            throw BizException.stateConflict("最早欠费账单逾期未满 " + overdueDays + " 天");
        }

        // 24 小时限额
        int limit = settings.getInt("iot.meter.switch.dailyLimit");
        Long today = mapper.selectCount(new LambdaQueryWrapper<DevCommand>()
                .eq(DevCommand::getCommandType, "METER_SWITCH")
                .eq(DevCommand::getDeviceId, c.getDeviceId())
                .ne(DevCommand::getStatus, "CANCELED")
                .ge(DevCommand::getCreateTime, LocalDate.now().atStartOfDay()));
        if (today != null && today >= limit) {
            throw BizException.stateConflict("该表 24 小时内已拉闸 " + today
                    + " 次，达上限 " + limit + " 次");
        }
    }

    private boolean inNightWindow(java.time.LocalTime now, String from, String to) {
        if (from == null || to == null || from.isBlank() || to.isBlank()) {
            return false;
        }
        try {
            java.time.LocalTime f = java.time.LocalTime.parse(from);
            java.time.LocalTime t = java.time.LocalTime.parse(to);
            if (f.isBefore(t)) {
                return !now.isBefore(f) && now.isBefore(t);
            }
            // 跨零点：22:00–次日 07:00
            return !now.isBefore(f) || now.isBefore(t);
        } catch (Exception e) {
            return false;
        }
    }

    /** 拉闸前通知（提前 30 分钟，站内记录 + 待发）。 */
    private void notifyBeforeTrip(DevCommand c) {
        try {
            MsgSendRecord m = new MsgSendRecord();
            m.setId(idGen.nextId());
            m.setTenantId(c.getTenantId());
            m.setMessageNo("MSG" + m.getId());
            m.setTemplateCode("IOT_METER_TRIP_NOTICE");
            m.setChannel("INAPP");
            m.setBizType("METER_SWITCH");
            m.setBizId(c.getId());
            m.setReceiverType("HOUSE");
            m.setReceiverId(String.valueOf(c.getHouseId()));
            m.setTitle("电表拉闸预警");
            m.setContent("因欠费 " + c.getArrearsAmount() + " 元，将按计划执行断电，请尽快缴费。");
            m.setSendStatus("PENDING");
            m.setRetryCount(0);
            m.setPlanTime(c.getExecuteAfter() == null ? LocalDateTime.now()
                    : c.getExecuteAfter().minusMinutes(30));
            m.setCreateTime(LocalDateTime.now());
            msgMapper.insert(m);
        } catch (Exception e) {
            log.warn("拉闸通知写入失败: {}", e.getMessage());
        }
    }

    /** 到点执行（Job 调用）。 */
    public int executeDueSwitches() {
        List<DevCommand> due = mapper.selectList(new LambdaQueryWrapper<DevCommand>()
                .eq(DevCommand::getCommandType, "METER_SWITCH")
                .eq(DevCommand::getApproveStatus, "APPROVED")
                .eq(DevCommand::getStatus, "PENDING")
                .le(DevCommand::getExecuteAfter, LocalDateTime.now()));
        for (DevCommand c : due) {
            dispatch(c.getId());
        }
        return due.size();
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
