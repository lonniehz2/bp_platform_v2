package com.yundao.bp.dev.constant;

/**
 * 设备具体分类。
 *
 * <p>业务上按「具体设备」区分（门锁 / 门禁 / 道闸 / 水表 / 电表 / 燃气表），
 * {@code category} 只是便于理解的大类（通行设备 / 计量设备 / 安防设备）。
 */
public enum DevDeviceType {

    LOCK("门锁", "通行设备"),
    ACCESS("门禁", "通行设备"),
    BARRIER("道闸", "通行设备"),
    ELEVATOR("梯控", "通行设备"),
    WATER_METER("水表", "计量设备"),
    ELEC_METER("电表", "计量设备"),
    GAS_METER("燃气表", "计量设备"),
    HEAT_METER("热量表", "计量设备"),
    CAMERA("摄像头", "安防设备"),
    SENSOR("传感器", "安防设备"),
    OTHER("其他", "其他");

    private final String label;
    private final String category;

    DevDeviceType(String label, String category) {
        this.label = label;
        this.category = category;
    }

    public String label() { return label; }
    public String category() { return category; }

    public static DevDeviceType of(String code) {
        if (code == null) {
            return OTHER;
        }
        for (DevDeviceType t : values()) {
            if (t.name().equalsIgnoreCase(code)) {
                return t;
            }
        }
        return OTHER;
    }
}
