<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { canAction } from '../permissions'
import { confirmAction } from '../confirm'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
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
const editingListing = ref(null)
const listingEditForm = reactive({ title: '', description: '', monthlyRent: 0, depositAmount: 0, coverUrl: '' })
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
    if (!form.houseId || !form.title.trim()) throw new Error(t('listings.required'))
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


function openListingEdit(l) {
  editingListing.value = l
  Object.assign(listingEditForm, {
    title: l.title || '', description: l.description || '', monthlyRent: l.monthlyRent || 0,
    depositAmount: l.depositAmount || 0, coverUrl: l.coverUrl || ''
  })
}

async function saveListingEdit() {
  busy.value = true; error.value = ''
  try {
    if (!listingEditForm.title.trim()) throw new Error(t('listings.titleRequired'))
    await api.updateListing(editingListing.value.id, { ...listingEditForm })
    editingListing.value = null
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


async function convertOrder(o) {
  busy.value = true; error.value = ''
  try {
    await api.contractFromOrder(o.id)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function payOrder(o) {
  if (!await confirmAction({ title: t('listings.payTitle'), message: t('listings.payMessage', { amount: money(Number(o.rentAmount) + Number(o.depositAmount)) }), confirmText: t('listings.pay') })) return
  busy.value = true; error.value = ''
  try {
    await api.payListingOrder(o.id, { paymentMethod: 'ONLINE' })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function cancelOrder(o) {
  if (!await confirmAction({ title: t('listings.cancelTitle'), message: t('listings.cancelMessage'), confirmText: t('listings.cancelConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try {
    await api.cancelListingOrder(o.id)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">{{ t('listings.createProject') }}</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>{{ t('listings.title') }}</h2><p>{{ project.orgName }} · {{ t('listings.subtitle') }}</p></div><span class="pill">LISTING</span></div>
        <div class="row">
          <div class="field"><label>{{ t('listings.house') }}</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('listings.house')" /></div>
          <div class="field" style="flex:2"><label>{{ t('listings.titleCol') }}</label><input v-model="form.title" :placeholder="t('listings.titleCol')" /></div>
          <div class="field"><label>{{ t('listings.monthlyRent') }}</label><input v-model.number="form.monthlyRent" type="number" /></div>
          <div class="field"><label>{{ t('listings.deposit') }}</label><input v-model.number="form.depositAmount" type="number" /></div>
          <div class="field" style="flex:2"><label>{{ t('listings.cover') }}</label><input v-model="form.coverUrl" :placeholder="t('listings.coverUrl')" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="canAction('listing:manage', 'asset')" class="primary" :disabled="busy" @click="create">{{ t('listings.add') }}</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('listings.list') }}</h2><span class="small muted">{{ listings.length }} {{ t('listings.count') }}</span></div>
        <div v-if="!listings.length" class="empty">{{ t('listings.empty') }}</div>
        <div class="table-wrap" v-else>
          <table><thead><tr><th>{{ t('listings.cover') }}</th><th>{{ t('listings.house') }}</th><th>{{ t('listings.titleCol') }}</th><th>{{ t('listings.monthlyRent') }}</th><th>{{ t('listings.deposit') }}</th><th>{{ t('listings.status') }}</th><th>{{ t('listings.bookings') }}</th><th>{{ t('listings.action') }}</th></tr></thead>
            <tbody><tr v-for="l in listings" :key="l.id">
              <td><img v-if="l.coverUrl" :src="l.coverUrl" alt="" style="width:64px;height:44px;object-fit:cover;border-radius:6px" /><span v-else class="small muted">{{ t('listings.noImage') }}</span></td>
              <td>{{ l.houseCode }} · {{ l.houseName }}</td><td><button class="link" @click="openDetail(l)">{{ l.title }}</button></td>
              <td>¥{{ money(l.monthlyRent) }}</td><td>¥{{ money(l.depositAmount) }}</td>
              <td><span class="badge" :class="l.listingStatus === 'PUBLISHED' ? 'green' : 'orange'">{{ l.listingStatus }}</span></td>
              <td>{{ l.bookingCount }}</td>
              <td class="row">
                <button v-if="canAction('listing:manage', 'asset')" class="sm" @click="openListingEdit(l)">{{ t('listings.edit') }}</button>
                <button v-if="canAction('listing:manage', 'asset') && l.listingStatus !== 'PUBLISHED'" class="sm" @click="action(l, 'publish')">{{ t('listings.publish') }}</button>
                <button v-if="canAction('listing:manage', 'asset') && l.listingStatus === 'PUBLISHED'" class="sm" @click="action(l, 'offline')">{{ t('listings.offline') }}</button>
                <button v-if="canAction('listing:book', 'asset') && l.listingStatus === 'PUBLISHED'" class="sm primary" @click="openBooking(l)">{{ t('listings.book') }}</button>
              </td>
            </tr></tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('listings.bookings') }}</h2><span class="small muted">{{ bookings.length }} {{ t('listings.count') }}</span></div>
        <div v-if="!bookings.length" class="empty">{{ t('listings.noBookings') }}</div>
        <div class="table-wrap" v-else>
          <table><thead><tr><th>{{ t('listings.bookingNo') }}</th><th>{{ t('listings.listing') }}</th><th>{{ t('listings.person') }}</th><th>{{ t('listings.phone') }}</th><th>{{ t('listings.status') }}</th><th>{{ t('listings.action') }}</th></tr></thead>
            <tbody><tr v-for="b in bookings" :key="b.id">
              <td class="mono">{{ b.bookingNo }}</td><td>{{ b.title }}</td><td>{{ b.personName }}</td><td>{{ b.contactPhone || '-' }}</td>
              <td><span class="badge" :class="b.bookingStatus === 'CONFIRMED' ? 'green' : 'orange'">{{ b.bookingStatus }}</span></td>
              <td class="row">
                <button v-if="b.bookingStatus === 'PENDING'" class="sm" @click="updateBooking(b, 'confirm')">{{ t('listings.confirm') }}</button>
                <button v-if="b.bookingStatus === 'PENDING'" class="sm danger" @click="updateBooking(b, 'cancel')">{{ t('listings.cancel') }}</button>
              </td>
            </tr></tbody>
          </table>
        </div>
      </div>
    </template>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('listings.orders') }}</h2><span class="small muted">{{ orders.length }} {{ t('listings.count') }}</span></div>
      <div v-if="!orders.length" class="empty">{{ t('listings.noOrders') }}</div>
      <div class="table-wrap" v-else>
        <table><thead><tr><th>{{ t('listings.orderNo') }}</th><th>{{ t('listings.listing') }}</th><th>{{ t('listings.tenant') }}</th><th>{{ t('listings.monthlyRent') }}</th><th>{{ t('listings.deposit') }}</th><th>{{ t('listings.status') }}</th><th>{{ t('listings.payment') }}</th><th>{{ t('listings.action') }}</th></tr></thead>
          <tbody><tr v-for="o in orders" :key="o.id">
            <td class="mono">{{ o.orderNo }}</td><td>{{ o.title }}</td><td>{{ o.personName }}</td>
            <td>¥{{ money(o.rentAmount) }}</td><td>¥{{ money(o.depositAmount) }}</td>
            <td><span class="badge" :class="o.orderStatus === 'CONTRACTED' ? 'green' : 'orange'">{{ o.orderStatus }}</span></td>
            <td><span class="badge" :class="o.paymentStatus === 'PAID' ? 'green' : 'red'">{{ o.paymentStatus }}</span></td>
            <td class="row">
              <button v-if="canAction('listing:manage', 'asset') && o.paymentStatus !== 'PAID' && ['CONFIRMED','CONTRACTED'].includes(o.orderStatus)" class="sm primary" :disabled="busy" @click="payOrder(o)">{{ t('listings.payment') }}</button>
              <button v-if="canAction('listing:manage', 'asset') && o.orderStatus === 'CONFIRMED'" class="sm" :disabled="busy" @click="convertOrder(o)">{{ t('listings.contract') }}</button>
              <button v-if="canAction('listing:manage', 'asset') && o.orderStatus === 'CONFIRMED' && o.paymentStatus !== 'PAID'" class="sm danger" :disabled="busy" @click="cancelOrder(o)">{{ t('listings.cancel') }}</button>
            </td>
          </tr></tbody>
        </table>
      </div>
    </div>

    <div v-if="detail" class="modal-mask" @click.self="detail = null">
      <div class="modal" style="max-width:680px">
        <div class="panel-head"><h2>{{ detail.title }}</h2><button class="sm" @click="detail = null">{{ t('listings.close') }}</button></div>
        <img v-if="detail.coverUrl" :src="detail.coverUrl" alt="" style="width:100%;max-height:280px;object-fit:cover;border-radius:8px" />
        <p class="muted">{{ detail.description || t('listings.noDesc') }}</p>
        <div class="row"><span>{{ t('listings.monthlyRent') }} ¥{{ money(detail.monthlyRent) }}</span><span>{{ t('listings.deposit') }} ¥{{ money(detail.depositAmount) }}</span><span class="badge blue">{{ detail.listingStatus }}</span></div>
        <div class="row" style="justify-content:flex-end"><button v-if="canAction('listing:book', 'asset') && detail.listingStatus === 'PUBLISHED'" class="primary" @click="openBooking(detail); detail = null">{{ t('listings.book') }}</button></div>
      </div>
    </div>

    <div v-if="bookingOpen" class="modal-mask" @click.self="bookingOpen = false">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('listings.book') }}</h2><button class="sm" @click="bookingOpen = false">{{ t('listings.close') }}</button></div>
        <div class="field"><label>{{ t('listings.person') }}</label><SearchSelect v-model="booking.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('listings.person')" /></div>
        <div class="field"><label>{{ t('listings.contact') }}</label><input v-model="booking.contactPhone" /></div>
        <div class="field"><label>{{ t('listings.remark') }}</label><input v-model="booking.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="submitBooking">{{ t('listings.submit') }}</button></div>
      </div>
    </div>

    <div v-if="editingListing" class="modal-mask" @click.self="editingListing = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('listings.editTitle') }}</h2><button class="sm" @click="editingListing = null">{{ t('listings.close') }}</button></div>
        <div class="field"><label>{{ t('listings.house') }}</label><div class="mono">{{ editingListing.houseCode }} · {{ editingListing.houseName }}</div></div>
        <div class="field"><label>{{ t('listings.titleCol') }}</label><input v-model="listingEditForm.title" /></div>
        <div class="field"><label>{{ t('listings.desc') }}</label><input v-model="listingEditForm.description" /></div>
        <div class="field"><label>{{ t('listings.monthlyRent') }}</label><input v-model.number="listingEditForm.monthlyRent" type="number" /></div>
        <div class="field"><label>{{ t('listings.deposit') }}</label><input v-model.number="listingEditForm.depositAmount" type="number" /></div>
        <div class="field"><label>{{ t('listings.coverUrl') }}</label><input v-model="listingEditForm.coverUrl" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveListingEdit">{{ t('listings.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
