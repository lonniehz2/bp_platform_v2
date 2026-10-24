package com.yundao.bp.grant.constant;

/**
 * 钥匙类型。
 *
 * <p>{@code code} 对应 IoT 介质模块类型与介质类型编码，
 * 便于下发时直接映射，不在业务层写 if/else。
 */
public enum KeyType {

    FACE("人脸", "06", "601"),
    FINGERPRINT("指纹", "04", "401"),
    PALM_VEIN("掌静脉", "05", "501"),
    PASSWORD("密码", "01", "101"),
    CARD("卡片", "02", "201"),
    IDCARD("身份证", "02", "202"),
    QRCODE("二维码", "07", "701"),
    OFFLINE_CODE("离线激活码", "08", "801");

    private final String label;
    private final String moduleType;
    private final String channelType;

    KeyType(String label, String moduleType, String channelType) {
        this.label = label;
        this.moduleType = moduleType;
        this.channelType = channelType;
    }

    public String label() {
        return label;
    }

    public String moduleType() {
        return moduleType;
    }

    public String channelType() {
        return channelType;
    }

    public static KeyType of(String code) {
        for (KeyType t : values()) {
            if (t.name().equals(code)) {
                return t;
            }
        }
        return null;
    }
}
