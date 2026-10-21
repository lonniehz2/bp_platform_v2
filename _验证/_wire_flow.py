# -*- coding: utf-8 -*-
"""把资金流水接入业务：收款/退款/补贴自动记流水

用字段注入 @Autowired(required=false) 而非构造器注入，
避免改动现有构造器导致既有单元测试编译失败。
"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

FIELD = '''
    /** 资金流水记录器（可选注入，便于单测时不依赖） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.service.CashFlowService cashFlowService;

    private void writeFlow(com.yundao.bp.fin.constant.FlowType type,
                           com.yundao.bp.fin.constant.FlowBizType bizType,
                           Long bizId, java.math.BigDecimal amount, String remark) {
        if (cashFlowService == null) {
            return;
        }
        try {
            cashFlowService.record(type, bizType, bizId, amount, remark);
        } catch (Exception ex) {
            log.warn("写资金流水失败（不影响主业务）：{}", ex.getMessage());
        }
    }
'''

patches = []

# ---------- 1. 收款确认 → 收入流水 ----------
patches.append({
    'file': r'fin\service\impl\BillingServiceImpl.java',
    'insert_after': '    // ==================== 内部 ====================',
    'edits': [
        # createPayment 结尾 insert 之后记流水
        ('''        paymentMapper.insert(e);
        return PaymentVO.from(e);''',
         '''        paymentMapper.insert(e);
        // 收款成功即记收入流水
        if (PayStatus.SUCCESS.name().equals(e.getPayStatus())) {
            writeFlow(com.yundao.bp.fin.constant.FlowType.INCOME,
                    com.yundao.bp.fin.constant.FlowBizType.PAYMENT, e.getId(),
                    e.getPayAmount(), "收款 " + e.getPaymentNo());
        }
        return PaymentVO.from(e);'''),
        # confirmPayment
        ('''        e.setPayStatus(PayStatus.SUCCESS.name());
        e.setPayTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        paymentMapper.updateById(e);
        return PaymentVO.from(e);''',
         '''        e.setPayStatus(PayStatus.SUCCESS.name());
        e.setPayTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        paymentMapper.updateById(e);
        writeFlow(com.yundao.bp.fin.constant.FlowType.INCOME,
                com.yundao.bp.fin.constant.FlowBizType.PAYMENT, e.getId(),
                e.getPayAmount(), "收款确认 " + e.getPaymentNo());
        return PaymentVO.from(e);'''),
    ],
})

# ---------- 2. 退款打款 → 支出流水 ----------
patches.append({
    'file': r'fin\service\impl\DepositRefundServiceImpl.java',
    'insert_after': '    // ==================== 内部 ====================',
    'edits': [
        ('''        e.setRefundTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        refundMapper.updateById(e);''',
         '''        e.setRefundTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        refundMapper.updateById(e);
        // 退款打款 → 支出流水
        writeFlow(com.yundao.bp.fin.constant.FlowType.EXPENSE,
                com.yundao.bp.fin.constant.FlowBizType.REFUND, e.getId(),
                e.getRefundAmount(), "退款 " + e.getRefundNo());'''),
    ],
})

# ---------- 3. 补贴发放 → 支出流水 ----------
patches.append({
    'file': r'fin\service\impl\SubsidyServiceImpl.java',
    'insert_after': '    // ==================== 计算 ====================',
    'edits': [
        ('''        e.setUpdateTime(LocalDateTime.now());
        recordMapper.updateById(e);

        // OFFSET_RENT 抵扣租金：直接冲减当期租金账单''',
         '''        e.setUpdateTime(LocalDateTime.now());
        recordMapper.updateById(e);
        // 补贴发放 → 支出流水（平台代发，资金流出）
        writeFlow(com.yundao.bp.fin.constant.FlowType.EXPENSE,
                com.yundao.bp.fin.constant.FlowBizType.SUBSIDY, e.getId(),
                paid, "补贴发放 " + e.getRecordNo());

        // OFFSET_RENT 抵扣租金：直接冲减当期租金账单'''),
    ],
})

for p in patches:
    path = os.path.join(BASE, p['file'])
    s = io.open(path, encoding='utf-8').read()
    if 'CashFlowService' in s:
        print('  已接入，跳过: %s' % os.path.basename(path))
        continue
    # 需要 log 变量
    if 'private static final Logger log' not in s:
        print('  !! 无 log 变量，跳过: %s' % p['file'])
        continue
    # 插入字段与方法
    anchor = p['insert_after']
    if anchor not in s:
        print('  !! 找不到插入锚点，跳过: %s' % p['file'])
        continue
    s = s.replace(anchor, FIELD + '\n' + anchor, 1)
    # 应用编辑
    okall = True
    for old, new in p['edits']:
        if old not in s:
            print('  !! 编辑锚点缺失: %s' % p['file'])
            okall = False
            break
        s = s.replace(old, new, 1)
    if not okall:
        continue
    io.open(path, 'w', encoding='utf-8').write(s)
    print('  ✓ 已接入流水: %s' % os.path.basename(path))
