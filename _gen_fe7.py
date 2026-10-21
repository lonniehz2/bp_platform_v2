# -*- coding: utf-8 -*-
"""注册新页面路由与菜单 + 大屏第三入口 + 路由守卫放行 /screen"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'


def patch(rel, pairs, must=None):
    p = os.path.join(BASE, rel.replace('/', '\\'))
    s = io.open(p, encoding='utf-8').read()
    if must and must in s:
        print('  - %s 已包含，跳过' % rel)
        return
    n = 0
    for old, new in pairs:
        if old not in s:
            print('  !! %s 锚点缺失：%s' % (rel, old[:40]))
            continue
        s = s.replace(old, new, 1)
        n += 1
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ %s 修改 %d 处' % (rel, n))


# ---------- 1) 路由表新增 3 页 + 大屏路由 ----------
patch('src/router/index.js', [(
    '''  {
    path: '/access',
    name: 'access',
    component: () => import('@/views/AccessRecords.vue'),
    meta: { title: '通行记录', icon: 'Position' }
  }
]''',
    '''  {
    path: '/access',
    name: 'access',
    component: () => import('@/views/AccessRecords.vue'),
    meta: { title: '通行记录', icon: 'Position' }
  },
  {
    path: '/orgs',
    name: 'orgs',
    component: () => import('@/views/Orgs.vue'),
    meta: { title: '组织机构', icon: 'OfficeBuilding' }
  },
  {
    path: '/houses',
    name: 'houses',
    component: () => import('@/views/Houses.vue'),
    meta: { title: '房源台账', icon: 'House' }
  },
  {
    path: '/messages',
    name: 'messages',
    component: () => import('@/views/Messages.vue'),
    meta: { title: '消息待办', icon: 'Bell' }
  }
]''')], must='/orgs')

# ---------- 2) 大屏独立页路由（不进侧边菜单，新窗口打开） ----------
patch('src/router/index.js', [(
    '''  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }''',
    '''  // 独立全屏大屏（第三入口 screen.html，不走 Layout）
  {
    path: '/screen',
    component: () => import('@/screen/ScreenApp.vue'),
    meta: { public: true }
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }''')], must='/screen')

# ---------- 3) vite 三入口 ----------
patch('vite.config.js', [(
    '''        main: resolve(__dirname, 'index.html'),
        h5: resolve(__dirname, 'h5.html')''',
    '''        main: resolve(__dirname, 'index.html'),
        h5: resolve(__dirname, 'h5.html'),
        screen: resolve(__dirname, 'view-screen.html')''')], must='screen:')

# ---------- 4) 顶部加「大屏」按钮 ----------
patch('src/layout/Layout.vue', [(
    '''        <el-tag v-if="auth.admin" type="danger" size="small">管理员</el-tag>''',
    '''        <el-button size="small" plain @click="openScreen">
          <el-icon><FullScreen /></el-icon>大屏
        </el-button>
        <el-tag v-if="auth.admin" type="danger" size="small">管理员</el-tag>''')],
      must='openScreen')

patch('src/layout/Layout.vue', [(
    '''async function onCommand(cmd) {''',
    '''function openScreen() {
  // 独立窗口打开全屏大屏（token 存 localStorage，同源可共享）
  window.open('#/screen', 'bp-screen', 'width=1600,height=900')
}

async function onCommand(cmd) {''')], must='function openScreen')

print()
print('前端 patch 完成')
