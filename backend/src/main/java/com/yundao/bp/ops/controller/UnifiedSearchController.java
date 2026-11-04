package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.person.util.SensitiveDataCodec;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 统一查询：人员、合同、房源、账单。 */
@RestController
@RequestMapping("/api/v1/search")
public class UnifiedSearchController {

    private final JdbcTemplate jdbc;

    public UnifiedSearchController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:house:view")
    @GetMapping("/unified")
    public R<Map<String, Object>> search(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String idCard,
            @RequestParam(required = false) String personName,
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) Long buildingId,
            @RequestParam(required = false) String houseCode,
            @RequestParam(required = false) String houseStatus) {
        String kw = keyword == null ? null : keyword.trim();
        if (kw != null && kw.isEmpty()) {
            kw = null;
        }
        String pn = personName == null ? null : personName.trim();
        if (pn != null && pn.isEmpty()) {
            pn = null;
        }
        String hc = houseCode == null ? null : houseCode.trim();
        if (hc != null && hc.isEmpty()) {
            hc = null;
        }
        String idHash = null;
        if (idCard != null && !idCard.isBlank()
                && idCard.matches("^(\\d{17}[\\dXx]|\\d{15})$")) {
            idHash = SensitiveDataCodec.hash(idCard);
        }

        List<Object> pa = new ArrayList<>();
        String personSql = "select id, person_name as personName, phone, id_card_mask as idCardMask, "
                + "person_status as personStatus from bp_person where is_deleted = 0 ";
        if (pn != null) {
            personSql += "and person_name like ? ";
            pa.add("%" + pn + "%");
        }
        if (idHash != null) {
            personSql += "and id_card_hash = ? ";
            pa.add(idHash);
        } else if (idCard != null && !idCard.isBlank()) {
            personSql += "and (id_card_mask like ? or id_card like ?) ";
            pa.add("%" + idCard.trim() + "%");
            pa.add("%" + idCard.trim() + "%");
        }
        if (kw != null) {
            personSql += "and (person_name like ? or phone like ? or id_card_mask like ?) ";
            pa.add("%" + kw + "%");
            pa.add("%" + kw + "%");
            pa.add("%" + kw + "%");
        }
        personSql += "order by id desc limit 50";
        List<Map<String, Object>> persons = jdbc.queryForList(personSql, pa.toArray());

        List<Object> ca = new ArrayList<>();
        String contractSql = "select id, contract_no as contractNo, lessee_name as lesseeName, "
                + "org_id as orgId, house_id as houseId, contract_status as contractStatus, "
                + "lease_start as leaseStart, lease_end as leaseEnd, monthly_rent as monthlyRent "
                + "from bp_biz_contract where is_deleted = 0 ";
        if (orgId != null) {
            contractSql += "and org_id = ? ";
            ca.add(orgId);
        }
        if (kw != null) {
            contractSql += "and (contract_no like ? or lessee_name like ?) ";
            ca.add("%" + kw + "%");
            ca.add("%" + kw + "%");
        }
        if (pn != null) {
            contractSql += "and lessee_name like ? ";
            ca.add("%" + pn + "%");
        }
        contractSql += "order by id desc limit 50";
        List<Map<String, Object>> contracts = jdbc.queryForList(contractSql, ca.toArray());

        List<Object> ha = new ArrayList<>();
        String houseSql = "select h.id, h.house_code as houseCode, h.house_name as houseName, "
                + "h.house_status as houseStatus, h.org_id as orgId, h.area, "
                + "(select p.person_name from bp_biz_contract c join bp_person p "
                + " on p.id = c.lessee_person_id where c.house_id = h.id "
                + " and c.contract_status = 'EFFECTIVE' and c.is_deleted = 0 "
                + " order by c.id desc limit 1) as personName "
                + "from bp_asset_house h where h.is_deleted = 0 ";
        if (orgId != null) {
            houseSql += "and h.org_id = ? ";
            ha.add(orgId);
        }
        if (buildingId != null) {
            List<Map<String, Object>> bs = jdbc.queryForList(
                    "select space_path from bp_asset_space where id = ?", buildingId);
            String path = bs.isEmpty() || bs.get(0).get("space_path") == null
                    ? "" : String.valueOf(bs.get(0).get("space_path"));
            String prefix = path.isBlank() ? buildingId + "/" : path;
            houseSql += "and (h.space_id = ? or h.space_id in "
                    + "(select id from bp_asset_space where space_path like concat(?, '%'))) ";
            ha.add(buildingId);
            ha.add(prefix);
        }
        if (hc != null) {
            houseSql += "and (h.house_code like ? or h.house_name like ?) ";
            ha.add("%" + hc + "%");
            ha.add("%" + hc + "%");
        }
        if (houseStatus != null && !houseStatus.isBlank()) {
            houseSql += "and h.house_status = ? ";
            ha.add(houseStatus);
        }
        if (kw != null) {
            houseSql += "and (h.house_code like ? or h.house_name like ?) ";
            ha.add("%" + kw + "%");
            ha.add("%" + kw + "%");
        }
        houseSql += "order by h.id desc limit 100";
        List<Map<String, Object>> houses = jdbc.queryForList(houseSql, ha.toArray());

        List<Object> ba = new ArrayList<>();
        String billSql = "select b.id, b.bill_no as billNo, b.bill_period as billPeriod, "
                + "b.bill_amount as billAmount, b.payable_amount as payableAmount, "
                + "b.bill_status as billStatus, b.house_id as houseId, b.contract_id as contractId "
                + "from bp_fin_bill b where b.is_deleted = 0 ";
        if (orgId != null) {
            billSql += "and b.org_id = ? ";
            ba.add(orgId);
        }
        if (kw != null) {
            billSql += "and b.bill_no like ? ";
            ba.add("%" + kw + "%");
        }
        if (houseStatus != null && !houseStatus.isBlank()) {
            // 账单不按房源状态过滤
        }
        billSql += "order by b.id desc limit 50";
        List<Map<String, Object>> bills = jdbc.queryForList(billSql, ba.toArray());

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("keyword", kw);
        out.put("persons", persons);
        out.put("contracts", contracts);
        out.put("houses", houses);
        out.put("bills", bills);
        out.put("total", persons.size() + contracts.size() + houses.size() + bills.size());
        return R.ok(out);
    }
}
