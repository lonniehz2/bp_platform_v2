# -*- coding: utf-8 -*-
"""修复字典「类型下拉为空」：内置字典 tenant_id 为 NULL，被租户插件过滤掉。

做法：Mapper 增加忽略租户的查询方法，Service 的类型/按类型查询走该方法。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SYS = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'sys')

# ---------- 1) Mapper ----------
P = os.path.join(SYS, 'mapper', 'SysDictMapper.java')
s = io.open(P, encoding='utf-8').read()
if 'distinctTypes' not in s:
    s = s.replace('''@Mapper
public interface SysDictMapper extends BaseMapper<SysDict> {
}''', '''@Mapper
public interface SysDictMapper extends BaseMapper<SysDict> {

    /** 全部字典类型（含系统内置，忽略租户过滤）。 */
    @org.apache.ibatis.annotations.Select(
            "select distinct dict_type from bp_sys_dict"
            + " where dict_status = 'ENABLED' order by dict_type")
    @com.baomidou.mybatisplus.annotation.InterceptorIgnore(tenantLine = "true")
    java.util.List<String> distinctTypes();

    /** 按类型取字典项（含系统内置，忽略租户过滤）。 */
    @org.apache.ibatis.annotations.Select(
            "select * from bp_sys_dict where dict_type = #{dictType}"
            + " and dict_status = 'ENABLED' order by sort_no asc, id asc")
    @com.baomidou.mybatisplus.annotation.InterceptorIgnore(tenantLine = "true")
    java.util.List<SysDict> selectByTypeIgnoreTenant(@org.apache.ibatis.annotations.Param("dictType")
                                                     String dictType);
}''')
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('SysDictMapper：已加忽略租户的查询')

# ---------- 2) Service ----------
P = os.path.join(SYS, 'service', 'impl', 'DictServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

if 'distinctTypes()' not in s:
    OLD_TYPES = '''        List<SysDict> all = mapper.selectList(new LambdaQueryWrapper<SysDict>()
                .select(SysDict::getDictType)
                .eq(SysDict::getDictStatus, "ENABLED"));
        LinkedHashSet<String> set = new LinkedHashSet<>();
        all.forEach(d -> set.add(d.getDictType()));
        return new ArrayList<>(set);'''
    NEW_TYPES = '''        // 内置字典 tenant_id 为 NULL，必须忽略租户过滤才能查到
        return mapper.distinctTypes();'''
    if OLD_TYPES in s:
        s = s.replace(OLD_TYPES, NEW_TYPES, 1)
        print('DictServiceImpl.types：改走忽略租户查询')
    else:
        print('types 未匹配')

if 'selectByTypeIgnoreTenant' not in s:
    OLD_LIST = '''        List<SysDict> all = mapper.selectList(new LambdaQueryWrapper<SysDict>()
                .eq(SysDict::getDictType, dictType)
                .eq(SysDict::getDictStatus, "ENABLED")
                .orderByAsc(SysDict::getSortNo)
                .orderByAsc(SysDict::getId));'''
    NEW_LIST = '''        List<SysDict> all = mapper.selectByTypeIgnoreTenant(dictType);'''
    if OLD_LIST in s:
        s = s.replace(OLD_LIST, NEW_LIST, 1)
        print('DictServiceImpl.listByType：改走忽略租户查询')
    else:
        print('listByType 未匹配')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('完成')
