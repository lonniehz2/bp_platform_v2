# -*- coding: utf-8 -*-
"""让待办中心分类卡片带上「待处理」筛选意图。

后端：DEFS 里的 route 加 ?pending=1（工单额外带 tab=order）
前端：目标页在 onMounted 前读取 hash 中的 pending=1，把状态筛选设为待处理

背景：此前分类卡片只跳裸路由，进页面看到的是全部数据，与卡片数字不符。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'msg',
                    'service', 'impl', 'TodoCenterServiceImpl.java')
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

BACKEND_PAIRS = [
    ('"/applications",', '"/applications?pending=1",'),
    ('"/contracts",', '"/contracts?pending=1",'),
    ('"/terminations",', '"/terminations?pending=1",'),
    ('"/exchanges",', '"/exchanges?pending=1",'),
    ('"/annual-reviews",', '"/annual-reviews?pending=1",'),
    ('"/ops-center",', '"/ops-center?tab=order&pending=1",'),
    ('"/messages",', '"/messages?pending=1",'),
]

# 页面 → (插入锚点, 插入代码)。锚点用 onMounted 调用行，保证在首次加载前生效
FRONTEND = {
    'Applications.vue': ('onMounted(load)', '''
// 从待办中心「待审申请」点进来时带 pending=1，这里把状态筛选设为待审
if (/pending=1/.test(window.location.hash)) {
  query.applicationStatus = 'SUBMITTED'
}
'''),
    'Terminations.vue': ('onMounted(load)', '''
// 待办中心「待处理退租」跳转过来时带 pending=1
if (/pending=1/.test(window.location.hash)) {
  tf.status = 'APPLYING'
}
'''),
    'Contracts.vue': ('onMounted(load)', '''
// 待办中心「待签合同」跳转过来时带 pending=1（待签约状态）
if (/pending=1/.test(window.location.hash)) {
  q.contractStatus = 'PENDING_SIGN'
}
'''),
    'Exchanges.vue': ('onMounted(load)', '''
// 待办中心「待审换房」跳转过来时带 pending=1
if (/pending=1/.test(window.location.hash) && typeof xf !== 'undefined') {
  xf.status = 'APPLYING'
}
'''),
}


def main():
    s = io.open(JAVA, encoding='utf-8').read()
    n = 0
    for a, b in BACKEND_PAIRS:
        if a in s:
            s = s.replace(a, b, 1)
            n += 1
    io.open(JAVA, 'w', encoding='utf-8', newline='').write(s)
    print('后端路由已加 pending=1：%d 处' % n)

    for fn, (anchor, code) in FRONTEND.items():
        p = os.path.join(VIEWS, fn)
        if not os.path.exists(p):
            print('  跳过（不存在）:', fn)
            continue
        src = io.open(p, encoding='utf-8').read()
        if 'pending=1' in src:
            print('  已有:', fn)
            continue
        if anchor not in src:
            print('  锚点未找到:', fn)
            continue
        src = src.replace(anchor, code.strip('\n') + '\n' + anchor, 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(src)
        print('  已改:', fn)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
