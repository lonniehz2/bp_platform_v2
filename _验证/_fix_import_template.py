# -*- coding: utf-8 -*-
"""房源导入：模板表头与枚举值中文化。

- 前端模板：中文表头 + 中文示例值（保留 10 列顺序）
- 后端解析：兼容中文表头跳过；中文枚举值自动转码（也接受英文码）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------------- 1) 前端模板 ----------------
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Houses.vue')
s = io.open(P, encoding='utf-8').read()
OLD = """function downloadTemplate() {
  const header = 'ORGANIZATION_CODE,SPACE_CODE,HOUSE_CODE,HOUSE_NAME,HOUSE_TYPE,'
    + 'USE_TYPE,AREA,RENT,RENT_UNIT,STATUS\\n'
  const sample = 'DEMO-P1,P1-R1,HOUSE-001,示例房源1,PUBLIC_RENTAL,CIVIL,55,15,'
    + 'AREA_MONTH,VACANT\\n'
  const blob = new Blob(['\\ufeff' + header + sample], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'house-import-template.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}"""
NEW = """function downloadTemplate() {
  // 表头与示例值都用中文，业务人员可直接填；后端同时兼容英文码
  const header = '组织编码,空间编码,房源编号,房源名称,房源类型,用途,建筑面积(㎡),'
    + '租金标准,计价单位,房源状态\\n'
  const rows = [
    'DEMO-P1,P1-R1,HOUSE-001,示例房源1,公租房,民用,55,15,元/㎡·月,空置',
    'DEMO-P1,P1-R2,HOUSE-002,示例房源2,保障性租赁住房,民用,48.5,18.5,元/套·月,空置',
    'DEMO-P1,P1-R3,HOUSE-003,示例房源3,人才公寓,民用,32,1200,元/套·夜,待配租'
  ].join('\\n')
  const blob = new Blob(['\\ufeff' + header + rows + '\\n'],
    { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '房源导入模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}"""
if OLD in s:
    s = s.replace(OLD, NEW, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('前端模板已中文化')
else:
    print('前端模板锚点不匹配')

# 提示文案补一句可选值说明
OLD_TIP = """        <span class="muted" style="font-size:12px">
          首行可为表头；编号重复的行会被跳过并给出原因
        </span>"""
NEW_TIP = """        <div class="muted" style="font-size:12px;line-height:1.6">
          首行可为表头；编号重复的行会被跳过并给出原因。<br />
          可选值：房源类型（公租房 / 保障性租赁住房 / 人才公寓 / 公寓 / 宿舍 / 酒店民宿）；
          用途（民用 / 商用）；计价单位（元/㎡·月 / 元/套·月 / 元/床·月 / 元/套·夜 / 元/床·夜）；
          房源状态（空置 / 待配租 / 已配租 / 已出租 / 维修中 / 锁定）。
        </div>"""
if OLD_TIP in s:
    s = s.replace(OLD_TIP, NEW_TIP, 1)
    print('导入提示已补充可选值')

# ---------------- 2) 后端解析 ----------------
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'asset', 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

OLD_HEAD = """                if (lineNo == 1
                        && line.toLowerCase().replace("_", "").replace("-", "")
                                .contains("housecode")) {
                    continue;   // 表头
                }"""
NEW_HEAD = """                if (lineNo == 1 && isHeaderLine(line)) {
                    continue;   // 表头（英文或中文）
                }"""
if OLD_HEAD in s:
    s = s.replace(OLD_HEAD, NEW_HEAD, 1)
    print('后端表头识别已改为兼容中英文')

OLD_SET = """                    e.setHouseType(houseType.isBlank() ? "PUBLIC_RENTAL" : houseType);
                    e.setUseType(c.length > 5 && !c[5].isBlank() ? c[5].trim() : "CIVIL");
                    if (c.length > 6 && !c[6].isBlank()) {
                        e.setArea(new java.math.BigDecimal(c[6].trim()));
                    }
                    if (c.length > 7 && !c[7].isBlank()) {
                        e.setRentStandard(new java.math.BigDecimal(c[7].trim()));
                    }
                    e.setRentUnit(c.length > 8 && !c[8].isBlank() ? c[8].trim() : "AREA_MONTH");
                    e.setHouseStatus(c.length > 9 && !c[9].isBlank() ? c[9].trim() : "VACANT");"""
NEW_SET = """                    e.setHouseType(houseType.isBlank()
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
if OLD_SET in s:
    s = s.replace(OLD_SET, NEW_SET, 1)
    print('后端枚举解析已加中文转码')

# 追加辅助方法（放在 err 方法之前）
HELPERS = '''
    /** 表头行判断：兼容英文（HOUSE_CODE）与中文（房源编号/组织编码）。 */
    private boolean isHeaderLine(String line) {
        String low = line.toLowerCase().replace("_", "").replace("-", "")
                .replace("\\ufeff", "");
        return low.contains("housecode") || line.contains("房源编号")
                || line.contains("组织编码") || line.contains("空间编码");
    }

    /**
     * 中文枚举值 → 代码；已是英文码则原样返回（大小写不敏感）。
     * 导入模板给业务人员用中文，接口/历史文件仍兼容英文码。
     */
    private String codeOf(String field, String value) {
        if (value == null || value.isBlank()) {
            return value;
        }
        String v = value.trim();
        java.util.Map<String, String> map = switch (field) {
            case "houseType" -> java.util.Map.ofEntries(
                    java.util.Map.entry("公租房", "PUBLIC_RENTAL"),
                    java.util.Map.entry("保障性租赁住房", "AFFORDABLE_RENTAL"),
                    java.util.Map.entry("人才公寓", "TALENT"),
                    java.util.Map.entry("公寓", "APARTMENT"),
                    java.util.Map.entry("宿舍", "DORMITORY"),
                    java.util.Map.entry("酒店", "HOTEL"),
                    java.util.Map.entry("民宿", "HOTEL"),
                    java.util.Map.entry("酒店/民宿", "HOTEL"),
                    java.util.Map.entry("出租房", "RENTAL"));
            case "useType" -> java.util.Map.of(
                    "民用", "CIVIL", "商用", "COMMERCIAL");
            case "rentUnit" -> java.util.Map.ofEntries(
                    java.util.Map.entry("元/㎡·月", "AREA_MONTH"),
                    java.util.Map.entry("元/平米·月", "AREA_MONTH"),
                    java.util.Map.entry("元/套·月", "HOUSE_MONTH"),
                    java.util.Map.entry("元/床·月", "BED_MONTH"),
                    java.util.Map.entry("元/套·夜", "HOUSE_NIGHT"),
                    java.util.Map.entry("元/床·夜", "BED_NIGHT"));
            case "houseStatus" -> java.util.Map.ofEntries(
                    java.util.Map.entry("空置", "VACANT"),
                    java.util.Map.entry("可租", "VACANT"),
                    java.util.Map.entry("待配租", "PENDING_ALLOC"),
                    java.util.Map.entry("已配租", "ALLOCATED"),
                    java.util.Map.entry("已出租", "OCCUPIED"),
                    java.util.Map.entry("维修中", "REPAIR"),
                    java.util.Map.entry("锁定", "LOCKED"));
            default -> java.util.Map.of();
        };
        String hit = map.get(v);
        if (hit != null) {
            return hit;
        }
        // 已是代码：统一大写（容忍空格/小写）
        String up = v.toUpperCase().replace(' ', '_');
        return up;
    }

'''
if 'private String codeOf(' not in s:
    s = s.replace('    private java.util.Map<String, Object> err(int line, String message) {',
                  HELPERS + '    private java.util.Map<String, Object> err(int line, String message) {', 1)
    print('后端已加 codeOf/isHeaderLine')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
