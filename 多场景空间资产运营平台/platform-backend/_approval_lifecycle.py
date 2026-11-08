import io
p=r'src\main\java\com\yundao\platform\service\GuaranteeApplicationService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public Map<String, Object> reject(long applicationId, String comment) {
        Application app = load(applicationId);
        if (!"SUBMITTED".equals(app.status())) {
            throw BizException.conflict("申请不是待审核状态");
        }
        jdbc.update("update guarantee_application set application_status='REJECTED', review_time=now(), "
                + "review_comment=? where id=?", comment, applicationId);
        return Map.of("id", applicationId, "applicationStatus", "REJECTED");
    }

    public Map<String, Object> returnForSupplement(long applicationId, String comment) {
        Application app = load(applicationId);
        if (!"SUBMITTED".equals(app.status())) {
            throw BizException.conflict("申请不是待审核状态");
        }
        jdbc.update("update guarantee_application set application_status='RETURNED', review_time=now(), "
                + "review_comment=? where id=?", comment, applicationId);
        return Map.of("id", applicationId, "applicationStatus", "RETURNED");
    }

    public Map<String, Object> resubmit(long applicationId) {
        Application app = load(applicationId);
        if (!"RETURNED".equals(app.status())) {
            throw BizException.conflict("只有退回补充的申请可以重新提交");
        }
        jdbc.update("update guarantee_application set application_status='SUBMITTED', submit_time=now() "
                + "where id=?", applicationId);
        return Map.of("id", applicationId, "applicationStatus", "SUBMITTED");
    }

'''
marker='''    public Map<String, Object> joinWaitlist(long applicationId) {'''
if marker not in s: raise SystemExit('app marker')
s=s.replace(marker,insert+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\GuaranteeApplicationController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping("/applications/{applicationId}/waitlist")''','''    @PostMapping("/applications/{applicationId}/reject")
    public R<Map<String, Object>> reject(@PathVariable long applicationId,
                                         @RequestBody(required = false) Map<String, String> body) {
        permissions.require("application:reject");
        return R.ok(service.reject(applicationId, body == null ? null : body.get("comment")));
    }

    @PostMapping("/applications/{applicationId}/return")
    public R<Map<String, Object>> returnForSupplement(@PathVariable long applicationId,
                                                      @RequestBody(required = false) Map<String, String> body) {
        permissions.require("application:return");
        return R.ok(service.returnForSupplement(applicationId, body == null ? null : body.get("comment")));
    }

    @PostMapping("/applications/{applicationId}/resubmit")
    public R<Map<String, Object>> resubmit(@PathVariable long applicationId) {
        permissions.require("application:resubmit");
        return R.ok(service.resubmit(applicationId));
    }

    @PostMapping("/applications/{applicationId}/waitlist")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
# contract approve
p=r'src\main\java\com\yundao\platform\service\GuaranteeContractService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    public Map<String, Object> withdraw(long contractId) {''','''    public Map<String, Object> approve(long contractId) {
        Contract contract = load(contractId);
        if (!"APPROVING".equals(contract.contractStatus())) {
            throw BizException.conflict("只有审批中的合同可以通过");
        }
        long overlap = count("select count(*) from guarantee_contract where tenant_id=? and house_id=? "
                        + "and contract_status='ACTIVE' and is_deleted=0 and id<>? "
                        + "and start_date<=? and end_date>=?",
                TenantContext.require(), contract.houseId(), contractId, contract.endDate(), contract.startDate());
        if (overlap > 0) {
            throw BizException.conflict("该房屋在合同期间已有生效合同");
        }
        jdbc.update("update guarantee_contract set contract_status='ACTIVE', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "ACTIVE");
    }

    public Map<String, Object> withdraw(long contractId) {''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\GuaranteeContractController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping("/{contractId}/withdraw")''','''    @PostMapping("/{contractId}/approve")
    public R<Map<String, Object>> approve(@PathVariable long contractId) {
        permissions.require("contract:approve");
        return R.ok(contractService.approve(contractId));
    }

    @PostMapping("/{contractId}/withdraw")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('approval lifecycle')
