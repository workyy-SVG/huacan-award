// Public page narration only; bounded, expiring audio cache survives page refreshes.
let ziliAudioDBPromise;
function ziliAudioDB(){
  if(typeof indexedDB==='undefined')return Promise.resolve(null);
  return ziliAudioDBPromise||=new Promise(resolve=>{
    const request=indexedDB.open('zili-cloud-narration-v1',1);
    request.onupgradeneeded=()=>{const store=request.result.createObjectStore('clips',{keyPath:'key'});store.createIndex('updated','updated');};
    request.onsuccess=()=>resolve(request.result);request.onerror=()=>resolve(null);request.onblocked=()=>resolve(null);
  });
}
async function ziliReadAudio(key){
  try{const db=await ziliAudioDB();if(!db)return null;return await new Promise(resolve=>{
    const req=db.transaction('clips').objectStore('clips').get(key);
    req.onsuccess=()=>resolve(req.result&&Date.now()-req.result.updated<7*86400000?req.result.audio:null);req.onerror=()=>resolve(null);
  });}catch{return null;}
}
async function ziliSaveAudio(key,audio){
  try{const db=await ziliAudioDB();if(!db)return;
    const tx=db.transaction('clips','readwrite'),store=tx.objectStore('clips');store.put({key,audio,updated:Date.now()});
    const req=store.index('updated').openCursor(null,'prev');let count=0,bytes=0;
    req.onsuccess=()=>{const cursor=req.result;if(!cursor)return;count++;bytes+=cursor.value.audio.length;
      if(count>96||bytes>32*1024*1024||Date.now()-cursor.value.updated>7*86400000)cursor.delete();cursor.continue();};
    tx.onerror=()=>{};
  }catch{/* Private browsing or full storage must never prevent playback. */}
}
