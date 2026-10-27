# -*- coding: utf-8 -*-
"""设备批量绑定：后端批量接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'dev',
                 'controller', 'DeviceController.java')
s = io.open(p, encoding='utf-8').read()

if 'bind-batch' not in s:
    code = '''    /**
     * 批量绑定：按「房源编号 + 设备编号」逐行绑定到房源所在空间。
     *
     * <p>逐行返回结果，单行失败不影响其它行。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:update")
    @PostMapping("/bind-batch")
    public R<java.util.Map<String, Object>> bindBatch(
            @RequestBody java.util.List<java.util.Map<String, String>> rows) {
        java.util.List<java.util.Map<String, Object>> results = new java.util.ArrayList<>();
        int ok = 0;
        int line = 0;
        for (java.util.Map<String, String> row : rows == null
                ? java.util.List.<java.util.Map<String, String>>of() : rows) {
            line++;
            String houseCode = row.get("houseCode");
            String deviceNo = row.get("deviceId");
            java.util.Map<String, Object> r = new java.util.LinkedHashMap<>();
            r.put("line", line);
            r.put("houseCode", houseCode);
            r.put("deviceId", deviceNo);
            try {
                if (houseCode == null || houseCode.isBlank()) {
                    throw BizException.paramInvalid("房源编号为空");
                }
                if (deviceNo == null || deviceNo.isBlank()) {
                    throw BizException.paramInvalid("设备编号为空");
                }
                com.yundao.bp.asset.entity.AssetHouse h = houseMapper.selectOne(
                        new LambdaQueryWrapper<com.yundao.bp.asset.entity.AssetHouse>()
                                .eq(com.yundao.bp.asset.entity.AssetHouse::getHouseCode,
                                        houseCode.trim())
                                .last("LIMIT 1"));
                if (h == null) {
                    throw BizException.notFound("房源 " + houseCode);
                }
                if (h.getSpaceId() == null) {
                    throw BizException.stateConflict("房源未关联空间，无法绑定设备");
                }
                DevDevice d = mapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                        .eq(DevDevice::getDeviceId, deviceNo.trim())
                        .last("LIMIT 1"));
                if (d == null) {
                    throw BizException.notFound("设备 " + deviceNo);
                }
                if (d.getSpaceId() != null && !d.getSpaceId().equals(h.getSpaceId())) {
                    throw BizException.stateConflict("该设备已绑定其它空间，请先解绑");
                }
                d.setSpaceId(h.getSpaceId());
                d.setUpdateTime(java.time.LocalDateTime.now());
                mapper.updateById(d);
                r.put("success", true);
                r.put("message", "已绑定到 " + h.getSpaceId());
                ok++;
            } catch (Exception ex) {
                r.put("success", false);
                r.put("message", ex.getMessage() == null ? "绑定失败" : ex.getMessage());
            }
            results.add(r);
        }
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("total", line);
        out.put("success", ok);
        out.put("failed", line - ok);
        out.put("rows", results);
        return R.ok(out);
    }

'''
    s = s.replace('''    /**
     * 空间设备继承：''', code + '''    /**
     * 空间设备继承：''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('批量绑定接口已加')
else:
    print('已存在')
