// Screenshot each web UI section from the mock: node shoot.js <url> <outdir> [theme]
const { chromium } = require('playwright');
const [url = 'http://127.0.0.1:8080', out = '.', theme = ''] = process.argv.slice(2);
const tabs = ['dash', 'ports', 'vlan', 'lag', 'stp', 'mirror', 'system'];
(async () => {
  const b = await chromium.launch();
  for (const [tag, vp] of [['desk', { width: 1366, height: 860 }], ['phone', { width: 390, height: 844 }]]) {
    const p = await b.newPage({ viewport: vp });
    p.on('pageerror', e => console.error('pageerror', e.message));
    await p.goto(url + '/index.html');
    if (theme) await p.evaluate(t => { try { localStorage.setItem('rtl_theme', t) } catch (e) {} }, theme);
    for (const t of (tag === 'phone' ? ['dash'] : tabs)) {
      await p.goto(url + '/index.html#' + t); await p.reload();
      await p.waitForTimeout(1800);
      await p.screenshot({ path: `${out}/${tag}-${t}.png`, fullPage: tag === 'desk' });
    }
    await p.close();
  }
  await b.close();
})();
