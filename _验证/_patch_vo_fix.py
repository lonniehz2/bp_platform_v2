# -*- coding: utf-8 -*-
"""修 LotteryResultVO 两处构造调用。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'biz', 'dto', 'LotteryResultVO.java')
s = io.open(p, encoding='utf-8').read()
s = s.replace('''                e.getSelectTime(), e.getResultStatus(), e.getGiveUpReason(), null, null);''',
              '''                e.getSelectTime(), e.getResultStatus(), e.getGiveUpReason(), null, null,
                null, null, null);''', 1)
s = s.replace('''                resultStatus, giveUpReason, name, phone);''',
              '''                resultStatus, giveUpReason, name, phone, priorityScore, waitDays, totalScore);''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('构造调用已修')
