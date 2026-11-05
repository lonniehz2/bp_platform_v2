package com.yundao.bp.grant.controller;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.R;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** IoT 授权冻结/恢复回调。生产环境应增加签名或白名单校验。 */
@RestController
@RequestMapping("/api/v1/iot/authorization")
public class IotAuthorizationController {

    private final JdbcTemplate jdbc;

    public IotAuthorizationController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:grant:view")
    @PostMapping("/freeze-callback")
    public R<Map<String, Object>> callback(@RequestBody Map<String, Object> body) {
        String orderNo = str(body.get("orderNo"));
        String status = str(body.get("status"));
        String message = str(body.get("message"));
        if (orderNo.isBlank()) {
            return R.fail(ErrorCode.PARAM_INVALID, "orderNo required");
        }
        boolean ok = !"FAILED".equalsIgnoreCase(status) && !"FAIL".equalsIgnoreCase(status);
        String dbStatus = ok ? "FROZEN" : "FAILED";
        int n = jdbc.update("update bp_grant_freeze set freeze_status=?, error_msg=?, "
                + "update_time=now() where iot_order_no=?", dbStatus, message, orderNo);
        return R.ok(Map.of("orderNo", orderNo, "updated", n, "status", dbStatus));
    }

    private static String str(Object v) {
        return v == null ? "" : String.valueOf(v);
    }
}
