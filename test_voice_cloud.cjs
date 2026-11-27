const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context=vm.createContext({AbortController});
vm.runInContext(fs.readFileSync('voice-cloud.js','utf8'),context);
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function testSharedCache(){
 const handlers=new Set(),posts=[],saved=new Map();let id=0;
 const parent={postMessage:m=>posts.push(m)};
 const env=vm.createContext({AbortController,setTimeout,clearTimeout,crypto:{randomUUID:()=>String(++id)},parent,
   window:{addEventListener:(type,fn)=>handlers.add(fn),removeEventListener:(type,fn)=>handlers.delete(fn)},
   ziliReadAudio:async key=>saved.get(key)||null,ziliSaveAudio:async(key,audio)=>saved.set(key,audio)});
 vm.runInContext(fs.readFileSync('voice-cloud.js','utf8'),env);
 const a=new AbortController(),b=new AbortController();
 const first=env.ziliRequestCloudAudio('缓存测试','taiwan',a.signal).catch(error=>error);
 const second=env.ziliRequestCloudAudio('缓存测试','taiwan',b.signal);await flush();
 assert.equal(posts.length,1,'warmup and playback share one billable request');
 a.abort();assert.equal(posts.length,1,'one cancelled subscriber cannot abort another');
 for(const fn of [...handlers])fn({source:parent,data:{type:'qwen-response',id:posts[0].request.id,audio:'data:audio/wav;base64,AAAA'}});
 assert.equal(await second,'data:audio/wav;base64,AAAA');assert.match((await first).message,/取消/);
 vm.runInContext('ziliCloudAudioCache.clear()',env);
 assert.equal(await env.ziliRequestCloudAudio('缓存测试','taiwan',new AbortController().signal),'data:audio/wav;base64,AAAA');
 assert.equal(posts.length,1,'persistent browser cache prevents another server call');
}
function setup(request){
 const audios=[],states=[],marks=[];
 class Audio{constructor(){audios.push(this)}play(){this.onplaying?.();return Promise.resolve()}pause(){this.paused=true}removeAttribute(){}load(){}}
 const reader=context.createZiliCloudReader({requestAudio:request||(()=>Promise.resolve('data:audio/wav;base64,AAAA')),Audio,onState:s=>states.push(s),onParagraph:p=>marks.push(p)});
 return {reader,audios,states,marks};
}
(async()=>{
 await testSharedCache();
 {
  const {reader,audios,states,marks}=setup();reader.load([{text:'第一段。'},{text:'第二段。'}]);reader.play();await flush();
  assert.equal(states.at(-1).state,'playing');assert.equal(marks.at(-1).text,'第一段。');
  reader.pause();assert.equal(states.at(-1).state,'paused');reader.play();await flush();
  reader.configure(1.25);assert.equal(audios[0].playbackRate,1.25);
  audios[0].onended();await flush();assert.equal(audios.length,2);audios[1].onended();assert.equal(states.at(-1).state,'ended');reader.destroy();
 }
 {
  let resolve;const {reader,audios,states}=setup(()=>new Promise(r=>resolve=r));reader.load([{text:'未完成请求'}]);reader.play();reader.stop();resolve('audio');await flush();assert.equal(audios.length,0);assert.equal(states.at(-1).state,'idle');reader.destroy();
 }
 {
  let resolve;const {reader,audios,states}=setup(()=>new Promise(r=>resolve=r));reader.load([{text:'先暂停'}]);reader.play();reader.pause();resolve('audio');await flush();assert.equal(states.at(-1).state,'paused');assert.equal(audios.length,1);reader.play();await flush();assert.equal(states.at(-1).state,'playing');reader.destroy();
 }
 {
  const {reader,states}=setup(()=>Promise.reject(new Error('服务未授权')));reader.load([{text:'测试'}]);reader.play();await flush();assert.equal(states.at(-1).state,'error');assert.match(states.at(-1).message,/未授权/);reader.destroy();
 }
 console.log('PASS: real audio queue, continuity, pause during synthesis, rate, cancellation and service errors');
 console.log('PASS: deduplicated warmup/playback, independent cancellation and persisted clip reuse');
})().catch(error=>{console.error(error);process.exit(1)});
