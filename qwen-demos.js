(function mountQwenDemos() {
  const storyAddress = 'https://zili-xunzong.streamlit.app/?story=';
  function panel(anchor, title, examples, answer, before = false) {
    if (!anchor) return;
    const section = doc.createElement('details');
    section.style.cssText = 'margin:12px 0;padding:10px 14px;border:1px solid #aac3d0;border-radius:8px;background:#eef6f8;color:#244d67';
    section.innerHTML = '<summary style="cursor:pointer;font-weight:700"></summary><form style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px"><input required style="flex:1;min-width:150px" aria-label="输入问题"><button>提交</button></form><p role="status"></p><small>千问功能演示 · 使用预设回答</small>';
    section.querySelector('summary').textContent = title;
    const form = section.querySelector('form');
    const input = form.querySelector('input');
    const result = section.querySelector('[role="status"]');
    function show(question) {
      result.replaceChildren();
      const response = answer(question);
      if (typeof response === 'string') result.textContent = response;
      else result.append(...response);
    }
    for (const question of examples) {
      const button = doc.createElement('button');
      button.type = 'button';
      button.textContent = question;
      button.onclick = () => {input.value = question; show(question);};
      form.append(button);
    }
    form.onsubmit = event => {event.preventDefault(); show(input.value.trim());};
    anchor[before ? 'before' : 'after'](section);
    return section;
  }

  if (page === 'nian.html') {
    panel(doc.getElementById('keepsake'), '问问这个字',
      ['泉州和金门有什么不同？', '为什么要留一副碗筷？'], question =>
        /碗筷|留席/.test(question)
          ? '金门故事里，家人为没能返乡的游子留座、摆碗筷。出处见上方「金门｜围炉」。'
          : /泉州|金门|不同/.test(question)
            ? '泉州故事写游子赶回家吃饭，金门故事写家人为未返乡的游子留座。出处见上方两地故事。'
            : '你可以试试上方的两个示例问题。', true);
  }

  if (page === 'regions.html') {
    panel(doc.getElementById('habit-search'), '用一句话找故事',
      ['帮我找和端午划船有关的故事', '帮我找春节贴春联的故事'], question => {
        const key = /端午|龙舟|划船/.test(question) ? 'chuan' : /春联|门贴/.test(question) ? 'men' : '';
        if (!key) return '你可以试试「端午划船」或「春节贴春联」。';
        const results = doc.createElement('div');
        results.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px';
        const titles = key === 'chuan'
          ? ['香港大澳｜龙舟沿水道游涌', '澳门南湾湖｜端午龙舟竞渡']
          : ['福建泉州｜除夕贴春联', '台湾｜门左右贴春联'];
        for (const title of titles) {
          const link = doc.createElement('a');
          link.textContent = title;
          link.href = storyAddress + key;
          link.target = '_blank';
          link.rel = 'noopener';
          link.style.cssText = 'padding:8px;border:1px solid #aac3d0;border-radius:6px';
          results.append(link);
        }
        return [results];
      });
  }

  const lookup = doc.getElementById('lookup-result');
  if (lookup) {
    const content = {
      '船': ['船是在水上载人或运东西的交通工具。', '我们坐船过河。端午节那天，大家到河边看龙舟比赛。'],
      '茶': ['茶可以指茶叶，也可以指用热水泡出来的茶水。', '外婆泡了一壶茶。客人来了，我们请他喝茶。']
    };
    const help = panel(lookup, '千问讲解', ['通俗讲解', '看例句'], question => {
      const word = doc.getElementById('hanzi')?.value.trim();
      return content[word]?.[/例句/.test(question) ? 1 : 0] || '演示中可查询「船」或「茶」，再试这两个按钮。';
    });
    help.classList.add("qwen-lookup-demo");
    function syncLookup() {
      help.hidden = lookup.hidden || !lookup.textContent.trim();
      help.open = false;
      help.querySelector('[role="status"]').replaceChildren();
    }
    new MutationObserver(syncLookup).observe(lookup, {attributes:true,attributeFilter:['hidden'],childList:true,subtree:true});
    syncLookup();
  }
})();
