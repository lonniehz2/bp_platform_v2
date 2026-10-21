package com.yundao.bp.common.web;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.entity.AssetSpace;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.mapper.AssetSpaceMapper;
import com.yundao.bp.common.util.EnumLabels;
import com.yundao.bp.iam.entity.IamOrg;
import com.yundao.bp.iam.mapper.IamOrgMapper;
import com.yundao.bp.person.entity.Person;
import com.yundao.bp.person.mapper.PersonMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 显示层补全器：为接口返回的行对象补上「人能看懂」的字段。
 *
 * <p>解决一类反复出现的问题：列表接口只返回 {@code personId=370832686538952704}
 * 或 {@code batchStatus=ALLOCATED}，前端无从翻译，界面就出现数字和英文编码。</p>
 *
 * <p>补全规则（**只新增字段，绝不改原字段**，因此不影响任何既有业务逻辑）：</p>
 * <ul>
 *   <li>{@code personId} → 追加 {@code personName}</li>
 *   <li>{@code houseId} → 追加 {@code houseName}</li>
 *   <li>{@code orgId} → 追加 {@code orgName}</li>
 *   <li>{@code spaceId} → 追加 {@code spaceName}</li>
 *   <li>任何 *Status / *Type / *Stage / *Mode / *Level 等 → 追加 {@code xxxLabel}</li>
 * </ul>
 *
 * <p>名称走进程内缓存（含空值缓存，避免穿透），单页最多几十个 ID，
 * 补全开销可忽略。</p>
 */
@Component
public class DisplayEnricher {

    /** 名称缓存上限，防止长期运行内存膨胀 */
    private static final int CACHE_LIMIT = 20000;

    private final PersonMapper personMapper;
    private final AssetHouseMapper houseMapper;
    private final IamOrgMapper orgMapper;
    private final AssetSpaceMapper spaceMapper;
    private final ObjectMapper objectMapper;
    /** 业务编号解析用：直接按 id 查业务单号，避免为 8 张表各注入一个 Mapper */
    private final JdbcTemplate jdbcTemplate;
    private final Map<Long, String> bizNoCache = new ConcurrentHashMap<>();

    private final Map<Long, String> personCache = new ConcurrentHashMap<>();
    private final Map<Long, String> houseCache = new ConcurrentHashMap<>();
    private final Map<Long, String> orgCache = new ConcurrentHashMap<>();
    private final Map<Long, String> spaceCache = new ConcurrentHashMap<>();

    public DisplayEnricher(PersonMapper personMapper, AssetHouseMapper houseMapper,
                           IamOrgMapper orgMapper, AssetSpaceMapper spaceMapper,
                           ObjectMapper objectMapper, JdbcTemplate jdbcTemplate) {
        this.personMapper = personMapper;
        this.houseMapper = houseMapper;
        this.orgMapper = orgMapper;
        this.spaceMapper = spaceMapper;
        this.objectMapper = objectMapper;
        this.jdbcTemplate = jdbcTemplate;
    }

    /** 字段名后缀 → 中文标签的枚举类型 */
    private static final Map<String, String> FIELD_ENUM_TYPE = new HashMap<>();

    static {
        FIELD_ENUM_TYPE.put("houseType", "HOUSE_TYPE");
        FIELD_ENUM_TYPE.put("houseStatus", "HOUSE_STATUS");
        FIELD_ENUM_TYPE.put("securityType", "SECURITY_TYPE");
        FIELD_ENUM_TYPE.put("contractStatus", "CONTRACT_STATUS");
        FIELD_ENUM_TYPE.put("billStatus", "BILL_STATUS");
    }

    /** 是否需要按枚举翻译的字段 */
    private static boolean isEnumField(String key) {
        if (key.endsWith("Label") || key.endsWith("Name")) {
            return false;
        }
        return key.endsWith("Status") || key.endsWith("Type") || key.endsWith("Stage")
                || key.endsWith("Mode") || key.endsWith("Level") || key.endsWith("Channel")
                || key.endsWith("Result") || key.endsWith("Source") || key.endsWith("Kind")
                || key.endsWith("Way") || key.endsWith("Category")
                || FIELD_ENUM_TYPE.containsKey(key);
    }

    /** 补全单行；入参为 record/POJO，返回 Map（保留全部原字段） */
    /** 树形接口：最多递归 8 层，防止异常数据导致栈溢出 */
    private static final int MAX_TREE_DEPTH = 8;

    public Map<String, Object> enrich(Object row) {
        return enrich(row, 1);
    }

    private Map<String, Object> enrich(Object row, int depth) {
        if (row == null) {
            return null;
        }
        Map<String, Object> map;
        if (row instanceof Map<?, ?> m) {
            @SuppressWarnings("unchecked")
            Map<String, Object> copy = new LinkedHashMap<>((Map<String, Object>) m);
            map = copy;
        } else {
            map = objectMapper.convertValue(row, LinkedHashMap.class);
        }
        fill(map);
        enrichChildren(map, depth);
        return map;
    }

    /**
     * 递归补全嵌套子节点。
     *
     * <p>组织树 / 空间树这类接口把层级放在 {@code children} 里，
     * 如果只补顶层，子节点仍会露出 UNIT、FLOOR 这类英文编码。</p>
     */
    private void enrichChildren(Map<String, Object> map, int depth) {
        if (depth >= MAX_TREE_DEPTH) {
            return;
        }
        for (Map.Entry<String, Object> e : map.entrySet()) {
            if (!(e.getValue() instanceof List<?> list) || list.isEmpty()) {
                continue;
            }
            List<Object> replaced = new java.util.ArrayList<>(list.size());
            boolean changed = false;
            for (Object item : list) {
                if (item instanceof Map<?, ?> || item != null
                        && !(item instanceof String) && !(item instanceof Number)) {
                    replaced.add(enrich(item, depth + 1));
                    changed = true;
                } else {
                    replaced.add(item);
                }
            }
            if (changed) {
                e.setValue(replaced);
            }
        }
    }

    private void fill(Map<String, Object> map) {
        Map<String, String> extra = new LinkedHashMap<>();
        for (Map.Entry<String, Object> e : map.entrySet()) {
            String key = e.getKey();
            Object v = e.getValue();
            if (v == null) {
                continue;
            }
            Long idValue = asLong(v);
            if (key.endsWith("Id") && idValue != null) {
                // 注意：本项目 Long 统一序列化为字符串，因此不能只判断 Number
                String name = nameOf(key, idValue);
                if (name != null && !name.isBlank()) {
                    extra.put(key + "Name", name);
                }
            } else if (v instanceof String s && !s.isBlank() && isEnumField(key)) {
                String label = EnumLabels.of(key, s);
                if (label != null && !label.equals(s)) {
                    extra.put(key + "Label", label);
                }
            }
        }
        map.putAll(extra);
    }

    /** 兼容 Number 与「纯数字字符串」两种形态 */
    private static Long asLong(Object v) {
        if (v instanceof Number n) {
            return n.longValue();
        }
        if (v instanceof String str && !str.isBlank()) {
            String t = str.trim();
            boolean digits = true;
            for (int i = 0; i < t.length(); i++) {
                if (!Character.isDigit(t.charAt(i))) {
                    digits = false;
                    break;
                }
            }
            if (digits && t.length() <= 20) {
                try {
                    return Long.parseLong(t);
                } catch (NumberFormatException ignore) {
                    return null;
                }
            }
        }
        return null;
    }

    private String nameOf(String key, long id) {
        return switch (key) {
            case "personId", "lesseePersonId", "applicantPersonId", "holderPersonId",
                 "complainantPersonId", "guestPersonId", "payerPersonId" ->
                    personName(id);
            case "houseId", "oldHouseId", "newHouseId", "fromHouseId", "toHouseId" -> houseName(id);
            case "orgId", "lessorOrgId", "decideOrgId" -> orgName(id);
            case "spaceId" -> spaceName(id);
            case "contractId", "oldContractId", "newContractId", "parentContractId" ->
                    bizNo("bp_biz_contract", "contract_no", "contractId", id);
            case "applicationId" -> bizNo("bp_biz_application", "application_no", "applicationId", id);
            case "batchId" -> bizNo("bp_biz_batch", "batch_no", "batchId", id);
            case "billId" -> bizNo("bp_fin_bill", "bill_no", "billId", id);
            case "terminationId" -> bizNo("bp_biz_termination", "termination_no", "terminationId", id);
            case "reviewId" -> bizNo("bp_biz_annual_review", "review_no", "reviewId", id);
            case "allocationId" -> bizNo("bp_biz_allocation", "allocation_no", "allocationId", id);
            case "userId", "decideUserId", "handleUserId", "operatorId",
                 "assignUserId", "approveById" -> bizNo("bp_iam_user", "username", "userId", id);
            case "feeItemId" -> bizNo("bp_fin_fee_item", "item_name", "feeItemId", id);
            case "standardId" -> bizNo("bp_fin_subsidy_standard", "standard_name", "standardId", id);
            case "ownerOrgId" -> bizNo("bp_iam_org", "org_name", "ownerOrgId", id);
            case "deviceId" -> bizNo("bp_dev_device", "device_code", "deviceId", id);
            default -> null;
        };
    }

    private String personName(long id) {
        return personCache.computeIfAbsent(id, k -> {
            trim();
            Person p = personMapper.selectById(k);
            return p == null ? "" : nullToEmpty(p.getPersonName());
        });
    }

    private String houseName(long id) {
        return houseCache.computeIfAbsent(id, k -> {
            trim();
            AssetHouse h = houseMapper.selectById(k);
            if (h == null) {
                return "";
            }
            return nullToEmpty(h.getHouseName() != null && !h.getHouseName().isBlank()
                    ? h.getHouseName() : h.getHouseCode());
        });
    }

    private String orgName(long id) {
        return orgCache.computeIfAbsent(id, k -> {
            trim();
            IamOrg o = orgMapper.selectById(k);
            return o == null ? "" : nullToEmpty(o.getOrgName());
        });
    }

    private String spaceName(long id) {
        return spaceCache.computeIfAbsent(id, k -> {
            trim();
            AssetSpace s = spaceMapper.selectById(k);
            return s == null ? "" : nullToEmpty(s.getSpaceName());
        });
    }

    /**
     * 通用业务编号解析。只用于展示（补 xxxName），命中失败返回空串。
     * SQL 用固定白名单表名/列名，不接受外部输入，无注入风险。
     */
    private String bizNo(String table, String column, String key, long id) {
        String cacheKey = key + ":" + id;
        return bizNoCache.computeIfAbsent(cacheKey.hashCode() * 31L + id, k -> {
            trim();
            try {
                java.util.List<String> rows = jdbcTemplate.queryForList(
                        "SELECT " + column + " FROM " + table + " WHERE id = ? LIMIT 1",
                        String.class, id);
                return rows.isEmpty() || rows.get(0) == null ? "" : rows.get(0);
            } catch (RuntimeException ex) {
                // 表不存在或数据异常时不影响主流程
                return "";
            }
        });
    }

    private static String nullToEmpty(String s) {
        return s == null ? "" : s;
    }

    /** 缓存超过上限时整体清空：实现简单，且这些数据是冪等的 */
    private void trim() {
        if (personCache.size() > CACHE_LIMIT) {
            personCache.clear();
        }
        if (houseCache.size() > CACHE_LIMIT) {
            houseCache.clear();
        }
        if (orgCache.size() > CACHE_LIMIT) {
            orgCache.clear();
        }
        if (spaceCache.size() > CACHE_LIMIT) {
            spaceCache.clear();
        }
    }

    /** 补全分页结果的行 */
    public List<Map<String, Object>> enrichRows(List<?> rows) {
        if (rows == null || rows.isEmpty()) {
            return List.of();
        }
        return rows.stream().map(this::enrich).toList();
    }
}
