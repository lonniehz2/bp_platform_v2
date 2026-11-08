import io
p=r'src\main\java\com\yundao\platform\service\GuaranteeContractService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''        long id = idGen.nextId();
        BigDecimal rent = cmd.rentAmount() == null ? BigDecimal.ZERO : cmd.rentAmount();''','''        long id = idGen.nextId();
        String initialStatus = Boolean.TRUE.equals(cmd.draft()) ? "DRAFT" : "ACTIVE";
        BigDecimal rent = cmd.rentAmount() == null ? BigDecimal.ZERO : cmd.rentAmount();''')
s=s.replace('''                            + "contract_status,is_deleted) values(?,?,?,?,?,?,?,?,?,?,?,?,'ACTIVE',0)",
                    id, tenant, cmd.projectId(), cmd.contractNo().trim(), cmd.houseId(), cmd.personId(),
                    cmd.startDate(), cmd.endDate(), rent, deposit,
                    cmd.billingCycle() == null ? "MONTH" : cmd.billingCycle(),
                    cmd.billDay() == null ? 1 : cmd.billDay());''','''                            + "contract_status,is_deleted) values(?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                    id, tenant, cmd.projectId(), cmd.contractNo().trim(), cmd.houseId(), cmd.personId(),
                    cmd.startDate(), cmd.endDate(), rent, deposit,
                    cmd.billingCycle() == null ? "MONTH" : cmd.billingCycle(),
                    cmd.billDay() == null ? 1 : cmd.billDay(), initialStatus);''')
s=s.replace('''        out.put("contractStatus", "ACTIVE");
        return out;
    }

    @org.springframework.transaction.annotation.Transactional
    public Map<String, Object> createFromAllocation''','''        out.put("contractStatus", initialStatus);
        return out;
    }

    public Map<String, Object> submit(long contractId) {
        Contract contract = load(contractId);
        if (!"DRAFT".equals(contract.contractStatus())) {
            throw BizException.conflict("只有草稿合同可以提交");
        }
        jdbc.update("update guarantee_contract set contract_status='APPROVING', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "APPROVING");
    }

    public Map<String, Object> withdraw(long contractId) {
        Contract contract = load(contractId);
        if (!"APPROVING".equals(contract.contractStatus())) {
            throw BizException.conflict("只有审批中的合同可以撤回");
        }
        jdbc.update("update guarantee_contract set contract_status='DRAFT', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "DRAFT");
    }

    public Map<String, Object> discard(long contractId) {
        Contract contract = load(contractId);
        if (!"DRAFT".equals(contract.contractStatus())) {
            throw BizException.conflict("只有草稿合同可以作废");
        }
        jdbc.update("update guarantee_contract set contract_status='DISCARDED', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "DISCARDED");
    }

    @org.springframework.transaction.annotation.Transactional
    public Map<String, Object> createFromAllocation''')
s=s.replace('''    public record ContractCmd(long projectId, String contractNo, long houseId, long personId,
                              java.time.LocalDate startDate, java.time.LocalDate endDate,
                              BigDecimal rentAmount, BigDecimal depositAmount,
                              String billingCycle, Integer billDay) {
    }''','''    public record ContractCmd(long projectId, String contractNo, long houseId, long personId,
                              java.time.LocalDate startDate, java.time.LocalDate endDate,
                              BigDecimal rentAmount, BigDecimal depositAmount,
                              String billingCycle, Integer billDay, Boolean draft) {
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\GuaranteeContractController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping("/{contractId}/bills")''','''    @PostMapping("/{contractId}/submit")
    public R<Map<String, Object>> submit(@PathVariable long contractId) {
        return R.ok(contractService.submit(contractId));
    }

    @PostMapping("/{contractId}/withdraw")
    public R<Map<String, Object>> withdraw(@PathVariable long contractId) {
        return R.ok(contractService.withdraw(contractId));
    }

    @PostMapping("/{contractId}/discard")
    public R<Map<String, Object>> discard(@PathVariable long contractId) {
        return R.ok(contractService.discard(contractId));
    }

    @PostMapping("/{contractId}/bills")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('contract lifecycle')
