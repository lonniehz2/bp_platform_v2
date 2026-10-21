# -*- coding: utf-8 -*-
"""修正 ui_smoke.js 的登录逻辑（DOM 赋值 + 轮询等待）"""
import io
import re

P = r'D:\Work\业务平台开发\_验证\ui_smoke.js'
s = io.open(P, encoding='utf-8').read()

# 1) 定位输入块：从 'const inputs' 到 'throw new Error' 所在行的后续 '}'
start = s.find('const inputs = await page.')
if start < 0:
    start = s.find('const n = await page.evaluate')
if start < 0:
    print('未找到登录输入块')
else:
    throw_idx = s.find("throw new Error('登录表单结构不符", start)
    if throw_idx < 0:
        throw_idx = s.find('throw new Error(', start)
    # 找到该 throw 语句所在 if 块的结束：下一个 '\n    }\n'
    end = s.find('\n    }\n', throw_idx)
    end += len('\n    }\n') if end > 0 else 0

    NEW = '''    const n = await page.evaluate(() => document.querySelectorAll('input').length)
    if (n < 3) throw new Error('登录表单结构不符，输入框数=' + n)
    // 直接赋值 + 派发 input 事件，避免键盘输入重复与焦点丢失
    await page.evaluate(() => {
      const el = document.querySelectorAll('input')
      const set = (i, v) => {
        el[i].focus()
        el[i].value = v
        el[i].dispatchEvent(new Event('input', { bubbles: true }))
        el[i].dispatchEvent(new Event('change', { bubbles: true }))
        el[i].blur()
      }
      set(0, '350600')
      set(1, 'admin')
      set(2, 'admin123')
    })
    await sleep(300)
'''
    s = s[:start] + NEW + s[end:]

# 2) 轮询等待登录完成
s = s.replace('''    await sleep(3000)
    const loggedIn = await page.evaluate(() => !!document.querySelector('.el-menu, .rail'))''',
              '''    let loggedIn = false
    for (let i = 0; i < 30; i++) {
      await sleep(500)
      loggedIn = await page.evaluate(
        () => !!document.querySelector('.rail, .el-menu, .aside'))
      if (loggedIn) break
    }''')

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 已更新登录逻辑')

# 语法自检
import subprocess
r = subprocess.run(['node', '--check', P], capture_output=True, text=True)
print('  node --check: %s' % ('OK' if r.returncode == 0 else r.stderr[:200]))
