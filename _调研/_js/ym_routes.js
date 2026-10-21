(() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href, checks: {} };

  // 1) 框架判定
  out.checks.vue2 = !!document.querySelector('#app') && !!window.Vue;
  const app = document.querySelector('#app');
  out.checks.hasApp = !!app;
  out.checks.appVue = app ? Object.keys(app).filter(k => k.startsWith('__vue')).join(',') : null;
  out.checks.rootVue = !!(app && app.__vue__);

  // 2) 从 Vue 根实例拿 $router
  try {
    if (app && app.__vue__) {
      const vm = app.__vue__;
      const r = vm.$router;
      if (r && r.options && r.options.routes) {
        const flat = [];
        const walk = (rs, prefix) => {
          (rs || []).forEach(x => {
            const p = (prefix ? prefix + '/' : '') + (x.path || '');
            if (x.name || x.path) flat.push({ path: p, name: x.name || null, title: x.meta && (x.meta.title || x.meta.name) || null, comp: x.component ? (x.component.name || 'anon') : null });
            if (x.children) walk(x.children, p);
          });
        };
        walk(r.options.routes, '');
        out.routeCount = flat.length;
        out.routes = flat.slice(0, 400);
      } else {
        out.checks.routerErr = 'no routes on $router';
      }
      // 菜单数据常在 vuex 或组件 data
      try {
        const st = vm.$store;
        if (st) {
          out.storeKeys = Object.keys(st.state || {});
          const perm = st.state && (st.state.user || st.state.permission || st.state.menu);
          if (perm) out.storeUser = JSON.stringify(perm).slice(0, 1500);
        }
      } catch (e) { out.checks.storeErr = String(e).slice(0, 120); }
    }
  } catch (e) { out.checks.vueErr = String(e).slice(0, 200); }

  // 3) 兜底：扫描 window 上的路由/菜单
  try {
    const keys = Object.keys(window).filter(k => /route|menu|permission|store|app/i.test(k)).slice(0, 30);
    out.windowKeys = keys;
  } catch (e) {}

  return JSON.stringify(out, null, 1);
})()
