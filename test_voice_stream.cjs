const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const timers=new Map();let timerId=0;
const context=vm.createContext({AbortController,atob,setTimeout:fn=>{timers.set(++timerId,fn);return timerId},clearTimeout:id=>timers.delete(id)});
vm.runInContext(fs.readFileSync('voice-stream.js','utf8'),context);
const groups=context.ziliSpeechGroups([{text:'第一句'},{text:'第二句'},{text:'字'.repeat(1000)}]);
assert.ok(groups.every(group=>group.text.length<=580));assert.equal(groups[0].start,0);
assert.equal(groups.map(group=>group.text).join('').replaceAll('\n',''),'第一句第二句'+'字'.repeat(1000));
const clocks=[],sources=[],packets=[],states=[];
class AudioContext{
 constructor(){this.currentTime=0;clocks.push(this);this.state='running';this.destination={}}
 resume(){this.state='running';return Promise.resolve()}suspend(){this.state='suspended'}close(){this.state='closed'}
 createBuffer(channels,length,rate){return {duration:length/rate,getChannelData:()=>new Float32Array(length)}}
 createBufferSource(){const source={playbackRate:{value:1},connect(){},start(time){this.time=time},stop(){this.stopped=true}};sources.push(source);return source}
}
const reader=context.createZiliStreamReader({Context:AudioContext,openStream:(text,callback,signal)=>packets.push({text,callback,signal}),onState:s=>states.push(s),onParagraph:()=>{}});
(async()=>{
 reader.load([{text:'第一段'},{text:'第二段'}]);reader.play();await Promise.resolve();
 assert.equal(packets.length,1,'short adjacent paragraphs must share one synthesis request');assert.match(packets[0].text,/第一段\n第二段/);
 const pcm=Buffer.alloc(4800).toString('base64');packets[0].callback({pcm,done:false});packets[0].callback({pcm,done:false});
 assert.equal(sources[1].time,sources[0].time+0.1,'PCM chunks are scheduled adjacently without per-sentence gaps');
 reader.pause();assert.equal(clocks[0].state,'suspended');reader.play();assert.equal(clocks[0].state,'running');
 reader.stop();assert.ok(sources.every(source=>source.stopped));const count=sources.length;packets[0].callback({pcm,done:true});assert.equal(sources.length,count,'stale packets after stop cannot play');
 reader.destroy();assert.equal(clocks[0].state,'closed');
 console.log('PASS: grouped text preservation, adjacent PCM scheduling, pause/resume and late-packet cancellation');
})().catch(error=>{console.error(error);process.exit(1)});
