# 云门道业务平台 · 后端工程

Spring Boot 3.2.5 + Java 17 + MyBatis-Plus + MySQL 8.x + Redis + RabbitMQ

---

## 一、环境要求

| 项 | 版本 | 本机安装位置 |
|---|---|---|
| JDK | 17（Temurin 17.0.20.1） | `D:\Work\tools\jdk-17.0.20.1+1` |
| Maven | 3.9.9 | `D:\Work\tools\apache-maven-3.9.9` |
| MySQL | **8.0 / 8.4**（双版本兼容） | 测试实例 `192.168.31.153:33306` |
| Redis | 6+ | 同机（待确认端口） |
| RabbitMQ | 3.10+（建议装 `rabbitmq_delayed_message_exchange`） | 同机（待确认） |

> 环境变量已写入用户配置：`JAVA_HOME`、`PATH`（含 JDK 与 Maven 的 bin）。
> **新开终端**即可直接使用 `mvn` / `java`。

---

## 二、构建与测试

```powershell
cd D:\Work\业务平台开发\backend

# 编译
mvn -s D:\Work\tools\m2-settings.xml -B compile

# 单元测试
mvn -s D:\Work\tools\m2-settings.xml -B test

# 打包
mvn -s D:\Work\tools\m2-settings.xml -B package -DskipTests
```

> `-s D:\Work\tools\m2-settings.xml` 指定阿里云镜像与本地仓库 `D:/Work/tools/m2repo`，
> 可显著加速依赖下载。也可把它复制到 `%USERPROFILE%\.m2\settings.xml` 后省略 `-s`。

**当前状态**：`mvn test` → **Tests run: 22, Failures: 0, Errors: 0 — BUILD SUCCESS**

---

## 三、M0 里程碑：IoT 签名工具（已完成并验证）

协议 v2（`v2-hmac-sha256`）的完整实现与验证工具，**零第三方依赖**（纯 JDK），
可脱离 Spring 单独编译运行。

### 3.1 自测（26 项，全部通过）

```powershell
# 方式一：Maven 测试
mvn test -Dtest=SignatureProtocolTest

# 方式二：直接跑 CLI 自测（无需 Maven）
$jdk="D:\Work\tools\jdk-17.0.20.1+1"
$out="D:\Work\业务平台开发\backend\target\classes"
& "$jdk\bin\java.exe" "-Dfile.encoding=UTF-8" -cp $out com.yundao.bp.iot.tool.YmdCryptoVerify selftest
```

覆盖范围：
- **标准向量**：SHA-256（空串 / "abc"）、HMAC-SHA256（RFC 4231 TC2）
- **RFC3986 编码**：空格→`%20`、中文 UTF-8、保留字符、unreserved
- **规范串**：7 行结构、METHOD 大写、query 升序、空 body hash
- **安全性质**：篡改检测、错误密钥拒绝、nonce 随机性、密钥不泄露
- **字段加密**：AES-256-GCM 往返、随机 IV、AAD 绑定（换字段名/换 appId 必须失败）

### 3.2 与 IoT 方联调（排查签名不一致）

```powershell
# 生成签名头 + 打印规范串
java -cp $out com.yundao.bp.iot.tool.YmdCryptoVerify sign `
  --appId "ymd-biz-prod" --secret "<密钥>" `
  --method POST --path "/v1/lock/open" `
  --query "lockId=LK0001" --body '{"openType":"1049"}'
```

输出示例：
```
===== Canonical Request =====
POST ⏎ /v1/lock/open ⏎ lockId=LK0001 ⏎ f13f6edb... ⏎ 1792348496975 ⏎ 4122fefe... ⏎ k1
===== Signature =====
177b4c91497bd98bab93e46e633c7aae90b121d2b8ee55449ce95f9dd80afd66
===== Headers =====
X-Ymd-AppId:         ymd-biz-prod
X-Ymd-Timestamp:     1792348496975
X-Ymd-Nonce:         4122fefe58dcea807a7cc988b176f415
X-Ymd-KeyVersion:    k1
X-Ymd-Signature:     177b4c91497bd98bab93e46e633c7aae90b121d2b8ee55449ce95f9dd80afd66
X-Ymd-Proto:         v2-hmac-sha256
```

> **联调方法**：把 `Canonical Request` 与 `Signature` 发给 IoT 侧逐字符比对
> （`⏎` 表示换行符）。这是定位签名差异最快的手段。

### 3.3 ⭐ 现网协议实现（一期主力）

`com.yundao.bp.iot.legacy` 包实现了**云门道现网 AES/MD5 协议**，
**已用真实凭证调用真实平台验证通过**。

| 类 | 职责 |
|---|---|
| `AesCbcStrategy` | AES 参数加解密（PBKDF2 + 固定盐 + CBC + 固定 IV + Base64） |
| `Md5Signer` | 请求签名（参数字典序 → MD5 大写） |
| `YmdClient` | 业务调用（token 管理 + 参数加密 + 签名 + 响应解密） |
| `YmdTokenManager` | Token 缓存与提前 5 分钟续期 |
| `JdkHttpTransport` / `YmdHttpTransport` | HTTP 传输（可注入假实现便于测试） |
| `dto/YmdLockInfo` | 门锁信息（含 `online()` / `batteryPercent()`） |

**算法要点**（来自 `算法参考.zip` 源码，已用文档示例验证）：

```
密钥 = PBKDF2WithHmacSHA1(token[:25], salt="4BDD60B281D31F1B70EC3AAA81F282BC", iterations=100, 16B)
加密 = AES/CBC/PKCS5Padding, IV="1269571869323221", 输出 Base64
签名 = MD5(参数按key字典序 "k=v&k=v").toUpperCase()
约定 = Content-Type 必须 JSON；time 用秒；version 传 "1.0.0"
```

**验证工具**：

```powershell
$cp = "target\classes;" + (Get-Content target\cp.txt -Raw).Trim()

# 离线自测（算法是否与官方一致）
java "-Dfile.encoding=UTF-8" -cp $cp com.yundao.bp.iot.tool.YmdLegacyVerify selftest

# 真实调用（凭证走环境变量）
$env:YMD_APP_KEY="..."; $env:YMD_APP_SECRET="..."; $env:YMD_AGENT_CODE="20261019001"
java "-Dfile.encoding=UTF-8" -cp $cp com.yundao.bp.iot.tool.YmdLegacyVerify live
```

**实测输出**：

```
门锁总数 = 36
在线     = 4 (11.1%)
有电量信息 = 24 台
✔ 现网协议打通
```

> 生成 classpath：`mvn dependency:build-classpath -Dmdep.outputFile=target\cp.txt`

**完整规范**：`_验证/IoT对接规范-定稿.md`

### 3.4 其他子命令

```powershell
java -cp $out com.yundao.bp.iot.tool.YmdCryptoVerify genkey      # 生成 AES-256 密钥
java -cp $out com.yundao.bp.iot.tool.YmdCryptoVerify enc --key K --appId A --field idCard --value 110101...
java -cp $out com.yundao.bp.iot.tool.YmdCryptoVerify dec --key K --appId A --field idCard --value <Base64>
java -cp $out com.yundao.bp.iot.tool.YmdCryptoVerify verify --secret S --canonical C --signature G
```

---

## 四、运行应用

```powershell
# 用环境变量覆盖连接（推荐）
$env:BP_DB_HOST="192.168.31.153"
$env:BP_DB_PORT="33306"
$env:BP_DB_USER="root"
$env:BP_DB_PWD="5677@Mysql"
$env:YMD_APP_ID="<IoT appId>"
$env:YMD_APP_SECRET="<IoT appSecret>"

mvn spring-boot:run
# 或
java -jar target/bp-platform.jar
```

访问 `http://localhost:8080/actuator/health` 验证启动。

---

## 五、目录结构

```
backend/
├── pom.xml
├── README.md
└── src/
    ├── main/
    │   ├── java/com/yundao/bp/
    │   │   ├── BpApplication.java          启动类
    │   │   ├── common/                     ✅ 通用层（已实现 12 个类）
    │   │   ├── iam/                        ✅ BC-01 租户与权限（组织 CRUD 已通）
    │   │   ├── asset/                      ✅ BC-02 空间与资产（空间树 + 房源状态机）
    │   │   ├── person/                     BC-03 人员与档案（待建）
    │   │   ├── grant/                      BC-04 权益与钥匙（待建）
    │   │   ├── biz/                        BC-05 业务办理（待建）
    │   │   ├── fin/                        BC-06 资金账务（待建）
    │   │   ├── iot/                        BC-07 设备与通信
    │   │   │   ├── legacy/                 ✅ 现网 AES/MD5 协议（一期，已实测打通）
    │   │   │   │   ├── AesCbcStrategy.java     AES 加解密（PBKDF2+固定盐+CBC）
    │   │   │   │   ├── Md5Signer.java          签名
    │   │   │   │   ├── YmdClient.java          业务调用
    │   │   │   │   ├── YmdTokenManager.java    Token 缓存
    │   │   │   │   ├── JdkHttpTransport.java   HTTP 传输
    │   │   │   │   └── dto/YmdLockInfo.java    门锁 DTO
    │   │   │   ├── sign/                   ⏸️ 二期 v2 协议
    │   │   │   │   ├── CanonicalRequest.java      规范串构造（RFC3986）
    │   │   │   │   ├── SignCredentials.java       凭证（secret 脱敏）
    │   │   │   │   ├── SignatureStrategy.java     策略接口
    │   │   │   │   ├── HmacSha256Strategy.java    v2 实现 ✅
    │   │   │   │   └── AesGcmFieldCipher.java     字段级 AES-256-GCM
    │   │   │   └── tool/
    │   │   │       └── YmdCryptoVerify.java       M0 验证工具 ✅
    │   │   └── ops/                        BC-08 告警与工单（待建）
    │   └── resources/
    │       └── application.yml
    └── test/java/com/yundao/bp/
        └── iot/sign/SignatureProtocolTest.java    22 个单测 ✅
```

---

## 六、配置说明

全部连接参数支持**环境变量覆盖**（见 `application.yml`）：

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `BP_DB_HOST` / `BP_DB_PORT` | 192.168.31.153 / 33306 | 数据库 |
| `BP_DB_USER` / `BP_DB_PWD` | root / 5677@Mysql | 账号 |
| `BP_DB_NAME` | bp_platform | 库名 |
| `BP_REDIS_HOST` / `BP_REDIS_PORT` | 同上 | Redis |
| `BP_MQ_HOST` / `BP_MQ_PORT` | 同上 | RabbitMQ |
| `YMD_APP_ID` / `YMD_APP_SECRET` | 空 | **IoT 凭证，必须配置** |
| `YMD_FIELD_CRYPTO` / `YMD_FIELD_KEY` | false / 空 | 敏感字段加密开关与密钥 |
| `YMD_PRINT_CANONICAL` | false | **仅测试环境**开启，打印规范串用于联调 |

> ⚠️ `YMD_APP_SECRET` 与 `YMD_FIELD_KEY` **禁止写入代码或提交到仓库**，应由密钥管理系统注入。

---

## 七、下一步（M1 · P0.1 可演示集合）

| 顺序 | 模块 | 内容 |
|---|---|---|
| 1 | `common` | `Result<T>` / `BizException` / `TenantContext`（TTL + 缺失即抛异常）/ 雪花 ID / 全局异常处理 |
| 2 | `iam` | 租户、组织、用户、角色、权限（含 MyBatis-Plus 租户插件） |
| 3 | `asset` | 空间树（楼栋→单元→楼层→房间→床位）、房源 |
| 4 | `person` | 人员主档、家庭、证件 |
| 5 | `iot` | HTTP 客户端 + 限流 + 调用日志（复用 §sign 的签名） |
| 6 | `grant` | 授权编排（异步队列 + 结果回调） |
| 7 | `ops` | 告警、工单 |
| 8 | `rpt` | 基础报表 + 大屏数据接口 |

**前置**：`02_架构与技术方案.md` §15 协议需与云门道 IoT 侧对齐（M0 工具已备好用于联调）。

---

## 八、已有验证证据

| 项 | 结果 | 位置 |
|---|---|---|
| DDL 真机执行（原 111 表） | 118/118 语句成功，0 失败 | `_调研/DDL真机验证报告.md` |
| 查询性能压测 | 分区裁剪正确、索引命中、幂等 `type=const` | `_调研/压测与查询性能验证报告.md` |
| **整合后 115 表 DDL** | 静态校验通过（115 表 / 2036 列 / 注释 100%） | 待公司网络恢复后真机验证 |
| **协议 v2 实现** | **22 个单测 + 26 项 CLI 自测全部通过** | 本工程 |
