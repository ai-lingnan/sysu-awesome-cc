// 在已打开的公众号文章页里运行（浏览器工具的“执行 JavaScript”），返回一段精简 HTML。
// 把返回的字符串原样存成 page.html，再运行：wechat_save.py "<文章链接>" --from-html page.html
// 页面不是文章（例如“环境异常”验证页）时返回以 NO_JS_CONTENT 开头的说明。
(() => {
  const c = document.querySelector('#js_content');
  if (!c) return 'NO_JS_CONTENT: ' + document.title + ' | ' + (document.body.innerText || '').slice(0, 200);
  const k = c.cloneNode(true);
  // 视频播放器整块换成占位，避免把“播放、倍速、全屏”等按钮文字当正文
  k.querySelectorAll('.video_iframe, [data-mpvid], mpvideosnap, mp-common-videosnap, video, iframe').forEach(n => {
    const s = n.closest('section');
    const t = s && k.contains(s) && s.innerText.trim().length < 30 ? s : n;
    const ph = document.createElement('iframe');
    ph.setAttribute('data-src', 'video');
    t.replaceWith(ph);
  });
  k.querySelectorAll('script, style, svg').forEach(n => n.remove());
  k.querySelectorAll('*').forEach(n => [...n.attributes].forEach(a => {
    if (!['data-src', 'src', 'href'].includes(a.name) || a.value.startsWith('data:')) n.removeAttribute(a.name);
  }));
  const q = s => (document.querySelector(s)?.innerText || '').trim();
  const e = s => String(s || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  const v = name => e(window[name] || '');
  return '<html><head>'
    + `<meta property="og:title" content="${e(window.msg_title || q('#activity-name') || document.title)}">`
    + `<meta name="author" content="${e(q('#js_author_name'))}">`
    + `<script>var ct = "${v('ct')}"; var biz = "${v('biz')}"; var mid = "${v('mid')}"; var idx = "${v('idx')}"; var sn = "${v('sn')}";</script>`
    + `</head><body><span id="js_name">${e(window.nickname || q('#js_name'))}</span>`
    + `<em id="publish_time">${e(q('#publish_time'))}</em>`
    + `<div id="js_content">${k.innerHTML.replace(/<(\w+)>\s*<\/\1>/g, '')}</div></body></html>`;
})()
