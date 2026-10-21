# -*- coding: utf-8 -*-
"""把硬编码政策参数改为读配置（公示天数/禁申年限/过渡期/换房次数/冻结时长/申诉期限）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
done = []


def patch(rel, pairs, inject_after=None, inject=None, must_miss='configService'):
    path = os.path.join(BASE, rel)
    s = io.open(path, encoding='utf-8').read()
    if must_miss and must_miss in s and inject is None:
        print('  - 已接入 %s' % os.path.basename(path))
        return
    ok = True
    for old, new in pairs:
        if old not in s:
            print('  !! 锚点缺失 %s' % os.path.basename(path))
            ok = False
            break
        s = s.replace(old, new, 1)
    if not ok:
        return
    if inject and inject_after and inject_after in s and 'ConfigService' not in s:
        s = s.replace(inject_after, inject + '\n' + inject_after, 1)
    io.open(path, 'w', encoding='utf-8').write(s)
    done.append(os.path.basename(path))
    print('  ✓ %s' % os.path.basename(path))


FIELD = '''
    /** 系统参数（政策参数可配置） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.sys.service.ConfigService configService;

    private int cfgInt(String key, int def) {
        return configService == null ? def : configService.getInt(key, def);
    }

    private java.math.BigDecimal cfgDec(String key, String def) {
        return configService == null ? new java.math.BigDecimal(def)
                : configService.getDecimal(key, new java.math.BigDecimal(def));
    }
'''

IMPORT = 'import com.yundao.bp.sys.constant.ConfigKeys;\n'

# ---------- 1) 公示天数 ----------
patch(r'..\biz\service\impl\PublicityServiceImpl.java'.replace('..\\', ''),
      [], must_miss=None) if False else None

p = os.path.join(BASE, r'biz\service\impl\PublicityServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'ConfigKeys' not in s:
    s = s.replace('import com.yundao.bp.common.tenant.TenantContext;',
                  'import com.yundao.bp.common.tenant.TenantContext;\n' + IMPORT.strip(), 1)
    s = s.replace('''    private static final Logger log = LoggerFactory.getLogger(PublicityServiceImpl.class);

    /** 配租公示最短公示期（自然日） */
    private static final int MIN_ALLOCATION_DAYS = 7;''',
                  '''    private static final Logger log = LoggerFactory.getLogger(PublicityServiceImpl.class);

    /** 配租公示最短公示期默认值（可被系统参数覆盖） */
    private static final int DEFAULT_MIN_ALLOCATION_DAYS = 7;''' + FIELD)
    s = s.replace('''        if (tp == PublicityType.ALLOCATION && days < MIN_ALLOCATION_DAYS) {
            throw BizException.paramInvalid(
                    "配租公示期不得少于 " + MIN_ALLOCATION_DAYS + " 个自然日，当前仅 "''',
                  '''        int minDays = cfgInt(ConfigKeys.PUBLICITY_ALLOC_MIN_DAYS,
                DEFAULT_MIN_ALLOCATION_DAYS);
        if (tp == PublicityType.ALLOCATION && days < minDays) {
            throw BizException.paramInvalid(
                    "配租公示期不得少于 " + minDays + " 个自然日，当前仅 "''')
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ PublicityServiceImpl（公示天数可配置）')

# ---------- 2) 信用禁申年限 ----------
p = os.path.join(BASE, r'biz\service\impl\CreditServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'ConfigKeys' not in s:
    s = s.replace('import com.yundao.bp.common.tenant.TenantContext;',
                  'import com.yundao.bp.common.tenant.TenantContext;\n' + IMPORT.strip(), 1)
    s = s.replace('''    /** 严重违规默认限制年限 */
    private static final int DEFAULT_SEVERE_BAN_YEARS = 5;
    /** 一般违规默认限制年限 */
    private static final int DEFAULT_BAN_YEARS = 1;''',
                  '''    /** 严重违规默认限制年限（可被系统参数覆盖） */
    private static final int DEFAULT_SEVERE_BAN_YEARS = 5;
    /** 一般违规默认限制年限（可被系统参数覆盖） */
    private static final int DEFAULT_BAN_YEARS = 1;''' + FIELD)
    s = s.replace('''                    : (vt.severe() ? DEFAULT_SEVERE_BAN_YEARS : DEFAULT_BAN_YEARS);''',
                  '''                    : (vt.severe()
                            ? cfgInt(ConfigKeys.CREDIT_BAN_YEARS_SEVERE,
                                    DEFAULT_SEVERE_BAN_YEARS)
                            : cfgInt(ConfigKeys.CREDIT_BAN_YEARS_NORMAL,
                                    DEFAULT_BAN_YEARS));''')
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ CreditServiceImpl（禁申年限可配置）')

# ---------- 3) 腾退过渡期 ----------
p = os.path.join(BASE, r'biz\service\impl\TerminationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'ConfigKeys' not in s:
    s = s.replace('import com.yundao.bp.common.tenant.TenantContext;',
                  'import com.yundao.bp.common.tenant.TenantContext;\n' + IMPORT.strip(), 1)
    s = s.replace('''    /** 成都：搬迁期上限 6 个月 */
    private static final int MAX_RELOCATION_MONTHS = 6;''',
                  '''    /** 成都：搬迁期上限 6 个月（可被系统参数覆盖） */
    private static final int DEFAULT_MAX_RELOCATION_MONTHS = 6;''' + FIELD)
    s = s.replace('''        if (cmd.relocationMonths() != null && cmd.relocationMonths() > MAX_RELOCATION_MONTHS) {
            throw BizException.paramInvalid(
                    "搬迁期不能超过 " + MAX_RELOCATION_MONTHS + " 个月（成都政策）");''',
                  '''        int maxReloc = cfgInt(ConfigKeys.TERMINATION_RELOCATION_MAX_MONTHS,
                DEFAULT_MAX_RELOCATION_MONTHS);
        if (cmd.relocationMonths() != null && cmd.relocationMonths() > maxReloc) {
            throw BizException.paramInvalid(
                    "搬迁期不能超过 " + maxReloc + " 个月（成都政策）");''')
    s = s.replace('''            e.setTransitionRentMultiplier(cmd.transitionRentMultiplier() == null
                    ? DEFAULT_TRANSITION_MULTIPLIER : cmd.transitionRentMultiplier());''',
                  '''            e.setTransitionRentMultiplier(cmd.transitionRentMultiplier() == null
                    ? cfgDec(ConfigKeys.TERMINATION_TRANSITION_MULTIPLIER, "1.5")
                    : cmd.transitionRentMultiplier());''')
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ TerminationServiceImpl（搬迁期/倍率可配置）')

# ---------- 4) 换房次数与倍率 ----------
p = os.path.join(BASE, r'biz\service\impl\ExchangeServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'ConfigKeys' not in s:
    s = s.replace('import com.yundao.bp.common.tenant.TenantContext;',
                  'import com.yundao.bp.common.tenant.TenantContext;\n' + IMPORT.strip(), 1)
    s = s.replace('''    /** 成都：同一租期内限换 1 次 */
    private static final int MAX_EXCHANGE_TIMES = 1;
    /** 重庆：应换不换的加价倍率 */
    private static final BigDecimal NO_EXCHANGE_MULTIPLIER = new BigDecimal("1.5");''',
                  '''    /** 成都：同一租期内限换次数（可被系统参数覆盖） */
    private static final int DEFAULT_MAX_EXCHANGE_TIMES = 1;
    /** 重庆：应换不换的加价倍率默认值 */
    private static final String DEFAULT_NO_EXCHANGE_MULTIPLIER = "1.5";''' + FIELD)
    s = s.replace('''        int done = countCompleted(cmd.oldContractId());
        if (done >= MAX_EXCHANGE_TIMES) {''',
                  '''        int done = countCompleted(cmd.oldContractId());
        int maxTimes = cfgInt(ConfigKeys.EXCHANGE_MAX_TIMES, DEFAULT_MAX_EXCHANGE_TIMES);
        if (done >= maxTimes) {''')
    s = s.replace('''                    "同一租期内已换房 " + done + " 次，超过上限（成都限 1 次），不可再换");''',
                  '''                    "同一租期内已换房 " + done + " 次，超过上限（成都限 "
                            + maxTimes + " 次），不可再换");''')
    s = s.replace('''        e.setRentMultiplier(NO_EXCHANGE_MULTIPLIER);''',
                  '''        BigDecimal mult = cfgDec(ConfigKeys.EXCHANGE_NO_EXCHANGE_MULTIPLIER,
                DEFAULT_NO_EXCHANGE_MULTIPLIER);
        e.setRentMultiplier(mult);''')
    s = s.replace('''                e.getExchangeNo(), NO_EXCHANGE_MULTIPLIER);''',
                  '''                e.getExchangeNo(), e.getRentMultiplier());''')
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ ExchangeServiceImpl（换房限次/倍率可配置）')

# ---------- 5) 申诉期限 ----------
p = os.path.join(BASE, r'biz\service\impl\AppealServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'ConfigKeys' not in s:
    s = s.replace('import com.yundao.bp.common.tenant.TenantContext;',
                  'import com.yundao.bp.common.tenant.TenantContext;\n' + IMPORT.strip(), 1)
    s = s.replace('''    /** 默认申诉期限（自然日） */
    private static final int DEFAULT_DAYS = 10;''',
                  '''    /** 默认申诉期限（自然日，可被系统参数覆盖） */
    private static final int DEFAULT_DAYS = 10;''' + FIELD)
    s = s.replace('''        int days = cmd.daysFromNow() == null || cmd.daysFromNow() <= 0
                ? DEFAULT_DAYS : cmd.daysFromNow();''',
                  '''        int days = cmd.daysFromNow() == null || cmd.daysFromNow() <= 0
                ? cfgInt(ConfigKeys.APPEAL_DEADLINE_DAYS, DEFAULT_DAYS)
                : cmd.daysFromNow();''')
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ AppealServiceImpl（申诉期限可配置）')

print()
print('已接入 %d 个文件' % len(done))
