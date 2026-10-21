# -*- coding: utf-8 -*-
"""后端提供字段中文名字典：从 information_schema 列注释生成"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

SVC = '''package com.yundao.bp.sys.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 字段中文名字典。
 *
 * <p>数据来源：MySQL {@code information_schema.columns.column_comment}。
 * 本项目 DDL 要求列注释 100% 覆盖（有校验脚本保证），因此可以直接
 * 用「列注释」当字段中文名，**新增字段无需改前端字典**。</p>
 *
 * <p>同时做 camelCase ↔ snake_case 双向对齐，前端按 camelCase 取用。</p>
 */
@Service
public class FieldLabelService {

    private final JdbcTemplate jdbcTemplate;

    /** 简单缓存：字典不常变化，进程内缓存足够 */
    private volatile Map<String, String> cache;

    public FieldLabelService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public Map<String, String> labels() {
        Map<String, String> local = cache;
        if (local != null) {
            return local;
        }
        synchronized (this) {
            if (cache != null) {
                return cache;
            }
            Map<String, String> map = new HashMap<>(4096);
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                    "SELECT column_name AS cn, column_comment AS cc "
                            + "FROM information_schema.columns "
                            + "WHERE table_schema = DATABASE() "
                            + "AND column_comment IS NOT NULL AND column_comment <> ''");
            for (Map<String, Object> r : rows) {
                String col = String.valueOf(r.get("cn"));
                String comment = String.valueOf(r.get("cc"));
                if (comment.isBlank()) {
                    continue;
                }
                // 去掉注释里的单位/枚举提示，保留主体中文，如「面积(㎡)」→「面积」
                String label = comment.replaceAll("\\\\([^)]*\\\\)", "").trim();
                if (label.isBlank()) {
                    label = comment;
                }
                String camel = toCamel(col);
                // 同一 camel 名可能来自多张表：优先保留更短/更具体的注释
                map.merge(camel, label,
                        (a, b) -> a.length() <= b.length() ? a : b);
            }
            cache = map;
            return map;
        }
    }

    /** 失效缓存（DDL 变更后调用） */
    public void refresh() {
        cache = null;
    }

    private static String toCamel(String snake) {
        StringBuilder sb = new StringBuilder(snake.length());
        boolean upper = false;
        for (int i = 0; i < snake.length(); i++) {
            char c = snake.charAt(i);
            if (c == '_') {
                upper = true;
                continue;
            }
            sb.append(upper ? Character.toUpperCase(c) : c);
            upper = false;
        }
        return sb.toString();
    }
}
'''

CTL = '''package com.yundao.bp.sys.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.sys.service.FieldLabelService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * 字段中文名字典接口（前端详情/表单展示用）。
 */
@RestController
@RequestMapping("/api/v1/sys/field-labels")
public class FieldLabelController {

    private final FieldLabelService fieldLabelService;

    public FieldLabelController(FieldLabelService fieldLabelService) {
        this.fieldLabelService = fieldLabelService;
    }

    @GetMapping
    public R<Map<String, String>> labels() {
        return R.ok(fieldLabelService.labels());
    }

    /** DDL 变更后手动刷新缓存 */
    @PostMapping("/refresh")
    public R<Integer> refresh() {
        fieldLabelService.refresh();
        return R.ok(fieldLabelService.labels().size());
    }
}
'''

os.makedirs(os.path.join(BASE, 'sys', 'controller'), exist_ok=True)
io.open(os.path.join(BASE, 'sys', 'service', 'FieldLabelService.java'), 'w',
        encoding='utf-8').write(SVC)
io.open(os.path.join(BASE, 'sys', 'controller', 'FieldLabelController.java'), 'w',
        encoding='utf-8').write(CTL)
print('  ✓ FieldLabelService + FieldLabelController（/api/v1/sys/field-labels）')
