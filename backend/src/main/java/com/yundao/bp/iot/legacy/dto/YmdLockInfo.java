package com.yundao.bp.iot.legacy.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 门锁信息（{@code getPtAgentLocks} / {@code getLockInfo} 返回项）。
 *
 * <p>字段名与平台返回一致（全小写，无下划线转换），故用 {@code @JsonProperty} 显式映射。
 *
 * <p>⚠️ 实测要点：
 * <ul>
 *   <li>{@code onlineStatus}：{@code "0"} 离线 / {@code "1"} 在线</li>
 *   <li>{@code battery}：形如 {@code "43%"}；<b>门禁类设备为 null</b></li>
 * </ul>
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class YmdLockInfo {

    @JsonProperty("lockid")
    private String lockId;

    @JsonProperty("mac")
    private String mac;

    @JsonProperty("lockname")
    private String lockName;

    /** "0" 离线 / "1" 在线 */
    @JsonProperty("onlineStatus")
    private String onlineStatus;

    /** 形如 "43%"，门禁类设备可能为 null */
    @JsonProperty("battery")
    private String battery;

    @JsonProperty("ventor")
    private String ventor;

    @JsonProperty("hdver")
    private String hdver;

    @JsonProperty("rssi")
    private String rssi;

    @JsonProperty("ischarge")
    private String isCharge;

    @JsonProperty("createtime")
    private String createTime;

    @JsonProperty("address2")
    private String address;

    /** 是否在线。 */
    public boolean online() {
        return "1".equals(onlineStatus);
    }

    /** 电量百分比（无电量信息返回 null）。 */
    public Integer batteryPercent() {
        if (battery == null) {
            return null;
        }
        String digits = battery.replaceAll("[^0-9]", "");
        return digits.isEmpty() ? null : Integer.valueOf(digits);
    }

    // ---------- getter / setter ----------
    public String getLockId() { return lockId; }
    public void setLockId(String lockId) { this.lockId = lockId; }
    public String getMac() { return mac; }
    public void setMac(String mac) { this.mac = mac; }
    public String getLockName() { return lockName; }
    public void setLockName(String lockName) { this.lockName = lockName; }
    public String getOnlineStatus() { return onlineStatus; }
    public void setOnlineStatus(String onlineStatus) { this.onlineStatus = onlineStatus; }
    public String getBattery() { return battery; }
    public void setBattery(String battery) { this.battery = battery; }
    public String getVentor() { return ventor; }
    public void setVentor(String ventor) { this.ventor = ventor; }
    public String getHdver() { return hdver; }
    public void setHdver(String hdver) { this.hdver = hdver; }
    public String getRssi() { return rssi; }
    public void setRssi(String rssi) { this.rssi = rssi; }
    public String getIsCharge() { return isCharge; }
    public void setIsCharge(String isCharge) { this.isCharge = isCharge; }
    public String getCreateTime() { return createTime; }
    public void setCreateTime(String createTime) { this.createTime = createTime; }
    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }
}
