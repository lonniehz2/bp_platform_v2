# -*- coding: utf-8 -*-
"""修正 insert(any()) 重载歧义 → 显式指定 RuleExecuteLog"""
import io

P = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\rule'
     r'\RuleEngineTest.java')
s = io.open(P, encoding='utf-8').read()

# 1) 导入
if 'entity.RuleExecuteLog;' not in s:
    s = s.replace('import com.yundao.bp.rule.entity.RuleRule;',
                  'import com.yundao.bp.rule.entity.RuleExecuteLog;\n'
                  'import com.yundao.bp.rule.entity.RuleRule;', 1)

# 2) stub
s = s.replace('when(logMapper.insert(any())).thenReturn(1);',
              '// MyBatis-Plus 3.5.7 的 insert 有单条与批量两个重载，必须显式指定类型\n'
              '        when(logMapper.insert(any(RuleExecuteLog.class))).thenReturn(1);', 1)

# 3) verify
s = s.replace('''        org.mockito.Mockito.verify(logMapper, org.mockito.Mockito.times(2))
                .insert(any());''',
              '''        org.mockito.Mockito.verify(logMapper, org.mockito.Mockito.times(2))
                .insert(any(RuleExecuteLog.class));''', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('已修正 insert 重载歧义（2 处 + import）')
