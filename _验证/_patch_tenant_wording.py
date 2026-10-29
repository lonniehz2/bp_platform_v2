# -*- coding: utf-8 -*-
"""登录口径去歧义：平台租户码 -> 平台编码（与承租人区分）。"""
import io

def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new in pairs:
        if old in s:
            s = s.replace(old, new)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)

patch(r'..\frontend\src\views\Login.vue', [
    ('平台租户码，如 350600', '平台编码，如 350600'),
    ('请使用平台租户码与账号登录', '请使用平台编码与账号登录'),
    ('输入平台租户码', '输入平台编码'),
    ('租户码是<b>数据隔离标识</b>，不是组织编码。', '平台编码是<b>数据隔离标识</b>，既不是组织编码，也不是承租人。'),
    ('一个租户下可有多级组织；登录后右上角显示你的<b>组织</b>，',
     '一个平台下可有多级组织与承租人；登录后右上角显示你的<b>组织</b>，'),
    ('租户码可在悬停提示中查看。', '平台编码可在悬停提示中查看。'),
    ('登录后右上角显示「组织 · 平台」；租户码可在悬停提示中查看。',
     '登录后右上角显示「组织 · 平台」；平台编码可在悬停提示中查看。')
])

patch(r'..\frontend\src\layout\LayoutRail.vue', [
    (":content=\"'租户：' + (auth.user?.tenantName || '—') + '（' + (auth.user?.tenantId || '—') + '）'\"",
     ":content=\"'平台：' + (auth.user?.tenantName || '—') + '（' + (auth.user?.tenantId || '—') + '）'\"")
])

patch(r'..\frontend\src\layout\LayoutClassic.vue', [
    (":content=\"'租户：' + (auth.user?.tenantName || '—') + '（' + (auth.user?.tenantId || '—') + '）'\"",
     ":content=\"'平台：' + (auth.user?.tenantName || '—') + '（' + (auth.user?.tenantId || '—') + '）'\"")
])

patch(r'..\frontend\src\h5\views\H5Login.vue', [
    ('placeholder="平台租户码"', 'placeholder="平台编码"')
])

patch(r'..\frontend\src\content\help.js', [
    ('输入平台租户码（默认 350600；它是数据隔离标识，不是组织编码）',
     '输入平台编码（默认 350600；它是数据隔离标识，不是组织编码，也不是承租人）')
])
print('wording updated')
