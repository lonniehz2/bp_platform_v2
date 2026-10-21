(() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href, title: document.title };
  out.inputs = Array.from(document.querySelectorAll('input')).map((i, k) => ({
    idx: k, type: i.type, name: i.name || '', ph: i.placeholder || '',
    cls: (i.className || '').toString().slice(0, 60),
    val: (i.value || '').slice(0, 20),
    visible: !!(i.offsetWidth || i.offsetHeight),
  }));
  out.buttons = Array.from(document.querySelectorAll('button')).map((b, k) => ({
    idx: k, text: norm(b.innerText).slice(0, 20), cls: (b.className || '').toString().slice(0, 60),
  }));
  // 滑块验证码线索
  out.captcha = {
    hasSlider: !!document.querySelector('[class*="slider"],[class*="captcha"],[class*="verify"]'),
    sliderCls: Array.from(document.querySelectorAll('[class*="slider"],[class*="captcha"],[class*="verify"]'))
      .slice(0, 8).map(e => (e.className || '').toString().slice(0, 70)),
    canvasCount: document.querySelectorAll('canvas').length,
  };
  return JSON.stringify(out, null, 1);
})()
