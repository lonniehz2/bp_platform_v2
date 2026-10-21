# -*- coding: utf-8 -*-
"""历史数据修补：为「已履约但没有占用记录」的合同补建占用

背景：占用联动是后加的能力，此前生效的合同只改了合同状态，房源仍是
待分配/空置，占用流水为空——看板上会出现「合同履约中 + 房源空置」。

本脚本按与 OccupancyService 相同的规则补齐：
  · 合同状态 EFFECTIVE / RENEWING 且无 ACTIVE 占用
  · 房源存在且有剩余容量
  · 插入 ACTIVE 占用，房源置 OCCUPIED、入住人数 +1

幂等：已有 ACTIVE 占用的合同会跳过，可重复执行。

用法：
  python _backfill_occupancy.py --dry
  python _backfill_occupancy.py
"""
import sys

import pymysql

DRY = '--dry' in sys.argv

SELECT_DUE = """
select c.id, c.contract_no, c.house_id, c.lessee_person_id, c.lease_start, c.lease_end
from bp_biz_contract c
where c.contract_status in ('EFFECTIVE', 'RENEWING')
  and c.house_id is not null
  and not exists (select 1 from bp_asset_space_occupancy o
                  where o.source_type = 'CONTRACT' and o.source_id = c.id and o.status = 'ACTIVE')
"""


def main():
    c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                        password='5677@Mysql', database='bp_platform', charset='utf8mb4')
    cur = c.cursor()
    cur.execute(SELECT_DUE)
    due = cur.fetchall()
    print('待补占用合同：%d 份' % len(due))

    done = skipped = 0
    for cid, cno, hid, pid, start, end in due:
        cur.execute('select space_id, house_status, current_capacity, max_capacity, tenant_id '
                    'from bp_asset_house where id=%s', (hid,))
        row = cur.fetchone()
        if not row:
            print('  跳过 %s：房源 %s 不存在' % (cno, hid))
            skipped += 1
            continue
        space_id, status, cap, maxcap, tenant = row
        cap = cap or 0
        if maxcap and cap >= maxcap:
            print('  跳过 %s：房源 %s 已满员 %s/%s' % (cno, hid, cap, maxcap))
            skipped += 1
            continue
        if DRY:
            print('  将补 %s → 房源 %s（%s，入住 %s→%s）' % (cno, hid, status, cap, cap + 1))
            done += 1
            continue
        cur.execute("""insert into bp_asset_space_occupancy
                       (id, tenant_id, space_id, house_id, person_id, occupy_type, is_primary,
                        start_date, end_date, status, source_type, source_id, create_by, create_time,
                        update_by, update_time)
                       values (%s,%s,%s,%s,%s,'CONTRACT',1,%s,%s,'ACTIVE','CONTRACT',%s,
                               'backfill',now(3),'backfill',now(3))""",
                    (_next_id(), tenant, space_id, hid, pid, start, end, cid))
        cur.execute("update bp_asset_house set house_status='OCCUPIED', current_capacity=%s "
                    "where id=%s", (cap + 1, hid))
        print('  已补 %s → 房源 %s（%s → OCCUPIED）' % (cno, hid, status))
        done += 1

    if not DRY:
        c.commit()

    cur.execute("select count(*) from bp_asset_space_occupancy where status='ACTIVE'")
    active = cur.fetchone()[0]
    cur.execute("select house_status, count(*) from bp_asset_house group by house_status")
    dist = cur.fetchall()
    print('\n补建 %d 份，跳过 %d 份%s' % (done, skipped, '（dry-run）' if DRY else ''))
    print('ACTIVE 占用 %d 条；房源状态分布 %s' % (active, dist))
    c.close()
    return 0


_id_seq = [0]


def _next_id():
    """给补建记录生成一个不冲突的雪花风格 ID（时间片 + 自增）。"""
    import time
    if not _id_seq[0]:
        _id_seq[0] = int(time.time() * 1000) * 1000
    _id_seq[0] += 1
    return _id_seq[0]


if __name__ == '__main__':
    sys.exit(main())
