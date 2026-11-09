import { reactive } from 'vue'

export const confirmState = reactive({
  open: false,
  title: '确认操作',
  message: '',
  confirmText: '确认',
  cancelText: '取消',
  danger: false
})

let resolver = null

export function confirmAction(options = {}) {
  Object.assign(confirmState, {
    open: true,
    title: options.title || '确认操作',
    message: options.message || '',
    confirmText: options.confirmText || '确认',
    cancelText: options.cancelText || '取消',
    danger: !!options.danger
  })
  return new Promise((resolve) => { resolver = resolve })
}

export function closeConfirm(result) {
  confirmState.open = false
  if (resolver) {
    resolver(!!result)
    resolver = null
  }
}
