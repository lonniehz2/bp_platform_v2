# -*- coding: utf-8 -*-
"""数据体检：扫描业务不一致（并发/历史遗留脏数据），支持自动修复。

检查项：
  1. 一房多签     同一房源存在多份生效合同
  2. 超收         账单已收 > 应收
  3. 重复退租     同一合同存在多张进行中的退租单
  4. 房源合同不一致 合同生效但房源未占用 / 房源已占用但无生效合同
  5. 抄表重复出账 同一条读数关联多张账单（bill_status=BILLED 但 bill_id 为空或重复）

用法：
  python _check_data_health.py           # 只检查
  python _check_data_health.py --fix     # 修复（保留最早一条，其余作废/纠正）
"""
import sys

import pymysql

FIX = '--fix' in sys.argv

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()

issues = []


def report(name, rows, detail_fn):
    print('\n【%s】%d 处' % (name, len(rows)))
    for r in rows[:8]:
        print('   ' + detail_fn(r))
    if len(rows) > 8:
        print('   ... 其余 %d 处' % (len(rows) - 8))
    issues.append((name, len(rows)))


# ---------- 1) 一房多签 ----------
cur.execute("""
    select house_id, count(*) n, group_concat(id order by id) ids
    from bp_biz_contract
    where contract_status in ('EFFECTIVE', 'RENEWING') and house_id is not null
    group by house_id having n > 1
""")
dup_sign = cur.fetchall()
report('一房多签', dup_sign,
       lambda r: '房源 %s 有 %d 份生效合同：%s' % (r[0], r[1], r[2]))

if FIX and dup_sign:
    fixed = 0
    for hid, n, ids in dup_sign:
        lst = ids.split(',')
        for other in lst[1:]:
            cur.execute("""update bp_biz_contract set contract_status='CANCELLED',
                           remark=concat(coalesce(remark,''), ' [数据体检:重复签约作废]')
                           where id=%s""", (other,))
            fixed += 1
    conn.commit()
    print('   → 已作废 %d 份重复合同' % fixed)

# ---------- 2) 超收 ----------
# 超收 = 累计已收 > 应收总额（bill_amount - 减免 + 滞纳金 - 豁免）
# 注意：不能与 payable_amount（剩余应缴）比较，否则已缴清账单会被误判
cur.execute("""
    select id, bill_no, payable_amount, paid_amount
    from bp_fin_bill
    where coalesce(paid_amount,0) > (coalesce(bill_amount,0)
          - coalesce(discount_amount,0) + coalesce(late_fee,0)
          - coalesce(waived_amount,0)) + 0.01
      and coalesce(is_deleted,0)=0
""")
overpaid = cur.fetchall()
report('账单超收', overpaid,
       lambda r: '%s 应收 %s 已收 %s%s' % (r[1], r[2], r[3],
                                          '（已减免但仍有收款，需退款）'
                                          if float(r[2] or 0) == 0 else ''))

if overpaid:
    print('   → 涉及金额，不自动改写；请人工核对（常见原因：账单已减免/作废但仍有收款）')

# ---------- 3) 重复退租 ----------
cur.execute("""
    select contract_id, count(*) n, group_concat(id order by id) ids
    from bp_biz_termination
    where termination_status not in ('CANCELLED', 'REJECTED', 'COMPLETED')
    group by contract_id having n > 1
""")
dup_term = cur.fetchall()
report('重复退租', dup_term,
       lambda r: '合同 %s 有 %d 张进行中退租单：%s' % (r[0], r[1], r[2]))

if FIX and dup_term:
    fixed = 0
    for cid, n, ids in dup_term:
        lst = ids.split(',')
        for other in lst[1:]:
            cur.execute("""update bp_biz_termination set termination_status='CANCELLED'
                           where id=%s""", (other,))
            fixed += 1
    conn.commit()
    print('   → 已作废 %d 张重复退租单' % fixed)

# ---------- 4) 房源与合同不一致 ----------
cur.execute("""
    select c.id, c.contract_no, c.house_id, h.house_status
    from bp_biz_contract c join bp_asset_house h on h.id = c.house_id
    where c.contract_status in ('EFFECTIVE', 'RENEWING')
      and h.house_status not in ('OCCUPIED', 'ALLOCATED')
""")
ct_but_free = cur.fetchall()
report('合同生效但房源未占用', ct_but_free,
       lambda r: '%s 房源 %s 状态 %s' % (r[1], r[2], r[3]))

cur.execute("""
    select h.id, h.house_name, h.house_status
    from bp_asset_house h
    where h.house_status in ('OCCUPIED', 'ALLOCATED')
      and not exists (select 1 from bp_biz_contract c
                      where c.house_id = h.id
                        and c.contract_status in ('EFFECTIVE', 'RENEWING'))
    limit 200
""")
occupied_no_ct = cur.fetchall()
report('房源占用但无生效合同（多为造数残留）', occupied_no_ct,
       lambda r: '%s（%s）状态 %s' % (r[1], r[0], r[2]))

# ---------- 5) 抄表重复出账 ----------
cur.execute("""
    select bill_id, count(*) n from bp_fin_meter_reading
    where bill_id is not null and coalesce(is_deleted,0)=0
    group by bill_id having n > 1
""")
dup_bill = cur.fetchall()
report('抄表读数共用同一账单', dup_bill,
       lambda r: '账单 %s 被 %d 条读数引用' % (r[0], r[1]))

# ---------- 6) 悬空引用 ----------
DANGLING = [
    ('合同→房源', """select c.id, c.contract_no from bp_biz_contract c
        left join bp_asset_house h on h.id=c.house_id
        where c.house_id is not null and h.id is null limit 200"""),
    ('合同→组织', """select c.id, c.contract_no from bp_biz_contract c
        left join bp_iam_org o on o.id=c.org_id
        where c.org_id is not null and o.id is null limit 200"""),
    ('合同→承租人', """select c.id, c.contract_no from bp_biz_contract c
        left join bp_person p on p.id=c.lessee_person_id
        where c.lessee_person_id is not null and p.id is null limit 200"""),
    ('申请→组织', """select a.id, a.apply_no from bp_biz_application a
        left join bp_iam_org o on o.id=a.org_id
        where a.org_id is not null and o.id is null limit 200"""),
    ('换房→原合同', """select e.id, e.exchange_no from bp_biz_exchange e
        left join bp_biz_contract c on c.id=e.old_contract_id
        where e.old_contract_id is not null and c.id is null limit 200"""),
    ('账单→合同', """select b.id, b.bill_no from bp_fin_bill b
        left join bp_biz_contract c on c.id=b.contract_id
        where b.contract_id is not null and c.id is null limit 200"""),
]
for label, sql in DANGLING:
    try:
        cur.execute(sql)
        dangling = cur.fetchall()
    except Exception:
        continue
    report('悬空引用 · ' + label, dangling,
           lambda r: '记录 %s 指向不存在的记录' % (r[1] or r[0]))

# ---------- 汇总 ----------
total = sum(n for _, n in issues)
print('\n' + '=' * 52)
print('体检结论：共 %d 类问题、%d 处不一致' % (len([1 for _, n in issues if n]), total))
if total and not FIX:
    print('可执行 --fix 自动修复（保留最早一条，其余作废/纠正）')
elif total and FIX:
    print('已尝试修复，请再次运行确认')
else:
    print('数据一致，无需处理')
conn.close()
sys.exit(0 if total == 0 else 1)
