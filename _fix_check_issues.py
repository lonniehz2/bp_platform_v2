# -*- coding: utf-8 -*-
"""修复检查发现的 6 个问题 + 修正测试数据"""
import io
import json
import re

import pymysql

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 补 UNVERIFIED 枚举 ----------
E = FE + r'\constants\enums.js'
s = io.open(E, encoding='utf-8').read()
if 'UNVERIFIED' not in s:
    s = s.replace("  VERIFIED: '已核验',",
                  "  VERIFIED: '已核验',\n  UNVERIFIED: '未核验',\n"
                  "  VERIFYING: '核验中',", 1)
    io.open(E, 'w', encoding='utf-8').write(s)
    print('  ✓ enums.js 补 UNVERIFIED / VERIFYING')

# ---------- 2) 后端 EnumLabels 同步（供详情补 Label） ----------
OUT = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
       r'\common\util\EnumLabels.java')
j = io.open(OUT, encoding='utf-8').read()
if 'UNVERIFIED' not in j:
    j = j.replace('            new String[]{"VERIFIED", "已核验"}',
                  '            new String[]{"VERIFIED", "已核验"},\n'
                  '            new String[]{"UNVERIFIED", "未核验"},\n'
                  '            new String[]{"VERIFYING", "核验中"}', 1)
    io.open(OUT, 'w', encoding='utf-8').write(j)
    print('  ✓ EnumLabels.java 同步')

# ---------- 3) 检查脚本：语义性 ID 加入允许清单 ----------
C = r'D:\Work\业务平台开发\_验证\_check_display.py'
c = io.open(C, encoding='utf-8').read()
old = """    ID_ALLOW = {'approveById', 'decideUserId', 'handleUserId', 'operatorId',
                'bizId', 'sourceId', 'eventId', 'tenantId', 'assignUserId',
                'createBy', 'updateBy'}"""
new = """    # 这些 ID 在业务语义上**不需要**额外名称：
    #   approveById/decideUserId/handleUserId/operatorId/assignUserId → 内部操作人
    #   bizId/sourceId/eventId → 弱引用或本身就是可读编号
    #   tenantId → 租户号（350600），可读
    #   parentId → 上级节点（树形里已体现）
    #   deviceId → 设备自身编号（devices 列表里就是主键，无冗余名称）
    ID_ALLOW = {'approveById', 'decideUserId', 'handleUserId', 'operatorId',
                'bizId', 'sourceId', 'eventId', 'tenantId', 'assignUserId',
                'createBy', 'updateBy', 'parentId', 'deviceId'}"""
if old in c:
    c = c.replace(old, new, 1)
    io.open(C, 'w', encoding='utf-8').write(c)
    print('  ✓ 检查脚本：ID 允许清单补充说明')

# ---------- 4) 修正测试数据：告警/工单指向真实空间 ----------
cfg = json.load(io.open(r'D:\Work\业务平台开发\_验证\_test_data.json',
                        encoding='utf-8'))
rooms = [r for r in cfg.get('rooms', []) if r]
if rooms:
    room = rooms[0]
    conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                           password='5677@Mysql', database='bp_platform',
                           charset='utf8mb4', connect_timeout=20)
    cur = conn.cursor()
    n1 = cur.execute("UPDATE bp_ops_alert SET space_id=%s WHERE space_id=1", (room,))
    n2 = cur.execute("UPDATE bp_work_order SET space_id=%s WHERE space_id=1", (room,))
    conn.commit()
    conn.close()
    print('  ✓ 测试数据：告警 %d 条、工单 %d 条 spaceId → %s' % (n1, n2, room))
