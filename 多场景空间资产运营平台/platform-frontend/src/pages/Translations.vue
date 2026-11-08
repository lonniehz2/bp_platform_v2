<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '../i18n'

const { locale } = useI18n()
const keyword = ref('')
const terms = [
  ['GUARANTEE', '保障房', 'Guarantee Housing'],
  ['PUBLIC_RENTAL', '公共租赁', 'Public Rental'],
  ['AFFORDABLE_RENTAL', '保障性租赁', 'Affordable Rental'],
  ['ACTIVE', '有效', 'Active'],
  ['VACANT', '空置', 'Vacant'],
  ['ALLOCATED', '已配租', 'Allocated'],
  ['UNPAID', '未缴', 'Unpaid'],
  ['OVERDUE', '逾期', 'Overdue'],
  ['RENT_CHANGE', '租金变更', 'Rent Change'],
  ['TERMINATION', '退租', 'Termination'],
  ['BUILDING', '楼栋', 'Building'],
  ['ROOM', '房屋', 'Room'],
  ['LOCK', '门锁', 'Lock'],
  ['PENDING', '待处理', 'Pending'],
  ['RESOLVED', '已解决', 'Resolved']
]
const filtered = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return q ? terms.filter(t => t.some(v => String(v).toLowerCase().includes(q))) : terms
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head"><div><h2>业务数据翻译</h2><p>业务编码、状态和类型的中英文对照</p></div>
        <div class="row">
          <button class="sm" :class="{ primary: locale === 'zh-CN' }" @click="setLocale('zh-CN')">中文</button>
          <button class="sm" :class="{ primary: locale === 'en-US' }" @click="setLocale('en-US')">English</button>
        </div>
      </div>
      <div class="field" style="max-width:360px"><label>查询</label><input v-model="keyword" placeholder="编码/中文/English" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>翻译对照</h2><span class="small muted">{{ filtered.length }} 条</span></div>
      <div class="table-wrap">
        <table data-no-i18n>
          <thead><tr><th>业务编码</th><th>中文</th><th>English</th></tr></thead>
          <tbody>
            <tr v-for="t in filtered" :key="t[0]">
              <td class="mono">{{ t[0] }}</td><td>{{ t[1] }}</td><td>{{ t[2] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="alert" style="margin-top:12px">当前页面用于查看业务编码翻译；系统语言切换后，页面编码会自动显示对应语言。</div>
    </div>
  </div>
</template>
