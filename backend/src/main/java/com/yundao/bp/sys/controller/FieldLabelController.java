package com.yundao.bp.sys.controller;

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

    @com.yundao.bp.iam.security.RequirePerm("sys:field-labels:view")
    @GetMapping
    public R<Map<String, String>> labels() {
        return R.ok(fieldLabelService.labels());
    }

    /** DDL 变更后手动刷新缓存 */
    @com.yundao.bp.iam.security.RequirePerm("sys:field-labels:create")
    @PostMapping("/refresh")
    public R<Integer> refresh() {
        fieldLabelService.refresh();
        return R.ok(fieldLabelService.labels().size());
    }
}
