# -*- coding: utf-8 -*-
"""修正：BizContract 只有 lesseeIdCardMask（已脱敏），无需再 mask"""
import io

p = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\gov\service\impl\GovReportServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

old = 'r.put("lesseeIdCard", maskIdCard(c.getLesseeIdCard()));'
new = ('// 合同表只存脱敏证件号（lesseeIdCardMask），无需二次掩码\n'
       '                r.put("lesseeIdCard", c.getLesseeIdCardMask());')
assert old in s, '锚点缺失'
s = s.replace(old, new, 1)

# 一并报送联系电话（同样已是可外发字段）
s = s.replace('r.put("lesseeName", c.getLesseeName());',
              'r.put("lesseeName", c.getLesseeName());\n'
              '                r.put("lesseePhone", c.getLesseePhone());', 1)

# maskIdCard 不再使用则删除，避免死代码
if 'maskIdCard(' in s and s.count('maskIdCard(') == 1:
    s = s.replace('''    /** 证件号脱敏（报送也需要最小化个人信息）。 */
    private static String maskIdCard(String id) {
        if (id == null || id.length() < 8) {
            return id;
        }
        return id.substring(0, 4) + "**********" + id.substring(id.length() - 4);
    }

''', '')
    print('  ✓ 移除未使用的 maskIdCard（合同表已存脱敏值）')

io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ 已改用 lesseeIdCardMask')
