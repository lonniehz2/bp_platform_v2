package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.ExchangeCreateCmd;
import com.yundao.bp.biz.dto.ExchangeVO;
import com.yundao.bp.biz.service.ExchangeService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 换房接口（BC-05）。
 *
 * <p>成都限换 1 次；重庆应换不换按 1.5 倍计租。
 */
@RestController
@RequestMapping("/api/v1/exchanges")
public class ExchangeController {

    private final ExchangeService service;

    public ExchangeController(ExchangeService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:create")
    @PostMapping
    public R<ExchangeVO> apply(@Valid @RequestBody ExchangeCreateCmd cmd) {
        return R.ok(service.apply(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:view")
    @GetMapping("/{id}")
    public R<ExchangeVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:view")
    @GetMapping
    public R<PageResult<ExchangeVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                          @RequestParam(defaultValue = "20") long pageSize,
                                          @RequestParam(required = false) Long personId,
                                          @RequestParam(required = false) Long oldContractId,
                                          @RequestParam(required = false) String status,
                                          @RequestParam(required = false) String keyword,
                                          @RequestParam(required = false) Long orgId) {
        return R.ok(service.page(pageNum, pageSize, personId, oldContractId, status,
                keyword, orgId));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:submit")
    @PostMapping("/{id}/submit")
    public R<ExchangeVO> submit(@PathVariable Long id) {
        return R.ok(service.submit(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:approve")
    @PostMapping("/{id}/approve")
    public R<ExchangeVO> approve(@PathVariable Long id,
                                 @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.approve(id, cmd == null ? null : cmd.reason()));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:create")
    @PostMapping("/{id}/reject")
    public R<ExchangeVO> reject(@PathVariable Long id,
                                @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.reject(id, cmd == null ? null : cmd.reason()));
    }

    /** 执行换房（权限迁移）。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:create")
    @PostMapping("/{id}/complete")
    public R<ExchangeVO> complete(@PathVariable Long id) {
        return R.ok(service.complete(id));
    }

    /** 标记应换不换（重庆 1.5 倍计租）。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:change")
    @PostMapping("/{id}/no-exchange")
    public R<ExchangeVO> noExchange(@PathVariable Long id,
                                    @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.markNoExchange(id, cmd == null ? null : cmd.reason()));
    }

    /** 某合同已完成换房次数。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:exchange:view")
    @GetMapping("/count")
    public R<Integer> count(@RequestParam Long oldContractId) {
        return R.ok(service.countCompleted(oldContractId));
    }

    public record ReasonCmd(String reason) {
    }
}
