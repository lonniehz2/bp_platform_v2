# 新场景接入契约（SCENE ONBOARDING）

新增场景不能只加前端路由。必须按以下顺序完成。

## 1. 场景定义

先确定并评审：

```text
sceneCode：大写英文，例如 PARK
场景名称：例如 园区运营
路由前缀：例如 /park
默认首页：/park/dashboard 或 /park/cockpit
```

同时更新：

```text
platform-frontend/src/scene.js
SCENE_ROUTES
```

## 2. 菜单模板

必须通过 SQL 迁移新增，禁止只改前端 `navConfig`。

字段：

```text
id
scene_code = 新场景
menu_code
parent_code
menu_name
menu_type = GROUP / PAGE
route = /新前缀/...
sort_no
menu_status = ENABLED
```

最低要求：

```text
10 个一级分组
每个分组至少 1 个页面
```

## 3. 角色模板

每个场景至少 4 个角色：

```text
<SCENE>_ADMIN
<SCENE>_MANAGER
<SCENE>_FINANCE
<SCENE>_STEWARD
```

必须完成：

```text
bp_role 插入
bp_role_menu 授权
bp_user_role 绑定
```

不允许复制 `GUARANTEE_*` 角色编码到新场景。

## 4. 数据范围

确认相关表都有：

```text
tenant_id
scene_code
project_id / org_id
```

确认以下代码支持新场景：

```text
DataScopeService
PermissionInterceptor
MenuService.userMenuTree
报表查询
```

## 5. 报表

新场景报表必须定义：

```text
报表 key
中英文标题
列定义
数据接口
场景过滤
CSV 表头
```

## 6. 国际化

新增页面必须：

```text
所有文案 t()
所有枚举 enumLabel(value, domain)
所有详情字段 field.*
所有 API 错误 messageKey
```

菜单名称必须加入：

```text
platform-frontend/scripts/menu-design.json
```

## 7. 验收命令

```bash
cd 多场景空间资产运营平台/platform-frontend
node scripts/check-i18n.mjs --strict
node scripts/check-i18n-en.mjs
node scripts/check-scene.mjs
node scripts/check-ui-labels.mjs
node scripts/check-field-labels.mjs
node scripts/check-menu-labels.mjs
node scripts/check-report-csv.mjs
node scripts/check-scene-data.mjs
```

英文页面：

```bash
cd ../platform-local/scripts
node smoke-en-pages.cjs
```

数据库级场景 E2E：

```text
.github/workflows/scene-e2e.yml
```

## 8. 合并前检查

```text
[ ] 新场景菜单已写入迁移
[ ] 新场景 4 个角色已创建
[ ] 用户角色已绑定
[ ] 场景路由前缀已加入 SCENE_ROUTES
[ ] 报表场景过滤已验证
[ ] 中英文菜单词条已补齐
[ ] check-scene-data 通过
[ ] en-smoke 通过
```

## 9. 禁止事项

```text
禁止只加前端路由不加菜单 SQL
禁止复用 GUARANTEE_* 角色编码
禁止在页面硬编码场景名
禁止绕过 enumLabel 输出枚举
禁止把测试数据带入演示环境
```
