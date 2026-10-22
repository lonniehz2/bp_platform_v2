# -*- coding: utf-8 -*-
"""实现公摊费用分摊：按面积或户数把总费用分摊到在租房源并生成账单。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'fin', 'service', 'impl', 'BillingServiceImpl.java')

s = io.open(P, encoding='utf-8').read()

# 依赖注入（可选，避免动构造器影响单测）
if 'sharedHouseMapper' not in s:
    inject = '''
    /** 房源（公摊分摊基数：面积/套数） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper sharedHouseMapper;

    /** 合同（取在租合同的承租人作为付款人） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizContractMapper sharedContractMapper;
'''
    j = s.find('    public BillingServiceImpl(')
    s = s[:j] + inject + '\n' + s[j:]

impl = '''
    /**
     * 公摊费用分摊出账。
     *
     * <p>物业场景：公共区域水电/电梯维保等总费用，按建筑面积（AREA）或户数（HOUSE）
     * 分摊到该组织下所有「在租」房源，为每套生成一张账单；
     * 缴费人取该房源当前履约合同的承租人，无在租合同的房源跳过。
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public java.util.Map<String, Object> generateSharedBills(
            com.yundao.bp.fin.dto.SharedBillCmd cmd) {
        if (!cmd.periodEnd().isAfter(cmd.periodStart())) {
            throw BizException.paramInvalid("费用截止日必须晚于起始日");
        }
        if (sharedHouseMapper == null || sharedContractMapper == null) {
            throw BizException.paramInvalid("公摊分摊服务未就绪");
        }
        String allocateBy = (cmd.allocateBy() == null || cmd.allocateBy().isBlank())
                ? "AREA" : cmd.allocateBy().toUpperCase();

        // 1) 取该组织下的在租房源
        java.util.List<com.yundao.bp.asset.entity.AssetHouse> houses =
                sharedHouseMapper.selectList(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                <com.yundao.bp.asset.entity.AssetHouse>()
                                .eq(com.yundao.bp.asset.entity.AssetHouse::getOrgId, cmd.orgId())
                                .eq(cmd.spaceId() != null,
                                        com.yundao.bp.asset.entity.AssetHouse::getSpaceId,
                                        cmd.spaceId())
                                .in(com.yundao.bp.asset.entity.AssetHouse::getHouseStatus,
                                        java.util.List.of("OCCUPIED", "ALLOCATED")));
        if (houses.isEmpty()) {
            throw BizException.paramInvalid("该范围内没有在租房源，无法分摊");
        }

        // 2) 计算分摊权重
        BigDecimal totalWeight = BigDecimal.ZERO;
        java.util.Map<Long, BigDecimal> weightOf = new java.util.HashMap<>();
        for (com.yundao.bp.asset.entity.AssetHouse h : houses) {
            BigDecimal w = "HOUSE".equals(allocateBy)
                    ? BigDecimal.ONE
                    : (h.getArea() == null || h.getArea().compareTo(BigDecimal.ZERO) <= 0
                            ? BigDecimal.ONE : h.getArea());
            weightOf.put(h.getId(), w);
            totalWeight = totalWeight.add(w);
        }
        if (totalWeight.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("分摊基数为 0，无法分摊");
        }

        // 3) 逐套生成账单（末位差额补到最后一户，保证合计等于总额）
        java.util.List<java.util.Map<String, Object>> details = new java.util.ArrayList<>();
        BigDecimal allocated = BigDecimal.ZERO;
        int created = 0;
        int skipped = 0;
        long now = System.currentTimeMillis();
        for (int i = 0; i < houses.size(); i++) {
            com.yundao.bp.asset.entity.AssetHouse h = houses.get(i);
            BigDecimal share;
            if (i == houses.size() - 1) {
                share = cmd.totalAmount().subtract(allocated).setScale(2, RoundingMode.HALF_UP);
            } else {
                share = cmd.totalAmount().multiply(weightOf.get(h.getId()))
                        .divide(totalWeight, 2, RoundingMode.HALF_UP);
                allocated = allocated.add(share);
            }
            if (share.compareTo(BigDecimal.ZERO) <= 0) {
                skipped++;
                continue;
            }

            com.yundao.bp.biz.entity.BizContract contract =
                    sharedContractMapper.selectOne(
                            new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                    <com.yundao.bp.biz.entity.BizContract>()
                                    .eq(com.yundao.bp.biz.entity.BizContract::getHouseId, h.getId())
                                    .eq(com.yundao.bp.biz.entity.BizContract::getContractStatus,
                                            "EFFECTIVE")
                                    .last("LIMIT 1"));
            if (contract == null) {
                skipped++;
                continue;
            }

            long id = idGen.nextId();
            FinBill e = new FinBill();
            e.setId(id);
            e.setTenantId(TenantContext.tenantId());
            e.setBillNo("FS" + id);
            e.setOrgId(cmd.orgId());
            e.setContractId(contract.getId());
            e.setHouseId(h.getId());
            e.setSpaceId(h.getSpaceId());
            e.setPersonId(contract.getLesseePersonId());
            e.setPayerName(contract.getLesseeName());
            e.setPayerPhone(contract.getLesseePhone());
            e.setFeeItemId(cmd.feeItemId());
            e.setBillPeriod(cmd.billPeriod());
            e.setPeriodStart(cmd.periodStart());
            e.setPeriodEnd(cmd.periodEnd());
            e.setBillAmount(share);
            e.setDiscountAmount(money(null));
            e.setLateFee(money(null));
            e.setPaidAmount(money(null));
            e.setWaivedAmount(money(null));
            e.setPayableAmount(share);
            e.setDueDate(cmd.dueDate() == null ? cmd.periodStart() : cmd.dueDate());
            e.setBillStatus(BillStatus.UNPAID.name());
            e.setOverdueDays(0);
            e.setGenerateType("SHARED");
            e.setRemark("公摊分摊(" + allocateBy + ")");
            e.setIsDeleted(0);
            e.setCreateTime(java.time.LocalDateTime.now());
            billMapper.insert(e);
            created++;

            java.util.Map<String, Object> d = new java.util.HashMap<>();
            d.put("houseId", h.getId());
            d.put("houseName", h.getHouseName());
            d.put("share", share);
            details.add(d);
        }

        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("allocateBy", allocateBy);
        out.put("totalAmount", cmd.totalAmount());
        out.put("houseCount", houses.size());
        out.put("created", created);
        out.put("skipped", skipped);
        out.put("details", details);
        log.info("公摊分摊完成 org={} 方式={} 生成 {} 张", cmd.orgId(), allocateBy, created);
        return out;
    }
'''

if 'generateSharedBills(' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('BillingServiceImpl：generateSharedBills 已实现')
else:
    print('已存在')
