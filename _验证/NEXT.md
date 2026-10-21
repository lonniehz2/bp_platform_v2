# 交接状态（每个会话开始只读这个文件）

> 更新时间：2026-10-21　｜　用途：新会话开工前 30 秒读完即可接上
> 详细记录看 `../05_首期功能完整性检查报告.md` 附录 P/Q/R/S/T（按需读）

## 1. 环境速查

| 项 | 值 |
|---|---|
| 后端 | Spring Boot 3.2.5 / Java 17，`backend/` |
| 前端 | Vue3 + Vite，`frontend/`，构建产物直接进 `backend/src/main/resources/static` |
| VM | `192.168.31.11:8080`，用户 `luo` / `hzbit56771010` |
| MySQL | `192.168.31.153:33306`，root / `5677@Mysql`，库 `bp_platform` |
| 部署 | `python _deploy.py --upload <jar>`；**su 提权偶发失败，重跑一次即可** |
| root 命令 | `python _root_cmd.py "<命令>"`（走 su，无 sudo 权限时的唯一通道） |
| 演示账号 | 租户 `350600`，`admin/admin123` |

**铁律**
- 改前端必须 `pnpm build` **看退出码**（`_check_build.py` 查的是上次产物，会误报通过）
- 写表单/查询参数前先读真实 DTO，禁止猜字段名
- 后端参数名与前端传参必须核对（已踩过两次：`status` vs `contractStatus` / `todoStatus`，都是静默失效）
- 交付前跑：`_check_all.py` → `_check_ui.py` → `_check_e2e.py`

## 2. 当前状态

**已上线可用**
- 合同：新建（9 必填）/ 状态链 草稿→待签→签约中→履约 / 关键字+状态筛选
- 合同生效驱动房源占用（`OccupancyService`），签约占房、终止退房
- 统一待办中心 `/todos`：角标、7 类聚合、筛选（状态/类型/关键字/日期）、只看我的、批量完成/已读、去处理跳转
- FilterBar 组件（折叠「更多筛选」），已接入：计费项目、退租管理、配租批次（UI）
- 列表页「清空」：25 个单 toolbar 页面已补
- 表单化：告警、申诉（JSON 文本框 → 结构化表单）

**当前阻塞（已更正 2026-10-21）**

> ⚠️ 前一版本写的「配租模块读接口全 500」是**误报**，已撤销。
> 真实路径是 `/api/v1/allocation/allocations`（三级），不是 `/allocations`。
> 实测：`/allocation/allocations` → 200/total=3，`/allocation/batches` → 200/total=1，
> `/allocation/waiting` → 200/total=4。**配租模块健康**。

1. **【真缺陷】404 被包装成 500**：访问不存在的接口时，Spring 抛
   `NoResourceFoundException`（落到静态资源处理器），被 `GlobalExceptionHandler`
   的 `@ExceptionHandler(Exception.class)` 捕获 → 返回 `BP99999 系统异常 / 500`。
   后果：路径写错、接口缺失这类问题全部表现为「系统异常」，排查时被严重误导
   （本项目就这么误判了一整个模块）。
   修法：在 `GlobalExceptionHandler` 里加
   `@ExceptionHandler(NoResourceFoundException.class)` → `BP30001 / 404`。
2. 押金退费页筛选未做：`/fin/deposits` 参数未确认，页面同时读 `/fin/deposits` + `/fin/refunds`

**日志在哪（重要）**
```
/var/log/bp-platform/app.log   ← 应用日志（标准输出），已 385MB，异常全在这
/var/log/bp-platform/err.log   ← 空
```
读法：`python _root_cmd.py "tail -c 2000000 /var/log/bp-platform/app.log | grep -A10 '未处理异常'"`
（**别**用 `journalctl -u bp-platform`，那里只有系统生命周期消息）

## 3. 下一步（按顺序，第一条命令已给全）

### 第 1 步：修「404 被包装成 500」（真缺陷，改动很小）
`GlobalExceptionHandler` 加：
```java
@ExceptionHandler(org.springframework.web.servlet.resource.NoResourceFoundException.class)
public ResponseEntity<R<Void>> handleNoResource(NoResourceFoundException e, HttpServletRequest req) {
    log.warn("接口不存在 {} {}", req.getMethod(), req.getRequestURI());
    return ResponseEntity.status(404).body(R.fail(ErrorCode.NOT_FOUND));
}
```
改完 `package` → `_deploy.py --upload` → 再访问一个不存在的路径，应返回 404/BP30001 而不是 500。

### 第 2 步：给冒烟加「接口非 5xx」断言
`_check_ui.py` 43/43 全绿却漏掉整个配租模块——它只验「页面能渲染」。
在 `ui_smoke.js` 里拦截 response，凡 `status >= 500` 记为失败。改完重跑，可能还有别的「假通过」页面。

### 第 3 步：多 tab 页面拆成独立路由（方案已定）
| 原页面 | 拆成 |
|---|---|
| Rbac (3) | `/rbac/users`、`/rbac/roles`、`/rbac/perms` |
| SysAdmin (3) | `/sys/dicts`、`/sys/fields`、`/sys/config` |
| OpsCenter (3) | `/ops/houses`、`/ops/persons`、`/ops/workorders` |
| OpsExtras (7) | `/ops/messages`、`/ops/rules`、`/ops/open`、`/ops/rbac`、`/ops/revoke`、`/ops/day-status`… |

每页 4 步：抽出 tab 内容成独立组件 → 父页面删 `el-tabs` → 加路由（`meta.group` 不变即成为子菜单）→ 旧路径 `redirect` 到第一个子页。
拆完每页立刻用 `_check_filter_ui.js` 验清空。**先拆 OpsExtras（7 个，收益最大）**。

### 第 4 步：收尾
- 剩余页面补筛选（押金、工单、消息、机构等，FilterBar 已就绪，每页约 3 处改动）
- 给账单/合同/退费加日期范围（放进 FilterBar 的 `#more` 槽）
- 补 05 报告附录 U（表单化 + 两个死弹窗）、附录 V（日志盲区教训）

## 4. 已知缺陷清单（未修）

| # | 缺陷 | 位置 |
|---|---|---|
| 1 | 配租模块读接口全 500 | `/allocations/*` |
| 2 | `BatchStatus.valueOf(null)` NPE 未兜住 | `BatchVO.from` |
| 3 | 系统无日志出口，异常不可见 | systemd unit |
| 4 | 冒烟只验渲染，不验接口状态码 | `ui_smoke.js` |
| 5 | 剩余 5 个 JSON 编辑器页面 | Complaints / Credits / Exchanges / Keyring / OpsExtras / FeeItems.priceConfig |
| 6 | 多 tab 页面无清空 | Rbac / SysAdmin / OpsCenter / OpsExtras |
| 7 | `_check_jsonform_ui.js` 的「空提交」断言匹配过宽（只认「请填写」三字，会读到上一条残留提示） | 测试脚本 |
