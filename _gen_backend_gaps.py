# -*- coding: utf-8 -*-
"""补后端两处能力：设备列表接口 + 公示结束接口"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

# ==================== 1) 设备列表控制器 ====================
F['dev/controller/DeviceController.java'] = '''package com.yundao.bp.dev.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 设备查询接口。
 *
 * <p><b>补齐说明</b>：此前只有「门锁绑定解析」，没有设备列表接口，
 * 导致前端「设备管理」页无处可查。本控制器只做<b>查询</b>，
 * 设备注册/绑定仍由 IoT 侧与绑定流程负责。
 */
@RestController
@RequestMapping("/api/v1/devices")
public class DeviceController {

    private final DevDeviceMapper mapper;

    public DeviceController(DevDeviceMapper mapper) {
        this.mapper = mapper;
    }

    /** 分页查询设备（可按空间/房源/门锁ID 过滤）。 */
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
                .orderByDesc(DevDevice::getId);
        IPage<DevDevice> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return R.ok(PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords()));
    }

    /** 设备详情。 */
    @GetMapping("/{id}")
    public R<DevDevice> get(@PathVariable Long id) {
        DevDevice d = mapper.selectById(id);
        if (d == null) {
            throw BizException.notFound("设备");
        }
        return R.ok(d);
    }

    /** 在线/绑定状态统计（看板用）。 */
    @GetMapping("/stats")
    public R<java.util.Map<String, Object>> stats() {
        Long total = mapper.selectCount(new LambdaQueryWrapper<>());
        java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("total", total == null ? 0 : total);
        return R.ok(m);
    }
}
'''

# ==================== 2) 公示结束/发布接口 ====================
F['biz/controller/PublicityOpsController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.PublicityVO;
import com.yundao.bp.biz.service.PublicityService;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.sys.audit.Audit;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 公示状态流转接口（发布 / 结束）。
 *
 * <p><b>补齐说明</b>：前端此前调用 {@code /publicities/{id}/finish}，
 * 而后端服务只有 {@code publish} 与 {@code close}。本控制器把两个真实动作
 * 暴露为 REST 接口，前端改为调用 {@code /close}。
 *
 * <p><b>合规要点</b>：配租公示必须是「已发布 + 满 7 自然日 + 已结束」才能签约，
 * 因此结束公示是一个有业务后果的动作，记 IMPORTANT 审计。
 */
@RestController
@RequestMapping("/api/v1/publicities")
public class PublicityOpsController {

    private final PublicityService service;

    public PublicityOpsController(PublicityService service) {
        this.service = service;
    }

    /** 发布公示。 */
    @PostMapping("/{id}/publish")
    @RequirePerm("biz:publicity:manage")
    @Audit(type = "DATA", level = "IMPORTANT", action = "发布公示")
    public R<PublicityVO> publish(@PathVariable Long id) {
        return R.ok(service.publish(id));
    }

    /** ⭐ 结束公示（结束后才满足配租签约的公示条件）。 */
    @PostMapping("/{id}/close")
    @RequirePerm("biz:publicity:manage")
    @Audit(type = "DATA", level = "IMPORTANT", action = "结束公示")
    public R<PublicityVO> close(@PathVariable Long id,
                                @RequestBody(required = false) CloseCmd cmd) {
        return R.ok(service.close(id, cmd == null ? null : cmd.remark()));
    }

    public record CloseCmd(String remark) {
    }
}
'''

for rel, content in F.items():
    p = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8').write(content)
    print('  + ' + rel)
