# -*- coding: utf-8 -*-
"""生成《业务系统多语言版本可行性评估与实施路径》Word 报告。"""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(BASE, '业务系统多语言版本可行性评估与实施路径_V1.0.docx')
ACCENT = RGBColor(0x1F, 0x4E, 0x79)
MUTED = RGBColor(0x60, 0x60, 0x60)
RED = RGBColor(0xB0, 0x30, 0x30)

doc = Document()
for section in doc.sections:
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(1.9)
    section.bottom_margin = Cm(1.7)

normal = doc.styles['Normal']
normal.font.name = '微软雅黑'
normal.font.size = Pt(10.5)
normal._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
normal.paragraph_format.line_spacing = 1.4
normal.paragraph_format.space_after = Pt(4)

for name, size, color in (('Heading 1', 15.5, ACCENT), ('Heading 2', 12.5, ACCENT),
                          ('Heading 3', 11, RGBColor(0x33, 0x33, 0x33))):
    st = doc.styles[name]
    st.font.name = '微软雅黑'
    st.font.size = Pt(size)
    st.font.color.rgb = color
    st.font.bold = True
    st._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(5)


def h(text, level=1):
    doc.add_heading(text, level=level)


def p(text='', bold=False, color=None, size=10.5, align=None, italic=False):
    par = doc.add_paragraph()
    run = par.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color
    if align is not None:
        par.alignment = align
    return par


def bullets(items):
    for it in items:
        doc.add_paragraph(it, style='List Bullet')


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def table(headers, rows, widths=None, font_size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, head in enumerate(headers):
        hdr[i].text = ''
        run = hdr[i].paragraphs[0].add_run(head)
        run.bold = True
        run.font.size = Pt(font_size)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(hdr[i], '1F4E79')
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ''
            run = cells[i].paragraphs[0].add_run(str(val))
            run.font.size = Pt(font_size)
    if widths:
        total = sum(widths)
        max_w = 16.4
        if total > max_w:
            widths = [w * max_w / total for w in widths]
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return t


def code(text):
    t = doc.add_table(rows=1, cols=1)
    t.style = 'Table Grid'
    cell = t.rows[0].cells[0]
    shade(cell, 'F2F5F9')
    run = cell.paragraphs[0].add_run(text)
    run.font.name = 'Consolas'
    run.font.size = Pt(8.5)
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
    doc.add_paragraph()


def note(text, fill='FFF7E6'):
    t = doc.add_table(rows=1, cols=1)
    t.style = 'Table Grid'
    cell = t.rows[0].cells[0]
    shade(cell, fill)
    run = cell.paragraphs[0].add_run(text)
    run.font.size = Pt(9.5)
    doc.add_paragraph()


def footer_page(section):
    par = section.footer.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.add_run('第 ')
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), 'PAGE')
    run = OxmlElement('w:r')
    txt = OxmlElement('w:t')
    txt.text = '1'
    run.append(txt)
    fld.append(run)
    par._p.append(fld)
    par.add_run(' 页')


# ---------------- 封面 ----------------
for _ in range(5):
    doc.add_paragraph()
p('租赁性保障用房管理平台', bold=True, size=14, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
p('多语言版本可行性评估', bold=True, size=28, color=ACCENT, align=WD_ALIGN_PARAGRAPH.CENTER)
p('与实施路径', bold=True, size=22, color=ACCENT, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
p('Web · H5 · APP / 小程序 · 第三方 API · IoT 设备管理平台', size=11,
  color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
p('V1.0　｜　2026-10-31', size=11, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
for _ in range(6):
    doc.add_paragraph()

table(['项目', '内容'], [
    ['评估对象', '现有保障房长租业务系统（Web + H5）及后续移动端、第三方接口'],
    ['评估范围', '界面文案、后端消息、业务主数据、合同/通知、开放 API、IoT 接口'],
    ['建议基线语言', '简体中文 zh-CN（源语言）+ 英语 en-US（第一目标语言）'],
    ['结论', '技术可行，属于中等偏大改造；主要成本在存量文案抽取、业务数据翻译和移动端/第三方适配'],
], widths=[3.5, 13])
doc.add_page_break()

# ---------------- 0 结论 ----------------
h('0　执行结论', 1)
p('可行，但不是“加一个语言切换按钮”那么简单。', bold=True, size=12, color=RED)
p('现有系统没有国际化（i18n）基础设施，中文文案分散在前端页面、后端异常、枚举字典、'
  '业务主数据、合同模板、通知模板、帮助文档和报表中。直接逐页翻译会形成多份难以维护的副本，'
  '也会在移动端和第三方接口上重复出现。')
p('建议按“先基础设施、再业务模块、最后移动端与外部接口”的顺序实施；'
  '第一阶段只承诺 zh-CN + en-US，数据模型和接口按多语言扩展设计，后续增加语言不再改代码。')

table(['判断项', '结论'], [
    ['技术可行性', '高。Spring Boot / Vue 3 均有成熟国际化方案，现有 API 已有稳定业务码，适合扩展'],
    ['改造性质', '中等偏大。不是重写，但需要全量字符串治理和数据模型增补'],
    ['最大难点', '业务主数据/合同/公告的人工翻译与版本管理，不是框架接入'],
    ['建议首期范围', '后台 Web + H5 的 zh-CN/en-US；API 支持 Accept-Language；IoT 保持语言中立'],
    ['预计周期', '4–6 个月（4–6 人团队，含翻译与验收）；仅做英文界面约 6–8 周'],
], widths=[4, 12])

note('关键原则：代码、枚举、设备指令、金额、日期、单位保持语言中立；'
     '只翻译“给人看的文字”。合同、公告、用户姓名等法律/个人内容必须人工确认，不能静默机器翻译。')

# ---------------- 1 边界与假设 ----------------
h('1　评估边界与假设', 1)
h('1.1　评估边界', 2)
bullets([
    '现有 Web 管理端、租客 H5、后端 API、数据库、帮助文档；',
    '后续移动端 APP / 微信小程序（当前仓库未发现 APP/小程序工程，仅有 H5）；',
    '第三方平台开放 API、IoT 设备管理平台及其回调/指令；',
    '不包含硬件固件、IoT 厂商内部系统改造。',
])
h('1.2　语言假设', 2)
p('首期建议 zh-CN + en-US。若目标市场包含港澳台、东南亚或共建“一带一路”国家，'
  '再按优先级增加 zh-Hant、vi、lo、my、th 等；阿拉伯语/希伯来语涉及 RTL，'
  '需要额外的布局改造，不建议与首期同时做。')
table(['语言', '建议阶段', '说明'], [
    ['zh-CN', 'P1', '源语言、默认语言、回退语言'],
    ['en-US', 'P1', '第一目标语言，界面 + 合同/通知 + 帮助'],
    ['zh-Hant', 'P2', '术语转换为主，可用翻译记忆库'],
    ['vi / lo / my / th', 'P3', '按项目所在国政策与租客结构决定'],
    ['ar / he', '暂缓', 'RTL 布局、字体、表单方向需专项改造'],
], widths=[3, 4, 9])

# ---------------- 2 现状盘点 ----------------
h('2　现状盘点', 1)
p('以下数据来自当前代码仓库静态扫描（2026-10-31）。')
table(['层面', '现状', '对多语言的影响'], [
    ['前端 Web', '108 个 .vue/.js 文件，104 个含中文，共约 44,311 个中文字符；'
                 '无 vue-i18n 依赖', '页面、表格列、按钮、提示、枚举、菜单全部硬编码，需逐项抽 key'],
    ['前端 H5', '8 个 H5 页面，约 453 个中文字符；独立路由与视图', '与 Web 重复维护，需共享语言包'],
    ['后端 Java', '690 个 Java 文件，587 个含中文，约 63,006 个中文字符；'
                  '无 MessageSource / LocaleResolver / Accept-Language 处理', '异常、校验、日志、枚举标签均为中文'],
    ['错误码', '已有稳定业务码 BPxxxxx，但 ErrorCode 自带中文 message', '业务码可复用；message 需改为按 locale 解析'],
    ['数据库', '业务表普遍只有单语 name/title/content 字段；未见翻译表', '组织、房源、收费项目、公告、模板无法按语言展示'],
    ['合同/通知', '模板与正文为中文单版本', '法律文本需按语言独立版本、独立审批'],
    ['帮助文档', '在线帮助约 5,207 个中文字符；Word/PDF 为中文', '需按语言维护内容与截图'],
    ['移动端', '当前仅有 H5，未发现 APP/小程序工程', '可在新建时直接采用共享语言包，避免二次改造'],
    ['第三方/IoT', 'REST + JSON，业务码稳定；错误 message 为中文；无 locale 协商', '机器对机器可不用语言，但人工排障/运营界面需要本地化'],
], widths=[3, 8.5, 4.5])

h('2.1　成熟度评分', 2)
table(['维度', '现状（1 差–5 好）', '改造难度', '说明'], [
    ['框架与工程', '1', '中', '无 i18n 依赖、无语言包、无语言切换'],
    ['界面文案', '1', '中', '44k 中文字符，46 个功能页'],
    ['后端消息', '1', '中', 'ErrorCode/校验/异常均为中文'],
    ['业务数据', '1', '高', '名称、地址、公告、模板只有单语'],
    ['API 契约', '3', '低–中', '已有稳定 code；缺 messageKey/locale 协商'],
    ['移动端/H5', '1', '中', 'H5 文案独立硬编码；APP/小程序待建'],
    ['文档/法律文本', '1', '高', '合同、公示、帮助均需人工翻译与审校'],
], widths=[3, 3.5, 3, 6.5])

h('2.2　已有有利条件', 2)
bullets([
    '前后端分离，API 边界清晰，适合在网关/过滤器统一处理语言；',
    '业务错误码已稳定，机器调用方可以不依赖 message；',
    '枚举多使用英文 code（如 EFFECTIVE、UNPAID），数据库不需要把枚举值改成中文；',
    'Vue 3 + Element Plus 有成熟 locale 包，后端 Spring 有 MessageSource；',
    '已有自动化验收管线，适合增加“缺失 key / 伪语言 / 接口语言”检查。',
])

# ---------------- 3 分层模型 ----------------
h('3　多语言分层模型', 1)
p('不要把所有中文都当成同一类问题。建议分为四层，分别制定策略和验收标准。')
table(['层级', '内容', '策略', '优先级'], [
    ['T1 界面与系统消息', '按钮、菜单、表头、提示、校验、异常、枚举标签', 'key + 语言包，随代码发布', '必须'],
    ['T2 业务字典/主数据', '组织、房源、收费项目、规则、设备、公告标题', '翻译表/多语字段，后台维护', '必须'],
    ['T3 用户生成内容', '承租人姓名、备注、投诉正文、上传附件', '默认原文；按需人工翻译/摘要', '可选'],
    ['T4 法律与正式文本', '合同、公示、通知、政策、帮助文档', '按语言独立版本，法务/业务审核', '必须但独立流程'],
], widths=[4, 6.5, 4.5, 2])
note('T3 不能静默机器翻译后展示给租客或监管方；如需翻译，必须标注“译文仅供参考”并保留原文。')

# ---------------- 4 目标架构 ----------------
h('4　目标架构', 1)
h('4.1　总体链路', 2)
code('''浏览器 / H5 / APP / 小程序
        │  Accept-Language: zh-CN,en;q=0.9
        │  X-Locale: en-US（可选，优先级更高）
        ▼
   API 网关 / LocaleFilter
        │  解析：用户偏好 > 平台默认 > 请求头 > zh-CN
        ▼
   Service / MessageSource / 字典服务
        │  code + messageKey + args（语言中立）
        ▼
   JSON 响应：code / messageKey / message(本地化) / data
        │
        ├── Web/H5：vue-i18n 语言包
        ├── APP/小程序：共享同一套 key 语言包
        └── 第三方/IoT：只消费 code / 业务字段，忽略 message''')

h('4.2　前端 Web', 2)
bullets([
    '引入 vue-i18n（Composition API）与 Element Plus 官方 locale、dayjs locale；',
    '按领域拆分语言包：common、contract、finance、energy、asset、service、help；',
    '路由 meta 使用 titleKey，菜单由后端返回 titleKey + 当前语言 title；',
    '`fieldLabels.js` / `enums.js` 改为“code → i18n key”，不直接存中文；',
    '语言切换不刷新页面；选择存 localStorage，并同步到用户偏好；',
    '日期、金额、面积、电话号码使用 Intl/dayjs 格式化，不手工拼接；',
    '语言包懒加载，避免首屏体积膨胀；缺失 key 回退 zh-CN 并上报。',
])
code('''// 推荐：模板只引用 key
<el-table-column :label="$t('contract.field.monthlyRent')" />
<el-tag>{{ $t(`enum.contractStatus.${row.contractStatus}`) }}</el-tag>

// 不推荐：在模板里写中文或拼接
<el-table-column label="月租金" />
<el-tag>{{ row.contractStatus === 'EFFECTIVE' ? '履约中' : '已终止' }}</el-tag>''')

h('4.3　后端', 2)
bullets([
    '新增 LocaleContext（TransmittableThreadLocal，和 TenantContext 同模式），'
    'LocaleFilter 解析 Accept-Language / X-Locale，finally 清理；',
    '新增 MessageSource：messages_zh_CN.properties、messages_en_US.properties；',
    'ErrorCode 只保留 code/httpStatus，message 改为 messageKey；'
    'R 增加 messageKey、args（可选），message 按 locale 解析；',
    'Bean Validation 的 message 改为 `{error.xxx}`，由 MessageSource 解析；',
    '枚举标签从 EnumLabels 迁到字典服务，按 locale 返回；',
    '日志统一英文（或中文 + 稳定 code），不随请求语言变化，便于检索。',
])
code('''GET /api/v1/contracts/123
Accept-Language: en-US

{
  "code": "BP40001",
  "message": "The current status does not allow this operation.",
  "messageKey": "error.state_conflict",
  "args": [],
  "data": null,
  "timestamp": 1793423168074
}''')
note('兼容策略：保留 message 字段并本地化，新增 messageKey/args 为增量字段；'
     '现有客户端不受影响，新客户端可只用 code + messageKey 做多语言。')

h('4.4　数据模型', 2)
p('建议采用“默认字段 + 翻译表”的混合方案，而不是给每张表加 name_en/name_vi 列。')
code('''sys_i18n_text (
  id            bigint primary key,
  tenant_id     varchar(32),
  resource_type varchar(64),   -- org / space / house / fee_item / notice / ...
  resource_id   bigint,
  field         varchar(64),   -- name / title / content / address ...
  locale        varchar(16),   -- en-US / zh-Hant ...
  text          longtext,
  status        varchar(16),   -- DRAFT / REVIEWED / PUBLISHED
  updated_by    bigint,
  updated_at    datetime,
  unique key uk_i18n (tenant_id, resource_type, resource_id, field, locale)
)''')
bullets([
    '主表保留中文默认字段，作为回退和默认搜索字段；',
    '翻译表按需存储其他语言，未翻译时回退默认语言；',
    '公告/通知/合同模板增加 locale、version、status，正式文本独立审批；',
    'person 姓名、证件等不做自动翻译；地址拆分为结构化字段，英文按目标国格式渲染；',
    '搜索：默认搜索中文主字段；英文搜索可检索翻译表，或后续增加全文索引。',
])
table(['方案', '优点', '缺点', '建议'], [
    ['每表加 name_en 列', '查询简单', '语言一多就爆炸；DDL 频繁', '不推荐'],
    ['JSON 字段 name_i18n', '灵活、无需新表', '索引/检索/审核弱', '仅适合小配置'],
    ['统一翻译表', '扩展语言不改表；可审核', '联表/缓存稍复杂', '推荐'],
], widths=[4, 5, 5, 2])

h('4.5　第三方 API 与 IoT', 2)
p('机器对机器接口不需要“翻译 JSON”，需要的是稳定的 code、明确的字段语义和可本地化的错误目录。')
table(['场景', '建议'], [
    ['入站 API', '支持 Accept-Language；响应带 Content-Language；错误含 code/messageKey/message/args'],
    ['OpenAPI 文档', '字段描述双语或按语言生成两套文档；示例同时给 code 与 messageKey'],
    ['出站 IoT 指令', '只用 deviceId/pointId/commandCode/数值/ISO 时间/单位，不传中文标签'],
    ['IoT 回调/告警', 'alarmCode + params + 设备 ID；不传翻译后的告警文案'],
    ['厂商错误', '厂商 code → 内部 code + i18n key 映射；原始 message 只入日志/诊断字段'],
    ['签名/幂等', 'locale 头不参与签名 canonicalization；重试不受语言影响'],
    ['SDK', '错误码目录 + 各语言消息资源；示例代码不硬编码中文'],
], widths=[4, 12])
code('''// IoT 告警：语言中立
{
  "eventId": "evt-20261031-001",
  "eventType": "DEVICE_ALARM",
  "deviceId": "LOCK-00123",
  "alarmCode": "DOOR_OPEN_TIMEOUT",
  "params": { "seconds": 300 },
  "occurredAt": "2026-10-31T10:15:30+08:00"
}
// 运营端按当前语言显示：
// zh-CN：门长时间未关闭（300 秒）
// en-US：Door left open too long (300 s)''')
note('不要把中文设备名、楼栋名、告警文案写进 IoT 指令或回调；这些属于主数据，'
     '应通过 ID 关联并在展示层本地化。')

h('4.6　H5 / APP / 小程序', 2)
table(['端', '策略'], [
    ['H5', '与 Web 共用语言包包（npm 私有包/JSON），登录后按用户偏好；无需重新发版即可更新文案'],
    ['APP', '原生/Flutter/uni-app 共用 key 目录；语言包可热更新；系统语言变化时可提示切换'],
    ['小程序', '包体积敏感：主包只放 zh-CN，en-US 放分包/按需下载；页面标题/菜单用服务端 titleKey'],
    ['推送/短信', '服务端按接收人 locale 渲染模板；模板存多语言版本，不把翻译放客户端'],
    ['应用商店', '名称、简介、截图、隐私政策按语言分别维护'],
], widths=[3, 13])
note('移动端最容易被忽略的是：推送、短信、应用商店文案、隐私政策、离线缓存。'
     '这些都不在页面语言包里，需要单独的翻译与发布流程。')

# ---------------- 5 实施路径 ----------------
h('5　实施路径', 1)
p('建议分 6 个阶段，先做“可验证的纵向切片”，再批量铺开。')
table(['阶段', '周期', '主要内容', '交付/验收'], [
    ['P0 盘点与设计', '2 周', '字符串清单、语言范围、术语表、key 规范、技术选型、试点模块', '评估报告、规范、试点方案'],
    ['P1 基础设施', '4–6 周', 'LocaleFilter/MessageSource、R 增加 messageKey、vue-i18n、Element locale、语言开关', '中英文切换、错误消息双语、CI 缺失 key 检查'],
    ['P2 业务模块', '8–12 周', '按合同/收费/房源/服务/系统分批抽 key；字典与主数据翻译；帮助/PDF', '46 个页面双语、核心旅程双语'],
    ['P3 移动端', '4–6 周', 'H5 共享语言包；APP/小程序接入；推送/短信模板', 'H5/APP/小程序语言切换与回退'],
    ['P4 外部接口', '3–4 周', '开放 API 错误目录、OpenAPI 双语文档、IoT code 映射、SDK', '接口语言测试、厂商联调'],
    ['P5 验收与推广', '3–4 周', '伪语言、视觉回归、法务审校、试点租户、上线', '验收报告、翻译运维流程'],
], widths=[3, 2.5, 7.5, 4])
p('总周期约 4–6 个月（4–6 人团队）。如果只做“管理端英文界面 + 英文错误消息”，'
  '可压缩到 6–8 周；但合同、公告、帮助、移动端和第三方接口仍需另排期。', color=MUTED)

h('5.1　推荐的首个纵向切片', 2)
p('不要从“全部页面”开始。建议选一条完整链路，验证架构和翻译流程：')
code('''登录 → 工作台 → 合同列表/详情 → 账单列表/详情 → 错误提示 → 帮助页
要求：切 en-US 后整条链路无中文残留；错误消息、枚举、金额/日期格式正确；
      缺失 key 有回退与日志；刷新后语言保持。''')
p('这条链路同时覆盖：菜单、表格、表单、枚举、金额、日期、异常、帮助和权限，'
  '能最早暴露 key 设计、布局变长、后端消息等问题。')

h('5.2　分批策略', 2)
table(['批次', '模块', '说明'], [
    ['第 1 批', '登录、工作台、合同、账单', '高频、闭环、可演示'],
    ['第 2 批', '收费、押金、补贴、能耗', '金额/单位/公式多，需财务审校'],
    ['第 3 批', '房源、人员、申请、配租', '主数据多，需翻译表'],
    ['第 4 批', '服务、设备、报表、系统', '长尾页面，可并行'],
], widths=[3, 6, 7])

# ---------------- 6 工作量 ----------------
h('6　工作量与成本估算', 1)
p('以下为工程量级估算，实际取决于目标语言数量、翻译方式和法务要求。')
table(['工作项', '人周', '说明'], [
    ['P0 盘点/规范/试点设计', '4–6', '字符串扫描、key 规范、术语表'],
    ['后端 i18n 基础设施', '4–6', 'Locale、MessageSource、错误码、校验'],
    ['前端 Web 基础设施', '4–6', 'vue-i18n、Element、菜单、格式化'],
    ['Web 全量文案抽取', '10–14', '46 个页面、44k 中文字符'],
    ['业务数据/字典翻译', '8–12', '组织、房源、收费项目、公告、模板'],
    ['H5/APP/小程序', '6–9', '共享语言包、推送/短信、商店文案'],
    ['开放 API/IoT 适配', '4–6', '错误目录、OpenAPI、厂商 code 映射'],
    ['帮助/合同/PDF/法务', '6–10', '按语言出正式版本，需审校'],
    ['测试/验收/上线', '6–8', '伪语言、视觉回归、双语言旅程'],
], widths=[6, 4, 6])
p('合计约 52–77 人周（约 12–18 人月）。5 人团队并行约 4–6 个月；'
  '若首期只做英文界面和系统消息，约 12–18 人周。', color=MUTED)
p('翻译成本另计：按 3,000–5,000 个 key、约 2–3 万字估算，'
  '英语翻译 + 审校通常为数万元级；合同/政策/法律文本需单独报价。', color=MUTED)

# ---------------- 7 风险 ----------------
h('7　主要风险与对策', 1)
table(['风险', '影响', '对策'], [
    ['存量文案隐藏深', '漏翻、返工', 'AST/正则扫描 + 运行时缺失 key 上报 + 页面巡检'],
    ['字符串拼接/复数', '英文语序错误', 'ICU MessageFormat；禁止手工拼接句子'],
    ['布局变长', '按钮溢出、表格错位', '英文 1.3–1.5 倍长度预算；伪语言 `en-XA` 视觉回归'],
    ['业务数据翻译质量', '租客/监管误解', '术语表 + 业务审校；法律文本法务签字'],
    ['用户内容误译', '隐私/名誉风险', '默认不翻译；译文标注“仅供参考”'],
    ['数据库改造风险', '查询/性能/迁移', '只增表不删列；默认字段回退；缓存翻译'],
    ['API 兼容性', '第三方调用失败', 'code 不变；messageKey/args 增量；版本化文档'],
    ['IoT 厂商限制', '指令/告警不一致', '语言中立 payload；code 映射表；联调沙箱'],
    ['移动端包体积', '小程序超限', '分包/按需下载；主包只留默认语言'],
    ['翻译运维断档', '新功能又变中文', 'key 必须进 TMS；CI 禁止硬编码中文'],
], widths=[4, 5, 7])
note('最大的风险不是技术，而是“没有把翻译纳入研发流程”。如果允许开发者继续在模板里写中文，'
     '多语言版本会在 2–3 个迭代后重新退化。')

# ---------------- 8 验收 ----------------
h('8　验收标准', 1)
bullets([
    '切换 zh-CN/en-US 不刷新页面，刷新后保持；',
    '46 个功能页无中文残留（允许业务数据未翻译，但需回退并标识）；',
    '错误响应同时含 code、messageKey、本地化 message、args；',
    '同一业务错误在两种语言下 code 相同、message 不同；',
    '金额、日期、面积、电话格式符合 locale；',
    '合同/公告/通知按语言出正式版本，审批记录可追溯；',
    'H5/APP/小程序语言切换、系统语言跟随、离线回退正常；',
    'IoT 指令/回调 payload 无中文标签，厂商 code 映射完整；',
    'OpenAPI 文档双语，第三方按 code 处理错误；',
    'CI 检查：缺失 key、硬编码中文、伪语言布局、接口语言。',
])

# ---------------- 9 待决策 ----------------
h('9　需要业务方先确认的事项', 1)
table(['决策项', '选项', '建议'], [
    ['首期语言', '仅英文 / 中英 + 东南亚语言', 'zh-CN + en-US'],
    ['合同与政策', '机器翻译 / 人工翻译+法务', '人工翻译+法务签字'],
    ['用户内容', '不翻译 / 人工翻译 / 机器翻译+标识', '默认不翻译'],
    ['租户语言', '平台统一 / 租户可配置默认语言', '租户可配置，用户可覆盖'],
    ['翻译工具', 'Excel / TMS（Crowdin、Phrase、Lokalise）', 'TMS + 术语表'],
    ['移动端形态', 'H5 优先 / APP / 小程序', '先 H5，APP/小程序按业务优先级'],
    ['上线方式', '一次性 / 按模块灰度', '按模块灰度，先试点租户'],
], widths=[4, 7, 5])

# ---------------- 10 建议 ----------------
h('10　建议的下一步', 1)
bullets([
    '先做 2 周 P0：确认语言范围、术语表、key 规范，选“登录→合同→账单”做试点；',
    'P1 先改后端错误契约和前端语言开关，不要先批量翻译页面；',
    '用伪语言跑一遍布局，提前发现英文变长问题；',
    '把“禁止硬编码中文”加入 CI，否则无法长期维持；',
    '移动端和 IoT 接口在 P1 就确定“语言中立”规范，避免后期改协议。',
])

# ---------------- 附录 ----------------
h('附录 A　API 多语言契约建议', 1)
code('''请求：
Accept-Language: en-US,en;q=0.9
X-Locale: en-US            # 可选，优先级高于 Accept-Language
Authorization: Bearer ...

响应：
Content-Language: en-US
{
  "code": "BP30001",
  "message": "Resource not found.",
  "messageKey": "error.not_found",
  "args": ["contract"],
  "data": null,
  "timestamp": 1793423168074
}''')
bullets([
    '第三方系统只依据 code 做分支，不解析 message；',
    'messageKey 稳定、可读、可翻译；args 用于参数化；',
    'locale 头不参与签名，避免签名校验因语言失败；',
    '错误码目录随 OpenAPI 发布，新增 code 必须登记。',
])

h('附录 B　翻译 key 命名规范', 1)
code('''common.action.save
common.field.status
contract.field.monthlyRent
contract.status.EFFECTIVE
finance.bill.status.UNPAID
energy.allocation.operatorBear
error.state_conflict
error.not_found
help.contract.sign.step1''')
bullets([
    '按“领域.对象.字段/动作”命名，不用中文拼音；',
    '枚举 key 与数据库 code 对齐，不翻译 code；',
    '一个 key 只表达一个含义，不复用多义词；',
    '删除 key 前先查引用；保留 deprecated 标记；',
    '翻译文案带上下文/截图，避免“确定/确认”混淆。',
])

h('附录 C　上线检查清单', 1)
table(['检查项', '通过标准'], [
    ['语言切换', '不刷新、即时生效、刷新保持'],
    ['缺失 key', '回退默认语言、记录日志、不显示 key 本身'],
    ['后端消息', '两种语言均返回、code 一致'],
    ['数据回退', '未翻译主数据展示默认语言并有标识'],
    ['布局', '英文/伪语言无溢出、无截断'],
    ['金额/日期', '按 locale 格式化，时区正确'],
    ['合同/公告', '按语言版本审批、归档'],
    ['移动端', '系统语言跟随、应用内切换、推送模板正确'],
    ['IoT', '指令/回调无中文标签，错误映射完整'],
    ['第三方', 'OpenAPI/SDK/错误目录可用'],
], widths=[5, 11])

footer_page(doc.sections[0])
doc.save(OUT)
print('saved:', os.path.abspath(OUT))
