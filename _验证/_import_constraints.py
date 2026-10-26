# -*- coding: utf-8 -*-
"""导入模板内置可选值约束 + 后端严格校验。

1) 模板：表头下加一行「# 可选值说明」，解析时跳过以 # 开头的行
2) 后端：四个枚举字段严格校验，填错直接报「第 N 行：用途不合法：xx（可选：民用 / 商用）」
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------------- 1) 前端模板：加说明行 ----------------
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Houses.vue')
s = io.open(P, encoding='utf-8').read()

OLD = """  const rows = [
    'DEMO-P1,P1-R1,HOUSE-001,示例房源1,公租房,民用,55,15,元/㎡·月,空置',"""
NEW = """  const note = '# 可选值：房源类型=公租房/保障性租赁住房/人才公寓/公寓/宿舍/酒店民宿/出租房；'
    + '用途=民用/商用；计价单位=元/㎡·月/元/套·月/元/床·月/元/套·夜/元/床·夜；'
    + '房源状态=空置/可租/待配租/已配租/已出租/维修中/锁定（本行可保留，导入时自动忽略）'
  const rows = [
    'DEMO-P1,P1-R1,HOUSE-001,示例房源1,公租房,民用,55,15,元/㎡·月,空置',"""
if OLD in s:
    s = s.replace(OLD, NEW, 1)

OLD2 = """  const blob = new Blob(['\\ufeff' + header + rows + '\\n'],
    { type: 'text/csv;charset=utf-8' })"""
NEW2 = """  const blob = new Blob(['\\ufeff' + header + '\\n' + note + '\\n' + rows + '\\n'],
    { type: 'text/csv;charset=utf-8' })"""
if OLD2 in s:
    s = s.replace(OLD2, NEW2, 1)

OLD3 = """          可选值：房源类型（公租房 / 保障性租赁住房 / 人才公寓 / 公寓 / 宿舍 / 酒店民宿）；
          用途（民用 / 商用）；计价单位（元/㎡·月 / 元/套·月 / 元/床·月 / 元/套·夜 / 元/床·夜）；
          房源状态（空置 / 待配租 / 已配租 / 已出租 / 维修中 / 锁定）。"""
NEW3 = """          模板第 2 行是可选值说明（以 # 开头，可保留，导入时自动忽略）；填错会被逐行拦下并提示可选值。"""
if OLD3 in s:
    s = s.replace(OLD3, NEW3, 1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('前端模板已加可选值说明行')

# ---------------- 2) 后端：跳过说明行 + 严格校验 ----------------
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'asset', 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

OLD_SKIP = """                if (line.isBlank()) {
                    continue;
                }"""
NEW_SKIP = """                if (line.isBlank() || line.startsWith("#") || line.startsWith("\\ufeff#")) {
                    continue;   // 空行 / 以 # 开头的说明行
                }"""
if OLD_SKIP in s:
    s = s.replace(OLD_SKIP, NEW_SKIP, 1)
    print('后端已跳过说明行')

# 严格校验：把 codeOf 调用换成 resolveEnum（返回 null 即非法）
OLD_VAL = """                    e.setHouseType(houseType.isBlank()
                            ? "PUBLIC_RENTAL" : codeOf("houseType", houseType));
                    e.setUseType(c.length > 5 && !c[5].isBlank()
                            ? codeOf("useType", c[5].trim()) : "CIVIL");
                    if (c.length > 6 && !c[6].isBlank()) {
                        e.setArea(new java.math.BigDecimal(c[6].trim()));
                    }
                    if (c.length > 7 && !c[7].isBlank()) {
                        e.setRentStandard(new java.math.BigDecimal(c[7].trim()));
                    }
                    e.setRentUnit(c.length > 8 && !c[8].isBlank()
                            ? codeOf("rentUnit", c[8].trim()) : "AREA_MONTH");
                    e.setHouseStatus(c.length > 9 && !c[9].isBlank()
                            ? codeOf("houseStatus", c[9].trim()) : "VACANT");"""
NEW_VAL = """                    String typeCode = houseType.isBlank()
                            ? "PUBLIC_RENTAL" : requireEnum("houseType", houseType);
                    String useCode = c.length > 5 && !c[5].isBlank()
                            ? requireEnum("useType", c[5].trim()) : "CIVIL";
                    String unitCode = c.length > 8 && !c[8].isBlank()
                            ? requireEnum("rentUnit", c[8].trim()) : "AREA_MONTH";
                    String statusCode = c.length > 9 && !c[9].isBlank()
                            ? requireEnum("houseStatus", c[9].trim()) : "VACANT";
                    e.setHouseType(typeCode);
                    e.setUseType(useCode);
                    if (c.length > 6 && !c[6].isBlank()) {
                        e.setArea(new java.math.BigDecimal(c[6].trim()));
                    }
                    if (c.length > 7 && !c[7].isBlank()) {
                        e.setRentStandard(new java.math.BigDecimal(c[7].trim()));
                    }
                    e.setRentUnit(unitCode);
                    e.setHouseStatus(statusCode);"""
if OLD_VAL in s:
    s = s.replace(OLD_VAL, NEW_VAL, 1)
    print('后端已切换为严格校验')

# 新增 requireEnum + 允许值表（放在 codeOf 前面）
HELPERS = '''
    /** 各枚举字段的允许值（中文标签 → 代码），用于导入校验与错误提示。 */
    private static final java.util.Map<String, java.util.Map<String, String>> IMPORT_ENUMS =
            importEnumTable();

    private static java.util.Map<String, java.util.Map<String, String>> importEnumTable() {
        java.util.Map<String, java.util.Map<String, String>> all = new java.util.HashMap<>();
        all.put("houseType", java.util.Map.ofEntries(
                java.util.Map.entry("公租房", "PUBLIC_RENTAL"),
                java.util.Map.entry("保障性租赁住房", "AFFORDABLE_RENTAL"),
                java.util.Map.entry("人才公寓", "TALENT"),
                java.util.Map.entry("公寓", "APARTMENT"),
                java.util.Map.entry("宿舍", "DORMITORY"),
                java.util.Map.entry("酒店民宿", "HOTEL"),
                java.util.Map.entry("酒店", "HOTEL"),
                java.util.Map.entry("民宿", "HOTEL"),
                java.util.Map.entry("出租房", "RENTAL")));
        all.put("useType", java.util.Map.of(
                "民用", "CIVIL", "商用", "COMMERCIAL"));
        all.put("rentUnit", java.util.Map.ofEntries(
                java.util.Map.entry("元/㎡·月", "AREA_MONTH"),
                java.util.Map.entry("元/平米·月", "AREA_MONTH"),
                java.util.Map.entry("元/套·月", "HOUSE_MONTH"),
                java.util.Map.entry("元/床·月", "BED_MONTH"),
                java.util.Map.entry("元/套·夜", "HOUSE_NIGHT"),
                java.util.Map.entry("元/床·夜", "BED_NIGHT")));
        all.put("houseStatus", java.util.Map.ofEntries(
                java.util.Map.entry("空置", "VACANT"),
                java.util.Map.entry("可租", "VACANT"),
                java.util.Map.entry("待配租", "PENDING_ALLOC"),
                java.util.Map.entry("已配租", "ALLOCATED"),
                java.util.Map.entry("已出租", "OCCUPIED"),
                java.util.Map.entry("维修中", "REPAIR"),
                java.util.Map.entry("锁定", "LOCKED")));
        return all;
    }

    private static final java.util.Map<String, String> FIELD_LABEL = java.util.Map.of(
            "houseType", "房源类型", "useType", "用途",
            "rentUnit", "计价单位", "houseStatus", "房源状态");

    /**
     * 严格解析枚举：中文标签或英文代码均可；非法值直接抛出可读错误。
     * 错误信息带上可选值，便于用户对照模板修正。
     */
    private String requireEnum(String field, String raw) {
        String v = raw == null ? "" : raw.trim();
        java.util.Map<String, String> map = IMPORT_ENUMS.get(field);
        String code = map == null ? null : map.get(v);
        if (code == null && !v.isBlank()) {
            String up = v.toUpperCase().replace(' ', '_');
            if (map != null && map.containsValue(up)) {
                code = up;
            }
        }
        if (code == null) {
            String allowed = map == null ? "" : String.join(" / ", map.keySet());
            throw com.yundao.bp.common.exception.BizException.paramInvalid(
                    FIELD_LABEL.getOrDefault(field, field) + "不合法：" + v
                            + "（可选：" + allowed + "）");
        }
        return code;
    }

'''
if 'private String requireEnum(' not in s:
    s = s.replace('    private String codeOf(String field, String value) {',
                  HELPERS + '    private String codeOf(String field, String value) {', 1)
    print('后端已加 requireEnum 与允许值表')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
