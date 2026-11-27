function bindLiveCollectionGuide(doc) {
  const guide=doc.querySelector('.track-guide');
  if(!guide)return;
  if(guide.dataset.liveGuide){guide.refreshCollection?.();return;}
  const entries=[];
  for(const page of ['nian.html','men.html','cha.html','chuan.html','deng.html','yuan.html']){
    const source=new DOMParser().parseFromString(pages[page],'text/html');
    const node=source.getElementById('records');
    if(!node)continue;
    for(const record of JSON.parse(node.textContent))entries.push({record,page,character:source.body.dataset.character||({nian:'年',men:'门',cha:'茶',chuan:'船',deng:'灯',yuan:'圆'})[page.split('.')[0]]});
  }
  if(!entries.length)return;
  guide.dataset.liveGuide='true';
  guide.innerHTML='<p><b>从真实故事开始，完成一次收藏。</b> 选取本站记录，保存后即可在下方看到自己的收藏。</p><ol><li><strong>选一则故事</strong><label>本站故事<select aria-label="选择要收藏的真实故事"></select></label><img class="live-story-image" alt=""><b class="live-story-title"></b><a class="live-story-link">打开这则故事 →</a><small>配图沿用本站场景示意。</small></li><li><strong>保存寻踪记录</strong><div class="live-record-preview"><small>当前选择</small><h3></h3><p></p></div><button type="button" class="live-save">保存这则故事</button><p class="live-save-status" role="status"></p></li><li><strong>翻开收藏</strong><p class="live-collection-count" role="status"></p><div class="live-collection-preview"></div><a href="#saved-cards" class="live-view-collection">查看下方真实收藏 ↓</a></li></ol><small>实际读取本站故事和当前浏览器收藏。更换浏览器或清除数据后，收藏不会自动同步。</small>';
  const select=guide.querySelector('select'),status=guide.querySelector('.live-save-status');
  entries.forEach((entry,i)=>select.add(new Option(entry.character+' · '+entry.record.place+'｜'+(entry.record.short||entry.record.title),String(i))));
  select.value=String(Math.max(0,entries.findIndex(entry=>entry.record.id==='nian-jinmen')));
  function imageName(entry){return entry.record.image||entry.record.id+'.webp';}
  function updateSelection(){
    const entry=entries[Number(select.value)];
    const name=imageName(entry);
    const image=guide.querySelector('.live-story-image');
    image.src=window.ziliImage(name);image.alt=entry.record.place+' · '+entry.record.title+'（站内场景示意）';
    guide.querySelector('.live-story-title').textContent=entry.record.place+'｜'+entry.record.title;
    guide.querySelector('.live-story-link').href=entry.page+'#'+entry.record.id;
    guide.querySelector('.live-record-preview h3').textContent=entry.character+' · '+entry.record.place;
    guide.querySelector('.live-record-preview p').textContent=entry.record.recorded_action||entry.record.body;
    status.textContent='';
  }
  guide.refreshCollection=()=>{
    guide.querySelector('.live-collection-count').textContent='当前浏览器实际收藏：'+savedKeepsakes.length+' 条';
    const preview=guide.querySelector('.live-collection-preview');preview.replaceChildren();
    const item=savedKeepsakes[0];
    if(item){
      const title=doc.createElement('b');title.textContent=item.character+' · '+item.place;
      const text=doc.createElement('p');text.textContent=item.title;
      const link=doc.createElement('a');link.textContent='回到这条已保存的故事 →';link.href=item.page+'#'+item.id;
      preview.append(title,text,link);
    }else{
      const empty=doc.createElement('p');empty.textContent='还没有收藏。完成第二步后，这里会显示刚保存的真实记录。';preview.append(empty);
    }
  };
  select.onchange=updateSelection;
  guide.querySelector('.live-save').onclick=()=>{
    const entry=entries[Number(select.value)],record=entry.record;
    const item={id:record.id,page:entry.page,character:entry.character,place:record.place,title:record.title,detail:record.recorded_action||record.body,image:imageName(entry),source:record.source_url||record.source||''};
    savedKeepsakes=[item,...savedKeepsakes.filter(old=>old.id!==item.id||old.page!==item.page)];
    let persistent=true;
    try{localStorage.setItem(keepsakeKey,JSON.stringify(savedKeepsakes));}catch{persistent=false;}
    doc.getElementById('saved-cards').replaceChildren();
    doc.getElementById('collection-tools')?.remove();
    renderKeepsakes(doc);
    status.textContent=persistent?'已保存到当前浏览器，下方收藏已更新。':'已加入本次浏览；浏览器存储不可用，请导出备份。';
  };
  updateSelection();guide.refreshCollection();
}
