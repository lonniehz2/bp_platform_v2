import io
p=r'src\main\java\com\yundao\platform\service\BillingService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    @Transactional
    public Map<String, Object> adjust(long billId, AdjustCmd cmd) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, amount, discount_amount discountAmount, paid_amount paidAmount, bill_status billStatus "
                        + "from bp_bill where id=? and tenant_id=? and is_deleted=0 for update",
                billId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("账单不存在");
        }
        Map<String, Object> bill = rows.get(0);
        if ("PAID".equals(String.valueOf(bill.get("billStatus")))) {
            throw BizException.conflict("已结清账单不能调整");
        }
        BigDecimal amount = (BigDecimal) bill.get("amount");
        BigDecimal oldDiscount = (BigDecimal) bill.get("discountAmount");
        BigDecimal add = cmd.discountAmount() == null ? BigDecimal.ZERO : cmd.discountAmount();
        if (add.signum() < 0) {
            throw BizException.param("调整金额不能为负数");
        }
        BigDecimal discount = (oldDiscount == null ? BigDecimal.ZERO : oldDiscount).add(add);
        if (discount.compareTo(amount) > 0) {
            discount = amount;
        }
        BigDecimal payable = amount.subtract(discount);
        BigDecimal paid = (BigDecimal) bill.get("paidAmount");
        if (paid == null) paid = BigDecimal.ZERO;
        String status = payable.signum() == 0 ? "WAIVED"
                : paid.compareTo(payable) >= 0 ? "PAID"
                : paid.signum() > 0 ? "PARTIAL" : "UNPAID";
        jdbc.update("update bp_bill set discount_amount=?, payable_amount=?, bill_status=?, "
                        + "remark=concat(coalesce(remark,''), ?), update_time=now() where id=?",
                discount, payable, status, "\\n调整:" + (cmd.remark() == null ? "" : cmd.remark()), billId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("billId", billId);
        out.put("discountAmount", discount);
        out.put("payableAmount", payable);
        out.put("billStatus", status);
        return out;
    }

'''
marker='    public List<Map<String, Object>> payments(long projectId) {'
s=s.replace(marker,insert+marker,1)
s=s.replace('''    public record PaymentCmd(BigDecimal amount, String paymentMethod) {
    }''','''    public record PaymentCmd(BigDecimal amount, String paymentMethod) {
    }

    public record AdjustCmd(BigDecimal discountAmount, String remark) {
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\BillingController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @GetMapping("/payments")''','''    @PostMapping("/bills/{billId}/adjust")
    public R<Map<String, Object>> adjust(@PathVariable long billId,
                                         @RequestBody BillingService.AdjustCmd cmd) {
        return R.ok(service.adjust(billId, cmd));
    }

    @GetMapping("/payments")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('adjust api')
