/**
 * 菜单信息架构：9 分组 + 组内分区 + 排序 + 角标 + 说明。
 *
 * 设计目标（A+ 方案）：
 *  1. 组内按「使用频率」排序，配置类置末
 *  2. 大组加分区标题（收费作业 / 资金管理 / 基础配置…），避免一长串
 *  3. 每个菜单项一句说明（hover 显示），降低学习成本
 *  4. 角标数字对应「有没有活要干」，来自 /menu/badges
 */
export const GROUP_ORDER = [
  '工作台', '保障与资格', '合同与租赁', '收费与账务', '计量与能耗',
  '房源与空间', '设备与通行', '服务与监督', '系统与数据'
]

export const GROUP_ICON = {
  工作台: 'HomeFilled',
  保障与资格: 'UserFilled',
  合同与租赁: 'Document',
  收费与账务: 'Money',
  计量与能耗: 'Odometer',
  房源与空间: 'OfficeBuilding',
  设备与通行: 'Cpu',
  服务与监督: 'Service',
  系统与数据: 'Setting'
}

/** 旧分组名 → 新分组名（兼容历史 meta 与用户本地缓存） */
export const GROUP_ALIAS = {
  运营总览: '工作台',
  仪表盘: '工作台',
  管理后台: '系统与数据',
  系统与集成: '系统与数据',
  保障对象: '保障与资格',
  资格准入: '保障与资格',
  会员: '保障与资格',
  线索: '保障与资格',
  合同管理: '合同与租赁',
  合同: '合同与租赁',
  账务收费: '收费与账务',
  财务: '收费与账务',
  资产与设备: '房源与空间',
  房源: '房源与空间',
  授权与交房: '设备与通行',
  资产台账: '房源与空间',
  服务与监督: '服务与监督',
  更多: '服务与监督',
  退出与监督: '服务与监督'
}

/** 组内分区：3 项以上的大组分段展示（顺序即展示顺序） */
export const SUBGROUPS = {
  收费与账务: [
    { title: '收费作业', paths: ['/bills', '/arrears'] },
    { title: '资金管理', paths: ['/deposits', '/subsidies', '/cashflow'] },
    { title: '基础配置', paths: ['/fee-items'] }
  ],
  房源与空间: [
    { title: '台账', paths: ['/houses', '/spaces'] },
    { title: '经营', paths: ['/house-calendar', '/short-rent'] }
  ],
  设备与通行: [
    { title: '设备', paths: ['/devices', '/device-bind', '/dev-events'] },
    { title: '门禁通行', paths: ['/access', '/keyring', '/grants'] }
  ],
  服务与监督: [
    { title: '服务作业', paths: ['/workorders', '/complaints', '/appeals'] },
    { title: '记录与规则', paths: ['/credits', '/visits', '/alerts'] }
  ],
  系统与数据: [
    { title: '数据', paths: ['/reports', '/gov'] },
    { title: '组织与权限', paths: ['/orgs', '/rbac'] },
    { title: '平台', paths: ['/sys', '/open', '/help', '/ops-center', '/ops-extras'] }
  ]
}

/** 组内排序：高频在前、配置置末 */
export const MENU_RANK = {
  '/dashboard': 1, '/todos': 2, '/messages': 3,
  '/persons': 10, '/applications': 11, '/waitlist': 12, '/allocations': 13,
  '/publicities': 14, '/annual-reviews': 19,
  '/contracts': 20, '/contract-changes': 21, '/exchanges': 22, '/terminations': 23,
  '/bills': 30, '/arrears': 31, '/deposits': 32, '/subsidies': 33,
  '/cashflow': 34, '/fee-items': 39,
  '/meter-readings': 40, '/energy': 41,
  '/houses': 50, '/house-calendar': 51, '/short-rent': 52, '/spaces': 59,
  '/devices': 60, '/device-bind': 61, '/dev-events': 62,
  '/access': 63, '/keyring': 64, '/grants': 65,
  '/workorders': 70, '/complaints': 71, '/appeals': 72,
  '/credits': 73, '/visits': 74, '/alerts': 79,
  '/reports': 80, '/gov': 81, '/orgs': 82, '/rbac': 83,
  '/sys': 84, '/open': 85, '/help': 86, '/ops-center': 87, '/ops-extras': 88
}

/** 菜单项一句话说明（hover 提示） */
export const MENU_DESC = {
  '/dashboard': '关键指标、趋势与待办概览',
  '/todos': '待受理、待审核、待处理任务',
  '/messages': '系统消息与站内通知',
  '/persons': '人员建档、实名核验与保障档案',
  '/applications': '申请受理与四级审批（初审/形式/联合/终审）',
  '/waitlist': '轮候队列与排位调整',
  '/allocations': '批次配租、摇号与中签签约',
  '/publicities': '名单公示与异议处理',
  '/annual-reviews': '年度复核任务与结果登记',
  '/contracts': '合同签订、续签与台账',
  '/contract-changes': '租金、付款方式等条款变更',
  '/exchanges': '换房申请与房源调整',
  '/terminations': '退租申请、验房与结算',
  '/bills': '出账、收款登记与账单核销',
  '/arrears': '逾期扫描、催缴动作与欠费停权',
  '/deposits': '押金收取、抵扣与退还',
  '/subsidies': '补贴标准、发放与租金抵扣',
  '/cashflow': '收入支出流水与核账',
  '/fee-items': '收费项、单价与计费规则',
  '/meter-readings': '水/电/燃气读数录入与出账',
  '/energy': '按项目、楼栋、房源的能耗分析',
  '/houses': '房源台账、房态与批量导入',
  '/house-calendar': '按天查看可售与已售',
  '/short-rent': '短租下单、入住与退房',
  '/spaces': '小区→楼栋→单元→楼层→房间空间树',
  '/devices': '门锁、水电表、门禁等设备台账',
  '/device-bind': '房源与设备绑定/解绑',
  '/dev-events': '低电量、拆机、试错、离线等告警',
  '/access': '开门记录查询',
  '/keyring': '钥匙登记、领用与归还',
  '/grants': '发卡授权任务与下发对账',
  '/workorders': '报修维保工单派单与完工',
  '/complaints': '投诉登记、处理与归档',
  '/appeals': '申诉受理与结果反馈',
  '/credits': '违规扣分与惩戒期限',
  '/visits': '来访登记与出入记录',
  '/alerts': '告警阈值、级别与通知规则',
  '/reports': '业务报表查询与导出',
  '/gov': '适配器配置、报送任务与明细',
  '/orgs': '组织层级与标准地址',
  '/rbac': '用户、角色与权限配置',
  '/sys': '数据字典、系统参数、审计日志',
  '/open': '第三方应用、AppKey 与密钥',
  '/help': '本手册：按菜单逐项说明',
  '/ops-center': '人员/房源状态与工单流程巡检',
  '/ops-extras': '消息、规则、授权等扩展工具'
}

/** 菜单项角标：路径 → /menu/badges 返回字段 */
export const MENU_BADGE_KEY = {
  '/todos': 'todo',
  '/bills': 'overdueBills',
  '/arrears': 'pendingArrears',
  '/dev-events': 'pendingAlerts',
  '/workorders': 'pendingWorkOrders'
}

/** 说明与角标都用基础路径（子页签回退到父路径） */
export function basePathOf(path, parent) {
  return parent || String(path || '').split('/:')[0]
}
