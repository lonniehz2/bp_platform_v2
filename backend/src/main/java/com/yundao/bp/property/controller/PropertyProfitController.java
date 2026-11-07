package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyProfitService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业支出与经营报表。 */
@RestController
@RequestMapping("/api/v1/property")
public class PropertyProfitController {

    private final PropertyProfitService service;

    public PropertyProfitController(PropertyProfitService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:expense:view")
    @GetMapping("/expenses")
    public R<List<Map<String, Object>>> expenses(@RequestParam Long projectId,
                                                 @RequestParam(required = false) String month) {
        return R.ok(service.expenses(projectId, month));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:expense:edit")
    @PostMapping("/expenses")
    public R<Map<String, Object>> create(@RequestParam Long projectId,
            @RequestBody PropertyProfitService.ExpenseCmd cmd) {
        return R.ok(service.createExpense(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:expense:edit")
    @DeleteMapping("/expenses/{id}")
    public R<Map<String, Object>> delete(@PathVariable Long id) {
        return R.ok(service.deleteExpense(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:report:view")
    @GetMapping("/reports/overview")
    public R<Map<String, Object>> overview(@RequestParam Long projectId,
                                           @RequestParam(required = false) String month) {
        return R.ok(service.overview(projectId, month));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:expense:view")
    @GetMapping("/expense-categories")
    public R<List<Map<String, Object>>> categories() {
        return R.ok(service.expenseCategories());
    }
}
