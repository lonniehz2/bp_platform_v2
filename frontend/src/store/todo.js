import { defineStore } from 'pinia'
import { ref } from 'vue'
import { msgApi } from '@/api/modules'

/**
 * 待办计数（侧边栏角标用）。
 *
 * 说明：
 *  - 与「待办中心」页共用同一个接口，但页面自己会再拉一次，两边互不依赖
 *  - 轮询间隔 60s；页面切走不停止，因为角标要一直准
 *  - 接口失败静默处理：角标不是关键路径，不能因为它弹错误提示
 */
export const useTodoStore = defineStore('todo', () => {
  const total = ref(0)
  const categories = ref([])
  let timer = null

  async function load() {
    try {
      const d = await msgApi.todoOverview()
      categories.value = d.categories || []
      total.value = Number(d.total || 0)
    } catch (e) {
      /* 静默：角标失败不影响主流程 */
    }
  }

  function start(interval = 60000) {
    if (timer) return
    load()
    timer = setInterval(load, interval)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  /** 处理完一条待办后立即刷新角标 */
  function refresh() {
    return load()
  }

  return { total, categories, load, start, stop, refresh }
})
