# -*- coding: utf-8 -*-
"""注册 4 个新页面路由与菜单 + 首屏分包"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'


def patch(rel, pairs):
    p = os.path.join(BASE, rel.replace('/', '\\'))
    s = io.open(p, encoding='utf-8').read()
    n = 0
    for old, new in pairs:
        if old in s:
            s = s.replace(old, new, 1)
            n += 1
        else:
            print('  !! %s 锚点缺失：%s' % (rel, old[:36]))
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ %-22s %d/%d' % (rel, n, len(pairs)))


# ---------- 1) 路由：新增 4 页 ----------
patch('src/router/index.js', [(
    '''  {
    path: '/messages',
    name: 'messages',
    component: () => import('@/views/Messages.vue'),
    meta: { title: '消息待办', icon: 'Bell' }
  }
]''',
    '''  {
    path: '/messages',
    name: 'messages',
    component: () => import('@/views/Messages.vue'),
    meta: { title: '消息待办', icon: 'Bell' }
  },
  {
    path: '/workorders',
    name: 'workorders',
    component: () => import('@/views/WorkOrders.vue'),
    meta: { title: '工单维保', icon: 'Tools' }
  },
  {
    path: '/alerts',
    name: 'alerts',
    component: () => import('@/views/Alerts.vue'),
    meta: { title: '告警与规则', icon: 'Warning' }
  },
  {
    path: '/keyring',
    name: 'keyring',
    component: () => import('@/views/Keyring.vue'),
    meta: { title: '钥匙包', icon: 'Key' }
  },
  {
    path: '/grants',
    name: 'grants',
    component: () => import('@/views/Grants.vue'),
    meta: { title: '授权与对账', icon: 'Link' }
  }
]''')])

# ---------- 2) 首屏分包 ----------
patch('vite.config.js', [(
    '''    rollupOptions: {
      input: {''',
    '''    rollupOptions: {
      // 首屏分包：把体积大的第三方库拆出来，避免单包 1.2MB
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('echarts') || id.includes('zrender')) return 'echarts'
            if (id.includes('element-plus')) return 'element-plus'
            if (id.includes('@element-plus/icons-vue')) return 'ep-icons'
            return 'vendor'
          }
        }
      },
      input: {''')])

print()
print('patch 完成')
