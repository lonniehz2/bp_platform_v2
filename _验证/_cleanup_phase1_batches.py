# -*- coding: utf-8 -*-
"""清理一期示范小区中早期失败的批次（保留最新一个已摇号完成的批次）。"""
import pymysql

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()

cur.execute("select id from bp_iam_org where org_name = '一期示范小区' limit 1")
row = cur.fetchone()
if not row:
    raise SystemExit('未找到一期示范小区')
org_id = row[0]

cur.execute("""select id, batch_name, batch_status from bp_biz_batch
               where org_id = %s order by create_time desc""", (org_id,))
batches = cur.fetchall()
print('该小区批次数：%d' % len(batches))
for b in batches:
    print('   %s  %s  %s' % (b[0], b[1], b[2]))

if len(batches) <= 1:
    print('无需清理')
    raise SystemExit(0)

keep = batches[0][0]
drop = [b[0] for b in batches[1:]]
ph = ','.join(['%s'] * len(drop))

cur.execute('select count(*) from bp_biz_lottery_result where batch_id in (%s)' % ph, drop)
print('将删除摇号结果 %d 条' % cur.fetchone()[0])
cur.execute('delete from bp_biz_lottery_result where batch_id in (%s)' % ph, drop)
cur.execute('delete from bp_biz_batch_house where batch_id in (%s)' % ph, drop)
n = cur.execute('delete from bp_biz_batch where id in (%s)' % ph, drop)
conn.commit()
print('保留批次 %s，已删除多余批次 %d 个' % (keep, n))

cur.execute("""select b.batch_name, b.batch_status,
                      (select count(*) from bp_biz_batch_house h where h.batch_id=b.id) as houses,
                      (select count(*) from bp_biz_lottery_result r where r.batch_id=b.id) as results
               from bp_biz_batch b where b.org_id=%s order by b.create_time desc""", (org_id,))
print('\n清理后：')
for r in cur.fetchall():
    print('   %-30s %-12s 房源 %s 结果 %s' % r)
conn.close()
