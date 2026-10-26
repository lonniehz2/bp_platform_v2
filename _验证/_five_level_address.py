# -*- coding: utf-8 -*-
"""标准地址支持五级（省/市/区县/街道/社区）：级联选择 + 社区编码回填。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'Orgs.vue')
s = io.open(P, encoding='utf-8').read()
n = 0

# 1) 新增弹窗：占位与说明
OLD1 = """                       placeholder="省 / 地市 / 区县 / 街道乡镇（点击逐级选择）"
                       style="width:100%" @change="onRegionChange" />
          <div class="muted" style="font-size:12px;margin-top:4px">
            数据来源：国家统计局五级行政区划（已载入省/市/区县/街道共
            {{ regionCount }} 条）
          </div>"""
NEW1 = """                       placeholder="省 / 地市 / 区县 / 街道 / 社区（点击逐级选择）"
                       style="width:100%" @change="onRegionChange" />
          <div class="muted" style="font-size:12px;margin-top:4px">
            数据来源：国家统计局五级行政区划（省/市/区县/街道/社区，共
            {{ regionCount }}）
          </div>"""
if OLD1 in s:
    s = s.replace(OLD1, NEW1, 1)
    n += 1

# 2) 社区提示：选了第五级会自动带出
OLD2 = """          <div class="muted" style="font-size:12px;margin-top:4px">
            区划库为省/市/区县/街道四级；社区/村请从下拉选择已录入社区，或直接输入新名称
          </div>"""
NEW2 = """          <div class="muted" style="font-size:12px;margin-top:4px">
            在标准地址里选到第五级会自动填入；也可在此手工输入或从历史社区中选择
          </div>"""
if OLD2 in s:
    s = s.replace(OLD2, NEW2, 1)
    n += 1

# 3) 编辑弹窗：占位
OLD3 = """                       placeholder="如需修改，请重新逐级选择"
"""
NEW3 = """                       placeholder="如需修改，请重新逐级选择（省/市/区县/街道/社区）"
"""
if OLD3 in s:
    s = s.replace(OLD3, NEW3, 1)
    n += 1

# 4) onRegionChange：支持第五级社区
OLD4 = """  // 代码逐级落到表单，供后端保存（第五级社区允许手填，故不存代码）
  f.provinceCode = codes[0] || ''
  f.cityCode = codes[1] || ''
  f.districtCode = codes[2] || ''
  f.streetCode = codes[3] || ''
  if (f.streetCode) {
    loadCommunities(f.streetCode)
  }
  // codes 是逐级代码，按顺序映射到 省/市/区县/街道
  req.get('/sys/regions/path', { params: { code: codes[codes.length - 1] } })
    .then((path) => {
      const names = (path || []).map((x) => x.name)
      f.province = names[0] || ''
      f.city = names[1] || ''
      f.district = names[2] || ''
      f.street = names[3] || ''
    })
    .catch(() => { /* 忽略，保留已填名称 */ })"""
NEW4 = """  // 代码逐级落到表单（第五级社区也有编码，一并保存）
  f.provinceCode = codes[0] || ''
  f.cityCode = codes[1] || ''
  f.districtCode = codes[2] || ''
  f.streetCode = codes[3] || ''
  f.communityCode = codes[4] || ''
  if (f.streetCode) {
    loadCommunities(f.streetCode)
  }
  // codes 是逐级代码，按顺序映射到 省/市/区县/街道/社区
  req.get('/sys/regions/path', { params: { code: codes[codes.length - 1] } })
    .then((path) => {
      const names = (path || []).map((x) => x.name)
      f.province = names[0] || ''
      f.city = names[1] || ''
      f.district = names[2] || ''
      f.street = names[3] || ''
      if (names[4]) {
        f.community = names[4]
      }
    })
    .catch(() => { /* 忽略，保留已填名称 */ })"""
if OLD4 in s:
    s = s.replace(OLD4, NEW4, 1)
    n += 1

# 5) 条数文案
OLD5 = "const regionCount = ref('31 万+')"
NEW5 = "const regionCount = ref('约 66 万条')"
if OLD5 in s:
    s = s.replace(OLD5, NEW5, 1)
    n += 1

# 6) 清空时一并清 communityCode
OLD6 = """    f.provinceCode = ''; f.cityCode = ''; f.districtCode = ''; f.streetCode = ''
    communityOptions.value = []"""
NEW6 = """    f.provinceCode = ''; f.cityCode = ''; f.districtCode = ''; f.streetCode = ''
    f.communityCode = ''
    communityOptions.value = []"""
if OLD6 in s:
    s = s.replace(OLD6, NEW6, 1)
    n += 1

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Orgs.vue 五级地址改动:', n, '/ 6')
