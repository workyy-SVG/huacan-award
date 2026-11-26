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
