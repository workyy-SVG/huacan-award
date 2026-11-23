(() => {
  const result = document.getElementById('lookup-result');
  if (!result) return;
  const heading = result.querySelector('#word');
  const definitionNodes = [...result.children].filter(node => node !== heading);
  const grid = document.createElement('div');
  grid.className = 'lookup-three';
  grid.innerHTML = '<section class="lookup-tile"><h3>萌典 · 看字义</h3></section><section class="lookup-tile"><h3>Unihan · 看简繁</h3><div class="lookup-forms" role="group" aria-label="切换字形"></div><div class="lookup-glyph"></div><p class="lookup-variant-note"></p></section><section class="lookup-tile"><h3>Hanzi Writer · 看笔顺</h3><p class="lookup-stroke-form"></p><div class="lookup-stroke-board" hidden></div><div class="lookup-stroke-controls"><button type="button" class="lookup-play">播放笔顺</button><p class="lookup-stroke-status" role="status"></p></div></section>';
  grid.firstElementChild.append(...definitionNodes);
  result.append(grid);

  const buttons = grid.querySelector('.lookup-forms');
  const glyph = grid.querySelector('.lookup-glyph');
  const board = grid.querySelector('.lookup-stroke-board');
  const play = grid.querySelector('.lookup-play');
  const strokeStatus = grid.querySelector('.lookup-stroke-status');
  let writer, selected;
  let paused = false;
  for (const tile of [...grid.children].slice(1)) tile.hidden = true;
  function choose(form) {
    writer?.pauseAnimation();
    writer = undefined;
    paused = false;
    selected = form;
    glyph.textContent = form;
    grid.querySelector('.lookup-stroke-form').textContent = '当前字形：' + form;
    for (const button of buttons.children) {
      button.setAttribute('aria-pressed', String(button.textContent === form));
    }
    board.replaceChildren();
    board.hidden = true;
    play.textContent = '播放笔顺';
    const ready = Boolean(parent.ziliStrokeData?.[form] && globalThis.HanziWriter);
    play.disabled = !ready;
    strokeStatus.textContent = ready ? '' : '暂无该字形的笔顺数据。';
  }
  document.addEventListener('zili:lookup', event => {
    const word = event.detail;
    for (const tile of [...grid.children].slice(1)) tile.hidden = !word;
    if (!word) {
      choose('');
      return;
    }
    const forms = [...new Set([word, ...(parent.ziliVariants?.[word] ?? [])])];
    buttons.replaceChildren(...forms.map(form => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = form;
      button.addEventListener('click', () => choose(form));
      return button;
    }));
    grid.querySelector('.lookup-variant-note').textContent = forms.length > 1
      ? '切换字形可比较写法，并选择对应的笔顺。'
      : 'Unihan 暂无其他简繁关联字形。';
    choose(word);
  });
  play.addEventListener('click', async () => {
    const form = selected;
    const data = parent.ziliStrokeData?.[form];
    if (play.disabled || !data) return;
    board.hidden = false;
    try {
      if (writer) {
        if (paused) writer.resumeAnimation();
        else writer.pauseAnimation();
        paused = !paused;
        play.textContent = paused ? '继续播放' : '暂停';
        return;
      }

      writer = HanziWriter.create(board, form, {
        width: 160,
        height: 160,
        padding: 10,
        showOutline: true,
        showCharacter: false,
        strokeColor: '#8c291e',
        delayBetweenLoops: 1000,
        charDataLoader: (_, complete) => complete(data),
      });
      const playing = writer;
      play.textContent = '暂停';
      strokeStatus.textContent = '「' + form + '」共 ' + data.strokes.length + ' 笔。';
      await Promise.resolve(playing.loopCharacterAnimation()).catch(error => {
        if (playing === writer) throw error;
      });
    } catch {
      writer?.pauseAnimation();
      writer = undefined;
      paused = false;
      board.replaceChildren();
      board.hidden = true;
      play.textContent = '播放笔顺';
      strokeStatus.textContent = '笔顺暂时无法播放。';
    }
  });
})();