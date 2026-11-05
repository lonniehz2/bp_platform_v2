package com.yundao.bp.grant.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantVO;
import com.yundao.bp.grant.dto.KeyringVO;
import com.yundao.bp.grant.iot.IotAuthorizationClient;
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
    private final SnowflakeIdGenerator idGen;
    private final IotAuthorizationClient authClient;

    public HouseAccessService(JdbcTemplate jdbc, GrantService grantService,
                              KeyringService keyringService, SnowflakeIdGenerator idGen,
                              IotAuthorizationClient authClient) {
        this.jdbc = jdbc;
        this.grantService = grantService;
        this.keyringService = keyringService;
        this.idGen = idGen;
        this.authClient = authClient;
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
        out.put("frozen", !jdbc.queryForList(
                "select id from bp_grant_freeze where house_id=? and freeze_status in ('FREEZING','FROZEN') limit 1",
                houseId).isEmpty());
        out.put("freezes", jdbc.queryForList(
                "select id, person_id personId, grant_id grantId, keyring_id keyringId, "
                        + "freeze_scope freezeScope, reason, freeze_status freezeStatus, "
                        + "iot_order_no iotOrderNo, operator_id operatorId, "
                        + "operator_name operatorName, freeze_time freezeTime, restore_time restoreTime "
                        + "from bp_grant_freeze where house_id=? order by id desc limit 50", houseId));
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
    public Map<String, Object> freeze(Long houseId, String reason, Long personId) {
        requireReason(reason);
        Map<String, Object> p = panel(houseId);
        List<Map<String, Object>> ents = (List<Map<String, Object>>) p.get("entitlements");
        int n = 0;
        for (Map<String, Object> e : ents) {
            String st = String.valueOf(e.get("grantStatus"));
            if (!("EFFECTIVE".equals(st) || "PENDING".equals(st))) {
                continue;
            }
            Long pid = e.get("personId") == null ? null : ((Number) e.get("personId")).longValue();
            if (personId != null && !personId.equals(pid)) {
                continue;
            }
            Long grantId = ((Number) e.get("id")).longValue();
            String scope = personId == null ? "HOUSE" : "PERSON";
            IotAuthorizationClient.IotAuthorizationResult ir = authClient.freeze(
                    new IotAuthorizationClient.IotAuthorizationRequest(
                            houseId, pid, grantId, List.of(), scope, reason.trim()));
            jdbc.update("insert into bp_grant_freeze"
                            + "(id, tenant_id, house_id, person_id, grant_id, freeze_scope, reason,"
                            + " freeze_status, original_status, iot_order_no, operator_id, freeze_time,"
                            + " create_time, update_time)"
                            + " values(?,?,?,?,?,?,?, ?, ?, ?, ?, now(), now(), now())",
                    idGen.nextId(), com.yundao.bp.common.tenant.TenantContext.tenantId(), houseId,
                    pid, grantId, scope, reason.trim(), ir.success() ? "FROZEN" : "FAILED",
                    st, ir.orderNo(), com.yundao.bp.common.tenant.TenantContext.userId());
            if (ir.success()) {
                jdbc.update("update bp_grant_entitlement set grant_status='FROZEN', "
                        + "freeze_reason=?, update_time=now() where id=?", reason.trim(), grantId);
                n++;
            }
        }
        return Map.of("frozen", n);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> restore(Long houseId, String reason, Long personId) {
        requireReason(reason);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, grant_id grantId, person_id personId, original_status originalStatus "
                        + "from bp_grant_freeze where house_id=? and freeze_status='FROZEN' "
                        + (personId == null ? "" : "and person_id=? ") + "order by id desc",
                personId == null ? new Object[]{houseId} : new Object[]{houseId, personId});
        int n = 0;
        for (Map<String, Object> r : rows) {
            Long grantId = r.get("grantId") == null ? null : ((Number) r.get("grantId")).longValue();
            if (grantId != null) {
                String original = r.get("originalStatus") == null ? "EFFECTIVE"
                        : String.valueOf(r.get("originalStatus"));
                jdbc.update("update bp_grant_entitlement set grant_status=?, freeze_reason=null, "
                        + "update_time=now() where id=?", original, grantId);
            }
            authClient.unfreeze(new IotAuthorizationClient.IotAuthorizationRequest(
                    houseId, r.get("personId") == null ? null : ((Number) r.get("personId")).longValue(),
                    grantId, List.of(), "HOUSE", reason.trim()));
            jdbc.update("update bp_grant_freeze set freeze_status='NORMAL', restore_time=now(), "
                    + "update_time=now() where id=?", r.get("id"));
            n++;
        }
        return Map.of("restored", n);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> personAuthorize(Long houseId, Long personId,
                                               LocalDateTime start, LocalDateTime end,
                                               String reason) {
        Map<String, Object> p = panel(houseId);
        Map<String, Object> house = (Map<String, Object>) p.get("house");
        Long spaceId = ((Number) house.get("spaceId")).longValue();
        List<Map<String, Object>> keys = jdbc.queryForList(
                "select id from bp_grant_keyring where person_id=? and is_deleted=0 "
                        + "and key_status='ACTIVE' and (expire_time is null or expire_time > now())",
                personId);
        if (keys.isEmpty()) {
            throw BizException.paramInvalid("该人员没有可用钥匙，无法人员授权");
        }
        List<Long> keyringIds = new ArrayList<>();
        for (Map<String, Object> k : keys) {
            keyringIds.add(((Number) k.get("id")).longValue());
        }
        LocalDateTime realEnd = end == null ? LocalDateTime.now().plusYears(1) : end;
        GrantVO g = grantService.apply(new GrantApplyCmd(personId, spaceId, "USAGE",
                start == null ? LocalDateTime.now() : start, realEnd, keyringIds,
                "MANUAL", null, reason == null ? "person authorize" : reason));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("grantId", g.id());
        out.put("grantNo", g.grantNo());
        out.put("keyringCount", keyringIds.size());
        return out;
    }

    private static void requireReason(String reason) {
        if (reason == null || reason.isBlank()) {
            throw BizException.paramInvalid("操作原因不能为空");
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> freezeKey(Long houseId, Long keyringId, String reason) {
        requireReason(reason);
        List<Map<String, Object>> keys = jdbc.queryForList(
                "select id, person_id personId from bp_grant_keyring where id=? and is_deleted=0", keyringId);
        if (keys.isEmpty()) {
            throw BizException.notFound("keyring");
        }
        Long personId = keys.get(0).get("personId") == null ? null
                : ((Number) keys.get(0).get("personId")).longValue();
        IotAuthorizationClient.IotAuthorizationResult ir = authClient.freeze(
                new IotAuthorizationClient.IotAuthorizationRequest(houseId, personId, null,
                        List.of(keyringId), "KEY", reason.trim()));
        jdbc.update("insert into bp_grant_freeze"
                        + "(id, tenant_id, house_id, person_id, keyring_id, freeze_scope, reason,"
                        + " freeze_status, iot_order_no, operator_id, freeze_time, create_time, update_time)"
                        + " values(?,?,?,?,?, 'KEY', ?, ?, ?, ?, now(), now(), now())",
                idGen.nextId(), com.yundao.bp.common.tenant.TenantContext.tenantId(), houseId,
                personId, keyringId, reason.trim(), ir.success() ? "FROZEN" : "FAILED",
                ir.orderNo(), com.yundao.bp.common.tenant.TenantContext.userId());
        if (ir.success()) {
            jdbc.update("update bp_grant_keyring set key_status='FROZEN', update_time=now() where id=?",
                    keyringId);
        }
        return Map.of("frozen", ir.success() ? 1 : 0, "orderNo", ir.orderNo());
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> restoreKey(Long houseId, Long keyringId, String reason) {
        requireReason(reason);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, person_id personId from bp_grant_freeze where house_id=? and keyring_id=? "
                        + "and freeze_status='FROZEN' order by id desc", houseId, keyringId);
        int n = 0;
        for (Map<String, Object> r : rows) {
            Long personId = r.get("personId") == null ? null : ((Number) r.get("personId")).longValue();
            authClient.unfreeze(new IotAuthorizationClient.IotAuthorizationRequest(
                    houseId, personId, null, List.of(keyringId), "KEY", reason.trim()));
            jdbc.update("update bp_grant_freeze set freeze_status='NORMAL', restore_time=now(), "
                    + "update_time=now() where id=?", r.get("id"));
            jdbc.update("update bp_grant_keyring set key_status='ACTIVE', update_time=now() where id=?",
                    keyringId);
            n++;
        }
        return Map.of("restored", n);
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
