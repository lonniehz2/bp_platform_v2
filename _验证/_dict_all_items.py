# -*- coding: utf-8 -*-
"""字典管理页需要看到已停用项（否则停用后从列表消失，无法再启用）。

做法：列表接口加 all 参数，管理页传 all=true。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SYS = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'sys')

# ---------- Mapper：全部 + 仅启用 ----------
P = os.path.join(SYS, 'mapper', 'SysDictMapper.java')
s = io.open(P, encoding='utf-8').read()
if 'selectByTypeAll' not in s:
    s = s.replace('''    @com.baomidou.mybatisplus.annotation.InterceptorIgnore(tenantLine = "true")
    java.util.List<SysDict> selectByTypeIgnoreTenant(@org.apache.ibatis.annotations.Param("dictType")
                                                     String dictType);''',
'''    @com.baomidou.mybatisplus.annotation.InterceptorIgnore(tenantLine = "true")
    java.util.List<SysDict> selectByTypeIgnoreTenant(@org.apache.ibatis.annotations.Param("dictType")
                                                     String dictType);

    /** 按类型取全部字典项（含已停用，管理页用）。 */
    @org.apache.ibatis.annotations.Select(
            "select * from bp_sys_dict where dict_type = #{dictType}"
            + " order by sort_no asc, id asc")
    @com.baomidou.mybatisplus.annotation.InterceptorIgnore(tenantLine = "true")
    java.util.List<SysDict> selectByTypeAll(@org.apache.ibatis.annotations.Param("dictType")
                                            String dictType);''')
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('SysDictMapper：已加 selectByTypeAll')

# ---------- Service 接口 ----------
P = os.path.join(SYS, 'service', 'DictService.java')
s = io.open(P, encoding='utf-8').read()
if 'listByType(String dictType, boolean includeDisabled)' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 按类型取字典项；includeDisabled=true 时含已停用（管理页）。 */
    java.util.List<com.yundao.bp.sys.entity.SysDict> listByType(String dictType,
                                                               boolean includeDisabled);
''' + s[i:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('DictService：已加重载方法')

# ---------- Service 实现 ----------
P = os.path.join(SYS, 'service', 'impl', 'DictServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()
if 'includeDisabled' not in s:
    i = s.find('public List<SysDict> listByType(String dictType)')
    if i > 0:
        # 在 listByType 结束处插入新方法：找到该方法体的结束花括号
        depth, j = 0, s.find('{', i)
        while j < len(s):
            if s[j] == '{':
                depth += 1
            elif s[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        add = '''

    @Override
    public List<SysDict> listByType(String dictType, boolean includeDisabled) {
        if (!includeDisabled) {
            return listByType(dictType);
        }
        // 管理页：含已停用，便于重新启用
        return mapper.selectByTypeAll(dictType);
    }'''
        s = s[:j + 1] + add + s[j + 1:]
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('DictServiceImpl：已实现 includeDisabled')
    else:
        print('未找到 listByType')

# ---------- Controller ----------
P = os.path.join(SYS, 'controller', 'SysController.java')
s = io.open(P, encoding='utf-8').read()
if 'includeDisabled' not in s:
    OLD = '''    public R<List<SysDict>> dictItems(@PathVariable String dictType) {'''
    if OLD in s:
        i = s.find(OLD)
        j = s.find('\n    }', i)
        seg = s[i:j]
        new = seg.replace('dictItems(@PathVariable String dictType)',
                          'dictItems(@PathVariable String dictType,\n'
                          '                                 @RequestParam(defaultValue = "false")\n'
                          '                                 boolean includeDisabled)')
        new = new.replace('dictService.listByType(dictType)',
                          'dictService.listByType(dictType, includeDisabled)')
        s = s[:i] + new + s[j:]
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('SysController：字典列表支持 includeDisabled')
    else:
        print('未找到字典列表方法，跳过')
