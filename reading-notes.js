// The "年" archive assigns its sources anchor to the first story disclosure.
const notes = doc.querySelector('main > details[data-source-notes], main > details#sources');
if (notes) {
  const misplaced = doc.querySelector('.tile details#journey-sources');
  if (misplaced) {
    misplaced.removeAttribute('id');
    if (!notes.id) notes.id = 'journey-sources';
  }
  notes.classList.add('field-notes');
  for (const item of notes.querySelectorAll(':scope > ul > li')) {
    const link = item.querySelector('a');
    if (!link) continue;
    const parts = link.textContent.split('｜');
    if (parts.length > 1) {
      const place = doc.createElement('span');
      place.className = 'note-place';
      place.textContent = parts.shift();
      item.prepend(place);
      link.textContent = parts.join('｜');
    }
    const quote = link.nextSibling;
    if (quote?.nodeType === 3) quote.textContent = quote.textContent.replace(/^\s*[：:]\s*/, '');
  }
}
const description = doc.querySelector('#form .observation p');
if (description && !description.children.length) {
  const sentences = description.textContent.match(/^(.{1,45}?[。！？])(.+)$/u);
  if (sentences) {
    const lead = doc.createElement('strong');
    lead.className = 'glyph-reading';
    lead.textContent = sentences[1];
    description.replaceChildren(lead, doc.createTextNode(sentences[2]));
  }
}

const form = doc.getElementById('form');
const glyphCell = form?.querySelector('.glyph');
if (glyphCell) {
  const samples = doc.createElement('figure');
  samples.className = 'stroke-samples';
  form.append(samples);
  function drawSamples() {
    const glyph = glyphCell.textContent.trim();
    const paths = strokes[glyph]?.strokes;
    samples.hidden = !paths?.length;
    if (samples.hidden) return;
    samples.replaceChildren();
    const caption = doc.createElement('figcaption');
    caption.textContent = glyph + ' · ' + paths.length + ' 画';
    samples.append(caption);
    const svgNS = 'http://www.w3.org/2000/svg';
    for (const [label, count] of [['起笔',1],['行笔',Math.ceil(paths.length/2)],['成字',paths.length]]) {
      const stage = doc.createElement('div');
      const svg = doc.createElementNS(svgNS,'svg');
      svg.setAttribute('viewBox','-32 0 1088 1088');
      svg.setAttribute('aria-hidden','true');
      paths.forEach((outline,i) => {
        const path = doc.createElementNS(svgNS,'path');
        path.setAttribute('d',outline);
        path.setAttribute('transform','translate(0 924) scale(1 -1)');
        path.setAttribute('fill',i>=count?'#d9d1bd':i===count-1?'#963f2e':'#314e4a');
        svg.append(path);
      });
      const text = doc.createElement('span');
      text.textContent = label;
      stage.append(svg,text);
      samples.append(stage);
    }
  }
  drawSamples();
  new MutationObserver(drawSamples).observe(glyphCell,{subtree:true,characterData:true,childList:true});
}

const keepsakeTitle = doc.querySelector('#keepsake > h2');
if (keepsakeTitle) keepsakeTitle.insertAdjacentHTML('afterend', "<style>.track-guide{margin:16px 0 26px;padding:clamp(14px,3vw,30px);background:#fbf6e9;color:#304642;border-block:3px double #bcaa87}.track-guide>p{margin:0 0 16px;font-size:1.12rem;line-height:1.7}.track-guide ol{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;list-style:none;margin:0;padding:0}.track-guide li{position:relative;display:grid;justify-items:center;align-content:start;text-align:center;gap:4px}.track-guide li+li:before{content:'→';position:absolute;left:-20px;top:25%;font-size:24px;color:#946444}.track-guide svg{height:76px;width:110px}.track-guide strong{color:#783f31;font-size:1.05rem}.track-guide li span,.track-guide small{font-size:.95rem;line-height:1.6}.track-guide small{display:block;margin-top:14px;color:#605644}@media(max-width:560px){.track-guide ol{grid-template-columns:1fr;gap:12px}.track-guide li{grid-template-columns:70px 1fr;justify-items:start;align-items:center;text-align:left;column-gap:12px}.track-guide svg{grid-row:span 2;width:68px;height:56px}.track-guide li+li:before{content:none}}</style><div class=\"track-guide\"><p><b>寻踪卡是你的民俗收藏笔记。</b> 以金门年夜饭为例，看看一则故事怎样留下来。</p><ol><li><svg aria-hidden=\"true\" viewBox=\"0 0 108 72\" fill=\"none\" stroke=\"#614e38\" stroke-width=\"2.4\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 36h56c-3 17-12 23-28 23S20 53 16 36Z\" fill=\"#ead6ad\"/><path d=\"M17 36q26 9 55 0M35 62h19M69 32 89 8m-14 26L96 12\"/><path d=\"M30 25q-6-5 1-11m12 12q-6-5 1-11\" stroke=\"#ab6850\"/></svg><strong>选一则故事</strong><span>例如「年」字里的金门除夕留席。</span></li><li><svg aria-hidden=\"true\" viewBox=\"0 0 108 72\" fill=\"none\" stroke=\"#614e38\" stroke-width=\"2.4\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><rect x=\"17\" y=\"10\" width=\"70\" height=\"50\" rx=\"4\" fill=\"#fff4da\"/><path d=\"M27 24h28m-28 9h36m-36 9h24\"/><path d=\"M64 8h14v22l-7-5-7 5Z\" fill=\"#9b5139\"/><circle cx=\"82\" cy=\"52\" r=\"12\" fill=\"#456658\"/><path d=\"m76 52 4 4 8-9\" stroke=\"white\"/></svg><strong>保存寻踪记录</strong><span>把汉字、地点和故事摘要收进自己的卡片。</span></li><li><svg aria-hidden=\"true\" viewBox=\"0 0 108 72\" fill=\"none\" stroke=\"#614e38\" stroke-width=\"2.4\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 17q20-5 38 4 17-9 38-4v40q-22-4-38 5-16-9-38-5Z\" fill=\"#f8ead1\"/><path d=\"M51 21v41m-31-35 21 3m-21 6 21 3m17-9 21-3m-21 12 15-2\"/><path d=\"M72 15h8v17l-4-3-4 3Z\" fill=\"#9b5139\"/></svg><strong>翻开收藏</strong><span>在「已保存的寻踪卡」里点「回到故事」。</span></li></ol><small>收藏保存在当前浏览器中。</small></div>");
