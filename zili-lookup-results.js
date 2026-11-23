(() => {
  const result = document.getElementById('lookup-result');
  if (!result) return;
  const heading = result.querySelector('#word');
  const definitionNodes = [...result.children].filter(node => node !== heading);
  const grid = document.createElement('div');
  grid.className = 'lookup-three';
  grid.innerHTML = '<section class="lookup-tile lookup-definition"><h3>萌典 · 看字义</h3></section><section class="lookup-tile"><h3>Unihan · 看简繁</h3><div class="lookup-forms" role="group" aria-label="切换字形"></div><div class="lookup-glyph"></div><p class="lookup-variant-note"></p></section><section class="lookup-tile"><h3>Hanzi Writer · 看笔顺</h3><p class="lookup-stroke-form"></p><div class="lookup-stroke-board" hidden></div><div class="lookup-stroke-controls"><button type="button" class="lookup-play">播放笔顺</button><p class="lookup-stroke-status" role="status"></p></div></section>';
  grid.firstElementChild.append(...definitionNodes);
  for (const link of grid.firstElementChild.querySelectorAll('a')) {
    const arrow = document.createElement('span');
    arrow.className = 'lookup-link-arrow';
    arrow.setAttribute('aria-hidden', 'true');
    arrow.textContent = ' →';
    link.append(arrow);
  }
  result.append(grid);

  const buttons = grid.querySelector('.lookup-forms');
  const glyph = grid.querySelector('.lookup-glyph');
  const board = grid.querySelector('.lookup-stroke-board');
  const play = grid.querySelector('.lookup-play');
  const strokeStatus = grid.querySelector('.lookup-stroke-status');
  let writer, selected;
  let paused = false;
  let autoplayTimer;
  let strokeRequest;
  let strokeData;
  for (const tile of [...grid.children].slice(1)) tile.hidden = true;
  async function choose(form) {
    clearTimeout(autoplayTimer);
    strokeRequest?.abort();
    strokeRequest = undefined;
    strokeData = undefined;
    writer?.pauseAnimation();
    writer = undefined;
    paused = false;
    selected = form;
    glyph.textContent = form;
    grid.querySelector('.lookup-stroke-form').textContent = '当前字形：' + form;
    for (const button of buttons.children) {
      button.setAttribute('aria-pressed', String(button.dataset.form === form));
    }
    board.replaceChildren();
    board.hidden = true;
    play.disabled = true;
    play.textContent = '播放笔顺';
    strokeStatus.textContent = '';
    if (!form) return;
    if (!globalThis.HanziWriter) {
      strokeStatus.textContent = '笔顺组件暂时无法加载。';
      return;
    }

    strokeData = parent.ziliStrokeData?.[form];
    if (!strokeData) {
      const request = new AbortController();
      strokeRequest = request;
      const timeout = setTimeout(() => request.abort(), 8000);
      strokeStatus.textContent = '正在加载笔顺…';
      try {
        const url = 'https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0.1/' +
          encodeURIComponent(form) + '.json';
        const response = await fetch(url, {signal: request.signal});
        if (strokeRequest !== request) return;
        if (response.status === 404) {
          strokeStatus.textContent = '笔顺库暂无该字形。';
          return;
        }
        if (!response.ok) throw new Error('Stroke data request failed');
        const data = await response.json();
        if (strokeRequest !== request) return;
        if (!Array.isArray(data.strokes) || !data.strokes.length ||
            data.strokes.length !== data.medians?.length) {
          throw new Error('Invalid stroke data');
        }
        strokeData = data;
      } catch {
        if (strokeRequest === request) {
          strokeStatus.textContent = '暂时无法加载笔顺，请重新查询。';
        }
        return;
      } finally {
        clearTimeout(timeout);
        if (strokeRequest === request) strokeRequest = undefined;
      }
    }

    strokeStatus.textContent = '';
    play.textContent = '即将播放';
    autoplayTimer = setTimeout(() => {
      play.disabled = false;
      togglePlayback();
    }, 2000);
  }
  document.addEventListener('zili:lookup', event => {
    const word = event.detail;
    for (const tile of [...grid.children].slice(1)) tile.hidden = !word;
    if (!word) {
      choose('');
      return;
    }
    const pair = parent.ziliVariantPairs?.[word];
    const same = parent.ziliSameForms?.has(word);
    const forms = new Map();
    if (pair) {
      const [simple, traditional] = pair;
      for (const [values, label] of [[simple || word, '简体'], [traditional || word, '繁体']]) {
        for (const form of values) {
          forms.set(form, forms.has(form) ? '简繁同形' : label);
        }
      }
    }
    if (!forms.has(word)) forms.set(word, same ? '简繁同形' : '输入字');
    buttons.replaceChildren(...Array.from(forms, ([form, label]) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.form = form;
      const caption = document.createElement('small');
      caption.textContent = label;
      button.append(caption, form);
      button.addEventListener('click', () => {
        if (form !== selected) choose(form);
      });
      return button;
    }));
    grid.querySelector('.lookup-variant-note').textContent = pair
      ? '点击字形查看对应笔顺。若有多个繁体写法，请按词义区分。'
      : same
        ? '常用简体和繁体都写作「' + word + '」。'
        : '暂未查到该字的简繁对应。';
    choose(word);
  });
  async function togglePlayback() {
    const form = selected;
    const data = strokeData;
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

      const size = 260;
      writer = HanziWriter.create(board, form, {
        width: size,
        height: size,
        padding: 10,
        showOutline: true,
        showCharacter: false,
        strokeColor: '#8c291e',
        delayBetweenLoops: 1000,
        charDataLoader: (_, complete) => complete(data),
      });
      board.querySelector('svg')?.setAttribute('viewBox', `0 0 ${size} ${size}`);
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
  }
  play.addEventListener('click', togglePlayback);
})();