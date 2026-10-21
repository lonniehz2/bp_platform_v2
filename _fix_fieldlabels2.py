# -*- coding: utf-8 -*-
"""① 后端：列注释截断取主名 ② 前端：补计算字段中文名"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ---------- 1) 后端截断 ----------
P = os.path.join(BASE, 'sys', 'service', 'FieldLabelService.java')
s = io.open(P, encoding='utf-8').read()

old = '''                // 去掉注释里的单位/枚举提示，保留主体中文，如「面积(㎡)」→「面积」
                String label = comment.replaceAll("\\\\([^)]*\\\\)", "").trim();
                if (label.isBlank()) {
                    label = comment;
                }'''
new = '''                // 列注释常写成「发放方式：FINANCE 财政直发 / BANK 银行代发」，
                // 作为表单标签只需要冒号前的主名；括号里的单位同理去掉。
                String label = comment;
                int cut = indexOfAny(label, '：', ':', '（', '(');
                if (cut > 0) {
                    label = label.substring(0, cut);
                }
                label = label.trim();
                if (label.isBlank()) {
                    label = comment;
                }'''
assert old in s, '锚点未找到'
s = s.replace(old, new, 1)

s = s.replace('''    private static String toCamel(String snake) {''',
              '''    private static int indexOfAny(String s, char... chars) {
        int best = -1;
        for (char c : chars) {
            int i = s.indexOf(c);
            if (i > 0 && (best < 0 || i < best)) {
                best = i;
            }
        }
        return best;
    }

    private static String toCamel(String snake) {''', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 后端：标签在「：」或「(」处截断')

# ---------- 2) 前端补计算字段 ----------
L = r'D:\Work\业务平台开发\frontend\src\constants\fieldLabels.js'
t = io.open(L, encoding='utf-8').read()

EXTRA2 = {
    'changesOutcome': '变更结果', 'daysToExpire': '距到期天数',
    'durationDays': '公示天数', 'exchangeLimitReached': '已达换房上限',
    'exempt': '是否免收', 'expired': '已失效', 'expiringSoon': '即将到期',
    'finishOverdue': '完工逾期', 'forced': '是否强制',
    'liveWaitDays': '实时轮候天数', 'lockOverdue': '锁定超时',
    'lockRemainHours': '锁定剩余(小时)', 'notified': '已通知',
    'occupyFrom': '占用开始', 'occupyTo': '占用结束', 'occupying': '占用中',
    'ongoing': '进行中', 'overCap': '超出政策上限', 'overdue': '已逾期',
    'overdueCheckout': '退房逾期', 'overdueExit': '退出逾期',
    'overdueNow': '当前逾期', 'periodMet': '公示期已满',
    'phoneMask': '手机号(脱敏)', 'pushed': '已推送',
    'suspectIdle': '疑似空置', 'trusted': '可信', 'abnormal': '异常',
    'usable': '可用', 'idleDays': '连续未开门天数',
    'openTypeName': '开门方式', 'lastOpenTime': '最近开门时间',
    'canRenew': '可续签', 'needPublicity': '需公示', 'publicityDone': '公示已完成',
    'waitlistRank': '轮候名次', 'totalScore': '综合得分',
    'remainAmount': '剩余金额', 'deductAmount': '已抵扣金额',
}

if 'changesOutcome' not in t:
    add = '\n'.join("  %s: '%s'" % (k, v) for k, v in EXTRA2.items())
    t = t.replace('export const FIELD_LABEL = {',
                  'export const FIELD_LABEL = {\n'
                  '  // ---------- 计算/派生字段（非数据库列，需手工维护） ----------\n'
                  + add + ',', 1)
    io.open(L, 'w', encoding='utf-8').write(t)
    print('  ✓ 前端：补 %d 个计算字段中文名' % len(EXTRA2))
