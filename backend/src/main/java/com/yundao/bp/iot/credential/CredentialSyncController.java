package com.yundao.bp.iot.credential;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.iot.credential.entity.IotCredentialSync;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 凭据同步记录查询（联调工具用）。 */
@RestController
@RequestMapping("/api/v1/iot")
public class CredentialSyncController {

    private final CredentialSyncService service;

    public CredentialSyncController(CredentialSyncService service) {
        this.service = service;
    }

    @RequirePerm("dev:command:view")
    @GetMapping("/credential-sync")
    public R<PageResult<IotCredentialSync>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long keyringId,
            @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, keyringId, status));
    }
}
