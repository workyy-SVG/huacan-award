(function mountQwen() {
  const storyPresets = {
  "men": [
    "泉州什么时候贴春联？",
    "台湾辞典记载春联贴在哪里？",
    "泉州和台湾的记录各讲了什么？",
    "香港的挥春通常写什么？",
    "澳门案例里门上贴的是什么？",
    "门神和春联在故事里分别是什么？",
    "新加坡的家庭怎样布置春节？",
    "想看用文字迎新的故事，先读哪几则？"
  ],
  "cha": [
    "大陆案例里为什么要以茶待客？",
    "喝茶只发生在家里吗？",
    "台湾客家案例展示了什么？",
    "擂茶里的「擂」是什么意思？",
    "以茶待客和做擂茶有什么不同？",
    "香港和澳门的故事也讲喝茶吗？",
    "新加坡祭祖时也会用茶吗？",
    "想读与待客有关的茶故事，从哪里开始？"
  ],
  "chuan": [
    "福建沿海记录了什么送王船习俗？",
    "台湾东港的王船有什么用途？",
    "香港大澳的龙舟用来做什么？",
    "澳门在哪里办端午龙舟竞渡？",
    "南湾湖赛事有哪些组别？",
    "马六甲的送王船由谁传承？",
    "大澳游涌和澳门竞渡有什么不同？",
    "想找送王船的故事，先看哪几则？"
  ],
  "deng": [
    "泉州花灯有哪些制作类别？",
    "台湾花灯为什么提到竹纸工艺？",
    "香港的故事在哪个节日看彩灯？",
    "澳门元宵活动里能做什么灯？",
    "新加坡的传统花灯记录在哪里？",
    "想了解做灯，可以先看哪几则？",
    "哪则故事最适合看赏灯习俗？",
    "泉州和台湾的资料各强调什么？"
  ],
  "yuan": [
    "台湾的元宵夜有哪些习俗？",
    "宁波南塘老街记录的是吃汤圆吗？",
    "澳门案例哪里提到汤圆？",
    "新加坡故事讲的是哪一餐？",
    "台湾元宵和新加坡团圆饭有什么不同？",
    "香港这则资料介绍的是哪个节日？",
    "想找本站直接提到汤圆的资料，先读哪两则？",
    "为什么把汤圆和团圆饭放在「圆」字页？"
  ],
  "nian": [
    "泉州和金门有什么不同？",
    "为什么要留一副碗筷？",
    "泉州的游子除夕怎么过？",
    "金门的围炉有什么讲究？",
    "金门怎么为没回家的人留席？",
    "两地的团圆饭怎么体现团聚？",
    "泉州团圆饭的故事讲了什么？",
    "金门留座和摆碗筷有什么关系？"
  ]
};
  const story = page.replace(/\.html$/, '');
  const lookup = doc.getElementById('lookup-result');

  function panel(anchor, mode, title, presets, before = false) {
    if (!anchor) return;
    const section = doc.createElement('details');
    section.open = true;
    section.style.cssText = 'margin:12px 0;padding:10px 14px;border:1px solid #aac3d0;border-radius:8px;background:#eef6f8;color:#244d67';
    section.innerHTML = '<summary style="cursor:pointer;font-weight:700"></summary><form style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px"><input required maxlength="400" style="flex:1;min-width:150px" aria-label="输入问题"><button>提交</button><select aria-label="预设问题"></select></form><div role="status" style="white-space:pre-wrap;margin-top:8px"></div><small>千问实时回答</small>';
    section.querySelector('summary').textContent = title;
    const form = section.querySelector('form');
    const input = form.querySelector('input');
    const submit = form.querySelector('button');
    const picker = form.querySelector('select');
    const result = section.querySelector('[role="status"]');
    const placeholder = new Option('选择预设问题', '', true, true);
    placeholder.disabled = true;
    picker.add(placeholder);
    for (const question of presets) picker.add(new Option(question, question));
    picker.onchange = () => {
      input.value = picker.value;
      picker.selectedIndex = 0;
      form.requestSubmit();
    };

    const pendingKey = 'zili-pending:' + mode + ':' + story;
    let resumed;
    try { resumed = JSON.parse(sessionStorage.getItem(pendingKey) || 'null'); } catch {}
    if (resumed && Date.now() - resumed.time > 40000) resumed = null;
    form.onsubmit = event => {
      event.preventDefault();
      const question = input.value.trim();
      if (!question || submit.disabled) return;
      const restored = resumed; resumed = null;
      const id = restored?.id || crypto.randomUUID();
      try { sessionStorage.setItem(pendingKey, JSON.stringify({id, question, time:restored?.time || Date.now()})); } catch {}
      submit.disabled = picker.disabled = true;
      result.textContent = '千问正在回答…';
      const timeout = setTimeout(() => {
        parent.postMessage({type:'qwen-cancel', id}, '*');
        finish({error:'请求超时，请稍后重试。'});
      }, Math.max(1, 40000 - (Date.now() - (restored?.time || Date.now()))));
      function finish(response) {
        clearTimeout(timeout);
        try { sessionStorage.removeItem(pendingKey); } catch {}
        window.removeEventListener('message', receive);
        submit.disabled = picker.disabled = false;
        result.textContent = response.error || response.text || '';
        if (response.records?.length === 0) result.textContent = '站内没有找到相关故事。';
        for (const record of response.records || []) {
          const card = doc.createElement('article');
          card.style.cssText = 'border-top:1px solid #aac3d0;padding:8px 0';
          const link = doc.createElement('a');
          link.href = 'https://zili-xunzong.streamlit.app/?story=' + encodeURIComponent(record.story);
          link.target = '_blank';
          link.rel = 'noopener';
          link.textContent = record.place + '｜' + record.title;
          const description = doc.createElement('div');
          description.textContent = record.body;
          card.append(link, description);
          result.append(card);
        }
        for (const record of response.sources || []) {
          const source = doc.createElement('div');
          source.textContent = '[' + record.id + '] ' + record.place + '｜' + record.title;
          if (/^https?:\/\//i.test(record.source)) {
            const link = doc.createElement('a');
            link.href = record.source;
            link.target = '_blank';
            link.rel = 'noopener';
            link.textContent = ' 查看出处';
            source.append(link);
          }
          result.append(source);
        }
      }
      function receive({source, data}) {
        if (source === parent && data?.type === 'qwen-response' && data.id === id) finish(data);
      }
      window.addEventListener('message', receive);
      const request = {id, mode, story, question};
      if (mode === 'lookup') {
        request.character = doc.getElementById('hanzi').value.trim();
        request.dictionary = lookup.textContent.trim();
      }
      if (!restored) parent.postMessage({type:'qwen-request', request}, '*');
      else {
        let completed;
        try { completed = JSON.parse(sessionStorage.getItem('zili-answer:' + id) || 'null'); } catch {}
        if (completed) finish(completed);
      }
    };
    anchor[before ? 'before' : 'after'](section);
    if (resumed) { input.value = resumed.question; form.requestSubmit(); }
    return section;
  }

  if (storyPresets[story]) {
    panel(doc.getElementById('keepsake'), 'story', '问问这个字', storyPresets[story], true);
  }
  if (page === 'regions.html') {
    const keywordSearch = doc.getElementById('habit-search');
    panel(keywordSearch, 'search', '用一句话找故事', ['帮我找和端午划船有关的故事', '帮我找春节贴春联的故事', '哪里有龙舟竞渡的故事？', '想读香港大澳的龙舟故事', '想了解澳门的端午划船习俗', '泉州除夕怎么贴春联？', '台湾的门贴有什么故事？', '有哪些门贴和迎新年的故事？']);
    if (keywordSearch) { keywordSearch.title = '关键词搜索，无需 AI'; }
  }
  if (lookup) {
    const help = panel(lookup, 'lookup', '千问讲解', ['用大白话讲讲这个字', '给我两个日常例句', '这个字是什么意思？', '怎么给小学生讲这个字？', '用一句话解释这个字', '这个字可以怎么用？给个例句', '用这个字造两个句子', '给我适合朗读的例句']);
    help.classList.add('qwen-lookup-demo');
    function syncLookup() {
      const wasHidden = help.hidden;
      help.hidden = lookup.hidden || !lookup.textContent.trim();
      if (wasHidden && !help.hidden) {
        help.open = true;
        if (doc.body.matches('.lookup-only, :has(.lookup-credit-flow)')) {
          const view = doc.defaultView;
          view.requestAnimationFrame(() => view.scrollTo(0, 0));
        }
      }
    }
    new MutationObserver(syncLookup).observe(lookup, {attributes:true,attributeFilter:['hidden'],childList:true,subtree:true});
    syncLookup();
  }
})();

