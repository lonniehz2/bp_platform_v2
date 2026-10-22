# -*- coding: utf-8 -*-
"""合同页增强：详情 + 编辑（仅草稿）+ 更多表格字段。

后端：新增 PUT /contracts/{id}（仅 DRAFT 可改租金/租期/备注等条款字段）
前端：列表补充 合同类型/月租/押金/签约时间/到期天数 等列；操作列加「详情」「编辑」
详情：弹窗展示全部关键字段（含承租人证件、房屋面积、支付周期等）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
B = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')
F = os.path.join(ROOT, 'frontend', 'src', 'views', 'Contracts.vue')

# ---------------- 后端 ----------------
C = os.path.join(B, 'controller', 'ContractController.java')
s = io.open(C, encoding='utf-8').read()
if '/** 更新合同条款' not in s:
    block = '''
    /** 更新合同条款（仅草稿状态可改；签约后金额与租期需走变更单）。 */
    @PutMapping("/{id}")
    @RequirePerm("biz:contract:update")
    @Transactional(rollbackFor = Exception.class)
    public R<ContractVO> update(@PathVariable Long id,
                                @RequestBody ContractUpdateCmd cmd) {
        return R.ok(contractService.updateContract(id, cmd));
    }

    /** 合同更新入参（仅允许改草稿期条款）。 */
    public record ContractUpdateCmd(
            java.math.BigDecimal rentPrice,
            java.math.BigDecimal monthlyRent,
            java.math.BigDecimal depositAmount,
            java.math.BigDecimal subsidyAmount,
            java.time.LocalDate leaseStart,
            java.time.LocalDate leaseEnd,
            Integer payDay,
            String payCycle,
            String remark) {
    }
'''
    anchor = '    /** 提交待签 */'
    if anchor in s:
        s = s.replace(anchor, block + '\n' + anchor, 1)
    else:
        i = s.rstrip().rfind('}')
        s = s[:i] + block + s[i:]
    if 'PutMapping' not in s:
        s = s.replace('import org.springframework.web.bind.annotation.PostMapping;',
                      'import org.springframework.web.bind.annotation.PostMapping;\n'
                      'import org.springframework.web.bind.annotation.PutMapping;', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('ContractController：已加 PUT /{id}')

# 服务接口
S = os.path.join(B, 'service', 'ContractService.java')
s = io.open(S, encoding='utf-8').read()
if 'updateContract' not in s:
    s = s.replace('    int expireDue();',
                  '    /** 更新合同条款（仅草稿）。 */\n'
                  '    ContractVO updateContract(Long id,\n'
                  '            com.yundao.bp.biz.controller.ContractController.ContractUpdateCmd cmd);\n\n'
                  '    int expireDue();', 1)
    if 'updateContract' not in s:
        i = s.rstrip().rfind('}')
        s = s[:i] + ('\n    /** 更新合同条款（仅草稿）。 */\n'
                     '    ContractVO updateContract(Long id,\n'
                     '            com.yundao.bp.biz.controller.ContractController.ContractUpdateCmd cmd);\n') + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('ContractService：已加 updateContract')

# 服务实现
IMPL = os.path.join(B, 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(IMPL, encoding='utf-8').read()
if 'updateContract' not in s:
    impl = '''
    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO updateContract(Long id,
            com.yundao.bp.biz.controller.ContractController.ContractUpdateCmd cmd) {
        BizContract e = contractMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("合同");
        }
        if (!"DRAFT".equals(e.getContractStatus())) {
            throw BizException.paramInvalid("仅草稿状态的合同可直接编辑，签约后请走合同变更");
        }
        if (cmd.rentPrice() != null) {
            e.setRentPrice(money(cmd.rentPrice()));
        }
        if (cmd.monthlyRent() != null) {
            e.setMonthlyRent(money(cmd.monthlyRent()));
        }
        if (cmd.depositAmount() != null) {
            e.setDepositAmount(money(cmd.depositAmount()));
        }
        if (cmd.subsidyAmount() != null) {
            e.setSubsidyAmount(money(cmd.subsidyAmount()));
        }
        if (cmd.leaseStart() != null) {
            e.setLeaseStart(cmd.leaseStart());
        }
        if (cmd.leaseEnd() != null) {
            e.setLeaseEnd(cmd.leaseEnd());
        }
        if (e.getLeaseStart() != null && e.getLeaseEnd() != null) {
            e.setLeaseMonths(monthCount(e.getLeaseStart(), e.getLeaseEnd()));
        }
        if (cmd.payDay() != null) {
            e.setPayDay(cmd.payDay());
        }
        if (cmd.payCycle() != null && !cmd.payCycle().isBlank()) {
            e.setPayCycle(cmd.payCycle());
        }
        if (cmd.remark() != null) {
            e.setRemark(cmd.remark());
        }
        contractMapper.updateById(e);
        return ContractVO.from(e, orgNameOf(e.getLessorOrgId()), houseAddressOf(e.getHouseId()));
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(IMPL, 'w', encoding='utf-8', newline='').write(s)
    print('ContractServiceImpl：已加 updateContract')

print('后端改造完成')
