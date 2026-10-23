package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.CohabitantCreateCmd;
import com.yundao.bp.biz.dto.CohabitantVO;
import com.yundao.bp.biz.service.CohabitantService;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 合同同住人接口（BC-05）。
 *
 * <p>同住人用于：按人补贴、年审人口核查、退租腾退、门禁授权。
 */
@RestController
@RequestMapping("/api/v1/contracts/{contractId}/cohabitants")
public class CohabitantController {

    private final CohabitantService service;

    public CohabitantController(CohabitantService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:cohabitant:create")
    @PostMapping
    public R<CohabitantVO> add(@PathVariable Long contractId,
                               @Valid @RequestBody CohabitantCreateCmd cmd) {
        return R.ok(service.add(contractId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:cohabitant:view")
    @GetMapping
    public R<List<CohabitantVO>> list(@PathVariable Long contractId) {
        return R.ok(service.list(contractId));
    }

    /** 保障人口数（承租人 1 + 同住人）。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:cohabitant:view")
    @GetMapping("/household-size")
    public R<Integer> householdSize(@PathVariable Long contractId) {
        return R.ok(service.householdSize(contractId));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:cohabitant:view")
    @GetMapping("/{id}")
    public R<CohabitantVO> get(@PathVariable Long contractId, @PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:cohabitant:delete")
    @DeleteMapping("/{id}")
    public R<Void> remove(@PathVariable Long contractId, @PathVariable Long id) {
        service.remove(id);
        return R.ok(null);
    }

    /** 门禁开门授权。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:cohabitant:grant")
    @PostMapping("/{id}/grant")
    public R<CohabitantVO> grant(@PathVariable Long contractId, @PathVariable Long id,
                                 @RequestBody GrantCmd cmd) {
        return R.ok(service.setGranted(id, cmd.granted()));
    }

    public record GrantCmd(boolean granted) {
    }
}
