# -*- coding: utf-8 -*-
import io

p = r'..\backend\src\main\java\com\yundao\bp\fin\service\LateFeeService.java'
s = io.open(p, encoding='utf-8').read()
s = s.replace('''import com.yundao.bp.fin.mapper.LateFeePolicyMapper;''',
              '''import com.yundao.bp.fin.mapper.LateFeePolicyMapper;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.mapper.IamTenantMapper;''', 1)
s = s.replace('''    private final LateFeePolicyMapper policyMapper;
    private final FinBillMapper billMapper;
    private final SnowflakeIdGenerator idGen;

    public LateFeeService(LateFeePolicyMapper policyMapper, FinBillMapper billMapper,
                          SnowflakeIdGenerator idGen) {
        this.policyMapper = policyMapper;
        this.billMapper = billMapper;
        this.idGen = idGen;
    }''',
              '''    private final LateFeePolicyMapper policyMapper;
    private final FinBillMapper billMapper;
    private final IamTenantMapper tenantMapper;
    private final SnowflakeIdGenerator idGen;

    public LateFeeService(LateFeePolicyMapper policyMapper, FinBillMapper billMapper,
                          IamTenantMapper tenantMapper, SnowflakeIdGenerator idGen) {
        this.policyMapper = policyMapper;
        this.billMapper = billMapper;
        this.tenantMapper = tenantMapper;
        this.idGen = idGen;
    }''', 1)
s = s.replace('''    @Scheduled(cron = "0 0 1 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public int runDaily() {
        if (!TenantContext.hasTenant()) {
            log.warn("滞纳金定时任务缺少租户上下文，跳过本次执行");
            return 0;
        }
        return calculate(LocalDate.now(), null);
    }

    @Transactional(rollbackFor = Exception.class)
    public int calculate(LocalDate today, Long billId) {''',
              '''    @Scheduled(cron = "0 0 1 * * ?")
    public int runDaily() {
        List<IamTenant> tenants = tenantMapper.selectList(
                new LambdaQueryWrapper<IamTenant>()
                        .eq(IamTenant::getStatus, "ENABLED")
                        .eq(IamTenant::getDeleted, 0));
        int total = 0;
        for (IamTenant t : tenants) {
            final int[] one = {0};
            TenantContext.runAs(t.getTenantCode(),
                    () -> one[0] = calculate(LocalDate.now(), null));
            total += one[0];
        }
        log.info("滞纳金定时任务：{} 个平台，{} 张账单", tenants.size(), total);
        return total;
    }

    public int calculate(LocalDate today, Long billId) {''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('late fee multi-tenant job')
