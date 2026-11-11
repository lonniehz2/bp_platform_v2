<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const messages = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ title: '', content: '', bizType: '', bizId: '' })
const unread = computed(() => messages.value.filter(m => m.readStatus === 'UNREAD').length)

async function load() {
  error.value = ''
  try { messages.value = await api.messages() } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error(t('messages.required'))
    await api.createMessage({ userId: null, title: form.title.trim(), content: form.content, bizType: form.bizType, bizId: form.bizId })
    form.title = ''; form.content = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function read(m) {
  try { await api.readMessage(m.id); await load() } catch (e) { error.value = e.message }
}

async function readAll() {
  try { await api.readAllMessages(); await load() } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('messages.title') }}</h2><p>{{ t('messages.subtitle') }}</p></div>
        <div class="row"><span class="badge" :class="unread ? 'orange' : 'green'">{{ t('messages.unread') }} {{ unread }}</span><button class="sm" @click="readAll">{{ t('messages.readAll') }}</button></div>
      </div>
      <div class="row">
        <div class="field" style="flex:2"><label>{{ t('messages.titleCol') }}</label><input v-model="form.title" /></div>
        <div class="field"><label>{{ t('messages.bizType') }}</label><input v-model="form.bizType" placeholder="CONTRACT/BILL" /></div>
        <div class="field"><label>{{ t('messages.bizId') }}</label><input v-model="form.bizId" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">{{ t('messages.publish') }}</button></div>
      </div>
      <div class="field" style="margin-top:8px"><label>{{ t('messages.content') }}</label><textarea v-model="form.content" rows="2" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('messages.list') }}</h2><span class="small muted">{{ messages.length }} {{ t('messages.count') }}</span></div>
      <div v-if="!messages.length" class="empty">{{ t('messages.empty') }}</div>
      <div v-for="m in messages" :key="m.id" class="row" style="padding:12px 0;border-bottom:1px solid var(--line);align-items:flex-start">
        <div style="flex:1">
          <div style="font-weight:500">{{ m.title }} <span v-if="m.readStatus === 'UNREAD'" class="badge orange">{{ t('messages.unread') }}</span></div>
          <div class="small muted" style="margin-top:4px">{{ m.content || '-' }}</div>
          <div class="small muted" style="margin-top:4px">{{ m.createTime }} {{ m.bizType ? '· ' + enumLabel(m.bizType) : '' }} {{ m.bizId || '' }}</div>
        </div>
        <button v-if="m.readStatus === 'UNREAD'" class="sm" @click="read(m)">{{ t('messages.markRead') }}</button>
      </div>
    </div>
  </div>
</template>
