import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import PlatformInfo from './pages/PlatformInfo.vue'","import PlatformInfo from './pages/PlatformInfo.vue'\nimport Sys from './pages/Sys.vue'\nimport Translations from './pages/Translations.vue'")
s=s.replace("{ path: '/sys', component: Menus, meta: { title: '系统支撑' } }","{ path: '/sys', component: Sys, meta: { title: '系统支撑' } }")
s=s.replace("{ path: '/translations', component: Help, meta: { title: '业务数据翻译' } }","{ path: '/translations', component: Translations, meta: { title: '业务数据翻译' } }")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\pages\Qualification.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { onMounted, reactive, ref, watch } from 'vue'","import { onMounted, reactive, ref, watch } from 'vue'\nimport { useRoute } from 'vue-router'")
s=s.replace("const project = ref(null)","const route = useRoute()\nconst pageTitle = route.path === '/annual-reviews' ? '年审复核' : '资格复核'\nconst project = ref(null)")
s=s.replace('<h2>资格复核</h2>','<h2>{{ pageTitle }}</h2>')
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\pages\Billing.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { computed, onMounted, reactive, ref } from 'vue'","import { computed, onMounted, reactive, ref } from 'vue'\nimport { useRoute } from 'vue-router'")
s=s.replace("const project = ref(null)","const route = useRoute()\nconst pageTitle = route.path === '/bills' ? '账单与缴费' : '收款'\nconst project = ref(null)")
s=s.replace('<h2>收款</h2>','<h2>{{ pageTitle }}</h2>')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('routes/titles')
