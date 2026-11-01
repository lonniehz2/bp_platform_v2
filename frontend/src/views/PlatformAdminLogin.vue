<template>
  <div class="ops-login">
    <div class="bg-grid" />
    <div class="card">
      <div class="logo-row">
        <div class="logo"><span /></div>
        <div>
          <h1>{{ t('opsLogin.adminTitle') }}</h1>
          <p>Platform Operations Console</p>
        </div>
      </div>

      <el-form :model="form" @keyup.enter="submit">
        <el-form-item>
          <el-input v-model="form.username" size="large" :placeholder="t('opsLogin.adminUser')">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" size="large" type="password" show-password
                    :placeholder="t('opsLogin.adminPwd')">
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button class="submit" size="large" :loading="loading" @click="submit">
          {{ t('opsLogin.adminLogin') }}
        </el-button>
      </el-form>

      <p class="hint">{{ t('opsLogin.adminHint') }}</p>
      <el-link type="primary" style="font-size:12px" @click="toBusiness">{{ t('opsLogin.backBusiness') }}</el-link>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { operatorApi, setOperatorToken, setOperatorName } from '@/api/operator'

const router = useRouter()
const { t } = useI18n()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入账号与密码')
    return
  }
  loading.value = true
  try {
    const d = await operatorApi.login({ ...form })
    setOperatorToken(d.token)
    setOperatorName(d.realName || d.username)
    sessionStorage.setItem('bp.operator.mustChange', d.mustChangePassword ? '1' : '0')
    router.replace('/platform-admin')
  } finally {
    loading.value = false
  }
}

function toBusiness() {
  router.replace('/login')
}
</script>

<style scoped>
.ops-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(900px 500px at 20% 10%, #16283f 0%, transparent 60%),
              linear-gradient(135deg, #060b16, #0a1424 50%, #07131c);
  color: #e6f1ff;
  position: relative;
  overflow: hidden;
}
.bg-grid {
  position: absolute;
  inset: -20%;
  background-image: linear-gradient(rgba(80, 180, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(80, 180, 255, 0.07) 1px, transparent 1px);
  background-size: 48px 48px;
  transform: perspective(600px) rotateX(52deg) translateY(-10%);
  mask-image: radial-gradient(ellipse at 50% 30%, #000 30%, transparent 75%);
}
.card {
  position: relative;
  z-index: 2;
  width: 400px;
  padding: 32px 30px 22px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(17, 32, 54, 0.94), rgba(9, 19, 34, 0.96));
  border: 1px solid rgba(88, 166, 255, 0.22);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.55);
}
.logo-row { display: flex; align-items: center; gap: 14px; margin-bottom: 22px; }
.logo {
  width: 46px; height: 46px; border-radius: 14px;
  background: linear-gradient(145deg, #2b7bff, #12c2a0);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10px 30px rgba(43, 123, 255, 0.45);
}
.logo span { width: 18px; height: 18px; border-radius: 5px; background: #eaf6ff; }
h1 { margin: 0; font-size: 22px; color: #eaf6ff; }
.logo-row p { margin: 4px 0 0; font-size: 11px; color: #6f8fb3; letter-spacing: 1px; }
:deep(.el-input__wrapper) {
  background: rgba(9, 20, 36, 0.9);
  box-shadow: 0 0 0 1px rgba(88, 166, 255, 0.25) inset;
  border-radius: 10px;
}
:deep(.el-input__inner) { color: #e6f1ff; }
:deep(.el-input__inner::placeholder) { color: #56789c; }
.submit {
  width: 100%; height: 44px; border: none; border-radius: 10px;
  color: #04121f; font-weight: 700; letter-spacing: 3px;
  background: linear-gradient(90deg, #59d9ff, #38f2c0);
}
.hint { margin: 16px 0 10px; font-size: 11px; color: #56789c; text-align: center; }
</style>
