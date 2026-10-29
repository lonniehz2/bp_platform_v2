<template>
  <div class="login-page">
    <div class="bg-grid" />
    <div class="orb orb-a" />
    <div class="orb orb-b" />
    <div class="orb orb-c" />

    <div class="login-shell">
      <!-- 左侧品牌区 -->
      <section class="brand">
        <div class="brand-head">
          <div class="logo"><span class="logo-core" /></div>
          <div>
            <h1>租赁性保障用房管理平台</h1>
            <p class="en">Leased Affordable Housing Management Platform</p>
          </div>
        </div>

        <p class="slogan">房源、合同、收费、物联一体化的保障房运营中枢</p>

        <ul class="features">
          <li><span class="dot" /><div><b>全流程闭环</b><em>申请 · 配租 · 签约 · 收费 · 退租</em></div></li>
          <li><span class="dot" /><div><b>账务可追溯</b><em>账单计费明细 · 收款核销 · 押金台账</em></div></li>
          <li><span class="dot" /><div><b>物联联动</b><em>门锁 / 水电表 / 告警 · IoT 对账</em></div></li>
          <li><span class="dot" /><div><b>多租户隔离</b><em>租户级数据隔离 · 组织级数据范围</em></div></li>
        </ul>

        <div class="stats">
          <div><b>46</b><span>业务页面</span></div>
          <div><b>7</b><span>计费方式</span></div>
          <div><b>24h</b><span>设备在线监测</span></div>
        </div>
      </section>

      <!-- 右侧登录卡 -->
      <section class="card">
        <div class="card-head">
          <h2>欢迎登录</h2>
          <p>请使用平台租户码与账号登录</p>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="onSubmit">
          <el-form-item prop="tenantId">
            <el-input v-model="form.tenantId" placeholder="平台租户码，如 350600" size="large">
              <template #prefix><el-icon><OfficeBuilding /></el-icon></template>
              <template #suffix>
                <el-tooltip placement="top">
                  <template #content>
                    <div style="max-width:260px;line-height:1.7">
                      租户码是<b>数据隔离标识</b>，不是组织编码。<br />
                      一个租户下可有多级组织；登录后右上角显示你的<b>组织</b>，<br />
                      未限定组织（全局范围）时显示「平台」。
                    </div>
                  </template>
                  <el-icon style="cursor:help"><InfoFilled /></el-icon>
                </el-tooltip>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" size="large">
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>

          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" show-password
                      placeholder="密码" size="large">
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>

          <el-button class="submit" size="large" :loading="loading" @click="onSubmit">
            登 录
          </el-button>
        </el-form>

        <div class="hint">
          <div class="hint-title">演示账号（点击填充）</div>
          <div class="accounts">
            <el-tag v-for="a in accounts" :key="a.u" size="small" effect="dark"
                    :type="a.type" style="cursor:pointer;margin:3px"
                    @click="fill(a)">{{ a.label }}</el-tag>
          </div>
          <p class="scope-note">
            登录后右上角显示「组织 · 平台」；租户码可在悬停提示中查看。
          </p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ tenantId: '350600', username: 'admin', password: 'admin123' })

const rules = {
  tenantId: [{ required: true, message: '请输入平台租户码', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const accounts = [
  { label: '管理员 admin', u: 'admin', p: 'admin123', type: 'primary' },
  { label: '受理岗 acceptor', u: 'acceptor', p: 'acc123', type: 'success' },
  { label: '只读 viewer', u: 'viewer', p: 'view123', type: 'info' }
]

function fill(a) {
  form.username = a.u
  form.password = a.p
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login({ ...form })
    ElMessage.success('登录成功')
    router.replace(route.query.redirect || '/dashboard')
  } catch (e) {
    // 错误提示已在拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    radial-gradient(1200px 600px at 15% 10%, #16324f 0%, transparent 60%),
    radial-gradient(900px 500px at 85% 90%, #123a3a 0%, transparent 55%),
    linear-gradient(135deg, #060b16 0%, #0a1424 45%, #07131c 100%);
  color: #e6f1ff;
}

.bg-grid {
  position: absolute;
  inset: -20%;
  background-image:
    linear-gradient(rgba(80, 180, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(80, 180, 255, 0.07) 1px, transparent 1px);
  background-size: 48px 48px;
  transform: perspective(600px) rotateX(52deg) translateY(-10%);
  transform-origin: center top;
  animation: gridMove 18s linear infinite;
  mask-image: radial-gradient(ellipse at 50% 30%, #000 30%, transparent 75%);
}

@keyframes gridMove {
  from { background-position: 0 0, 0 0; }
  to { background-position: 0 96px, 96px 0; }
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.55;
  animation: float 12s ease-in-out infinite;
}
.orb-a { width: 380px; height: 380px; left: 6%; top: 12%; background: #1e6bff; }
.orb-b { width: 320px; height: 320px; right: 8%; top: 8%; background: #12c2a0; animation-delay: -3s; }
.orb-c { width: 300px; height: 300px; right: 18%; bottom: 4%; background: #7a4dff; animation-delay: -6s; }

@keyframes float {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(0, -18px, 0) scale(1.06); }
}

.login-shell {
  position: relative;
  z-index: 2;
  width: min(1120px, 94vw);
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 48px;
  align-items: center;
}

.brand { padding: 8px 4px; }
.brand-head { display: flex; align-items: center; gap: 16px; }

.logo {
  width: 54px; height: 54px; border-radius: 16px;
  background: linear-gradient(145deg, #2b7bff, #12c2a0);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10px 30px rgba(43, 123, 255, 0.45);
}
.logo-core {
  width: 22px; height: 22px; border-radius: 6px;
  background: #eaf6ff;
  box-shadow: 0 0 18px #eaf6ff;
}

.brand h1 {
  margin: 0;
  font-size: 30px;
  letter-spacing: 1px;
  background: linear-gradient(90deg, #eaf6ff, #7fd3ff 60%, #5ef2cd);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.brand .en { margin: 4px 0 0; font-size: 12px; letter-spacing: 1.5px; color: #6f8fb3; }
.slogan { margin: 22px 0 24px; color: #9db8d6; font-size: 14px; }

.features { list-style: none; padding: 0; margin: 0 0 30px; display: grid; gap: 14px; }
.features li { display: flex; gap: 12px; align-items: flex-start; }
.features .dot {
  width: 8px; height: 8px; margin-top: 7px; border-radius: 50%;
  background: #12c2a0; box-shadow: 0 0 12px #12c2a0;
}
.features b { display: block; font-size: 14px; color: #e6f1ff; }
.features em { font-style: normal; font-size: 12px; color: #6f8fb3; }

.stats { display: flex; gap: 28px; }
.stats b {
  display: block; font-size: 26px;
  background: linear-gradient(90deg, #7fd3ff, #5ef2cd);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.stats span { font-size: 12px; color: #6f8fb3; }

.card {
  background: linear-gradient(180deg, rgba(17, 32, 54, 0.92), rgba(9, 19, 34, 0.94));
  border: 1px solid rgba(88, 166, 255, 0.22);
  border-radius: 20px;
  padding: 34px 32px 24px;
  box-shadow:
    0 30px 80px rgba(0, 0, 0, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
}

.card-head h2 { margin: 0 0 6px; font-size: 24px; color: #eaf6ff; }
.card-head p { margin: 0 0 22px; font-size: 12px; color: #6f8fb3; }

.card :deep(.el-input__wrapper) {
  background: rgba(9, 20, 36, 0.9);
  box-shadow: 0 0 0 1px rgba(88, 166, 255, 0.25) inset;
  border-radius: 10px;
}
.card :deep(.el-input__inner) { color: #e6f1ff; }
.card :deep(.el-input__inner::placeholder) { color: #56789c; }
.card :deep(.el-input__prefix), .card :deep(.el-input__suffix) { color: #6f9fd6; }

.submit {
  width: 100%;
  margin-top: 6px;
  height: 46px;
  border: none;
  border-radius: 10px;
  color: #04121f;
  font-weight: 700;
  letter-spacing: 4px;
  background: linear-gradient(90deg, #59d9ff, #38f2c0);
  box-shadow: 0 10px 28px rgba(56, 242, 192, 0.28);
}
.submit:hover { filter: brightness(1.06); }

.hint { margin-top: 20px; text-align: center; }
.hint-title { font-size: 12px; color: #6f8fb3; margin-bottom: 6px; }
.scope-note { margin: 12px 0 0; font-size: 11px; color: #56789c; line-height: 1.6; }

@media (max-width: 900px) {
  .login-shell { grid-template-columns: 1fr; gap: 26px; }
  .brand { display: none; }
  .card { padding: 26px 20px 18px; }
}
</style>
