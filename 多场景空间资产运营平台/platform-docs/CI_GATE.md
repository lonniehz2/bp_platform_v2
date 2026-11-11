# CI 门禁

必须在 GitHub 仓库设置中开启分支保护，并把以下 job 设为 required。

## 必需检查

```text
i18n-check / i18n
scene-e2e / scene-e2e
```

`i18n-check` 包含：

```text
check-i18n --strict
check-i18n-en
check-scene
check-ui-labels
check-field-labels
check-menu-labels
check-report-csv
```

`scene-e2e` 使用 MySQL service：

```text
执行 001–027 迁移
执行 seed
构建后端
启动 8091
调用 /api/v1/auth/login
校验三个场景菜单/角色
```

## Branch protection 建议

```text
Require a pull request before merging
Require status checks to pass
Require branches to be up to date
Do not allow bypassing the above settings
```

## 本地无法代替 CI

本地脚本 `check-scene-data.mjs` 和 `smoke-en-pages.cjs` 只能作为补充验证，
合并门禁必须以 CI 的 `scene-e2e` 为准。
