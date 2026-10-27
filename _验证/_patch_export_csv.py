# -*- coding: utf-8 -*-
"""合同/账单导出 CSV。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---------------- 合同 ----------------
p = os.path.join(VIEWS, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()

if 'exportContracts' not in s:
    s = s.replace('''        <el-button @click="expireDue">到期批量处理</el-button>''',
                  '''        <el-button @click="expireDue">到期批量处理</el-button>
        <el-button plain data-testid="contract-export" @click="exportContracts">
          导出 CSV
        </el-button>''', 1)
    if "from '@/utils/csv'" not in s:
        s = s.replace("import req from '@/api/request'",
                      "import req from '@/api/request'\nimport { downloadCsv } from '@/utils/csv'", 1)
    s = s.replace('''function resetQuery() {''', '''/** 按当前筛选导出 CSV（最多 5000 行） */
async function exportContracts() {
  try {
    const d = await contractApi.page({
      pageNum: 1, pageSize: 5000,
      orgId: q.orgId || undefined,
      contractStatus: q.contractStatus || undefined,
      keyword: q.keyword || undefined
    })
    const rows = d.rows || []
    downloadCsv('合同台账_' + new Date().toISOString().slice(0, 10), [
      { key: 'contractNo', label: '合同号' },
      { key: 'lesseeName', label: '承租人' },
      { key: 'orgIdName', label: '组织' },
      { key: 'houseAddress', label: '房屋' },
      { key: 'leaseStart', label: '起租日' },
      { key: 'leaseEnd', label: '止租日' },
      { key: 'monthlyRent', label: '月租' },
      { key: 'depositAmount', label: '押金' },
      { key: 'contractTypeLabel', label: '类型' },
      { key: 'contractStatusLabel', label: '状态' },
      { key: 'signTime', label: '签约时间' }
    ], rows)
    ElMessage.success('已导出 ' + rows.length + ' 条合同')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导出失败')
  }
}

function resetQuery() {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('合同导出已加')

# ---------------- 账单 ----------------
p = os.path.join(VIEWS, 'Bills.vue')
s = io.open(p, encoding='utf-8').read()
if 'exportBills' not in s:
    s = s.replace('''        <el-button @click="scanOverdue">扫描逾期</el-button>''',
                  '''        <el-button @click="scanOverdue">扫描逾期</el-button>
        <el-button plain data-testid="bill-export" @click="exportBills">导出 CSV</el-button>''', 1)
    if "from '@/utils/csv'" not in s:
        s = s.replace("import req from '@/api/request'",
                      "import req from '@/api/request'\nimport { downloadCsv } from '@/utils/csv'", 1)
    # 在 loadTrend 前插入导出函数
    s = s.replace('''async function loadTrend() {''', '''/** 按当前筛选导出账单 CSV（最多 5000 行） */
async function exportBills() {
  try {
    const d = await financeApi.bills({
      pageNum: 1, pageSize: 5000,
      orgId: q.orgId || undefined,
      status: q.billStatus || undefined,
      billPeriod: q.billPeriod || undefined,
      houseId: q.houseId || undefined
    })
    const rows = d.rows || []
    downloadCsv('账单_' + new Date().toISOString().slice(0, 10), [
      { key: 'billNo', label: '账单号' },
      { key: 'payerName', label: '缴费人' },
      { key: 'billPeriod', label: '账期' },
      { key: 'totalAmount', label: '应收' },
      { key: 'paidAmount', label: '已缴' },
      { key: 'reduceAmount', label: '减免' },
      { key: 'remainAmount', label: '待缴' },
      { key: 'dueDate', label: '截止日' },
      { key: 'billStatusLabel', label: '状态' },
      { key: 'overdueDays', label: '逾期天数' }
    ], rows)
    ElMessage.success('已导出 ' + rows.length + ' 条账单')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导出失败')
  }
}

async function loadTrend() {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('账单导出已加')
