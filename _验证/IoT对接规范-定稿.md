# 云门道 IoT 平台对接规范（实测定稿）

| 项目 | 内容 |
|---|---|
| 状态 | ✅ **全部实测验证通过**（真实凭证 + 真实服务端） |
| 依据 | ① 接口文档 V2.0.0 ② **`算法参考.zip` 中的 JAVA 源码**（AES/Base64Util/MD5）③ 实测验证 |
| API 域名 | **`https://api.hzbit.cn:4443`** |
| 验证结果 | 成功取 token、成功调用 `getPtAgentLocks`、**成功解密响应**（取得 36 把锁的真实数据） |

> 本文档可直接作为集成层编码依据。所有结论均已用真实请求验证，非推测。

---

## 一、算法源码要点（来自 `算法参考.zip`）

### 1.1 AES.java 关键参数

```java
private static final String VIPARA = "1269571869323221";              // 固定 IV（16 字节）
private static final int    KEY_SIZE = 16;                            // AES-128
private static final String SALT = "4BDD60B281D31F1B70EC3AAA81F282BC"; // 固定盐
// 密钥派生：PBKDF2WithHmacSHA1
PBEKeySpec(password.toCharArray(), salt, 100 /*iterations*/, 16*8)
// 加密：AES/CBC/PKCS5Padding，输出 Base64
```

> ⚠️ **注意**：源码中 `AES_PWD = "GM56771314"` 这个常量**未被使用**；
> 实际密钥由调用方传入的 `pwd`（= `token.substring(0,25)`）经 **PBKDF2** 派生。
> 这正是"附件缺失"期间无法猜出的关键——用固定盐 + PBKDF2 迭代 100 次。

### 1.2 MD5.java

```java
byteToString(md.digest(strObj.getBytes("UTF-8"))).toUpperCase()
```

→ 「UTF-8 编码 → MD5 → 十六进制 → **大写**」，与本文 §2 一致。

### 1.3 已验证的实现等价性

用文档 §3.3 的示例验证：

| 项 | 值 |
|---|---|
| pwd | `5x41nO+EIYENqlj8FmG2XGXMa` |
| 明文 | `719B29DB1EF45F00D9C5CD320DAE6` |
| 文档密文 | `FeBrmAMo+eO63Uuojon/x/1mlWlRhTVL3f+QtwKTEpo=` |
| **本实现** | **`FeBrmAMo+eO63Uuojon/x/1mlWlRhTVL3f+QtwKTEpo=`** ✅ **完全一致** |

---

## 二、协议全貌（三步）

```
① 取 Token
   POST /ymd/auth-service/sys/getAccessToken
   Content-Type: application/json
   参数（明文）: appKey, appSecret, time(秒), version=1.0.0, sign
   sign = MD5_UPPER( "appKey=..&appSecret=..&time=..&version=.." )
   返回: data.token

② 密钥派生
   pwd = token.substring(0, 25)                     ← 取前 25 个字符
   key = PBKDF2WithHmacSHA1(pwd, SALT, 100, 16)     ← 16 字节

③ 调用业务接口
   POST /ymd/{service}/...
   Content-Type: application/json
   ★ 所有业务参数值用 AES 加密（Base64）
   time / token / version 保持明文
   sign = MD5_UPPER( 所有参数按 key 字典序 "k=v&k=v..." )
   响应 data 亦为 AES 密文 → 用同一 key 解密
```

---

## 三、逐项规范

### 3.1 公共约定

| 项 | 值 | 说明 |
|---|---|---|
| Content-Type | **`application/json;charset=UTF-8`** | ⚠️ 用 `x-www-form-urlencoded` 返回 **415** |
| `time` | **秒级**时间戳（10 位） | ⚠️ 用毫秒（13 位）会失败 |
| `version` | **`1.0.0`** | ⚠️ 传 `V1.0.0` 会被平台再加 V 前缀，报"VV1.0.0无此版本接口" |
| `token` 有效期 | 30 分钟 | 文档声明；建议提前 5 分钟续期 |
| 编码 | UTF-8 | 源码明确 `getBytes("UTF-8")` |

### 3.2 签名算法 `sign`

```python
def sign(params: dict) -> str:
    # 1) 所有参数（不含 sign 本身）按 key 字典序排序
    # 2) 拼成 "k1=v1&k2=v2&..."
    # 3) MD5（UTF-8 编码）→ 十六进制 → 大写
    s = '&'.join(f'{k}={params[k]}' for k in sorted(params))
    return hashlib.md5(s.encode('utf-8')).hexdigest().upper()
```

**参与签名的参数**：
- 取 token 时：`appKey`, `appSecret`, `time`, `version`
- 业务接口时：**全部参数**，包括加密后的业务参数值 + `appKey`/`appSecret`（若传）+ `time` + `token` + `version`

> ✅ 已用文档示例验证：`loginname=..&logpwd=..&time=1553595995&version=1.0.0`
> → `46812299FB1BC111AC69A27F99068BE2` **完全一致**

### 3.3 AES 参数加密

```python
IV   = b'1269571869323221'
SALT = b'4BDD60B281D31F1B70EC3AAA81F282BC'
ITER = 100
KEYLEN = 16

def derive_key(pwd: str) -> bytes:
    return hashlib.pbkdf2_hmac('sha1', pwd.encode('utf-8'), SALT, ITER, KEYLEN)

def encrypt(pwd: str, value: str) -> str:
    cipher = AES.new(derive_key(pwd), AES.MODE_CBC, iv=IV)
    return base64.b64encode(cipher.encrypt(pad(value.encode('utf-8'), 16))).decode()

def decrypt(pwd: str, b64: str) -> str:
    b64 = re.sub(r'\s+', '', b64)          # 响应密文可能含换行/空格
    cipher = AES.new(derive_key(pwd), AES.MODE_CBC, iv=IV)
    return unpad(cipher.decrypt(base64.b64decode(b64)), 16).decode('utf-8')
```

| 项 | 值 |
|---|---|
| 密钥派生 | **PBKDF2WithHmacSHA1**，salt=`4BDD60B281D31F1B70EC3AAA81F282BC`，iterations=**100**，keyLen=**16** |
| 模式 | **AES/CBC/PKCS5Padding** |
| IV | **`1269571869323221`**（固定，16 ASCII 字节） |
| 输出 | **Base64** |

### 3.4 哪些参数需要加密（实测确认）

| 接口 | 需加密的参数 |
|---|---|
| `getAccessToken` | **不加密**（appKey/appSecret/time/version 全明文） |
| `getPtAgentLocks` | **appKey、appSecret、agentCode 全部加密** |

> ⚠️ **易错点**：业务接口如果不传 `appKey`/`appSecret`，会被拒（`99990002`）；
> 传**明文** `appKey` 会报 `99990010 appKey参数解密异常`；
> **必须传加密后的 appKey/appSecret**。
> 这是我在实测中踩过的坑——顺序错会得到看似无关的错误码。

### 3.5 响应处理

- `status = "1"` 表示成功
- **成功时 `data` 是 AES 密文**（Base64），需用同一 key 解密后才能得到 JSON
- 解密后为 JSON 数组或对象
- 密文中可能夹带空白字符（换行），解码前需 `re.sub(r'\s+','',data)`

---

## 四、实测验证记录

### 4.1 取 Token ✅

```http
POST https://api.hzbit.cn:4443/ymd/auth-service/sys/getAccessToken
Content-Type: application/json

{"appKey":"4576A2026...","appSecret":"1D42A79...","time":"1792385072","version":"1.0.0","sign":"..."}
```

```json
{"status":"1","message":"操作成功","time":"1792384690",
 "data":{"token":"U9uzhll2owQ6dTAekDQXJkJBhah26KuAb/chNmtO8EbKVtL0U37z8tqIbbPbFaih"}}
```

### 4.2 获取代理商门锁清单 ✅

```http
POST https://api.hzbit.cn:4443/ymd/lockPt-service/pt/getPtAgentLocks
Content-Type: application/json

{"appKey":"X7+4nRvWq+Gir5yhXWilbs3pBxg/YTc5uAkRwFdZv10=",
 "appSecret":"U6qcn191q5UMFQXznvzerUOXV3mOoJL24a8rXtMgM6q1aFkoNzV4XAWHnGunkWSo",
 "agentCode":"oYhaxRQvswWILQAzkLFPmQ==",
 "time":"1792385072","token":"U9uz...","version":"1.0.0","sign":"..."}
```

响应：`{"status":"1","message":"操作成功","data":"<AES密文>"}`

**解密后（真实数据，36 把锁）**：

```json
[
  {"lockid":"17YLGJHZBIYMD202005161059","lockname":"比特大门人脸机","mac":"C0847D53B21A",
   "onlineStatus":"0","battery":null,"ventor":"485A4254","hdver":"001",
   "createtime":"2023-10-13 13:26:03","address2":"赛银","ischarge":"0","rssi":"80"},
  {"lockid":"07DC66D2F5144257AF94A8D3E5DC","lockname":"308","mac":"ED2503388308",
   "onlineStatus":"0","battery":"43%","ventor":"485A4254","hdver":"1016", ...}
  ...
]
```

### 4.3 数据字段与统计

| 字段 | 含义 | 备注 |
|---|---|---|
| `lockid` | 门锁 ID | 主键，可作为业务侧 `device_id` |
| `mac` | 门锁 MAC | 唯一 |
| `lockname` | 名称 | |
| **`onlineStatus`** | **在线状态** | `"0"` 离线 / `"1"` 在线 |
| **`battery`** | **电量** | 形如 `"43%"`；**门禁类设备为 `null`** |
| `ventor` | 厂商代码 | `485A4254` 等 |
| `hdver` | 硬件版本 | |
| `rssi` | 信号强度 | |
| `ischarge` | 是否充电 | |
| `createtime` | 创建时间 | |
| `address2` | 地址/备注 | 质量参差（有空值、有"3"这类） |

**实测统计（代理商 20261019001）**：

| 项 | 值 |
|---|---|
| 门锁总数 | **36** |
| `onlineStatus` 分布 | 离线 `0` = **32**，在线 `1` = **4**（在线率 11.1%） |
| `ventor` 分布 | `485A4254`=31, `487A4258`=2, `485A4258`=1, `47A5AD64`=1, `685A4259`=1 |

---

## 五、对项目阻塞项的影响

### 5.1 ✅ A2（AES/MD5 算法）—— **彻底关闭**

- 算法已从源码确认 + 文档示例验证 + 真实调用验证
- **不再需要"重新设计协议"**，现网协议可直接对接

### 5.2 ✅ A1（设备在线状态/电量批量查询）—— **确认可实现**

`getPtAgentLocks` 一次返回该代理商下**全部门锁**的 `onlineStatus` 与 `battery`：

- 在线率统计：`count(onlineStatus=="1") / total`
- 电量统计：解析 `battery` 百分数
- **无需额外接口**，直接满足漳州标"在线率 ≥98%、可用率 ≥99%"的统计需求

⚠️ **需注意**：**门禁类设备（人脸机、车闸等）的 `battery` 为 `null`**，
电量统计需按设备类型区分，否则平均值会被拉低。
建议：仅对 `ventor`/`lockname` 识别为"门锁"的设备统计电量。

### 5.3 对设计文档 §15（v2-hmac-sha256）的修正建议

原设计提出用 `v2-hmac-sha256` **替代** AES/MD5。现在 A2 已解除，建议改为：

| 方案 | 定位 |
|---|---|
| **现网 AES/MD5 协议** | ✅ **一期采用**（已验证可用） |
| `v2-hmac-sha256` | ⏸️ **二期可选增强**（需 IoT 侧同步改造，非必需） |

> 理由：现网协议虽然用 MD5 + 固定 IV（安全性一般），但**已可用且无需对方改造**。
> 一期应以"快速对接"为先；协议加固作为二期独立议题。

---

## 六、待确认的次要问题

| # | 问题 | 影响 | 建议 |
|---|---|---|---|
| 1 | 是否有 `limit`/分页参数？36 条一次返回，20 万设备时会怎样？ | 大批量拉取的性能 | 需实测或索取文档 |
| 2 | `onlineStatus` 是否有除 0/1 外的值？ | 统计口径 | 实测仅见 0/1 |
| 3 | 单次调用 QPS 限制 | 节流参数 | 需索取 |
| 4 | 是否有"设备状态变更回调" | 实时性 | 文档 §6.6 只有开门记录回调 |
| 5 | `battery` 为 null 的设备如何统计可用率 | 考核口径 | 建议单独口径 |
| 6 | 开门记录接口（§6.3）的参数与分页上限 | 17.5 亿记录拉取 | 需实测 |

---

## 七、可复现脚本

| 脚本 | 作用 |
|---|---|
| **`_验证/iot_client.py`** | ⭐ **完整客户端**（token + 加密 + 调用 + 响应解密），可直接复用 |
| `_验证/iot_call_correct.py` | 首次打通验证脚本 |
| `_验证/iot_token_json.py` | 取 token 的最小示例 |
| `_验证/iot_sign_calibrate.py` | 用文档示例校验 MD5 |
| `_验证/iot_aes_crack.py` | 早期离线尝试（失败，归档留证） |
| `_验证/iot_param_enc.py` | 判定哪些参数需加密 |
| `_调研/算法参考/` | 云门道提供的 AES/Base64Util/MD5 JAVA 源码 |

---

*本规范基于 `算法参考.zip` 源码 + 真实服务端实测。所有结论可复现。*
