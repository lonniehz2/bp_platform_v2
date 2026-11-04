package com.yundao.bp.grant.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantVO;
import com.yundao.bp.grant.dto.KeyringVO;
import com.yundao.bp.grant.service.KeyringService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 房源权限一键操作面板：查询、冻结、恢复、临时权限、应急密码。 */
@Service
public class HouseAccessService {

    private final JdbcTemplate jdbc;
    private final GrantService grantService;
    private final KeyringService keyringService;

    public HouseAccessService(JdbcTemplate jdbc, GrantService grantService,
                              KeyringService keyringService) {
        this.jdbc = jdbc;
        this.grantService = grantService;
        this.keyringService = keyringService;
    }

    public Map<String, Object> panel(Long houseId) {
        Map<String, Object> out = new LinkedHashMap<>();
        List<Map<String, Object>> houses = jdbc.queryForList(
                "select h.id, h.house_code houseCode, h.house_name houseName, h.space_id spaceId, "
                        + "h.house_status houseStatus, h.org_id orgId from bp_asset_house h "
                        + "where h.id = ? and h.is_deleted = 0", houseId);
        if (houses.isEmpty()) {
            throw BizException.notFound("house");
        }
        Map<String, Object> house = houses.get(0);
        out.put("house", house);
        List<Map<String, Object>> contracts = jdbc.queryForList(
                "select c.id, c.contract_no contractNo, c.lessee_person_id personId, "
                        + "c.lessee_name lesseeName, c.contract_status contractStatus, "
                        + "c.lease_start leaseStart, c.lease_end leaseEnd "
                        + "from bp_biz_contract c where c.house_id = ? and c.is_deleted = 0 "
                        + "and c.contract_status in ('EFFECTIVE','CHANGING') order by c.id desc limit 1",
                houseId);
        Map<String, Object> contract = contracts.isEmpty() ? null : contracts.get(0);
        out.put("contract", contract);
        Long personId = contract == null || contract.get("personId") == null
                ? null : ((Number) contract.get("personId")).longValue();
        Long spaceId = house.get("spaceId") == null ? null
                : ((Number) house.get("spaceId")).longValue();
        out.put("entitlements", jdbc.queryForList(
                "select id, grant_no grantNo, grant_level grantLevel, person_id personId, "
                        + "valid_start validStart, valid_end validEnd, grant_status grantStatus, "
                        + "freeze_reason freezeReason from bp_grant_entitlement "
                        + "where is_deleted = 0 and (house_id = ? or space_id = ?) "
                        + "order by id desc limit 50", houseId, spaceId));
        out.put("keyrings", personId == null ? List.of() : jdbc.queryForList(
                "select id, key_type keyType, key_alias keyAlias, channel_value channelValue, "
                        + "key_status keyStatus, expire_time expireTime from bp_grant_keyring "
                        + "where person_id = ? and is_deleted = 0 order by id desc limit 50", personId));
        out.put("deviceCount", jdbc.queryForObject(
                "select count(*) from bp_dev_device where space_id = ? and is_deleted = 0",
                Long.class, spaceId));
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> freeze(Long houseId, String reason) {
        Map<String, Object> p = panel(houseId);
        List<Map<String, Object>> ents = (List<Map<String, Object>>) p.get("entitlements");
        int n = 0;
        for (Map<String, Object> e : ents) {
            String st = String.valueOf(e.get("grantStatus"));
            if ("EFFECTIVE".equals(st) || "PENDING".equals(st) || "FROZEN".equals(st)) {
                grantService.revoke(((Number) e.get("id")).longValue(),
                        reason == null || reason.isBlank() ? "manual freeze" : reason);
                n++;
            }
        }
        return Map.of("revoked", n);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> restore(Long houseId) {
        Map<String, Object> p = panel(houseId);
        Map<String, Object> c = (Map<String, Object>) p.get("contract");
        if (c == null) {
            throw BizException.stateConflict("No effective contract for this house");
        }
        Long personId = ((Number) c.get("personId")).longValue();
        Long spaceId = ((Number) ((Map<String, Object>) p.get("house")).get("spaceId")).longValue();
        LocalDate end = c.get("leaseEnd") == null ? LocalDate.now().plusYears(1)
                : ((java.sql.Date) c.get("leaseEnd")).toLocalDate();
        GrantVO g = grantService.apply(new GrantApplyCmd(personId, spaceId, "USAGE",
                LocalDateTime.now(), end.atTime(23, 59, 59), null, "CONTRACT",
                ((Number) c.get("id")).longValue(), "restore by house access panel"));
        return Map.of("grantId", g.id(), "grantNo", g.grantNo());
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> temporary(Long houseId, Long personId, String level,
                                         LocalDateTime start, LocalDateTime end) {
        Map<String, Object> p = panel(houseId);
        Long spaceId = ((Number) ((Map<String, Object>) p.get("house")).get("spaceId")).longValue();
        if (end == null || end.isBefore(LocalDateTime.now())) {
            throw BizException.paramInvalid("Temporary permission end time must be in the future");
        }
        String lv = level == null || level.isBlank() ? "VISIT" : level;
        if (!List.of("OWNERSHIP", "MANAGEMENT", "USAGE", "VISIT").contains(lv)) {
            throw BizException.paramInvalid("Invalid grant level");
        }
        GrantVO g = grantService.apply(new GrantApplyCmd(personId, spaceId, lv,
                start == null ? LocalDateTime.now() : start, end, null, "MANUAL",
                null, "temporary permission by house access panel"));
        return Map.of("grantId", g.id(), "grantNo", g.grantNo(), "validEnd", end);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> emergencyPassword(Long houseId, Long personId, int hours) {
        if (personId == null) {
            Map<String, Object> p = panel(houseId);
            Map<String, Object> c = (Map<String, Object>) p.get("contract");
            if (c == null || c.get("personId") == null) {
                throw BizException.stateConflict("No lessee for this house");
            }
            personId = ((Number) c.get("personId")).longValue();
        }
        int h = hours <= 0 ? 24 : Math.min(hours, 168);
        LocalDateTime expire = LocalDateTime.now().plusHours(h);
        KeyringVO k = keyringService.add(new KeyringService.KeyringCmd(personId,
                "OFFLINE_CODE", "emergency-" + houseId, null, "ADMIN", null,
                "ALL_GRANTED", expire.toString()));
        Map<String, Object> out = new LinkedHashMap<>();
        com.yundao.bp.grant.entity.GrantKeyring entity = keyringService.get(k.id());
        out.put("keyringId", k.id());
        out.put("code", entity == null ? null : entity.getChannelValue());
        out.put("expireTime", expire);
        return out;
    }
}
