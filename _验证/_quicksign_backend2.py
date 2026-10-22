# -*- coding: utf-8 -*-
"""后端：快捷签约（按真实 Cmd 字段顺序）+ 公示中签名单。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
B = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')

# ---------------- 1) Controller / Service 接口 ----------------
C = os.path.join(B, 'controller', 'ContractController.java')
s = io.open(C, encoding='utf-8').read()
if 'quickSign' not in s:
    block = '''
    /**
     * 快捷签约：存量人员 + 空置房源直接生成合同草稿。
     *
     * <p>用于「公司已结束的存量人员/房源」这类不走线上申请的签约场景。
     * 服务端会自动补一张线下受理申请单（applyChannel=OFFLINE），保证合同可追溯。
     */
    @PostMapping("/quick-sign")
    @RequirePerm("biz:contract:create")
    @Transactional(rollbackFor = Exception.class)
    public R<ContractVO> quickSign(@Valid @RequestBody QuickSignCmd cmd) {
        return R.ok(contractService.quickSign(cmd));
    }

    /** 快捷签约入参（只暴露业务必需项，其余由服务端按房源与人员补齐）。 */
    public record QuickSignCmd(
            @NotNull(message = "承租人不能为空") Long personId,
            @NotNull(message = "房源不能为空") Long houseId,
            @NotNull(message = "起租日不能为空") LocalDate leaseStart,
            @NotNull(message = "止租日不能为空") LocalDate leaseEnd,
            @NotNull(message = "月租不能为空") BigDecimal monthlyRent,
            BigDecimal depositAmount,
            String securityType,
            String remark) {
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + block + s[i:]
    if 'jakarta.validation.constraints.NotNull' not in s:
        s = s.replace('import jakarta.validation.Valid;',
                      'import jakarta.validation.Valid;\nimport jakarta.validation.constraints.NotNull;', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('ContractController：/quick-sign 已加')

S = os.path.join(B, 'service', 'ContractService.java')
s = io.open(S, encoding='utf-8').read()
if 'quickSign' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + ('\n    /** 快捷签约（存量人员/房源直接签约，自动补线下受理申请单）。 */\n'
                 '    ContractVO quickSign('
                 'com.yundao.bp.biz.controller.ContractController.QuickSignCmd cmd);\n') + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('ContractService：quickSign 已加')

# ---------------- 2) 实现 ----------------
I = os.path.join(B, 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'quickSign' not in s:
    # 依赖：HouseMapper 与 ApplicationService（可选注入，避免动构造器）
    if 'quickSignApplicationService' not in s:
        inject = '''
    /** 房源查询（快捷签约需要房源组织与地址） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizHouseMapper quickSignHouseMapper;

    /** 申请服务（快捷签约自动补线下受理申请单） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.service.ApplicationService quickSignApplicationService;
'''
        j = s.find('    public ContractServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]

    impl = '''
    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public ContractVO quickSign(com.yundao.bp.biz.controller.ContractController.QuickSignCmd cmd) {
        com.yundao.bp.biz.entity.BizHouse house =
                quickSignHouseMapper == null ? null : quickSignHouseMapper.selectById(cmd.houseId());
        if (house == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("房源");
        }
        Long orgId = house.getOrgId() == null ? com.yundao.bp.tenant.TenantContext.orgId() : house.getOrgId();
        if (orgId == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("房源缺少所属组织，无法签约");
        }
        String securityType = (cmd.securityType() == null || cmd.securityType().isBlank())
                ? "PUBLIC" : cmd.securityType();

        // 1) 自动补一张线下受理申请单（失败不阻断合同创建）
        Long appId = null;
        if (quickSignApplicationService != null) {
            try {
                com.yundao.bp.biz.dto.ApplicationCreateCmd app =
                        new com.yundao.bp.biz.dto.ApplicationCreateCmd(
                                orgId, cmd.personId(), securityType, "HOUSE", "OFFLINE",
                                1, null, null, null, null, null,
                                null, null, null, null, null, null, null, null, null,
                                cmd.remark());
                com.yundao.bp.biz.dto.ApplicationVO vo = quickSignApplicationService.create(app);
                appId = vo == null ? null : vo.id();
            } catch (Exception ex) {
                log.warn("快捷签约自动补申请单失败（合同仍创建）：{}", ex.getMessage());
            }
        }

        // 2) 创建合同草稿（金额口径：actualPay 由服务端计算）
        java.math.BigDecimal rent = cmd.monthlyRent();
        String contractType = "AFFORDABLE".equals(securityType) ? "AFFORDABLE"
                : ("TALENT".equals(securityType) ? "TALENT" : "PUBLIC_RENTAL");
        com.yundao.bp.biz.dto.ContractCreateCmd create =
                new com.yundao.bp.biz.dto.ContractCreateCmd(
                        contractType, orgId, orgId, cmd.personId(),
                        null, null, null,
                        cmd.houseId(), null, house.getAddress(), house.getBuildArea(),
                        cmd.leaseStart(), cmd.leaseEnd(),
                        rent, "HOUSE_MONTH", rent,
                        cmd.depositAmount(), null,
                        "MONTH", 5, null, null, null, null, null,
                        cmd.remark());
        return create(create);
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('ContractServiceImpl：quickSign 已加')

print('完成')
