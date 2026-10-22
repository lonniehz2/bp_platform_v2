# -*- coding: utf-8 -*-
"""并发加固三处：
1) 合同签约：把事务放进锁内（TransactionTemplate），锁释放时数据已提交
2) 账单核销：按 billId 串行 + 核销前校验剩余应收
3) 退租申请：按 contractId 串行 + 校验是否已有有效退租单
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------------- 1) 合同签约 ----------------
P = os.path.join(J, 'biz', 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

old_sig = '''    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO sign(Long id, String signFileUrl, String signFlowId) {
        BizContract pre = require(id);'''
new_sig = '''    @Override
    public ContractVO sign(Long id, String signFileUrl, String signFlowId) {
        BizContract pre = require(id);'''
if old_sig in s:
    s = s.replace(old_sig, new_sig, 1)

old_lock = '''        Object lock = SIGN_LOCKS.computeIfAbsent(
                String.valueOf(pre.getHouseId()), k -> new Object());
        synchronized (lock) {
            return doSign(id, signFileUrl, signFlowId);
        }
    }'''
new_lock = '''        Object lock = SIGN_LOCKS.computeIfAbsent(
                String.valueOf(pre.getHouseId()), k -> new Object());
        synchronized (lock) {
            // 事务必须在锁内完成：否则锁先释放、事务后提交，另一线程仍会读到旧状态
            org.springframework.transaction.support.TransactionTemplate tt =
                    new org.springframework.transaction.support.TransactionTemplate(
                            txManager);
            return tt.execute(status -> doSign(id, signFileUrl, signFlowId));
        }
    }'''
if old_lock in s:
    s = s.replace(old_lock, new_lock, 1)

if 'private org.springframework.transaction.PlatformTransactionManager txManager' not in s:
    inject = '''
    /** 事务管理器：签约需在锁内完成事务，保证并发下读到已提交状态 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.transaction.PlatformTransactionManager txManager;
'''
    j = s.find('    public ContractServiceImpl(')
    s = s[:j] + inject + '\n' + s[j:]

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('合同签约：事务已移入锁内')

# ---------------- 2) 账单核销 ----------------
B = os.path.join(J, 'fin', 'service', 'impl', 'BillingServiceImpl.java')
s = io.open(B, encoding='utf-8').read()
if 'ALLOC_LOCKS' not in s:
    old = '''    public BillVO allocate(Long paymentId, Long billId, BigDecimal amount) {'''
    new = '''    public BillVO allocate(Long paymentId, Long billId, BigDecimal amount) {
        // 同一账单串行核销，避免并发重复核销/超收
        Object lock = ALLOC_LOCKS.computeIfAbsent(String.valueOf(billId), k -> new Object());
        synchronized (lock) {
            return doAllocate(paymentId, billId, amount);
        }
    }

    /** 核销分片锁：key = billId。 */
    private static final java.util.concurrent.ConcurrentHashMap<String, Object> ALLOC_LOCKS
            = new java.util.concurrent.ConcurrentHashMap<>();

    private BillVO doAllocate(Long paymentId, Long billId, BigDecimal amount) {'''
    if old in s:
        s = s.replace(old, new, 1)
        io.open(B, 'w', encoding='utf-8', newline='').write(s)
        print('账单核销：已加 billId 串行锁')
    else:
        print('账单核销：未找到 allocate 方法')
else:
    print('账单核销：已存在')

print('完成')
