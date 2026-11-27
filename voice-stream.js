function ziliSpeechGroups(items,start=0){
  const groups=[];let group={text:'',nodes:[],start,end:start};
  for(let i=start;i<items.length;i++){
    let rest=items[i].text;
    while(rest){
      const space=580-group.text.length-(group.text?1:0);
      if(space<1){groups.push(group);group={text:'',nodes:[],start:i,end:i};continue;}
      const part=rest.slice(0,space);rest=rest.slice(part.length);
      group.text+=(group.text?'\n':'')+part;group.end=i;
      if(items[i].node&&!group.nodes.includes(items[i].node))group.nodes.push(items[i].node);
      if(rest){groups.push(group);group={text:'',nodes:[],start:i,end:i};}
    }
  }
  if(group.text)groups.push(group);return groups;
}

function ziliOpenSpeechStream(text,language,onPacket,signal){
  const id=crypto.randomUUID();let last=0,finished=false;
  function cleanup(){clearTimeout(timer);window.removeEventListener('message',receive);signal.removeEventListener('abort',abort);}
  function fail(message){if(finished)return;finished=true;cleanup();onPacket({error:message});}
  function arm(){clearTimeout(timer);timer=setTimeout(()=>{parent.postMessage({type:'qwen-cancel',id},'*');fail('实时语音暂未返回，请重新开始。');},40000);}
  let timer;arm();
  function receive({source,data}){
    if(source!==parent||data?.type!=='qwen-response'||data.id!==id)return;
    if(data.error){fail(data.error);return;}
    if(!data.stream||!Number.isInteger(data.seq)||data.seq<=last)return;
    last=data.seq;arm();onPacket(data);
    if(data.done){finished=true;cleanup();}
  }
  function abort(){if(finished)return;finished=true;cleanup();parent.postMessage({type:'qwen-cancel',id},'*');}
  window.addEventListener('message',receive);signal.addEventListener('abort',abort,{once:true});
  if(signal.aborted){abort();return;}
  parent.postMessage({type:'qwen-request',request:{id,mode:'tts_stream',text,language}},'*');
}

function createZiliStreamReader({Context,openStream,onState,onParagraph}){
  let items=[],groups=[],groupIndex=0,index=0,state='idle',rate=1,context=null,controller=null;
  let token=0,nextTime=0,receiving=false,complete=false,scheduled=[],finishTimer=null,markTimers=[];
  function emit(message='',end){onState({state,index,end,total:items.length,message});}
  function ensureContext(){if(!context||context.state==='closed')context=new Context({sampleRate:24000,latencyHint:'interactive'});return context;}
  function cancel(){
    token++;controller?.abort();controller=null;clearTimeout(finishTimer);markTimers.forEach(clearTimeout);markTimers=[];
    scheduled.forEach(source=>{try{source.stop();}catch{}});scheduled=[];nextTime=0;receiving=false;complete=false;
  }
  function resetGroups(){groups=ziliSpeechGroups(items,index);groupIndex=0;}
  function completePlayback(current){
    clearTimeout(finishTimer);
    const tick=()=>{if(current!==token)return;if(state==='paused'){finishTimer=setTimeout(tick,100);return;}
      if(context.currentTime+0.025>=nextTime){state='ended';onParagraph(null);emit('本次朗读已完成。');}else finishTimer=setTimeout(tick,100);};tick();
  }
  function requestGroup(current){
    if(current!==token)return;
    if(groupIndex>=groups.length){complete=true;completePlayback(current);return;}
    const group=groups[groupIndex++];
    if(items.slice(group.start,group.end+1).some(item=>item.valid&&!item.valid())){cancel();state='idle';onParagraph(null);emit('正文已变化，请重新选择朗读内容。');return;}
    receiving=true;controller=new AbortController();let marked=false;
    openStream(group.text,packet=>{
      if(current!==token)return;
      if(packet.error){cancel();state='error';onParagraph(null);emit(packet.error);return;}
      if(packet.pcm){
        const raw=atob(packet.pcm);if(raw.length%2){cancel();state='error';emit('实时音频格式异常。');return;}
        const samples=raw.length/2,buffer=context.createBuffer(1,samples,24000),channel=buffer.getChannelData(0);
        for(let i=0;i<samples;i++){let value=raw.charCodeAt(i*2)|(raw.charCodeAt(i*2+1)<<8);if(value>=32768)value-=65536;channel[i]=value/32768;}
        const source=context.createBufferSource();source.buffer=buffer;source.playbackRate.value=rate;source.connect(context.destination);
        const start=Math.max(nextTime,context.currentTime+(nextTime?0.015:0.25));source.start(start);nextTime=start+samples/24000/rate;
        scheduled.push(source);source.onended=()=>{scheduled=scheduled.filter(item=>item!==source);};
        if(!marked){marked=true;const mark=()=>{if(current!==token)return;if(context.currentTime+0.015<start){markTimers.push(setTimeout(mark,50));return;}index=group.start;if(state!=='paused')state='playing';onParagraph(group);emit('',group.end);};markTimers.push(setTimeout(mark,Math.max(0,(start-context.currentTime)*1000)));}
      }
      if(packet.done){receiving=false;requestGroup(current);}
    },controller.signal);
  }
  function start(){
    if(!items.length){emit('当前没有可朗读的正文。');return;}
    cancel();resetGroups();ensureContext();const current=token;state='loading';emit('正在连接实时语音…');
    context.resume().then(()=>requestGroup(current)).catch(()=>{if(current===token){state='paused';emit('浏览器需要再次点击继续讲解才能播放。');}});
  }
  return {
    load(next,selected=0){cancel();items=next;index=Math.max(0,Math.min(selected,next.length-1));state='idle';onParagraph(null);emit();},
    play(){if(state==='paused'&&groups.length&&(receiving||scheduled.length||complete)){state='playing';context.resume();emit();return;}if(state==='ended')index=0;start();},
    pause(){if(!['playing','loading'].includes(state))return;state='paused';context?.suspend();emit();},
    stop(){cancel();state='idle';onParagraph(null);emit('已停止。');},
    select(next){cancel();index=Math.max(0,Math.min(next,items.length-1));state='idle';onParagraph(null);emit();},
    next(){index=Math.min(index+1,items.length);start();},
    restart(){index=0;start();},
    configure(nextRate){if(nextRate===rate)return;rate=nextRate;if(state==='playing'||state==='loading'){start();}},
    destroy(){cancel();context?.close();context=null;onParagraph(null);}
  };
}
