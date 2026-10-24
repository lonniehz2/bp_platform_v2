# -*- coding: utf-8 -*-
"""房源计量模式：独立表 / 分摊 / 独立+公区分摊。

背景：一套房分隔多个独立房间出租时，水电表可能是
  INDEPENDENT 每间独立表
  SHARED      整户一表，按房间分摊
  MIXED       每间独立表 + 公区表分摊
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'asset')

# 实体
E = os.path.join(J, 'entity', 'AssetHouse.java')
s = io.open(E, encoding='utf-8').read()
if 'meterMode' not in s:
    s = s.replace('    private Integer currentCapacity;',
                  '    /** 计量模式：INDEPENDENT 独立表 / SHARED 分摊 / MIXED 独立+公区分摊 */\n'
                  '    private String meterMode;\n\n'
                  '    private Integer currentCapacity;', 1)
    if 'public String getMeterMode' not in s:
        i = s.rfind('}')
        s = s[:i] + ('\n    public String getMeterMode() { return meterMode; }\n'
                     '    public void setMeterMode(String meterMode) { this.meterMode = meterMode; }\n') + s[i:]
    io.open(E, 'w', encoding='utf-8', newline='').write(s)
    print('AssetHouse：meterMode 已加')

# 创建命令
C = os.path.join(J, 'dto', 'HouseCreateCmd.java')
s = io.open(C, encoding='utf-8').read()
if 'meterMode' not in s:
    s = s.replace('        String rentUnit,', '        String rentUnit,\n        String meterMode,', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('HouseCreateCmd：meterMode 已加')

# VO
V = os.path.join(J, 'dto', 'HouseVO.java')
s = io.open(V, encoding='utf-8').read()
if 'meterMode' not in s:
    s = s.replace('        String rentUnit,', '        String rentUnit,\n        String meterMode,', 1)
    s = s.replace('e.getRentUnit()', 'e.getRentUnit(), e.getMeterMode()', 1)
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('HouseVO：meterMode 已加')

# 服务映射
I = os.path.join(J, 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'setMeterMode' not in s:
    s = s.replace('e.setRentUnit(cmd.rentUnit());',
                  'e.setRentUnit(cmd.rentUnit());\n'
                  '        e.setMeterMode(normalizeMeterMode(cmd.meterMode()));', 1)
    if 'normalizeMeterMode' not in s:
        i = s.rstrip().rfind('}')
        s = s[:i] + '''
    /** 计量模式校验：空值默认独立表。 */
    private String normalizeMeterMode(String v) {
        if (v == null || v.isBlank()) {
            return "INDEPENDENT";
        }
        String up = v.trim().toUpperCase();
        if (!java.util.Set.of("INDEPENDENT", "SHARED", "MIXED").contains(up)) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid(
                    "计量模式只能是 INDEPENDENT / SHARED / MIXED");
        }
        return up;
    }
''' + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('HouseServiceImpl：meterMode 写入与校验已加')

print('完成')
