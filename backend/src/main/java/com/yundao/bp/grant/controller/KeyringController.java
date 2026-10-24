package com.yundao.bp.grant.controller;

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
    @com.yundao.bp.iam.security.RequirePerm("asset:keyring:view")
    @GetMapping("/person/{personId}")
    public R<List<KeyringVO>> listByPerson(@PathVariable Long personId) {
        return R.ok(service.listByPerson(personId));
    }

    /** ⭐ 钥匙包概览（四分类统计 + 是否满足强安全要求）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:keyring:view")
    @GetMapping("/person/{personId}/summary")
    public R<Map<String, Object>> summary(@PathVariable Long personId) {
        return R.ok(service.summary(personId));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:keyring:view")
    @GetMapping
    public R<PageResult<KeyringVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                         @RequestParam(defaultValue = "20") long pageSize,
                                         @RequestParam(required = false) Long personId,
                                         @RequestParam(required = false) String keyType,
                                         @RequestParam(required = false) String keyClass,
                                         @RequestParam(required = false) String keyStatus) {
        return R.ok(service.page(pageNum, pageSize, personId, keyType, keyClass, keyStatus));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:keyring:view")
    @GetMapping("/{id}")
    public R<KeyringVO> get(@PathVariable Long id) {
        return R.ok(KeyringVO.from(service.get(id)));
    }

    /** 冻结钥匙（临时停用）。 */
    @PostMapping("/{id}/freeze")
    @RequirePerm("grant:keyring:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "冻结钥匙")
    public R<KeyringVO> freeze(@PathVariable Long id) {
        return R.ok(service.freeze(id));
    }

    /** 解冻钥匙。 */
    @PostMapping("/{id}/unfreeze")
    @RequirePerm("grant:keyring:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "解冻钥匙")
    public R<KeyringVO> unfreeze(@PathVariable Long id) {
        return R.ok(service.unfreeze(id));
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
