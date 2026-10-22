# -*- coding: utf-8 -*-
"""把误插到 <template> 内部的 <style> 块移到文件末尾（scoped 样式才能生效）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Rbac.vue')

CSS_BLOCK = '''<style scoped>
.perm-group { border: 1px solid #ebeef5; border-radius: 4px; margin-bottom: 8px; }
.perm-group-head { background: #fafafa; padding: 6px 10px; border-bottom: 1px solid #ebeef5; }
.perm-group-body { padding: 6px 12px 10px; }
/* 二级：资源；三级：操作，逐级缩进，便于看清层级 */
.perm-res { margin-top: 6px; }
.perm-res-head { padding-left: 20px; }
.perm-actions { padding-left: 46px; display: flex; flex-wrap: wrap; gap: 4px 18px; margin-top: 2px; }
</style>
'''


def main():
    s = io.open(P, encoding='utf-8').read()
    # 定位模板中间那段 style
    i = s.find('<style scoped>')
    j = s.find('</style>', i)
    if i < 0 or j < 0:
        print('未找到内联 style 块')
        return 1
    inline = s[i:j + len('</style>')]
    s = s[:i] + s[j + len('</style>'):]
    # 清理空行
    s = s.replace('\n\n\n', '\n\n')
    # 追加到文件末尾
    if '.perm-res-head' not in s.split('</style>')[-1]:
        s = s.rstrip() + '\n\n' + CSS_BLOCK
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('已移除内联样式 %d 字符，并在末尾追加 scoped 样式' % len(inline))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
