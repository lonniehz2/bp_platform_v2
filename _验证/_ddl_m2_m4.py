# -*- coding: utf-8 -*-
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=120)
cur = c.cursor()

cur.execute('''create table if not exists bp_fin_meter_point (
  id bigint primary key,
  tenant_id varchar(32) not null,
  space_id bigint null,
  fee_item_id bigint not null,
  meter_scope varchar(20) not null default 'ROOM',
  allocation_basis varchar(20) not null default 'PERSON_DAYS',
  meter_name varchar(100),
  status varchar(20) not null default 'ENABLED',
  create_time datetime(3),
  update_time datetime(3),
  key idx_meter_space (space_id),
  key idx_meter_item (fee_item_id)
) engine=InnoDB default charset=utf8mb4 comment='表计点位' ''')

cur.execute('''create table if not exists bp_fin_meter_point_reading (
  id bigint primary key,
  tenant_id varchar(32) not null,
  meter_point_id bigint not null,
  reading decimal(18,4) not null,
  read_time datetime(3) not null,
  source varchar(20) not null,
  operator_id bigint,
  photo_url varchar(512),
  remark varchar(500),
  create_time datetime(3),
  key idx_mpr_point (meter_point_id, read_time)
) engine=InnoDB default charset=utf8mb4 comment='表计读数（房间表/总表）' ''')

cur.execute('''create table if not exists bp_fin_utility_allocation (
  id bigint primary key,
  tenant_id varchar(32) not null,
  meter_point_id bigint not null,
  period varchar(7) not null,
  start_reading decimal(18,4),
  end_reading decimal(18,4),
  total_usage decimal(18,4),
  total_amount decimal(18,2),
  operator_bear_amount decimal(18,2) default 0,
  tier_detail json,
  status varchar(20) not null default 'CONFIRMED',
  create_time datetime(3),
  unique key uk_alloc (meter_point_id, period)
) engine=InnoDB default charset=utf8mb4 comment='能耗月度分摊主单' ''')

cur.execute('''create table if not exists bp_fin_utility_share (
  id bigint primary key,
  tenant_id varchar(32) not null,
  allocation_id bigint not null,
  contract_id bigint not null,
  person_id bigint,
  occupy_days int,
  person_days decimal(18,2),
  share_ratio decimal(12,8),
  share_amount decimal(18,2),
  rounding_delta decimal(18,2) default 0,
  bill_id bigint,
  key idx_share_alloc (allocation_id)
) engine=InnoDB default charset=utf8mb4 comment='能耗分摊明细' ''')

cur.execute('''create table if not exists bp_fin_energy_policy (
  id bigint primary key,
  tenant_id varchar(32) not null,
  org_id bigint null,
  vacancy_bearer varchar(20) not null default 'OPERATOR',
  warn_rate decimal(8,4) not null default 0.0500,
  alarm_rate decimal(8,4) not null default 0.1000,
  status varchar(20) not null default 'ENABLED',
  create_time datetime(3),
  update_time datetime(3),
  unique key uk_policy_org (tenant_id, org_id)
) engine=InnoDB default charset=utf8mb4 comment='能耗策略' ''')

cur.execute('''create table if not exists bp_fin_energy_monthly_stat (
  id bigint primary key,
  tenant_id varchar(32) not null,
  period varchar(7) not null,
  space_id bigint null,
  total_usage decimal(18,4) default 0,
  submeter_usage decimal(18,4) default 0,
  diff_usage decimal(18,4) default 0,
  diff_rate decimal(8,4) default 0,
  alert_level varchar(20) default 'NORMAL',
  create_time datetime(3),
  unique key uk_energy_stat (tenant_id, period, space_id)
) engine=InnoDB default charset=utf8mb4 comment='总表/分表月度对比' ''')

cur.execute('''create table if not exists bp_fin_late_fee_policy (
  id bigint primary key,
  tenant_id varchar(32) not null,
  org_id bigint null,
  daily_rate decimal(8,6) not null default 0.000500,
  grace_days int not null default 5,
  cap_rate decimal(5,4) not null default 0.2000,
  status varchar(20) not null default 'ENABLED',
  create_time datetime(3),
  update_time datetime(3),
  unique key uk_late_policy (tenant_id, org_id)
) engine=InnoDB default charset=utf8mb4 comment='滞纳金策略' ''')

cur.execute('''create table if not exists bp_fin_deposit_transfer (
  id bigint primary key,
  tenant_id varchar(32) not null,
  exchange_id bigint,
  old_contract_id bigint,
  new_contract_id bigint,
  old_deposit_id bigint,
  new_deposit_id bigint,
  transfer_amount decimal(18,2),
  operator_id bigint,
  create_time datetime(3)
) engine=InnoDB default charset=utf8mb4 comment='押金转移记录' ''')


def add(table, col, ddl):
    cur.execute('show columns from %s like %%s' % table, (col,))
    if not cur.fetchone():
        cur.execute('alter table %s add column %s %s' % (table, col, ddl))
        print('added', table, col)


add('bp_fin_bill', 'tier_detail', 'json null')
add('bp_fin_bill', 'late_fee_days', 'int null')
add('bp_fin_bill', 'late_fee_detail', 'json null')
add('bp_fin_deposit', 'source_type', "varchar(20) default 'NEW'")
add('bp_fin_deposit', 'source_contract_id', 'bigint null')
print('M2-M4 schema ready')
c.close()
