<template>
  <component :is="shell" />

  <el-dialog v-model="pwdVisible" :title="t('layout.pwdTitle')" width="440px"
             :close-on-click-modal="false" :close-on-press-escape="false" :show-close="false">
    <el-alert type="warning" :closable="false" show-icon
              :title="t('layout.pwdTip')" />
    <el-form :model="pwd" label-width="90px" style="margin-top:12px">
      <el-form-item :label="t('layout.oldPwd')">
        <el-input v-model="pwd.oldPassword" type="password" show-password />
      </el-form-item>
      <el-form-item :label="t('layout.newPwd')">
        <el-input v-model="pwd.newPassword" type="password" show-password />
      </el-form-item>
      <el-form-item :label="t('layout.confirmPwd')">
        <el-input v-model="pwd.confirm" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button type="primary" :loading="saving" @click="savePwd">{{ t('layout.saveContinue') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, ref, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { uiState } from './uiState'
import LayoutClassic from './LayoutClassic.vue'
import LayoutRail from './LayoutRail.vue'
const { t } = useI18n()
import { useTodoStore } from '@/store/todo'
import { useAuthStore } from '@/store/auth'
import req from '@/api/request'

/** 两种风格共用同一路由树，切换只换外壳，页面内容完全一致 */
const shell = computed(() =>
  uiState.style === 'classic' ? LayoutClassic : LayoutRail)

const todo = useTodoStore()
onMounted(() => todo.start())

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
}
</script>
