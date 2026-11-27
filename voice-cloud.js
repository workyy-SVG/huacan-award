const ziliCloudAudioCache=new Map();
const ziliCloudPending=new Map();
function ziliRememberAudio(key,audio){
  ziliCloudAudioCache.delete(key);ziliCloudAudioCache.set(key,audio);
  let bytes=0;for(const clip of ziliCloudAudioCache.values())bytes+=clip.length;
  while(ziliCloudAudioCache.size>96||bytes>32*1024*1024){const oldest=ziliCloudAudioCache.keys().next().value;bytes-=ziliCloudAudioCache.get(oldest).length;ziliCloudAudioCache.delete(oldest);}
}
async function ziliRequestCloudAudio(text,language,signal){
  const key='qwen3-tts-flash-v1\0'+language+'\0'+text;
  if(signal.aborted)throw new Error('讲解已取消。');
  if(ziliCloudAudioCache.has(key))return ziliCloudAudioCache.get(key);
  const stored=await ziliReadAudio(key);
  if(signal.aborted)throw new Error('讲解已取消。');
  if(stored){ziliRememberAudio(key,stored);return stored;}
  let pending=ziliCloudPending.get(key);
  if(!pending){
    const controller=new AbortController();pending={controller,users:0};
    pending.promise=ziliFetchCloudAudio(text,language,controller.signal).then(audio=>{ziliRememberAudio(key,audio);ziliSaveAudio(key,audio);return audio;}).finally(()=>{if(ziliCloudPending.get(key)===pending)ziliCloudPending.delete(key);});
    ziliCloudPending.set(key,pending);
  }
  pending.users++;
  return new Promise((resolve,reject)=>{
    let settled=false;
    const finish=(error,audio)=>{if(settled)return;settled=true;signal.removeEventListener('abort',abort);pending.users--;if(error)reject(error);else resolve(audio);};
    const abort=()=>{finish(new Error('讲解已取消。'));if(!pending.users){ziliCloudPending.delete(key);pending.controller.abort();}};
    signal.addEventListener('abort',abort,{once:true});
    pending.promise.then(audio=>finish(null,audio),error=>finish(error));
    if(signal.aborted)abort();
  });
}
function ziliFetchCloudAudio(text,language,signal){
  return new Promise((resolve,reject)=>{
    const id=crypto.randomUUID();let done=false;
    const cleanup=()=>{clearTimeout(timeout);window.removeEventListener('message',receive);signal.removeEventListener('abort',abort);};
    const finish=(error,audio)=>{if(done)return;done=true;cleanup();if(error)reject(error);else resolve(audio);};
    const abort=()=>{parent.postMessage({type:'qwen-cancel',id},'*');finish(new Error('讲解已取消。'));};
    const timeout=setTimeout(()=>{parent.postMessage({type:'qwen-cancel',id},'*');finish(new Error('云端语音超时，请稍后重新开始。'));},40000);
    function receive({source,data}){
      if(source!==parent||data?.type!=='qwen-response'||data.id!==id)return;
      if(data.error){finish(new Error(data.error));return;}
      if(typeof data.audio!=='string'||!/^data:audio\/wav;base64,[A-Za-z0-9+/=]+$/.test(data.audio)){finish(new Error('云端未返回有效音频。'));return;}
      finish(null,data.audio);
    }
    window.addEventListener('message',receive);signal.addEventListener('abort',abort,{once:true});
    if(signal.aborted){abort();return;}
    parent.postMessage({type:'qwen-request',request:{id,mode:'tts',text,language}},'*');
  });
}

function createZiliCloudReader({requestAudio,Audio,onState,onParagraph}){
  let items=[],index=0,offset=0,token=0,audio=null,controller=null,prefetch=null,state='idle',rate=1;
  function emit(message=''){onState({state,index,total:items.length,message});}
  function cancel(){token++;controller?.abort();controller=null;prefetch?.abort();prefetch=null;if(audio){audio.onended=audio.onerror=audio.onplaying=null;audio.pause();audio.removeAttribute('src');audio.load();audio=null;}}
  function finish(next,message){cancel();state=next;onParagraph(null);emit(message);}
  async function playAudio(current){
    try{await audio.play();}catch(error){if(current!==token)return;state='paused';emit(error.name==='NotAllowedError'?'音频已生成，浏览器需要你再点击一次「继续讲解」播放。':'音频暂时无法播放，请重新开始。');}
  }
  async function speak(){
    if(index>=items.length){finish('ended','本页讲解已完成。');return;}
    const item=items[index];if(item.valid&&!item.valid()){finish('idle','页面内容已变化，请重新选择段落。');return;}
    const rest=item.text.slice(offset),chunk=rest.match(/^[\s\S]{1,279}(?:[。！？；\n]|$)/)?.[0]||rest.slice(0,280);
    const current=token;controller=new AbortController();state='loading';onParagraph(null);emit('云端正在合成语音 · 第 '+(index+1)+' / '+items.length+' 段');
    try{
      const source=await requestAudio(chunk,controller.signal);if(current!==token)return;
      audio=new Audio();audio.src=source;audio.playbackRate=rate;
      let prepared=false;
      audio.onplaying=()=>{if(current!==token)return;state='playing';onParagraph(item);emit();
        if(!prepared){prepared=true;const nextOffset=offset+chunk.length,nextIndex=nextOffset>=item.text.length?index+1:index;
          const nextItem=items[nextIndex];if(nextItem&&(!nextItem.valid||nextItem.valid())){
            const nextText=nextItem.text.slice(nextIndex===index?nextOffset:0),nextChunk=nextText.match(/^[\s\S]{1,279}(?:[。！？；\n]|$)/)?.[0]||nextText.slice(0,280);
            prefetch?.abort();prefetch=new AbortController();requestAudio(nextChunk,prefetch.signal).catch(()=>{});
          }
        }
      };
      audio.onerror=()=>{if(current===token)finish('error','云端音频无法播放，请重新开始。');};
      audio.onended=()=>{if(current!==token)return;offset+=chunk.length;if(offset>=item.text.length){index++;offset=0;}audio=null;if(state==='playing')speak();};
      if(state!=='paused')await playAudio(current);
    }catch(error){if(current===token)finish('error',error.message||'云端语音暂时不可用。');}
  }
  return {
    load(next,selected=0){cancel();items=next;index=Math.max(0,Math.min(selected,items.length-1));offset=0;state='idle';onParagraph(null);emit();},
    play(){if(!items.length){emit('当前没有可朗读的正文。');return;}if(state==='paused'){if(audio)playAudio(token);else{state='loading';emit('继续等待云端语音…');}return;}if(state==='ended'){index=0;offset=0;}cancel();speak();},
    pause(){if(!['playing','loading'].includes(state))return;state='paused';audio?.pause();emit();},
    stop(){finish('idle','已停止。');offset=0;},
    select(next){cancel();index=Math.max(0,Math.min(next,items.length-1));offset=0;state='idle';onParagraph(null);emit();},
    next(){cancel();offset=0;index++;speak();},
    restart(){cancel();index=0;offset=0;speak();},
    configure(nextRate){rate=nextRate;if(audio)audio.playbackRate=rate;},
    destroy(){cancel();state='idle';onParagraph(null);}
  };
}
