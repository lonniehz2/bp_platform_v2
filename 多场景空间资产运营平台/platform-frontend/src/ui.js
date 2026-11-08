import { ref, watch } from 'vue'

const saved = localStorage.getItem('platformMode')
export const mode = ref(saved === 'dark' ? 'dark' : 'light')
document.documentElement.classList.toggle('dark', mode.value === 'dark')

export function toggleMode() {
  mode.value = mode.value === 'dark' ? 'light' : 'dark'
}

watch(mode, (value) => {
  localStorage.setItem('platformMode', value)
  document.documentElement.classList.toggle('dark', value === 'dark')
})
