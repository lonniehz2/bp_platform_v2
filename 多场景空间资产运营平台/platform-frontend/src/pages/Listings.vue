<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { canAction } from '../permissions'

const project = ref(null)
const listings = ref([])
const bookings = ref([])
const orders = ref([])
const houses = ref([])
const persons = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ houseId: '', title: '', description: '', monthlyRent: 1200, depositAmount: 1200, coverUrl: '' })
const booking = reactive({ listingId: '', personId: '', contactPhone: '', remark: '' })
const bookingOpen = ref(false)
const detail = ref(null)

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const [l, b, h, p, o] = await Promise.all([
      api.listings(project.value.id), api.bookings(project.value.id),
      api.houses(project.value.id), api.persons().catch(() => []),
      api.listingOrders(project.value.id).catch(() => [])
    ])
    listings.value = l; bookings.value = b; houses.value = h; persons.value = p; orders.value = o
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!booking.personId && p.length) booking.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.houseId || !form.title.trim()) throw new Error('请选择房屋并填写标题')
    await api.createListing({ projectId: project.value.id, houseId: form.houseId, title: form.title,
      description: form.description, monthlyRent: Number(form.monthlyRent), depositAmount: Number(form.depositAmount),
      coverUrl: form.coverUrl })
    form.title = ''; form.description = ''; form.coverUrl = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function action(l, type) {
  busy.value = true; error.value = ''
  try {
    if (type === 'publish') await api.publishListing(l.id)
    if (type === 'offline') await api.offlineListing(l.id)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function openDetail(l) {
  detail.value = l
}

function openBooking(l) {
  booking.listingId = l.id
  bookingOpen.value = true
  booking.contactPhone = ''
  booking.remark = ''
}

async function submitBooking() {
  busy.value = true; error.value = ''
  try {
    await api.bookListing(booking.listingId, { personId: booking.personId, contactPhone: booking.contactPhone, remark: booking.remark })
    bookingOpen.value = false
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function updateBooking(b, type) {
  busy.value = true; error.value = ''
  try {
    if (type === 'confirm') await api.confirmBooking(b.id)
    if (type === 'cancel') await api.cancelBooking(b.id)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>房源展示</h2><p>{{ project.orgName }} · 发布房源、看房预约</p></div><span class="pill">LISTING</span></div>
        <div class="row">
          <div class="field"><label>房屋</label><select v-model="form.houseId"><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select></div>
          <div class="field" style="flex:2"><label>标题</label><input v-model="form.title" placeholder="如 101室精装一居" /></div>
          <div class="field"><label>月租金</label><input v-model.number="form.monthlyRent" type="number" /></div>
          <div class="field"><label>押金</label><input v-model.number="form.depositAmount" type="number" /></div>
          <div class="field" style="flex:2"><label>封面图 URL</label><input v-model="form.coverUrl" placeholder="https://..." /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="canAction('listing:manage', 'asset')" class="primary" :disabled="busy" @click="create">创建展示</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>展示列表</h2><span class="small muted">{{ listings.length }} 条</span></div>
        <div v-if="!listings.length" class="empty">暂无展示</div>
        <div class="table-wrap" v-else>
          <table><thead><tr><th>封面</th><th>房屋</th><th>标题</th><th>月租金</th><th>押金</th><th>状态</th><th>预约</th><th>操作</th></tr></thead>
            <tbody><tr v-for="l in listings" :key="l.id">
              <td><img v-if="l.coverUrl" :src="l.coverUrl" alt="" style="width:64px;height:44px;object-fit:cover;border-radius:6px" /><span v-else class="small muted">无图</span></td>
              <td>{{ l.houseCode }} · {{ l.houseName }}</td><td><button class="link" @click="openDetail(l)">{{ l.title }}</button></td>
              <td>¥{{ money(l.monthlyRent) }}</td><td>¥{{ money(l.depositAmount) }}</td>
              <td><span class="badge" :class="l.listingStatus === 'PUBLISHED' ? 'green' : 'orange'">{{ l.listingStatus }}</span></td>
              <td>{{ l.bookingCount }}</td>
              <td class="row">
                <button v-if="canAction('listing:manage', 'asset') && l.listingStatus !== 'PUBLISHED'" class="sm" @click="action(l, 'publish')">发布</button>
                <button v-if="canAction('listing:manage', 'asset') && l.listingStatus === 'PUBLISHED'" class="sm" @click="action(l, 'offline')">下线</button>
                <button v-if="canAction('listing:book', 'asset') && l.listingStatus === 'PUBLISHED'" class="sm primary" @click="openBooking(l)">预约看房</button>
              </td>
            </tr></tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>看房预约</h2><span class="small muted">{{ bookings.length }} 条</span></div>
        <div v-if="!bookings.length" class="empty">暂无预约</div>
        <div class="table-wrap" v-else>
          <table><thead><tr><th>预约号</th><th>房源</th><th>预约人</th><th>电话</th><th>状态</th><th>操作</th></tr></thead>
            <tbody><tr v-for="b in bookings" :key="b.id">
              <td class="mono">{{ b.bookingNo }}</td><td>{{ b.title }}</td><td>{{ b.personName }}</td><td>{{ b.contactPhone || '-' }}</td>
              <td><span class="badge" :class="b.bookingStatus === 'CONFIRMED' ? 'green' : 'orange'">{{ b.bookingStatus }}</span></td>
              <td class="row">
                <button v-if="b.bookingStatus === 'PENDING'" class="sm" @click="updateBooking(b, 'confirm')">确认</button>
                <button v-if="b.bookingStatus === 'PENDING'" class="sm danger" @click="updateBooking(b, 'cancel')">取消</button>
              </td>
            </tr></tbody>
          </table>
        </div>
      </div>
    </template>

    <div class="panel">
      <div class="panel-head"><h2>预约订单</h2><span class="small muted">{{ orders.length }} 条</span></div>
      <div v-if="!orders.length" class="empty">暂无订单</div>
      <div class="table-wrap" v-else>
        <table><thead><tr><th>订单号</th><th>房源</th><th>承租人</th><th>月租金</th><th>押金</th><th>状态</th></tr></thead>
          <tbody><tr v-for="o in orders" :key="o.id">
            <td class="mono">{{ o.orderNo }}</td><td>{{ o.title }}</td><td>{{ o.personName }}</td>
            <td>¥{{ money(o.rentAmount) }}</td><td>¥{{ money(o.depositAmount) }}</td>
            <td><span class="badge green">{{ o.orderStatus }}</span></td>
          </tr></tbody>
        </table>
      </div>
    </div>

    <div v-if="detail" class="modal-mask" @click.self="detail = null">
      <div class="modal" style="max-width:680px">
        <div class="panel-head"><h2>{{ detail.title }}</h2><button class="sm" @click="detail = null">关闭</button></div>
        <img v-if="detail.coverUrl" :src="detail.coverUrl" alt="" style="width:100%;max-height:280px;object-fit:cover;border-radius:8px" />
        <p class="muted">{{ detail.description || '暂无描述' }}</p>
        <div class="row"><span>月租金 ¥{{ money(detail.monthlyRent) }}</span><span>押金 ¥{{ money(detail.depositAmount) }}</span><span class="badge blue">{{ detail.listingStatus }}</span></div>
        <div class="row" style="justify-content:flex-end"><button v-if="canAction('listing:book', 'asset') && detail.listingStatus === 'PUBLISHED'" class="primary" @click="openBooking(detail); detail = null">预约看房</button></div>
      </div>
    </div>

    <div v-if="bookingOpen" class="modal-mask" @click.self="bookingOpen = false">
      <div class="modal">
        <div class="panel-head"><h2>预约看房</h2><button class="sm" @click="bookingOpen = false">关闭</button></div>
        <div class="field"><label>预约人</label><select v-model="booking.personId"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}（{{ p.personCode }}）</option></select></div>
        <div class="field"><label>联系电话</label><input v-model="booking.contactPhone" /></div>
        <div class="field"><label>备注</label><input v-model="booking.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="submitBooking">提交预约</button></div>
      </div>
    </div>
  </div>
</template>
