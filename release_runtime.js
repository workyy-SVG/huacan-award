// Runs inside the release shell, with access to its page and collection state.
let navigationSequence = 0;
let routeRestoring = false;
let routeHost = window;
window.ziliFetchDictionary = async (form, signal) => {
  const key = 'zili-dictionary-v1:' + form;
  try {
    const response = await fetch('https://www.moedict.tw/uni/' + encodeURIComponent(form), {signal});
    if (response.status === 404) return response;
    if (!response.ok) throw Error('Dictionary unavailable');
    const entry = await response.json();
    if (signal.aborted) throw Error('Cancelled');
    if (entry.title !== form || !Array.isArray(entry.heteronyms)) throw Error('Invalid dictionary');
    try { localStorage.setItem(key, JSON.stringify(entry)); } catch {}
    return {ok:true,status:200,json:async()=>entry};
  } catch (error) {
    let entry;
    try { entry = JSON.parse(localStorage.getItem(key) || 'null'); } catch {}
    entry ||= window.ziliDictionaryCache?.[form];
    if (!entry) throw error;
    return {ok:true,status:200,fromCache:true,json:async()=>entry};
  }
};
try { if (window.top.location.origin === new URL(document.baseURI).origin) routeHost = window.top; } catch {}
function routeState(page, hash = '', tab = '') {
  return {page, hash, tab, traditionalUI};
}
function rememberRoute(page, hash = '', tab = '') {
  const route = routeState(page, hash, tab);
  try { sessionStorage.setItem('zili-navigation-v2', JSON.stringify(route)); } catch {}
  if (routeRestoring) return;
  try {
    const url = new URL(routeHost.location.href);
    const code = encodeURIComponent(JSON.stringify(route));
    if (url.hash === '#zili=' + code) return;
    url.hash = 'zili=' + code;
    routeHost.history.pushState({zili:route}, '', url);
  } catch {}
}
function restoreRoute() {
  let state;
  try {
    const hash = routeHost.location.hash;
    if (hash.startsWith('#zili=')) state = JSON.parse(decodeURIComponent(hash.slice(6)));
  } catch {}
  if (!state || !Object.hasOwn(pages, state.page)) return false;
  routeRestoring = true;
  try {
    traditionalUI = !!state.traditionalUI;
    navigate(state.page, typeof state.hash === 'string' ? state.hash : '', typeof state.tab === 'string' ? state.tab : '');
  } finally { routeRestoring = false; }
  return true;
}
routeHost.addEventListener('popstate', restoreRoute);

function manageCollection(doc, add) {
  const main = doc.querySelector('main');
  const tools = add(main, 'div');
  tools.id = 'collection-tools';
  tools.setAttribute('role', 'group');
  tools.setAttribute('aria-label', '管理收藏');
  main.insertBefore(tools, doc.getElementById('saved-count'));
  const status = add(tools, 'p');
  status.setAttribute('role', 'status');
  function persist() {
    try {
      localStorage.setItem(keepsakeKey, JSON.stringify(savedKeepsakes));
      return true;
    } catch {
      status.textContent = '浏览器无法保存更改，本次浏览已更新。';
      return false;
    }
  }
  function download(extension, text) {
    const url = URL.createObjectURL(new Blob([text], {type:'text/plain;charset=utf-8'}));
    const link = add(tools, 'a');
    link.href = url;
    link.download = '我的寻踪卡.' + extension;
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }
  const exportJSON = add(tools, 'button', '导出收藏备份');
  exportJSON.onclick = () => download('json', JSON.stringify({version:1,items:savedKeepsakes}, null, 2));
  const exportText = add(tools, 'button', '导出阅读笔记');
  exportText.onclick = () => download('txt', savedKeepsakes.map(item => [item.character+' · '+item.place,item.title,item.detail,item.source || ''].join('\n')).join('\n\n'));
  const label = add(tools, 'label', '导入收藏备份 ');
  const input = add(label, 'input');
  input.type = 'file'; input.accept = '.json,application/json';
  input.onchange = async () => {
    const file = input.files[0];
    if (!file || file.size > 1024 * 1024) { status.textContent = '请选择不超过 1 MB 的收藏备份。'; return; }
    try {
      const data = JSON.parse(await file.text());
      if (data.version !== 1 || !Array.isArray(data.items) || data.items.length > 200) throw Error();
      const imported = data.items.map(item => {
        if (!item || typeof item.id !== 'string' || !Object.hasOwn(pages,item.page) ||
            ![item.id,item.character,item.place,item.title,item.detail].every(value=>typeof value==='string' && value.length<=4000)) throw Error();
        return {id:item.id,page:item.page,character:item.character,place:item.place,title:item.title,detail:item.detail,
          image:typeof item.image==='string' && Object.hasOwn(images,item.image) ? item.image : '',
          source:typeof item.source==='string' && /^https?:\/\//.test(item.source) ? item.source : ''};
      });
      const merged = new Map(savedKeepsakes.map(item=>[item.page+':'+item.id,item]));
      for (const item of imported) merged.set(item.page+':'+item.id,item);
      if (merged.size>200) throw Error();
      savedKeepsakes = [...merged.values()];
      if (persist()) navigate(keepsakePage);
    } catch { status.textContent = '备份格式不正确，原有收藏未被覆盖。'; }
  };
  const cards = [...doc.querySelectorAll('#saved-cards > article')];
  cards.forEach((card,index) => {
    const item = savedKeepsakes[index];
    const remove = add(card.lastElementChild,'button','移除这条收藏');
    remove.onclick = () => {
      savedKeepsakes = savedKeepsakes.filter(entry=>entry.page!==item.page || entry.id!==item.id);
      if (persist()) navigate(keepsakePage);
      else { card.remove(); doc.getElementById('saved-count').textContent=savedKeepsakes.length+' 条已保存'; }
    };
  });
  bindLiveCollectionGuide(doc);
}

function bindShareLink(doc, page) {
  if (!isStory(page)) return;
  const link = doc.createElement('a');
  link.textContent = '打开此故事的分享链接 →';
  const url = new URL('https://zili-xunzong.streamlit.app/');
  url.searchParams.set('story',page.replace('.html',''));
  link.href = url.href; link.target = '_blank'; link.rel = 'noopener';
  (doc.querySelector('[data-source-notes]') || doc.querySelector('main')).append(link);
}
