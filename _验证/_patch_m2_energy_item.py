# -*- coding: utf-8 -*-
import io
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('show columns from bp_fin_energy_monthly_stat like %s', ('fee_item_id',))
if not cur.fetchone():
    cur.execute('alter table bp_fin_energy_monthly_stat add fee_item_id bigint null after period')
    print('fee_item_id added')
cur.execute('show index from bp_fin_energy_monthly_stat where Key_name=%s', ('uk_energy_stat',))
if cur.fetchone():
    cur.execute('alter table bp_fin_energy_monthly_stat drop index uk_energy_stat')
cur.execute('alter table bp_fin_energy_monthly_stat add unique key uk_energy_stat (tenant_id, period, fee_item_id)')
c.close()

p = r'..\backend\src\main\java\com\yundao\bp\fin\entity\EnergyMonthlyStat.java'
s = io.open(p, encoding='utf-8').read()
if 'feeItemId' not in s:
    s = s.replace('    private Long spaceId;', '    private Long feeItemId;\n    private Long spaceId;', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('entity feeItemId')

p = r'..\backend\src\main\java\com\yundao\bp\fin\service\UtilityAllocationService.java'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    public EnergyStatVO energyMonthly(String period) {',
              '    public EnergyStatVO energyMonthly(String period, Long feeItemId) {', 1)
s = s.replace('''        List<MeterPoint> points = pointMapper.selectList(new LambdaQueryWrapper<MeterPoint>()
                .eq(MeterPoint::getStatus, "ENABLED"));''',
              '''        List<MeterPoint> points = pointMapper.selectList(new LambdaQueryWrapper<MeterPoint>()
                .eq(MeterPoint::getStatus, "ENABLED")
                .eq(feeItemId != null, MeterPoint::getFeeItemId, feeItemId));''', 1)
s = s.replace('''        jdbc.update("delete from bp_fin_energy_monthly_stat where tenant_id=? and period=?",
                TenantContext.tenantId(), period);''',
              '''        jdbc.update("delete from bp_fin_energy_monthly_stat where tenant_id=? and period=?"
                        + " and (fee_item_id=? or (fee_item_id is null and ? is null))",
                TenantContext.tenantId(), period, feeItemId, feeItemId);''', 1)
s = s.replace('''        st.setPeriod(period);''', '''        st.setPeriod(period);
        st.setFeeItemId(feeItemId);''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('energy item filter')

p = r'..\backend\src\main\java\com\yundao\bp\fin\controller\UtilityAllocationController.java'
s = io.open(p, encoding='utf-8').read()
s = s.replace('''    public R<EnergyStatVO> monthly(@RequestParam String period) {
        return R.ok(service.energyMonthly(period));
    }''','''    public R<EnergyStatVO> monthly(@RequestParam String period,
                                   @RequestParam(required = false) Long feeItemId) {
        return R.ok(service.energyMonthly(period, feeItemId));
    }''',1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('energy API item')
