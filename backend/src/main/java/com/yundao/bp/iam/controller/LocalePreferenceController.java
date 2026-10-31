package com.yundao.bp.iam.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.security.LoginUser;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 当前登录用户的界面语言偏好。 */
@RestController
@RequestMapping("/api/v1/auth")
public class LocalePreferenceController {

    private final JdbcTemplate jdbc;

    public LocalePreferenceController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @PutMapping("/locale")
    public R<Void> save(@RequestBody LocaleCmd cmd) {
        LoginUser user = LoginUser.get();
        if (user == null) {
            throw BizException.of(com.yundao.bp.common.api.ErrorCode.UNAUTHORIZED);
        }
        String tag = cmd.locale() == null ? "" : cmd.locale().trim();
        if (!"zh-CN".equals(tag) && !"en-US".equals(tag)) {
            throw BizException.paramInvalid("Unsupported locale: " + tag);
        }
        jdbc.update("update bp_iam_user set locale=?, update_time=now(3)"
                        + " where id=? and tenant_id=?",
                tag, user.userId(), TenantContext.tenantId());
        return R.ok(null);
    }

    public record LocaleCmd(String locale) {
    }
}
