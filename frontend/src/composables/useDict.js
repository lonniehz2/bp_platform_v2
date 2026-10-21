import { ref, onMounted } from 'vue'
import { sysApi } from '@/api/modules'

/**
 * 字典下拉（替代硬编码枚举）。
 *
 * 用法：
 *   const { options, label } = useDict('HOUSE_TYPE')
 *   <el-option v-for="o in options" :key="o.value" :label="o.label" :value="o.value" />
 *
 * 设计：
 * - 同类型并发只请求一次（模块级缓存）
 * - 后端不可用时**不抛错**，退化为空数组（页面仍可用，只是下拉为空）
 * - 支持 fallback：由调用方传入静态兜底项，保证字典服务异常时业务不中断
 */
const cache = new Map()      // dictType -> options[]
const pending = new Map()    // dictType -> Promise

export function useDict(dictType, fallback = []) {
  const options = ref(cache.get(dictType) || fallback)

  async function load() {
    if (cache.has(dictType)) {
      options.value = cache.get(dictType)
      return
    }
    try {
      let p = pending.get(dictType)
      if (!p) {
        p = sysApi.dicts(dictType)
        pending.set(dictType, p)
      }
      const list = await p
      const opts = (list || []).map((d) => ({
        value: d.dictCode,
        label: d.dictLabel,
        raw: d
      }))
      cache.set(dictType, opts)
      options.value = opts.length ? opts : fallback
    } catch (e) {
      // 字典不可用不应阻断页面
      options.value = fallback
    } finally {
      pending.delete(dictType)
    }
  }

  /** 编码 → 中文标签 */
  function label(code) {
    const hit = (options.value || []).find((o) => o.value === code)
    return hit ? hit.label : code
  }

  onMounted(load)

  return { options, label, reload: load }
}

/** 清除缓存（字典维护后调用） */
export function clearDictCache() {
  cache.clear()
}
