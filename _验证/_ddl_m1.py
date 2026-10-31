# -*- coding: utf-8 -*-
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=120)
cur = c.cursor()


def add(table, col, ddl):
    cur.execute('show columns from %s like %%s' % table, (col,))
    if not cur.fetchone():
        cur.execute('alter table %s add column %s %s' % (table, col, ddl))
        print('added', table, col)


add('bp_biz_contract', 'billing_person_count', 'int null')
add('bp_biz_contract', 'billing_bed_count', 'int null')
add('bp_biz_contract', 'quantity_updated_at', 'datetime(3) null')

add('bp_fin_bill', 'rule_id', 'bigint null')
add('bp_fin_bill', 'rule_version', 'int null')
add('bp_fin_bill', 'rule_snapshot', 'json null')
add('bp_fin_bill', 'billing_quantity', 'int null')
add('bp_fin_bill', 'quantity_unit', 'varchar(20) null')
add('bp_fin_bill', 'quantity_source', 'varchar(40) null')

c.close()
