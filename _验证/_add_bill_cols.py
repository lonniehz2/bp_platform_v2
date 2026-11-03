import pymysql
c=pymysql.connect(host='192.168.31.153',port=33306,user='root',password='5677@Mysql',database='bp_platform',charset='utf8mb4')
cur=c.cursor()
cur.execute("show columns from bp_fin_bill")
have={r[0] for r in cur.fetchall()}
cols={
 'settlement_date':'date null after period_end',
 'unit_price_snapshot':'decimal(14,4) null after bill_amount',
 'price_source':'varchar(20) null after unit_price_snapshot',
 'bill_date':'date null after due_date',
 'billing_days':'int null after billing_quantity',
 'proration_months':'decimal(10,6) null after billing_days',
}
for name,ddl in cols.items():
 if name not in have:
  cur.execute(f'alter table bp_fin_bill add column {name} {ddl}')
  print('added',name)
else:
 pass
c.commit(); c.close()
