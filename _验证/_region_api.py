# -*- coding: utf-8 -*-
"""五级行政区划查询接口：懒加载级联（按父级取子级）+ 按代码取路径。

接口：
  GET /sys/regions/children?parentCode=     父级下的子级（parentCode 为空取省级）
  GET /sys/regions/path?code=               从省到该级的名称路径
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'sys')
PKG = 'com.yundao.bp.sys'

ENTITY = '''package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

/**
 * 全国五级行政区划（省/市/区县/街道乡镇/社区村）。
 *
 * <p>数据来源：国家统计局行政区划代码；用于组织地址的级联选择。
 */
@TableName("bp_sys_region")
public class SysRegion {

    /** 行政区划代码（12 位） */
    @TableId
    private String code;

    private String name;

    private String parentCode;

    /** 1=省 2=市 3=区县 4=街道乡镇 5=社区村 */
    private Integer level;

    private Integer hasChild;

    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getParentCode() { return parentCode; }
    public void setParentCode(String parentCode) { this.parentCode = parentCode; }

    public Integer getLevel() { return level; }
    public void setLevel(Integer level) { this.level = level; }

    public Integer getHasChild() { return hasChild; }
    public void setHasChild(Integer hasChild) { this.hasChild = hasChild; }
}
'''

MAPPER = '''package com.yundao.bp.sys.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.sys.entity.SysRegion;
import org.apache.ibatis.annotations.Mapper;

/** 行政区划。 */
@Mapper
public interface SysRegionMapper extends BaseMapper<SysRegion> {
}
'''

CONTROLLER = '''package com.yundao.bp.sys.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.R;
import com.yundao.bp.sys.entity.SysRegion;
import com.yundao.bp.sys.mapper.SysRegionMapper;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 五级行政区划懒加载。
 *
 * <p>前端级联选择器逐级请求：先取省级，再按 parentCode 取下级，避免一次加载 60 万行。
 */
@RestController
@RequestMapping("/api/v1/sys/regions")
public class RegionController {

    private final SysRegionMapper mapper;

    public RegionController(SysRegionMapper mapper) {
        this.mapper = mapper;
    }

    /** 子级列表（parentCode 为空返回省级）。 */
    @GetMapping("/children")
    public R<List<Map<String, Object>>> children(
            @RequestParam(required = false) String parentCode,
            @RequestParam(required = false) String keyword) {
        LambdaQueryWrapper<SysRegion> qw = new LambdaQueryWrapper<>();
        if (parentCode == null || parentCode.isBlank()) {
            qw.eq(SysRegion::getLevel, 1);
        } else {
            qw.eq(SysRegion::getParentCode, parentCode);
        }
        if (keyword != null && !keyword.isBlank()) {
            qw.like(SysRegion::getName, keyword);
        }
        qw.orderByAsc(SysRegion::getCode).last("limit 500");
        List<Map<String, Object>> out = new ArrayList<>();
        for (SysRegion r : mapper.selectList(qw)) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("code", r.getCode());
            m.put("name", r.getName());
            m.put("level", r.getLevel());
            m.put("leaf", r.getHasChild() == null || r.getHasChild() == 0);
            out.add(m);
        }
        return R.ok(out);
    }

    /** 按代码返回从省到该级的路径。 */
    @GetMapping("/path")
    public R<List<Map<String, Object>>> path(@RequestParam String code) {
        List<Map<String, Object>> out = new ArrayList<>();
        String cur = code;
        int guard = 0;
        while (cur != null && guard++ < 8) {
            SysRegion r = mapper.selectById(cur);
            if (r == null) {
                break;
            }
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("code", r.getCode());
            m.put("name", r.getName());
            m.put("level", r.getLevel());
            out.add(0, m);
            cur = r.getParentCode();
        }
        return R.ok(out);
    }
}
'''

for path, content in [
    (os.path.join(J, 'entity', 'SysRegion.java'), ENTITY),
    (os.path.join(J, 'mapper', 'SysRegionMapper.java'), MAPPER),
    (os.path.join(J, 'controller', 'RegionController.java'), CONTROLLER),
]:
    if os.path.exists(path):
        print('已存在', os.path.basename(path))
        continue
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8', newline='').write(content)
    print('已创建', os.path.basename(path))
