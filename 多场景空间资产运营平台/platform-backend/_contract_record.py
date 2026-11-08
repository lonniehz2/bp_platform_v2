import io
p=r'src\main\java\com\yundao\platform\service\GuaranteeContractService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    public record ContractCmd(Long projectId, String contractNo, Long houseId, Long personId,
                              LocalDate startDate, LocalDate endDate, BigDecimal rentAmount,
                              BigDecimal depositAmount, String billingCycle, Integer billDay) {
    }''','''    public record ContractCmd(Long projectId, String contractNo, Long houseId, Long personId,
                              LocalDate startDate, LocalDate endDate, BigDecimal rentAmount,
                              BigDecimal depositAmount, String billingCycle, Integer billDay,
                              Boolean draft) {
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('record fixed')
