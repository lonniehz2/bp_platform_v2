# -*- coding: utf-8 -*-
import io
import pymysql

# 表结构补床位容量
c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('show columns from bp_fin_meter_point like %s', ('bed_capacity',))
if not cur.fetchone():
    cur.execute('alter table bp_fin_meter_point add bed_capacity int null')
    print('bed_capacity added')
c.close()

# 实体
p = r'..\backend\src\main\java\com\yundao\bp\fin\entity\MeterPoint.java'
s = io.open(p, encoding='utf-8').read()
if 'bedCapacity' not in s:
    s = s.replace('    private String meterName;', '    private Integer bedCapacity;\n    private String meterName;', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('MeterPoint bedCapacity')

# DTO
p = r'..\backend\src\main\java\com\yundao\bp\fin\dto\MeterPointCmd.java'
s = io.open(p, encoding='utf-8').read()
if 'bedCapacity' not in s:
    s = s.replace('        String meterName,', '        Integer bedCapacity,\n        String meterName,', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('MeterPointCmd bedCapacity')

# 分摊分母：运营方承担空床时以“床位容量×天数”为分母
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\UtilityAllocationService.java'
s = io.open(p, encoding='utf-8').read()
s = s.replace('''        p.setMeterName(cmd.meterName());''',
              '''        p.setBedCapacity(cmd.bedCapacity());
        p.setMeterName(cmd.meterName());''', 1)
s = s.replace('''        BigDecimal totalPd = drafts.stream().map(d -> d.personDays)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        BigDecimal allocated = BigDecimal.ZERO;
        for (ShareDraft d : drafts) {
            d.ratio = totalPd.compareTo(BigDecimal.ZERO) <= 0 ? BigDecimal.ZERO
                    : d.personDays.divide(totalPd, 8, RoundingMode.HALF_UP);''',
'''        BigDecimal totalPd = drafts.stream().map(d -> d.personDays)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        EnergyPolicy policy = policy(null);
        boolean operatorBears = policy == null || "OPERATOR".equals(policy.getVacancyBearer());
        BigDecimal denominator = totalPd;
        if (operatorBears && point.getBedCapacity() != null
                && point.getBedCapacity() > 0) {
            int daysInPeriod = ym.lengthOfMonth();
            BigDecimal capacityDays = BigDecimal.valueOf(
                    (long) point.getBedCapacity() * daysInPeriod);
            denominator = capacityDays.max(totalPd);
        }
        BigDecimal allocated = BigDecimal.ZERO;
        for (ShareDraft d : drafts) {
            d.ratio = denominator.compareTo(BigDecimal.ZERO) <= 0 ? BigDecimal.ZERO
                    : d.personDays.divide(denominator, 8, RoundingMode.HALF_UP);''', 1)
s = s.replace('''        BigDecimal operator = totalAmount.subtract(allocated);
        EnergyPolicy policy = policy(null);
        boolean operatorBears = policy == null || "OPERATOR".equals(policy.getVacancyBearer());
        if (!operatorBears && drafts.size() > 0) {''',
'''        BigDecimal operator = totalAmount.subtract(allocated);
        if (!operatorBears && drafts.size() > 0) {''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('allocation capacity denominator')
