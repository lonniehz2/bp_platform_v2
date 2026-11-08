import io
p=r'platform-docs\19-多场景平台总体设计基线.md'
s=io.open(p,encoding='utf-8').read()
marker='## 0. 已确认决策'
record='''## 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-09 | 初始设计基线，五项核心目标 |
| v1.1 | 2026-11-09 | 核心目标调整为八项；新前端改为技术约束；补充目标映射、安全、数据、稳定、可持续设计 |

---

'''
s=s.replace(marker,record+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('change record')
