# -*- coding: utf-8 -*-
"""开放平台 + 监管报送：权限种子与字典

用法：
    python _seed_open_gov.py            # 实际写入（需 DB 可达）
    python _seed_open_gov.py --dry-run  # 只打印计划，不连库

设计要点：
1. **幂等**：先按 perm_code 清理再插入，可反复执行。
2. **角色自省**：不硬编码角色 ID，改为从 bp_iam_role 查
   「管理员 / 只读」角色，避免不同环境 ID 不一致导致授权丢失。
3. **字典为系统内置**（tenant_id = NULL），租户可覆盖。
"""
import sys
import time

DRY = '--dry-run' in sys.argv

TENANT = '350600'
NOW = time.strftime('%Y-%m-%d %H:%M:%S')

# 主键基址（避免与既有手工数据撞号，保持本项目既有风格）
PERM_BASE = 800000000000000000
ROLE_PERM_BASE = 805000000000000000
DICT_BASE = 810000000000000000

# ==================== 1. 权限 ====================
# (perm_code, perm_name, sort_no)
PERMS = [
    ('open:app:manage', '开放应用管理', 401),
    ('open:app:list', '开放应用查询', 402),
    ('open:log:list', '开放调用日志查询', 403),
    ('open:webhook:manage', 'Webhook 订阅管理', 404),
    ('gov:adapter:manage', '政务适配器配置', 405),
    ('gov:report:submit', '发起监管报送', 406),
    ('gov:report:list', '监管报送查询', 407),
]

# 只读类权限（授予「只读/查询」角色）
READONLY_CODES = {'open:app:list', 'open:log:list', 'gov:report:list'}

# ==================== 2. 字典 ====================
# dict_type, [(code, label, sort)]
DICTS = {
    'OPEN_APP_TYPE': [
        ('THIRD_PARTY', '第三方应用', 1),
        ('INTERNAL', '内部应用', 2),
        ('GOV', '政务应用', 3),
    ],
    'OPEN_APP_STATUS': [
        ('ENABLED', '启用', 1),
        ('DISABLED', '停用', 2),
        ('EXPIRED', '已过期', 3),
    ],
    'OPEN_API_GROUP': [
        ('HOUSE', '房源', 1),
        ('PERSON', '人员', 2),
        ('CONTRACT', '合同', 3),
        ('ACCESS', '通行', 4),
        ('ALERT', '告警', 5),
        ('DEVICE', '设备', 6),
    ],
    'GOV_SYSTEM_TYPE': [
        ('PUBLIC_HOUSING', '公租房管理信息系统', 1),
        ('POLICE', '公安可信身份平台', 2),
        ('HOUSING', '住建部门', 3),
        ('REAL_ESTATE', '不动产登记系统', 4),
    ],
    'GOV_REPORT_TYPE': [
        ('HOUSE', '房源数据', 1),
        ('TENANT', '租户/人员数据', 2),
        ('STATUS', '房源状态', 3),
        ('CONTRACT', '合同数据', 4),
        ('FINANCE', '财务数据', 5),
        ('ACCESS', '通行数据', 6),
    ],
    'GOV_REPORT_MODE': [
        ('API', '接口直连', 1),
        ('FILE', '文件交换', 2),
        ('MANUAL', '人工报送', 3),
    ],
    'GOV_REPORT_CYCLE': [
        ('REALTIME', '实时', 1),
        ('DAILY', '每日', 2),
        ('MONTHLY', '每月', 3),
        ('QUARTERLY', '每季', 4),
        ('ONCE', '一次性', 5),
    ],
    'GOV_TASK_STATUS': [
        ('PENDING', '待报送', 1),
        ('RUNNING', '报送中', 2),
        ('SUCCESS', '成功', 3),
        ('PARTIAL', '部分成功', 4),
        ('FAILED', '失败', 5),
    ],
    'GOV_DEGRADE_MODE': [
        ('RETRY', '自动重试', 1),
        ('MANUAL', '转人工', 2),
        ('FILE', '转文件交换', 3),
        ('BLOCK', '阻断并告警', 4),
    ],
    'GOV_AUTH_TYPE': [
        ('NONE', '不鉴权', 1),
        ('APPKEY', 'AppKey', 2),
        ('TOKEN', 'Token', 3),
        ('BASIC', 'Basic', 4),
        ('CERT', '证书', 5),
        ('SIGN', '签名', 6),
    ],
}

# ==================== 3. 开放接口清单 ====================
# (api_code, api_name, api_path, method, group, need_auth, rate_limit, desc)
OPEN_APIS = [
    ('house.list', '查询房源列表', '/api/v1/houses', 'GET', 'HOUSE', 1, 20,
     '按组织/状态分页查询房源，仅返回本租户数据'),
    ('house.get', '查询房源详情', '/api/v1/houses/{id}', 'GET', 'HOUSE', 1, 20,
     '单套房源详情（含面积、状态、所属空间）'),
    ('person.get', '查询保障对象', '/api/v1/persons/{id}', 'GET', 'PERSON', 1, 20,
     '按 ID 查询保障对象（证件号已脱敏）'),
    ('contract.list', '查询合同列表', '/api/v1/contracts', 'GET', 'CONTRACT', 1, 20,
     '分页查询合同（可按状态、组织过滤）'),
    ('contract.get', '查询合同详情', '/api/v1/contracts/{id}', 'GET', 'CONTRACT', 1, 20,
     '单份合同详情'),
    ('access.record', '上报通行记录', '/api/v1/access-records', 'POST', 'ACCESS', 1, 50,
     '开门事件上报（按 eventId 幂等）'),
    ('alert.list', '查询告警列表', '/api/v1/alerts', 'GET', 'ALERT', 1, 20,
     '分页查询告警（可按级别/状态过滤）'),
    ('device.list', '查询设备列表', '/api/v1/devices', 'GET', 'DEVICE', 1, 20,
     '查询已绑定设备及其在线状态'),
]

API_BASE = 820000000000000000

if DRY:
    print('=' * 76)
    print(' DRY-RUN：以下为将执行的写入计划（不连库）')
    print('=' * 76)
    print()
    print('【1】权限 %d 条（perm_type=API）' % len(PERMS))
    for code, name, sort in PERMS:
        print('   %-24s %-18s sort=%d' % (code, name, sort))
    print()
    print('【2】授权给管理员角色：全部 %d 条' % len(PERMS))
    print('【3】授权给只读角色：%d 条（%s）'
          % (len(READONLY_CODES), ', '.join(sorted(READONLY_CODES))))
    print()
    total = sum(len(v) for v in DICTS.values())
    print('【4】字典 %d 类 / %d 项（tenant_id = NULL，系统内置）'
          % (len(DICTS), total))
    for t, items in DICTS.items():
        print('   %-20s %2d 项：%s'
              % (t, len(items), ', '.join(i[0] for i in items)))
    print()
    print('【5】开放接口清单 %d 个（bp_open_api）' % len(OPEN_APIS))
    for code, name, path, method, grp, _a, qps, _d in OPEN_APIS:
        print('   %-16s %-6s %-24s %-10s qps=%d  %s'
              % (code, method, path, grp, qps, name))
    print()
    print('计划完成。实际执行请去掉 --dry-run（需 DB 可达）。')
    sys.exit(0)

# ==================== 实际执行 ====================
try:
    import pymysql
except ImportError:
    print('缺少 pymysql，请先安装：pip install pymysql')
    sys.exit(1)

DB = dict(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
          database='bp_platform', charset='utf8mb4', connect_timeout=15)

print('=' * 76)
print(' 开放平台 + 监管报送 权限与字典种子')
print('=' * 76)

try:
    conn = pymysql.connect(**DB)
except Exception as e:
    print()
    print('❌ 无法连接数据库 %s:%s（%s）' % (DB['host'], DB['port'], type(e).__name__))
    print('   请回到内网后重新执行本脚本；或先 --dry-run 查看写入计划。')
    sys.exit(2)

cur = conn.cursor()
# 租户主表是 bp_iam_tenant 本身（无 tenant_id 列），按 tenant_code 校验
cur.execute("SELECT COUNT(*) FROM bp_iam_tenant WHERE tenant_code=%s", (TENANT,))
if cur.fetchone()[0] == 0:
    print('⚠️ 租户主表 bp_iam_tenant 无 %s 记录（本环境主表未用），'
          '继续写入权限/字典' % TENANT)

# ---- 角色自省 ----
cur.execute("SELECT id, role_code, role_name FROM bp_iam_role WHERE tenant_id=%s AND is_deleted=0", (TENANT,))
roles = cur.fetchall()
print()
print('发现角色 %d 个：' % len(roles))
admin_roles, readonly_roles = [], []
for rid, rcode, rname in roles:
    tag = ''
    blob = ('%s%s' % (rcode or '', rname or '')).upper()
    if 'ADMIN' in blob or '管理' in (rname or '') or '管理员' in (rname or ''):
        admin_roles.append(rid)
        tag = ' ← 管理员'
    elif 'VIEW' in blob or 'READ' in blob or '只读' in (rname or '') \
            or '查询' in (rname or ''):
        readonly_roles.append(rid)
        tag = ' ← 只读'
    print('   %s %-20s %-16s%s' % (rid, rcode or '-', rname or '-', tag))

if not admin_roles:
    print('⚠️ 未识别到管理员角色，将为全部角色授予全部权限（避免权限缺失）')
    admin_roles = [r[0] for r in roles]

# ---- 写权限 ----
cur.execute("DELETE FROM bp_iam_role_permission WHERE permission_id IN "
            "(SELECT id FROM bp_iam_permission WHERE perm_code IN %s)",
            (tuple(p[0] for p in PERMS),))
cur.execute("DELETE FROM bp_iam_permission WHERE perm_code IN %s",
            (tuple(p[0] for p in PERMS),))

perm_ids = {}
for i, (code, name, sort) in enumerate(PERMS):
    pid = PERM_BASE + i + 1
    perm_ids[code] = pid
    cur.execute("""INSERT INTO bp_iam_permission
        (id, parent_id, perm_code, perm_name, perm_type, sort_no, status, create_time)
        VALUES (%s,NULL,%s,%s,'API',%s,'ENABLED',%s)""",
                (pid, code, name, sort, NOW))
print()
print('✓ 写入权限 %d 条' % len(perm_ids))

# ---- 授权 ----
seq = 0
granted = 0
for rid in admin_roles:
    for code, _n, _s in PERMS:
        seq += 1
        cur.execute("""INSERT INTO bp_iam_role_permission
            (id, tenant_id, role_id, permission_id, create_time)
            VALUES (%s,%s,%s,%s,%s)""",
                    (ROLE_PERM_BASE + seq, TENANT, rid, perm_ids[code], NOW))
        granted += 1
for rid in readonly_roles:
    for code in sorted(READONLY_CODES):
        seq += 1
        cur.execute("""INSERT INTO bp_iam_role_permission
            (id, tenant_id, role_id, permission_id, create_time)
            VALUES (%s,%s,%s,%s,%s)""",
                    (ROLE_PERM_BASE + seq, TENANT, rid, perm_ids[code], NOW))
        granted += 1
print('✓ 写入角色授权 %d 条（管理员 %d 个、只读 %d 个）'
      % (granted, len(admin_roles), len(readonly_roles)))

# ---- 写字典 ----
cur.execute("DELETE FROM bp_sys_dict WHERE tenant_id IS NULL AND dict_type IN %s",
            (tuple(DICTS.keys()),))
n = 0
for dtype, items in DICTS.items():
    for code, label, sort in items:
        n += 1
        cur.execute("""INSERT INTO bp_sys_dict
            (id, tenant_id, dict_type, dict_code, dict_label, dict_value, sort_no,
             is_default, dict_status, is_deleted, create_time, update_time)
            VALUES (%s,NULL,%s,%s,%s,%s,%s,0,'ENABLED',0,%s,%s)""",
                    (DICT_BASE + n, dtype, code, label, code, sort, NOW, NOW))
print('✓ 写入字典 %d 类 / %d 项' % (len(DICTS), n))

# ---- 写开放接口清单 ----
cur.execute("DELETE FROM bp_open_api WHERE api_code IN %s",
            (tuple(a[0] for a in OPEN_APIS),))
m = 0
for code, name, path, method, grp, need_auth, qps, desc in OPEN_APIS:
    m += 1
    cur.execute("""INSERT INTO bp_open_api
        (id, api_code, api_name, api_path, http_method, api_group, need_auth,
         rate_limit, api_status, description, create_time)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'ENABLED',%s,%s)""",
                (API_BASE + m, code, name, path, method, grp, need_auth, qps, desc, NOW))
print('✓ 写入开放接口 %d 个' % m)

conn.commit()

# ---- 复核 ----
cur.execute("SELECT COUNT(*) FROM bp_iam_permission "
            "WHERE perm_code LIKE 'open:%' OR perm_code LIKE 'gov:%'")
c1 = cur.fetchone()[0]
cur.execute("""SELECT COUNT(*) FROM bp_iam_role_permission rp
               JOIN bp_iam_permission p ON p.id=rp.permission_id
               WHERE p.perm_code LIKE 'open:%' OR p.perm_code LIKE 'gov:%'""")
c2 = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT dict_type) FROM bp_sys_dict "
            "WHERE tenant_id IS NULL AND is_deleted=0")
c3 = cur.fetchone()[0]
print()
print('-' * 76)
print('复核：权限 %d 条，授权 %d 条，系统字典类型 %d 类' % (c1, c2, c3))
print('-' * 76)
conn.close()
