// Verify queue completion, stale browser events, pause/resume and error handling.
const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const context=vm.createContext({setTimeout,clearTimeout});
vm.runInContext(readFileSync('voice-assistant.js','utf8'),context);
function setup(){
  const spoken=[],states=[],highlights=[];
  const synth={paused:false,speak(u){spoken.push(u)},cancel(){},pause(){this.paused=true},resume(){this.paused=false}};
  const reader=context.createZiliReader({synth,Utterance:function(text){this.text=text},onState:s=>states.push(s),onParagraph:p=>highlights.push(p)});
  return {reader,synth,spoken,states,highlights};
}
{
  const {reader,spoken,states,highlights}=setup();
  reader.load([{text:'第一段。'},{text:'第二段。'}]);reader.play();
  assert.equal(spoken.length,1);spoken[0].onstart();assert.equal(highlights.at(-1).text,'第一段。');
  spoken[0].onend();assert.equal(spoken.length,2);spoken[1].onstart();spoken[1].onend();
  assert.equal(states.at(-1).state,'ended');assert.equal(highlights.at(-1),null);reader.destroy();
}
{
  const {reader,spoken,states,synth}=setup();reader.load([{text:'一'.repeat(260)}]);reader.play();spoken[0].onstart();
  assert.equal(spoken[0].text.length,100);reader.pause();assert.equal(synth.paused,true);assert.equal(states.at(-1).state,'paused');
  reader.play();assert.equal(synth.paused,false);assert.equal(spoken.length,1);
  spoken[0].onend();assert.equal(spoken[1].text.length,100);reader.configure(1.25,null);
  const n=spoken.length;spoken[1].onend();assert.equal(spoken.length,n,'cancelled callback cannot advance new queue');
  assert.equal(spoken.at(-1).rate,1.25);reader.destroy();spoken.at(-1).onend();assert.equal(spoken.length,n);
}
{
  const {reader,spoken,states}=setup();reader.load([{text:'语音权限测试'}]);reader.play();spoken[0].onerror({error:'not-allowed'});
  assert.equal(states.at(-1).state,'error');assert.match(states.at(-1).message,/未允许/);reader.destroy();
}
{
  const {reader,spoken,states}=setup();reader.load([{text:'已隐藏内容',valid:()=>false}]);reader.play();assert.equal(spoken.length,0);assert.match(states.at(-1).message,/内容已变化/);
  reader.load([]);reader.play();assert.equal(spoken.length,0);assert.match(states.at(-1).message,/没有可朗读/);reader.destroy();
}
console.log('PASS: speech sequencing, chunking, pause/resume, stale events, settings, permissions, navigation cleanup and empty content');
