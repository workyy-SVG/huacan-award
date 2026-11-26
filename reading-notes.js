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
