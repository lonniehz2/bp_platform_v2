# -*- coding: utf-8 -*-
"""重命名 grant 模块的 ReconcileServiceImpl → GrantReconcileServiceImpl（消除 MyBatis 别名冲突）"""
import io
import os

D = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp\grant\service\impl'
old = os.path.join(D, 'ReconcileServiceImpl.java')
new = os.path.join(D, 'GrantReconcileServiceImpl.java')

s = io.open(old, encoding='utf-8').read()
s = s.replace('class ReconcileServiceImpl', 'class GrantReconcileServiceImpl')
s = s.replace('public ReconcileServiceImpl(', 'public GrantReconcileServiceImpl(')
s = s.replace('@Service("grantReconcileServiceImpl")',
              '// 类名与 fin 模块的 ReconcileServiceImpl 区分：\n'
              '// MyBatis 的类型别名扫描把 Service 也注册了别名，同名类会导致\n'
              '// "The alias \'X\' is already mapped to" 启动失败\n'
              '@Service("grantReconcileService")')
# 补一句类注释说明
s = s.replace('public class GrantReconcileServiceImpl',
              'public class GrantReconcileServiceImpl')

io.open(new, 'w', encoding='utf-8').write(s)
os.remove(old)
print('已重命名 → GrantReconcileServiceImpl.java')

# 同步测试类引用（若有）
T = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\grant\ReconcileTest.java'
if os.path.exists(T):
    t = io.open(T, encoding='utf-8').read()
    t = t.replace('import com.yundao.bp.grant.service.impl.ReconcileServiceImpl;',
                  'import com.yundao.bp.grant.service.impl.GrantReconcileServiceImpl;')
    t = t.replace('private ReconcileServiceImpl service;',
                  'private GrantReconcileServiceImpl service;')
    t = t.replace('new ReconcileServiceImpl(', 'new GrantReconcileServiceImpl(')
    io.open(T, 'w', encoding='utf-8').write(t)
    print('已同步更新 ReconcileTest.java')
