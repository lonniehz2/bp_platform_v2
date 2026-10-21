package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.AppealCreateCmd;
import com.yundao.bp.biz.dto.AppealDecisionCmd;
import com.yundao.bp.biz.dto.AppealVO;
import com.yundao.bp.biz.service.AppealService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
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
 * 申诉/异议（复议）接口（BC-05）。
 *
 * <p>⭐ 保障房法定救济通道：对审核、年审核查、公示、退出决定不服可申诉。
 */
@RestController
@RequestMapping("/api/v1/appeals")
public class AppealController {

    private final AppealService service;

    public AppealController(AppealService service) {
        this.service = service;
    }

    @PostMapping
    public R<AppealVO> submit(@Valid @RequestBody AppealCreateCmd cmd) {
        return R.ok(service.submit(cmd));
    }

    @GetMapping("/{id}")
    public R<AppealVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<AppealVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                        @RequestParam(defaultValue = "20") long pageSize,
                                        @RequestParam(required = false) Long personId,
                                        @RequestParam(required = false) String bizType,
                                        @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, personId, bizType, status));
    }

    /** 某业务对象的申诉记录。 */
    @GetMapping("/by-biz")
    public R<List<AppealVO>> byBiz(@RequestParam String bizType, @RequestParam Long bizId) {
        return R.ok(service.listByBiz(bizType, bizId));
    }

    @PostMapping("/{id}/accept")
    public R<AppealVO> accept(@PathVariable Long id,
                              @RequestBody(required = false) UserCmd cmd) {
        return R.ok(service.accept(id, cmd == null ? null : cmd.userId()));
    }

    @PostMapping("/{id}/investigate")
    public R<AppealVO> investigate(@PathVariable Long id,
                                   @RequestBody(required = false) UserCmd cmd) {
        return R.ok(service.investigate(id, cmd == null ? null : cmd.userId()));
    }

    /** 作出决定。 */
    @PostMapping("/{id}/decide")
    public R<AppealVO> decide(@PathVariable Long id,
                              @Valid @RequestBody AppealDecisionCmd cmd) {
        return R.ok(service.decide(id, cmd));
    }

    @PostMapping("/{id}/withdraw")
    public R<AppealVO> withdraw(@PathVariable Long id,
                                @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.withdraw(id, cmd == null ? null : cmd.reason()));
    }

    /** 告知结果。 */
    @PostMapping("/{id}/notify")
    public R<AppealVO> notifyResult(@PathVariable Long id) {
        return R.ok(service.markNotified(id));
    }

    /** 超期标记扫描。 */
    @PostMapping("/mark-timeout")
    public R<Integer> markTimeout() {
        return R.ok(service.markTimeout());
    }

    public record UserCmd(Long userId) {
    }

    public record ReasonCmd(String reason) {
    }
}
