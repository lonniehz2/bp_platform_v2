# -*- coding: utf-8 -*-
"""补 orgApi 导入 + 加强错误提示（避免静默空白）"""
import io
import re

P = r'D:\Work\业务平台开发\frontend\src\views\Spaces.vue'
s = io.open(P, encoding='utf-8').read()

# 1) 补导入
if 'orgApi' in s and 'spaceApi, orgApi' not in s:
    s = s.replace("import { spaceApi } from '@/api/modules'",
                  "import { spaceApi, orgApi } from '@/api/modules'", 1)

# 2) loadOrgs：失败时给出可见提示，而不是静默空白
s = s.replace('''  } catch (e) { orgs.value = [] }
}

onMounted(loadOrgs)''',
              '''  } catch (e) {
    orgs.value = []
    ElMessage.error('组织列表加载失败：' + (e?.message || e))
  }
}

onMounted(loadOrgs)''', 1)

# 3) load：失败时提示具体原因
s = s.replace('''  } catch (e) { tree.value = [] }
}

function onSelect''',
              '''  } catch (e) {
    tree.value = []
    ElMessage.error('空间树加载失败：' + (e?.message || e))
  }
}

function onSelect''', 1)

# 4) 空态更明确
s = s.replace('<el-empty v-if="!tree.length" description="暂无空间数据" :image-size="60" />',
              '<el-empty v-if="!tree.length" description="暂无空间数据（可切换上方组织）" '
              ':image-size="60" />')

io.open(P, 'w', encoding='utf-8').write(s)

print('  导入行：')
for ln in s.split('\n'):
    if ln.strip().startswith('import '):
        print('    ' + ln.strip())
print('\n  orgApi 引用 %d 处 ｜ onMounted %d 处'
      % (s.count('orgApi'), s.count('onMounted(')))
