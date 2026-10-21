# -*- coding: utf-8 -*-
"""页面接入登录：自动登录 + 令牌注入 + 登录条"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'bpToken' in s:
    print('已接入，跳过')
    raise SystemExit

# ---------- 1) 找到 req() 里的 header 构造，注入 Authorization ----------
# 先看现有实现方式
import re
m = re.search(r'function req\(([^)]*)\)\s*\{', s)
assert m, '找不到 req 函数'
print('req 函数签名：function req(%s)' % m.group(1))

# 在 req 函数体最前面插入 header 补丁（更稳：包装 fetch）
marker = 'function req('
idx = s.index(marker)
# 找到 req 函数定义结束（下一个 "\nfunction " 之前）
nxt = s.find('\nfunction ', idx + len(marker))
req_src = s[idx:nxt]
print('req 函数长度 %d' % len(req_src))

# 采用全局包装：在 req 定义之后插入 token 注入逻辑
inject = '''

// ---------- 认证：令牌与登录 ----------
const BP_TOKEN_KEY = 'bp_token';
const BP_USER_KEY = 'bp_user';

function bpToken() { return localStorage.getItem(BP_TOKEN_KEY) || ''; }

/** 登录（成功后存令牌）。 */
function bpLogin(username, password, silent) {
  const body = JSON.stringify({ username: username, password: password, deviceType: 'WEB' });
  return fetch('/api/v1/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body
  }).then(r => r.json()).then(j => {
    if (j && j.code === 'BP00000' && j.data && j.data.token) {
      localStorage.setItem(BP_TOKEN_KEY, j.data.token);
      localStorage.setItem(BP_USER_KEY, JSON.stringify(j.data));
      bpRenderAuthBar(j.data);
      if (!silent) out.innerHTML = '<span class="ok">登录成功：' + (j.data.realName || j.data.username) + '</span>';
      return j.data;
    }
    if (!silent) out.innerHTML = '<span class="err">登录失败：' + (j && j.message) + '</span>';
    return null;
  }).catch(e => { if (!silent) out.innerHTML = '<span class="err">登录异常：' + e + '</span>'; return null; });
}

/** 自动登录（演示用：默认 admin）。 */
function bpAutoLogin() {
  if (bpToken()) { bpRenderAuthBar(JSON.parse(localStorage.getItem(BP_USER_KEY) || '{}')); return Promise.resolve(); }
  return bpLogin('admin', 'admin123', true);
}

function bpLogout() {
  const t = bpToken();
  const done = () => {
    localStorage.removeItem(BP_TOKEN_KEY);
    localStorage.removeItem(BP_USER_KEY);
    bpRenderAuthBar(null);
    out.innerHTML = '<span class="ok">已登出</span>';
  };
  if (!t) { done(); return; }
  fetch('/api/v1/auth/logout', { method: 'POST', headers: { 'X-Token': t } })
    .then(done).catch(done);
}

function bpRenderAuthBar(u) {
  const el = document.getElementById('authBar');
  if (!el) return;
  if (u && u.username) {
    el.innerHTML = '👤 <b>' + (u.realName || u.username) + '</b>（' + u.username + '）'
      + (u.admin ? ' <span class="post">管理员</span>' : '')
      + ' <a href="javascript:bpLogout()">登出</a>';
  } else {
    el.innerHTML = '未登录 <a href="javascript:bpAutoLogin()">登录</a>';
  }
}

/** 当前用户权限（前端菜单/按钮控制用）。 */
function bpHasPerm(code) {
  const u = JSON.parse(localStorage.getItem(BP_USER_KEY) || '{}');
  if (u.admin) return true;
  return false;
}

/** 统一带令牌的 fetch 包装（所有 req 走它）。 */
function bpFetch(url, opts) {
  opts = opts || {};
  opts.headers = Object.assign({}, opts.headers || {});
  const t = bpToken();
  if (t) opts.headers['Authorization'] = 'Bearer ' + t;
  return fetch(url, opts);
}
'''

s = s[:nxt] + inject + s[nxt:]

# ---------- 2) 让 req 使用 bpFetch ----------
if 'fetch(' in req_src:
    new_req = req_src.replace('fetch(', 'bpFetch(')
    s = s.replace(req_src, new_req, 1)
    print('  ✓ req 已改用 bpFetch')
else:
    print('  !! req 内未发现 fetch(')

# ---------- 3) 顶部登录条 ----------
s = s.replace('<body>', '''<body>
<div id="authBar" style="position:sticky;top:0;z-index:99;background:#0f172a;color:#cbd5e1;
  padding:8px 16px;font-size:13px;display:flex;gap:12px;align-items:center;justify-content:flex-end">
  未登录
</div>
<script>document.addEventListener('DOMContentLoaded', function(){ bpAutoLogin(); });</script>''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('页面已接入登录，长度', len(s))
