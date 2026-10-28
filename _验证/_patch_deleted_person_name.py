# -*- coding: utf-8 -*-
"""显示层：历史单据显示已删除人员的姓名。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

p = os.path.join(BE, 'person', 'mapper', 'PersonMapper.java')
s = io.open(p, encoding='utf-8').read()
if 'selectNameIncludeDeleted' not in s:
    s = s.replace(
        'public interface PersonMapper extends BaseMapper<Person> {',
        'public interface PersonMapper extends BaseMapper<Person> {\n\n'
        '    /** 显示用：包含已逻辑删除的人员，保证历史单据里的人名不丢。 */\n'
        '    @org.apache.ibatis.annotations.Select(\n'
        '            "select person_name from bp_person where id = #{id} limit 1")\n'
        '    String selectNameIncludeDeleted(\n'
        '            @org.apache.ibatis.annotations.Param("id") Long id);')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('PersonMapper 已加含删除查询')

p = os.path.join(BE, 'common', 'web', 'DisplayEnricher.java')
s = io.open(p, encoding='utf-8').read()
if 'selectNameIncludeDeleted' not in s:
    old = ('            Person p = personMapper.selectById(k);\n'
           '            return p == null ? "" : nullToEmpty(p.getPersonName());')
    new = ('            // 含逻辑删除：人员注销/删除后，历史申请与配租单仍显示姓名\n'
           '            String name = personMapper.selectNameIncludeDeleted(k);\n'
           '            if (name != null && !name.isBlank()) {\n'
           '                return name;\n'
           '            }\n'
           '            Person p = personMapper.selectById(k);\n'
           '            return p == null ? "" : nullToEmpty(p.getPersonName());')
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('Enricher 已含删除人员')
