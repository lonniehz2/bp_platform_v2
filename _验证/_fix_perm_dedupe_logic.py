# -*- coding: utf-8 -*-
"""修正 _add_require_perm 的重复检测：只在「同一方法」范围内判断是否已有注解。

判定范围：从当前 Mapping 行向上回溯，遇到以下情况即停止：
  · 上一个 @XxxMapping（说明进入上一个方法）
  · 类声明 / 字段声明（public class / private final 等）
  · 方法体结束（}）
在此范围内若出现 @RequirePerm → 视为已有，跳过。
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_add_require_perm.py')
s = io.open(P, encoding='utf-8').read()

old = """                    # 找该方法前 8 行是否已有 RequirePerm
                    ctx = ''.join(lines[max(0, i - 8):i])
                    has_perm = '@RequirePerm' in ctx"""

new = """                    # 只在「同一方法」范围内判断：向上回溯到上一个映射注解/方法边界
                    span = []
                    for back in range(i - 1, max(-1, i - 15), -1):
                        prev = lines[back]
                        if '@RequirePerm' in prev:
                            span.append(prev)
                            break
                        if ('Mapping' in prev and '@' in prev) or 'class ' in prev \\
                                or prev.strip().startswith('}') or 'public ' in prev \\
                                or 'private ' in prev:
                            break
                        span.append(prev)
                    has_perm = any('@RequirePerm' in x for x in span)"""

if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('重复检测逻辑已修正')
else:
    print('未匹配，检查脚本内容')
