(function mountQwenDemos() {
  const storyAddress = 'https://zili-xunzong.streamlit.app/?story=';
  function panel(anchor, title, examples, answer, before = false) {
    if (!anchor) return;
    const section = doc.createElement('details');
    section.open = true;
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
    const presets = doc.createElement('select');
    presets.setAttribute('aria-label', '预设问题');
    const placeholder = new Option('选择预设问题', '', true, true);
    placeholder.disabled = true;
    presets.add(placeholder);
    for (const question of examples) presets.add(new Option(question, question));
    presets.onchange = () => {
      input.value = presets.value;
      presets.selectedIndex = 0;
      form.requestSubmit();
    };
    form.append(presets);
    form.onsubmit = event => {event.preventDefault(); show(input.value.trim());};
    anchor[before ? 'before' : 'after'](section);
    return section;
  }

  if (page === 'nian.html') {
    panel(doc.getElementById('keepsake'), '问问这个字',
      ['泉州和金门有什么不同？', '为什么要留一副碗筷？', '泉州的游子除夕怎么过？', '金门的围炉有什么讲究？', '金门怎么为没回家的人留席？', '两地的团圆饭怎么体现团聚？', '泉州团圆饭的故事讲了什么？', '金门留座和摆碗筷有什么关系？'], question =>
        /碗筷|留席|留座|讲究/.test(question)
          ? '金门故事里，家人为没能返乡的游子留座、摆碗筷。出处见上方「金门｜围炉」。'
          : /泉州|金门|不同|团聚/.test(question)
            ? '泉州故事写游子赶回家吃饭，金门故事写家人为未返乡的游子留座。出处见上方两地故事。'
            : '你可以试试下拉菜单里的预设问题。', true);
  }

  const storyQuestions = {
  "men": [
    [
      "泉州什么时候贴春联？",
      "泉州案例记录了除夕贴春联的习俗。"
    ],
    [
      "台湾辞典记载春联贴在哪里？",
      "台湾案例提到大门两边可贴春联，门扇也可贴二字联。"
    ],
    [
      "泉州和台湾的记录各讲了什么？",
      "泉州案例交代贴春联的时间，台湾案例说明春联可以贴在门的哪些位置。"
    ],
    [
      "香港的挥春通常写什么？",
      "香港案例提到挥春会写吉祥字句，寄托对家人的祝福。"
    ],
    [
      "澳门案例里门上贴的是什么？",
      "澳门案例展示了在门上贴门神的做法。"
    ],
    [
      "门神和春联在故事里分别是什么？",
      "春联是写有祝福的文字，门神是贴在门上的人物图像。"
    ],
    [
      "新加坡的家庭怎样布置春节？",
      "新加坡案例提到春联和写有吉祥字的红纸剪饰。"
    ],
    [
      "想看用文字迎新的故事，先读哪几则？",
      "可以先读泉州贴春联、台湾门左右贴春联和香港写挥春。"
    ]
  ],
  "cha": [
    [
      "大陆案例里为什么要以茶待客？",
      "故事把给客人奉茶作为迎接客人的做法。"
    ],
    [
      "喝茶只发生在家里吗？",
      "大陆案例也提到茶馆和仪式中的饮茶。"
    ],
    [
      "台湾客家案例展示了什么？",
      "台湾案例介绍庄台芳制作擂茶的记录。"
    ],
    [
      "擂茶里的「擂」是什么意思？",
      "这里的「擂」指用工具把材料研磨，呼应故事中的手工制作。"
    ],
    [
      "以茶待客和做擂茶有什么不同？",
      "前者讲怎样用茶迎接客人，后者讲怎样动手制作擂茶。"
    ],
    [
      "香港和澳门的故事也讲喝茶吗？",
      "可翻到本页港澳栏，看各自记录把茶放在什么生活场景里。"
    ],
    [
      "新加坡祭祖时也会用茶吗？",
      "本站新加坡案例提到，有些家庭会在中元节祭祖时以茶叶作供品。"
    ],
    [
      "想读与待客有关的茶故事，从哪里开始？",
      "可以从两岸栏的「以茶待客」读起，再看旁边介绍擂茶制作的案例。"
    ]
  ],
  "chuan": [
    [
      "福建沿海记录了什么送王船习俗？",
      "福建案例将厦门湾和泉州湾沿海列为送王船习俗的传承区域。"
    ],
    [
      "台湾东港的王船有什么用途？",
      "台湾案例把王船列为东港迎王平安祭典的重要仪式物件。"
    ],
    [
      "香港大澳的龙舟用来做什么？",
      "大澳案例记载端午前后用龙舟接神、游涌，最后送神回庙。"
    ],
    [
      "澳门在哪里办端午龙舟竞渡？",
      "澳门案例收录的是南湾湖龙舟赛事。"
    ],
    [
      "南湾湖赛事有哪些组别？",
      "本页澳门资料提到赛事设有本地和国际组别。"
    ],
    [
      "马六甲的送王船由谁传承？",
      "联合申报资料将马六甲华人社群列为该习俗的传承社群。"
    ],
    [
      "大澳游涌和澳门竞渡有什么不同？",
      "大澳故事讲沿水道进行的仪式，澳门故事讲龙舟比赛。"
    ],
    [
      "想找送王船的故事，先看哪几则？",
      "可以看福建沿海、台湾东港和马来西亚马六甲三个案例。"
    ]
  ],
  "deng": [
    [
      "泉州花灯有哪些制作类别？",
      "泉州资料列出了彩扎灯、刻纸灯、针刺无骨灯等类别。"
    ],
    [
      "台湾花灯为什么提到竹纸工艺？",
      "台湾资料把花灯和传统照明器具，以及以竹、纸制灯的工艺联系起来。"
    ],
    [
      "香港的故事在哪个节日看彩灯？",
      "香港案例记录的是中秋彩灯会。"
    ],
    [
      "澳门元宵活动里能做什么灯？",
      "澳门新街坊案例提到鱼灯和花草纸灯两种手作。"
    ],
    [
      "新加坡的传统花灯记录在哪里？",
      "本站新加坡案例引用国家文物局收录的传统中式灯笼制作项目。"
    ],
    [
      "想了解做灯，可以先看哪几则？",
      "可以从泉州的针刺无骨灯、台湾的竹纸花灯和澳门的手作花灯读起。"
    ],
    [
      "哪则故事最适合看赏灯习俗？",
      "香港中秋彩灯会的故事侧重节庆中的赏灯。"
    ],
    [
      "泉州和台湾的资料各强调什么？",
      "泉州资料列举花灯制作类别，台湾资料介绍照明器具和竹纸做灯的联系。"
    ]
  ],
  "yuan": [
    [
      "台湾的元宵夜有哪些习俗？",
      "台湾文献案例列出吃汤圆、赏花灯和猜灯谜。"
    ],
    [
      "宁波南塘老街记录的是吃汤圆吗？",
      "现有资料记录的是南塘老街年节长桌宴，汤圆细节还待补直接证据。"
    ],
    [
      "澳门案例哪里提到汤圆？",
      "本页澳门案例引用澳门旅游学院资料中元宵节汤圆活动的段落。"
    ],
    [
      "新加坡故事讲的是哪一餐？",
      "新加坡案例聚焦春节团圆饭，记录新加坡华人家庭在春节相聚。"
    ],
    [
      "台湾元宵和新加坡团圆饭有什么不同？",
      "台湾案例讲元宵习俗，新加坡案例讲春节家庭团圆饭。"
    ],
    [
      "香港这则资料介绍的是哪个节日？",
      "香港案例的阅读材料介绍农历正月十五的元宵节。"
    ],
    [
      "想找本站直接提到汤圆的资料，先读哪两则？",
      "先读台湾元宵夜和澳门元宵汤圆活动的案例。"
    ],
    [
      "为什么把汤圆和团圆饭放在「圆」字页？",
      "这页用汤圆的圆形和「团圆」的用法，串起节日里相聚的故事。"
    ]
  ]
};
  const questions = storyQuestions[page.replace(/\.html$/, '')];
  if (questions) {
    const answers = new Map(questions);
    panel(doc.getElementById('keepsake'), '问问这个字', [...answers.keys()],
      question => answers.get(question) || '这页演示已准备 8 个问题，可从下拉菜单选一个查看回答。', true);
  }

  if (page === 'regions.html') {
    panel(doc.getElementById('habit-search'), '用一句话找故事',
      ['帮我找和端午划船有关的故事', '帮我找春节贴春联的故事', '哪里有龙舟竞渡的故事？', '想读香港大澳的龙舟故事', '想了解澳门的端午划船习俗', '泉州除夕怎么贴春联？', '台湾的门贴有什么故事？', '有哪些门贴和迎新年的故事？'], question => {
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
    const help = panel(lookup, '千问讲解', ['用大白话讲讲这个字', '给我两个日常例句', '这个字是什么意思？', '怎么给小学生讲这个字？', '用一句话解释这个字', '这个字可以怎么用？给个例句', '用这个字造两个句子', '给我适合朗读的例句'], question => {
      const word = doc.getElementById('hanzi')?.value.trim();
      return content[word]?.[/例句|造句|造两个/.test(question) ? 1 : 0] || '演示中可查询「船」或「茶」，再试下拉菜单里的问题。';
    });
    help.classList.add("qwen-lookup-demo");
    function syncLookup() {
      const wasHidden = help.hidden;
      help.hidden = lookup.hidden || !lookup.textContent.trim();
      if (wasHidden && !help.hidden) help.open = true;
      help.querySelector('[role="status"]').replaceChildren();
    }
    new MutationObserver(syncLookup).observe(lookup, {attributes:true,attributeFilter:['hidden'],childList:true,subtree:true});
    syncLookup();
  }
})();
