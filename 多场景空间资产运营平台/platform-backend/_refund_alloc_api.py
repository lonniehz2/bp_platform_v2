import io
p=r'src\main\java\com\yundao\platform\service\BillingService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public List<Map<String, Object>> paymentAllocations(long paymentId) {
        String tenant = TenantContext.require();
        return jdbc.queryForList(
                "select al.id allocationId, al.bill_id billId, b.bill_no billNo, b.period_start periodStart, "
                        + "b.period_end periodEnd, al.amount, b.bill_status billStatus, "
                        + "coalesce((select sum(r.amount) from bp_refund r where r.tenant_id=al.tenant_id "
                        + "and r.allocation_id=al.id and r.is_deleted=0),0) refunded "
                        + "from bp_payment_allocation al join bp_bill b on b.id=al.bill_id "
                        + "where al.tenant_id=? and al.payment_id=? order by al.id",
                tenant, paymentId);
    }

'''
marker='''    @Transactional
    public Map<String, Object> refund(long paymentId, RefundCmd cmd) {'''
if marker not in s: raise SystemExit('marker')
s=s.replace(marker,insert+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\BillingController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping("/payments/{paymentId}/refund")''','''    @GetMapping("/payments/{paymentId}/allocations")
    public R<List<Map<String, Object>>> paymentAllocations(@PathVariable long paymentId) {
        return R.ok(service.paymentAllocations(paymentId));
    }

    @PostMapping("/payments/{paymentId}/refund")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('allocations endpoint')
