package com.yundao.bp.grant.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.grant.service.HouseAccessService;
import java.time.LocalDateTime;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 房源权限一键操作面板。 */
@RestController
@RequestMapping("/api/v1/house-access")
public class HouseAccessController {

    private final HouseAccessService service;

    public HouseAccessController(HouseAccessService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:grant:view")
    @GetMapping("/{houseId}")
    public R<Map<String, Object>> panel(@PathVariable Long houseId) {
        return R.ok(service.panel(houseId));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:grant:revoke")
    @PostMapping("/{houseId}/freeze")
    public R<Map<String, Object>> freeze(@PathVariable Long houseId,
            @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.freeze(houseId, cmd == null ? null : cmd.reason()));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:grant:create")
    @PostMapping("/{houseId}/restore")
    public R<Map<String, Object>> restore(@PathVariable Long houseId) {
        return R.ok(service.restore(houseId));
    }

    public record TempCmd(Long personId, String grantLevel, LocalDateTime validStart,
                          LocalDateTime validEnd) {
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:grant:create")
    @PostMapping("/{houseId}/temporary")
    public R<Map<String, Object>> temporary(@PathVariable Long houseId,
            @RequestBody TempCmd cmd) {
        return R.ok(service.temporary(houseId, cmd.personId(), cmd.grantLevel(),
                cmd.validStart(), cmd.validEnd()));
    }

    public record PasswordCmd(Long personId, Integer hours) {
    }

    @com.yundao.bp.iam.security.RequirePerm("grant:keyring:manage")
    @PostMapping("/{houseId}/emergency-password")
    public R<Map<String, Object>> emergencyPassword(@PathVariable Long houseId,
            @RequestBody(required = false) PasswordCmd cmd) {
        return R.ok(service.emergencyPassword(houseId,
                cmd == null ? null : cmd.personId(), cmd == null ? 24 : cmd.hours()));
    }

    public record ReasonCmd(String reason) {
    }
}
