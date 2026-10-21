# -*- coding: utf-8 -*-
"""生成首期功能完整性检查报告（孤儿表清单已固化，不依赖 DB）"""
import io
import os
import re

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
OUT = r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md'

# ---------- 接口盘点（本地代码，不依赖 DB）----------
apis = []
for root, _, files in os.walk(BASE):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        base = m.group(1) if m else ''
        cnt = len(re.findall(r'@(Get|Post|Put|Delete)Mapping', s))
        apis.append((f.replace('Controller.java', ''), base, cnt))
apis.sort()
total_api = sum(a[2] for a in apis)

# ---------- 孤儿表（上次 DB 盘点结果，72 张）----------
ORPHANS = """bp_asset_import_batch|资产导入批次（留痕与回滚）
bp_asset_parking|车位
bp_asset_space_device|空间-设备绑定关系（业务视图）
bp_asset_space_occupancy|空间-人员占用关系
bp_biz_contract_template|合同模板
bp_biz_priority_object|优先配租对象明细
bp_biz_publicity_item|公示名单明细（含异议）
bp_dev_access_record|开门记录（大表，按月分区）
bp_dev_availability_probe|核心功能可用率探针记录
bp_dev_callback_log|回调接收日志（含幂等命中统计）
bp_dev_change_log|换锁/换表记录
bp_dev_device_alert|设备告警记录
bp_dev_iot_call_log|IoT 接口调用日志
bp_dev_online_stat|设备在线率统计
bp_dev_reconcile_watermark|对账任务水位（断点续跑）
bp_flow_definition|流程定义
bp_flow_instance|流程实例
bp_flow_log|流程流转日志
bp_flow_node|流程节点
bp_flow_task|流程任务（待办）
bp_gov_adapter_config|外部系统接口配置（适配器）
bp_gov_adapter_log|适配器调用日志
bp_gov_report_detail|监管报送明细
bp_gov_report_task|监管报送任务
bp_grant_audit_log|授权操作审计（不可修改）
bp_grant_iot_person_map|IoT 人员映射
bp_grant_keyring|钥匙包（以人为中心的介质集合）
bp_grant_reconcile_diff|授权对账差异记录
bp_iam_account_set|账套（多财务主体隔离）
bp_iam_permission|权限资源
bp_iam_role|角色
bp_iam_role_permission|角色-权限关系
bp_iam_session|登录会话
bp_iam_user|系统用户
bp_iam_user_role|用户-角色-组织关系
bp_msg_send_record|消息发送记录
bp_msg_subscription|消息订阅配置
bp_msg_template|消息模板
bp_msg_todo|待办事项（站内）
bp_open_api|开放接口清单
bp_open_app|开放应用（AppKey/AppSecret）
bp_open_call_log|开放调用日志
bp_open_webhook|Webhook 订阅
bp_open_webhook_log|Webhook 推送记录
bp_ops_alert_notify|告警通知记录
bp_ops_alert_rule|告警规则（可配置规则引擎）
bp_ops_auto_inspection|自动巡查任务与结果
bp_person_blacklist|黑名单/失信名单
bp_person_document|证件与材料
bp_person_family|家庭成员
bp_person_guarantee_profile|保障对象档案（保障房专有扩展）
bp_person_service_address|送达地址
bp_person_tag|人员标签定义
bp_person_tag_relation|人员-标签关系
bp_person_verify_record|实名认证记录
bp_rpt_export_task|导出任务（异步）
bp_rpt_metric_daily|指标日汇总
bp_rpt_metric_hourly|指标小时汇总
bp_rpt_report_def|报表定义
bp_rpt_screen_def|大屏定义（可配置布局）
bp_rule_execute_log|规则执行日志
bp_rule_rule|规则（条件+阈值+动作）
bp_rule_ruleset|规则集
bp_sys_audit_log|审计日志（只追加）
bp_sys_config|系统参数
bp_sys_dict|数据字典
bp_sys_file|文件
bp_sys_job|定时任务定义
bp_sys_job_log|定时任务执行日志
bp_sys_mq_dlq|死信消息
bp_sys_mq_idempotent|MQ 消费幂等记录
bp_sys_oper_log|操作日志"""

orphans = []
for ln in ORPHANS.strip().split('\n'):
    t, cm = ln.split('|')
    orphans.append((t.strip(), cm.strip()))

groups = {}
for t, cm in orphans:
    key = t.split('_')[1]
    groups.setdefault(key, []).append((t, cm))

TOTAL_TABLES = 117
TOTAL_ENTITIES = TOTAL_TABLES - len(orphans)

# ---------- P0 逐项 ----------
P0 = [
    ("1", "组织与权限（含多租户）", "部分",
     "组织 CRUD ✅（Org 5 接口）+ 多租户行级隔离 ✅",
     "**RBAC 完全缺失**：`bp_iam_user`/`role`/`permission`/`user_role`/`role_permission`/"
     "`session`/`account_set` 共 7 表无实体无接口。当前用请求头 `X-User-Id` 直接信任，"
     "**无登录、无鉴权、无会话管理**",
     "高"),
    ("2", "空间资产管理与房源台账", "已实现",
     "Space 6 接口（6 级空间树 + path_code）+ House 4 接口 + 日房态 HouseCalendar 8 接口",
     "`bp_asset_import_batch`（批量导入留痕/回滚）未实现；车位按文档属 P1 暂缓",
     "—"),
    ("3", "保障对象档案", "部分",
     "Person 6 接口；家庭成员由 `bp_biz_contract_cohabitant` 替代实现",
     "**`bp_person_guarantee_profile`（保障对象档案专有扩展）未实现**——收入档位/保障类型/"
     "住房困难情况无存放处；`bp_person_tag`/`tag_relation` 未实现",
     "中"),
    ("4", "实名认证与唯一性绑定 ★", "部分",
     "`SensitiveDataCodec` 已实现身份证校验和 hash+脱敏（可支撑唯一性判定）",
     "**`bp_person_verify_record`（实名认证记录）未实现**——无认证流水/渠道/合规留痕；"
     "`bp_person_document` 未实现；唯一性绑定未在申请链路强制校验",
     "中"),
    ("5", "资格审核（申请→联审→公示→轮候）", "已实现",
     "Application 8 接口（4 阶段审核 + 补件/撤回/轨迹）+ Publicity 13 接口（7 天强制校验）"
     "+ Allocation 21 接口（轮候/批次/摇号）",
     "**流程引擎未采用**：`bp_flow_*` 5 表空置，审核阶段枚举硬编码；"
     "`bp_biz_publicity_item`（公示名单明细含异议）未实现，公示只有主体没有名单",
     "—"),
    ("6", "配租管理（批次→摇号→选房→配租）", "已实现",
     "Allocation 21 接口：入轮候/算分排名/冻结解冻/批次/房源池/摇号(种子可复现)/"
     "配租单/签约/放弃/超时释放",
     "**自动递补未实现**（放弃后需人工排递补）；`bp_biz_priority_object` 未实现，优先分靠手工传",
     "—"),
    ("7", "合同管理（签约→续签→终止）", "已实现",
     "Contract 10 + ContractChange 6（调租/租期/承租人，批准写回）+ Cohabitant 6"
     "（同住人/保障人口）+ Exchange 9（换房真实落地：新合同+原合同终止+房源互换）",
     "`bp_biz_contract_template`（合同模板）未实现；续签走 RENEW 只延长止租日，不生成新合同",
     "—"),
    ("8", "计费与账务（账单→缴费→催缴→欠费关停）", "已实现",
     "**fin 13/13 张表全部实现**：Billing 11 + FeeItem 9（计费引擎 7 方式×4 规则）"
     "+ BillGeneration 2 + DepositRefund 12 + Subsidy 11 + ArrearsAction 7"
     "（安全底线：不停大门）+ FinLedger 14（催缴/对账/流水，自动记账）",
     "—", "—"),
    ("9", "补贴管理", "已实现",
     "Subsidy 11 接口：4 种方式（定额/按面积/按人/租金比例）+ 月度封顶 + 抵租联动 + 批量发放",
     "—", "—"),
    ("10", "权益与授权编排（四级权限+钥匙包+自动匹配）★", "部分",
     "Grant 6 接口（权益/任务/明细 + MQ 异步 + 重试）+ 真实 IoT 加解密对接已实测通过",
     "**钥匙包未实现**（`bp_grant_keyring`）——无法以人为中心管理多介质；"
     "**授权审计未实现**（`bp_grant_audit_log`）——★ 级要求，授权操作必须不可篡改可追溯；"
     "`bp_grant_iot_person_map`/`bp_grant_reconcile_diff` 未实现",
     "高"),
    ("11", "设备管理（业务视图）+ 通行记录 + 行为轨迹", "部分",
     "Dev 4 接口（设备类型/绑定解析）+ 真实 IoT 对接验证（36 把锁，含在线状态/电量）",
     "**通行记录缺失**（`bp_dev_access_record` 已建表但无实体无接口）——"
     "「行为轨迹」「空置判定」失去数据源；`bp_asset_space_device`/`bp_dev_change_log` 未实现",
     "高"),
    ("12", "告警与预警", "部分",
     "Alert 9 接口（5 状态/4 级别/分类/转工单）",
     "**告警规则引擎未实现**（`bp_ops_alert_rule`）——“自设阈值”要求未满足，规则写死在代码；"
     "`bp_ops_alert_notify` 未实现；`bp_rule_*` 3 表未实现",
     "中"),
    ("13", "工单与维保", "已实现",
     "WorkOrder 11 接口（8 状态 / SLA 响应与完成时限 / 超时判定）",
     "`bp_ops_auto_inspection`（7×24 自动巡查）未实现",
     "—"),
    ("14", "消息中心", "未实现", "无",
     "**`bp_msg_template`/`subscription`/`send_record`/`todo` 4 表全部未实现**——"
     "无模板、无订阅、无发送记录、无站内待办",
     "高"),
    ("15", "报表与数据导出", "未实现", "无（仅各模块分页查询）",
     "**`bp_rpt_report_def`/`export_task`/`metric_daily`/`metric_hourly` 4 表未实现**——"
     "无报表定义、无异步导出、无指标汇总",
     "高"),
    ("16", "数据大屏（驾驶舱）", "部分",
     "验证台有「驾驶舱」页签（调告警统计做简单展示）",
     "**`bp_rpt_screen_def`（可配置大屏）+ `bp_rpt_metric_*`（指标汇总）未实现**——"
     "当前为前端硬编码取数，非产品级可配置大屏，也未做指标预聚合",
     "中"),
    ("17", "移动端（租户小程序 + 工作人员端）", "未实现", "无",
     "**完全未实现**。当前只有 PC 验证台（单页 20 页签），无小程序、无移动端",
     "高"),
    ("18", "开放平台（对接公租房系统、公安）", "未实现", "无",
     "**`bp_open_app`/`api`/`call_log`/`webhook`/`webhook_log` 5 表未实现**；"
     "`bp_gov_adapter_config`/`adapter_log`/`report_task`/`report_detail` 4 表未实现——"
     "无房管局备案报送、无公安登记推送，**标书明确要求**",
     "高"),
]

SYS_GAPS = [
    ("bp_sys_audit_log", "审计日志（关键动作只追加不可改）", "保障房必须可审计；当前仅应用日志"),
    ("bp_sys_dict", "数据字典", "枚举全硬编码 Java enum，无法租户级配置"),
    ("bp_sys_config", "系统参数", "7 天公示/5 年禁申/3 个月过渡期等政策参数硬编码"),
    ("bp_sys_file", "文件", "证据材料/公示附件仅存 URL 字符串，无文件管理"),
    ("bp_sys_job / bp_sys_job_log", "定时任务定义与执行日志", "定时出账/年审/扫描用 @Scheduled 硬编码"),
    ("bp_sys_mq_idempotent / bp_sys_mq_dlq", "MQ 幂等与死信处置", "幂等靠业务层，无统一死信入口"),
    ("bp_sys_oper_log", "操作日志", "无"),
]

done = [p for p in P0 if p[2] == '已实现']
part = [p for p in P0 if p[2] == '部分']
none = [p for p in P0 if p[2] == '未实现']

L = []
w = L.append

w('# 首期功能完整性检查报告')
w('')
w('| 项 | 内容 |')
w('|---|---|')
w('| 检查基准 | `01_需求与功能方案.md` §7.1 「首期范围（必建 P0）」共 **18 项** |')
w('| 检查方式 | 代码静态盘点（Controller/接口数、`@TableName` 实体）+ 数据库表覆盖比对 + 真机接口验证 |')
w('| 代码现状 | **%d 个接口** ／ **%d 张表**（有实体 %d、孤儿表 %d）'
  % (total_api, TOTAL_TABLES, TOTAL_ENTITIES, len(orphans)))
w('| 检查结论 | **完全实现 %d 项 ／ 部分实现 %d 项 ／ 未实现 %d 项**'
  % (len(done), len(part), len(none)))
w('')
w('---')
w('')
w('## 一、总体结论')
w('')
w('| 判定 | 数量 | P0 项 |')
w('|---|---|---|')
w('| ✅ 已实现 | %d / 18 | %s |' % (len(done), '、'.join(p[0] for p in done)))
w('| ⚠️ 部分实现 | %d / 18 | %s |' % (len(part), '、'.join(p[0] for p in part)))
w('| ❌ 未实现 | %d / 18 | %s |' % (len(none), '、'.join(p[0] for p in none)))
w('')
w('### 一句话结论')
w('')
w('> **业务主线完整可用，平台能力基本空白。**')
w('>')
w('> 保障房核心闭环（申请 → 审核 → 配租 → 摇号 → 公示 → 签约 → 计费 → 收款 → 补贴 '
  '→ 年审 → 换房 → 退租 → 结算 → 复议 → 失信惩戒）**已全部落地并经真机验证**，'
  '%d 个接口、约 950 项真机用例通过。' % total_api)
w('>')
w('> 但作为**可交付的生产系统**，还缺三块地基：**权限与鉴权**（无法上生产）、'
  '**系统支撑层**（审计/字典/配置/文件）、**平台能力**（消息/报表/开放/移动端）。')
w('')
w('---')
w('')
w('## 二、P0 逐项核查表')
w('')
w('| # | P0 项 | 判定 | 已实现内容 | 缺口 |')
w('|---|---|---|---|---|')
for no, name, st, has, gap, prio in P0:
    icon = {'已实现': '✅', '部分': '⚠️', '未实现': '❌'}[st]
    w('| %s | %s | %s %s | %s | %s |' % (no, name, icon, st, has, gap if gap else '—'))
w('')
w('---')
w('')
w('## 三、缺口按影响分级')
w('')
w('### 🔴 阻塞级（不补无法验收/上生产）')
w('')
w('| 缺口 | 涉及表 | 具体影响 |')
w('|---|---|---|')
w('| **RBAC 权限体系** | 7 张 `bp_iam_*` | 无登录、无鉴权、无会话。**任何人构造 `X-User-Id` 头即可调任意接口**，'
  '无角色/菜单/按钮/数据权限控制，无法多用户上线 |')
w('| **审计日志** | `bp_sys_audit_log` | 保障房业务（审核/配租/调租/清退/失信）**必须可追溯**，'
  '当前只有应用日志，无结构化审计表 |')
w('| **监管报送** | 4 张 `bp_gov_*` | 标书要求对接房管局备案系统与公安平台，**完全未实现** |')
w('| **开放平台** | 5 张 `bp_open_*` | 无 AppKey/AppSecret 管理、无接口清单、无调用日志、无 Webhook |')
w('')
w('### 🟠 高优先（★ 级考核项或业务触达）')
w('')
w('| 缺口 | 涉及表 | 具体影响 |')
w('|---|---|---|')
w('| **通行记录** | `bp_dev_access_record` | ★ 级考核「空置与违规使用判定」「行为轨迹」的**唯一数据源**，'
  '表已建（按月分区）但零实现 |')
w('| **授权审计** | `bp_grant_audit_log` | ★ 级要求「四级权限」必须可追溯且不可篡改 |')
w('| **钥匙包** | `bp_grant_keyring` | ★ 级要求「以人为中心的介质集合」（人脸/指纹/密码/卡）未实现 |')
w('| **消息中心** | 4 张 `bp_msg_*` | 催缴/告警/审核结果**无法触达租户**，业务闭环缺“最后一公里” |')
w('| **报表与导出** | 4 张 `bp_rpt_*` | 无监管报表、无异步导出，无法向上报送 |')
w('| **移动端** | — | 租户小程序、工作人员端均无，交付形态不完整 |')
w('')
w('### 🟡 中优先（精细化与合规完整性）')
w('')
w('| 缺口 | 涉及表 | 具体影响 |')
w('|---|---|---|')
w('| 保障对象档案 | `bp_person_guarantee_profile` | 收入档位/保障类型/住房困难等**保障专有属性无存放处** |')
w('| 实名认证留痕 | `bp_person_verify_record` | 有身份证校验逻辑，但无认证记录、无渠道、无合规留痕 |')
w('| 告警规则引擎 | `bp_ops_alert_rule` + 3 张 `bp_rule_*` | 文档要求「预设规则条件、自设阈值」，当前规则写死 |')
w('| 可配置大屏 | `bp_rpt_screen_def` | 驾驶舱为前端硬编码，非产品级可配置 |')
w('| 公示名单明细 | `bp_biz_publicity_item` | 公示只有主体，**无法列出具体名单与异议处理** |')
w('')
w('### 🟢 可延后（不阻塞主流程）')
w('')
w('| 缺口 | 涉及表 |')
w('|---|---|')
w('| 优先配租对象明细 | `bp_biz_priority_object`（优先分靠手工传） |')
w('| 合同模板 | `bp_biz_contract_template` |')
w('| 自动递补 | 无表（逻辑缺失，放弃后需人工） |')
w('| 车位 / 能源 / 梯控 | `bp_asset_parking` 等（文档已列 P1 暂缓） |')
w('| 人员标签 / 送达地址 / 黑名单 | 3 张 `bp_person_*` |')
w('')
w('---')
w('')
w('## 四、孤儿表清单（%d 张，建表未实现）' % len(orphans))
w('')
w('> 孤儿表 = 数据库已建表，但无 Java 实体、无 Mapper、无 Service、无接口。')
w('')
w('| 分组 | 张数 | 表名（去掉前缀） |')
w('|---|---|---|')
for g in sorted(groups):
    items = groups[g]
    w('| `bp_%s_*` | %d | %s |'
      % (g, len(items),
         '、'.join('`%s`' % t.replace('bp_' + g + '_', '') for t, _ in items)))
w('')
w('### 系统支撑层缺口（影响全局，非单模块）')
w('')
w('| 表 | 能力 | 现状 |')
w('|---|---|---|')
for t, cap, note in SYS_GAPS:
    w('| `%s` | %s | %s |' % (t, cap, note))
w('')
w('---')
w('')
w('## 五、已实现模块清单（可直接演示验收）')
w('')
w('| 模块 | 接口数 | 根路径 |')
w('|---|---|---|')
for mod, base, cnt in apis:
    w('| %s | %d | `%s` |' % (mod, cnt, base))
w('')
w('**合计 %d 个接口。**' % total_api)
w('')
w('---')
w('')
w('## 六、与设计文档的偏差（需业务确认）')
w('')
w('| # | 偏差 | 现状 | 建议 |')
w('|---|---|---|---|')
w('| 1 | 流程引擎未采用 | 审核阶段用 `ReviewStage` 枚举硬编码，`bp_flow_*` 5 表空置 | '
  '多地区审核流程差异大（文档 §3.4.2「差异最大的环节」），建议接入或明确降级 |')
w('| 2 | 枚举硬编码 | 状态/类型全用 Java enum，`bp_sys_dict` 空置 | 多租户差异化需字典表；当前改政策要改代码 |')
w('| 3 | 政策参数硬编码 | 7 天公示、5 年禁申、3 个月过渡期、1.5 倍租金写在常量 | 迁入 `bp_sys_config` 支持分地区配置 |')
w('| 4 | 续签不生成新合同 | `RENEW` 只延长 `leaseEnd`；换房会生成新合同 | 统一：续签也生成新合同 + `parentContractId` 链 |')
w('| 5 | 公示无名单 | 只有公示主体 | 补 `bp_biz_publicity_item` |')
w('| 6 | **单元测试为零** | 363 个类、0 个业务单测（宿主机约 1GB 内存，Mockito 无法初始化） | '
  '释放内存后补齐；否则“性能稳定”目标无保障 |')
w('')
w('---')
w('')
w('## 七、建议收尾顺序')
w('')
w('| 批次 | 内容 | 理由 |')
w('|---|---|---|')
w('| **第 1 批** | RBAC 权限（7 表）+ 审计日志 + 数据字典/系统参数 | 无鉴权不能上生产；审计是保障房合规底线 |')
w('| **第 2 批** | 通行记录 + 授权审计 + 钥匙包 | ★ 级考核指标的数据来源与 ★ 级要求 |')
w('| **第 3 批** | 消息中心 + 报表导出 | 业务触达与向上报送 |')
w('| **第 4 批** | 开放平台 + 监管报送 | 标书明确要求，对接房管局/公安 |')
w('| **第 5 批** | 移动端 | 交付形态 |')
w('| **第 6 批** | 单元测试 + 性能压测 | 支撑“性能稳定” |')
w('| 可延后 | 优先对象、合同模板、公示名单、自动递补、文件管理 | 精细化，不阻塞主流程 |')
w('')
w('---')
w('')
w('## 附：本报告证据来源')
w('')
w('| 证据 | 位置 |')
w('|---|---|')
w('| 接口清单（%d 个） | `_验证/_inventory.txt` |' % total_api)
w('| 表结构（117 张 / 2079 列） | `03_数据库设计_P1~P7*.sql` + 真机 `verify.py readback` |')
w('| 真机接口验证（约 950 项） | `_验证/_verify_*.py` 共 40+ 脚本 |')
w('| 首期范围定义 | `01_需求与功能方案.md` §7.1 |')
w('')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('报告已生成：%s' % OUT)
print('  行数 %d' % len(L))
print('  P0: 已实现 %d / 部分 %d / 未实现 %d' % (len(done), len(part), len(none)))
print('  孤儿表 %d 张，分 %d 组' % (len(orphans), len(groups)))
print('  接口 %d 个' % total_api)
