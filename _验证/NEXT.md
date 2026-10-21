# 交接状态（每个会话开始只读这个文件）

> 更新时间：2026-10-21（第 33 轮）　｜　新会话开工前 30 秒读完即可接上
> 详细记录见 `../05_首期功能完整性检查报告.md` 附录 P~T

## 1. 环境速查

| 项 | 值 |
|---|---|
| 后端 | Spring Boot 3.2.5 / Java 17，`backend/` |
| 前端 | Vue3 + Vite，`frontend/`，产物直接进 `backend/src/main/resources/static` |
| VM | `192.168.31.11:8080`，用户 `luo` / `hzbit56771010` |
| MySQL | `192.168.31.153:33306`，root / `5677@Mysql`，库 `bp_platform` |
| 部署 | `python _deploy.py --upload <jar>`；**必须看到「已提权 root」，否则等于没部署** |
| root 命令 | `python _root_cmd.py "<命令>"`（luo 无 sudo，走 su） |
| 日志 | `/var/log/bp-platform/app.log`（**别用 journalctl**，那里只有系统消息） |
| git | `D:\Work\tools\PortableGit\cmd\git.exe`，裸仓库 `D:\Work\git-repos\bp-platform.git` |

**铁律**
- 改前端必须 `pnpm build` 并看退出码（`_check_build.py` 查的是上次产物，会误报通过）
- `mvn package -DskipTests` **不编译测试类**，已被 `clean` 暴露过一次，定期 `clean`
- 写表单/查询参数前先读真实 DTO，禁止猜字段名（已踩坑：`status` vs `contractStatus`/`todoStatus`）
- 断言前清空 `.el-message`（toast 存活 3 秒，会污染下一条断言）
- 多用例浏览器测试必须**整页重载隔离**，否则残留弹窗导致点击落空
- `.el-menu-item` 文本要用 `textContent` 取（`innerText` 对折叠项返回空）

## 2. 当前状态

**已上线可用**
- 合同：新建（9 必填）/ 状态链 草稿→待签→签约中→履约 / 关键字+状态筛选
- 合同驱动房源占用：签约占房、终止退房、续签延期（`OccupancyService`）
- 统一待办中心 `/todos`：角标 + 7 类聚合 + 筛选 + 只看我的 + 批量完成/已读 + 去处理跳转
- 列表页筛选：25 个单 toolbar 页有查询+清空；FilterBar 支持折叠「更多筛选」
- 多 tab 页面**路由驱动**：`/ops-extras/rule`、`/rbac/role`、`/sys/dict`、`/ops-center/house` 等 19 条深链可用
- 表单化（JSON → 结构化表单）：**6 个页面** 告警/申诉/投诉/信用惩戒/换房/钥匙包
- 404 不再被包装成 500（`GlobalExceptionHandler` 单独处理 `NoResourceFoundException`）

**当前阻塞**
- ⚠️ **VM `192.168.31.11` 从第 32 轮起完全不可达**（HTTP 与 SSH 均超时）。
  第 32 轮的钥匙包表单化**已构建打包但未部署、未验证**。

**已知未修**
| # | 项 | 影响 |
|---|---|---|
| 1 | 侧边栏子菜单缺 OpsExtras 的 6 个 tab（另 3 页 9 个正常） | 展示层，不影响业务 |
| 2 | 剩余表单化 2 处：OpsExtras 多表单、FeeItems 的 `priceConfig` | 功能可用性 |
| 3 | 4 个多 tab 页面各 tab 仍共用一套 toolbar | 体验 |
| 4 | 表单化专项 24/25 待复验（钥匙包「卡类必须设有效期」修复未实测） | 验收口径 |

## 3. 下一步（VM 恢复后按序执行）

```bash
python _deploy.py --upload ../backend/target/bp-platform.jar   # 看「已提权 root」
node _check_jsonform_ui.js        # 期望 25/25
python _check_all.py              # 四项静态
python _check_ui.py               # 43 页冒烟
python _check_e2e.py              # 10 条业务闭环
python _cleanup_e2e.py            # 清测试数据（表单化 6 页都会留数据）
```

VM 长期不可用时的纯本地工作：
1. 补 05 报告附录 U（表单化改造记录 + 三个规则发现）
2. 给 `_cleanup_e2e.py` 加自校验（删完再 count，不为 0 则报错）
3. 给 `_check_ui.py` 加自校验（读到的路由数 ≠ 枚举数时报错）——第 21 轮曾因正则漏匹配导致页数静默从 43 掉到 39

## 4. 更长期的目标缺口

目标要求「可扩展到宿舍/公寓/酒店民宿/园区/物业」，当前仍是**保障房单业态**。缺：
- 多业态配置（房源类型已支持 DORM/HOTEL/APARTMENT，但计费、准入、合同模板未按业态分支）
- 车辆/停车、巡房、备案、供应商、日租等模块
- 微信小程序端（外部依赖：备案主体 + 短信通道）
