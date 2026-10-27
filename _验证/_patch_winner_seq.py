# -*- coding: utf-8 -*-
"""中签序号与摇号结果排序修正。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')

# winners: 序号用选房序号（数字），避免展示哈希串
p = os.path.join(BK, 'service', 'impl', 'PublicityServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'seqNo' not in s:
    s = s.replace('''                    house == null ? null : house.getHouseName(),
                    r.getLotterySeq(),''', '''                    house == null ? null : house.getHouseName(),
                    r.getSelectSeq() == null ? r.getLotterySeq()
                            : String.format("%02d", r.getSelectSeq()),''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('winners 序号已改')

# 摇号结果：中签在前、选房序号升序、无序号在后
p2 = os.path.join(BK, 'service', 'impl', 'AllocationServiceImpl.java')
t = io.open(p2, encoding='utf-8').read()
if 'sortedLottery' not in t:
    t = t.replace('''                .stream().map(LotteryResultVO::from).toList();
        java.util.Set<Long> pids = rows.stream().map(LotteryResultVO::personId)''',
                  '''                .stream().map(LotteryResultVO::from)
                .sorted((a, b) -> {
                    boolean wa = \"WON\".equals(a.resultType());
                    boolean wb = \"WON\".equals(b.resultType());
                    if (wa != wb) {
                        return wa ? -1 : 1;
                    }
                    Integer sa = a.selectSeq() == null ? Integer.MAX_VALUE : a.selectSeq();
                    Integer sb = b.selectSeq() == null ? Integer.MAX_VALUE : b.selectSeq();
                    return Integer.compare(sa, sb);
                })
                .toList();
        java.util.Set<Long> pids = rows.stream().map(LotteryResultVO::personId)''', 1)
    io.open(p2, 'w', encoding='utf-8', newline='').write(t)
    print('摇号结果排序已改')
