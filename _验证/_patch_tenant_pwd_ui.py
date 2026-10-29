# -*- coding: utf-8 -*-
import io

p = r'..\frontend\src\layout\Layout.vue'
s = io.open(p, encoding='utf-8').read()
if 'mustChangePassword' not in s:
    s = s.replace('''<template>
  <component :is="shell" />
</template>''', '''<template>
  <component :is="shell" />

  <el-dialog v-model="pwdVisible" title="修改初始密码" width="440px"
             :close-on-click-modal="false" :close-on-press-escape="false" :show-close="false">
    <el-alert type="warning" :closable="false" show-icon
              title="首次登录需要修改密码后才能继续使用。" />
    <el-form :model="pwd" label-width="90px" style="margin-top:12px">
      <el-form-item label="原密码">
        <el-input v-model="pwd.oldPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="pwd.newPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="pwd.confirm" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button type="primary" :loading="saving" @click="savePwd">保存并继续</el-button>
    </template>
  </el-dialog>
</template>''', 1)
    s = s.replace('''import { computed, onMounted } from 'vue' ''' .strip(),
                  '''import { computed, onMounted, ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { useAuthStore } from '@/store/auth' ''', 1)
    s = s.replace('''onMounted(() => todo.start())''', '''onMounted(() => todo.start())

// 首次登录/重置密码后强制修改
const auth = useAuthStore()
const pwdVisible = ref(false)
const saving = ref(false)
const pwd = reactive({ oldPassword: '', newPassword: '', confirm: '' })
watch(() => auth.user?.mustChangePassword, (v) => {
  if (v) pwdVisible.value = true
}, { immediate: true })

async function savePwd() {
  if (!pwd.oldPassword || !pwd.newPassword) {
    ElMessage.warning('请填写原密码与新密码')
    return
  }
  if (pwd.newPassword !== pwd.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  saving.value = true
  try {
    await req.post('/auth/change-password', {
      oldPassword: pwd.oldPassword, newPassword: pwd.newPassword
    })
    ElMessage.success('密码已修改')
    pwdVisible.value = false
    await auth.loadMe()
  } finally {
    saving.value = false
  }
}''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('layout change password dialog added')
