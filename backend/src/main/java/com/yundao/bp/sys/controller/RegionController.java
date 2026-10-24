package com.yundao.bp.sys.controller;

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

    /** 子级列表（parentCode 为空返回省级）；code 可按下级代码反查其父级下的兄弟节点。 */
    @GetMapping("/children")
    public R<List<Map<String, Object>>> children(
            @RequestParam(required = false) String parentCode,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String code) {
        String parent = parentCode;
        if ((parent == null || parent.isBlank()) && code != null && !code.isBlank()) {
            SysRegion self = mapper.selectById(code);
            parent = self == null ? null : self.getParentCode();
        }
        LambdaQueryWrapper<SysRegion> qw = new LambdaQueryWrapper<>();
        if (parent == null || parent.isBlank()) {
            qw.eq(SysRegion::getLevel, 1);
        } else {
            qw.eq(SysRegion::getParentCode, parent);
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
