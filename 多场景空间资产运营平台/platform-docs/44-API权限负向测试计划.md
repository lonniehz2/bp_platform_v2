# API 权限负向测试计划

> 目的：验证越权、非法状态、重复提交、跨范围访问被后端拒绝  
> 依据：36-权限负向复核、39-状态机与接口一致性检查、43-设计评审记录  
> 状态：计划已确认，实现阶段执行

---

## 1. 测试原则

```text
以后端响应为准
不以页面按钮隐藏作为权限验证
每个用例必须有正向对照
拒绝应返回明确错误码
拒绝也要写审计
```

期望状态码：

```text
401 未登录
403 无权限
404 不存在
409 状态冲突
422 业务校验失败
```

---

## 2. 测试角色

```text
平台管理员
租户管理员
场景管理员
项目管理员
窗口受理
审核员
财务（区级/根组织）
设备运维
保障对象
```

---

## 3. 测试数据

```text
项目 A：幸福里
项目 B：海棠家园
项目 A 人员：张三
项目 B 人员：李四
项目 A 合同：BC202611001
项目 A 账单：BL202611001
项目 A 房源：101
项目 B 房源：201
项目 A 设备：DV202611001
```

---

## 4. 负向用例

### NP-01 项目管理员跨项目看人员

```text
角色：项目 A 管理员
请求：GET /platform/persons/options?keyword=李四
预期：结果不含项目 B 人员
请求：GET /platform/persons/{李四ID}
预期：403 或 404
```

### NP-02 财务看平级组织

```text
角色：区 A 财务
请求：GET /billing/bills?orgId=区B
预期：403 或空列表
请求：GET /billing/bills/{区B账单}
预期：403
```

### NP-03 窗口直接收款

```text
角色：窗口
请求：POST /billing/bills/{id}/pay
预期：403
```

### NP-04 审核员转轮候

```text
角色：审核员
请求：POST /applications/{id}/waitlist
预期：403
```

### NP-05 设备运维修改账单

```text
角色：设备运维
请求：POST /billing/bills/{id}/adjust
预期：403
```

### NP-06 普通角色导入设备

```text
角色：窗口/财务/审核员
请求：POST /devices/import
预期：403
```

### NP-07 无导出权限导出

```text
角色：只读领导/客服
请求：GET /billing/bills/export
预期：403
审计：记录导出尝试
```

### NP-08 未授权角色无模板合同直通

```text
角色：窗口/财务
请求：POST /contracts/{id}/effective-without-approval
预期：403
```

### NP-09 根组织财务未授权

```text
角色：财务
请求：GET /billing/bills?scope=tenant
预期：403 或仅返回授权组织
```

### NP-10 跨租户访问

```text
请求：修改 X-Tenant-Id 访问其他租户
预期：401/403
审计：记录
```

### NP-11 跨项目配租

```text
角色：项目 A 管理员
请求：POST /allocations {houseId: 项目B房源}
预期：403/422
```

### NP-12 非空置房源配租

```text
请求：POST /allocations {houseId: 已配租房源}
预期：409
```

### NP-13 非法合同状态撤回

```text
请求：POST /contracts/{ACTIVE合同}/withdraw
预期：409
```

### NP-14 非法账单状态关闭

```text
请求：POST /billing/bills/{UNPAID}/close
预期：409
```

### NP-15 退款超过原收款

```text
请求：POST /payments/{id}/refund {amount > original}
预期：422
```

### NP-16 设备绑定第二个空间

```text
请求：POST /devices/{已绑定}/bind {spaceId: 其他空间}
预期：409
```

### NP-17 设备 MAC 重复

```text
请求：POST /devices/import 含重复 MAC
预期：失败行返回原因，其他行成功
```

### NP-18 重复收款

```text
请求：同一 Idempotency-Key 重复 POST /pay
预期：只产生一笔收款
```

### NP-19 重复配租

```text
并发两个请求配租同一房源
预期：一个成功，一个 409
```

### NP-20 选择器越权

```text
角色：项目 A 管理员
请求：GET /houses/options?projectId=项目B
预期：403 或空
```

---

## 5. 字段与导出

```text
身份证默认脱敏
手机号默认脱敏
无字段权限不返回原值
导出按字段权限
导出写审计
```

用例：

```text
NP-21 详情接口返回身份证明文 → 失败
NP-22 导出包含未授权字段 → 失败
NP-23 无权限下载附件 → 403
```

---

## 6. 非法状态用例

```text
DRAFT 合同直接归档 → 409
APPROVED 申请直接关闭 → 409
PAID 账单再次出账 → 409
WAIVED 账单收款 → 409
DISABLED 设备绑定 → 409
```

---

## 7. 审计验证

每个拒绝用例检查：

```text
是否记录操作人
是否记录接口
是否记录业务ID
是否记录拒绝原因
是否记录IP
```

---

## 8. 测试环境

```text
测试环境
独立租户
独立项目
测试账号按角色创建
测试数据可重置
```

---

## 9. 执行方式

```text
API 自动化优先
Postman/脚本均可
每次回归执行
失败阻断发布
```

---

## 10. 输出

```text
用例编号
请求
期望
实际
状态
证据
缺陷编号
```

---

## 11. 退出标准

```text
所有负向用例通过
无越权数据泄露
无非法状态穿透
重复提交幂等
审计记录完整
```

---

## 12. 结论

```text
计划已确认
待实现阶段执行
执行通过后才允许上线
```
