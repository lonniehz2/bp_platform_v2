# -*- coding: utf-8 -*-
"""修复 Bean 名冲突：两个 ReconcileServiceImpl 同名"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FIX = [
    (r'grant\service\impl\ReconcileServiceImpl.java', 'grantReconcileServiceImpl'),
    (r'fin\service\impl\ReconcileServiceImpl.java', 'finReconcileServiceImpl'),
]

for rel, bean in FIX:
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print('  !! 不存在：%s' % rel)
        continue
    s = io.open(p, encoding='utf-8').read()
    if '@Service("%s")' % bean in s:
        print('  - 已是 %s' % bean)
        continue
    # 只替换类上的 @Service（无参形式）
    if '\n@Service\n' in s:
        s = s.replace('\n@Service\n', '\n@Service("%s")\n' % bean, 1)
    elif '@Service\n' in s:
        s = s.replace('@Service\n', '@Service("%s")\n' % bean, 1)
    else:
        print('  !! 未找到 @Service：%s' % rel)
        continue
    # 加注释说明
    s = s.replace('@Service("%s")' % bean,
                  '// Bean 名显式指定：与另一模块的同名实现类区分，避免运行期 BeanDefinition 冲突\n'
                  '@Service("%s")' % bean, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ %s → @Service("%s")' % (rel.split('\\')[-1], bean))
