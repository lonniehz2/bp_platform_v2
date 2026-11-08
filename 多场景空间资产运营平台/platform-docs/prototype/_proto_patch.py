import io
p='standard-pages.html'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''function go(page){
  state.page = page;''','''function go(page){
  closeModal();
  state.page = page;''')
s=s.replace('''      <button class="btn primary" data-roles="审核员,场景管理员" onclick="toast('审核通过，可转轮候');closeModal()">通过</button>''','''      <button class="btn primary" data-roles="审核员,场景管理员" onclick="approveApp()">通过</button>''')
s=s.replace('''  `);
  applyRole();
}

function noApproval(){''','''  `);
  window.__currentAppNo = no;
  applyRole();
}

function approveApp(){
  const no = window.__currentAppNo;
  const rows = [...document.querySelectorAll('#page-applications tbody tr')];
  const row = rows.find(r => r.innerText.includes(no));
  if (row) row.cells[4].innerHTML = '<span class="badge green">已通过</span>';
  closeModal();
  toast('审核通过，可转轮候');
}

function noApproval(){''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('prototype patched')
