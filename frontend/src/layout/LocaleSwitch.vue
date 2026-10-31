<template>
  <el-dropdown trigger="click" @command="change">
    <el-button text class="locale-switch">
      {{ currentLabel }}
      <el-icon><ArrowDown /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="zh-CN" :disabled="locale === 'zh-CN'">
          {{ t('locale.zh') }}
        </el-dropdown-item>
        <el-dropdown-item command="en-US" :disabled="locale === 'en-US'">
          {{ t('locale.en') }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { setLocale } from '@/i18n'
import req, { getToken } from '@/api/request'

const { t, locale } = useI18n()
const currentLabel = computed(() => (locale.value === 'en-US' ? 'EN' : 'ZH'))

function change(tag) {
  setLocale(tag)
  ElMessage.success(t('locale.changed'))
  if (getToken()) {
    req.put('/auth/locale', { locale: tag }).catch(() => {})
  }
}
</script>

<style scoped>
.locale-switch { font-size: 12px; padding: 4px 6px; }
</style>
