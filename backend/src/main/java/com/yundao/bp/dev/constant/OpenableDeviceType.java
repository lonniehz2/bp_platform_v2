package com.yundao.bp.dev.constant;

import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 设备类型（对应 {@code bp_dev_device.device_type}）。
 *
 * <p>只有"可开门"类型才参与授权下发；水电气表等计量设备不参与。
 */
public enum OpenableDeviceType {

    LOCK("门锁", true),
    ACCESS("门禁", true),
    ELEVATOR("梯控", true),
    GATE("道闸", true),
    METER_W("水表", false),
    METER_E("电表", false),
    METER_G("燃气表", false),
    GATEWAY("网关", false),
    COLLECTOR("采集器", false),
    BOX("车闸盒子", true),
    VISITOR_CTRL("访客码控制器", true);

    private final String label;
    private final boolean openable;

    OpenableDeviceType(String label, boolean openable) {
        this.label = label;
        this.openable = openable;
    }

    public String label() {
        return label;
    }

    /** 是否可参与开门授权。 */
    public boolean openable() {
        return openable;
    }

    /** 所有可开门类型的名字集合（用于 SQL IN 过滤）。 */
    public static Set<String> openableNames() {
        return Arrays.stream(values()).filter(OpenableDeviceType::openable)
                .map(Enum::name).collect(Collectors.toSet());
    }
}
