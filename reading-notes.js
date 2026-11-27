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
if (keepsakeTitle) keepsakeTitle.insertAdjacentHTML('afterend', "<style>.track-guide{margin:12px 0 22px;padding:16px 20px;background:#f5edde;border-inline-start:4px solid #96503c;color:#344943}.track-guide p{margin:0 0 14px;line-height:1.7}.track-guide ol{display:flex;flex-wrap:wrap;gap:10px 18px;list-style:none;padding:0;margin:0 0 12px}.track-guide li{font-weight:600}.track-guide li+li:before{content:'→';margin-right:12px;color:#946444}.track-guide span{color:#894331}.track-guide small{color:#605644}@media(max-width:600px){.track-guide ol{display:grid}.track-guide li+li:before{content:none}}</style><div class=\"track-guide\"><p><b>寻踪卡是你的民俗收藏笔记。</b>把一个字在某地的生活故事留下，之后可以从收藏中回到原文。</p><ol aria-label=\"使用寻踪卡的三个步骤\"><li><span>①</span> 选一则地方记录</li><li><span>②</span> 保存寻踪记录</li><li><span>③</span> 打开已保存的寻踪卡回看</li></ol><small>收藏保存在当前浏览器中。</small></div>");
