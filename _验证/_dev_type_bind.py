# -*- coding: utf-8 -*-
"""设备分类细化 + 按类型查询 + 空间绑定接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'dev')

ENUM = '''package com.yundao.bp.dev.constant;

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
'''
p = os.path.join(J, 'constant', 'DevDeviceType.java')
io.open(p, 'w', encoding='utf-8', newline='').write(ENUM)
print('已创建 DevDeviceType')

# ---------- 控制器：类型筛选 + 类型清单 + 绑定/解绑 ----------
C = os.path.join(J, 'controller', 'DeviceController.java')
s = io.open(C, encoding='utf-8').read()

if 'deviceType' not in s:
    s = s.replace('''            @RequestParam(required = false) Integer onlineStatus) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<>()
                .eq(spaceId != null, DevDevice::getSpaceId, spaceId)''',
'''            @RequestParam(required = false) Integer onlineStatus,
            @RequestParam(required = false) String deviceType) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<>()
                .eq(spaceId != null, DevDevice::getSpaceId, spaceId)
                .eq(deviceType != null && !deviceType.isBlank(),
                        DevDevice::getDeviceType, deviceType)''')
    print('DeviceController：已加 deviceType 筛选')

BIND = '''
    /** 设备分类清单（具体分类 + 大类）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/types")
    public R<java.util.List<java.util.Map<String, Object>>> types() {
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (com.yundao.bp.dev.constant.DevDeviceType t
                : com.yundao.bp.dev.constant.DevDeviceType.values()) {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("code", t.name());
            m.put("label", t.label());
            m.put("category", t.category());
            long n = mapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceType, t.name()));
            m.put("count", n);
            out.add(m);
        }
        return R.ok(out);
    }

    /** 设备挂到空间（绑定）。spaceId 置空即解绑。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:update")
    @PostMapping("/{id}/bind")
    public R<DevDevice> bind(@PathVariable Long id,
                             @RequestBody java.util.Map<String, Object> body) {
        DevDevice d = mapper.selectById(id);
        if (d == null) {
            throw BizException.notFound("设备");
        }
        Object raw = body == null ? null : body.get("spaceId");
        if (raw == null || String.valueOf(raw).isBlank()
                || "null".equals(String.valueOf(raw))) {
            d.setSpaceId(null);
        } else {
            Long spaceId = Long.valueOf(String.valueOf(raw));
            if (spaceMapper.selectById(spaceId) == null) {
                throw BizException.notFound("空间");
            }
            d.setSpaceId(spaceId);
        }
        d.setUpdateTime(java.time.LocalDateTime.now());
        mapper.updateById(d);
        return R.ok(d);
    }

    /** 未绑定任何空间的设备（供绑定弹窗选择）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/unbound")
    public R<java.util.List<DevDevice>> unbound(
            @RequestParam(required = false) String deviceType) {
        return R.ok(mapper.selectList(new LambdaQueryWrapper<DevDevice>()
                .isNull(DevDevice::getSpaceId)
                .eq(deviceType != null && !deviceType.isBlank(),
                        DevDevice::getDeviceType, deviceType)
                .orderByDesc(DevDevice::getId)));
    }
'''
if '/bind' not in s:
    anchor = '    /** 空间设备继承：给定房源，沿空间祖先链收集可授权设备。'
    s = s.replace(anchor, BIND + '\n' + anchor, 1)
    print('DeviceController：已加 /types、/bind、/unbound')

io.open(C, 'w', encoding='utf-8', newline='').write(s)
print('完成')
