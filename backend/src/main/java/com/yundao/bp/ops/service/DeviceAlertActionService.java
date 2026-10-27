package com.yundao.bp.ops.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.dev.entity.DevEvent;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.entity.OpsWorkorder;
import com.yundao.bp.ops.mapper.OpsWorkorderMapper;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * 设备告警联动：严重级别事件自动生成工单（同设备同标题 24 小时内只生成一次）。
 */
@Service
public class DeviceAlertActionService {

    private static final Logger log = LoggerFactory.getLogger(DeviceAlertActionService.class);
    private static final List<String> AUTO_TYPES =
            List.of("DURESS", "TAMPER", "POWER_OVER", "OFFLINE", "LOW_BATTERY");

    private final WorkOrderService workOrderService;
    private final OpsWorkorderMapper workOrderMapper;

    public DeviceAlertActionService(WorkOrderService workOrderService,
                                    OpsWorkorderMapper workOrderMapper) {
        this.workOrderService = workOrderService;
        this.workOrderMapper = workOrderMapper;
    }

    /** 判断是否需要联动，并创建工单。返回工单号或 null。 */
    public String onDeviceEvent(DevEvent e) {
        if (e == null || e.getIdentifier() == null) {
            return null;
        }
        boolean serious = "CRITICAL".equals(e.getEventLevel())
                || AUTO_TYPES.contains(e.getIdentifier());
        if (!serious) {
            return null;
        }
        String title = "设备告警：" + label(e.getIdentifier()) + "（" + e.getDeviceId() + "）";
        Long dup = workOrderMapper.selectCount(new LambdaQueryWrapper<OpsWorkorder>()
                .eq(OpsWorkorder::getDeviceId, e.getDeviceId())
                .eq(OpsWorkorder::getOrderType, "ALERT")
                .ge(OpsWorkorder::getCreateTime, LocalDateTime.now().minusHours(24))
                .ne(OpsWorkorder::getOrderStatus, "CLOSED"));
        if (dup != null && dup > 0) {
            return null;
        }
        try {
            var vo = workOrderService.create(new WorkOrderCreateCmd(
                    "ALERT", "ALERT", title,
                    e.getBody() == null ? "设备事件自动转单" : e.getBody(),
                    e.getOrgId(), e.getSpaceId(), null, e.getDeviceId(), null,
                    null, null, null, null, null, null, null, null));
            return vo == null ? null : vo.workorderNo();
        } catch (Exception ex) {
            log.warn("告警转工单失败 device={}: {}", e.getDeviceId(), ex.getMessage());
            return null;
        }
    }

    private static String label(String id) {
        return switch (id) {
            case "DURESS" -> "胁迫告警";
            case "TAMPER" -> "防拆告警";
            case "POWER_OVER" -> "超功率告警";
            case "OFFLINE" -> "设备离线";
            case "LOW_BATTERY" -> "低电量";
            default -> id;
        };
    }
}
