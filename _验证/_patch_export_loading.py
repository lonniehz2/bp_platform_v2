# -*- coding: utf-8 -*-
"""导出按钮 loading 状态。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

# 合同
p = os.path.join(VIEWS, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
s = s.replace('''        <el-button plain data-testid="contract-export" @click="exportContracts">
          导出 CSV
        </el-button>''',
              '''        <el-button plain data-testid="contract-export" :loading="exporting"
                   @click="exportContracts">导出 CSV</el-button>''', 1)
if 'const exporting = ref(false)' not in s:
    s = s.replace('''async function exportContracts() {''', '''const exporting = ref(false)

async function exportContracts() {''', 1)
s = s.replace('''async function exportContracts() {
  try {''', '''async function exportContracts() {
  exporting.value = true
  try {''', 1)
s = s.replace('''  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导出失败')
  }
}

function resetQuery() {''', '''  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导出失败')
  } finally { exporting.value = false }
}

function resetQuery() {''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('合同导出 loading 已加')

# 账单
p = os.path.join(VIEWS, 'Bills.vue')
s = io.open(p, encoding='utf-8').read()
s = s.replace('''        <el-button plain data-testid="bill-export" @click="exportBills">导出 CSV</el-button>''',
              '''        <el-button plain data-testid="bill-export" :loading="exporting"
                   @click="exportBills">导出 CSV</el-button>''', 1)
if 'const exporting = ref(false)' not in s:
    s = s.replace('''/** 按当前筛选导出账单 CSV（最多 5000 行） */''', '''const exporting = ref(false)

/** 按当前筛选导出账单 CSV（分页拉全量） */''', 1)
s = s.replace('''async function exportBills() {
  try {''', '''async function exportBills() {
  exporting.value = true
  try {''', 1)
s = s.replace('''  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导出失败')
  }
}

async function loadTrend() {''', '''  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导出失败')
  } finally { exporting.value = false }
}

async function loadTrend() {''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('账单导出 loading 已加')
