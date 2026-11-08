import io
p=r'platform-frontend\README.md'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''收费与账务
设备与授权
菜单与角色''','''收费与账务
押金与补贴
设备与授权
合同变更
审批中心
菜单与角色''')
s=s.replace('''收费与账务：账单列表、收款''','''收费与账务：账单列表、收款
押金与补贴：押金收取/退还、补贴新增
合同变更：创建、提交、审批
审批中心：任务列表、通过/驳回、记录''')
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'platform-docs\06-前端操作台.md'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''### 收费与账务''','''### 押金与补贴

```text
押金收取
押金退还
押金流水
租金补贴
```

### 合同变更

```text
租金变更
期限变更
退租
提交审批
审批通过/驳回
```

### 审批中心

```text
工作流任务列表
通过
驳回
审批记录
```

### 收费与账务''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('docs updated')
