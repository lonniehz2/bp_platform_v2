# -*- coding: utf-8 -*-
"""修正面包屑：多页签页面（/rbac/user）应显示父页面名或页签名。

原实现用路径去查 TAB_MENU（键是路由 name），必然查不到，显示「页面」。
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'layout', 'useMenu.js')
s = io.open(P, encoding='utf-8').read()

OLD = """  function titleOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    if (hit) return hit.meta?.title || '页面'
    const cut = path.lastIndexOf('/')
    const base = path.slice(0, cut)
    const tab = path.slice(cut + 1)
    const t = (TAB_MENU[base] || []).find((x) => x.tab === tab)
    return t ? t.title : '页面'
  }

  function groupOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    if (hit) return groupNameOf(hit.meta)
    const base = path.slice(0, path.lastIndexOf('/'))
    const parent = menuRoutes.find((m) => m.path === base)
    return groupNameOf(parent?.meta)
  }"""

NEW = """  /** 按基础路径找父路由（/rbac/user → /rbac/:tab? 那条） */
  function parentRouteOf(path) {
    const base = String(path || '').split('/:')[0].replace(/\\/[^/]+$/, '')
    return menuRoutes.find((m) => {
      const b = NAME_BASE[m.name] || m.path.split('/:')[0]
      return b === base
    })
  }

  function titleOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    if (hit) return hit.meta?.title || '页面'
    // 子页签：/rbac/user → 父页面「用户与权限」+「用户管理」
    const parent = parentRouteOf(path)
    if (!parent) return '页面'
    const tab = String(path).split('/').pop()
    const t = (TAB_MENU[parent.name] || []).find((x) => x.tab === tab)
    const parentTitle = parent.meta?.title || '页面'
    return t ? parentTitle + ' · ' + t.title : parentTitle
  }

  function groupOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    if (hit) return groupNameOf(hit.meta)
    const parent = parentRouteOf(path)
    return groupNameOf(parent?.meta)
  }"""

if OLD in s:
    s = s.replace(OLD, NEW, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('面包屑逻辑已修正')
else:
    print('锚点不匹配')
