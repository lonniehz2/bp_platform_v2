# -*- coding: utf-8 -*-
import io

# 1) 路由：运营台（独立入口）
p = r'..\frontend\src\router\index.js'
s = io.open(p, encoding='utf-8').read()
if 'PlatformAdminLogin' not in s:
    s = s.replace('''  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },''', '''  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/platform-admin/login',
    name: 'platformadminlogin',
    component: () => import('@/views/PlatformAdminLogin.vue'),
    meta: { public: true }
  },
  {
    path: '/platform-admin',
    name: 'platformadmin',
    component: () => import('@/views/PlatformAdmin.vue'),
    meta: { public: true }
  },''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('routes added')

# 2) 运营登录：记录强制改密标记
p = r'..\frontend\src\views\PlatformAdminLogin.vue'
s = io.open(p, encoding='utf-8').read()
s = s.replace('''    setOperatorName(d.realName || d.username)''', '''    setOperatorName(d.realName || d.username)
    sessionStorage.setItem('bp.operator.mustChange', d.mustChangePassword ? '1' : '0')''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)

# 3) 业务登录页增加运营入口
p = r'..\frontend\src\views\Login.vue'
s = io.open(p, encoding='utf-8').read()
if '平台运营登录' not in s:
    s = s.replace('''          <p class="scope-note">
            登录后右上角显示「组织 · 平台」；平台编码可在悬停提示中查看。
          </p>''', '''          <p class="scope-note">
            登录后右上角显示「组织 · 平台」；平台编码可在悬停提示中查看。
          </p>
          <el-link type="info" style="font-size:12px" @click="toOperator">
            平台运营登录
          </el-link>''', 1)
    s = s.replace('''async function onSubmit() {''', '''function toOperator() {
  router.push('/platform-admin/login')
}

async function onSubmit() {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('login link added')
