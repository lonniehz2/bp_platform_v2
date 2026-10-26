# -*- coding: utf-8 -*-
"""IoT 回调网关 / 指令模块：建表与补列（幂等执行）。"""
import pymysql

DDL_COMMAND = """
create table if not exists bp_dev_command (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  command_no varchar(64) not null,
  command_type varchar(32) not null comment 'LOCK_OPEN/DEVICE_REBOOT/DEVICE_SYNC_TIME/LOCK_MODE/ACCESS_OPEN/METER_SWITCH',
  device_id varchar(64) default null,
  lock_id varchar(64) default null,
  meter_no varchar(64) default null,
  request_id varchar(64) not null,
  params_json json default null,
  status varchar(16) not null default 'PENDING' comment 'PENDING/SENT/SUCCESS/FAILED/TIMEOUT/CANCELED',
  retry_count int not null default 0,
  max_retry int not null default 3,
  timeout_at datetime default null,
  dispatch_time datetime default null,
  ack_time datetime default null,
  result_code varchar(32) default null,
  result_msg varchar(500) default null,
  cost_ms int default null,
  operator_id bigint default null,
  operator_name varchar(64) default null,
  reason varchar(255) default null,
  source varchar(16) not null default 'CONSOLE' comment 'CONSOLE/API/SCHEDULE',
  approve_status varchar(16) default null comment '拉合闸审批：PENDING/APPROVED/REJECTED',
  approve_by bigint default null,
  approve_time datetime default null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_command_no (command_no),
  unique key uk_request_id (request_id),
  key idx_status_timeout (status, timeout_at),
  key idx_device_time (device_id, create_time),
  key idx_tenant_time (tenant_id, create_time)
) engine=InnoDB default charset=utf8mb4 comment='设备指令（开锁/重启/校时/拉合闸）'
"""

DDL_NONCE = """
create table if not exists bp_iot_nonce (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  app_id varchar(64) not null,
  nonce varchar(64) not null,
  expire_at datetime not null,
  create_time datetime not null default current_timestamp,
  unique key uk_app_nonce (app_id, nonce),
  key idx_expire (expire_at)
) engine=InnoDB default charset=utf8mb4 comment='IoT 回调 Nonce（防重放）'
"""


def columns(cur, table):
    cur.execute('show columns from %s' % table)
    return [r[0] for r in cur.fetchall()]


def indexes(cur, table):
    cur.execute('show index from %s' % table)
    return [r[2] for r in cur.fetchall()]


c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=180)
cur = c.cursor()
cur.execute(DDL_COMMAND)
cur.execute(DDL_NONCE)
print('表已就绪: bp_dev_command, bp_iot_nonce')

cols = columns(cur, 'bp_dev_callback_log')
if 'app_id' not in cols:
    cur.execute("alter table bp_dev_callback_log add column app_id varchar(64) null after tenant_id")
    print('callback_log 补 app_id')
if 'sign_ok' not in cols:
    cur.execute("alter table bp_dev_callback_log add column sign_ok tinyint not null default 0 after event_id")
    print('callback_log 补 sign_ok')
idx = indexes(cur, 'bp_dev_callback_log')
if 'uk_msg_event' not in idx:
    cur.execute("alter table bp_dev_callback_log add unique key uk_msg_event (tenant_id, msg_type, event_id)")
    print('callback_log 补唯一键 uk_msg_event')

cols = columns(cur, 'bp_dev_event')
if 'event_id' not in cols:
    cur.execute("alter table bp_dev_event add column event_id varchar(64) null after device_id")
    print('dev_event 补 event_id')
idx = indexes(cur, 'bp_dev_event')
if 'uk_event_id' not in idx:
    cur.execute("alter table bp_dev_event add unique key uk_event_id (tenant_id, event_id)")
    print('dev_event 补唯一键 uk_event_id')

# 权限码（页面 + 按钮）
perms = [
    ('page:dev-commands:view', '页面-设备指令', 'MENU', '/dev-commands', 63),
    ('dev:command:view', '查看设备指令', 'BUTTON', None, 63),
    ('dev:command:create', '创建设备指令（开锁/重启/校时）', 'BUTTON', None, 63),
    ('dev:command:retry', '重试/取消设备指令', 'BUTTON', None, 63),
]
cur.execute('select count(*) from bp_iam_permission')
for code, name, ptype, route, sort in perms:
    cur.execute('select id from bp_iam_permission where perm_code=%s', (code,))
    if cur.fetchone():
        continue
    cur.execute('''insert into bp_iam_permission
        (id, parent_id, perm_code, perm_name, perm_type, route_path, scenario, sort_no, status, create_time)
        values (%s, null, %s, %s, %s, %s, 'PLATFORM', %s, 'ENABLED', now())''',
                (str(822942014900000 + sort + len(code)), code, name, ptype, route, sort))
    print('新增权限:', code)

# 授予所有已有角色（避免非 admin 看不到菜单）
cur.execute('select id from bp_iam_role')
roles = [r[0] for r in cur.fetchall()]
for role_id in roles:
    for code, *_ in perms:
        cur.execute('select id from bp_iam_permission where perm_code=%s', (code,))
        pid = cur.fetchone()[0]
        cur.execute('select id from bp_iam_role_permission where role_id=%s and permission_id=%s',
                    (role_id, pid))
        if not cur.fetchone():
            cur.execute('insert into bp_iam_role_permission (id, role_id, permission_id) values (%s,%s,%s)',
                        (str(822942014910000 + role_id % 100000 + pid % 1000), role_id, pid))
print('权限授予角色数:', len(roles))

c.close()
print('DONE')
