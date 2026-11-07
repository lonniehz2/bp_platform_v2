package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.entity.PropCategory;
import com.yundao.bp.property.service.PropertyCategoryService;
import java.util.List;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业收入/支出分类。 */
@RestController
@RequestMapping("/api/v1/property/categories")
public class PropertyCategoryController {

    private final PropertyCategoryService service;

    public PropertyCategoryController(PropertyCategoryService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:category:view")
    @GetMapping
    public R<List<PropCategory>> list(@RequestParam(required = false) String type) {
        return R.ok(service.list(type));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:category:manage")
    @PostMapping
    public R<PropCategory> create(@RequestBody PropertyCategoryService.CreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:category:manage")
    @PutMapping("/{id}")
    public R<PropCategory> update(@PathVariable Long id,
                                  @RequestBody PropertyCategoryService.UpdateCmd cmd) {
        return R.ok(service.update(id, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:category:manage")
    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        service.delete(id);
        return R.ok();
    }
}
