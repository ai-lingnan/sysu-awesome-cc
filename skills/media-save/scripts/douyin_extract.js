// 在浏览器里打开抖音分享链接、页面渲染后运行，返回一段 JSON 字符串：
//   status   ok / no_video / verify / login / note
//   aweme_id、page_url、author、title、published、duration_s、media_urls（按优先级排列）
// 把 media_urls 等字段交给 douyin_save.py --media-url ... 下载。最多等 15 秒让视频地址出现。
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const href = location.href;
  const idMatch = href.match(/\/(?:video|note|share\/video|share\/note)\/(\d{8,})/) || href.match(/modal_id=(\d{8,})/);
  const id = idMatch ? idMatch[1] : '';
  const out = { status: 'no_video', aweme_id: id, page_url: href };
  if (/\/(share\/)?note\//.test(href)) { out.status = 'note'; return JSON.stringify(out); }

  // 只认带本作品 ID（__vid=<作品ID>）的地址，避免拿到加载动画或推荐流里的下一条
  const mine = u => u && /^https?:/.test(u) && (!id || u.includes('__vid=' + id));
  const pick = () => {
    for (const v of document.querySelectorAll('video')) {
      const cands = [v.currentSrc, v.src, ...[...v.querySelectorAll('source')].map(s => s.src)].filter(mine);
      if (cands.length && isFinite(v.duration) && v.duration > 0) {
        out.duration_s = Math.round(v.duration * 100) / 100;
        // 直连 CDN 的 MP4 排前面，官方 /aweme/v1/play/ 跳转地址排后面
        return [...new Set(cands)].sort((a, b) => (/douyinvod\.com/.test(b) - /douyinvod\.com/.test(a)));
      }
    }
    return [];
  };
  const ready = () => document.querySelector('meta[name="lark:url:video_title"]') || document.querySelector('[data-e2e="detail-video-info"]');
  let urls = [];
  for (let i = 0; i < 30 && !(urls.length && ready()); i++) { urls = pick(); if (!(urls.length && ready())) await sleep(500); }
  // <video> 只给 blob: 地址时，用页面加载过的媒体请求
  if (!urls.length && id) {
    urls = [...new Set(performance.getEntriesByType('resource').map(e => e.name)
      .filter(u => /douyinvod\.com/.test(u) && u.includes('__vid=' + id)))];
    if (urls.length) out.media_from = 'network';
  }

  const text = document.body ? document.body.innerText : '';
  if (!urls.length) {
    if (/验证码|安全验证|拖动滑块|请完成验证|captcha/i.test(text) || document.querySelector('iframe[src*="verify"], #captcha_container')) out.status = 'verify';
    else if (/登录后|扫码登录|请先登录/.test(text) && !document.querySelector('video')) out.status = 'login';
    return JSON.stringify(out);
  }

  let author = '';
  for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      const j = JSON.parse(s.textContent);
      const item = (j.itemListElement || []).find(x => x.position === 2);
      if (item && item.name) { author = item.name; break; }
    } catch (e) { /* 忽略 */ }
  }
  const desc = document.querySelector('meta[name="description"]')?.content || '';
  if (!author) { const m = desc.match(/ - (.+?)于\d{8}发布在抖音/); if (m) author = m[1]; }
  if (!author) author = (document.querySelector('[data-e2e="user-info"] a[href*="/user/"]')?.innerText || '').split('\n')[0].trim();
  const t = document.querySelector('meta[name="lark:url:video_title"]')?.content || document.title || '';
  const pub = (document.querySelector('[data-e2e="detail-video-publish-time"]')?.innerText || '').replace(/^发布时间[:：]\s*/, '').trim();
  Object.assign(out, { status: 'ok', author, title: t.replace(/\s*-\s*抖音\s*$/, '').trim(), published: pub, media_urls: urls.slice(0, 4), user_agent: navigator.userAgent });
  return JSON.stringify(out);
})()
