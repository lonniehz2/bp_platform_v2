import { reactive, watch } from 'vue'

const KEY = 'bp.ui.style'
const MODE_KEY = 'bp.ui.mode'

/**
 * 布局风格：
 *   classic —— 风格1：宽侧栏 + 分组二级菜单（传统后台，信息密度高）
 *   rail    —— 风格2：图标窄栏 + 二级面板（参考系统样式，视觉更轻）
 *
 * 两种风格共用同一套路由与页面组件，切换只影响外壳，**内容完全同步**。
 */
function read() {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'classic' || v === 'rail' ? v : 'rail'
  } catch (e) {
    return 'rail'
  }
}

function readMode() {
  try {
    const v = localStorage.getItem(MODE_KEY)
    return v === 'dark' ? 'dark' : 'light'
  } catch (e) {
    return 'light'
  }
}

function applyMode(mode) {
  try {
    document.documentElement.classList.toggle('dark', mode === 'dark')
  } catch (e) { /* ignore */ }
}

export const uiState = reactive({ style: read(), mode: readMode() })
applyMode(uiState.mode)

watch(() => uiState.mode, (v) => {
  applyMode(v)
  try { localStorage.setItem(MODE_KEY, v) } catch (e) { /* ignore */ }
})

export function setMode(v) {
  uiState.mode = v === 'dark' ? 'dark' : 'light'
}

export function toggleMode() {
  setMode(uiState.mode === 'dark' ? 'light' : 'dark')
}

watch(() => uiState.style, (v) => {
  try { localStorage.setItem(KEY, v) } catch (e) { /* ignore */ }
})

export function setStyle(v) {
  uiState.style = v === 'classic' ? 'classic' : 'rail'
}

export function toggleStyle() {
  setStyle(uiState.style === 'rail' ? 'classic' : 'rail')
}
