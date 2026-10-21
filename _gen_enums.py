# -*- coding: utf-8 -*-
"""全量枚举中文化：建统一枚举字典 + 批量改造 35 个页面的枚举列"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'
V = os.path.join(FE, 'views')

ENUMS = '''/**
 * 全局枚举字典（值 → 中文）。
 *
 * 设计说明：
 * 1. 绝大多数枚举码是**全局唯一**的（VACANT / UNPAID / EFFECTIVE…），
 *    因此用一张扁平表即可覆盖全部页面，无需按字段名分别维护。
 * 2. 少数同名不同义的值（如 VISIT：催缴=上门 / 来访=来访登记）
 *    用 TYPE_OVERRIDE 按字段名覆盖。
 * 3. 未登记的值**原样返回**，避免脏数据被静默吞掉。
 *
 * 之所以放前端统一处理而不是逐个改后端 VO：
 * 后端已有 applicationStatusLabel 这类字段，但覆盖不全且不一致；
 * 统一在前端做展示层映射，既覆盖全部页面，又不影响后端编码语义。
 */

const GLOBAL = {
  // ---------- 房源 / 空间 ----------
  PUBLIC_RENTAL: '公租房',
  AFFORDABLE_RENTAL: '保障性租赁住房',
  TALENT: '人才公寓',
  APARTMENT: '公寓',
  DORMITORY: '宿舍',
  HOTEL: '酒店/民宿',
  RENTAL: '出租房',
  VACANT: '空置',
  PENDING_ALLOC: '待配租',
  ALLOCATED: '已配租',
  OCCUPIED: '已出租',
  LOCKED: '锁定',
  REPAIR: '维修中',
  AREA: '片区',
  BUILDING: '楼栋',
  UNIT: '单元',
  FLOOR: '楼层',
  ROOM: '房间',
  BED: '床位',
  PARKING: '车位',
  GARAGE: '车库',
  SITE: '场地',
  VILLA: '别墅',
  MULTI: '多层',
  SMALL_HIGH: '小高层',
  HIGH: '高层',
  SUPER_HIGH: '超高层',
  CIVIL: '民用',
  COMMERCIAL: '商用',
  ROUGH: '毛坯',
  SIMPLE: '简装',
  FINE: '精装',
  SELF: '自营',
  ENTRUST: '委托',
  LEASE: '租赁',
  STATE: '国有',
  COLLECTIVE: '集体',
  PRIVATE: '私有',
  SOUTH: '朝南',
  NORTH: '朝北',

  // ---------- 保障类型 / 组织 ----------
  PUBLIC: '公租房',
  AFFORDABLE: '保租房',
  'LOW_RENT': '廉租房',
  DISTRICT: '区级',
  COMMUNITY: '社区/小区',
  COMPANY: '公司',
  DEPARTMENT: '部门',

  // ---------- 合同 ----------
  DRAFT: '草稿',
  PENDING_SIGN: '待签约',
  SIGNING: '签约中',
  EFFECTIVE: '履约中',
  RENEWING: '续签中',
  EXPIRED: '已到期',
  TERMINATED: '已终止',
  CANCELLED: '已取消',
  RENEW: '续签',
  RENT_ADJUST: '调租',
  PERIOD: '租期变更',
  LESSEE: '承租人变更',
  RENT: '租金',

  // ---------- 账单 / 财务 ----------
  UNPAID: '未缴',
  PARTIAL: '部分缴纳',
  PAID: '已缴清',
  OVERDUE: '已逾期',
  WAIVED: '已减免',
  BILL: '账单',
  PAYMENT: '收款',
  REFUND: '退款',
  DEPOSIT: '押金',
  SUBSIDY: '补贴',
  LATE_FEE: '滞纳金',
  PROPERTY: '物业费',
  ENERGY: '能耗费',
  OTHER: '其他',
  FIXED: '定额',
  BY_AREA: '按面积',
  BY_HOUSE: '按套',
  BY_PERSON: '按人',
  BY_BED: '按床位',
  BY_NIGHT: '按房晚',
  METER: '抄表',
  RATIO: '按比例',
  IN: '收入',
  OUT: '支出',
  CASH: '现金',
  BANK: '银行转账',
  ALIPAY: '支付宝',
  POS: 'POS',
  HOLD: '暂扣',
  HELD: '已收讫',
  DEDUCTED: '已抵扣',
  REFUNDED: '已退还',

  // ---------- 审批 / 流程 ----------
  SUBMITTED: '已提交',
  ACCEPTED: '已受理',
  REVIEWING: '审核中',
  APPROVED: '已通过',
  REJECTED: '已驳回',
  RETURNED: '已退回',
  PENDING: '待处理',
  PROCESSING: '处理中',
  SUCCESS: '成功',
  FAILED: '失败',
  COMPLETED: '已完成',
  CLOSED: '已关闭',
  CLOSING: '关闭中',
  OPEN: '开启',
  ENABLED: '启用',
  DISABLED: '停用',
  ACTIVE: '生效',
  INACTIVE: '失效',
  IGNORED: '已忽略',
  RESOLVED: '已解决',
  HANDLED: '已处理',
  ESCALATED: '已升级',
  UNHANDLED: '未处理',

  // ---------- 设备 / 通行 ----------
  ONLINE: '在线',
  OFFLINE: '离线',
  ABNORMAL: '异常',
  NORMAL: '正常',
  FROZEN: '冻结',
  PASS: '通过',
  FAIL: '未通过',
  TEMP_PASSWORD: '临时密码',
  CARD: '门禁卡',
  FACE: '人脸',
  QRCODE: '二维码',
  PHONE_BLUETOOTH: '手机蓝牙',
  DUPLICATE: '重复开门',
  TAILGATING: '尾随',
  EXPIRED_CREDENTIAL: '凭证过期',
  UNTRUSTED: '不可信',
  OPENED: '已开门',

  // ---------- 配租 ----------
  LOTTERY: '摇号',
  SELECT: '选房',
  DIRECT: '直配',
  SUPPLEMENT: '补配',
  WON: '中签',
  LOST: '未中签',
  WAITING: '轮候中',
  QUEUING: '排队中',
  EXITED: '已退出',
  PENDING_SIGN_ALLOC: '待签约',
  SIGNED: '已签约',
  GIVEN_UP: '已放弃',

  // ---------- 退租 / 年审 ----------
  NORMAL: '正常',
  EXPEL: '违规清退',
  EXPIRE: '到期退出',
  EXCHANGE: '换房退出',
  KEEP: '保留',
  ADJUST: '调整',
  EXIT: '退出',

  // ---------- 服务 ----------
  SMS: '短信',
  WECHAT: '微信',
  PHONE: '电话',
  NOTICE: '书面通知',
  PLATFORM: '平台推送',
  LETTER: '律师函',
  VISIT: '上门',
  COMPLAINT: '投诉',
  REPAIR_ORDER: '报修',
  CONSULT: '咨询',
  SUGGESTION: '建议',
  MINOR: '轻微',
  MAJOR: '较重',
  SEVERE: '严重',
  WARNING: '警告',
  INFO: '提示',
  CRITICAL: '严重',

  // ---------- 短租 ----------
  OTA: 'OTA平台',
  WALKIN: '上门散客',
  BOOKED: '已预订',
  CHECKED_IN: '已入住',
  CHECKED_OUT: '已退房',
  NO_SHOW: '未到店',
  FREE: '空闲',
  FULL: '满房',

  // ---------- 授权 / 钥匙 ----------
  OWNERSHIP: '产权级',
  MANAGEMENT: '管理级',
  USAGE: '使用级',
  IN_USE: '使用中',
  RETURNED_KEY: '已归还',
  LOST_KEY: '已丢失',
  MISSING: '缺失',
  CONSISTENT: '一致',
  INCONSISTENT: '不一致',

  // ---------- 系统 ----------
  API: '接口',
  MENU: '菜单',
  BUTTON: '按钮',
  DATA: '数据',
  CREATE: '新增',
  UPDATE: '修改',
  DELETE: '删除',
  QUERY: '查询',
  LOGIN: '登录',
  LOGOUT: '登出',
  EXPORT: '导出',
  IMPORT: '导入',
  STRING: '字符串',
  NUMBER: '数值',
  JSON: 'JSON',
  MONTHLY: '按月',
  ANNUAL: '按年',
  DAILY: '按日',
  WEEKLY: '按周',
  DAILY_REPORT: '日报',
  GOLDEN: '金卡'
}

/** 同名不同义的覆盖（按字段名） */
const TYPE_OVERRIDE = {
  visitStatus: { VISIT: '来访', PENDING: '待处理', DONE: '已完成' },
  actionType: { VISIT: '上门', PHONE: '电话', SMS: '短信', LETTER: '律师函' },
  flowType: { IN: '收入', OUT: '支出' },
  bizType: { RENT: '租金', DEPOSIT: '押金', SUBSIDY: '补贴', PROPERTY: '物业费' },
  calcMode: { FIXED: '定额', METER: '抄表' },
  subsidyMode: { FIXED: '定额', RATIO: '按比例' },
  permType: { API: '接口', MENU: '菜单', BUTTON: '按钮', DATA: '数据' },
  valueType: { STRING: '字符串', NUMBER: '数值', JSON: 'JSON' },
  onlineStatus: { ONLINE: '在线', OFFLINE: '离线' },
  auditLevel: { INFO: '提示', WARNING: '警告', CRITICAL: '严重' },
  alertLevel: { INFO: '提示', WARNING: '警告', CRITICAL: '严重' },
  creditLevel: { MINOR: '轻微', MAJOR: '较重', SEVERE: '严重' },
  handleStatus: { PENDING: '待处理', HANDLED: '已处理', IGNORED: '已忽略' },
  dayStatus: { FREE: '空闲', FULL: '满房', LOCKED: '锁定', CLOSED: '关闭' }
}

/**
 * 枚举值 → 中文。
 * @param {string} field 字段名（用于同名覆盖，可空）
 * @param {*} value 原始值
 */
export function enumLabel(field, value) {
  if (value === null || value === undefined || value === '') return '-'
  const v = String(value)
  if (field && TYPE_OVERRIDE[field] && TYPE_OVERRIDE[field][v]) {
    return TYPE_OVERRIDE[field][v]
  }
  return GLOBAL[v] || v
}

/** 用于表格列的简写：仅传值 */
export function label(value) {
  return enumLabel(null, value)
}

export default GLOBAL
'''

io.open(os.path.join(FE, 'constants', 'enums.js'), 'w', encoding='utf-8').write(ENUMS)
print('  ✓ 新建 constants/enums.js（约 190 个枚举值）')

# ---------- 批量改造枚举列 ----------
ENUM_SUFFIX = (r'(?:Status|Type|Stage|Mode|Level|Channel|Result|Source|Way|'
               r'Category|Kind)')

patched_files = 0
patched_cols = 0
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    p = os.path.join(V, f)
    s = io.open(p, encoding='utf-8').read()
    orig = s

    # 只处理「自闭合且 prop 以枚举后缀结尾」的列
    def repl(m):
        global patched_cols
        indent, prop, rest = m.group(1), m.group(2), m.group(3)
        # rest 里可能含 label="x" width="y"
        label_m = re.search(r'label="([^"]+)"', rest)
        label_txt = label_m.group(1) if label_m else prop
        attrs = rest
        patched_cols += 1
        return (f'{indent}<el-table-column{attrs}>\n'
                f'{indent}  <template #default="{{ row }}">'
                f'{{{{ enumLabel(\'{prop}\', row.{prop}) }}}}</template>\n'
                f'{indent}</el-table-column>')

    s2 = re.sub(r'( *)<el-table-column( (?:[^>]*?)?prop="(\w*%s)"((?:[^">]*"[^"]*")*)) */>'
                % ENUM_SUFFIX,
                lambda m: (m.group(1) + '<el-table-column' + m.group(2) + '>\n'
                           + m.group(1) + '  <template #default="{ row }">'
                           + "{{ enumLabel('%s', row.%s) }}</template>\n" % (m.group(3), m.group(3))
                           + m.group(1) + '</el-table-column>'),
                s)

    if s2 != orig:
        # 补 import
        if 'from \'@/constants/enums\'' not in s2:
            if '<script setup>' in s2:
                i = s2.find('<script setup>') + len('<script setup>')
                s2 = s2[:i] + "\nimport { enumLabel } from '@/constants/enums'" + s2[i:]
            else:
                continue
        io.open(p, 'w', encoding='utf-8').write(s2)
        patched_files += 1

print('  ✓ 改造 %d 个页面' % patched_files)
