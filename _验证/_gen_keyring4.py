# -*- coding: utf-8 -*-
"""生成钥匙包 + 授权对账 控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

KEYRING_CTRL = '''package com.yundao.bp.grant.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.grant.dto.KeyringVO;
import com.yundao.bp.grant.service.KeyringService;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.sys.audit.Audit;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 钥匙包接口（★ 级「四级权限」）。
 *
 * <p>以人为中心管理多介质钥匙，按四分类区分安全等级。
 */
@RestController
@RequestMapping("/api/v1/keyring")
public class KeyringController {

    private final KeyringService service;

    public KeyringController(KeyringService service) {
        this.service = service;
    }

    /** ⭐ 新增钥匙（自动推导四分类）。 */
    @PostMapping
    @RequirePerm("grant:keyring:manage")
    @Audit(type = "SECURITY", level = "CRITICAL", action = "新增钥匙介质")
    public R<KeyringVO> add(@RequestBody KeyringService.KeyringCmd cmd) {
        return R.ok(service.add(cmd));
    }

    /** ⭐ 某人钥匙包。 */
    @GetMapping("/person/{personId}")
    public R<List<KeyringVO>> listByPerson(@PathVariable Long personId) {
        return R.ok(service.listByPerson(personId));
    }

    /** ⭐ 钥匙包概览（四分类统计 + 是否满足强安全要求）。 */
    @GetMapping("/person/{personId}/summary")
    public R<Map<String, Object>> summary(@PathVariable Long personId) {
        return R.ok(service.summary(personId));
    }

    @GetMapping
    public R<PageResult<KeyringVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                         @RequestParam(defaultValue = "20") long pageSize,
                                         @RequestParam(required = false) Long personId,
                                         @RequestParam(required = false) String keyType,
                                         @RequestParam(required = false) String keyClass,
                                         @RequestParam(required = false) String keyStatus) {
        return R.ok(service.page(pageNum, pageSize, personId, keyType, keyClass, keyStatus));
    }

    @GetMapping("/{id}")
    public R<KeyringVO> get(@PathVariable Long id) {
        return R.ok(KeyringVO.from(service.get(id)));
    }

    /** 冻结/解冻/置为过期。 */
    @PostMapping("/{id}/status")
    @RequirePerm("grant:keyring:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "变更钥匙状态")
    public R<KeyringVO> setStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(service.setStatus(id, cmd.status()));
    }

    /** 删除钥匙（逻辑删除，置 DELETED）。 */
    @PostMapping("/{id}/remove")
    @RequirePerm("grant:keyring:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "删除钥匙介质")
    public R<KeyringVO> remove(@PathVariable Long id) {
        return R.ok(service.remove(id));
    }

    public record StatusCmd(String status) {
    }
}
'''

RECON_CTRL = '''package com.yundao.bp.grant.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.grant.entity.GrantReconcileDiff;
import com.yundao.bp.grant.service.ReconcileService;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.sys.audit.Audit;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 授权对账接口（★ 级要求：本地与 IoT 授权一致）。
 */
@RestController
@RequestMapping("/api/v1/grant-reconcile")
public class ReconcileController {

    private final ReconcileService service;

    public ReconcileController(ReconcileService service) {
        this.service = service;
    }

    /** ⭐ 执行对账（可指定某台锁）。 */
    @PostMapping("/run")
    @RequirePerm("grant:reconcile:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "执行授权对账")
    public R<Map<String, Object>> run(@RequestParam(required = false) String lockId) {
        return R.ok(service.reconcile(lockId));
    }

    @GetMapping("/diffs")
    public R<PageResult<GrantReconcileDiff>> diffs(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String lockId,
            @RequestParam(required = false) String diffType,
            @RequestParam(required = false) String handleStatus) {
        return R.ok(service.pageDiffs(pageNum, pageSize, lockId, diffType, handleStatus));
    }

    @GetMapping("/diffs/pending")
    public R<List<GrantReconcileDiff>> pending() {
        return R.ok(service.listByHandleStatus("PENDING"));
    }

    /** ⭐ 处置单条差异。 */
    @PostMapping("/diffs/{id}/handle")
    @RequirePerm("grant:reconcile:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "处置对账差异")
    public R<GrantReconcileDiff> handle(@PathVariable Long id, @RequestBody HandleCmd cmd) {
        return R.ok(service.handle(id, cmd.action(), cmd.remark()));
    }

    /** ⭐ 批量处置。 */
    @PostMapping("/diffs/handle-batch")
    @RequirePerm("grant:reconcile:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "批量处置对账差异")
    public R<Map<String, Object>> handleBatch(@RequestBody BatchCmd cmd) {
        return R.ok(service.handleBatch(cmd.diffType(), cmd.action(), cmd.remark()));
    }

    /** 未处置差异统计（看板）。 */
    @GetMapping("/stats")
    public R<Map<String, Object>> stats() {
        return R.ok(service.stats());
    }

    public record HandleCmd(String action, String remark) {
    }

    public record BatchCmd(String diffType, String action, String remark) {
    }
}
'''

for rel, src in (('grant/controller/KeyringController.java', KEYRING_CTRL),
                 ('grant/controller/ReconcileController.java', RECON_CTRL)):
    p = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  + ' + rel)
