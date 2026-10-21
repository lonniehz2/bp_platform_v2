import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  { path: '/h5/login', component: () => import('./views/H5Login.vue'),
    meta: { public: true, hideTab: true } },
  { path: '/h5/home', component: () => import('./views/H5Home.vue') },
  { path: '/h5/bills', component: () => import('./views/H5Bills.vue') },
  { path: '/h5/applications', component: () => import('./views/H5Applications.vue') },
  { path: '/h5/access', component: () => import('./views/H5Access.vue'),
    meta: { hideTab: true } },
  { path: '/h5/repairs', component: () => import('./views/H5Repairs.vue'),
    meta: { hideTab: true } },
  { path: '/h5/profile', component: () => import('./views/H5Profile.vue') },
  { path: '/h5', redirect: '/h5/home' },
  { path: '/:pathMatch(.*)*', redirect: '/h5/home' }
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.loggedIn) return { path: '/h5/login' }
  if (!auth.user) {
    try { await auth.loadMe() } catch (e) { auth.logout(); return { path: '/h5/login' } }
  }
  return true
})

export default router
