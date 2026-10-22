# -*- coding: utf-8 -*-
"""后端：快捷签约 + 公示中签名单。

1) POST /contracts/quick-sign
   入参 personId/houseId/leaseStart/leaseEnd/monthlyRent/deposit/securityType
   行为：先自动创建一张「线下受理」申请单（applyChannel=OFFLINE），
         再创建合同草稿并关联该申请单。

2) GET /publicities/{id}/winners
   公示关联批次（bp_biz_publicity.batch_id），返回中签名单（身份证脱敏）。

3) 公示实体/VO 增加 batchId 字段（新建公示时可选关联批次）。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
B = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')

# ---------- 1) 合同：快捷签约 ----------
C = os.path.join(B, 'controller', 'ContractController.java')
s = io.open(C, encoding='utf-8').read()
if 'quickSign' not in s:
    block = '''
    /** 快捷签约：存量人员与空置房源直接生成合同（自动补一张线下受理申请单）。 */
    @PostMapping("/quick-sign")
    @RequirePerm("biz:contract:create")
    @Transactional(rollbackFor = Exception.class)
    public R<ContractVO> quickSign(@Valid @RequestBody QuickSignCmd cmd) {
        return R.ok(contractService.quickSign(cmd));
    }

    /** 快捷签约入参。 */
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
    if 'import jakarta.validation.constraints.NotNull;' not in s:
        s = s.replace('import jakarta.validation.Valid;',
                      'import jakarta.validation.Valid;\nimport jakarta.validation.constraints.NotNull;', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('ContractController：已加 /quick-sign')

S = os.path.join(B, 'service', 'ContractService.java')
s = io.open(S, encoding='utf-8').read()
if 'quickSign' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + ('\n    /** 快捷签约（存量人员/房源直接签约）。 */\n'
                 '    ContractVO quickSign(com.yundao.bp.biz.controller.ContractController.QuickSignCmd cmd);\n') + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('ContractService：已加 quickSign')

I = os.path.join(B, 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'quickSign' not in s:
    impl = '''
    /**
     * 快捷签约：存量人员与空置房源直接签约。
     *
     * <p>业务背景：公司已结束的存量人员/房源不走线上申请流程，但合同仍需可追溯，
     * 因此先自动补一张「线下受理」申请单（applyChannel=OFFLINE），再创建合同草稿。
     */
    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public ContractVO quickSign(com.yundao.bp.biz.controller.ContractController.QuickSignCmd cmd) {
        com.yundao.bp.biz.entity.BizHouse house = houseMapper.selectById(cmd.houseId());
        if (house == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("房源");
        }
        Long appId = null;
        try {
            com.yundao.bp.biz.dto.ApplicationCreateCmd app = new com.yundao.bp.biz.dto.ApplicationCreateCmd(
                    house.getOrgId(), cmd.personId(),
                    cmd.securityType() == null ? "PUBLIC" : cmd.securityType(),
                    "RENT", "OFFLINE", 1, null, house.getOrgId(), null, null, null, null, null);
            com.yundao.bp.biz.dto.ApplicationVO vo = applicationService.create(app);
            appId = vo.id();
        } catch (Exception ex) {
            log.warn("快捷签约自动补申请单失败（合同仍创建）：{}", ex.getMessage());
        }
        com.yundao.bp.biz.dto.ContractCreateCmd create = new com.yundao.bp.biz.dto.ContractCreateCmd(
                "PUBLIC_RENT", house.getOrgId(), house.getOrgId(), cmd.personId(),
                null, null, null, cmd.houseId(), null, null,
                cmd.leaseStart(), cmd.leaseEnd(), cmd.monthlyRent(), cmd.depositAmount(),
                null, "MONTH", 5, null, cmd.remark(), appId);
        return create(create);
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('ContractServiceImpl：已加 quickSign（字段顺序待编译校验）')

print('后端第一批写入完成')
