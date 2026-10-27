# -*- coding: utf-8 -*-
"""拉合闸安全策略 + 离线判定 + 联调工具（后端）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


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


def write(rel, body):
    path = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print('跳过(已存在)', rel)
        return
    io.open(path, 'w', encoding='utf-8', newline='').write(body)
    print('创建', rel)


# 1) 实体补字段
patch('dev/entity/DevCommand.java',
      '    private String reason;',
      '''    private String reason;

    /** 拉合闸：账单欠费金额快照 */
    private java.math.BigDecimal arrearsAmount;
    /** 拉合闸：目标房源 */
    private Long houseId;''')

patch('dev/entity/DevCommand.java',
      '    private LocalDateTime timeoutAt;',
      '''    private LocalDateTime timeoutAt;

    /** 拉合闸：延迟执行时间（到点才下发） */
    private LocalDateTime executeAfter;
    /** 拉合闸：可撤销截止时间（= executeAfter） */
    private LocalDateTime cancelDeadline;''')

# 2) 参数默认值
patch('iot/config/IotSettings.java',
      '        DEFAULTS.put("iot.meter.switch.delayMinutes", "10");',
      '''        DEFAULTS.put("iot.meter.switch.delayMinutes", "10");
        DEFAULTS.put("iot.meter.switch.arrearsThreshold", "0.01");
        DEFAULTS.put("iot.meter.switch.overdueDays", "30");
        DEFAULTS.put("iot.meter.switch.nightFrom", "22:00");
        DEFAULTS.put("iot.meter.switch.nightTo", "07:00");
        DEFAULTS.put("iot.meter.switch.dailyLimit", "3");''')

# 3) 服务：前置校验 + 延迟执行
OLD_CREATE = '''        if ("METER_SWITCH".equals(commandType)) {
            c.setApproveStatus("PENDING");
        }
        c.setIsDeleted(0);
        c.setCreateTime(now);
        c.setUpdateTime(now);
        mapper.insert(c);'''
NEW_CREATE = '''        if ("METER_SWITCH".equals(commandType)) {
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
        }'''
patch('dev/service/impl/DevCommandServiceImpl.java', OLD_CREATE, NEW_CREATE)

# 4) 追加安全校验/通知/时间判断方法
HELPERS = '''
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
                .in(FinBill::getStatus, List.of("UNPAID", "PARTIAL"))
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
'''
patch('dev/service/impl/DevCommandServiceImpl.java',
      '    /** 超时扫描：由 Job 调用。 */',
      HELPERS + '\n    /** 超时扫描：由 Job 调用。 */')

# 5) 依赖注入：房源/账单/消息
patch('dev/service/impl/DevCommandServiceImpl.java',
      'import com.yundao.bp.dev.service.DevCommandService;',
      '''import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.msg.entity.MsgSendRecord;
import com.yundao.bp.msg.mapper.MsgSendRecordMapper;
import com.yundao.bp.dev.service.DevCommandService;''')

patch('dev/service/impl/DevCommandServiceImpl.java',
      '    private final SnowflakeIdGenerator idGen;',
      '''    private final SnowflakeIdGenerator idGen;
    private final AssetHouseMapper houseMapper;
    private final FinBillMapper billMapper;
    private final MsgSendRecordMapper msgMapper;''')

patch('dev/service/impl/DevCommandServiceImpl.java',
      '''                                 DeviceCommandClient client, IotSettings settings,
                                 SnowflakeIdGenerator idGen) {''',
      '''                                 DeviceCommandClient client, IotSettings settings,
                                 SnowflakeIdGenerator idGen, AssetHouseMapper houseMapper,
                                 FinBillMapper billMapper, MsgSendRecordMapper msgMapper) {''')

patch('dev/service/impl/DevCommandServiceImpl.java',
      '        this.idGen = idGen;',
      '''        this.idGen = idGen;
        this.houseMapper = houseMapper;
        this.billMapper = billMapper;
        this.msgMapper = msgMapper;''')

# 6) 审批：通过后若已到执行时间立即下发，否则等 Job
patch('dev/service/impl/DevCommandServiceImpl.java',
      '''        mapper.updateById(c);
        dispatch(id);
        return mapper.selectById(id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispatch(Long id) {''',
      '''        mapper.updateById(c);
        if (c.getExecuteAfter() == null || !c.getExecuteAfter().isAfter(LocalDateTime.now())) {
            dispatch(id);
        }
        return mapper.selectById(id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispatch(Long id) {''')

print('拉合闸策略完成')
