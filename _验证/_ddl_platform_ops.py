# -*- coding: utf-8 -*-
"""平台运营台 DDL 与初始超管。"""
import base64
import hashlib
import os
import pymysql

PWD = 'Ops@123456'
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', PWD.encode(), salt, 120000, dklen=32)
HASH = 'pbkdf2$120000$%s$%s' % (base64.b64encode(salt).decode(),
                                base64.b64encode(dk).decode())

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=120)
cur = c.cursor()

cur.execute('''create table if not exists bp_iam_platform_operator (
  id bigint unsigned not null primary key,
  username varchar(64) not null,
  password_hash varchar(255) not null,
  real_name varchar(64),
  status varchar(20) not null default 'ENABLED',
  must_change_password tinyint not null default 1,
  fail_count int not null default 0,
  locked_until datetime(3) null,
  last_login_time datetime(3) null,
  is_deleted tinyint not null default 0,
  create_time datetime(3) not null,
  update_time datetime(3) not null,
  unique key uk_operator_username (username)
) engine=InnoDB default charset=utf8mb4 comment='平台运营超管' ''')

cur.execute('''create table if not exists bp_iam_platform_operator_session (
  id bigint unsigned not null primary key,
  operator_id bigint unsigned not null,
  token varchar(128) not null,
  status varchar(20) not null default 'ACTIVE',
  expire_time datetime(3) not null,
  create_time datetime(3) not null,
  unique key uk_operator_token (token),
  key idx_op_session_operator (operator_id)
) engine=InnoDB default charset=utf8mb4 comment='平台运营超管会话' ''')

cur.execute('''create table if not exists bp_iam_platform_audit (
  id bigint unsigned not null primary key,
  operator_id bigint unsigned,
  operator_name varchar(64),
  platform_code varchar(40),
  action varchar(60),
  detail varchar(1000),
  ip varchar(64),
  create_time datetime(3) not null,
  key idx_platform_audit_time (create_time)
) engine=InnoDB default charset=utf8mb4 comment='平台运营审计' ''')

cur.execute('''create table if not exists bp_iam_tenant_branding (
  tenant_id varchar(32) not null primary key,
  logo_url varchar(512),
  primary_color varchar(20),
  accent_color varchar(20),
  login_title varchar(120),
  login_subtitle varchar(200),
  menu_style varchar(20) default 'rail',
  color_mode varchar(20) default 'light',
  allow_user_switch tinyint not null default 1,
  update_time datetime(3)
) engine=InnoDB default charset=utf8mb4 comment='平台品牌与主题' ''')

cur.execute('''create table if not exists bp_sys_platform_seq (
  region_code varchar(20) not null primary key,
  seq int not null default 0
) engine=InnoDB default charset=utf8mb4 comment='平台编码序列' ''')

def add_col(table, col, ddl):
    cur.execute("show columns from %s like %%s" % table, (col,))
    if not cur.fetchone():
        cur.execute("alter table %s add column %s %s" % (table, col, ddl))
        print('added', table, col)

add_col('bp_iam_user', 'must_change_password', 'tinyint not null default 0')
add_col('bp_iam_user', 'fail_count', 'int not null default 0')
add_col('bp_iam_user', 'locked_until', 'datetime(3) null')
add_col('bp_iam_tenant', 'contact_name', 'varchar(64) null')
add_col('bp_iam_tenant', 'contact_phone', 'varchar(32) null')
add_col('bp_iam_tenant', 'business_type_code', "varchar(40) not null default 'BAOZHANG'")
add_col('bp_iam_tenant', 'deleted', 'tinyint not null default 0')
add_col('bp_iam_tenant', 'archive_time', 'datetime(3) null')

cur.execute("select id from bp_iam_platform_operator where username='opsadmin'")
if not cur.fetchone():
    cur.execute('''insert into bp_iam_platform_operator
        (id, username, password_hash, real_name, status, must_change_password,
         fail_count, is_deleted, create_time, update_time)
        values (%s,'opsadmin',%s,'平台运营管理员','ENABLED',1,0,0,now(3),now(3))''',
                (790000000000010001, HASH))
    print('operator created: opsadmin /', PWD)
else:
    print('operator exists')

c.close()
