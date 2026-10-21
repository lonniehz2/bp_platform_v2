# -*- coding: utf-8 -*-
"""报表枚举中文化：新建 EnumLabel 工具类并在报表行输出时翻译"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
UTIL_DIR = os.path.join(BASE, 'common', 'util')

UTIL = '''package com.yundao.bp.common.util;

import java.util.Map;

/**
 * 枚举值 → 中文标签。
 *
 * <p>用途：报表、CSV 导出、大屏等**面向用户输出**的场景，避免把
 * OCCUPIED / PUBLIC_RENTAL 这类内部编码直接展示给用户。
 * 内部接口（详情、列表 VO）仍返回编码，由前端按字典渲染，
 * 这里只服务于「一次性导出」这种没有前端渲染机会的场景。</p>
 */
public final class EnumLabels {

    private EnumLabels() {
    }

    /** 房源类型 */
    private static final Map<String, String> HOUSE_TYPE = Map.of(
            "PUBLIC_RENTAL", "公租房",
            "AFFORDABLE_RENTAL", "保障性租赁住房",
            "TALENT", "人才公寓",
            "APARTMENT", "公寓",
            "DORMITORY", "宿舍",
            "RENTAL", "出租房",
            "HOTEL", "酒店/民宿");

    /** 房源状态 */
    private static final Map<String, String> HOUSE_STATUS = Map.of(
            "VACANT", "空置",
            "PENDING_ALLOC", "待配租",
            "ALLOCATED", "已配租",
            "OCCUPIED", "已出租",
            "LOCKED", "锁定",
            "REPAIR", "维修中",
            "OFFLINE", "停用");

    /** 保障类型 */
    private static final Map<String, String> SECURITY_TYPE = Map.of(
            "PUBLIC", "公租房",
            "AFFORDABLE", "保租房",
            "TALENT", "人才房",
            "LOW_RENT", "廉租房");

    /** 合同状态 */
    private static final Map<String, String> CONTRACT_STATUS = Map.of(
            "DRAFT", "草稿",
            "PENDING_SIGN", "待签约",
            "SIGNING", "签约中",
            "EFFECTIVE", "履约中",
            "RENEWING", "续签中",
            "EXPIRED", "已到期",
            "TERMINATED", "已终止",
            "CANCELLED", "已作废");

    /** 账单状态 */
    private static final Map<String, String> BILL_STATUS = Map.of(
            "UNPAID", "未缴",
            "PARTIAL", "部分缴纳",
            "PAID", "已缴清",
            "OVERDUE", "已逾期",
            "WAIVED", "已减免",
            "CANCELLED", "已取消");

    public static String of(String type, Object value) {
        if (value == null) {
            return "";
        }
        String v = String.valueOf(value);
        if (v.isBlank()) {
            return "";
        }
        Map<String, String> dict = switch (type == null ? "" : type) {
            case "HOUSE_TYPE" -> HOUSE_TYPE;
            case "HOUSE_STATUS" -> HOUSE_STATUS;
            case "SECURITY_TYPE" -> SECURITY_TYPE;
            case "CONTRACT_STATUS" -> CONTRACT_STATUS;
            case "BILL_STATUS" -> BILL_STATUS;
            default -> null;
        };
        if (dict == null) {
            return v;
        }
        // 未登记的枚举值原样返回，避免脏数据被吞掉
        return dict.getOrDefault(v, v);
    }
}
'''

os.makedirs(UTIL_DIR, exist_ok=True)
io.open(os.path.join(UTIL_DIR, 'EnumLabels.java'), 'w', encoding='utf-8').write(UTIL)
print('  ✓ 新建 common/util/EnumLabels.java（5 类枚举中文映射）')

# ---------- 在 ReportServiceImpl 的 rowsOf 中应用 ----------
P = os.path.join(BASE, 'rpt', 'service', 'impl', 'ReportServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

if 'EnumLabels' not in s:
    # 1) import
    s = s.replace('package com.yundao.bp.rpt.service.impl;\n',
                  'package com.yundao.bp.rpt.service.impl;\n', 1)
    idx = s.find('\nimport ')
    s = s[:idx] + '\nimport com.yundao.bp.common.util.EnumLabels;' + s[idx:]

    # 2) 翻译各处枚举字段
    repl = [
        ('r.put("houseType", h.getHouseType());',
         'r.put("houseType", EnumLabels.of("HOUSE_TYPE", h.getHouseType()));'),
        ('r.put("houseStatus", h.getHouseStatus());',
         'r.put("houseStatus", EnumLabels.of("HOUSE_STATUS", h.getHouseStatus()));'),
        ('r.put("contractStatus", c.getContractStatus());',
         'r.put("contractStatus", EnumLabels.of("CONTRACT_STATUS", c.getContractStatus()));'),
        ('r.put("billStatus", b.getBillStatus());',
         'r.put("billStatus", EnumLabels.of("BILL_STATUS", b.getBillStatus()));'),
    ]
    n = 0
    for old, new in repl:
        if old in s:
            s = s.replace(old, new)
            n += 1
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ ReportServiceImpl：%d 处枚举改为中文输出' % n)
else:
    print('  - ReportServiceImpl 已接入 EnumLabels')
