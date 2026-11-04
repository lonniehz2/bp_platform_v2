/**
 * 菜单信息架构：8 分组 + 组内分区 + 排序 + 角标 + 说明。
 *
 * 设计目标：
 *  1. 先按「使用场景」分组，再按组内使用频率排序
 *  2. 预警、冻结、自动巡查等风险动作独立成组，不再埋在服务/收费末尾
 *  3. 合同、房源、退租、换房放在同一业务链
 *  4. 设备与通行合并，避免「设备告警」和「告警中心」重复
 */
export const GROUP_ORDER = [
  '工作台', '风险与预警', '保障服务', '合同与房源', '收费与账务',
  '通行与设备', '服务与监督', '系统与数据'
]

export const GROUP_ICON = {
  工作台: 'HomeFilled',
  风险与预警: 'Warning',
  保障服务: 'UserFilled',
  合同与房源: 'Document',
  收费与账务: 'Money',
  通行与设备: 'Cpu',
  服务与监督: 'Service',
  系统与数据: 'Setting'
}

/** 旧分组名 → 新分组名（兼容历史 meta 与用户本地缓存） */
export const GROUP_ALIAS = {
  运营总览: '工作台',
  仪表盘: '工作台',
  管理后台: '系统与数据',
  系统与集成: '系统与数据',
  保障对象: '保障服务',
  资格准入: '保障服务',
  会员: '保障服务',
  线索: '保障服务',
  保障与资格: '保障服务',
  合同管理: '合同与房源',
  合同: '合同与房源',
  合同与租赁: '合同与房源',
  房源: '合同与房源',
  房源与空间: '合同与房源',
  资产台账: '合同与房源',
  资产与设备: '通行与设备',
  授权与交房: '通行与设备',
  设备与通行: '通行与设备',
  账务收费: '收费与账务',
  财务: '收费与账务',
  计量与能耗: '收费与账务',
  服务与监督: '服务与监督',
  更多: '服务与监督',
  退出与监督: '服务与监督'
}

/** 组内分区：3 项以上的大组分段展示（顺序即展示顺序） */
export const SUBGROUPS = {
  风险与预警: [
    { title: '预警与处置', paths: ['/alerts', '/patrol', '/arrears'] },
    { title: '权限与核查', paths: ['/house-access', '/credits', '/visits'] }
  ],
  保障服务: [
    { title: '申请与配租', paths: ['/applications', '/waitlist', '/allocations', '/publicities'] },
    { title: '人员与复核', paths: ['/persons', '/annual-reviews'] }
  ],
  合同与房源: [
    { title: '合同', paths: ['/contracts', '/contract-changes', '/exchanges', '/terminations'] },
    { title: '房源', paths: ['/houses', '/spaces'] },
    { title: '经营', paths: ['/house-calendar', '/short-rent'] }
  ],
  收费与账务: [
    { title: '收费作业', paths: ['/bills'] },
    { title: '资金管理', paths: ['/deposits', '/subsidies', '/cashflow'] },
    { title: '计量与计费', paths: ['/meter-readings', '/energy', '/fee-items'] }
  ],
  通行与设备: [
    { title: '设备', paths: ['/devices', '/device-bind', '/dev-events', '/dev-commands', '/iot-tools', '/iot-monitor', '/iot-reconcile'] },
    { title: '通行与授权', paths: ['/access', '/keyring', '/grants'] }
  ],
  服务与监督: [
    { title: '服务作业', paths: ['/workorders', '/complaints', '/appeals'] }
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
  '/alerts': 4, '/patrol': 5, '/arrears': 6, '/house-access': 7, '/credits': 8, '/visits': 9,
  '/persons': 10, '/applications': 11, '/waitlist': 12, '/allocations': 13,
  '/publicities': 14, '/annual-reviews': 19,
  '/contracts': 20, '/contract-changes': 21, '/exchanges': 22, '/terminations': 23,
  '/bills': 30, '/deposits': 32, '/subsidies': 33,
  '/cashflow': 34, '/fee-items': 39,
  '/meter-readings': 40, '/energy': 41,
  '/houses': 50, '/house-calendar': 51, '/short-rent': 52, '/spaces': 59,
  '/devices': 60, '/device-bind': 61, '/dev-events': 62, '/dev-commands': 63, '/iot-tools': 64, '/iot-monitor': 65, '/iot-reconcile': 66,
  '/access': 63, '/keyring': 64, '/grants': 65,
  '/workorders': 70, '/complaints': 71, '/appeals': 72,
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
  '/arrears': '逾期扫描、催缴动作、冻结与恢复',
  '/deposits': '押金收取、抵扣与退还',
  '/subsidies': '补贴标准、发放与租金抵扣',
  '/cashflow': '流水 / 对账单 / 收款确认',
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
  '/dev-commands': '远程开锁/重启/校时/拉合闸（经 IoT 下发）',
  '/iot-tools': '验签自测、回调日志与重放',
  '/iot-monitor': '在线率、指令与回调成功率',
  '/iot-reconcile': '指令/回调/表计日对账与导出',
  '/access': '开门记录查询',
  '/keyring': '钥匙登记、领用与归还',
  '/grants': '通行权限的新建、撤销与对账审计',
  '/workorders': '报修维保工单派单与完工',
  '/complaints': '投诉登记、处理与归档',
  '/appeals': '申诉受理与结果反馈',
  '/house-access': '按房源一键冻结、恢复、临时授权与应急密码',
  '/patrol': '查看巡查阈值并手工补跑每日预警/欠费处置',
  '/credits': '违规扣分与惩戒期限',
  '/visits': '入户核查房屋使用情况（转租/空置/违规）',
  '/alerts': '预警事件处置：处理/解决/忽略/升级，含告警规则',
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
  '/dev-events': 'devAlerts',
  '/alerts': 'pendingAlerts',
  '/workorders': 'pendingWorkOrders'
}

/** 说明与角标都用基础路径（子页签回退到父路径） */
export function basePathOf(path, parent) {
  return parent || String(path || '').split('/:')[0]
}

/**
 * 菜单中隐藏的路径（路由保留，管理员可直接访问）。
 *
 * 运维操作台 / 扩展操作台是早期后台工具，功能与业务页重复：
 *   人员状态 → 人员档案「改状态」
 *   房源状态 → 房源台账「改状态」
 *   工单流程 → 工单维保「派单/流转」
 *   扩展台 6 个页签 → 消息/告警规则/开放平台/权限/授权/日房态 均已存在
 * 因此不再占用菜单项，减少「系统与数据」的拥挤。
 */
export const HIDDEN_PATHS = ['/ops-center', '/ops-extras', '/energy-allocation']
