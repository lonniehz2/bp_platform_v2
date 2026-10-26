package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.BillingRuleCreateCmd;
import com.yundao.bp.fin.dto.CalcPreviewCmd;
import com.yundao.bp.fin.dto.FeeItemCreateCmd;
import com.yundao.bp.fin.dto.FeeItemVO;
import com.yundao.bp.fin.entity.FinBillingRule;
import com.yundao.bp.fin.service.BillingCalculator;
import com.yundao.bp.fin.service.FeeItemService;
import com.yundao.bp.fin.service.FeeTypeService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 收费项目与计费规则接口（BC-08）。
 *
 * <p>⭐ <b>多业态适配点</b>：通过 {@code calcMode}（按面积/按套/按床位/按夜/按抄表）
 * + {@code ruleType}（标准价/阶梯/折扣/减免）的组合，覆盖保障房、宿舍、公寓、
 * 酒店民宿、园区物业等不同业态的计费差异，无需改代码。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class FeeItemController {

    private final FeeItemService service;
    private final FeeTypeService feeTypeService;

    public FeeItemController(FeeItemService service, FeeTypeService feeTypeService) {
        this.service = service;
        this.feeTypeService = feeTypeService;
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:create")
    @PostMapping("/fee-items")
    public R<FeeItemVO> createFeeItem(@Valid @RequestBody FeeItemCreateCmd cmd) {
        return R.ok(service.createFeeItem(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:view")
    @GetMapping("/fee-items/{id}")
    public R<FeeItemVO> getFeeItem(@PathVariable Long id) {
        return R.ok(service.getFeeItem(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:view")
    @GetMapping("/fee-items")
    public R<PageResult<FeeItemVO>> pageFeeItems(@RequestParam(defaultValue = "1") long pageNum,
                                                 @RequestParam(defaultValue = "20") long pageSize,
                                                 @RequestParam(required = false) String itemType,
                                                 @RequestParam(required = false) String calcMode,
                                                 @RequestParam(required = false) String keyword) {
        return R.ok(service.pageFeeItems(pageNum, pageSize, itemType, calcMode, keyword));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:status")
    @PostMapping("/fee-items/{id}/status")
    public R<FeeItemVO> setStatus(@PathVariable Long id,
                                  @RequestBody(required = false) StatusCmd cmd) {
        return R.ok(service.setFeeItemStatus(id, cmd != null && cmd.enabled()));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:billing-rules:create")
    @PostMapping("/billing-rules")
    public R<FinBillingRule> createRule(@Valid @RequestBody BillingRuleCreateCmd cmd) {
        return R.ok(service.createRule(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:billing-rules:view")
    @GetMapping("/billing-rules/{id}")
    public R<FinBillingRule> getRule(@PathVariable Long id) {
        return R.ok(service.getRule(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:billing-rules:view")
    @GetMapping("/billing-rules")
    public R<List<FinBillingRule>> listRules(@RequestParam(required = false) Long feeItemId,
                                             @RequestParam(required = false) String houseType) {
        return R.ok(service.listRules(feeItemId, houseType));
    }

    /** 编辑计费规则（已审批通过的不可改）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:billing-rules:create")
    @org.springframework.web.bind.annotation.PutMapping("/billing-rules/{id}")
    public R<FinBillingRule> updateRule(@PathVariable Long id,
                                        @Valid @RequestBody BillingRuleCreateCmd cmd) {
        return R.ok(service.updateRule(id, cmd));
    }

    /** 删除计费规则（已审批通过的不可删）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:billing-rules:create")
    @org.springframework.web.bind.annotation.DeleteMapping("/billing-rules/{id}")
    public R<Void> deleteRule(@PathVariable Long id) {
        service.deleteRule(id);
        return R.ok(null);
    }

    /** 政府限价审批。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:billing-rules:approve")
    @PostMapping("/billing-rules/{id}/approve")
    public R<FinBillingRule> approveRule(@PathVariable Long id,
                                         @RequestBody(required = false) ApproveCmd cmd) {
        return R.ok(service.approveRule(id, cmd == null ? null : cmd.approveById()));
    }

    /** 试算（不落库）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:calc-preview:calc")
    @PostMapping("/calc-preview")
    public R<BillingCalculator.Result> preview(@Valid @RequestBody CalcPreviewCmd cmd) {
        return R.ok(service.preview(cmd));
    }


    // ==================== 费用类型字典 ====================

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:view")
    @GetMapping("/fee-types")
    public R<java.util.List<com.yundao.bp.fin.entity.FinFeeType>> feeTypes(
            @RequestParam(defaultValue = "false") boolean enabledOnly) {
        return R.ok(feeTypeService.list(enabledOnly));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:create")
    @PostMapping("/fee-types")
    public R<com.yundao.bp.fin.entity.FinFeeType> createFeeType(
            @RequestBody FeeTypeCmd cmd) {
        return R.ok(feeTypeService.create(cmd.typeCode(), cmd.typeName(), cmd.sortNo()));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:create")
    @org.springframework.web.bind.annotation.PutMapping("/fee-types/{id}")
    public R<com.yundao.bp.fin.entity.FinFeeType> updateFeeType(
            @PathVariable Long id, @RequestBody FeeTypeCmd cmd) {
        return R.ok(feeTypeService.update(id, cmd.typeCode(), cmd.typeName(), cmd.sortNo()));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:status")
    @PostMapping("/fee-types/{id}/status")
    public R<com.yundao.bp.fin.entity.FinFeeType> setFeeTypeStatus(
            @PathVariable Long id, @RequestBody(required = false) StatusCmd cmd) {
        return R.ok(feeTypeService.setStatus(id, cmd != null && cmd.enabled()));
    }

    public record FeeTypeCmd(String typeCode, String typeName, Integer sortNo) {
    }

    public record StatusCmd(boolean enabled) {
    }

    public record ApproveCmd(Long approveById) {
    }
}
