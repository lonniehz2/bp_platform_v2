import io
p=r'src\main\java\com\yundao\platform\service\GuaranteeContractService.java'
s=io.open(p,encoding='utf-8').read()
if 'createFromAllocation' not in s:
 s=s.replace('''    public Contract load(long contractId) {''','''    @org.springframework.transaction.annotation.Transactional
    public Map<String, Object> createFromAllocation(long allocationId, AllocationContractCmd cmd) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select al.id, al.project_id projectId, al.house_id houseId, "
                        + "al.allocation_status allocationStatus, a.applicant_person_id personId "
                        + "from guarantee_allocation al join guarantee_application a on a.id=al.application_id "
                        + "where al.id=? and al.tenant_id=? and al.is_deleted=0 for update",
                allocationId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("配租记录不存在");
        }
        Map<String, Object> row = rows.get(0);
        if (!"ALLOCATED".equals(String.valueOf(row.get("allocationStatus")))) {
            throw BizException.conflict("配租记录不是待签约状态");
        }
        long projectId = ((Number) row.get("projectId")).longValue();
        long houseId = ((Number) row.get("houseId")).longValue();
        long personId = ((Number) row.get("personId")).longValue();
        Map<String, Object> contract = create(new ContractCmd(projectId, cmd.contractNo(), houseId, personId,
                cmd.startDate(), cmd.endDate(), cmd.rentAmount(), cmd.depositAmount(),
                cmd.billingCycle(), cmd.billDay()));
        long contractId = ((Number) contract.get("id")).longValue();
        jdbc.update("update guarantee_allocation set allocation_status='CONTRACTED', contract_id=? "
                + "where id=?", contractId, allocationId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("allocationId", allocationId);
        out.put("contractId", contractId);
        out.put("allocationStatus", "CONTRACTED");
        return out;
    }

    public Contract load(long contractId) {''')
 s += '''
    public record AllocationContractCmd(String contractNo, LocalDate startDate, LocalDate endDate,
                                        BigDecimal rentAmount, BigDecimal depositAmount,
                                        String billingCycle, Integer billDay) {
    }
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('createFromAllocation added')
