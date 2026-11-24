const cases = JSON.parse(document.querySelector('#records').textContent);
const dialog = document.querySelector('dialog');
const selection = document.querySelector('#place');
let activeRecord;
const config = typeof embedded === 'undefined' ? {} : embedded;
if (cases.some(record => record.id === config.selected)) selection.value = config.selected;

function imageFor(record) {
  return config.images?.[record.id] || record.image;
}

function updateCard() {
  const record = cases.find(item => item.id === selection.value);
  document.querySelector('#keepsake-image').src = imageFor(record);
  document.querySelector('#selected-title').textContent = record.place + '｜' + record.short;
  document.querySelector('#selected-detail').textContent = record.recorded_action;
}

document.querySelectorAll('[data-record]').forEach(button => {
  button.addEventListener('click', () => {
    activeRecord = cases.find(item => item.id === button.dataset.record);
    selection.value = activeRecord.id;
    updateCard();
    document.querySelector('#record-title').textContent = activeRecord.place + '｜' + activeRecord.title;
    document.querySelector('#record-image').src = imageFor(activeRecord);
    document.querySelector('#record-body').textContent = activeRecord.body;
    document.querySelector('#record-quote').textContent = activeRecord.source_quote || '';
    document.querySelector('#record-source').href = activeRecord.source_url;
    dialog.showModal();
  });
});

document.querySelector('#keep').addEventListener('click', () => {
  selection.value = activeRecord.id;
  updateCard();
  dialog.close();
  location.hash = 'keepsake';
});
selection.addEventListener('change', updateCard);
document.querySelector('#save').addEventListener('click', () => {
  const record = cases.find(item => item.id === selection.value);
  if (typeof parent.ziliSaveKeepsake === 'function') {
    const saved = parent.ziliSaveKeepsake(record, config.images?.[record.id] || record.image);
    document.getElementById('keepsake-status').textContent =
      (saved ? '已保存 · ' : '已保存到本次浏览 · ') + record.place;
    document.getElementById('keepsake-collection-link').hidden = false;
    return;
  }
  const body = ['字里寻踪 · ' + document.body.dataset.character, record.place + '｜' + record.title, record.recorded_action,
    '出处：' + record.source_title, record.source_url].join('\n');
  const url = URL.createObjectURL(new Blob([body], {type: 'text/plain;charset=utf-8'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = '我的寻踪卡-' + document.body.dataset.character + '.txt';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
});
updateCard();
