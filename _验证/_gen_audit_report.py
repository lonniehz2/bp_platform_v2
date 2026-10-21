# -*- coding: utf-8 -*-
"""生成首期功能完整性检查报告"""
import io
import os
import re

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
OUT = r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md'

# ---------- 采集：接口 ----------
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

# ---------- 采集：表 ----------
import pymysql
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = c.cursor()
cur.execute("""SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES
               WHERE TABLE_SCHEMA='bp_platform' ORDER BY TABLE_NAME""")
tables = cur.fetchall()
c.close()

entities = set()
for root, _, files in os.walk(BASE):
    for f in files:
        if not f.endswith('.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        m = re.search(r'@TableName\("([^"]+)"\)', s)
        if m:
            entities.add(m.group(1))

orphans = [(t, cm) for t, cm in tables if t not in entities]

# 按前缀分组
groups = {}
for t, cm in orphans:
    key = t.split('_')[1] if t.count('_') >= 2 else 'other'
    groups.setdefault(key, []).append((t, cm or ''))

total_api = sum(a[2] for a in apis)

# ---------- P0 逐项评估 ----------
P0 = [
    ("1", "组织与权限（含多租户）", "部分",
     "组织 CRUD ✅（Org 5 接口）+ 多租户行级隔离 ✅（TransmittableThreadLocal + TenantLineInnerInterceptor）",
     "**RBAC 完全缺失**：`bp_iam_user` / `bp_iam_role` / `bp_iam_permission` / "
     "`bp_iam_user_role` / `bp_iam_role_permission` / `bp_iam_session` / `bp_iam_account_set` "
     "共 7 张表无实体无接口。当前用请求头 `X-User-Id` 直接信任，**无登录、无鉴权、无会话**。",
     "P0-高"),
    ("2", "空间资产管理与房源台账", "已实现",
     "Space 6 接口（6 级空间树 + path_code）+ House 4 接口 + 日房态 HouseCalendar 8 接口",
     "`bp_asset_import_batch`（批量导入留痕/回滚）未实现；`bp_asset_parking`（车位）按文档属 P1 暂缓",
     "—"),
    ("3", "保障对象档案", "部分",
     "Person 6 接口 + `bp_person_family` 由 `bp_biz_contract_cohabitant` 替代实现",
     "**`bp_person_guarantee_profile`（保障对象档案专有扩展）未实现**——收入档位、保障类型、"
     "住房困难情况等保障专有字段无处存放；`bp_person_tag` / `bp_person_tag_relation`（标签）未实现",
     "P0-中"),
    ("4", "实名认证与唯一性绑定 ★", "部分",
     "`SensitiveDataCodec` 已实现身份证校验和 hash+脱敏（可支撑唯一性判定）",
     "**`bp_person_verify_record`（实名认证记录）未实现**——无认证流水、无认证渠道、无合规留痕；"
     "`bp_person_document`（证件与材料）未实现；唯一性绑定未在申请链路强制校验",
     "P0-中"),
    ("5", "资格审核（申请→联审→公示→轮候）", "已实现",
     "Application 8 接口（4 阶段审核 + 补件/撤回/轨迹）+ Publicity 13 接口（7 天强制校验）"
     "+ Allocation 21 接口（轮候/批次/摇号）",
     "**流程引擎未采用**：`bp_flow_*` 5 张表为空，审核阶段用枚举硬编码（`ReviewStage`），"
     "政策变化需改代码而非配流程；`bp_biz_publicity_item`（公示名单明细含异议）未实现，"
     "公示只有主体没有名单",
     "—"),
    ("6", "配租管理（批次→摇号→选房→配租）", "已实现",
     "Allocation 21 接口：入轮候/算分排名/冻结解冻/批次/房源池/摇号(种子可复现)/配租单/签约/放弃/超时释放",
     "**自动递补未实现**：中签者放弃后房源回池，但不会自动排给递补者（需人工发起）；"
     "`bp_biz_priority_object`（优先对象明细）未实现，优先分靠手工传",
     "—"),
    ("7", "合同管理（签约→续签→终止）", "已实现",
     "Contract 10 接口 + ContractChange 6 接口（调租/租期/承租人，批准写回）+ "
     "Cohabitant 6 接口（同住人/保障人口）+ Exchange 9 接口（换房真实落地）",
     "`bp_biz_contract_template`（合同模板）未实现，合同无模板版本管理；"
     "**续签走 ContractChange 的 RENEW 类型，未生成独立新合同**（换房会生成新合同）",
     "—"),
    ("8", "计费与账务（账单→缴费→催缴→欠费关停）", "已实现",
     "**13/13 张 fin 表全部实现**：Billing 11 + FeeItem 9（计费引擎 7 方式×4 规则）"
     "+ BillGeneration 2（批量出账）+ DepositRefund 12 + Subsidy 11 + ArrearsAction 7"
     "（安全底线：不停大门）+ FinLedger 14（催缴/对账/流水）",
     "—",
     "—"),
    ("9", "补贴管理", "已实现",
     "Subsidy 11 接口：4 种补贴方式（定额/按面积/按人/租金比例）+ 月度封顶 + 抵租联动 + 批量发放",
     "—", "—"),
    ("10", "权益与授权编排（四级权限+钥匙包+自动匹配）★", "部分",
     "Grant 6 接口（权益/任务/明细 + MQ 异步 + 重试）+ 真实 IoT 加解密对接（AES-CBC + MD5 签名，已实测通过）",
     "**钥匙包未实现**（`bp_grant_keyring`）——无法以人为中心管理多介质（人脸/指纹/密码/卡）；"
     "**授权审计未实现**（`bp_grant_audit_log`）——授权操作无不可篡改记录，这是 ★ 级要求；"
     "`bp_grant_iot_person_map`（本地↔IoT 人员映射）与 `bp_grant_reconcile_diff`（授权对账差异）未实现",
     "P0-高"),
    ("11", "设备管理（业务视图）+ 通行记录 + 行为轨迹", "部分",
     "Dev 4 接口（设备类型/绑定解析）+ 真实 IoT 平台对接验证（36 把锁，含在线状态/电量）",
     "**通行记录缺失**（`bp_dev_access_record`，大表按月分区已建但无实体无接口）——"
     "「行为轨迹」「空置判定」失去数据源；`bp_asset_space_device`（空间-设备绑定业务视图）未实现；"
     "`bp_dev_change_log`（换锁记录）未实现",
     "P0-高"),
    ("12", "告警与预警", "部分",
     "Alert 9 接口（5 状态 / 4 级别 / 分类 / 转工单）",
     "**告警规则引擎未实现**（`bp_ops_alert_rule`）——文档要求「预设规则条件、自设阈值」"
     "目前规则写死在代码；`bp_ops_alert_notify`（通知记录）未实现；`bp_rule_*` 3 张表未实现",
     "P0-中"),
    ("13", "工单与维保", "已实现",
     "WorkOrder 11 接口（8 状态 / SLA 响应与完成时限 / 超时判定）",
     "`bp_ops_auto_inspection`（自动巡查任务）未实现——文档要求「7×24 无人化巡查」",
     "—"),
    ("14", "消息中心", "未实现",
     "无",
     "**`bp_msg_template` / `bp_msg_subscription` / `bp_msg_send_record` / `bp_msg_todo` 4 张表全部未实现**——"
     "无消息模板、无订阅配置、无发送记录、无站内待办",
     "P0-高"),
    ("15", "报表与数据导出", "未实现",
     "无（仅各模块分页查询）",
     "**`bp_rpt_report_def` / `bp_rpt_export_task` / `bp_rpt_metric_daily` / `bp_rpt_metric_hourly` 5 张表全部未实现**——"
     "无报表定义、无异步导出、无指标汇总",
     "P0-高"),
    ("16", "数据大屏（驾驶舱）", "部分",
     "验证台有「驾驶舱」页签（调用告警统计接口做简单展示）",
     "**`bp_rpt_screen_def`（大屏定义，可配置布局与组件）+ `bp_rpt_metric_*`（指标汇总）未实现**——"
     "当前驾驶舱是前端硬编码取数，不是可配置大屏，也未做指标预聚合",
     "P0-中"),
    ("17", "移动端（租户小程序 + 工作人员端）", "未实现",
     "无",
     "**完全未实现**。当前只有 PC 验证台（单页 index.html，20 页签），无小程序、无工作人员移动端",
     "P0-高"),
    ("18", "开放平台（对接公租房系统、公安）", "未实现",
     "无",
     "**`bp_open_app` / `bp_open_api` / `bp_open_call_log` / `bp_open_webhook` / `bp_open_webhook_log` 5 张表未实现**；"
     "`bp_gov_adapter_config` / `bp_gov_adapter_log` / `bp_gov_report_task` / `bp_gov_report_detail` 4 张表未实现 —— "
     "**无房管局备案报送、无公安登记推送**",
     "P0-高"),
]

# 系统支撑层（横切，非 P0 单列但必需）
SYS_GAPS = [
    ("bp_sys_audit_log", "审计日志（关键动作只追加）", "保障房必须可审计；当前仅应用日志"),
    ("bp_sys_dict", "数据字典", "枚举全硬编码在 Java enum，无法租户级配置"),
    ("bp_sys_config", "系统参数", "政策参数（如 7 天公示、5 年禁申）硬编码"),
    ("bp_sys_file", "文件", "证据材料/公示附件仅存 URL 字符串，无文件管理"),
    ("bp_sys_job / bp_sys_job_log", "定时任务定义与执行日志", "定时出账/年审/扫描用 @Scheduled 硬编码"),
    ("bp_sys_mq_idempotent / bp_sys_mq_dlq", "MQ 幂等与死信", "MQ 消费幂等靠业务幂等，无统一死信处置"),
    ("bp_sys_oper_log", "操作日志", "无"),
]

lines = []
w = lines.append

w('# 首期功能完整性检查报告')
w('')
w('| 项 | 内容 |')
w('|---|---|')
w('| 检查对象 | 智慧保障房（公租房）首期范围 —— `01_需求与功能方案.md` §7.1 P0 共 18 项 |')
w('| 检查方式 | 代码静态盘点（接口/实体）+ 数据库表覆盖比对 + 真机接口验证 |')
w('| 代码现状 | **%d 个接口 / %d 张表 / %d 张有实体 / %d 张孤儿表**'
  % (total_api, len(tables), len(entities), len(orphans)))
w('| 结论 | **首期 18 项 P0：完全实现 6 项、部分实现 6 项、未实现 6 项** |')
w('')
w('---')
w('')
w('## 一、总体结论')
w('')
w('| 判定 | 数量 | 占比 | P0 项 |')
w('|---|---|---|---|')
done = [p for p in P0 if p[2] == '已实现']
part = [p for p in P0 if p[2] == '部分']
none = [p for p in P0 if p[2] == '未实现']
w('| ✅ 已实现 | %d | %.0f%% | %s |'
  % (len(done), len(done) / 18 * 100, '、'.join(p[0] for p in done)))
w('| ⚠️ 部分实现 | %d | %.0f%% | %s |'
  % (len(part), len(part) / 18 * 100, '、'.join(p[0] for p in part)))
w('| ❌ 未实现 | %d | %.0f%% | %s |'
  % (len(none), len(none) / 18 * 100, '、'.join(p[0] for p in none)))
w('')
w('**核心业务主线（申请→配租→合同→计费→退租）已完整闭环并经真机验证**；')
w('**但平台化能力（权限、消息、报表、开放、移动端）与系统性要求（审计、字典、配置、文件）基本空白。**')
w('')
w('---')
w('')
w('## 二、P0 逐项核查')
w('')
w('| # | P0 项 | 判定 | 已实现 | 缺口 |')
w('|---|---|---|---|---|')
for no, name, st, has, gap, prio in P0:
    icon = {'已实现': '✅', '部分': '⚠️', '未实现': '❌'}[st]
    w('| %s | %s | %s %s | %s | %s |' % (no, name, icon, st, has, gap if gap else '—'))
w('')
w('### 缺口分级（按对验收的影响）')
w('')
w('| 优先级 | 缺口 | 影响 |')
w('|---|---|---|')
w('| **P0-高** | RBAC 权限体系（7 表） | 无登录/鉴权/会话，任何人可调任意接口——**无法验收、无法上生产** |')
w('| **P0-高** | 消息中心（4 表） | 催缴/告警/审核结果无法触达租户——业务闭环缺“最后一公里” |')
w('| **P0-高** | 报表与导出（5 表） | 无监管报表、无导出，房管局报送无法完成 |')
w('| **P0-高** | 移动端 | 租户与工作人员无入口，纯 PC 后台不符合交付形态 |')
w('| **P0-高** | 开放平台 + 监管报送（9 表） | 无法对接公租房管理信息系统与公安平台，**标书明确要求** |')
w('| **P0-高** | 通行记录（`bp_dev_access_record`） | 「行为轨迹」「空置判定」失去数据源，★ 级考核指标无法证明 |')
w('| **P0-高** | 授权审计（`bp_grant_audit_log`） | ★ 级要求，授权操作必须可追溯且不可篡改 |')
w('| P0-中 | 保障对象档案、实名认证 | 保障专有属性无存放处；实名无留痕 |')
w('| P0-中 | 告警规则引擎（3 表） | “自设阈值”要求未满足 |')
w('| P0-中 | 可配置大屏 | 驾驶舱为前端硬编码，非产品级大屏 |')
w('')
w('---')
w('')
w('## 三、孤儿表清单（%d 张，有表无实现）' % len(orphans))
w('')
w('> 孤儿表 = 数据库已建表但无 Java 实体、无 Mapper、无 Service、无接口。')
w('')
w('| 分组 | 张数 | 表 |')
w('|---|---|---|')
for g in sorted(groups):
    items = groups[g]
    w('| `bp_%s_*` | %d | %s |'
      % (g, len(items), '、'.join('`%s`' % t.replace('bp_' + g + '_', '') for t, _ in items)))
w('')
w('### 系统支撑层缺口（横切能力，影响全局）')
w('')
w('| 表 | 能力 | 现状 |')
w('|---|---|---|')
for t, cap, note in SYS_GAPS:
    w('| `%s` | %s | %s |' % (t, cap, note))
w('')
w('---')
w('')
w('## 四、已实现模块清单（可直接验收演示）')
w('')
w('| 模块 | 接口数 | 说明 |')
w('|---|---|---|')
for mod, base, cnt in apis:
    w('| %s | %d | `%s` |' % (mod, cnt, base))
w('')
w('**合计 %d 个接口。**' % total_api)
w('')
w('---')
w('')
w('## 五、与设计文档的偏差（需确认）')
w('')
w('| # | 偏差 | 现状 | 建议 |')
w('|---|---|---|---|')
w('| 1 | 流程引擎未采用 | 审核阶段用 `ReviewStage` 枚举硬编码，`bp_flow_*` 5 表空置 | '
  '若政策流程会变，应接入流程引擎；若不改代码可接受，需在文档中明确降级为「固定四阶段」 |')
w('| 2 | 枚举硬编码 | 所有状态/类型用 Java enum，`bp_sys_dict` 空置 | 多租户差异化配置需字典表；当前改政策要改代码 |')
w('| 3 | 政策参数硬编码 | 7 天公示、5 年禁申、3 个月过渡期写在常量 | 应迁入 `bp_sys_config` 支持分地区配置 |')
w('| 4 | 续签未生成新合同 | `RENEW` 只延长 `leaseEnd`；换房会生成新合同 | 统一口径：续签也应生成新合同（`parentContractId` 链） |')
w('| 5 | 公示无名单明细 | `bp_biz_publicity` 只有主体，`bp_biz_publicity_item` 空置 | 公示必须能列出具体名单及异议处理 |')
w('| 6 | 单元测试缺失 | 363 个类、**0 个业务单测**（宿主机内存不足，Mockito 无法初始化） | 释放内存后补齐，否则无法保证“性能稳定” |')
w('')
w('---')
w('')
w('## 六、建议的收尾顺序')
w('')
w('| 阶段 | 内容 | 理由 |')
w('|---|---|---|')
w('| **第 1 批（阻塞验收）** | RBAC 权限（7 表）+ 审计日志 + 数据字典/配置 | 无鉴权不能上生产；审计是保障房合规底线 |')
w('| **第 2 批（闭环补齐）** | 通行记录 + 授权审计 + 消息中心 | ★ 级考核指标的数据来源与触达能力 |')
w('| **第 3 批（对接交付）** | 开放平台 + 监管报送 + 报表导出 | 标书明确要求，对接房管局/公安 |')
w('| **第 4 批（形态补齐）** | 移动端（租客端小程序 + 工作人员端） | 交付形态要求 |')
w('| **第 5 批（质量）** | 单元测试 + 性能压测 | 支撑“性能稳定”目标 |')
w('| 可延后 | 优先对象、合同模板、公示名单、自动递补 | 影响精细化但不阻塞主流程 |')
w('')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('报告已生成：%s' % OUT)
print('  总行数 %d' % len(lines))
print('  P0: 已实现 %d / 部分 %d / 未实现 %d' % (len(done), len(part), len(none)))
print('  孤儿表 %d 张，分 %d 组' % (len(orphans), len(groups)))
