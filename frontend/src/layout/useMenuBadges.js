/**
 * 菜单角标：拉取 /menu/badges，60 秒刷新一次。
 *
 * 失败时全部按 0 处理，不影响菜单渲染。
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import req from '@/api/request'

export function useMenuBadges() {
  const badges = ref({})
  let timer = null

  async function load() {
    try {
      const d = await req.get('/menu/badges')
      badges.value = d || {}
    } catch (e) {
      badges.value = {}
    }
  }

  function countOf(key) {
    const n = Number(badges.value[key] || 0)
    return Number.isFinite(n) ? n : 0
  }

  onMounted(() => {
    load()
    timer = setInterval(load, 60000)
  })
  onBeforeUnmount(() => {
    if (timer) clearInterval(timer)
  })

  return { badges, countOf, reload: load }
}
