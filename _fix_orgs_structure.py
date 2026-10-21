# -*- coding: utf-8 -*-
"""修复 Orgs.vue：把误插的对话框移到模板末尾"""
import io

P = r'D:\Work\业务平台开发\frontend\src\views\Orgs.vue'
L = io.open(P, encoding='utf-8').read().split('\n')

# 1) 取出 36~67 行那段（被误插的 dialog + 提前闭合的 </div></template>）
start = None
for i, ln in enumerate(L):
    if '<el-dialog v-model="createVisible" title="新增组织"' in ln:
        start = i
        break

if start is None:
    print('未找到误插对话框')
else:
    # 向上找 el-dialog 前的空行，向下找第二个 </template>（对话框结束）
    end = None
    for j in range(start, len(L)):
        if L[j].strip() == '</el-dialog>':
            end = j
            break
    block = L[start:end + 1]
    # 删除该块 + 其后紧跟的 「  </div>」「</template>」两行（被提前闭合的）
    del_from, del_to = start, end
    if del_to + 1 < len(L) and L[del_to + 1].strip() == '</div>':
        del_to += 1
    if del_to + 1 < len(L) and L[del_to + 1].strip() == '</template>':
        del_to += 1
    L = L[:del_from] + L[del_to + 1:]

    # 2) 插入到真正的模板末尾（最后一个 </template> 之前）
    last_tpl = None
    for i in range(len(L) - 1, -1, -1):
        if L[i].strip() == '</template>':
            last_tpl = i
            break
    if last_tpl is None:
        print('未找到模板结尾')
    else:
        # 在最后一个 </template> 前补 </div> 已经在原处，这里直接插对话框
        L = L[:last_tpl] + [''] + block + L[last_tpl:]

io.open(P, 'w', encoding='utf-8').write('\n'.join(L))

s = io.open(P, encoding='utf-8').read()
print('template 开始:', s.count('<template>'), ' 结束:', s.count('</template>'))
print('el-dialog:', s.count('<el-dialog'), ' /el-dialog:', s.count('</el-dialog>'))
print('div:', s.count('<div'), '/div:', s.count('</div>'))
