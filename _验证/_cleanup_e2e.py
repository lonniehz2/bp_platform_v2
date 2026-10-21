# -*- coding: utf-8 -*-
"""清理 E2E 自动化产生的测试数据（含房源占用回滚）

识别规则（与 ui_e2e.js 的命名约定对应）：
  · 人员：person_name 以 E2E人员 / DIAG 开头
  · 计费项目：item_code 以 E2E 开头
  · 合同：lessee_phone = 13900002222（E2E 专用号码）

合同清理必须连带处理房源占用：
  1. 删掉这些合同的占用流水
  2. 若房源已无 ACTIVE 占用，把房源状态放回 VACANT、入住人数归零
否则每跑一轮就会留下「房源已入住但合同已删除」的僵尸房源。

用法：
  python _cleanup_e2e.py          # 执行清理
  python _cleanup_e2e.py --dry    # 只看会删多少
"""
import sys

import pymysql

DRY = '--dry' in sys.argv
E2E_PHONE = '13900002222'


def main():
    c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                        password='5677@Mysql', database='bp_platform', charset='utf8mb4')
    cur = c.cursor()
    total = 0
    verb = '将删除' if DRY else '已删除'

    # ---------- 1. 定位 E2E 合同及其房源 ----------
    cur.execute('select id, house_id from bp_biz_contract where lessee_phone = %s', (E2E_PHONE,))
    contracts = cur.fetchall()
    cids = [r[0] for r in contracts]
    hids = sorted({r[1] for r in contracts if r[1]})
    print('E2E 合同 %d 份，涉及房源 %d 间' % (len(cids), len(hids)))

    if cids and not DRY:
        fmt = ','.join(['%s'] * len(cids))
        n = cur.execute(
            "delete from bp_asset_space_occupancy where source_type='CONTRACT' and source_id in (%s)" % fmt,
            cids)
        print('%-22s %-24s %s %d' % ('占用流水', 'space_occupancy', verb, n))
        total += n

    if cids:
        fmt = ','.join(['%s'] * len(cids))
        if DRY:
            n = len(cids)
        else:
            n = cur.execute('delete from bp_biz_contract where id in (%s)' % fmt, cids)
        print('%-22s %-24s %s %d' % ('合同', 'bp_biz_contract', verb, n))
        total += n

    # ---------- 2. 房源状态回滚 ----------
    for hid in hids:
        cur.execute("select count(*) from bp_asset_space_occupancy "
                    "where house_id=%s and status='ACTIVE'", (hid,))
        active = cur.fetchone()[0]
        if active:
            print('%-22s %-24s 保留（仍有 %d 条在用占用）' % ('房源 %s' % hid, 'bp_asset_house', active))
            continue
        if DRY:
            cur.execute("select house_status from bp_asset_house where id=%s", (hid,))
            row = cur.fetchone()
            print('%-22s %-24s 将重置为 VACANT（当前 %s）' % ('房源 %s' % hid, 'bp_asset_house',
                                                        row[0] if row else '缺失'))
        else:
            n = cur.execute("update bp_asset_house set house_status='VACANT', current_capacity=0 "
                            "where id=%s and house_status in ('OCCUPIED','ALLOCATED','LOCKED')", (hid,))
            if n:
                print('%-22s %-24s 重置为 VACANT' % ('房源 %s' % hid, 'bp_asset_house'))
                total += n

    # ---------- 3. 其它测试数据 ----------
    extra = [
        ('计费项目', 'bp_fin_fee_item', "item_code like 'E2E%'"),
        ('人员', 'bp_person', "person_name like 'E2E人员%' or person_name like 'DIAG%'"),
        ('脏合同（房源不存在）', 'bp_biz_contract',
         'house_id not in (select id from bp_asset_house)'),
    ]
    for label, table, where in extra:
        if DRY:
            cur.execute('select count(*) from %s where %s' % (table, where))
            n = cur.fetchone()[0]
        else:
            n = cur.execute('delete from %s where %s' % (table, where))
        total += n
        print('%-22s %-24s %s %d' % (label, table, verb, n))

    if not DRY:
        c.commit()

    print('\n合计 %d 行%s' % (total, '（dry-run，未改动）' if DRY else ''))
    for t in ('bp_person', 'bp_biz_contract', 'bp_asset_space_occupancy', 'bp_fin_fee_item'):
        cur.execute('select count(*) from ' + t)
        print('  剩余 %-26s %d' % (t, cur.fetchone()[0]))
    c.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
