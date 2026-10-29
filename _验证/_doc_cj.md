
---

## 附录 CJ　平台运营台与平台信息维护（2026-10-30）

### 一、入口与账号

| 项 | 说明 |
|---|---|
| 运营台入口 | `#/platform-admin/login`（独立登录页，不输入平台编码） |
| 初始超管 | `opsadmin` / `Ops@123456`（首次登录强制改密） |
| 会话方式 | 独立 `X-Operator-Token`，与业务 Token 不互通，12 小时有效 |
| 业务入口 | 业务登录页底部「平台运营登录」可跳转 |

### 二、平台生命周期

| 操作 | 规则 |
|---|---|
| 创建 | 名称、6 位行政区划、类型、联系人；编码按「行政区划 + 3 位序列」自动生成（如 `350699001`），不可修改；同时创建默认组织「平台」和平台管理员，初始密码只显示一次 |
| 修改 | 名称、类型、区域、联系人可改；编码不可改 |
| 停用 | 拒绝新登录，现有会话置为失效；数据保留 |
| 启用 | 停用平台可重新启用 |
| 归档 | 仅「停用」状态可归档；归档需输入平台编码确认；不物理删除；归档后不可登录 |
| 恢复 | 归档 → 停用，需再手动启用 |

### 三、平台管理员

- 新增：账号 + 姓名 + 联系方式，初始密码一次性显示；
- 重置密码：一次性显示，标记「待改密」；
- 启用/停用/解锁；每个平台至少保留 1 个启用管理员；
- 平台管理员登录后若「待改密」，弹出不可关闭的改密对话框，改密成功后才能继续。

### 四、平台信息维护（平台侧）

- 入口：系统与数据 → 平台信息；
- 平台编码、类型、区域、隔离模式、状态均只读；
- 仅平台名称可改，保存后顶部「平台名 · 组织」即时刷新；
- 状态由运营台控制，平台侧不可自行停用。

### 五、主要接口

```
POST /api/v1/platform-admin/auth/login
POST /api/v1/platform-admin/auth/change-password
POST /api/v1/platform-admin/auth/logout
GET/POST /api/v1/platform-admin/platforms
GET/PUT  /api/v1/platform-admin/platforms/{id}
POST     /api/v1/platform-admin/platforms/{id}/enable|disable|archive|restore
GET/POST /api/v1/platform-admin/platforms/{id}/admins
POST     /api/v1/platform-admin/platforms/{id}/admins/{uid}/reset-password|enable|disable|unlock
GET      /api/v1/platform-admin/audits
GET      /api/v1/public/platform-branding?code=350600
GET/PUT  /api/v1/platform/info        # 平台侧，PUT 仅 tenantName
POST     /api/v1/auth/change-password # 业务用户首次改密
```

### 六、验证记录

- 运营登录 → 平台列表 → 创建平台（350699001）→ 平台管理员登录 → 停用后登录被拒（403）→ 归档，全链路通过；
- 首次登录强制改密：弹窗出现、改密后关闭，业务页面正常；
- 平台信息：编码只读、类型/区域/状态只读，改名成功并还原；
- 一键验收管线 16 项全部通过。
