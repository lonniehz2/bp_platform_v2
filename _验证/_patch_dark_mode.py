# -*- coding: utf-8 -*-
"""深色模式：uiState + 切换按钮 + 全局变量。"""
import io

# ---------- uiState ----------
p = r'..\frontend\src\layout\uiState.js'
s = io.open(p, encoding='utf-8').read()
if 'uiState.mode' not in s:
    s = s.replace("const KEY = 'bp.ui.style'",
                  "const KEY = 'bp.ui.style'\nconst MODE_KEY = 'bp.ui.mode'")
    s = s.replace("export const uiState = reactive({ style: read() })",
                  """function readMode() {
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
}""")
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('uiState mode added')

# ---------- main.js 引入 dark 变量 ----------
p = r'..\frontend\src\main.js'
s = io.open(p, encoding='utf-8').read()
if 'dark/css-vars.css' not in s:
    s = s.replace("import 'element-plus/dist/index.css'",
                  "import 'element-plus/dist/index.css'\n"
                  "import 'element-plus/theme-chalk/dark/css-vars.css'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('dark css imported')

# ---------- StyleSwitch：增加浅色/深色 ----------
p = r'..\frontend\src\layout\StyleSwitch.vue'
s = io.open(p, encoding='utf-8').read()
if 'toggleMode' not in s:
    s = s.replace('''<template>
  <el-tooltip''', '''<template>
  <el-tooltip :content="uiState.mode === 'dark' ? '切换到浅色模式' : '切换到深色模式'">
    <el-button circle size="small" style="margin-right:8px" @click="toggleMode">
      <el-icon><Moon v-if="uiState.mode === 'light'" /><Sunny v-else /></el-icon>
    </el-button>
  </el-tooltip>
  <el-tooltip''', 1)
    s = s.replace("import { uiState, setStyle } from './uiState'",
                  "import { uiState, setStyle, toggleMode } from './uiState'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('style switch updated')
