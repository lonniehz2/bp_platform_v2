<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const version = 'v0.1.0'
const tenant = localStorage.getItem('platformUser') ? (JSON.parse(localStorage.getItem('platformUser') || '{}').tenantId || '350600') : '350600'
const sections = [
  { title: '项目与空间', items: ['创建项目并选择空间模板', '维护小区/楼栋/单元/楼层/房屋', '可出租空间自动生成房源'] },
  { title: '人员与申请', items: ['新增人员档案', '创建申请并提交审核', '审核通过后进入轮候', '轮候记录分配空置房屋'] },
  { title: '合同与收费', items: ['配租生成合同或手工创建合同', '合同生效后生成租金账单', '补贴在账单生成时抵扣', '确认收款并打印收据'] },
  { title: '变更与审批', items: ['租金/期限/换房/退租变更', '提交后进入审批流程', '多级审批需逐级通过', '退租后合同终止、房屋释放'] },
  { title: '权限与主题', items: ['用户管理绑定角色', '角色管理分配菜单', '顶栏切换中英文', '顶栏切换深色/浅色'] }
]
const currentTitle = computed(() => route.meta?.title || '使用帮助')
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head"><div><h2>使用帮助</h2><p>保障房业务操作顺序和平台信息</p></div><span class="badge blue">{{ version }}</span></div>
      <div class="grid cards">
        <div class="card"><div class="label">当前页面</div><div class="value" style="font-size:18px">{{ currentTitle }}</div><div class="hint">从左侧菜单进入</div></div>
        <div class="card"><div class="label">租户</div><div class="value" style="font-size:18px">{{ tenant }}</div><div class="hint">平台租户编码</div></div>
        <div class="card"><div class="label">前端</div><div class="value" style="font-size:18px">Vue 3</div><div class="hint">内置 Spring Boot 静态资源</div></div>
        <div class="card"><div class="label">后端</div><div class="value" style="font-size:18px">Spring Boot 3</div><div class="hint">Java 17 / MySQL</div></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
      <div v-for="s in sections" :key="s.title" class="panel">
        <div class="panel-head"><h2>{{ s.title }}</h2></div>
        <div v-for="(item, i) in s.items" :key="item" class="row" style="padding:7px 0;border-bottom:1px solid var(--line)">
          <span class="badge blue">{{ i + 1 }}</span>
          <span class="small">{{ item }}</span>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>常用入口</h2></div>
      <div class="row">
        <RouterLink class="badge blue" to="/projects">项目与资产</RouterLink>
        <RouterLink class="badge blue" to="/applications">申请与轮候</RouterLink>
        <RouterLink class="badge blue" to="/contracts">合同与租赁</RouterLink>
        <RouterLink class="badge blue" to="/billing">收费与账务</RouterLink>
        <RouterLink class="badge blue" to="/audit">审批中心</RouterLink>
        <RouterLink class="badge blue" to="/users">用户管理</RouterLink>
      </div>
    </div>
  </div>
</template>
