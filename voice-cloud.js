const ziliCloudAudioCache=new Map();
function ziliRequestCloudAudio(text,language,signal){
  const key=language+'\0'+text;
  if(ziliCloudAudioCache.has(key))return Promise.resolve(ziliCloudAudioCache.get(key));
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
      ziliCloudAudioCache.set(key,data.audio);while(ziliCloudAudioCache.size>12)ziliCloudAudioCache.delete(ziliCloudAudioCache.keys().next().value);
      finish(null,data.audio);
    }
    window.addEventListener('message',receive);signal.addEventListener('abort',abort,{once:true});
    if(signal.aborted){abort();return;}
    parent.postMessage({type:'qwen-request',request:{id,mode:'tts',text,language}},'*');
  });
}

function createZiliCloudReader({requestAudio,Audio,onState,onParagraph}){
  let items=[],index=0,offset=0,token=0,audio=null,controller=null,state='idle',rate=1;
  function emit(message=''){onState({state,index,total:items.length,message});}
  function cancel(){token++;controller?.abort();controller=null;if(audio){audio.onended=audio.onerror=audio.onplaying=null;audio.pause();audio.removeAttribute('src');audio.load();audio=null;}}
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
      audio.onplaying=()=>{if(current!==token)return;state='playing';onParagraph(item);emit();};
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
