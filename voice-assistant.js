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

// Match actual language metadata. zh-TW is Mandarin, never Taiwanese Hokkien.
function ziliRegionalVoices(voices,mode){
  return voices.filter(voice=>{
    const lang=voice.lang.toLowerCase().replaceAll('_','-');
    if(mode==='mandarin')return /^(zh-(cn|sg|hans)(-|$)|cmn(-|$)|zh$)/.test(lang);
    if(mode==='hongkong'||mode==='macau')return /^(yue(-|$)|zh-(hk|mo)(-|$))/.test(lang);
    return /^(nan(-|$)|zh-min-nan(-|$))/.test(lang);
  });
}
function ziliClampVoicePosition(x,y,width,height,buttonWidth,buttonHeight){
  return {x:Math.max(8,Math.min(x,width-buttonWidth-8)),y:Math.max(8,Math.min(y,height-buttonHeight-8))};
}
let ziliVoiceGuide=null;
let ziliVoicePosition=null;
let ziliVoiceMode='mandarin';
function bindZiliVoiceGuide(doc){
  ziliVoiceGuide?.destroy();
  const view=doc.defaultView;
  const supported=!!(view.AudioContext||view.webkitAudioContext);
  const host=doc.createElement('div');host.id='zili-voice-assistant';
  host.innerHTML='<button type="button" class="zv-launch" aria-expanded="false" aria-controls="zv-panel"><span class="zv-seal" aria-hidden="true">听</span>寻踪小助手</button><section id="zv-panel" aria-label="寻踪小助手朗读控制" hidden><header><div><b>寻踪小助手</b><small>让汉字文化被听见</small></div><button type="button" class="zv-close" aria-label="收起语音助手">⌄</button></header><div class="zv-body"><p class="zv-page"></p><p class="zv-status" role="status" aria-live="polite"></p><label>选择朗读段落<select class="zv-segments" aria-label="选择朗读段落"></select></label><div class="zv-actions"><button type="button" class="zv-play">开始讲解</button><button type="button" class="zv-next">下一段</button><button type="button" class="zv-stop">停止</button><button type="button" class="zv-restart">从头朗读</button></div><div class="zv-settings"><label>朗读语速<select class="zv-rate" aria-label="朗读语速"><option value="0.75">0.75×</option><option value="1" selected>1.0×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option></select></label><label>讲解声音<select class="zv-voice" aria-label="讲解声音"><option value="">设备默认中文声音</option></select></label></div><p class="zv-note">按页面原文朗读；声音由设备提供。收起可继续听，切换页面自动停止。</p></div></section>';
  doc.body.append(host);
  const get=selector=>host.querySelector(selector);
  const launch=get('.zv-launch'),panel=get('#zv-panel'),status=get('.zv-status'),segments=get('.zv-segments'),play=get('.zv-play');
  const languageLabel=doc.createElement('label');languageLabel.className='zv-language-label';
  languageLabel.innerHTML='讲解语言<select class="zv-language" aria-label="讲解语言"><option value="mandarin">中文普通话</option><option value="cantonese">香港澳门粤语</option><option value="taiwan">台湾台语（闽南语）</option></select>';
  get('.zv-settings').before(languageLabel);
  const languageNote=doc.createElement('p');languageNote.className='zv-language-note';languageNote.setAttribute('role','status');languageLabel.after(languageNote);
  const reset=doc.createElement('button');reset.type='button';reset.className='zv-reset';reset.textContent='恢复默认位置';get('.zv-note').before(reset);
  get('.zv-note').textContent='边生成边播放，需要联网。连续朗读时会高亮当前内容组。拖动入口或标题可移动；Home 复位。';
  if(['hongkong','macau'].includes(ziliVoiceMode))ziliVoiceMode='cantonese';
  get('.zv-language').value=ziliVoiceMode;
  let entries=[],currentState='idle',highlighted=[],answerEntries=null,picking=false;
  let voiceReady=false,drag=null,suppressClick=false,warmController=null;
  const prepared=doc.createElement('p');prepared.className='zv-language-note zv-prepared';prepared.setAttribute('role','status');languageNote.after(prepared);
  function prepareSelected(){
    prepared.textContent='连续流式朗读：从所选段落往下读，音频边生成边播放。';
  }
  const scopeActions=doc.createElement('div');scopeActions.className='zv-actions';
  scopeActions.innerHTML='<button type="button" class="zv-pick">从这里朗读</button><button type="button" class="zv-original">朗读本页原文</button>';
  get('.zv-segments').parentElement.after(scopeActions);
  function fillEntries(next){
    entries=next;segments.replaceChildren();
    entries.forEach((entry,i)=>segments.add(new view.Option((i+1)+' · '+entry.text.slice(0,42)+(entry.text.length>42?'…':''),String(i))));
    reader?.load(entries);
    play.disabled=!supported||!entries.length||!voiceReady;
    get('.zv-next').disabled=get('.zv-restart').disabled=play.disabled;
  }
  function readAnswer(event){
    const {node,text}=event.detail||{};if(!node?.isConnected||typeof text!=='string'||!text.trim())return;
    endPicking();
    answerEntries=[{node,text:text.trim(),valid:()=>node.isConnected&&node.textContent.includes(text.trim())}];
    panel.hidden=false;launch.setAttribute('aria-expanded','true');get('.zv-page').textContent='朗读千问回答';
    fillEntries(answerEntries);fitPanel();reader?.play();
  }
  doc.addEventListener('zili-read-answer',readAnswer);
  function endPicking(){picking=false;doc.querySelectorAll('.zv-read-target').forEach(node=>node.classList.remove('zv-read-target'));doc.body.classList.remove('zv-picking');get('.zv-pick').textContent='从这里朗读';}
  function pickText(event){
    if(!picking||host.contains(event.target))return;
    const selected=entries.findIndex(entry=>entry.node===event.target||entry.node?.contains(event.target));
    if(selected<0)return;event.preventDefault();event.stopImmediatePropagation();endPicking();
    panel.hidden=false;launch.setAttribute('aria-expanded','true');segments.value=String(selected);reader.select(selected);fitPanel();reader.play();
  }
  get('.zv-pick').onclick=()=>{
    if(picking){endPicking();return;}answerEntries=null;get('.zv-page').textContent='朗读本页原文';refresh();picking=true;
    entries.forEach(entry=>entry.node?.classList.add('zv-read-target'));doc.body.classList.add('zv-picking');
    get('.zv-pick').textContent='取消选择';status.textContent='请点击想开始朗读的正文段落。';
  };
  get('.zv-original').onclick=()=>{answerEntries=null;endPicking();get('.zv-page').textContent='朗读本页原文';refresh();reader?.play();};
  doc.addEventListener('click',pickText,true);
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
  function highlight(item){highlighted.forEach(node=>node.classList.remove('zili-voice-reading'));highlighted=item?.nodes||[];highlighted.forEach(node=>node.classList.add('zili-voice-reading'));}
  const reader=supported?createZiliStreamReader({Context:view.AudioContext||view.webkitAudioContext,openStream:(text,packet,signal)=>ziliOpenSpeechStream(text,get('.zv-language').value,packet,signal),onParagraph:highlight,onState:update}):null;
  function update({state,index,end,total,message}){
    currentState=state;
    play.textContent=(state==='playing'||state==='loading')?'暂停讲解':state==='paused'?'继续讲解':state==='ended'?'重新朗读':'开始讲解';
    play.setAttribute('aria-label',play.textContent);
    if(total&&index<total)segments.value=String(index);
    status.textContent=message||(state==='playing'?'正在讲解':state==='paused'?'已暂停':'准备就绪')+(total?' · 第 '+Math.min(index+1,total)+(end>index?'—'+(end+1):'')+' / '+total+' 段':'');
    segments.disabled=['playing','loading','paused'].includes(state);
  }
  function refresh(){
    fillEntries(answerEntries||collect());
    if(!entries.length)status.textContent='当前没有可朗读的正文，请先打开故事或查询汉字。';
  }
  function fitPanel(){
    if(panel.hidden)return;
    const button=launch.getBoundingClientRect();
    const spaceAbove=button.top-20,spaceBelow=view.innerHeight-button.bottom-20;
    panel.style.maxHeight=Math.max(120,Math.max(spaceAbove,spaceBelow))+'px';
    const box=panel.getBoundingClientRect();
    const left=Math.max(8,Math.min(button.right-box.width,view.innerWidth-box.width-8));
    let top=button.top-box.height-12;
    if(top<8)top=button.bottom+12;
    top=Math.max(8,Math.min(top,view.innerHeight-box.height-8));
    const hostBox=host.getBoundingClientRect();
    panel.style.left=(left-hostBox.left)+'px';panel.style.top=(top-hostBox.top)+'px';panel.style.right='auto';panel.style.bottom='auto';
  }
  function position(x,y,remember=true){
    const box=launch.getBoundingClientRect(),p=ziliClampVoicePosition(x,y,view.innerWidth,view.innerHeight,box.width,box.height);
    host.style.left=p.x+'px';host.style.top=p.y+'px';host.style.right='auto';host.style.bottom='auto';
    if(remember)ziliVoicePosition={x:p.x/Math.max(1,view.innerWidth-box.width),y:p.y/Math.max(1,view.innerHeight-box.height)};
    fitPanel();
  }
  function restorePosition(){
    if(ziliVoicePosition){const box=launch.getBoundingClientRect();position(ziliVoicePosition.x*(view.innerWidth-box.width),ziliVoicePosition.y*(view.innerHeight-box.height),false);}
    else fitPanel();
  }
  reset.onclick=()=>{ziliVoicePosition=null;for(const property of ['left','top','right','bottom'])host.style.removeProperty(property);fitPanel();};
  function pointerDown(event){
    if(event.button!==0||event.target.closest('button')&&event.target.closest('button')!==launch)return;
    const box=launch.getBoundingClientRect();drag={id:event.pointerId,startX:event.clientX,startY:event.clientY,x:box.left,y:box.top,moved:false};
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function pointerMove(event){
    if(!drag||event.pointerId!==drag.id)return;
    const dx=event.clientX-drag.startX,dy=event.clientY-drag.startY;
    if(Math.hypot(dx,dy)>6)drag.moved=true;
    if(drag.moved){event.preventDefault();position(drag.x+dx,drag.y+dy);}
  }
  function pointerUp(event){if(!drag||event.pointerId!==drag.id)return;if(drag.moved){suppressClick=true;view.setTimeout(()=>suppressClick=false,0);}drag=null;}
  for(const handle of [launch,get('header')]){handle.addEventListener('pointerdown',pointerDown);handle.addEventListener('pointermove',pointerMove);handle.addEventListener('pointerup',pointerUp);handle.addEventListener('pointercancel',()=>drag=null);}
  launch.addEventListener('keydown',event=>{
    if(event.key==='Home'){event.preventDefault();reset.click();return;}
    const delta={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,-10],ArrowDown:[0,10]}[event.key];
    if(delta){event.preventDefault();const box=launch.getBoundingClientRect();position(box.left+delta[0],box.top+delta[1]);}
  });
  function open(value){panel.hidden=!value;launch.setAttribute('aria-expanded',String(value));if(value&&supported&&!['playing','loading','paused'].includes(currentState)){refresh();prepareSelected();}fitPanel();}
  launch.onclick=event=>{if(suppressClick){event.preventDefault();return;}open(panel.hidden);};
  get('.zv-close').onclick=()=>{open(false);launch.focus();};
  host.addEventListener('keydown',e=>{if(e.key==='Escape'){open(false);launch.focus();}});
  function loadVoices(){
    const mode=get('.zv-language').value;
    voiceReady=true;
    const names={mandarin:'普通话 · Cherry',cantonese:'粤语 · Kiki',taiwan:'闽南语 · Roy'};
    get('.zv-voice').replaceChildren(new view.Option(names[mode],'cloud'));
    get('.zv-voice').disabled=true;
    languageNote.textContent=mode==='taiwan'?'云端闽南语音色 Roy；不是台湾普通话。方言表达和发音由模型生成，具体效果请试听。':mode==='cantonese'?'香港、澳门合并使用云端粤语音色 Kiki。':'云端普通话音色 Cherry。';
    play.disabled=!entries.length;get('.zv-next').disabled=get('.zv-restart').disabled=play.disabled;
    reader.configure(Number(get('.zv-rate').value));fitPanel();prepareSelected();
  }
  if(supported){
    loadVoices();
    get('.zv-language').onchange=()=>{reader.stop();ziliVoiceMode=get('.zv-language').value;loadVoices();};
    play.onclick=()=>{
      if(currentState==='playing'||currentState==='loading'){reader.pause();return;}
      if(currentState==='paused'){reader.play();return;}
      if(currentState==='ended'){refresh();reader.restart();return;}
      if(!voiceReady)return;
      const selected=Number(segments.value)||0;refresh();reader.select(selected);reader.play();
    };
    get('.zv-stop').onclick=()=>reader.stop();get('.zv-restart').onclick=()=>{refresh();reader.restart();};
    get('.zv-next').onclick=()=>{if(currentState==='ended'){refresh();reader.play();}else reader.next();};
    segments.onchange=()=>{reader.select(Number(segments.value));prepareSelected();};
    get('.zv-rate').onchange=()=>reader.configure(Number(get('.zv-rate').value));
  }else{
    status.textContent='当前浏览器不支持实时音频播放，请更换浏览器。';
    host.querySelectorAll('.zv-actions button,.zv-segments,.zv-rate,.zv-voice').forEach(control=>control.disabled=true);
  }
  const unload=()=>reader?.destroy();view.addEventListener('pagehide',unload);
  view.addEventListener('resize',restorePosition);view.visualViewport?.addEventListener('resize',restorePosition);
  const panelObserver=new view.ResizeObserver(fitPanel);panelObserver.observe(panel);restorePosition();
  ziliVoiceGuide={destroy(){endPicking();doc.removeEventListener('zili-read-answer',readAnswer);doc.removeEventListener('click',pickText,true);reader?.destroy();view.removeEventListener('pagehide',unload);view.removeEventListener('resize',restorePosition);view.visualViewport?.removeEventListener('resize',restorePosition);panelObserver.disconnect();host.remove();}};
}
