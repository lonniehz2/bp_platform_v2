import io
p=r'platform-docs\19-多场景平台总体设计基线.md'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''## 13. 交付路线

### P0：交互基础

```text
SearchSelect
TreeSelect/CascadeSelect
EntityPickerModal
DetailDrawer
审批组件
草稿
批量框架
```''','''## 13. 交付路线

### P0：平台底座与交互基础

平台底座：

```text
租户/组织/权限数据范围
字段权限与脱敏
审计日志
主数据与编码
行政区划
审批引擎
金额阈值
财务口径
```

交互基础：

```text
SearchSelect
TreeSelect/CascadeSelect
EntityPickerModal
DetailDrawer
审批组件
草稿
批量框架
```

质量底座：

```text
接口契约
统一错误码
页面模板
关键流程回归
```''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('roadmap')
