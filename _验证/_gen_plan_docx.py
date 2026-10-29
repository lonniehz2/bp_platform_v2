# -*- coding: utf-8 -*-
"""生成《保障房业态收口与平台底座实施方案》Word 文档。"""
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = os.path.join(os.path.dirname(__file__), '..',
                   '保障房业态收口与平台底座实施方案_V1.0.docx')
ACCENT = RGBColor(0x1F, 0x4E, 0x79)
MUTED = RGBColor(0x60, 0x60, 0x60)

doc = Document()
for section in doc.sections:
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)

# ---------- 基础样式 ----------
normal = doc.styles['Normal']
normal.font.name = '微软雅黑'
normal.font.size = Pt(10.5)
normal._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
normal.paragraph_format.line_spacing = 1.4
normal.paragraph_format.space_after = Pt(4)

for name, size, color in (('Heading 1', 16, ACCENT), ('Heading 2', 13, ACCENT),
                          ('Heading 3', 11.5, RGBColor(0x33, 0x33, 0x33))):
    st = doc.styles[name]
    st.font.name = '微软雅黑'
    st.font.size = Pt(size)
    st.font.color.rgb = color
    st.font.bold = True
    st._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(6)


def h(text, level=1):
    return doc.add_heading(text, level=level)


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


def bullets(items, style='List Bullet'):
    for it in items:
        doc.add_paragraph(it, style=style)


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def table(headers, rows, widths=None, font_size=9.5):
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
    par = cell.paragraphs[0]
    run = par.add_run(text)
    run.font.name = 'Consolas'
    run.font.size = Pt(8.5)
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
    doc.add_paragraph()


def note(text):
    t = doc.add_table(rows=1, cols=1)
    t.style = 'Table Grid'
    cell = t.rows[0].cells[0]
    shade(cell, 'FFF7E6')
    run = cell.paragraphs[0].add_run(text)
    run.font.size = Pt(9.5)
    doc.add_paragraph()


def footer_page_number(section):
    footer = section.footer
    par = footer.paragraphs[0]
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


# ---------- 封面 ----------
for _ in range(4):
    doc.add_paragraph()
p('租赁性保障用房管理平台', bold=True, size=15, color=MUTED,
  align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
title = p('保障房业态收口与平台底座', bold=True, size=28, color=ACCENT,
          align=WD_ALIGN_PARAGRAPH.CENTER)
p('实 施 方 案', bold=True, size=24, color=ACCENT, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
p('V1.0　｜　2026-10-30　｜　待评审', size=11, color=MUTED,
  align=WD_ALIGN_PARAGRAPH.CENTER)
for _ in range(8):
    doc.add_paragraph()

table(['项目', '内容'], [
    ['文档名称', '保障房业态收口与平台底座实施方案'],
    ['版本 / 状态', 'V1.0 / 待评审'],
    ['适用范围', '保障房业态（长租）收口、平台信息维护、平台运营台、品牌与主题'],
    ['明确后置', '多业态（宿舍/网约房/物业/酒店民宿/公寓）方案与开发'],
    ['编制 / 日期', '项目组 / 2026-10-30'],
], widths=[4, 12])

doc.add_page_break()

# ---------- 目录说明 ----------
h('文档说明', 1)
p('本文档用于统一“保障房业态收口 + 平台底座”的范围、口径、实施顺序与验收标准，'
  '作为后续开发、测试、试点与全量推行的依据。文档中确认过的决策不再重复讨论；'
  '“多业态”相关内容整体后置，待保障房业态验收通过后再启动。')
p('阅读对象：项目负责人、产品、开发、测试、平台运营超管、各平台管理员。', color=MUTED)

# ---------- 1 背景与目标 ----------
h('1　背景与目标', 1)
h('1.1　背景', 2)
bullets([
    '现有系统以保障房（长租）业务为主，业务页面、计费、合同、退租等主流程已具备；',
    '登录页与顶部信息存在“租户 / 组织 / 承租人”术语混淆，已统一口径；',
    '平台层缺少信息维护入口，平台生命周期（创建、启停、归档）与平台管理员开通依赖数据库；',
    '品牌、主题、菜单风格尚未平台化，各平台无法体现自身标识；',
    '多业态（宿舍、网约房、物业、酒店民宿、公寓）需求存在，但应在一期稳定后再扩展。',
])
h('1.2　目标', 2)
bullets([
    '把保障房业态的全流程跑到“可演示、可验收、无阻塞缺陷”；',
    '补齐平台底座：平台信息维护、平台运营超管、平台生命周期、管理员账号；',
    '品牌与主题可配置、有默认值，不配置也不影响使用；',
    '为后续多业态扩展预留字段与边界，但本期不实现多业态。',
])
h('1.3　成功标准', 2)
table(['维度', '标准'], [
    ['功能', '保障房主流程（申请→配租→签约→出账→收款→退租）人工走通'],
    ['质量', '一键验收管线 16 项全绿；49 个路由 UI 审计 0 异常；无 P0/P1 缺陷'],
    ['平台底座', '运营超管可创建平台、开通管理员、停用/归档；平台管理员可改名称与品牌'],
    ['体验', '顶部显示“平台名 · 组织”；登录页可按平台展示品牌；浅/深色可用'],
], widths=[3, 13])

# ---------- 2 已确认决策 ----------
h('2　已确认决策（不再讨论）', 1)
table(['序号', '决策项', '结论'], [
    ['1', '顶部展示', '采用 B：平台名 · 组织；悬停显示平台编码与组织'],
    ['2', '平台编码', '不允许修改；仅名称可改（平台管理员）；区域/类型只读'],
    ['3', '平台生命周期', '一级范围只做“平台信息维护”；平台创建/启停/归档由运营超管负责'],
    ['4', '运营超管入口', '独立登录入口 /platform-admin/login'],
    ['5', '平台编码规则', '行政区划 + 序列，创建时生成，永久不可改'],
    ['6', '删除策略', '只允许停用 + 归档，不允许物理删除'],
    ['7', '初始密码', '页面一次性显示；首次登录强制改密'],
    ['8', '品牌/主题维护', '运营超管设初始值；平台管理员可改品牌/主题；区域/类型仍只读'],
    ['9', '用户切换', '平台可配置“允许用户切换浅/深色与菜单风格”，默认允许'],
    ['10', '模板升级', '创建时快照；运营改模板不自动影响存量平台，需手动同步并审计'],
    ['11', '多业态', '本期不开发；平台创建时锁定一个主业态，业态不可变更（字段预留）'],
], widths=[1.3, 4, 11.5])

# ---------- 3 术语与边界 ----------
h('3　术语与边界', 1)
table(['术语', '定义', '出现位置'], [
    ['平台编码', '平台级数据隔离标识（如 350600），不是组织编码、不是承租人', '登录页、顶部悬停'],
    ['平台名称', '平台对外名称，随品牌展示', '顶部、登录页、报表抬头'],
    ['组织', '平台内的行政/运营单元（小区、片区）', '顶部“· 组织”、组织管理'],
    ['承租人 / 租客', '租房子的人，业务对象', '合同、账单缴费人、人员档案'],
    ['业态', '产品解决方案形态（保障房长租为本期唯一启用）', '平台创建时锁定（预留）'],
], widths=[3, 10, 5])
note('禁用词：不再单独使用“租户”，避免与“承租人”混淆；技术字段名可保留 tenant_id。')

# ---------- 4 范围与阶段 ----------
h('4　总体范围与阶段', 1)
table(['阶段', '内容', '状态'], [
    ['P0', '保障房业态收口与验收（只修缺陷，不加功能）', '本期'],
    ['P1', '平台信息维护（平台侧，名称可改）', '本期'],
    ['P2', '平台运营台（超管、平台生命周期、管理员账号）', '本期'],
    ['P3', '品牌与主题（LOGO/标题/主题色/菜单风格/浅深色）', '本期'],
    ['P4', '多业态方案（业态字典、菜单分组排序、功能开关、术语、组织覆盖）', '后置'],
], widths=[2, 12, 3])
p('原则：P0 未通过验收，不启动 P2/P3 的大规模改造；多业态不在一期建表，避免提前迁移。',
  bold=True)

# ---------- 5 P0 ----------
h('5　P0：保障房业态收口与验收', 1)
h('5.1　验收范围', 2)
table(['业务域', '必测要点'], [
    ['保障资格', '申请、审核、轮候、公示、摇号、配租、退房后再次入池'],
    ['合同', '新建/快捷签约、变更、换房、续签、退租、一房一租校验'],
    ['收费', '计费项目、批量出账（跨月折算）、账单、收款、核销、减免、催缴'],
    ['押金', '建档、收取、抵扣、退款、超退/超抵扣拦截'],
    ['抄表', '录入、批量、出账、零用量拦截、IoT 拉取'],
    ['服务', '工单、投诉、走访报告、告警、门禁'],
    ['报表/监管', '报表口径、监管报送（单次 500 条上限及提示）'],
    ['平台能力', '组织、房源、人员、权限、消息、审计'],
], widths=[3, 13])
h('5.2　验收门槛', 2)
bullets([
    '一键验收管线 16 项全部通过；',
    '49 个路由 UI 审计 0 异常（JS 报错、接口 4xx/5xx、异常文案、横向溢出）；',
    '关键流程人工走通：申请→配租→签约→出账→收款→退租；',
    '无 P0/P1 缺陷；P2 缺陷登记，不阻塞上线。',
])
h('5.3　产出物', 2)
bullets([
    '缺陷清单（按 P0/P1/P2 分级）与修复记录；',
    '演示脚本（按角色：受理、合同、财务、房源、运营）；',
    '验收结论：通过 / 有条件通过（附条件与期限）。',
])

# ---------- 6 P1 ----------
h('6　P1：平台信息维护（平台侧）', 1)
h('6.1　页面与字段', 2)
p('入口：系统与数据 → 平台信息。仅平台管理员可进入；平台编码、区域、类型只读。')
table(['字段', '可编辑', '说明'], [
    ['平台编码', '否', '数据隔离标识，创建后不可改'],
    ['平台名称', '是', '保存后刷新会话，顶部名称即时更新'],
    ['平台类型', '否', '按决策只读'],
    ['所属区域', '否', '按决策只读'],
    ['隔离模式', '否', '本期固定 ROW'],
    ['状态', '否', '显示启用/停用/归档；由运营超管控制'],
    ['创建时间', '否', '只读'],
], widths=[3, 2.5, 10])
h('6.2　接口', 2)
code('GET /api/v1/platform/info\nPUT /api/v1/platform/info     # 仅 tenantName')
h('6.3　验收', 2)
bullets([
    '改名后顶部、登录后首页、报表抬头同步；',
    '区域/类型/编码无编辑入口，接口层也拒绝修改；',
    '无平台信息时给出可读错误，不出现 500。',
])

# ---------- 7 P2 ----------
h('7　P2：平台运营台（超管）', 1)
h('7.1　账号与登录', 2)
bullets([
    '独立表 bp_iam_platform_operator，不参与租户数据过滤；',
    '独立入口 #/platform-admin/login，无需输入平台编码；',
    '初始超管由初始化脚本/环境变量创建，页面不提供注册；',
    '首次登录强制改密；连续失败锁定；操作全量审计。',
])
h('7.2　平台生命周期', 2)
table(['操作', '规则'], [
    ['创建', '填名称、区域、联系人；业态本期固定“保障房”并锁定；编码自动生成（行政区划+3位序列）且不可改；同时初始化默认组织「平台」、平台管理员（初始密码一次性显示）、默认角色与菜单'],
    ['修改', '名称、区域、类型、联系人可改；编码不可改'],
    ['停用', '拒绝新登录；现有会话到期失效；数据保留'],
    ['归档', '仅停用后可归档；归档后不可登录；不物理删除；运营可查询'],
    ['恢复', '归档 → 停用（可选），需审计'],
], widths=[2.5, 13])
h('7.3　平台管理员账号', 2)
bullets([
    '新建：用户名（平台内唯一）、姓名、初始密码（页面一次性显示）；',
    '首次登录强制改密；超管可重置密码（同样一次性显示 + 强制改密）；',
    '启用/停用/解锁；每个平台至少保留 1 个启用管理员；',
    '不允许把业务用户直接提升为平台管理员。',
])
h('7.4　页面结构', 2)
code('/platform-admin\n'
     '  ├─ 平台列表（编码/名称/业态/区域/状态/管理员数/创建时间）\n'
     '  ├─ 新建平台\n'
     '  ├─ 平台详情（基本信息 / 管理员账号 / 状态操作）\n'
     '  └─ 运营审计')
h('7.5　接口清单', 2)
table(['方法', '路径', '说明'], [
    ['POST', '/api/v1/platform-admin/auth/login', '超管登录'],
    ['GET/POST', '/api/v1/platforms', '列表 / 创建'],
    ['GET/PUT', '/api/v1/platforms/{id}', '详情 / 修改'],
    ['POST', '/api/v1/platforms/{id}/enable|disable|archive|restore', '状态操作'],
    ['GET/POST', '/api/v1/platforms/{id}/admins', '管理员列表 / 新建'],
    ['POST', '/api/v1/platforms/{id}/admins/{uid}/reset-password|enable|disable|unlock', '账号操作'],
    ['GET', '/api/v1/platform-admin/audits', '运营审计'],
], widths=[2, 9, 5])
h('7.6　安全要求', 2)
bullets([
    '超管接口显式跨租户，使用独立 mapper，不复用带租户过滤的查询；',
    '超管 token 与业务 token 不可串用（独立签发/校验）；',
    '停用/归档二次确认；归档需输入平台编码确认；',
    '审计记录：操作者、时间、平台、动作、前后值。',
])

# ---------- 8 P3 ----------
h('8　P3：品牌与主题（有默认值）', 1)
h('8.1　配置项', 2)
table(['配置项', '默认值', '维护人'], [
    ['LOGO', '系统默认图标', '平台管理员'],
    ['登录页标题', '租赁性保障用房管理平台', '平台管理员'],
    ['登录页副标题', '英文名/口号', '平台管理员'],
    ['主题色（主色/辅助色）', '现有蓝绿', '平台管理员'],
    ['菜单风格', 'rail（现有）', '平台管理员'],
    ['页面配色', '浅色', '平台管理员'],
    ['允许用户切换', '是', '平台管理员'],
], widths=[4.5, 7, 4])
h('8.2　登录页品牌', 2)
bullets([
    '登录前根据平台编码获取公开品牌信息：GET /api/v1/public/platform-branding?code=350600；',
    '取不到或未配置时使用系统默认，保证“零配置可用”；',
    '公开接口只返回品牌相关字段，做频率限制。',
])
h('8.3　主题实现', 2)
bullets([
    '品牌色通过 CSS 变量注入（--brand-primary、--brand-accent 等），不改组件代码；',
    '浅色/深色两套变量 + Element Plus dark；',
    '优先级：平台默认 → 用户偏好（允许时）→ 系统默认；',
    '排查页面写死颜色（图表、状态标签、打印样式）。',
])
h('8.4　验收', 2)
bullets([
    '不做任何配置时，页面与现在一致；',
    '配置后登录页、顶部、主色、按钮风格一致变化；',
    '深色模式下表格、表单、图表可读，无白底黑字冲突。',
])

# ---------- 9 数据模型 ----------
h('9　数据模型', 1)
code('-- P2\n'
     'bp_iam_platform_operator   -- 超管账号（id, username, password_hash, status, ...）\n'
     'bp_iam_tenant              -- + contact_name/contact_phone/deleted/archive_time,\n'
     '                           --   business_type_code（预留，本期固定 BAOZHANG）\n'
     'bp_iam_user                -- + must_change_password, fail_count, locked_until\n'
     'bp_sys_platform_audit      -- 运营审计\n'
     '\n'
     '-- P3\n'
     'bp_iam_tenant_branding     -- logo_file_id, primary_color, accent_color,\n'
     '                           -- login_title, login_subtitle, menu_style,\n'
     '                           -- color_mode, allow_user_switch\n'
     '\n'
     '-- 本期不建（多业态后置）\n'
     '-- bp_sys_solution / solution_menu / solution_feature / solution_label')
note('编码生成：行政区划（如 350600）+ 3 位序列（001…），由序列表或数据库唯一键保证不重复；'
     '创建后编码写入业务表与登录态，禁止修改。')

# ---------- 10 角色权限 ----------
h('10　角色与权限矩阵', 1)
table(['能力', '运营超管', '平台管理员', '普通业务用户'], [
    ['创建/停用/归档平台', '✔', '—', '—'],
    ['修改平台名称', '✔', '✔', '—'],
    ['修改区域/类型/编码', '创建时设定', '—', '—'],
    ['开通/重置平台管理员', '✔', '—', '—'],
    ['修改品牌/主题', '✔', '✔', '—'],
    ['切换浅/深色、菜单风格', '✔', '✔', '视平台开关'],
    ['业务数据（合同/账单等）', '不进入', '本平台', '按角色'],
], widths=[7, 3, 3, 3])

# ---------- 11 验收与测试 ----------
h('11　验收与测试策略', 1)
table(['层级', '内容', '通过标准'], [
    ['自动化', '一键管线 16 项：构建、ID 精度、接口路径、参数接线、显示层、列表、筛选、菜单、权限、并发、数据范围、页面 46、旅程 70、新增功能 12', '全部通过'],
    ['UI 审计', '49 路由：JS 异常、接口错误、异常文案、横向溢出、空表提示', '0 异常'],
    ['关键流程', '申请→配租→签约→出账→收款→退租；批量出账/催缴；押金超退拦截', '人工走通并留截图'],
    ['平台底座', '创建平台→管理员首次登录改密→改名→停用→归档', '全链路通过'],
    ['品牌主题', '零配置、配置后、深色模式三组截图', '一致且可读'],
], widths=[2.5, 10.5, 3])
p('缺陷分级：P0 阻塞（无法演示/数据错误）、P1 严重（主流程需绕过）、P2 一般（体验问题）；'
  'P0/P1 清零方可进入试点。', color=MUTED)

# ---------- 12 推行计划 ----------
h('12　推行计划', 1)
h('12.1　里程碑', 2)
table(['里程碑', '内容', '完成标志'], [
    ['M1', 'P0 保障房收口', '管线全绿、关键流程走通、缺陷清单确认'],
    ['M2', 'P1 平台信息维护 + 顶部 B', '改名生效、只读项锁定'],
    ['M3', 'P2 运营超管与平台生命周期', '新建→登录改密→停用→归档全链路'],
    ['M4', 'P3 品牌与主题', '零配置可用、配置生效、深色可读'],
    ['M5', '试点与全量', '试点平台 1 周无 P0/P1；全量上线'],
], widths=[2, 9, 5])
h('12.2　试点与全量', 2)
bullets([
    '试点：选 1 个平台 + 1 个组织，覆盖受理、合同、财务、房源四个角色；',
    '试点周期：1 周；收集问题按 P0/P1/P2 处理；',
    '全量：按平台分批开通，先停旧入口再切新入口，保留回滚窗口；',
    '培训：平台管理员 1 次集中培训 + 操作手册 + 演示视频；业务用户按角色发操作卡。',
])
h('12.3　上线检查清单', 2)
bullets([
    '数据库备份与回滚脚本就绪；',
    '运营超管账号已创建并完成首次改密；',
    '各平台管理员初始密码已一次性交付并完成改密；',
    '平台停用/归档演练完成；',
    '监控与日志（登录失败、接口 5xx、审计）已接入；',
    '客服/运维联系人、问题上报通道明确。',
])

# ---------- 13 风险 ----------
h('13　风险与应对', 1)
table(['风险', '影响', '应对'], [
    ['超管与业务会话串用', '越权/数据泄露', '独立 token 前缀与会话校验；联调覆盖'],
    ['编码生成重复', '平台创建失败/数据错乱', '唯一键 + 序列表事务；创建失败可重试'],
    ['归档误操作', '平台不可登录', '二次确认 + 输入编码；保留恢复路径'],
    ['深色模式兼容', '页面可读性差', '写死颜色排查清单；逐页截图验收'],
    ['品牌上传异常', '登录页空白', '默认回退；文件类型/大小校验'],
    ['多业态提前侵入', '范围失控', '本期只预留字段，不建 solution 表'],
], widths=[5, 5, 6])

# ---------- 14 后置 ----------
h('14　后置：多业态扩展（本期不开发）', 1)
p('以下内容已完成方案讨论，待保障房业态验收通过后启动：')
bullets([
    '业态字典与解决方案模板（版本化）；',
    '菜单分组、排序、名称、显隐的可配置化；',
    '功能开关、术语覆盖、页面变体（房态、网约房核验、保洁等）；',
    '平台创建时锁定主业态（本期仅预留字段）；',
    '组织级业态覆盖（仅多业态运营需要时开启）。',
])
note('冻结原则：多业态不在一期建表、不改现有菜单结构，避免与保障房收口相互干扰。')

# ---------- 15 附录 ----------
h('15　附录：当前基础与待办确认', 1)
h('15.1　当前基础', 2)
bullets([
    '保障房主流程页面与接口已具备，一键验收管线 16 项；',
    '顶部已统一为“平台名 · 组织”，登录页已改版并区分平台/组织/承租人；',
    '平台信息维护的接口与页面草稿已具备，需按“区域/类型只读”调整；',
    '计费已支持逐月折算、重复出账拦截、历史账单重算。',
])
h('15.2　待确认', 2)
bullets([
    '归档平台的数据保留期限（建议 1 年，到期归档离线存储）；',
    '平台 LOGO 是否允许 SVG（建议允许，但需防脚本注入）；',
    '深色模式是否覆盖打印/导出样式（建议导出保持浅色）。',
])

footer_page_number(doc.sections[0])
doc.save(OUT)
print('saved:', os.path.abspath(OUT))
