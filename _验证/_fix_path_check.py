# -*- coding: utf-8 -*-
"""修正核对脚本：支持 @GetMapping 无括号写法"""
import io

P = r'D:\Work\业务平台开发\_验证\_check_api_paths.py'
s = io.open(P, encoding='utf-8').read()

old = """        for mm in re.finditer(
                r'@(Get|Post|Put|Delete|Patch)Mapping\\(\\s*(?:value\\s*=\\s*)?'
                r'(?:"([^"]*)")?\\s*\\)', s):"""

new = """        # 兼容两种写法：@GetMapping 与 @GetMapping("/x")，以及 @GetMapping(value="/x")
        # 早期版本只匹配带括号的，导致大量「无括号映射」被漏掉，产生误报
        for mm in re.finditer(
                r'@(Get|Post|Put|Delete|Patch)Mapping'
                r'(?:\\s*\\(\\s*(?:value\\s*=\\s*)?"([^"]*)"?\\s*\\))?', s):"""

assert old in s, '锚点缺失'
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('已修正正则：允许 @XxxMapping 无括号')
