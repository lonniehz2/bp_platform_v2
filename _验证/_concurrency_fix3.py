# -*- coding: utf-8 -*-
"""退租申请并发加固：同一合同串行 + 已有有效退租单则拒绝。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'biz', 'service', 'impl', 'TerminationServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

if 'TERM_LOCKS' not in s:
    s = s.replace('''    public TerminationVO apply(TerminationCreateCmd cmd) {''',
                  '''    public TerminationVO apply(TerminationCreateCmd cmd) {
        // 同一合同串行申请，避免并发产生多张有效退租单
        Object lock = TERM_LOCKS.computeIfAbsent(
                String.valueOf(cmd.contractId()), k -> new Object());
        synchronized (lock) {
            return doApply(cmd);
        }
    }

    /** 退租申请分片锁：key = contractId。 */
    private static final java.util.concurrent.ConcurrentHashMap<String, Object> TERM_LOCKS
            = new java.util.concurrent.ConcurrentHashMap<>();

    private TerminationVO doApply(TerminationCreateCmd cmd) {''', 1)

    # 在业务校验后补「已有有效退租单」检查：插在创建实体之前
    anchor = '        BizTermination e = new BizTermination();'
    guard = '''        // 已有未结束的退租单时拒绝重复申请
        Long active = mapper.selectCount(
                new LambdaQueryWrapper<BizTermination>()
                        .eq(BizTermination::getContractId, cmd.contractId())
                        .notIn(BizTermination::getTerminationStatus,
                                java.util.List.of("CANCELLED", "REJECTED", "COMPLETED")));
        if (active != null && active > 0) {
            throw BizException.stateConflict("该合同已有进行中的退租单，不能重复申请");
        }

'''
    if anchor in s:
        s = s.replace(anchor, guard + anchor, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('退租申请：已加串行锁与重复校验')
    else:
        print('退租申请：未找到创建锚点')
else:
    print('退租申请：已存在')
