# -*- coding: utf-8 -*-
"""帮助与手册：房源导入模板中文化。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 帮助 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()
OLD = """          '「床位管理」：先在下拉中选择房间（按组织自动加载空间树），再批量生成床位；已存在的床位编号会自动跳过。',"""
NEW = """          '「床位管理」：先在下拉中选择房间（按组织自动加载空间树），再批量生成床位；已存在的床位编号会自动跳过。',
          '「批量导入」下载的模板是中文表头（组织编码/空间编码/房源编号/房源名称/房源类型/用途/建筑面积/租金标准/计价单位/房源状态），示例值也是中文，填好直接上传即可。',"""
n = 0
if OLD in s:
    s = s.replace(OLD, NEW, 1)
    n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助更新:', n)

# ---------- 手册附录 W ----------
P2 = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
t = io.open(P2, encoding='utf-8').read()
if '附录 W' not in t:
    t = t.rstrip() + '''

---

## 附录 W　房源批量导入模板中文化

### W.1 模板变化

| 项 | 改前 | 改后 |
|---|---|---|
| 表头 | `ORGANIZATION_CODE,SPACE_CODE,HOUSE_CODE,…` | **组织编码,空间编码,房源编号,房源名称,房源类型,用途,建筑面积(㎡),租金标准,计价单位,房源状态** |
| 示例值 | `PUBLIC_RENTAL / CIVIL / AREA_MONTH / VACANT` | **公租房 / 民用 / 元/㎡·月 / 空置** |
| 文件名 | `house-import-template.csv` | **房源导入模板.csv** |
| 示例行数 | 1 行 | 3 行（公租房 / 保障性租赁住房 / 人才公寓，含套·月与套·夜计价） |

### W.2 后端兼容策略

- 表头识别：英文（含 `HOUSE_CODE`）与中文（含「房源编号 / 组织编码 / 空间编码」）都能跳过
- 枚举值：中文自动转码，**英文码也照旧可用**（大小写不敏感）

| 字段 | 可填中文 |
|---|---|
| 房源类型 | 公租房 / 保障性租赁住房 / 人才公寓 / 公寓 / 宿舍 / 酒店民宿 / 出租房 |
| 用途 | 民用 / 商用 |
| 计价单位 | 元/㎡·月 / 元/套·月 / 元/床·月 / 元/套·夜 / 元/床·夜 |
| 房源状态 | 空置 / 可租 / 待配租 / 已配租 / 已出租 / 维修中 / 锁定 |

### W.3 实测

下载到的模板内容：

```
组织编码,空间编码,房源编号,房源名称,房源类型,用途,建筑面积(㎡),租金标准,计价单位,房源状态
DEMO-P1,P1-R1,HOUSE-001,示例房源1,公租房,民用,55,15,元/㎡·月,空置
DEMO-P1,P1-R2,HOUSE-002,示例房源2,保障性租赁住房,民用,48.5,18.5,元/套·月,空置
DEMO-P1,P1-R3,HOUSE-003,示例房源3,人才公寓,民用,32,1200,元/套·夜,待配租
```

上传后导入结果：**共 1 行，成功 1，跳过 0**；库中落值
`house_type=PUBLIC_RENTAL / use_type=CIVIL / rent_unit=AREA_MONTH / house_status=VACANT`（中文已正确转码）。

### W.4 其他导入模板排查

| 检查项 | 结论 |
|---|---|
| 后端 `*Controller` 里含 `import` 的接口 | 仅 `POST /houses/import` 一处 |
| 前端含「下载模板 / 批量导入」的页面 | 仅「房源台账」一处 |

即：当前系统**只有房源一个文件导入入口**，不存在其他英文模板。
'''
    io.open(P2, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 W')
