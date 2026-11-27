// Small speech queue; a generation token invalidates callbacks after cancellation/navigation.
function createZiliReader({synth, Utterance, onState, onParagraph}) {
  let paragraphs=[], index=0, offset=0, token=0, active=null, timer=null;
  let state='idle', rate=1, voice=null;
  const clearTimer=()=>{clearTimeout(timer);timer=null;};
  function emit(message=''){onState({state,index,total:paragraphs.length,message});}
  function cancel(){token++;clearTimer();active=null;synth.cancel();if(synth.paused)synth.resume();}
  function finish(nextState,message=''){cancel();state=nextState;onParagraph(null);emit(message);}
  function speak(){
    if(index>=paragraphs.length){finish('ended','本页讲解已完成。');return;}
    const paragraph=paragraphs[index];
    if(paragraph.valid&&!paragraph.valid()){finish('idle','页面内容已变化，请重新选择段落。');return;}
    const remaining=paragraph.text.slice(offset);
    const sentence=remaining.match(/^[\s\S]{1,100}(?:[。！？；\n]|$)/);
    const chunk=sentence?sentence[0]:remaining.slice(0,100);
    const current=token;
    const u=new Utterance(chunk);active=u;u.lang=voice?.lang||'zh-CN';u.rate=rate;if(voice)u.voice=voice;
    let started=false;
    u.onstart=()=>{if(current!==token)return;started=true;clearTimer();onParagraph(paragraph);emit();};
    u.onend=()=>{if(current!==token)return;clearTimer();active=null;offset+=chunk.length;if(offset>=paragraph.text.length){index++;offset=0;}if(state==='playing')speak();};
    u.onerror=e=>{if(current!==token)return;finish('error',e.error==='not-allowed'?'浏览器未允许播放，请再次点击开始或检查声音权限。':'语音播放失败，请检查设备声音或更换声音后重试。');};
    timer=setTimeout(()=>{if(current===token&&!started&&state==='playing')finish('error','设备未启动语音。请检查系统中文语音、音量或换用其他浏览器。');},8000);
    try{synth.speak(u);}catch{finish('error','当前设备无法启动语音播放。');}
  }
  return {
    load(items,selected=0){cancel();paragraphs=items;index=Math.max(0,Math.min(selected,items.length-1));offset=0;state='idle';onParagraph(null);emit();},
    play(){
      if(!paragraphs.length){emit('当前没有可朗读的正文。');return;}
      if(state==='paused'&&active){state='playing';try{synth.resume();}catch{finish('error','无法继续播放，请重新朗读。');return;}emit();return;}
      if(state==='ended'){index=0;offset=0;}
      cancel();state='playing';emit();speak();
    },
    pause(){if(state!=='playing')return;state='paused';clearTimer();try{synth.pause();}catch{finish('error','暂停失败，请停止后重试。');return;}emit();},
    stop(){finish('idle','已停止。');offset=0;},
    select(next){cancel();index=Math.max(0,Math.min(next,paragraphs.length-1));offset=0;state='idle';onParagraph(null);emit();},
    next(){cancel();offset=0;index++;if(index>=paragraphs.length){finish('ended','本页讲解已完成。');return;}state='playing';emit();speak();},
    restart(){cancel();index=0;offset=0;state='idle';this.play();},
    configure(nextRate,nextVoice){rate=nextRate;voice=nextVoice;if(state==='playing'||state==='paused'){const playing=state==='playing';cancel();state='idle';if(playing)this.play();else{state='idle';onParagraph(null);emit('设置已更新，点击开始讲解将从当前段落继续。');}}},
    destroy(){cancel();state='idle';onParagraph(null);}
  };
}

let ziliVoiceGuide=null;
function bindZiliVoiceGuide(doc){
  ziliVoiceGuide?.destroy();
  const view=doc.defaultView;
  const synth=view.speechSynthesis;
  const supported=!!(synth&&view.SpeechSynthesisUtterance);
  const host=doc.createElement('div');host.id='zili-voice-assistant';
  host.innerHTML='<button type="button" class="zv-launch" aria-expanded="false" aria-controls="zv-panel"><span class="zv-seal" aria-hidden="true">听</span>寻踪小助手</button><section id="zv-panel" aria-label="寻踪小助手朗读控制" hidden><header><div><b>寻踪小助手</b><small>让汉字文化被听见</small></div><button type="button" class="zv-close" aria-label="收起语音助手">⌄</button></header><div class="zv-body"><p class="zv-page"></p><p class="zv-status" role="status" aria-live="polite"></p><label>选择朗读段落<select class="zv-segments" aria-label="选择朗读段落"></select></label><div class="zv-actions"><button type="button" class="zv-play">开始讲解</button><button type="button" class="zv-next">下一段</button><button type="button" class="zv-stop">停止</button><button type="button" class="zv-restart">从头朗读</button></div><div class="zv-settings"><label>朗读语速<select class="zv-rate" aria-label="朗读语速"><option value="0.75">0.75×</option><option value="1" selected>1.0×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option></select></label><label>讲解声音<select class="zv-voice" aria-label="讲解声音"><option value="">设备默认中文声音</option></select></label></div><p class="zv-note">按页面原文朗读；声音由设备提供。收起可继续听，切换页面自动停止。</p></div></section>';
  doc.body.append(host);
  const get=selector=>host.querySelector(selector);
  const launch=get('.zv-launch'),panel=get('#zv-panel'),status=get('.zv-status'),segments=get('.zv-segments'),play=get('.zv-play');
  let entries=[],currentState='idle',highlighted=null,voices=[],selectedVoice='';
  get('.zv-page').textContent=doc.querySelector('h1')?.textContent.trim()||doc.title||'当前页面';
  function visible(node){
    if(!node.isConnected||node.closest('#zili-voice-assistant,[hidden],[aria-hidden="true"],nav,aside,form,dialog,script,style'))return false;
    for(let ancestor=node.parentElement;ancestor;ancestor=ancestor.parentElement){
      if(ancestor.tagName==='DETAILS'&&!ancestor.open&&!ancestor.querySelector('summary')?.contains(node))return false;
    }
    return node.getClientRects().length>0&&view.getComputedStyle(node).visibility!=='hidden';
  }
  function collect(){
    const scope=doc.body.classList.contains('lookup-only')?doc.querySelector('#story-lookup'):doc.querySelector('main')||doc.querySelector('.page')||doc.body;
    if(!scope)return [];
    const nodes=[...scope.querySelectorAll('h1,h2,h3,h4,p,li,blockquote,dt,dd')].filter(visible);
    return nodes.filter(node=>!nodes.some(child=>child!==node&&node.contains(child))).map(node=>{
      const clone=node.cloneNode(true);clone.querySelectorAll('button,input,select,textarea,svg,[aria-hidden="true"],.qwen-demo-status').forEach(el=>el.remove());
      return {node,text:clone.textContent.replace(/\s+/g,' ').trim(),valid:()=>visible(node)};
    }).filter(item=>item.text&&/[\p{L}\p{N}]/u.test(item.text));
  }
  function highlight(item){highlighted?.classList.remove('zili-voice-reading');highlighted=item?.node||null;highlighted?.classList.add('zili-voice-reading');}
  const reader=supported?createZiliReader({synth,Utterance:view.SpeechSynthesisUtterance,onParagraph:highlight,onState:update}):null;
  function update({state,index,total,message}){
    currentState=state;
    play.textContent=state==='playing'?'暂停讲解':state==='paused'?'继续讲解':state==='ended'?'重新朗读':'开始讲解';
    play.setAttribute('aria-label',play.textContent);
    if(total&&index<total)segments.value=String(index);
    status.textContent=message||(state==='playing'?'正在讲解':state==='paused'?'已暂停':'准备就绪')+(total?' · 第 '+Math.min(index+1,total)+' / '+total+' 段':'');
    segments.disabled=state==='playing'||state==='paused';
  }
  function refresh(){
    entries=collect();segments.replaceChildren();
    entries.forEach((entry,i)=>segments.add(new view.Option((i+1)+' · '+entry.text.slice(0,42)+(entry.text.length>42?'…':''),String(i))));
    reader?.load(entries);
    if(!entries.length)status.textContent='当前没有可朗读的正文，请先打开故事或查询汉字。';
    play.disabled=!supported||!entries.length;
    get('.zv-next').disabled=get('.zv-restart').disabled=!supported||!entries.length;
  }
  function open(value){panel.hidden=!value;launch.setAttribute('aria-expanded',String(value));if(value&&supported&&currentState!=='playing'&&currentState!=='paused')refresh();}
  launch.onclick=()=>open(panel.hidden);
  get('.zv-close').onclick=()=>{open(false);launch.focus();};
  host.addEventListener('keydown',e=>{if(e.key==='Escape'){open(false);launch.focus();}});
  function loadVoices(){
    voices=synth.getVoices().filter(voice=>/^(zh|cmn|yue)(-|_|$)/i.test(voice.lang));
    const previous=selectedVoice;get('.zv-voice').replaceChildren(new view.Option('设备默认中文声音',''));
    voices.forEach(voice=>get('.zv-voice').add(new view.Option(voice.name+' · '+voice.lang,voice.voiceURI)));
    selectedVoice=voices.some(voice=>voice.voiceURI===previous)?previous:'';
    get('.zv-voice').value=selectedVoice;
  }
  if(supported){
    loadVoices();synth.addEventListener('voiceschanged',loadVoices);
    play.onclick=()=>{
      if(currentState==='playing'){reader.pause();return;}
      if(currentState==='paused'){reader.play();return;}
      if(currentState==='ended'){refresh();reader.restart();return;}
      const selected=Number(segments.value)||0;refresh();reader.select(selected);reader.play();
    };
    get('.zv-stop').onclick=()=>reader.stop();get('.zv-restart').onclick=()=>{refresh();reader.restart();};
    get('.zv-next').onclick=()=>{if(currentState==='ended'){refresh();reader.play();}else reader.next();};
    segments.onchange=()=>reader.select(Number(segments.value));
    const settings=()=>{selectedVoice=get('.zv-voice').value;reader.configure(Number(get('.zv-rate').value),voices.find(voice=>voice.voiceURI===selectedVoice)||null);};
    get('.zv-rate').onchange=get('.zv-voice').onchange=settings;
  }else{
    status.textContent='当前浏览器不支持语音朗读，请在支持系统语音的 Chrome、Edge 或 Safari 中打开。';
    host.querySelectorAll('.zv-body button,.zv-body select').forEach(control=>control.disabled=true);
  }
  const unload=()=>reader?.destroy();view.addEventListener('pagehide',unload);
  ziliVoiceGuide={destroy(){reader?.destroy();view.removeEventListener('pagehide',unload);if(supported)synth.removeEventListener('voiceschanged',loadVoices);host.remove();}};
}
