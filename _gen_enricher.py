# -*- coding: utf-8 -*-
"""统一显示层补全：ID→名称、枚举→中文
生成 DisplayEnricher + ResponseBodyAdvice
"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp\common\web'
os.makedirs(BASE, exist_ok=True)

ENRICHER = '''package com.yundao.bp.common.web;

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

    private final Map<Long, String> personCache = new ConcurrentHashMap<>();
    private final Map<Long, String> houseCache = new ConcurrentHashMap<>();
    private final Map<Long, String> orgCache = new ConcurrentHashMap<>();
    private final Map<Long, String> spaceCache = new ConcurrentHashMap<>();

    public DisplayEnricher(PersonMapper personMapper, AssetHouseMapper houseMapper,
                           IamOrgMapper orgMapper, AssetSpaceMapper spaceMapper,
                           ObjectMapper objectMapper) {
        this.personMapper = personMapper;
        this.houseMapper = houseMapper;
        this.orgMapper = orgMapper;
        this.spaceMapper = spaceMapper;
        this.objectMapper = objectMapper;
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
    public Map<String, Object> enrich(Object row) {
        if (row == null) {
            return null;
        }
        if (row instanceof Map<?, ?> m) {
            @SuppressWarnings("unchecked")
            Map<String, Object> copy = new LinkedHashMap<>((Map<String, Object>) m);
            fill(copy);
            return copy;
        }
        Map<String, Object> map = objectMapper.convertValue(row, LinkedHashMap.class);
        fill(map);
        return map;
    }

    private void fill(Map<String, Object> map) {
        Map<String, String> extra = new LinkedHashMap<>();
        for (Map.Entry<String, Object> e : map.entrySet()) {
            String key = e.getKey();
            Object v = e.getValue();
            if (v == null) {
                continue;
            }
            if (key.endsWith("Id") && v instanceof Number n) {
                String name = nameOf(key, n.longValue());
                if (name != null && !name.isBlank()) {
                    extra.put(key + "Name", name);
                }
            } else if (v instanceof String s && !s.isBlank() && isEnumField(key)) {
                String label = EnumLabels.of(FIELD_ENUM_TYPE.get(key), s);
                if (label != null && !label.equals(s)) {
                    extra.put(key + "Label", label);
                }
            }
        }
        map.putAll(extra);
    }

    private String nameOf(String key, long id) {
        return switch (key) {
            case "personId", "lesseePersonId", "applicantPersonId", "holderPersonId",
                 "complainantPersonId", "guestPersonId", "payerPersonId" ->
                    personName(id);
            case "houseId", "oldHouseId", "newHouseId", "fromHouseId", "toHouseId" -> houseName(id);
            case "orgId", "lessorOrgId", "decideOrgId" -> orgName(id);
            case "spaceId" -> spaceName(id);
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
'''

ADVICE = '''package com.yundao.bp.common.web;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import org.springframework.core.MethodParameter;
import org.springframework.http.MediaType;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice;

import java.util.List;

/**
 * 统一响应补全：在序列化前给分页/列表结果补上名称与中文标签。
 *
 * <p>为什么放在这一层：显示层缺陷（界面上出现 {@code 370832686538952704}、
 * {@code ALLOCATED}）散落在几十个接口，逐个改 VO 既慢又容易漏。
 * 在此统一处理，**新写的接口自动获得补全能力**。</p>
 *
 * <p>安全性：只对 {@link PageResult} 与 {@code List} 生效，
 * 且只**追加**字段，原字段原样保留，不影响任何调用方。</p>
 */
@RestControllerAdvice
public class DisplayEnrichAdvice implements ResponseBodyAdvice<Object> {

    private final DisplayEnricher enricher;

    public DisplayEnrichAdvice(DisplayEnricher enricher) {
        this.enricher = enricher;
    }

    @Override
    public boolean supports(MethodParameter returnType, Class converterType) {
        return true;
    }

    @Override
    public Object beforeBodyWrite(Object body, MethodParameter returnType,
                                  MediaType selectedContentType,
                                  Class selectedConverterType,
                                  ServerHttpRequest request,
                                  ServerHttpResponse response) {
        if (!(body instanceof R<?> r) || r.data() == null) {
            return body;
        }
        Object data = r.data();
        if (data instanceof PageResult<?> pr) {
            return new R<>(r.code(), r.message(),
                    new PageResult<>(pr.total(), pr.pageNum(), pr.pageSize(),
                            enricher.enrichRows(pr.rows())),
                    r.timestamp());
        }
        if (data instanceof List<?> list && !list.isEmpty()
                && !(list.get(0) instanceof Map<?, ?>)) {
            return new R<>(r.code(), r.message(), enricher.enrichRows(list), r.timestamp());
        }
        return body;
    }
}
'''

io.open(os.path.join(BASE, 'DisplayEnricher.java'), 'w', encoding='utf-8').write(ENRICHER)
io.open(os.path.join(BASE, 'DisplayEnrichAdvice.java'), 'w', encoding='utf-8').write(ADVICE)
print('  ✓ 生成 DisplayEnricher.java + DisplayEnrichAdvice.java')
