# -*- coding: utf-8 -*-
"""给 v3 报告追加「验证资产与种子」「跨语言契约」章节"""
import io

P = r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md'
s = io.open(P, encoding='utf-8').read()

if '4.4 跨语言签名契约' in s:
    print('已追加，跳过')
    raise SystemExit

anchor = '''---

## 五、缺口清单（按对验收的影响排序）'''

block = '''### 4.4 ⭐ 跨语言签名契约测试（v3 新增）

开放平台的签名必须能被第三方（Python/Java/Go 等）独立复算。风险在于：只要待签串格式
有一点差异（结尾少个换行、方法名大小写），**所有第三方调用都会验签失败**，
而这种错误在单元测试里完全看不出来。

做法：用 Python 的 `hmac+hashlib` 独立算出固定向量，把结果作为常量写进 Java 测试：

```java
private static final String FIXTURE_SIGN =
        "bfd8aaf613b8ebad85623b253b49e2eb7e7fa1b241412ec44a1e04e793de7f61";

assertEquals(FIXTURE_SIGN, signer.sign("unit-test-secret", payload),
        "与 Python hmac 结果不一致，第三方将全部验签失败");
```

同时断言待签串的精确格式：

```
POST\\n/open/house.list\\n1700000000000\\nabc123\\n{"pageNum":1}
```

结果：**Java 与 Python 完全一致**。

### 4.5 验证资产（真机脚本，待内网执行）

| 脚本 | 断言数 | 覆盖 |
|---|---|---|
| `_verify_open.py` | 约 40 | 三道关卡（有效性/白名单与授权范围/签名防重放）、密钥一次性与重置、调用日志、用量统计、Webhook 订阅与推送留痕、权限 403 |
| `_verify_gov.py` | 约 40 | 适配器配置与鉴权脱敏、报送成功路径、明细逐条回滚可查、空数据集、失败补报精确性、降级（无适配器/无地址）、统计、权限 403 |
| `_seed_open_gov.py` | — | 权限 7 条、角色授权（**角色 ID 自省**，不硬编码）、字典 10 类 45 项、开放接口清单 8 个；支持 `--dry-run` |

两个验证脚本都做了**前置连通性守卫**：应用不可达时打印提示并以退出码 3 结束，不抛异常栈。

> ⚠️ 上述脚本与种子**尚未在真机执行**（编写时处于外网环境，应用与数据库不可达）。
> 回到内网后按以下顺序执行：
>
> ```bash
> python verify.py ddl          # 确认 9 张新表存在
> python _seed_open_gov.py      # 写入权限/字典/接口清单
> python _verify_open.py        # 开放平台
> python _verify_gov.py         # 监管报送
> python verify.py all          # 全量回归
> ```

''' + anchor

assert anchor in s
s = s.replace(anchor, block, 1)

# 同步更新证据来源表
s = s.replace(
    "| 真机接口验证（约 1100 项） | `_验证/_verify_*.py` 共 50+ 脚本 |",
    "| 真机接口验证（约 1100 项） | `_验证/_verify_*.py` 共 50+ 脚本 |\n"
    "| 开放平台/监管报送验证 | `_验证/_verify_open.py`、`_verify_gov.py`（待内网执行）|")

io.open(P, 'w', encoding='utf-8').write(s)
print('已追加 4.4 / 4.5 两节，报告行数 %d' % len(s.split('\n')))
