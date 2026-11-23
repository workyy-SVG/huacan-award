(() => {
  const dialog = document.getElementById('glyph-dialog');
  if (!dialog) return;
  const forms = [...dialog.querySelectorAll('.glyph-large')].map(node => node.textContent.trim());
  if (!forms.length) return;
  const section = document.createElement('section');
  section.className = 'stroke-preview';
  section.innerHTML = '<div class="stroke-controls"><label hidden>字形 <select aria-label="选择笔顺字形"></select></label><button class="outline" type="button">播放笔顺</button></div><div class="stroke-board" hidden></div><p class="stroke-status" role="status"></p><small>笔顺示范：Hanzi Writer / Make Me a Hanzi</small>';
  dialog.insertBefore(section, dialog.querySelector('a'));
  const button = section.querySelector('button');
  const select = section.querySelector('select');
  const board = section.querySelector('.stroke-board');
  const status = section.querySelector('.stroke-status');
  for (const form of forms) select.add(new Option(form, form));
  select.parentElement.hidden = forms.length < 2;
  let writer, writtenForm;
  select.addEventListener('change', () => {
    writer?.pauseAnimation();
    board.hidden = true;
    status.textContent = '';
    button.textContent = '播放笔顺';
  });
  button.addEventListener('click', async () => {
    const form = select.value;
    const data = parent.ziliStrokeData?.[form];
    if (!data || !globalThis.HanziWriter) {
      status.textContent = '暂时没有可播放的笔顺数据。';
      return;
    }
    board.hidden = false;
    try {
      if (!writer || writtenForm !== form) {
        writer?.pauseAnimation();
        board.replaceChildren();
        writer = HanziWriter.create(board, form, {
          width: 184, height: 184, padding: 12,
          showCharacter: false, showOutline: true, strokeColor: '#8c291d',
          charDataLoader: (_, complete) => complete(data),
        });
        writtenForm = form;
      }
      const playing = writer;
      status.textContent = '正在播放「' + form + '」的笔顺。';
      button.textContent = '重新播放';
      await playing.animateCharacter();
      if (writer === playing && select.value === form && dialog.open) {
        status.textContent = '「' + form + '」共 ' + data.strokes.length + ' 笔。';
      }
    } catch {
      status.textContent = '笔顺暂时无法播放。';
    }
  });
  dialog.addEventListener('close', () => {
    writer?.pauseAnimation();
    writer = null;
    board.replaceChildren();
    board.hidden = true;
    status.textContent = '';
    button.textContent = '播放笔顺';
  });
})();
