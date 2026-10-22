# -*- coding: utf-8 -*-
"""清理历史重复退租单（同合同多张 APPLYING，保留最早一张）。"""
import pymysql

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()
cur.execute("""select contract_id, group_concat(id order by id) ids
               from bp_biz_termination
               where termination_status = 'APPLYING'
               group by contract_id having count(*) > 1""")
rows = cur.fetchall()
n = 0
for cid, ids in rows:
    lst = ids.split(',')
    for other in lst[1:]:
        cur.execute("update bp_biz_termination set termination_status='CANCELLED', "
                    "remark=concat(coalesce(remark,''),' [并发测试清理]') where id=%s",
                    (other,))
        n += 1
conn.commit()
conn.close()
print('合同数 %d，已作废重复退租单 %d 张' % (len(rows), n))
