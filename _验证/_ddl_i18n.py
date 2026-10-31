# -*- coding: utf-8 -*-
"""多语言基础表结构（幂等）。"""
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()


def has_column(table, column):
    cur.execute('show columns from %s like %%s' % table, (column,))
    return cur.fetchone() is not None


if not has_column('bp_iam_user', 'locale'):
    cur.execute("alter table bp_iam_user add locale varchar(16) null comment '界面语言'")
if not has_column('bp_iam_tenant', 'default_locale'):
    cur.execute("alter table bp_iam_tenant add default_locale varchar(16) default 'zh-CN' "
                "comment '平台默认语言'")

cur.execute('''create table if not exists sys_i18n_text (
 id bigint not null primary key,
 tenant_id varchar(32) not null,
 resource_type varchar(64) not null,
 resource_id bigint not null,
 field varchar(64) not null,
 locale varchar(16) not null,
 text longtext not null,
 status varchar(16) not null default 'DRAFT',
 updated_by bigint null,
 updated_at datetime(3) null,
 unique key uk_i18n_text (tenant_id, resource_type, resource_id, field, locale),
 key idx_i18n_lookup (resource_type, resource_id, locale)
) comment '业务主数据翻译表' ''')

print('i18n ddl ok')
c.close()
