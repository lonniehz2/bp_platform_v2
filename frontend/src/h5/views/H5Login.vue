<template>
  <div class="login">
    <div class="logo">{{ t('h5.loginTitle') }}</div>
    <div class="slogan">{{ t('h5.slogan') }}</div>

    <div class="form card">
      <el-form :model="form">
        <el-form-item>
          <el-input v-model="form.tenantId" :placeholder="t('h5.tenant')" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.username" :placeholder="t('h5.account')" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" show-password
                    :placeholder="t('h5.password')" size="large" />
        </el-form-item>
        <el-button type="primary" size="large" style="width:100%"
                   :loading="loading" @click="onLogin">{{ t('h5.login') }}</el-button>
      </el-form>
      <div class="muted" style="margin-top:14px;text-align:center">
        {{ t('h5.demo') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ tenantId: '350600', username: 'admin', password: 'admin123' })

async function onLogin() {
  loading.value = true
  try {
    await auth.login({ ...form })
    ElMessage.success('登录成功')
    router.replace('/h5/home')
  } catch (e) { /* 已提示 */ } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  background: linear-gradient(160deg, #1f6feb 0%, #3f8cff 45%, #f2f4f7 45%);
  padding-top: 60px;
}
.logo { color: #fff; font-size: 26px; font-weight: 700; text-align: center; }
.slogan { color: rgba(255,255,255,.86); text-align: center; font-size: 13px; margin-top: 6px; }
.form { margin: 26px 20px; padding: 20px 16px; }
</style>
