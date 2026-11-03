<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">{{ t('bill.title') }}</h3>
        <OrgSelect v-model="q.orgId" width="200px" testid="bill-org-filter"
                   :placeholder="t('bill.org')" @update:model-value="reload" />
        <el-select v-model="q.billStatus" :placeholder="t('bill.status')" clearable
                   style="width:140px" @change="reload">
          <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
        </el-select>
        <el-input v-model="q.billPeriod" :placeholder="t('bill.period')" clearable
                  style="width:140px" @keyup.enter="reload" />
        <el-select v-model="q.houseId" filterable remote :remote-method="searchMeterHouse"
                   :loading="houseLoading" clearable style="width:200px"
                   :placeholder="t('bill.house')" @change="reload">
          <el-option v-for="h in meterHouses" :key="h.id" :label="h.houseName"
                     :value="String(h.id)" />
        </el-select>
        <el-button type="primary" @click="reload">{{ t('bill.search') }}</el-button>
        <el-button @click="resetQuery">{{ t('bill.reset') }}</el-button>
        <div class="spacer" />
        <el-button type="success" @click="openGen">{{ t('bill.generate') }}</el-button>
        <el-button type="warning" plain @click="batchDunning">{{ t('bill.dunning') }}</el-button>
        <el-button type="danger" plain @click="recalcBills">{{ t('bill.recalc') }}</el-button>
        <el-button type="warning" plain @click="openShared" data-testid="shared-bill">{{ t('bill.shared') }}</el-button>
        <el-button plain @click="openEnergy" data-testid="bill-energy">{{ t('bill.energy') }}</el-button>
        <el-button @click="openPay">{{ t('bill.pay') }}</el-button>
        <el-button plain @click="openPrepay">{{ t('bill.prepay') }}</el-button>
        <el-button plain @click="openPayments" data-testid="bill-payments">{{ t('bill.payments') }}</el-button>
        <el-button @click="scanOverdue">{{ t('bill.overdue') }}</el-button>
        <el-button plain data-testid="bill-export" :loading="exporting"
                   @click="exportBills">{{ t('bill.export') }}</el-button>
      </div>

      <el-row :gutter="12" style="margin-bottom:10px">
        <el-col :span="12">
          <div style="font-weight:600;margin-bottom:2px">{{ t('bill.recvTrend') }}</div>
          <LineTrend :rows="recvTrend" color="#409eff" :height="170" />
        </el-col>
        <el-col :span="12">
          <div style="font-weight:600;margin-bottom:2px">{{ t('bill.paidTrend') }}</div>
          <LineTrend :rows="paidTrend" color="#67c23a" :height="170" />
        </el-col>
      </el-row>

      <el-table :data="rows" @selection-change="onSelect"
                v-loading="loading" border size="small" :empty-text="t('bill.empty')">
        <el-table-column type="selection" width="42" />
        <el-table-column prop="billNo" :label="t('bill.no')" width="165" />
        <el-table-column prop="payerName" :label="t('bill.payer')" width="95" />
        <el-table-column prop="billPeriod" :label="t('bill.billingPeriod')" width="95" />
        <el-table-column :label="t('bill.range')" width="200">
          <template #default="{ row }">
            {{ row.periodStart || '—' }} ~ {{ row.periodEnd || '—' }}
          </template>
        </el-table-column>
        <el-table-column :label="t('bill.item')" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.feeItemIdName || row.feeItemName || row.feeItemId || '—' }}
          </template>
        </el-table-column>
        <el-table-column :label="t('bill.amount')" width="90" >
          <template #default="{ row }">{{ $money(row.billAmount) }}</template>
        </el-table-column>
        <el-table-column :label="t('bill.paid')" width="90" >
          <template #default="{ row }">{{ $money(row.paidAmount) }}</template>
        </el-table-column>
        <el-table-column :label="t('bill.waived')" width="85" >
          <template #default="{ row }">{{ $money(row.waivedAmount) }}</template>
        </el-table-column>
        <el-table-column :label="t('bill.payable')" width="90" >
          <template #default="{ row }">{{ $money(row.payableAmount) }}</template>
        </el-table-column>
        <el-table-column prop="dueDate" :label="t('bill.due')" width="105" />
        <el-table-column prop="billStatusLabel" :label="t('bill.status')" width="95">
          <template #default="{ row }">
            <el-tag size="small" :type="row.overdueNow ? 'danger'
              : (row.billStatus === 'PAID' ? 'success' : 'info')">
              {{ enumLabel('billStatus', row.billStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="overdueDays" :label="t('bill.overdueCol')" width="70" />
        <el-table-column :label="t('bill.actions')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('bill.detail') }}</el-button>
            <el-button link type="primary" @click="openAllocate(row)">{{ t('bill.allocate') }}</el-button>
            <el-dropdown trigger="click" style="margin-left:8px">
              <el-button link type="primary">{{ t('bill.more') }}</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="openWaive(row)">{{ t('bill.waive') }}</el-dropdown-item>
                  <el-dropdown-item @click="cancelBill(row)">{{ t('bill.cancel') }}</el-dropdown-item>
                  <el-dropdown-item @click="dunning(row)">{{ t('bill.remind') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                     :total="+total || 0" :page-size="q.pageSize" :current-page="q.pageNum"
                     @current-change="(p) => { q.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { q.pageSize = s; q.pageNum = 1; load() }" />
    </div>

    <!-- 批量出账 -->
    <el-dialog v-model="genVisible" :title="t('bill.genTitle')" width="500px">
      <el-form :model="g" label-width="120px">
        <el-form-item :label="labelOf('orgName')">
          <el-select v-model="g.orgId" filterable clearable style="width:100%"
                     :placeholder="t('bill.orgSearch')">
            <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('bill.feeItem')" required>
          <el-select v-model="g.feeItemId" filterable style="width:100%"
                     :placeholder="t('bill.selectFeeItem')" @change="loadGenRules">
            <el-option v-for="f in feeItems" :key="f.id"
                       :label="f.itemName || f.feeItemName || f.id" :value="String(f.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('bill.ruleName')">
          <el-radio-group v-model="g.ruleMode">
            <el-radio-button label="AUTO">{{ t('bill.ruleAuto') }}</el-radio-button>
            <el-radio-button label="MANUAL">{{ t('bill.ruleManual') }}</el-radio-button>
            <el-radio-button label="NONE">{{ t('bill.ruleNone') }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="g.ruleMode === 'MANUAL'" :label="t('bill.ruleName')" required>
          <el-select v-model="g.ruleId" filterable style="width:100%"
                     :placeholder="t('bill.selectRule')">
            <el-option v-for="r in genRules" :key="r.id"
                       :label="r.ruleName + '（' + r.ruleType + '）'" :value="String(r.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('bill.periodStart')" required>
          <el-date-picker v-model="g.periodStart" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('bill.periodEnd')" required>
          <el-date-picker v-model="g.periodEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('bill.paymentDueDate')">
          <el-date-picker v-model="g.dueDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" :placeholder="t('bill.paymentDueHint')" />
        </el-form-item>
        <el-alert type="warning" :closable="false" show-icon style="margin-bottom:8px"
                  :title="t('bill.billingDaysNote')" />
        <el-form-item :label="t('bill.dryRun')">
          <el-switch v-model="g.dryRun" /></el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                :title="t('bill.genTip1')" />
      <el-alert type="info" :closable="false" show-icon style="margin:4px 0 10px"
                :title="t('bill.genTip2')" />
      <div class="muted" style="font-size:12px;line-height:1.8;margin-bottom:6px">
        <b>{{ t('bill.formulaTitle') }}</b>
        <div class="muted" style="margin-bottom:4px">
          {{ t('bill.formulaDesc') }}
        </div>
        <div v-for="f in FORMULAS" :key="f.mode">
          <span :style="f.mode === selectedCalcMode ? 'color:#409eff;font-weight:600' : ''">
            {{ f.label }}：{{ f.text }}
          </span>
        </div>
      </div>
      <template #footer>
        <el-button @click="genVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doGenerate">{{ t('bill.startGen') }}</el-button>
      </template>
    </el-dialog>

    <!-- 批量出账结果 -->
    <el-dialog v-model="genResultVisible" :title="t('bill.resultTitle')" width="760px">
      <el-alert v-if="genResult" :closable="false" show-icon
                :type="genResult.skipped ? 'warning' : 'success'"
                :title="t('bill.genSummary', {
                  generated: genResult.generated || 0,
                  skipped: genResult.skipped ? t('bill.skippedPart', { n: genResult.skipped }) : '',
                  total: genResult.totalAmount != null ? t('bill.totalPart', { amount: genResult.totalAmount }) : ''
                })" />
      <el-table v-if="genResult && genResult.items" :data="genResult.items" size="small"
                border max-height="360" style="margin-top:10px">
        <el-table-column prop="contractNo" :label="labelOf('contractNo')" width="170" />
        <el-table-column :label="labelOf('amount')" width="100" >
          <template #default="{ row }">{{ $money(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="status" :label="labelOf('result')" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'OK' ? 'success' : 'warning'">
              {{ row.status === 'OK' ? t('bill.generatedOk') : t('bill.skippedTag') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="explain" :label="labelOf('explain')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reason" :label="labelOf('skipReason')" min-width="160" show-overflow-tooltip />
      </el-table>
      <template #footer>
        <el-button type="primary" @click="genResultVisible = false">{{ t('bill.gotIt') }}</el-button>
      </template>
    </el-dialog>

    <!-- 公摊费用分摊（物业） -->
    <el-dialog v-model="sharedVisible" :title="t('bill.sharedTitle')" width="560px">
      <el-alert type="info" :closable="false" show-icon
                :title="t('bill.sharedTip')"
                style="margin-bottom:12px" />
      <el-form :model="sf" label-width="110px">
        <el-form-item :label="labelOf('orgName')" required>
          <el-select v-model="sf.orgId" filterable style="width:100%" :placeholder="t('bill.selectOrg')">
            <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName" :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('bill.feeItem')" required>
          <el-select v-model="sf.feeItemId" filterable style="width:100%">
            <el-option v-for="f in feeItems" :key="f.id"
                       :label="f.itemName || f.feeItemName || f.itemCode || f.id"
                       :value="String(f.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="labelOf('totalAmount')" required>
          <el-input v-model="sf.totalAmount" type="number" :placeholder="t('bill.amountExample')" />
        </el-form-item>
        <el-form-item :label="labelOf('allocationMode')">
          <el-radio-group v-model="sf.allocateBy">
            <el-radio-button value="AREA">{{ t('bill.byArea') }}</el-radio-button>
            <el-radio-button value="HOUSE">{{ t('bill.byHousehold') }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('bill.periodStart')" required>
            <el-date-picker v-model="sf.periodStart" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('bill.periodEnd')" required>
            <el-date-picker v-model="sf.periodEnd" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="labelOf('billPeriod')" required>
            <el-input v-model="sf.billPeriod" placeholder="202610" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="labelOf('dueDate')">
            <el-date-picker v-model="sf.dueDate" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="sharedVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doShared">{{ t('bill.startShared') }}</el-button>
      </template>
    </el-dialog>

    <!-- 抄表录入（水电燃气按实际用量出账） -->
    <el-dialog v-model="meterVisible" :title="t('bill.meterTitle')" width="860px">
      <el-alert type="info" :closable="false" show-icon
                :title="t('bill.meterTip')"
                style="margin-bottom:12px" />
      <el-form :model="mf" label-width="96px" inline>
        <el-form-item :label="labelOf('houseName')">
          <el-select v-model="mf.houseId" filterable remote :remote-method="searchMeterHouse"
                     :loading="houseLoading" style="width:240px" :placeholder="t('bill.houseSearch')">
            <el-option v-for="h in meterHouses" :key="h.id" :label="h.houseName" :value="String(h.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('bill.feeItem')">
          <el-select v-model="mf.feeItemId" filterable style="width:200px">
            <el-option v-for="f in meterItems" :key="f.id"
                       :label="`${f.itemName}（${f.unitPrice}/${f.unit || '单位'}）`"
                       :value="String(f.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="labelOf('reading')">
          <el-input v-model="mf.reading" type="number" style="width:140px" />
        </el-form-item>
        <el-form-item :label="labelOf('readDate')">
          <el-date-picker v-model="mf.readDate" type="date" value-format="YYYY-MM-DD"
                          style="width:150px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="doMeterRecord">{{ t('bill.recordReading') }}</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="readings" size="small" border max-height="320" style="margin-top:8px">
        <el-table-column prop="readDate" :label="labelOf('readDate')" width="110" />
        <el-table-column prop="prevReading" :label="labelOf('prevReading')" width="100" />
        <el-table-column prop="reading" :label="labelOf('reading')" width="100" />
        <el-table-column prop="usageAmount" :label="labelOf('usage')" width="90" />
        <el-table-column :label="labelOf('unitPrice')" width="80" >
          <template #default="{ row }">{{ $money(row.unitPrice) }}</template>
        </el-table-column>
        <el-table-column :label="labelOf('amount')" width="100" >
          <template #default="{ row }">{{ $money(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="billStatus" :label="labelOf('status')" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.billStatus === 'BILLED' ? 'success' : 'warning'">
              {{ row.billStatus === 'BILLED' ? t('bill.billedYes') : t('bill.pendingBill') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="labelOf('actions')" width="90">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.billStatus === 'BILLED'"
                       @click="doMeterBill(row)">{{ t('bill.billAction') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="meterVisible = false">{{ t('bill.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 登记收款 PaymentCreateCmd -->
    <el-dialog v-model="payVisible" :title="t('bill.payTitle')" width="520px">
      <el-form :model="p" label-width="110px">
        <el-form-item :label="labelOf('orgName')">
          <el-select v-model="p.orgId" filterable clearable style="width:100%"
                     :placeholder="t('bill.orgSearch')">
            <el-option v-for="o in payOrgs" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="labelOf('personId')"><PersonPicker v-model="p.personId" width="240px" testid="person-picker" /></el-form-item>
        <el-form-item :label="labelOf('payerName')"><el-input v-model="p.payerName" /></el-form-item>
        <el-form-item :label="labelOf('payAmount')"><el-input v-model.number="p.payAmount" />
        </el-form-item>
        <el-form-item :label="labelOf('channel')">
          <el-select v-model="p.payChannel" style="width:100%">
              <el-option :label="enumLabel('payChannel', 'CASH')" value="CASH" />
              <el-option :label="enumLabel('payChannel', 'BANK')" value="BANK" />
              <el-option :label="enumLabel('payChannel', 'WECHAT')" value="WECHAT" />
              <el-option :label="enumLabel('payChannel', 'ALIPAY')" value="ALIPAY" />
            <el-option label="POS" value="POS" />
          </el-select></el-form-item>
        <el-form-item :label="labelOf('payTime')">
          <el-date-picker v-model="p.payTime" type="datetime" style="width:100%"
                          value-format="YYYY-MM-DD HH:mm:ss"
                          :placeholder="t('bill.payTimeHint')" />
        </el-form-item>
        <el-form-item :label="labelOf('transactionNo')"><el-input v-model="p.tradeNo" /></el-form-item>
        <el-form-item :label="labelOf('unknownSource')">
          <el-switch v-model="p.unknownFlag" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item :label="labelOf('remark')">
          <el-input v-model="p.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doPay">{{ t('bill.confirmPay') }}</el-button>
      </template>
    </el-dialog>

    <!-- 收款单列表 -->
    <el-dialog v-model="paymentsVisible" :title="t('bill.paymentsTitle')" width="1120px" top="5vh">
      <div class="toolbar" style="margin-bottom:8px">
        <el-input v-model="payKeyword" :placeholder="t('bill.paymentSearch')" clearable style="width:240px"
                  @keyup.enter="loadPayments" />
        <el-button type="primary" @click="loadPayments">查询</el-button>
        <div class="spacer" />
        <el-button @click="openPay">登记收款</el-button>
      </div>
      <el-table :data="payments" border size="small" max-height="420"
                empty-text="暂无收款单，点击「登记收款」新增">
        <el-table-column prop="paymentNo" :label="t('bill.paymentNo')" width="185" />
        <el-table-column :label="labelOf('payerName')" width="130">
          <template #default="{ row }">
            {{ row.payerName || row.personIdName || row.personId || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="payAmount" :label="labelOf('payAmount')" width="110" />
        <el-table-column prop="reconciledAmount" :label="t('bill.allocateAmount')" width="110" />
        <el-table-column prop="remainAmount" :label="labelOf('balance')" width="110" />
        <el-table-column :label="labelOf('status')" width="110">
          <template #default="{ row }">{{ row.payStatusLabel || row.payStatus }}</template>
        </el-table-column>
        <el-table-column prop="payTime" :label="labelOf('payTime')" width="170" />
        <el-table-column :label="labelOf('actions')" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openPaymentDetail(row)">{{ t('bill.detail') }}</el-button>
            <el-button link type="success" :disabled="!Number(row.remainAmount)"
                       @click="usePayment(row)">核销到账单</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:10px" layout="total, prev, pager, next"
                     :total="+payTotal || 0" :page-size="payPageSize"
                     :current-page="payPageNum"
                     @current-change="(p) => { payPageNum = p; loadPayments() }" />
    </el-dialog>

    <!-- 收款单详情：使用明细 -->
    <el-dialog v-model="payDetailVisible" title="收款单详情" width="820px">
      <el-descriptions v-if="payDetail" :column="2" border size="small">
        <el-descriptions-item :label="t('bill.paymentNo')">{{ payDetail.paymentNo }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('payerName')">
          {{ payDetail.payerName || payDetail.personIdName || payDetail.personId || '—' }}
        </el-descriptions-item>
        <el-descriptions-item :label="labelOf('payAmount')">{{ payDetail.payAmount }}</el-descriptions-item>
        <el-descriptions-item :label="t('bill.allocateAmount')">{{ payDetail.reconciledAmount }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('balance')">{{ payDetail.remainAmount }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('channel')">
          {{ enumLabel('payChannel', payDetail.payChannel) || payDetail.payChannel }}
        </el-descriptions-item>
        <el-descriptions-item :label="labelOf('payTime')">{{ payDetail.payTime }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('status')">
          {{ payDetail.payStatusLabel || payDetail.payStatus }}
        </el-descriptions-item>
        <el-descriptions-item :label="labelOf('remark')" :span="2">{{ payDetail.remark || '—' }}</el-descriptions-item>
      </el-descriptions>
      <div style="font-weight:600;margin:12px 0 6px">{{ t('bill.usageDetail') }}</div>
      <el-table :data="payUsage" border size="small"
                :empty-text="t('bill.noUsage')">
        <el-table-column prop="bill_no" :label="labelOf('billNo')" width="190" />
        <el-table-column prop="allocate_amount" :label="t('bill.allocateAmount')" width="120" />
        <el-table-column prop="create_time" :label="labelOf('allocateTime')" />
      </el-table>
    </el-dialog>

    <!-- 收款单核销到账单 -->
    <el-dialog v-model="useVisible" :title="t('bill.useTitle')" width="620px">
      <el-alert type="info" :closable="false" show-icon
                :title="t('bill.useTip')" />
      <el-form label-width="110px" style="margin-top:10px">
        <el-form-item :label="t('bill.paymentNo')">
          <el-input :model-value="usePaymentRow?.paymentNo" disabled />
        </el-form-item>
        <el-form-item :label="t('bill.availableAmount')">
          <el-input :model-value="usePaymentRow?.remainAmount" disabled />
        </el-form-item>
        <div style="font-weight:600;margin:6px 0">{{ t('bill.targetBill') }}</div>
        <el-table :data="useBills" border size="small" max-height="300"
                  @selection-change="onUseSelection">
          <el-table-column type="selection" width="42" />
          <el-table-column prop="billNo" :label="t('bill.no')" width="165" />
          <el-table-column prop="feeItemId" :label="t('bill.feeItem')" min-width="120">
            <template #default="{ row }">
              {{ row.feeItemIdName || row.feeItemName || row.feeItemId }}
            </template>
          </el-table-column>
          <el-table-column prop="billPeriod" :label="t('bill.billingPeriod')" width="90" />
          <el-table-column :label="t('bill.pendingAmount')" width="100">
            <template #default="{ row }">{{ $money(row.payableAmount) }}</template>
          </el-table-column>
        </el-table>
        <div class="muted" style="margin-top:8px">
          {{ t('bill.selectedBills', { n: useSelected.length }) }}
          · {{ t('bill.selectedTotal') }} {{ $money(useTotal) }}
        </div>
      </el-form>
      <template #footer>
        <el-button @click="useVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="confirmUse">{{ t('bill.confirmAllocate') }}</el-button>
      </template>
    </el-dialog>

    <!-- 合同预收余额 -->
    <el-dialog v-model="prepayVisible" :title="t('bill.prepayTitle')" width="760px">
      <el-form label-width="110px">
        <el-form-item :label="t('bill.contract')">
          <ContractSelect v-model="prepayContractId" width="100%"
                          @update:model-value="loadPrepay" />
        </el-form-item>
      </el-form>
      <el-descriptions v-if="prepayAccount" :column="3" border size="small">
        <el-descriptions-item :label="t('bill.prepayBalance')">
          {{ $money(prepayAccount.balanceAmount) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('bill.prepayTotalIn')">
          {{ $money(prepayAccount.totalIn) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('bill.prepayTotalOut')">
          {{ $money(prepayAccount.totalOut) }}
        </el-descriptions-item>
      </el-descriptions>
      <el-row :gutter="12" style="margin-top:12px">
        <el-col :span="12">
          <el-form label-width="90px">
            <el-form-item :label="t('bill.prepayAmount')">
              <el-input v-model.number="prepayAmount" type="number" />
            </el-form-item>
            <el-form-item :label="t('bill.payChannel')">
              <el-select v-model="prepayChannel" style="width:100%">
                <el-option label="现金" value="CASH" />
                <el-option label="银行转账" value="BANK_TRANSFER" />
                <el-option label="微信" value="WECHAT" />
                <el-option label="支付宝" value="ALIPAY" />
              </el-select>
            </el-form-item>
            <el-button type="primary" :loading="saving" @click="doPrepayIn">
              {{ t('bill.prepayIn') }}
            </el-button>
            <el-button type="warning" plain :loading="saving" @click="doPrepayApply">
              {{ t('bill.prepayApply') }}
            </el-button>
          </el-form>
        </el-col>
        <el-col :span="12">
          <el-form label-width="90px">
            <el-form-item :label="t('bill.refundAmount')">
              <el-input v-model.number="refundAmount" type="number" />
            </el-form-item>
            <el-form-item :label="t('bill.refundFee')">
              <el-input v-model.number="refundFee" type="number" />
            </el-form-item>
            <el-button type="danger" plain :loading="saving" @click="doPrepayRefund">
              {{ t('bill.prepayRefund') }}
            </el-button>
          </el-form>
        </el-col>
      </el-row>
      <el-divider content-position="left">{{ t('bill.prepayTransfer') }}</el-divider>
      <el-form label-width="110px" inline>
        <el-form-item :label="t('bill.transferTarget')">
          <ContractSelect v-model="prepayTargetId" width="240px" />
        </el-form-item>
        <el-form-item :label="t('bill.transferAmount')">
          <el-input v-model.number="transferAmount" type="number" style="width:150px" />
        </el-form-item>
        <el-button type="primary" plain :loading="saving" @click="doPrepayTransfer">
          {{ t('bill.prepayTransfer') }}
        </el-button>
      </el-form>
      <el-table :data="prepayAccount?.flows || []" border size="small" max-height="260"
                style="margin-top:12px">
        <el-table-column :label="t('bill.flowType')" width="90">
          <template #default="{ row }">{{ enumLabel('flowType', row.flowType) }}</template>
        </el-table-column>
        <el-table-column prop="amount" :label="t('bill.amount')" width="100" />
        <el-table-column prop="balanceAfter" :label="t('bill.prepayBalance')" width="110" />
        <el-table-column :label="t('bill.bizType')" width="110">
          <template #default="{ row }">{{ enumLabel('bizType', row.bizType) }}</template>
        </el-table-column>
        <el-table-column prop="remark" :label="t('bill.remark')" min-width="160" />
        <el-table-column prop="createTime" :label="t('bill.time')" width="170" />
      </el-table>
      <template #footer>
        <el-button @click="prepayVisible = false">{{ t('common.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 核销 AllocateCmd -->
    <el-dialog v-model="allocVisible" :title="t('bill.allocTitle')" width="480px">
      <el-alert type="info" :closable="false" show-icon
                :title="t('bill.allocTip')" />
      <el-form :model="a" label-width="110px" style="margin-top:12px">
        <el-form-item :label="labelOf('billNo')">
          <el-input :model-value="current?.billNo" disabled /></el-form-item>
        <el-form-item :label="labelOf('billPayable')">
          <el-input :model-value="current?.payableAmount" disabled /></el-form-item>
        <el-form-item :label="t('bill.paymentNo')" required>
          <el-select v-model="a.paymentId" filterable style="width:100%"
                     :placeholder="t('bill.selectPayment')">
            <el-option v-for="x in openPaymentsList" :key="x.id"
                       :label="x.paymentNo + ' · ' + (x.payerName || x.personIdName || x.personId || '—') + ' · ' + t('bill.balancePrefix') + ' ' + (x.remainAmount ?? 0)"
                       :value="String(x.id)" />
          </el-select>
          <span class="muted" style="font-size:12px">
            {{ t('bill.noPaymentHint') }}
          </span>
        </el-form-item>
        <el-form-item :label="t('bill.allocateAmount')">
          <el-input v-model.number="a.amount" :placeholder="t('bill.amountHint')" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="allocVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doAllocate">{{ t('bill.confirmAllocate') }}</el-button>
      </template>
    </el-dialog>

    <!-- 减免 WaiveCmd -->
    <el-dialog v-model="waiveVisible" :title="t('bill.waiveTitle')" width="460px">
      <el-form :model="w" label-width="110px">
        <el-form-item :label="labelOf('billNo')">
          <el-input :model-value="current?.billNo" disabled /></el-form-item>
        <el-form-item :label="labelOf('waiveAmount')">
          <el-input v-model.number="w.waiveAmount" :placeholder="t('bill.amountHint')" /></el-form-item>
        <el-form-item :label="labelOf('waiveReason')">
          <el-input v-model="w.reason" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="waiveVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="warning" :loading="saving" @click="doWaive">{{ t('bill.confirmWaive') }}</el-button>
      </template>
    </el-dialog>
  </div>

    <!-- 账单详情：结构化信息 + 计费说明 -->
    <el-dialog v-model="dvVisible" :title="t('bill.detailTitle')" width="780px" top="6vh">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
        <span style="font-weight:600">{{ dvRow.billNo }}</span>
        <el-tag size="small" :type="dvRow.billStatus === 'PAID' ? 'success'
          : (dvRow.billStatus === 'CANCELLED' ? 'info' : 'warning')">
          {{ enumLabel('billStatus', dvRow.billStatus) }}
        </el-tag>
        <span class="muted" v-if="dvRow.generateType">
          {{ t('bill.generateType') }}: {{ enumLabel('generateType', dvRow.generateType) }}
        </span>
      </div>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item :label="labelOf('payerName')">
          {{ dvRow.payerName || dvRow.personIdName || '—' }}
          <span v-if="dvRow.payerPhone" class="muted">（{{ dvRow.payerPhone }}）</span>
        </el-descriptions-item>
        <el-descriptions-item :label="labelOf('contractNo')">
          {{ dvRow.contractIdName || dvRow.contractId || '—' }}
        </el-descriptions-item>
        <el-descriptions-item :label="labelOf('houseName')">
          {{ dvRow.houseIdName || dvRow.houseId || '—' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('bill.feeItem')">
          {{ dvRow.feeItemIdName || dvRow.feeItemName || dvRow.feeItemId || '—' }}
        </el-descriptions-item>
        <el-descriptions-item :label="labelOf('billPeriod')">{{ dvRow.billPeriod }}（{{ dvRow.periodStart }} ~ {{ dvRow.periodEnd }}）</el-descriptions-item>
        <el-descriptions-item :label="t('bill.settlementDate')">{{ dvRow.settlementDate || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('bill.billDate')">{{ dvRow.billDate || dvRow.createTime || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('bill.billingDays')">{{ dvRow.billingDays ?? '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('bill.prorationMonths')">{{ dvRow.prorationMonths ?? '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('bill.unitPriceSnapshot')">{{ dvRow.unitPriceSnapshot ?? '—' }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('payDue')">{{ dvRow.dueDate || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('billAmount')">{{ dvRow.billAmount }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('paidAmount')">{{ dvRow.paidAmount }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('waiveAmount')">{{ dvRow.waivedAmount }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('payableAmount')">{{ dvRow.payableAmount }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('lateFee')">{{ dvRow.lateFee || 0 }}</el-descriptions-item>
        <el-descriptions-item :label="labelOf('overdueDays')">{{ dvRow.overdueDays || 0 }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top:12px">
        <div style="font-weight:600;margin-bottom:6px">{{ t('bill.paymentsDetail') }}</div>
        <el-table :data="billPayments" size="small" border
                  :empty-text="t('bill.noPayments')">
          <el-table-column prop="payment_no" :label="t('bill.paymentNo')" width="185" />
          <el-table-column :label="labelOf('payerName')" width="110">
            <template #default="{ row }">{{ row.payer_name || '—' }}</template>
          </el-table-column>
          <el-table-column prop="allocate_amount" :label="t('bill.allocateAmount')" width="110" />
          <el-table-column :label="labelOf('channel')" width="90">
            <template #default="{ row }">
              {{ enumLabel('payChannel', row.pay_channel) || row.pay_channel }}
            </template>
          </el-table-column>
          <el-table-column prop="pay_time" :label="labelOf('payTime')" />
        </el-table>
      </div>
      <div v-if="explainRows.length" style="margin-top:12px">
        <div style="font-weight:600;margin-bottom:6px">{{ t('bill.calcDetail') }}</div>
        <el-table :data="explainRows" size="small" border>
          <el-table-column :label="labelOf('item')" width="130">
            <template #default="{ row }">{{ explainLabel(row.label) }}</template>
          </el-table-column>
          <el-table-column :label="labelOf('value')">
            <template #default="{ row }">{{ explainValue(row.label, row.value) }}</template>
          </el-table-column>
        </el-table>
      </div>
      <el-alert v-if="dvRow.remark" type="info" :closable="false" show-icon
                style="margin-top:10px" :title="t('bill.remarkTitle')">
        <div style="white-space:pre-wrap">{{ localizeRemark(dvRow.remark) }}</div>
      </el-alert>
      <el-collapse style="margin-top:8px">
        <el-collapse-item :title="t('bill.rawFields')">
          <DetailView :row="dvRow" />
        </el-collapse-item>
      </el-collapse>
    </el-dialog>

    <!-- 能耗分析 -->
    <el-dialog v-model="energyVisible" :title="t('bill.energyTitle')" width="860px">
      <div style="margin-bottom:8px">
        <el-radio-group v-model="energyMonths" size="small" @change="loadEnergy">
          <el-radio-button :value="3">{{ t('bill.last3') }}</el-radio-button>
          <el-radio-button :value="6">{{ t('bill.last6') }}</el-radio-button>
          <el-radio-button :value="12">{{ t('bill.last12') }}</el-radio-button>
        </el-radio-group>
        <span class="muted" style="font-size:12px;margin-left:8px">
          {{ t('bill.energyFormula') }}
        </span>
      </div>
      <el-row :gutter="12">
        <el-col :span="12">
          <div style="font-weight:600;margin-bottom:6px">{{ t('bill.monthlyTrend') }}</div>
          <el-table :data="energyMonths0" size="small" border max-height="240">
            <el-table-column prop="month" :label="labelOf('month')" width="100" />
            <el-table-column prop="reading" :label="labelOf('readCount')" width="90" />
            <el-table-column prop="usage" :label="labelOf('usage')" />
            <el-table-column :label="labelOf('amount')" >
          <template #default="{ row }">{{ $money(row.amount) }}</template>
        </el-table-column>
          </el-table>
        </el-col>
        <el-col :span="12">
          <div style="font-weight:600;margin-bottom:6px">{{ t('bill.buildingSummary') }}</div>
          <el-table :data="energyBuildings" size="small" border max-height="240">
            <el-table-column prop="building" :label="labelOf('building')" />
            <el-table-column prop="usage" :label="labelOf('usage')" width="120" />
          </el-table>
        </el-col>
      </el-row>
      <div style="font-weight:600;margin:12px 0 6px">{{ t('bill.topHouses') }}</div>
      <el-table :data="energyTop" size="small" border max-height="260">
        <el-table-column prop="houseCode" :label="labelOf('houseCode')" width="150" />
        <el-table-column prop="houseName" :label="labelOf('houseName')" min-width="180" />
        <el-table-column prop="building" :label="labelOf('building')" width="110" />
        <el-table-column prop="usage" :label="labelOf('usage')" width="100" />
      </el-table>
      <template #footer>
        <el-button @click="energyVisible = false">{{ t('bill.close') }}</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { getLocale } from '@/i18n'

/** 通用详情弹窗（复用 DetailView） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
const explainRows = ref([])

const billPayments = ref([])

async function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
  explainRows.value = []
  billPayments.value = []
  try {
    const list = await req.get('/fin/bills/' + row.id + '/payments')
    billPayments.value = list || []
  } catch (e) { billPayments.value = [] }
  try {
    const e = await req.get('/fin/bills/' + row.id + '/explain')
    explainRows.value = (e && e.lines) || []
  } catch (err) { explainRows.value = [] }
}

import { enumLabel } from '@/constants/enums'
import { labelOf } from '@/constants/fieldLabels'
import { ref, reactive, computed, onMounted } from 'vue'
import DetailView from '@/components/DetailView.vue'
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/modules'
import req from '@/api/request'
import { downloadCsv, fetchAllPages } from '@/utils/csv'
import OrgSelect from '@/components/OrgSelect.vue'
import ContractSelect from '@/components/ContractSelect.vue'
import LineTrend from '@/components/LineTrend.vue'

const statuses = ['UNPAID', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED', 'CANCELLED']
const loading = ref(false)
const saving = ref(false)

/** 抄表录入（METER 类收费） */
const meterVisible = ref(false)
const meterItems = ref([])
const meterHouses = ref([])
const houseLoading = ref(false)
const readings = ref([])
const mf = reactive({ houseId: '', feeItemId: '', reading: 0, readDate: '' })

async function openMeter() {
  meterVisible.value = true
  mf.readDate = new Date().toISOString().slice(0, 10)
  if (!meterItems.value.length) {
    try {
      const fi = await financeApi.feeItems({ pageNum: 1, pageSize: 100 })
      meterItems.value = ((fi && fi.rows) || []).filter((x) => x.calcMode === 'METER')
    } catch (e) { /* 忽略 */ }
  }
  await searchMeterHouse('')
  await loadReadings()
}

async function searchMeterHouse(kw) {
  houseLoading.value = true
  try {
    const d = await financeApi.houses({ pageNum: 1, pageSize: 20, keyword: kw || undefined })
    meterHouses.value = (d && d.rows) || []
  } finally { houseLoading.value = false }
}

async function loadReadings() {
  try {
    const d = await financeApi.meterList({ pageNum: 1, pageSize: 50, houseId: mf.houseId || undefined })
    readings.value = (d && d.rows) || []
  } catch (e) { readings.value = [] }
}

async function doMeterRecord() {
  if (!mf.houseId || !mf.feeItemId || mf.reading === '' || mf.reading === null) {
    ElMessage.warning(t('msg.meterRequired')); return
  }
  saving.value = true
  try {
    const r = await financeApi.meterRecord({
      houseId: mf.houseId, feeItemId: mf.feeItemId,
      reading: Number(mf.reading), readDate: mf.readDate || undefined
    })
    ElMessage.success(t('msg.meterSaved', { usage: r?.usageAmount ?? '-', amount: r?.amount ?? '-' }))
    await loadReadings()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('msg.saveFailed'))
  } finally { saving.value = false }
}

async function doMeterBill(row) {
  saving.value = true
  try {
    const b = await req.post(`/fin/meter-readings/${row.id}/bill`, {})
    ElMessage.success(t('msg.billGenerated', { no: b?.billNo || '', amount: b?.payableAmount ?? '' }))
    await loadReadings()
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('msg.billFailed'))
  } finally { saving.value = false }
}
const rows = ref([])
const selected = ref([])

function onSelect(v) { selected.value = v || [] }

async function loadGenOptions() {
  try {
    const org = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = (org && org.rows) || []
  } catch (e) { orgOptions.value = [] }
  try {
    const fi = await req.get('/fin/fee-items', { params: { pageNum: 1, pageSize: 200 } })
    feeItems.value = (fi && fi.rows) || []
  } catch (e) { feeItems.value = [] }
}

const FORMULAS = computed(() => [
  { mode: 'FIXED', label: t('fee.fixed'), text: t('bill.formulaFixed') },
  { mode: 'BY_AREA', label: t('fee.byArea'), text: t('bill.formulaArea') },
  { mode: 'BY_HOUSE', label: t('fee.byHouse'), text: t('bill.formulaHouse') },
  { mode: 'BY_PERSON', label: t('fee.byPerson'), text: t('bill.formulaPerson') },
  { mode: 'BY_BED', label: t('fee.byBed'), text: t('bill.formulaBed') },
  { mode: 'BY_NIGHT', label: t('fee.byNight'), text: t('bill.formulaNight') },
  { mode: 'METER', label: t('fee.meter'), text: t('bill.formulaMeter') }
])
const genResultVisible = ref(false)
const genResult = ref(null)
const selectedCalcMode = computed(() => {
  const f = feeItems.value.find((x) => String(x.id) === String(g.feeItemId))
  return f ? f.calcMode : ''
})

function openGen() {
  Object.assign(g, { orgId: '', feeItemId: '', periodStart: '', periodEnd: '', dueDate: '',
    billPeriod: '', dryRun: false, ruleMode: 'AUTO', ruleId: '' })
  genRules.value = []
  loadGenOptions()
  genVisible.value = true
}
const total = ref(0)
const q = reactive({ orgId: '', pageNum: 1, pageSize: 20, billStatus: '', billPeriod: '',
  houseId: '' })

/** 账单趋势：应收 / 实收 */
const trendRows = ref([])
const recvTrend = computed(() => trendRows.value.map((m) => ({
  label: String(m.month || '').slice(5), value: Number(m.receivable) || 0
})))
const paidTrend = computed(() => trendRows.value.map((m) => ({
  label: String(m.month || '').slice(5), value: Number(m.received) || 0
})))

const exporting = ref(false)

/** 按当前筛选导出账单 CSV（分页拉全量） */
async function exportBills() {
  exporting.value = true
  try {
    const rows = await fetchAllPages((params) => financeApi.bills(params), {
      orgId: q.orgId || undefined,
      status: q.billStatus || undefined,
      billPeriod: q.billPeriod || undefined,
      houseId: q.houseId || undefined
    })
    downloadCsv(t('bill.exportFile') + '_' + new Date().toISOString().slice(0, 10), [
      { key: 'billNo', label: labelOf('billNo') },
      { key: 'payerName', label: labelOf('payerName') },
      { key: 'billPeriod', label: labelOf('billPeriod') },
      { key: 'billAmount', label: labelOf('billAmount') },
      { key: 'paidAmount', label: labelOf('paidAmount') },
      { key: 'waivedAmount', label: labelOf('waivedAmount') },
      { key: 'payableAmount', label: labelOf('payableAmount') },
      { key: 'dueDate', label: labelOf('dueDate') },
      { key: 'billStatusLabel', label: labelOf('billStatus'), map: (r) => enumLabel('billStatus', r.billStatus) },
      { key: 'overdueDays', label: labelOf('overdueDays') }
    ], rows)
    ElMessage.success(t('bill.exported', { n: rows.length }))
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('bill.exportFailed'))
  } finally { exporting.value = false }
}

async function loadTrend() {
  try {
    const d = await req.get('/fin/bills/trend', { params: { months: 6 } })
    trendRows.value = d || []
  } catch (e) { trendRows.value = [] }
}
const current = ref(null)

const genVisible = ref(false)
const g = reactive({ orgId: null, billPeriod: '', dueDate: '', dryRun: true,
  ruleMode: 'AUTO', ruleId: '', feeItemId: '', periodStart: '', periodEnd: '' })
const genRules = ref([])

async function loadGenRules() {
  genRules.value = []
  if (!g.feeItemId) return
  try {
    const list = await req.get('/fin/billing-rules', { params: { feeItemId: g.feeItemId } })
    genRules.value = (list || []).filter((r) =>
      r.approveStatus === 'APPROVED' && r.status === 'ENABLED')
  } catch (e) { genRules.value = [] }
}

/** 公摊分摊（物业管理） */
const sharedVisible = ref(false)
const orgOptions = ref([])
const feeItems = ref([])
const sf = reactive({ orgId: '', feeItemId: '', totalAmount: 0, allocateBy: 'AREA',
  periodStart: '', periodEnd: '', billPeriod: '', dueDate: '' })

async function openShared() {
  sharedVisible.value = true
  try {
    const org = await financeApi.orgs({ pageNum: 1, pageSize: 100 })
    orgOptions.value = (org && org.rows) || []
  } catch (e) { /* 组织加载失败不阻断 */ }
  try {
    const fi = await financeApi.feeItems({ pageNum: 1, pageSize: 100 })
    feeItems.value = (fi && fi.rows) || []
  } catch (e) { /* 收费项目加载失败不阻断 */ }
}

async function doShared() {
  if (!sf.orgId || !sf.feeItemId || !sf.totalAmount) {
    ElMessage.warning(t('msg.orgItemAmount')); return
  }
  if (!sf.periodStart || !sf.periodEnd || !sf.billPeriod) {
    ElMessage.warning(t('msg.periodRequired')); return
  }
  saving.value = true
  try {
    const r = await financeApi.generateShared({
      orgId: sf.orgId, feeItemId: sf.feeItemId, totalAmount: Number(sf.totalAmount),
      allocateBy: sf.allocateBy, periodStart: sf.periodStart, periodEnd: sf.periodEnd,
      billPeriod: sf.billPeriod, dueDate: sf.dueDate || undefined
    })
    ElMessage.success(t('msg.allocationDone', { created: r?.created || 0, skipped: r?.skipped || 0 }))
    sharedVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('msg.allocationFailed'))
  } finally { saving.value = false }
}

const payVisible = ref(false)
const payOrgs = ref([])
async function loadPayOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    payOrgs.value = (d && d.rows) || []
  } catch (e) { payOrgs.value = [] }
}
function nowText() {
  const d = new Date()
  const z = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + z(d.getMonth() + 1) + '-' + z(d.getDate())
    + ' ' + z(d.getHours()) + ':' + z(d.getMinutes()) + ':' + z(d.getSeconds())
}
const p = reactive({ orgId: null, personId: null, payerName: '', payAmount: null,
  payChannel: 'CASH', payTime: nowText(), tradeNo: '', unknownFlag: 0, remark: '' })

const allocVisible = ref(false)
const a = reactive({ paymentId: null, amount: null })
const paymentsVisible = ref(false)
const payments = ref([])
const openPaymentsList = ref([])
const payKeyword = ref('')
const payPageNum = ref(1)
const payPageSize = ref(50)
const payTotal = ref(0)

async function loadPayments() {
  try {
    const d = await req.get('/fin/payments', {
      params: { pageNum: payPageNum.value, pageSize: payPageSize.value,
        keyword: payKeyword.value || undefined }
    })
    payments.value = (d && d.rows) || []
    payTotal.value = Number((d && d.total) || 0)
    openPaymentsList.value = payments.value.filter((x) => Number(x.remainAmount) > 0)
  } catch (e) { payments.value = []; openPaymentsList.value = [] }
}

async function openPayments() {
  payPageNum.value = 1
  await loadPayments()
  paymentsVisible.value = true
}

const payDetailVisible = ref(false)
const payDetail = ref(null)
const payUsage = ref([])
const useVisible = ref(false)
const usePaymentRow = ref(null)
const useBills = ref([])
const useBillId = ref('')
const useAmount = ref(null)
const useSelected = ref([])
const useTotal = computed(() =>
  useSelected.value.reduce((sum, b) => sum + Number(b.payableAmount || 0), 0))

async function openPaymentDetail(row) {
  payDetail.value = row
  payUsage.value = []
  payDetailVisible.value = true
  try {
    const list = await req.get('/fin/payments/' + row.id + '/allocations')
    payUsage.value = list || []
  } catch (e) { payUsage.value = [] }
}

/** 收款单 → 直接核销到账单 */
async function usePayment(row) {
  usePaymentRow.value = row
  useBillId.value = ''
  useAmount.value = null
  useSelected.value = []
  useBills.value = []
  paymentsVisible.value = false
  useVisible.value = true
  try {
    const params = { pageNum: 1, pageSize: 100, status: 'UNPAID' }
    if (row.contractId) params.contractId = row.contractId
    else if (row.personId) params.personId = row.personId
    const d = await req.get('/fin/bills', { params })
    let rows = (d && d.rows) || []
    // 没有缴费人时才退回全部未缴账单；有缴费人时不得跨人核销
    if (!rows.length && !row.personId) {
      const all = await req.get('/fin/bills', { params: { pageNum: 1, pageSize: 100, status: 'UNPAID' } })
      rows = (all && all.rows) || []
    }
    useBills.value = rows
  } catch (e) { useBills.value = [] }
}

function onUseBillChange(id) {
  const b = useBills.value.find((x) => String(x.id) === String(id))
  if (!b) return
  useAmount.value = Number(b.payableAmount || 0)
}

function onUseSelection(rows) {
  useSelected.value = rows || []
  useAmount.value = useTotal.value
}

async function confirmUse() {
  if (!useSelected.value.length) { ElMessage.warning(t('msg.selectBill')); return }
  saving.value = true
  try {
    await financeApi.allocateBatch(usePaymentRow.value.id,
      useSelected.value.map((b) => ({ billId: b.id, amount: b.payableAmount })))
    ElMessage.success(t('msg.verified'))
    useVisible.value = false
    load()
    loadPayments()
  } finally { saving.value = false }
}

const prepayVisible = ref(false)
const prepayContractId = ref('')
const prepayAccount = ref(null)
const prepayAmount = ref(null)
const prepayChannel = ref('CASH')
const refundAmount = ref(null)
const refundFee = ref(0)

async function openPrepay() {
  prepayVisible.value = true
  prepayAccount.value = null
  prepayAmount.value = null
  refundAmount.value = null
  refundFee.value = 0
}

async function loadPrepay() {
  if (!prepayContractId.value) { prepayAccount.value = null; return }
  try {
    prepayAccount.value = await financeApi.prepayAccount(prepayContractId.value)
  } catch (e) { prepayAccount.value = null }
}

async function doPrepayIn() {
  if (!prepayContractId.value) { ElMessage.warning(t('bill.contract')); return }
  if (!prepayAmount.value || Number(prepayAmount.value) <= 0) {
    ElMessage.warning(t('bill.prepayAmount')); return
  }
  saving.value = true
  try {
    prepayAccount.value = await financeApi.prepayIn({
      contractId: prepayContractId.value,
      amount: Number(prepayAmount.value),
      payChannel: prepayChannel.value
    })
    prepayAmount.value = null
    ElMessage.success(t('common.success'))
  } finally { saving.value = false }
}

async function doPrepayApply() {
  if (!prepayContractId.value) return
  saving.value = true
  try {
    const n = await financeApi.prepayApply(prepayContractId.value)
    ElMessage.success(t('bill.prepayApplied', { n }))
    await loadPrepay()
    load()
  } finally { saving.value = false }
}

const prepayTargetId = ref('')
const transferAmount = ref(null)

async function doPrepayTransfer() {
  if (!prepayContractId.value || !prepayTargetId.value || !transferAmount.value) return
  saving.value = true
  try {
    prepayAccount.value = await financeApi.prepayTransfer({
      fromContractId: prepayContractId.value,
      toContractId: prepayTargetId.value,
      amount: Number(transferAmount.value)
    })
    transferAmount.value = null
    ElMessage.success(t('common.success'))
  } finally { saving.value = false }
}

async function doPrepayRefund() {
  if (!prepayContractId.value || !refundAmount.value) return
  saving.value = true
  try {
    prepayAccount.value = await financeApi.prepayRefund({
      contractId: prepayContractId.value,
      amount: Number(refundAmount.value),
      feeAmount: Number(refundFee.value || 0),
      payChannel: prepayChannel.value
    })
    refundAmount.value = null
    refundFee.value = 0
    ElMessage.success(t('common.success'))
  } finally { saving.value = false }
}

const waiveVisible = ref(false)
const w = reactive({ waiveAmount: null, reason: '' })

async function load() {
  loading.value = true
  try {
    const d = await financeApi.bills({
      pageNum: q.pageNum, pageSize: q.pageSize,
      orgId: q.orgId || undefined,
      status: q.billStatus || undefined,
      billPeriod: q.billPeriod || undefined,
      houseId: q.houseId || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}
function reload() { q.pageNum = 1; load() }

async function doGenerate() {
  if (!g.feeItemId) { ElMessage.warning(t('msg.selectFeeItem')); return }
  if (!g.periodStart || !g.periodEnd) { ElMessage.warning(t('msg.feeDates')); return }
  if (g.periodEnd <= g.periodStart) { ElMessage.warning(t('msg.endAfterStart')); return }
  if (g.periodStart.slice(0, 7) !== g.periodEnd.slice(0, 7)) {
    ElMessage.warning(t('msg.noCrossMonth'))
    return
  }
  if (g.ruleMode === 'MANUAL' && !g.ruleId) {
    ElMessage.warning(t('msg.selectRule')); return
  }
  if (!g.dryRun) {
    await ElMessageBox.confirm(
      '将为该组织/项目/费用区间内符合条件的合同生成账单；已出过账的会自动跳过。是否继续？',
      '确认批量出账', { type: 'warning' })
  }
  saving.value = true
  try {
    const r = await financeApi.generate({
      orgId: g.orgId || undefined, feeItemId: g.feeItemId,
      periodStart: g.periodStart, periodEnd: g.periodEnd,
      dueDate: g.dueDate || undefined, billPeriod: g.periodStart.slice(0, 7).replace('-', ''),
      dryRun: !!g.dryRun
    })
    genResult.value = r
    genResultVisible.value = true
    genVisible.value = false
    load()
  } finally { saving.value = false }
}

function openPay() {
  loadPayOrgs()
  p.payTime = nowText()
  payVisible.value = true
}
async function doPay() {
  if (!p.payAmount || p.payAmount <= 0) { ElMessage.warning(t('msg.payPositive')); return }
  saving.value = true
  try {
    const created = await financeApi.createPayment({ ...p })
    const no = created && (created.paymentNo || created.id)
    ElMessage.success(t('msg.paymentSaved', { no: no || '' }))
    payVisible.value = false
    loadPayments()
  } finally { saving.value = false }
}

function openAllocate(row) {
  current.value = row; a.paymentId = null; a.amount = null
  loadPayments()
  allocVisible.value = true
}
async function doAllocate() {
  if (!a.paymentId) { ElMessage.warning(t('msg.paymentIdRequired')); return }
  saving.value = true
  try {
    await financeApi.allocate(a.paymentId, current.value.id, a.amount)
    ElMessage.success(t('msg.verified'))
    allocVisible.value = false; load()
  } finally { saving.value = false }
}

function openWaive(row) {
  current.value = row; w.waiveAmount = null; w.reason = ''
  waiveVisible.value = true
}
async function doWaive() {
  if (!w.reason) { ElMessage.warning(t('msg.reductionReason')); return }
  saving.value = true
  try {
    await financeApi.waive(current.value.id, { ...w })
    ElMessage.success(t('msg.reductionDone'))
    waiveVisible.value = false; load()
  } finally { saving.value = false }
}

async function cancelBill(row) {
  const { value } = await ElMessageBox.prompt(t('bill.cancelPrompt'), t('bill.cancelTitle'))
  await financeApi.cancelBill(row.id, value)
  ElMessage.success(t('msg.billCancelled')); load()
}

async function dunning(row) {
  await req.post('/fin/dunnings', {
    billId: row.id, personId: row.personId || undefined,
    dunningType: 'NOTICE', dunningContent: '账单 ' + (row.billNo || '') + ' 催缴'
  })
  ElMessage.success(t('msg.dunningCreated'))
  load()
}

/** 批量催缴 */
/** 历史账单按新折算规则重算（仅未缴、自动生成，含二次确认） */
async function recalcBills() {
  saving.value = true
  try {
    const pre = await req.post('/fin/bills/recalculate', { dryRun: true })
    if (!pre.changed) {
      ElMessage.info(t('msg.noRecalc', { scanned: pre.scanned }))
      return
    }
    await ElMessageBox.confirm(
      '试算结果：扫描 ' + pre.scanned + ' 张，需重算 ' + pre.changed + ' 张，合计 '
        + pre.oldTotal + ' → ' + pre.newTotal
        + '。将按「逐月天数折算」改写应收/待缴金额（已收/已缴不动）。是否继续？',
      '确认重算历史账单', { type: 'warning' })
    const r = await req.post('/fin/bills/recalculate', { dryRun: false })
    ElMessage.success(t('msg.recalcDone', {
      scanned: r.scanned, changed: r.changed, old: r.oldTotal, new: r.newTotal
    }))
    load()
  } finally { saving.value = false }
}

async function batchDunning() {
  const picked = selected.value
  if (!picked.length) { ElMessage.warning(t('msg.selectBills')); return }
  await ElMessageBox.confirm('将向已选 ' + picked.length + ' 张账单发起催缴，是否继续？',
    '确认批量催缴', { type: 'warning' })
  let ok = 0
  for (const row of picked) {
    try {
      await req.post('/fin/dunnings', {
        billId: row.id, personId: row.personId || undefined,
        dunningType: 'NOTICE', dunningContent: '批量催缴'
      })
      ok++
    } catch (e) { /* 忽略单条失败 */ }
  }
  ElMessage.success(t('msg.batchDunning', { count: ok }))
  load()
}

async function scanOverdue() {
  await financeApi.scanOverdue()
  ElMessage.success(t('msg.overdueScanned')); load()
}

function explainLabel(label) {
  const map = {
    '收费项目': 'Fee Item', '计费方式': 'Billing Mode', '单价': 'Unit Price',
    '建筑面积': 'Building Area', '数量': 'Quantity', '费用区间': 'Service Period',
    '计费天数': 'Billing Days', '折算月数': 'Prorated Months',
    '计算公式': 'Formula', '应收金额': 'Amount', '计费说明': 'Billing Notes'
  }
  return getLocale() === 'en-US' ? (map[label] || label) : label
}

function explainValue(label, value) {
  if (getLocale() !== 'en-US' || value === null || value === undefined) return value
  let v = String(value)
  const mode = {
    '按抄表': 'Meter', '按面积': 'Area', '按人': 'Person', '按床位': 'Bed',
    '按套': 'Unit', '按夜': 'Night', '固定额': 'Fixed'
  }
  if (label === '计费方式') v = mode[v] || v
  const formulas = {
    '天数 × 单价': 'Days × Unit Price',
    '用量 × 单价（用量见抄表记录）': 'Usage × Unit Price (see meter readings)',
    '面积 × 单价 × 月数': 'Area × Unit Price × Months',
    '数量 × 单价 × 月数': 'Quantity × Unit Price × Months',
    '单价 × 月数': 'Unit Price × Months'
  }
  if (label === '计算公式') v = formulas[v] || v
  v = v.replace(/元\/方/g, 'CNY/m³').replace(/元\/㎡/g, 'CNY/m²')
    .replace(/元\/月/g, 'CNY/month').replace(/元\/人·月/g, 'CNY/person·month')
    .replace(/㎡/g, 'm²').replace(/ 天/g, ' days')
  return v
}

function localizeRemark(text) {
  if (!text || getLocale() !== 'en-US') return text
  return String(text)
    .replace(/抄表出账/g, 'Meter billing').replace(/月租金/g, 'Monthly rent')
    .replace(/物业费/g, 'Property fee').replace(/公摊分摊/g, 'Shared allocation')
}

const q0 = JSON.parse(JSON.stringify(q))
function resetQuery() {
  Object.assign(q, q0)
  reload()
}


/** 能耗分析 */
const energyVisible = ref(false)
const energyMonths = ref(6)
const energyMonths0 = ref([])
const energyBuildings = ref([])
const energyTop = ref([])

function openEnergy() {
  energyVisible.value = true
  loadEnergy()
}

async function loadEnergy() {
  try {
    const r = await financeApi.meterAnalytics(energyMonths.value)
    const months = (r && r.months) || []
    energyMonths0.value = months.map((m) => ({
      month: m.month, reading: m.readings, usage: m.usage, amount: m.amount
    }))
    energyBuildings.value = (r && r.byBuilding) || []
    energyTop.value = (r && r.topHouses) || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('msg.energyLoadFailed'))
  }
}

onMounted(() => { loadTrend(); load() })
</script>
