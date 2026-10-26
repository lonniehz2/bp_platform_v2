# -*- coding: utf-8 -*-
"""房源详情中文：orientation / rentUnit / meterMode（前后端各一份映射）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 前端 enums ----------
P = os.path.join(ROOT, 'frontend', 'src', 'constants', 'enums.js')
s = io.open(P, encoding='utf-8').read()
if 'rentUnit:' not in s:
    OLD = """  freezeScope: {
    ALL: '全部（含大门）', ROOM_LOCK: '仅房间门锁',
    EXCLUDE_MAIN_DOOR: '仅门锁（不停大门）'
  }
}"""
    NEW = """  freezeScope: {
    ALL: '全部（含大门）', ROOM_LOCK: '仅房间门锁',
    EXCLUDE_MAIN_DOOR: '仅门锁（不停大门）'
  },
  // 房源：这几个字段在详情里之前显示英文原值
  orientation: {
    SOUTH: '朝南', NORTH: '朝北', EAST: '朝东', WEST: '朝西',
    SOUTHEAST: '东南', SOUTHWEST: '西南', NORTHEAST: '东北', NORTHWEST: '西北',
    NORTH_SOUTH: '南北通透'
  },
  rentUnit: {
    AREA_MONTH: '元/㎡·月', HOUSE_MONTH: '元/套·月', BED_MONTH: '元/床·月',
    HOUSE_NIGHT: '元/套·夜', BED_NIGHT: '元/床·夜'
  },
  meterMode: {
    INDEPENDENT: '独立表（每间独立计量）', SHARED: '整户分摊（一表按间分摊）',
    MIXED: '独立表 + 公区分摊'
  }
}"""
    if OLD in s:
        s = s.replace(OLD, NEW, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('前端 enums 已补 orientation/rentUnit/meterMode')
    else:
        print('前端锚点不匹配')
else:
    print('前端已存在')

# ---------- 后端 EnumLabels ----------
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'common', 'util', 'EnumLabels.java')
s = io.open(P, encoding='utf-8', errors='replace').read()
if '"rentUnit"' not in s:
    OLD = """            "grantLevel", Map.of("OWNERSHIP", "产权级", "MANAGEMENT", "管理级",
                    "USAGE", "使用级", "VISIT", "访客级")"""
    NEW = """            "grantLevel", Map.of("OWNERSHIP", "产权级", "MANAGEMENT", "管理级",
                    "USAGE", "使用级", "VISIT", "访客级"),
            // 房源字段：避免详情/列表出现英文原值
            "orientation", Map.of("SOUTH", "朝南", "NORTH", "朝北", "EAST", "朝东",
                    "WEST", "朝西", "SOUTHEAST", "东南", "SOUTHWEST", "西南",
                    "NORTHEAST", "东北", "NORTHWEST", "西北", "NORTH_SOUTH", "南北通透"),
            "rentUnit", Map.of("AREA_MONTH", "元/㎡·月", "HOUSE_MONTH", "元/套·月",
                    "BED_MONTH", "元/床·月", "HOUSE_NIGHT", "元/套·夜",
                    "BED_NIGHT", "元/床·夜"),
            "meterMode", Map.of("INDEPENDENT", "独立表（每间独立计量）",
                    "SHARED", "整户分摊（一表按间分摊）", "MIXED", "独立表 + 公区分摊")"""
    if OLD in s:
        s = s.replace(OLD, NEW, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('后端 EnumLabels 已补三个字段')
    else:
        print('后端锚点不匹配')
else:
    print('后端已存在')
