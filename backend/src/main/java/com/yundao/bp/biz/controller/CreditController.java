package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.CreditCreateCmd;
import com.yundao.bp.biz.dto.CreditVO;
import com.yundao.bp.biz.service.CreditService;
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
 * 信用惩戒接口（BC-05）。
 *
 * <p>⭐ 失信记录会真正限制再申请（{@code checkApplyBan}）。
 */
@RestController
@RequestMapping("/api/v1/credits")
public class CreditController {

    private final CreditService service;

    public CreditController(CreditService service) {
        this.service = service;
    }

    @PostMapping
    public R<CreditVO> record(@Valid @RequestBody CreditCreateCmd cmd) {
        return R.ok(service.record(cmd));
    }

    @GetMapping("/{id}")
    public R<CreditVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<CreditVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                        @RequestParam(defaultValue = "20") long pageSize,
                                        @RequestParam(required = false) Long personId,
                                        @RequestParam(required = false) String violationType,
                                        @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, personId, violationType, status));
    }

    @GetMapping("/by-person/{personId}")
    public R<List<CreditVO>> byPerson(@PathVariable Long personId) {
        return R.ok(service.listByPerson(personId));
    }

    /**
     * 申请前校验：是否处于限制申请期。
     *
     * <p>处于限制期返回 false 并给出解禁日期。
     */
    @GetMapping("/check-ban")
    public R<String> checkBan(@RequestParam Long personId) {
        if (service.isUnderBan(personId)) {
            service.checkApplyBan(personId);
        }
        return R.ok("未处于限制申请期，可正常申请");
    }

    /** 解除（期满）。 */
    @PostMapping("/{id}/expire")
    public R<CreditVO> expire(@PathVariable Long id) {
        return R.ok(service.expire(id));
    }

    /** 撤销（复议/纠错）。 */
    @PostMapping("/{id}/revoke")
    public R<CreditVO> revoke(@PathVariable Long id,
                              @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.revoke(id, cmd == null ? null : cmd.reason()));
    }

    /** 标记推送信用平台结果。 */
    @PostMapping("/{id}/push")
    public R<CreditVO> push(@PathVariable Long id,
                            @RequestBody(required = false) PushCmd cmd) {
        return R.ok(service.markPushed(id,
                cmd == null || cmd.success(),
                cmd == null ? null : cmd.platform()));
    }

    /** 期满扫描。 */
    @PostMapping("/scan-expired")
    public R<Integer> scanExpired() {
        return R.ok(service.scanExpired());
    }

    public record ReasonCmd(String reason) {
    }

    public record PushCmd(Boolean success, String platform) {
    }
}
