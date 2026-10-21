package com.yundao.bp.asset.controller;

import com.yundao.bp.asset.dto.HouseCreateCmd;
import com.yundao.bp.asset.dto.HouseVO;
import com.yundao.bp.asset.service.HouseService;
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
 * 房源接口（BC-02 空间资产）。
 *
 * <p>创建约束：只能挂到 ROOM / BED 节点；{@code orgId} 由服务端从空间节点派生。
 */
@RestController
@RequestMapping("/api/v1/houses")
public class HouseController {

    private final HouseService houseService;

    public HouseController(HouseService houseService) {
        this.houseService = houseService;
    }

    @PostMapping
    public R<HouseVO> create(@Valid @RequestBody HouseCreateCmd cmd) {
        return R.ok(houseService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<HouseVO> get(@PathVariable Long id) {
        return R.ok(houseService.get(id));
    }

    @GetMapping
    public R<PageResult<HouseVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                       @RequestParam(defaultValue = "20") long pageSize,
                                       @RequestParam(required = false) Long orgId,
                                       @RequestParam(required = false) Long spaceId,
                                       @RequestParam(required = false) String houseStatus,
                                       @RequestParam(required = false) String keyword) {
        return R.ok(houseService.page(pageNum, pageSize, orgId, spaceId, houseStatus, keyword));
    }

    @PostMapping("/{id}/status")
    public R<HouseVO> changeStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(houseService.changeStatus(id, cmd.status()));
    }

    public record StatusCmd(String status) {
    }
}
