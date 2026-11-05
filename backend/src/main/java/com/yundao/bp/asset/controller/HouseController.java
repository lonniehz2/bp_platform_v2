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
    private final com.yundao.bp.asset.service.impl.HouseImportService houseImportService;

    public HouseController(HouseService houseService,
                           com.yundao.bp.asset.service.impl.HouseImportService houseImportService) {
        this.houseService = houseService;
        this.houseImportService = houseImportService;
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:house:create")
    @PostMapping
    public R<HouseVO> create(@Valid @RequestBody HouseCreateCmd cmd) {
        return R.ok(houseService.create(cmd));
    }

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbcTemplate;

    /**
     * 房源入住信息：当前合同、承租人、同住人与已入住人数。
     *
     * <p>已出租房源详情用，避免房东只看到房态看不到人。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:house:view")
    @GetMapping("/{id}/occupancy")
    public R<java.util.Map<String, Object>> occupancy(@PathVariable Long id) {
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        if (jdbcTemplate == null) {
            return R.ok(out);
        }
        java.util.List<java.util.Map<String, Object>> cs = jdbcTemplate.queryForList(
                "select c.id, c.contract_no, c.lessee_person_id as person_id, c.lease_start, c.lease_end, "
                        + "c.contract_status, p.person_name, p.phone from bp_biz_contract c "
                        + "left join bp_person p on p.id = c.lessee_person_id "
                        + "where c.house_id = ? and c.is_deleted = 0 "
                        + "and c.contract_status in ('SIGNING','EFFECTIVE','RENEWING') "
                        + "order by c.id desc limit 1", id);
        if (cs.isEmpty()) {
            out.put("occupied", false);
            out.put("tenantCount", 0);
            out.put("cohabitants", java.util.List.of());
            return R.ok(out);
        }
        java.util.Map<String, Object> c = cs.get(0);
        Object contractId = c.get("id");
        java.util.List<java.util.Map<String, Object>> co = jdbcTemplate.queryForList(
                "select co.member_name as name, co.relation, co.id_card_mask from bp_biz_contract_cohabitant co "
                        + "where co.contract_id = ? order by co.id", contractId);
        int tenantCount = 1 + co.size();
        out.put("occupied", true);
        out.put("contractId", contractId);
        out.put("contractNo", c.get("contract_no"));
        out.put("contractStatus", c.get("contract_status"));
        out.put("leaseStart", c.get("lease_start"));
        out.put("leaseEnd", c.get("lease_end"));
        out.put("tenantName", c.get("person_name"));
        out.put("tenantPhone", c.get("phone"));
        out.put("personId", c.get("person_id"));
        out.put("tenantCount", tenantCount);
        out.put("cohabitantCount", co.size());
        out.put("cohabitants", co);
        return R.ok(out);
    }

    @GetMapping("/{id}")
    public R<HouseVO> get(@PathVariable Long id) {
        return R.ok(houseService.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:house:view")
    @GetMapping
    public R<PageResult<HouseVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                       @RequestParam(defaultValue = "20") long pageSize,
                                       @RequestParam(required = false) Long orgId,
                                       @RequestParam(required = false) Long spaceId,
                                       @RequestParam(required = false) String houseStatus,
                                       @RequestParam(required = false) String houseType,
                                       @RequestParam(required = false) String keyword,
                                       @RequestParam(required = false) Boolean includeChildren) {
        return R.ok(houseService.page(pageNum, pageSize, orgId, spaceId, houseStatus,
                houseType, keyword, includeChildren));
    }


    /**
     * 批量导入房源（CSV）。
     *
     * <p>用于真实台账迁移：逐行校验组织、空间、枚举与编号唯一性，
     * 失败行返回行号与原因，不中断整批。
     */
    /** 一张长表：自动创建空间、房源、虚拟设备并绑定。 */
    @PostMapping("/import-batch")
    @com.yundao.bp.iam.security.RequirePerm("asset:house:create")
    public R<java.util.Map<String, Object>> importBatch(
            @org.springframework.web.bind.annotation.RequestParam("file")
            org.springframework.web.multipart.MultipartFile file) {
        return R.ok(houseImportService.importCsv(file));
    }

    @PostMapping("/import")
    @com.yundao.bp.iam.security.RequirePerm("asset:house:create")
    public R<java.util.Map<String, Object>> importCsv(
            @org.springframework.web.bind.annotation.RequestParam("file")
            org.springframework.web.multipart.MultipartFile file) {
        return R.ok(houseService.importCsv(file));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:house:status")
    @PostMapping("/{id}/status")
    public R<HouseVO> changeStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(houseService.changeStatus(id, cmd.status()));
    }

    public record StatusCmd(String status) {
    }

    /** 宿舍：为房间批量生成床位房源。 */
    @PostMapping("/beds/batch-create")
    @com.yundao.bp.iam.security.RequirePerm("asset:house:create")
    public R<Integer> batchCreateBeds(@RequestBody BedBatchCmd cmd) {
        return R.ok(houseService.batchCreateBeds(cmd.roomSpaceId(), cmd.count(),
                cmd.rentStandard(), cmd.areaPerBed()));
    }

    /** 宿舍：房间下的床位视图（含在租人）。 */
    @GetMapping("/beds")
    public R<java.util.List<java.util.Map<String, Object>>> listBeds(
            @RequestParam Long roomSpaceId) {
        return R.ok(houseService.listBeds(roomSpaceId));
    }

    public record BedBatchCmd(Long roomSpaceId, int count,
                              java.math.BigDecimal rentStandard,
                              java.math.BigDecimal areaPerBed) {
    }
}
