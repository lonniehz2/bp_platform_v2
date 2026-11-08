import io
p=r'src\pages\Projects.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Pager from '../components/Pager.vue'\nimport { can } from '../permissions'","import Pager from '../components/Pager.vue'")
s=s.replace('''        </table>
      </div>
    </div>
  </div>
</template>''','''        </table>
      </div>
      <Pager :total="projects.length" :page="page" @update:page="page = $event" />
    </div>
  </div>
</template>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('projects fixed')
