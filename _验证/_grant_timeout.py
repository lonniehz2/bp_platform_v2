# -*- coding: utf-8 -*-
"""授权任务超时判定（不依赖 IoT 联调）。

规则：下发后 3 分钟未收到回调 → 置为 FAILED，记录原因，进入重试或人工处理。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'grant')

# 接口
S = os.path.join(J, 'service', 'GrantService.java')
s = io.open(S, encoding='utf-8').read()
if 'markTimeout' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 授权任务超时判定：下发超过 3 分钟未回调的置为失败，返回条数。 */
    int markTimeout();
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('GrantService：markTimeout 已加')

# 实现
I = os.path.join(J, 'service', 'impl', 'GrantServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'markTimeout' not in s:
    impl = '''
    @Override
    public int markTimeout() {
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        java.util.List<GrantTask> tasks = taskMapper.selectList(
                new LambdaQueryWrapper<GrantTask>()
                        .in(GrantTask::getTaskStatus, java.util.List.of("PENDING", "RUNNING")));
        int n = 0;
        for (GrantTask t : tasks) {
            if (t.getCallbackTime() != null) {
                continue;   // 已回调
            }
            java.time.LocalDateTime deadline = t.getTimeoutAt();
            if (deadline == null && t.getCreateTime() != null) {
                // 兼容历史任务：按创建时间 + 3 分钟推算
                deadline = t.getCreateTime().plusMinutes(3);
            }
            if (deadline == null || deadline.isAfter(now)) {
                continue;
            }
            t.setTaskStatus("FAILED");
            t.setFailCount((t.getFailCount() == null ? 0 : t.getFailCount()) + 1);
            t.setErrorMsg("超时未回调（超过 3 分钟），判定下发失败");
            taskMapper.updateById(t);
            n++;
        }
        if (n > 0) {
            log.warn("授权任务超时判定：{} 条置为失败", n);
        }
        return n;
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('GrantServiceImpl：markTimeout 已实现')

# 调度：并入现有每小时任务（同时每小时判超时）
P = os.path.join(J, 'GrantExpiryJob.java')
s = io.open(P, encoding='utf-8').read()
if 'markTimeout' not in s:
    s = s.replace('''            int n = grantService.expireOverdue();''',
                  '''            int timedOut = grantService.markTimeout();
            if (timedOut > 0) {
                log.warn("授权任务超时判定：{} 条", timedOut);
            }
            int n = grantService.expireOverdue();''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('GrantExpiryJob：已并入超时判定')
