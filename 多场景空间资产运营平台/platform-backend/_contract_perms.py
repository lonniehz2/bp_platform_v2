import io
p=r'src\main\java\com\yundao\platform\controller\GuaranteeContractController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    private final GuaranteeContractService contractService;
    private final BillingService billingService;

    public GuaranteeContractController(GuaranteeContractService contractService,
                                       BillingService billingService) {
        this.contractService = contractService;
        this.billingService = billingService;
    }''','''    private final GuaranteeContractService contractService;
    private final BillingService billingService;
    private final com.yundao.platform.service.PermissionService permissions;

    public GuaranteeContractController(GuaranteeContractService contractService,
                                       BillingService billingService,
                                       com.yundao.platform.service.PermissionService permissions) {
        this.contractService = contractService;
        this.billingService = billingService;
        this.permissions = permissions;
    }''')
s=s.replace('''    public R<Map<String, Object>> submit(@PathVariable long contractId) {
        return R.ok(contractService.submit(contractId));''','''    public R<Map<String, Object>> submit(@PathVariable long contractId) {
        permissions.require("contract:submit");
        return R.ok(contractService.submit(contractId));''')
s=s.replace('''    public R<Map<String, Object>> withdraw(@PathVariable long contractId) {
        return R.ok(contractService.withdraw(contractId));''','''    public R<Map<String, Object>> withdraw(@PathVariable long contractId) {
        permissions.require("contract:withdraw");
        return R.ok(contractService.withdraw(contractId));''')
s=s.replace('''    public R<Map<String, Object>> discard(@PathVariable long contractId) {
        return R.ok(contractService.discard(contractId));''','''    public R<Map<String, Object>> discard(@PathVariable long contractId) {
        permissions.require("contract:discard");
        return R.ok(contractService.discard(contractId));''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('contract perms')
