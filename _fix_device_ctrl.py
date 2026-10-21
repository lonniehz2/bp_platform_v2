# -*- coding: utf-8 -*-
"""修正 DeviceController：按 DevDevice 真实字段（deviceId/spaceId/deviceMac）过滤"""
import io

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\dev\controller\DeviceController.java')
s = io.open(P, encoding='utf-8').read()

old = '''    /** 分页查询设备（可按空间/房源/门锁ID 过滤）。 */
    @GetMapping
    public R<PageResult<DevDevice>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long spaceId,
            @RequestParam(required = false) Long houseId,
            @RequestParam(required = false) String lockId) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<DevDevice>()
                .eq(spaceId != null, DevDevice::getSpaceId, spaceId)
                .eq(houseId != null, DevDevice::getHouseId, houseId)
                .eq(lockId != null && !lockId.isBlank(), DevDevice::getLockId, lockId)
                .orderByDesc(DevDevice::getId);'''

new = '''    /**
     * 分页查询设备。
     *
     * <p>过滤维度按 `bp_dev_device` 实际字段：spaceId / deviceId / deviceMac /
     * onlineStatus。该表<b>没有</b> houseId / lockId 列——门锁与房源的关系
     * 由绑定记录与空间层级推导，不在设备表冗余。
     */
    @GetMapping
    public R<PageResult<DevDevice>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long spaceId,
            @RequestParam(required = false) String deviceId,
            @RequestParam(required = false) String deviceMac,
            @RequestParam(required = false) Integer onlineStatus) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<DevDevice>()
                .eq(spaceId != null, DevDevice::getSpaceId, spaceId)
                .eq(deviceId != null && !deviceId.isBlank(),
                        DevDevice::getDeviceId, deviceId)
                .like(deviceMac != null && !deviceMac.isBlank(),
                        DevDevice::getDeviceMac, deviceMac)
                .eq(onlineStatus != null, DevDevice::getOnlineStatus, onlineStatus)
                .orderByDesc(DevDevice::getId);'''

assert old in s, '锚点缺失'
s = s.replace(old, new, 1)

# stats 补在线/离线计数
old2 = '''    @GetMapping("/stats")
    public R<java.util.Map<String, Object>> stats() {
        Long total = mapper.selectCount(new LambdaQueryWrapper<>());
        java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("total", total == null ? 0 : total);
        return R.ok(m);
    }'''
new2 = '''    @GetMapping("/stats")
    public R<java.util.Map<String, Object>> stats() {
        long total = orZero(mapper.selectCount(new LambdaQueryWrapper<>()));
        long online = orZero(mapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getOnlineStatus, 1)));
        java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("total", total);
        m.put("online", online);
        m.put("offline", total - online);
        m.put("onlineRate", total == 0 ? 0.0
                : Math.round(online * 10000.0 / total) / 100.0);
        return R.ok(m);
    }

    private static long orZero(Long v) {
        return v == null ? 0 : v;
    }'''
assert old2 in s
s = s.replace(old2, new2, 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('已按真实字段修正 DeviceController')
