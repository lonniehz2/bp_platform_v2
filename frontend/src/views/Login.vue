<template>
  <div class="login-wrap">
    <div class="login-box">
      <h2>租赁性保障用房管理平台</h2>
      <p class="sub">Leased Affordable Housing Management Platform</p>

      <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="onSubmit">
        <el-form-item prop="tenantId">
          <el-input v-model="form.tenantId" placeholder="租户ID" size="large">
            <template #prefix><el-icon><OfficeBuilding /></el-icon></template>
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
        <el-button type="primary" size="large" style="width:100%"
                   :loading="loading" @click="onSubmit">登 录</el-button>
      </el-form>

      <div class="hint">
        <div class="muted">演示账号（租户 350600）</div>
        <div class="accounts">
          <el-tag v-for="a in accounts" :key="a.u" size="small"
                  style="cursor:pointer;margin:2px"
                  @click="fill(a)">{{ a.label }}</el-tag>
        </div>
      </div>
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
  tenantId: [{ required: true, message: '请输入租户ID', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const accounts = [
  { label: '管理员 admin', u: 'admin', p: 'admin123' },
  { label: '受理岗 acceptor', u: 'acceptor', p: 'acc123' },
  { label: '只读 viewer', u: 'viewer', p: 'view123' }
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
.login-wrap {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f2d3d 0%, #2c5364 100%);
}
.login-box {
  width: 380px;
  background: #fff;
  border-radius: 10px;
  padding: 32px 28px 24px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
}
.login-box h2 { margin: 0 0 4px; font-size: 20px; color: #303133; text-align: center; }
.sub { margin: 0 0 22px; text-align: center; color: #909399; font-size: 11px; }
.hint { margin-top: 18px; text-align: center; }
.accounts { margin-top: 6px; }
</style>
