"""Render the six-character website with its assets bundled into Streamlit."""
import base64
import gzip
import json
import mimetypes
from pathlib import Path
import re
import hashlib
import logging
from time import time

from io import BytesIO

from PIL import Image
import streamlit as st
from streamlit.components.v1 import declare_component, html as render_html

from qwen_live import answer as qwen_answer, validate_request, PROMPT_VERSION, config

ROOT = Path(__file__).resolve().parent
# Region navigation is provided by the fixed Streamlit sidebar.
PAGES = ("index.html", "featured.html", "regions.html", "nian.html",
         "men.html", "cha.html", "chuan.html", "deng.html", "yuan.html")


def site_version():
    names = {*PAGES, "cases.json", "style.css", "app.js", "demo.js", "unihan-variants.gz.b64", "featured-strokes.json",
             "hanzi-writer.min.js", "zili-strokes.js", "zili-lookup-results.js"}
    # Include the regional gallery page in the cache fingerprint.
    # Story pages include their inline lookup panels in the cached site bundle.
    return tuple(
        (path.name, info.st_mtime_ns, info.st_size)
        for path in sorted(ROOT.iterdir())
        if path.is_file() and (path.name in names or path.suffix.lower() in (".webp", ".png", ".jpg"))
        for info in (path.stat(),)
    )


def enrich_lookup(page):
    """Add local Unihan candidates to the existing dictionary query."""
    page = page.replace(
        "const [form, storyUrl] = entries[word] ?? [word];",
        """const [preferred, storyUrl] = entries[word] ?? [word];
  const variants = parent.ziliVariants?.[word] ?? [];
  const candidates = [...new Set([word, preferred, ...variants])].slice(0, 4);
  let form = word;
  document.dispatchEvent(new CustomEvent('zili:lookup', {detail:word}));""",
    )
    page = page.replace("const word = input.value.trim();", """const word = input.value.trim();
  document.dispatchEvent(new CustomEvent('zili:lookup', {detail:null}));""")
    old_request = "const response = await fetch('https://www.moedict.tw/uni/' + encodeURIComponent(form), {signal:controller.signal});"
    page = page.replace(old_request, """let response;
    for (const candidate of candidates) {
      form = candidate;
      response = await fetch('https://www.moedict.tw/uni/' + encodeURIComponent(form), {signal:controller.signal});
      if (response.status !== 404) break;
    }""")
    return page.replace(
        "if (!response.ok) throw new Error('Dictionary request failed');",
        """if (!response.ok) throw new Error('Dictionary request failed');
    source.href = 'https://www.moedict.tw/' + encodeURIComponent(form);""",
    ).replace(
        """entry.stroke_count].filter(Boolean)""",
        """entry.stroke_count, variants.length && '关联字形（Unihan） ' + variants.join('、')].filter(Boolean)""",
    )


@st.cache_data(show_spinner=False)
def bundle_site(version):
    def image_url(name):
        path = ROOT / name
        if path.parent != ROOT or not path.is_file():
            return name
        mime = mimetypes.guess_type(name)[0]
        if not mime or not mime.startswith("image/"):
            return name
        data = path.read_bytes()
        if name == "globe-cover-reference.png":
            with Image.open(path) as cover:
                buffer = BytesIO()
                cover.convert("RGB").save(buffer, format="JPEG", quality=92, optimize=True)
                data = buffer.getvalue()
                mime = "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")

    def json_script(value):
        return json.dumps(value, ensure_ascii=False).replace("<", r"\u003c")

    catalogue = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    variants = json.loads(gzip.decompress(base64.b64decode((ROOT / "unihan-variants.gz.b64").read_bytes())))
    strokes = json.loads((ROOT / "featured-strokes.json").read_text(encoding="utf-8"))
    stroke_library = (ROOT / "hanzi-writer.min.js").read_text(encoding="utf-8")
    stroke_ui = (ROOT / "zili-strokes.js").read_text(encoding="utf-8")
    story_switch_style = """<style>
.story-title-row{display:flex;flex-wrap:wrap;align-items:center;column-gap:clamp(12px,2.4vw,34px);row-gap:6px;margin-bottom:6px}
.story-title-row .brand{margin:0}
header .story-word-switch{display:flex;flex:0 1 auto;justify-content:flex-start;flex-wrap:wrap;gap:7px;width:auto;margin:0;padding:0}
header .story-word-switch a{display:grid;place-items:center;min-width:40px;min-height:44px;padding:2px 8px;border:1px solid #d6b995;border-radius:7px;background:#fcf4e6;color:#79271a;font:700 1.35rem/1 KaiTi,serif;text-decoration:none}
header .story-word-switch a[aria-current="page"],header .story-word-switch a:hover{background:#8c291e;border-color:#8c291e;color:#fff8eb}
header .story-word-switch a:focus-visible{outline:2px solid #8c291e;outline-offset:2px}
</style>"""
    story_words = dict(zip(PAGES[3:], "年门茶船灯圆"))
    keepsake_style = """<style>
#keepsake-status:not(:empty), #keepsake-collection-link:not([hidden]) { margin-top: 8px; }
#keepsake-collection-link:not([hidden]) { display: block; font-weight: 700; }
#keepsake .keepsake { min-height: clamp(290px, 26vw, 360px); }
@media (max-width: 540px) {
  #keepsake .keepsake { min-height: 240px; }
}
</style>"""
    observation_style = """<style>
#form .observation .glyph {
  width: clamp(118px, 20vw, 224px);
  font-size: clamp(4.6rem, 11.2vw, 9.4rem);
}
#form .observation p {
  color: #2d2119;
  font-size: clamp(1rem, 1.6vw, 1.25rem);
  font-weight: 500;
  line-height: 1.65;
  margin: 0 0 .65em;
}
#form .observation #open-glyph {
  color: #702117;
  font-size: clamp(1rem, 1.45vw, 1.125rem);
  font-weight: 700;
  min-height: 44px;
}
@media (min-width: 720px) {
  #form .observation .glyph { position: relative; left: -22px; }
}
@media (max-width: 540px) {
  #form .observation { grid-template-columns: 118px minmax(0, 1fr); }
}
</style>"""
    stroke_style = '<style>.stroke-preview{border-top:1px solid #decdb4;margin-top:14px;padding:12px 0}.stroke-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.stroke-controls select{font:inherit;padding:4px}.stroke-board{width:184px;height:184px;margin:10px auto;background:#fffaf2;border:1px solid #d8c1a5;border-radius:8px}.stroke-status{margin:5px 0!important}.stroke-preview small{color:#695849}</style>'
    history_ui = r"""<style>
.character-history{margin-top:12px}.character-history button{min-height:44px;padding:5px 12px;border:1px solid #b4896a;background:#fff7e9;color:#80271b;border-radius:8px;font:inherit;cursor:pointer}
.character-history dialog{position:fixed;inset:0;margin:auto;box-sizing:border-box;width:min(94vw,590px);max-height:92dvh;overflow:auto;border:1px solid #c4a17e;border-radius:16px;padding:clamp(12px,3vw,20px);background:#f9f0df;color:#39281d}
.character-history dialog::backdrop{background:#291b146b}
.character-history dialog header,.character-history .controls{position:static;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;background:none;padding:0;border:0}
.character-history dialog h2{margin:0;font:700 1.5rem KaiTi,serif;color:#84291c}
.character-history .screen{background:#f5e9d6;border:1px solid #d6bea1;border-radius:10px;text-align:center;padding:12px}
.character-history .screen svg{width:100%;height:clamp(140px,32vh,245px);display:block}
.character-history .stage{color:#86291d;font-weight:700}.character-history .steps{margin:10px 0;display:flex;gap:6px;flex-wrap:wrap}
.character-history button[aria-current=true],.character-history #history-play{background:#86291d;color:#fff}
.character-history progress{width:100%;accent-color:#86291d}
.character-history .note{font-size:.9rem;color:#744834;margin-top:8px}
.character-history a{color:#80271b}
</style><script>(() => {
function initializeOtherWord(block, word) {
const raw = {"圆":[[[192,757],[222,724],[236,647],[232,320],[212,91],[216,8]],[[257,737],[281,722],[549,762],[739,781],[769,771],[792,748],[801,732],[799,414],[810,138],[806,86],[795,46],[800,-17]],[[361,672],[392,642],[420,528]],[[412,670],[426,660],[587,693],[612,668],[597,624],[578,613]],[[434,566],[444,559],[576,585],[624,580]],[[369,496],[387,477],[395,452],[397,366],[386,283],[389,251]],[[412,486],[423,478],[452,481],[578,512],[613,499],[624,482],[621,427],[628,320],[622,260]],[[466,433],[483,426],[507,400],[496,281],[477,219],[443,166],[414,142],[357,116],[333,113]],[[554,231],[635,173],[653,137]],[[244,28],[267,43],[693,74],[738,69],[751,75]]],"圓":[[[175,765],[198,740],[210,716],[218,654],[209,263],[186,57],[192,-2]],[[242,743],[264,729],[447,763],[731,796],[765,784],[786,763],[796,748],[791,657],[796,413],[812,130],[810,78],[797,31],[804,-37]],[[334,687],[364,660],[396,548]],[[387,682],[408,678],[557,713],[577,710],[599,686],[578,635],[557,625]],[[410,581],[419,574],[544,597],[603,592]],[[331,518],[354,493],[358,478],[357,316],[352,291],[357,232]],[[379,502],[389,494],[569,534],[590,528],[613,507],[618,499],[613,415],[617,333],[610,242]],[[384,409],[389,419],[480,438],[533,437]],[[383,333],[391,344],[476,360],[518,366],[537,361]],[[378,246],[391,258],[403,255],[443,266],[547,278],[567,282],[579,292]],[[452,185],[425,183],[357,123],[292,90]],[[534,207],[616,156],[636,120]],[[222,15],[245,31],[655,63],[743,61]]],"灯":[[[169,579],[170,496],[156,409]],[[439,672],[453,637],[355,560],[345,558],[342,542]],[[259,787],[288,769],[311,744],[310,530],[292,333],[260,228],[224,166],[170,114],[107,79]],[[323,343],[405,277],[430,234]],[[482,565],[531,559],[648,585],[852,616],[934,600]],[[676,561],[707,542],[722,514],[729,139],[722,95],[703,62],[655,74],[572,114]]],"燈":[[[139,539],[147,466],[139,377]],[[336,615],[350,590],[317,547],[289,525],[277,501]],[[207,763],[255,723],[254,534],[231,286],[202,187],[175,135],[122,76],[51,30]],[[259,287],[322,240],[348,201]],[[430,709],[469,716],[527,740],[547,740],[563,724],[535,634],[493,550],[446,481],[400,428],[333,377]],[[426,633],[462,599],[471,567]],[[752,798],[721,797],[673,730],[647,704],[650,696]],[[799,758],[812,722],[770,683],[705,637]],[[597,698],[606,702],[619,693],[738,567],[851,476],[900,465],[983,460]],[[492,445],[570,445],[658,468],[700,467]],[[448,351],[472,334],[482,316],[512,206]],[[500,351],[508,342],[526,341],[670,372],[692,369],[722,339],[703,291],[677,274]],[[528,223],[543,233],[675,249],[730,243]],[[479,166],[535,118],[546,87]],[[686,226],[703,208],[711,187],[659,90],[633,73]],[[342,32],[396,22],[543,43],[816,65],[852,62],[903,44]]],"船":[[[377,800],[391,793],[411,770],[362,682],[322,622],[308,611]],[[232,613],[252,599],[268,577],[272,421],[263,302],[220,140],[183,58],[142,-6]],[[297,599],[310,594],[417,627],[436,623],[457,598],[453,542],[458,141],[452,48],[435,16],[408,23],[338,58]],[[334,513],[366,469],[372,450]],[[64,322],[119,301],[413,379],[428,392]],[[315,284],[358,229],[361,203]],[[564,655],[596,631],[603,614],[606,549],[600,481],[590,440],[570,398],[538,360],[513,343]],[[623,649],[643,639],[746,669],[765,664],[778,649],[755,571],[750,516],[751,468],[771,429],[797,418],[838,414],[918,430],[960,424]],[[528,264],[552,244],[562,224],[596,4]],[[585,260],[593,252],[608,251],[782,284],[802,283],[816,275],[843,245],[803,123],[775,103]],[[617,47],[628,59],[774,77],[820,77],[843,68]]],"茶":[[[213,662],[259,656],[323,660],[441,681],[727,715],[788,711],[823,697]],[[336,778],[359,768],[379,748],[408,597]],[[616,833],[632,823],[650,791],[580,603]],[[514,577],[484,571],[398,460],[306,374],[214,304],[115,249]],[[527,555],[531,542],[547,526],[620,463],[710,395],[779,355],[839,341],[971,331]],[[315,283],[355,275],[414,278],[624,320],[675,318]],[[470,435],[515,389],[512,61],[493,23],[443,42],[390,73]],[[338,173],[307,112],[249,33]],[[623,195],[737,105],[758,75],[769,39]]],"門":[[[207,736],[243,696],[252,611],[251,453],[239,243],[215,101],[215,46]],[[279,712],[291,704],[342,721],[418,731],[448,702],[426,507],[416,478],[400,477]],[[278,570],[284,582],[304,591],[329,595],[361,590]],[[271,466],[284,481],[345,495],[388,497]],[[579,786],[610,752],[616,729],[618,559],[629,490]],[[641,765],[654,754],[787,786],[807,780],[835,752],[835,69],[815,35],[785,43],[706,84]],[[645,627],[658,637],[714,647],[755,643]],[[648,512],[660,523],[760,539],[792,535],[800,524]]],"门":[[[304,770],[373,704],[393,669]],[[187,695],[219,664],[230,646],[231,631],[219,280],[190,93],[191,44]],[[514,741],[543,732],[570,732],[685,757],[739,761],[769,753],[793,731],[796,721],[801,86],[780,33],[725,47],[658,79]]]};
const glyph = char => raw[char].map(stroke=>stroke.map(([x,y])=>[18+x*.145,153-y*.145]));
const men=glyph('門'), cha=glyph('茶'), chuan=glyph('船'), deng=glyph('燈'), yuan=glyph('圓');
const teaExtra=[[70,121],[111,121]];
const doorOutline=[[[42,156],[42,50],[80,50],[80,113]],[[139,156],[139,50],[101,50],[101,113]]];
const ancientBoat=[[[76,37],[59,60],[56,121],[70,157],[92,169],[109,152],[118,112],[116,66],[99,39]],[[57,89],[118,90]],[[58,118],[117,119]]];
const cuhk=char=>'https://humanum.arts.cuhk.edu.hk/Lexis/lexi-mf/search.php?word='+encodeURIComponent(char);
const catalogue={
 '门':{source:'https://chardb.iis.sinica.edu.tw/evolution.jsp?cid=25079', stages:[
  [0,'早期构形示意','看左右相对的两扇门，古文字的构形可以从这里观察。',doorOutline],
  [20/3,'传统写法「門」','比较左右两个部分，看看双扇门的结构怎样保留下来。',men],
  [42/3,'简体写法「门」','看现代简体的左竖、横折钩和上方点。',glyph('门')]]},
 '茶':{source:'https://dict.variants.moe.edu.tw/dictView.jsp?ID=-37834', stages:[
  [0,'早期用字「荼」示意','古文献中，「荼」有用来记录茶的例子。留意草字头下方的笔画。',[...cha,teaExtra]],
  [30/3,'写作「茶」','比较「荼」和「茶」中间的横画。这个过渡用减笔示意说明两种写法的关系。',cha]]},
 '船':{source:cuhk('船'), stages:[
  [0,'部件来源「舟」','先看「舟」的舟船轮廓。同一幕是部件构形示意。',ancientBoat],
  [20/3,'船字的舟字旁','把视线移到左侧，现代「船」仍保留舟字旁。',chuan.slice(0,6)],
  [42/3,'现代写法「船」','看右半边与舟字旁合在一起，构成今天的「船」。',chuan]]},
 '灯':{source:cuhk('燈'), stages:[
  [0,'构形观察「火」','先观察左边的火字旁，它提示了这个字的意义。',deng.slice(0,4)],
  [20/3,'传统写法「燈」','火表示意义，右边的「登」提示读音。',deng],
  [42/3,'简体写法「灯」','火字旁仍保留，右边改写为「丁」。',glyph('灯')]]},
 '圆':{source:cuhk('圓'), stages:[
  [0,'构形观察「員」','先观察传统字形内部的「員」。',yuan.slice(2,-1)],
  [20/3,'传统写法「圓」','留意外框「囗」与里面的「員」。',yuan],
  [42/3,'简体写法「圆」','外框保留，里面的「員」写成简体「员」。',glyph('圆')]]}
};
let stages=[];
const strokeCount=16, pointsPerStroke=22;
let samples=[];
function sample(strokes) {
 return Array.from({length:strokeCount},(_,i)=>{
  const present=i<strokes.length;
  const path=strokes[Math.min(i,strokes.length-1)];
  const cumulative=[0];
  for(let k=1;k<path.length;k++) cumulative.push(cumulative[k-1]+Math.hypot(path[k][0]-path[k-1][0],path[k][1]-path[k-1][1]));
  const length=cumulative.at(-1);
  const points=Array.from({length:pointsPerStroke},(_,k)=>{
   const target=present?k*length/(pointsPerStroke-1):length;
   const right=cumulative.findIndex(x=>x>=target);
   if(right<=0) return {x:path[0][0],y:path[0][1]};
   const left=right-1;
   const ratio=(target-cumulative[left])/(cumulative[right]-cumulative[left]||1);
   return {x:path[left][0]+(path[right][0]-path[left][0])*ratio,y:path[left][1]+(path[right][1]-path[left][1])*ratio};
  });
  return {points,present};
 });
}
const get=id=>block.querySelector('#history-'+id);
const svgNS = 'http://www.w3.org/2000/svg';
const player=get('player');
player.setAttribute('aria-label',word+'字的字形演变');
const drawn = Array.from({length:strokeCount},()=>{
 const stroke=document.createElementNS(svgNS,'polyline');
 stroke.setAttribute('fill','none');
 stroke.setAttribute('stroke-linecap','round');
 stroke.setAttribute('stroke-linejoin','round');
 get('glyph').append(stroke);
 return stroke;
});
function drawMorph(index, elapsed){
 const target=Math.min(index+1,stages.length-1);
 const transitionSeconds=index===0?stages[1].time:4;
 const progress=target===index?0:Math.max(0,Math.min(1,(elapsed-stages[target].time+transitionSeconds)/transitionSeconds));
 const isModern=index===stages.length-1;
 drawn.forEach((stroke,i)=>{
  // Begin with the upper strokes. All strokes settle before the next stage.
  const delay=i/(strokeCount-1)*.23;
  const local=Math.max(0,Math.min(1,(progress-delay)/.77));
  const mix=local*local*(3-2*local);
  const a=samples[index][i],b=samples[target][i];
  stroke.setAttribute('points',a.points.map((v,j)=>{
   const next=b.points[j];
   return (v.x+(next.x-v.x)*mix).toFixed(2)+','+(v.y+(next.y-v.y)*mix).toFixed(2);
  }).join(' '));
  stroke.setAttribute('opacity',(Number(a.present)*(1-mix)+Number(b.present)*mix).toFixed(3));
  stroke.setAttribute('stroke-width',isModern?8:target===stages.length-1?5+3*mix:5);
  stroke.setAttribute('stroke',isModern?'#86291d':target===stages.length-1?
    'rgb('+Math.round(52+82*mix)+','+Math.round(39+2*mix)+','+Math.round(32-3*mix)+')':'#342720');
 });
}

let elapsed=0, started=null, frame, active=-1;
function render(){
 const index=stages.findLastIndex(stage=>stage.time<=elapsed);
 if(active!==index){
  active=index;const stage=stages[index];
  get('stage').textContent=stage.name;get('description').textContent=stage.note;
  get('glyph').setAttribute('aria-label',stage.name+'字形构形');

  [...get('steps').children].forEach((b,i)=>b.setAttribute('aria-current',i===index));
 }
 drawMorph(index,elapsed);
 get('progress').value=elapsed;get('clock').textContent=Math.floor(elapsed)+' 秒 / 20 秒';
}
function pause(){cancelAnimationFrame(frame);started=null;get('play').textContent=elapsed>=20?'重播':'继续';}
function tick(){
 if(started===null)return;
 elapsed=Math.max(elapsed,Math.min(20,(performance.now()-started)/1000));
 render();
 if(elapsed<20)frame=requestAnimationFrame(tick);else pause();
}
function start(){if(elapsed>=20)elapsed=0;started=performance.now()-elapsed*1000;render();get('play').textContent='暂停';frame=requestAnimationFrame(tick);}
function loadWord(word){
 const entry=catalogue[word];
 stages=entry.stages.map(([time,name,note])=>({time,name,note}));
 samples=entry.stages.map(stage=>sample(stage[3]));
 player.querySelector('h2').textContent='「'+word+'」是怎么写到今天的？';
 player.querySelector('a').href=entry.source;
 get('steps').replaceChildren();
 stages.forEach(stage=>{
  const button=document.createElement('button');
  button.textContent=stage.name;
  button.onclick=()=>{const playing=started!==null;pause();elapsed=stage.time;render();if(playing)start();};
  get('steps').append(button);
 });
 active=-1;
}
get('open').onclick=()=>{loadWord(word);elapsed=0;player.showModal();start();};
get('play').onclick=()=>started===null?start():pause();
get('close').onclick=()=>{pause();player.close();};
player.addEventListener('cancel',pause);
player.addEventListener('close',pause);

  block.stopHistory = () => { pause(); if (player.open) player.close(); };

}
const featuredHistory = new Set(['年','门','茶','船','灯','圆']);
const historyAliases = {'門':'门','燈':'灯','圓':'圆'};
function attach(container, word) {
  word = historyAliases[word] || word;
  const block = document.createElement('div');
  block.className = 'character-history';
  container.append(block);
  if (!featuredHistory.has(word)) {
    block.textContent = '这个字暂未收录可播放的字形资料。';
    return block;
  }
  block.innerHTML = "<button type=\"button\" id=\"history-open\" aria-haspopup=\"dialog\">播放字形演变</button><dialog id=\"history-player\" aria-label=\"年字的字形演变\">\n<header><h2 >「年」是怎么来的？</h2><button class=\"close\" id=\"history-close\" aria-label=\"关闭并停止播放\">×</button></header>\n<div class=\"screen\"><div class=\"stage\" id=\"history-stage\"></div><svg id=\"history-glyph\" viewBox=\"0 0 180 196\" role=\"img\"></svg><p id=\"history-description\"></p></div>\n<div class=\"steps\" id=\"history-steps\" aria-label=\"切换字形阶段\"></div>\n<progress id=\"history-progress\" max=\"20\" value=\"0\" aria-label=\"播放进度\"></progress>\n<div class=\"controls\"><button id=\"history-play\">暂停</button><span class=\"clock\" id=\"history-clock\">0 秒 / 20 秒</span><a href=\"https://chardb.iis.sinica.edu.tw/evolution.jsp?cid=10887\" target=\"_blank\" rel=\"noopener\">查看原始字形 →</a></div>\n<p class=\"note\">字形连变为演变示意。各阶段的原始字形可在中央研究院字库查看。</p>\n</dialog>";

if (word !== '年') { initializeOtherWord(block, word); return block; }
const stages=[
 {time:0,name:'甲骨文',note:'先看上面的禾，再看下面的人。这个构形像人背着禾，让人想到收成。',art:'<path d="M53 52L123 43M86 27L90 94M89 55L60 87M90 55l30 26M98 102L83 126L67 153M83 126L112 166"/>'},
 {time:16/3,name:'金文',note:'比较上下两部分：上部仍可看出禾的形态，下部保留了人形。',art:'<path d="M48 53Q79 50 128 45M88 24Q86 59 95 99M89 55Q78 75 54 89M90 55Q107 73 129 82M104 96Q102 122 65 166M91 126Q104 154 120 170"/>'},
 {time:32/3,name:'小篆',note:'留意下部：小篆这一写法中，下部呈「千」形。',art:'<path d="M57 51Q84 52 122 42M90 29Q88 65 91 91M88 57Q73 76 52 83M91 57Q105 75 127 83M72 111Q93 105 108 103M60 133Q83 134 123 127M93 109Q100 143 92 169"/>'},
 {time:46/3,name:'现代写法',note:'今天写作「年」。再回看最初的构形，就能比较古今写法的差别。',art:'<text x="90" y="153" text-anchor="middle" stroke="none" fill="#86291d" font-size="150" font-family="KaiTi,STKaiti,serif">年</text>'}
];
// Sample each visible stroke so adjacent frames can share the same geometry.
const modernStrokes = 'M65 36Q62 57 45 75 M62 58Q91 55 127 46 M62 89Q89 86 121 81 M65 90L62 122 M37 126Q88 118 144 118 M96 59Q97 108 91 167';
const strokeCount = 7;
const pointsPerStroke = 22;
const svgNS = 'http://www.w3.org/2000/svg';
const samples = stages.map((stage, i) => {
 const line = i === stages.length - 1 ? modernStrokes : stage.art.match(/d="([^"]+)"/)[1];
 const strokes = line.match(/M[^M]+/g);
 return Array.from({length:strokeCount}, (_, j)=>{
  const path=document.createElementNS(svgNS,'path');
  const present=j<strokes.length;
  path.setAttribute('d',strokes[Math.min(j,strokes.length-1)]);
  const length=path.getTotalLength();
  const points=Array.from({length:pointsPerStroke},(_, k)=>path.getPointAtLength(length*(present?k/(pointsPerStroke-1):1)));
  return {points,present};
 });
});
const get=id=>block.querySelector('#history-'+id);
const player=get('player');
const drawn = Array.from({length:strokeCount},()=>{
 const stroke=document.createElementNS(svgNS,'polyline');
 stroke.setAttribute('fill','none');
 stroke.setAttribute('stroke-linecap','round');
 stroke.setAttribute('stroke-linejoin','round');
 get('glyph').append(stroke);
 return stroke;
});
function drawMorph(index, elapsed){
 const target=Math.min(index+1,stages.length-1);
 const transitionSeconds=index===0?stages[1].time:4;
 const progress=target===index?0:Math.max(0,Math.min(1,(elapsed-stages[target].time+transitionSeconds)/transitionSeconds));
 const isModern=index===stages.length-1;
 drawn.forEach((stroke,i)=>{
  // Begin with the upper strokes. All strokes settle before the next stage.
  const delay=i/(strokeCount-1)*.23;
  const local=Math.max(0,Math.min(1,(progress-delay)/.77));
  const mix=local*local*(3-2*local);
  const a=samples[index][i],b=samples[target][i];
  stroke.setAttribute('points',a.points.map((v,j)=>{
   const next=b.points[j];
   return (v.x+(next.x-v.x)*mix).toFixed(2)+','+(v.y+(next.y-v.y)*mix).toFixed(2);
  }).join(' '));
  stroke.setAttribute('opacity',(Number(a.present)*(1-mix)+Number(b.present)*mix).toFixed(3));
  stroke.setAttribute('stroke-width',isModern?8:target===stages.length-1?5+3*mix:5);
  stroke.setAttribute('stroke',isModern?'#86291d':target===stages.length-1?
    'rgb('+Math.round(52+82*mix)+','+Math.round(39+2*mix)+','+Math.round(32-3*mix)+')':'#342720');
 });
}

let elapsed=0, started=null, frame, active=-1;
function render(){
 const index=stages.findLastIndex(stage=>stage.time<=elapsed);
 if(active!==index){
  active=index;const stage=stages[index];
  get('stage').textContent=stage.name;get('description').textContent=stage.note;
  get('glyph').setAttribute('aria-label',stage.name+'字形构形');

  [...get('steps').children].forEach((b,i)=>b.setAttribute('aria-current',i===index));
 }
 drawMorph(index,elapsed);
 get('progress').value=elapsed;get('clock').textContent=Math.floor(elapsed)+' 秒 / 20 秒';
}
function pause(){cancelAnimationFrame(frame);started=null;get('play').textContent=elapsed>=20?'重播':'继续';}
function tick(){
 if(started===null)return;
 elapsed=Math.max(elapsed,Math.min(20,(performance.now()-started)/1000));
 render();
 if(elapsed<20)frame=requestAnimationFrame(tick);else pause();
}
function start(){if(elapsed>=20)elapsed=0;started=performance.now()-elapsed*1000;render();get('play').textContent='暂停';frame=requestAnimationFrame(tick);}
stages.forEach(stage=>{const button=document.createElement('button');button.textContent=stage.name;button.onclick=()=>{const playing=started!==null;pause();elapsed=stage.time;render();if(playing)start();};get('steps').append(button);});
get('open').onclick=()=>{elapsed=0;player.showModal();start();};
get('play').onclick=()=>started===null?start():pause();
get('close').onclick=()=>{pause();player.close();};
player.addEventListener('cancel',pause);
player.addEventListener('close',pause);

  block.stopHistory = () => { pause(); if (player.open) player.close(); };
  return block;
}
const glyph = document.getElementById('open-glyph');
const storyWord = document.querySelector('#form .glyph')?.textContent.trim();
if (glyph && storyWord) attach(glyph.parentElement, storyWord);
let previous;
document.addEventListener('zili:lookup', event => {
  if (previous) { previous.stopHistory?.(); previous.remove(); }
  const result = document.getElementById('lookup-result');
  if (result && event.detail) previous = attach(result, event.detail);
});
})();</script>"""
    lookup_ui = (ROOT / "zili-lookup-results.js").read_text(encoding="utf-8")
    lookup_style = """<style>
.lookup-result:has(.lookup-three){width:100%;max-width:none;box-sizing:border-box;font-size:1.0625rem;line-height:1.65}
.lookup-result:has(.lookup-three) #word{font-size:clamp(1.75rem,3vw,2.25rem);margin:0 0 14px}
.story-lookup .lookup-credit{font-size:1rem;line-height:1.55}
.lookup-three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(12px,1.5vw,22px)}
.lookup-tile{min-width:0;padding:clamp(14px,1.5vw,24px);background:#fffaf0;border:1px solid #d7c2a4;border-radius:10px;overflow-wrap:anywhere}
.lookup-tile h3{margin:0 0 12px;color:#8c291e;font-size:clamp(1.2rem,1.65vw,1.5rem);line-height:1.35}
.lookup-tile p{font-size:inherit;line-height:inherit}
.lookup-tile button{font:inherit}
.lookup-definition{font-size:1.1875rem;line-height:1.7}
.lookup-definition a:any-link{color:#702117;font-weight:700;line-height:1.5;text-underline-offset:.19em}
.lookup-definition a:hover,.lookup-definition a:focus-visible{color:#49140d}
.lookup-link-arrow{display:inline-block;margin-inline-start:.3em;text-decoration:none}
.lookup-forms{display:flex;gap:8px;flex-wrap:wrap}
.lookup-forms button,.lookup-play{border:1px solid #d7c2a4;border-radius:8px;background:#fff8ed;color:#8c291e;padding:7px 13px}
.lookup-forms button{font:28px/1.2 KaiTi,serif}
.lookup-forms button small{display:block;font:600 .8rem/1.4 system-ui,sans-serif}
.lookup-forms button[aria-pressed=true],.lookup-play:not(:disabled){background:#8c291e;color:#fff}
.lookup-glyph{font:clamp(76px,8vw,110px)/1.25 KaiTi,serif;text-align:center;color:#8c291e}
.lookup-stroke-board{margin:12px auto;width:min(100%,260px);aspect-ratio:1;border:1px solid #d7c2a4;border-radius:8px}
.lookup-stroke-board svg{display:block;width:100%;height:auto}
.lookup-stroke-controls{display:grid;justify-items:start;gap:10px;margin-top:14px}
.lookup-stroke-controls .lookup-stroke-status{margin:0}
.lookup-variant-note,.lookup-stroke-status{color:#695849}
@media(max-width:900px){.lookup-three{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.lookup-three{grid-template-columns:minmax(0,1fr)}}
</style>"""
    writer_script = "<script>" + stroke_library + "</script>"
    pages = {}
    for name in PAGES:
        page = (ROOT / name).read_text(encoding="utf-8")
        page = re.sub(r'<link rel="stylesheet" href="style.css"\s*/?>',
                      lambda _: "<style>" + (ROOT / "style.css").read_text(encoding="utf-8") + "</style>", page)
        page = re.sub(r'<script( defer)? src="(app|demo)\.js"></script>',
                      lambda m: "<script>" + ("document.addEventListener('DOMContentLoaded', () => {\n" if m[1] else "")
                      + (ROOT / (m[2]+".js")).read_text(encoding="utf-8")
                      + ("\n});" if m[1] else "") + "</script>", page)
        page = page.replace("fetch('cases.json')", "Promise.resolve(new Response(JSON.stringify(" + json_script(catalogue) + ")))") if "fetch('cases.json')" in page else page
        page = page.replace("return config.images?.[record.id] || record.image;", "return parent.ziliImage(config.images?.[record.id] || record.image);")
        page = page.replace("return config.images?.[record.id] || record.id + '.webp';", "return parent.ziliImage(config.images?.[record.id] || record.id + '.webp');")
        page = re.sub(r'(picture\.src\s*=\s*)image\s*;', r'\1parent.ziliImage(image);', page)
        has_lookup = 'www.moedict.tw/uni/' in page
        if has_lookup:
            page = enrich_lookup(page)
            page = re.sub(r'(<section id="lookup-result"[\s\S]*?</section>)',
                          lambda m: m[1] + lookup_style + writer_script +
                          "<script>" + lookup_ui + "</script>", page, count=1)
        if 'id="glyph-dialog"' in page:
            page = re.sub(r'(<details(?: id="sources")?)(>\s*<summary>资料核验与素材说明</summary>)',
                          r'\1 open data-source-notes\2', page, count=1)
            page = page.replace("</head>", observation_style + keepsake_style + "</head>", 1)
            page = page.replace('保存寻踪记录</button>',
                                '保存寻踪记录</button><p id="keepsake-status" role="status"></p>'
                                '<a id="keepsake-collection-link" href="keepsakes.html" hidden>'
                                '查看已保存的寻踪卡 →</a>', 1)
            page = page.replace("</body>", stroke_style + ("" if has_lookup else writer_script) +
                                "<script>" + stroke_ui + "</script></body>")
        if has_lookup or name in story_words:
            page = page.replace("</body>", history_ui + "</body>", 1)
        if name in story_words:
            links = "".join(
                f'<a href="{path}"' + (' aria-current="page"' if path == name else '') + f'>{word}</a>'
                for path, word in story_words.items()
            )
            page, count = re.subn(
                r'(<(div|a) class="brand"[^>]*>[^<]*)<span>[^<]*</span>(</\2>)',
                lambda m: '<div class="story-title-row">' + m[1].rstrip() + m[3] +
                          '<nav class="story-word-switch" aria-label="切换精选汉字">' + links + '</nav></div>',
                page, count=1,
            )
            if count:
                page = page.replace("</head>", story_switch_style + "</head>", 1)
        pages[name] = page
    references = "\n".join([*pages.values(), json_script(catalogue)])
    assets = {path.name: image_url(path.name) for path in ROOT.iterdir()
              if path.suffix.lower() in (".webp", ".png", ".jpg")
              and (path.name in references or path.name.startswith("nian-") or path.name in {'home-terrain-reference.webp', 'home-terrain-corner-repair.webp', 'home-macao.webp', 'home-hongkong.webp', 'home-taiwan.webp', "paper.webp"})}
    payload = json_script({"pages": pages, "images": assets, "variants": variants, "strokes": strokes})
    return base64.b64encode(gzip.compress(payload.encode("utf-8"), compresslevel=6)).decode("ascii")


st.set_page_config(page_title="字里寻踪", page_icon="年", layout="wide")
st.html("""<style>
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #e9decd;
    height: 100dvh;
    overflow: hidden;
}
[data-testid="stMainBlockContainer"] { max-width: none; padding: 0; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] { gap: 0; }
[data-testid="stHeader"] { display: none; }
/* Keep the website readable while the Streamlit component waits for Qwen. */
[data-testid="stElementContainer"][data-stale="true"]:has(iframe[data-testid="stCustomComponentV1"]) {
    opacity: 1 !important;
    transition: none !important;
}
iframe[data-testid="stIFrame"], iframe[data-testid="stCustomComponentV1"] {
    display: block;
    width: 100%;
    height: 100dvh !important;
    border: 0;
}
</style>""")
# Build the legacy bundle only when the published release is absent.
@st.cache_data(show_spinner=False)
def published_story_theme(_path, story, version):
    """Extend the story gutter colors through the full reading area."""
    html = _path.read_text(encoding="utf-8")
    # Nested component documents have different base URLs. Pin the artwork to
    # its published revision so every page and lightbox loads the same master.
    asset_root = "__ZILI_ATLAS__/"

    def embed_atlas(match):
        return asset_root + match.group(1)

    atlas_path = re.compile(r"app/static/atlas/([\w.-]+\.(?:jpg|png|webp))")
    packed = re.compile(r"(const packed = ')([^']+)(';)")

    def embed_packed(match):
        site = gzip.decompress(base64.b64decode(match.group(2))).decode("utf-8")
        site = atlas_path.sub(embed_atlas, site)
        encoded = base64.b64encode(gzip.compress(site.encode("utf-8"), compresslevel=1, mtime=0)).decode("ascii")
        return match.group(1) + encoded + match.group(3)

    label = "const storyArt = "
    start = html.index(label) + len(label)
    story_art, length = json.JSONDecoder().raw_decode(html[start:])
    year_css = story_art["nian.html"]
    story_art["nian.html"] = re.sub(
        r'data:[^"]+(?="\) center 48%/cover no-repeat;)',
        "app/static/atlas/nian-theme.jpg",
        year_css,
    )
    html = html[:start] + json.dumps(story_art) + html[start + length:]
    html = packed.sub(embed_packed, atlas_path.sub(embed_atlas, html), count=1)
    cover_style = (ROOT / "cover-lettering.css").read_text(encoding="utf-8-sig")
    wordmark = (
        '<h1 class="atlas-wordmark" aria-label="字里寻踪">'
        '<span>字</span><span>里</span><span>寻</span><span class="seal-word">踪</span></h1>'
        '<svg class="atlas-rule" aria-hidden="true" viewBox="0 0 240 18">'
        '<path d="M0 12h86l12-6 6 3 13-8 15 11 10-6 14 6h84M94 15h54" '
        'fill="none" stroke="currentColor" stroke-width="1.3"/></svg>'
    )
    html = html.replace('<header class="terrain-heading"><h1>字里寻踪</h1>',
                        '<style>' + cover_style + '</style><header class="terrain-heading">' + wordmark, 1)

    accents = {
        "#f5dcc0": "#ad623a", "#efdfcb": "#984737",
        "#e6e8d6": "#527259", "#dce9e7": "#34647a",
        "#f1e2d4": "#935857", "#efe5e1": "#a65045",
    }
    for paper, accent in accents.items():
        gradient = (
            "linear-gradient(155deg,#7294aa 0%,#dce8ef 12%,#f5f7f8 31%,"
            f"#f8f9fa 57%,{paper} 100%)"
        )
        original = "fixed no-repeat,\\n              " + gradient
        extended = (
            "fixed no-repeat,\\n              "
            "radial-gradient(ellipse 24% 84% at 0% 92%,#a9c4d8 0%,#c1d6e566 60%,transparent 100%),"
            f"radial-gradient(ellipse 24% 84% at 100% 92%,{accent}42 0%,{accent}22 60%,transparent 100%),"
            + gradient
        )
        html = html.replace(original, extended)
    html = html.replace("frame.srcdoc = inlineImages.replace", "frame.srcdoc = (storyArt[page] ? inlineImages.replace(/<footer>\\s*(?:配图为\\s*AI\\s*场景示意。\\s*)?(?:原始资料|民俗资料)见各卡片出处。\\s*<\\/footer>/, '') : inlineImages).replace", 1)
    html = html.replace("  frame.srcdoc = ", "  const galleryPage = page === 'regions.html' ? inlineImages\n    .replace(/(<aside class=\"region\">[\\s\\S]*?<\\/aside>)\\s*(<section aria-label=\"地区故事\">)/, '$2<div class=\"gallery-toolbar\">$1')\n    .replace(/(<div id=\"character\"[^>]*><\\/div>)/, '$1</div>') : inlineImages;\n" + "  frame.srcdoc = ", 1)
    html = html.replace(": inlineImages).replace", ": galleryPage).replace", 1)
    lookup_style = "\nhtml body.lookup-only{background-color:#e4eef4;background-size:100% clamp(180px,25vh,290px),100% 15.38vh}\nhtml body.lookup-only .demo-shell>.page,html body.lookup-only .journey-layout>.page{background:transparent}\nhtml body.lookup-only .page>main{width:100%;max-width:none;padding:0;margin:0;background:transparent}\nhtml body.lookup-only #story-lookup{box-sizing:border-box;width:calc(100% - 2 * clamp(12px,2vw,30px));max-width:none;margin:clamp(14px,3vh,32px) auto 36px}\nhtml body #story-lookup{background:linear-gradient(105deg,#e2edf4f2,#f7fafce8 53%,#e9f2f6ed);border-color:#afc6d4;box-shadow:0 8px 24px #14364b0b;color:#19394d}\nhtml body #story-lookup :is(.story-lookup-form,.lookup-tile,.lookup-stroke-board,.stroke-board){background:#f2f8fb;border-color:#abc2d1;color:#19394d}\nhtml body #story-lookup .lookup-tile{background:linear-gradient(150deg,#f7fbfd,#e2eef5)}\nhtml body #story-lookup :is(h2,h3,.lookup-glyph,.lookup-stroke-status){color:#193e57}\nhtml body #story-lookup :is(input,select,button){color:#244d67;background-color:#f4f9fc;border-color:#a8c1d1}\nhtml body #story-lookup :is(.lookup-play,button[type=submit]){background-color:#315c78;color:white;border-color:#315c78}\nhtml body #story-lookup :is(a,input:focus,select:focus){color:#214f6e}\nhtml body #story-lookup :is(input,select,button):focus-visible{outline-color:#447799}\n\nhtml body:has(.globe-cover.lookup-credit-flow){background-color:#e6f0f5}\nhtml body .globe-cover.lookup-credit-flow{\n  box-sizing:border-box;position:relative;width:min(calc(100% - 2 * clamp(14px,2.4vw,32px)),1120px);\n  max-width:none;height:auto;min-height:0;margin:clamp(115px,24vh,220px) auto 24px clamp(14px,2.4vw,32px);\n  padding:clamp(12px,2vw,24px);background:linear-gradient(100deg,#dbeaf3ed,#f4f9fced);\n  border:1px solid #a9c2d1;border-radius:12px;color:#183b53;\n}\nhtml body .globe-cover.lookup-credit-flow .globe-search{max-width:none;margin:0;background:#edf5fa;border-color:#a7c2d3}\nhtml body .globe-cover.lookup-credit-flow :is(input,select,button){background:#f2f8fc;color:#224d6b;border-color:#a7c2d3}\nhtml body .globe-cover.lookup-credit-flow button[type=submit]{background:#315c78;color:#fff}\nhtml body .globe-cover.lookup-credit-flow .lookup-credit{text-align:left;color:#315268}\nhtml body.lookup-only #story-lookup{width:min(calc(100% - 2 * clamp(14px,2.4vw,32px)),1120px);margin-inline:clamp(14px,2.4vw,32px) auto}\nhtml body :is(#lookup-result,.lookup-result,.lookup-tile,.lookup-stroke-board){\n background:#edf5fa;border-color:#a9c2d2;color:#183d56;\n}\nhtml body :is(#lookup-result,.lookup-result) .lookup-tile{background:linear-gradient(150deg,#f7fbfd,#e2eef6);border-color:#a9c2d2}\nhtml body :is(#lookup-result,.lookup-result) :is(h2,h3,a,.lookup-glyph,.lookup-stroke-status){color:#194967}\nhtml body :is(#lookup-result,.lookup-result) :is(.lookup-play,button[aria-pressed=true]){background:#315c78;color:#fff;border-color:#315c78}\nhtml body :is(#lookup-result,.lookup-result) :is(select,button:not(.lookup-play):not([aria-pressed=true])){background:#f0f7fb;border-color:#9dbacc;color:#244e69}\n\nhtml body .globe-cover.lookup-credit-flow,html body.lookup-only #story-lookup{\n  display:block;aspect-ratio:auto!important;height:auto!important;min-height:0!important;\n  max-height:none!important;block-size:auto!important;min-block-size:0!important;\n  padding-block:clamp(10px,1.4vw,18px);\n}\nhtml body .globe-cover.lookup-credit-flow{margin-block:clamp(118px,24vh,190px) 20px;padding-block:clamp(32px,5.8vh,54px);overflow:visible}\nhtml body :is(.globe-cover.lookup-credit-flow,#story-lookup) :is(#lookup-result,#lookup-status)[hidden]{display:none!important}\nhtml body .globe-cover.lookup-credit-flow #lookup-status:empty{display:none}\n"
    gallery_toolbar_style = "\nhtml body:has(main>.gallery){background-size:100% clamp(220px,29vh,330px),100% 15.38vh}\nhtml body:has(main>.gallery)::before{mask-image:linear-gradient(transparent 12%,#000 34%,#000 88%,transparent)}\nhtml body main>.gallery{display:block}\nhtml body .gallery>section{min-width:0}\nhtml body .gallery .gallery-toolbar{position:sticky;top:0;z-index:12;display:grid;gap:8px;padding:10px 0 12px;background:linear-gradient(98deg,#d7e7f0,#f2f7fa 56%,#dcebf2);border-bottom:1px solid #a8c3d2}\nhtml body .gallery .gallery-toolbar .region{position:static;display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:0;background:transparent;border:0;box-shadow:none}\nhtml body .gallery .gallery-toolbar .region h2{margin:0;font-size:1rem}\nhtml body .gallery .gallery-toolbar :is(.filters,.habit-search){display:flex;flex-wrap:wrap;gap:8px;margin:0}\nhtml body .gallery .gallery-toolbar .habit-field{flex:1 1 180px;min-width:0}\nhtml body .gallery .gallery-toolbar .filters button{width:auto;margin:0}\nhtml body .gallery #records{grid-template-columns:repeat(auto-fit,minmax(min(245px,100%),1fr))}\n@media(max-width:600px){html body .gallery .gallery-toolbar{gap:5px;padding-block:5px}html body .gallery .gallery-toolbar .filters button{min-height:34px}}\n"
    gallery_toolbar_style += """
@media (min-width: 821px) {
  html body main:has(>.gallery)>h1 { font-size:clamp(32px,3vw,44px); line-height:1.15; margin-block:0 6px; }
  html body main:has(>.gallery)>.intro { margin-block:0 16px; }
  html body main:has(>.gallery) { padding-top:16px; }
  html body .gallery .gallery-toolbar { row-gap:5px; padding-block:5px 7px; }
  html body .gallery .gallery-toolbar details { margin-block:4px !important; padding-block:6px !important; }
  html body .gallery .gallery-toolbar details form { margin-top:4px !important; }
  html body .gallery .gallery-toolbar [role="status"]:empty { margin-top:0 !important; }
  html body .gallery .gallery-toolbar .filters button { padding-block:4px; min-height:34px; }
}
"""
    gallery_style = "\nhtml body:has(main>.gallery){background-color:#e9f2f6;isolation:isolate}\nhtml body:has(main>.gallery)::before{content:\"\";position:fixed;inset:0 0 15.38vh;z-index:-1;pointer-events:none;background:linear-gradient(102deg,#b3ccdc,#e7f0f5 30%,#f2f6f8 62%,#d6e7ed);mask-image:linear-gradient(transparent,#000 19%,#000 88%,transparent)}\nhtml body main:has(>.gallery){background:transparent;border-radius:0;box-shadow:none}\nhtml body main:has(>.gallery) :is(h1,h2,h3){color:#173b52}\nhtml body .gallery :is(.region,.grid article){background:linear-gradient(145deg,#f7fafc,#e8f1f6);border-color:#aec5d3;box-shadow:0 3px 12px #183a4b0c}\nhtml body .gallery :is(.filters,.habit-field){background:transparent;box-shadow:none}\nhtml body .gallery :is(input,select,.habit-suggestions){background:#f6fafc;border-color:#9eb9ca;color:#18374b}\nhtml body .gallery .filters button{background:#f3f8fb;border-color:#adc4d2;color:#24475d}\nhtml body .gallery .filters button:is(.active,[aria-pressed=true],[aria-current=true]),html body .gallery .habit-search button[type=submit]{background:#294f6a;border-color:#294f6a;color:#fff}\nhtml body main:has(>.gallery) footer{background:#f2f7fabd;border-color:#aec5d3;color:#244457}\n"
    lookup_style += """
html body:is(.lookup-only, :has(.globe-cover.lookup-credit-flow)) {
  --lookup-map-height:clamp(120px,25vh,290px);
  background-size:100% var(--lookup-map-height),100% 15.38vh;
}
html body.lookup-only .page>main {
  display:flow-root;
  padding-top:0 !important;
}
html body.lookup-only .page>main>#story-lookup {
  margin-top:var(--lookup-map-height) !important;
}
html body .globe-cover.lookup-credit-flow {
  margin-block-start:var(--lookup-map-height);
}
"""
    lookup_open = "      frame.contentWindow.scrollTo(0, 0);"
    html = html.replace(
        lookup_open,
        lookup_open + "\n      frame.contentWindow.requestAnimationFrame(() => frame.contentWindow.scrollTo(0, 0));",
        1,
    )
    lookup_style += """
html body:is(.lookup-only,:has(.lookup-credit-flow)) :is(#story-lookup,.lookup-credit-flow) {
  padding-block:12px;
  margin-bottom:8px;
}
html body:is(.lookup-only,:has(.lookup-credit-flow)) #lookup-result {
  margin-block:8px;
  padding:10px 14px;
  line-height:1.45;
}
html body:is(.lookup-only,:has(.lookup-credit-flow)) #lookup-result #word {
  font-size:clamp(1.35rem,2.4vw,1.75rem);
  margin:0 0 6px;
}
html body:is(.lookup-only,:has(.lookup-credit-flow)) #lookup-result .lookup-tile {
  padding:8px 12px;
}
html body:is(.lookup-only,:has(.lookup-credit-flow)) #lookup-result .lookup-tile :is(h3,p) {
  margin-block:0 6px;
}
html body:is(.lookup-only,:has(.lookup-credit-flow)) #lookup-result .lookup-stroke-board {
  width:min(100%,clamp(96px,13vh,142px));
  margin:4px auto;
}
html body:is(.lookup-only,:has(.lookup-credit-flow)) #lookup-result .lookup-glyph {
  font-size:clamp(48px,7vh,70px);
  line-height:1;
}
@media(min-width:681px) {
  html body:is(.lookup-only,:has(.lookup-credit-flow)) #lookup-result .lookup-three {
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:10px;
  }
  html body .globe-cover.lookup-credit-flow,
  html body.lookup-only #story-lookup .story-lookup-form {
    position:sticky;top:0;z-index:4;
  }
}
html body:is(.lookup-only,:has(.lookup-credit-flow)) .qwen-lookup-demo {
  margin:8px 14px !important;
  padding:8px 12px !important;
}
"""
    html = html.replace(
        "const inlineImages = lookupHtml",
        'const inlineImages = (lookupLanding ? lookupHtml.replaceAll('
        + json.dumps("panel.scrollIntoView({block:'nearest'});") + ", '') : lookupHtml)",
        1,
    )
    lookup_style += """
html body:is(.lookup-only,:has(.lookup-credit-flow)) {
  overflow-anchor:none;
  --lookup-top-gap:10px;
}
html body .globe-cover.lookup-credit-flow,
html body.lookup-only .page>main>#story-lookup {
  margin-top:var(--lookup-map-height) !important;
}
html body:has(#lookup-result:not([hidden])) .globe-cover.lookup-credit-flow,
html body.lookup-only:has(#lookup-result:not([hidden])) .page>main>#story-lookup {
  margin-top:var(--lookup-top-gap) !important;
}
@media(min-width:681px) {
  html body:has(#lookup-result:not([hidden])) .globe-cover.lookup-credit-flow,
  html body.lookup-only:has(#lookup-result:not([hidden])) #story-lookup .story-lookup-form {
    top:var(--lookup-top-gap);
  }
}
"""
    lookup_style += """
@media(min-width:681px) {
  html body.lookup-only:not(:has(#lookup-result:not([hidden]))) .page>main>#story-lookup,
  html body:not(:has(#lookup-result:not([hidden]))) .globe-cover.lookup-credit-flow {
    position:fixed !important;
    top:var(--lookup-map-height) !important;
    margin-block-start:0 !important;
    z-index:4;
  }
}
html body:is(.lookup-only,:has(.globe-cover.lookup-credit-flow)) {
  background-position-y:top,bottom !important;
  background-size:100% var(--lookup-map-height),100% 15.38vh !important;
}
"""
    lookup_style += """
html body:has(.globe-cover.lookup-credit-flow) {
  --lookup-side-gap:clamp(14px,2.4vw,32px);
  --lookup-width:calc(100% - 2 * var(--lookup-side-gap));
}
html body:has(.globe-cover.lookup-credit-flow) :is(.globe-cover.lookup-credit-flow,#lookup-result,.qwen-lookup-demo) {
  box-sizing:border-box;
  width:var(--lookup-width) !important;
  max-width:none !important;
  margin-inline:var(--lookup-side-gap) !important;
}
html body:has(.globe-cover.lookup-credit-flow) #lookup-result {
  padding-inline:0;
}
html body:has(.globe-cover.lookup-credit-flow) .qwen-lookup-demo {
  margin-block:8px !important;
}
html body.lookup-only .page>main>#story-lookup {
  padding-inline:0;
}
html body.lookup-only #story-lookup :is(.story-lookup-heading,.story-lookup-form,.lookup-credit) {
  margin-inline:12px;
}
html body.lookup-only #story-lookup :is(#lookup-result,.qwen-lookup-demo) {
  box-sizing:border-box;
  width:100%;
  margin-inline:0 !important;
}
"""
    source_style = "html body .page details:is([data-source-notes],#sources,#journey-sources){color:#172c3a;font-size:17px;font-weight:500}html body .page details:is([data-source-notes],#sources,#journey-sources)>summary{color:#172c3a;font-weight:700}html body .page details:is([data-source-notes],#sources,#journey-sources) :is(li,p){color:#172c3a;font-size:inherit;font-weight:500}html body .page details:is([data-source-notes],#sources,#journey-sources) a{color:#70271e;font-weight:700;text-underline-offset:.15em}"
    reading_style = (ROOT / "reading-edition.css").read_text(encoding="utf-8")
    reading_style += """
html body .page #form .observation :is(#open-glyph, .character-history) {
    display:inline-flex !important;
    width:auto !important;
    margin-block:4px !important;
    vertical-align:middle;
}
html body .page #form .observation .character-history {
    margin-inline-start:8px;
}
"""

    from release_fixes import patch_release
    html = patch_release(html, ROOT, story)
    notes_script = (ROOT / "reading-notes.js").read_text(encoding="utf-8")
    hook = "    if (page === keepsakePage) renderKeepsakes(doc);"
    html = html.replace("main>:not(#story-lookup)", "main>:not(#story-lookup,.qwen-lookup-demo)", 1)
    qwen_demos = (ROOT / "qwen-demos.js").read_text(encoding="utf-8-sig")
    stats_html = (ROOT / "folk-stats.html").read_text(encoding="utf-8")
    stats_html = stats_html.replace('<link rel="stylesheet" href="stats-3d.css">',
                                    '<style>' + (ROOT / 'stats-3d.css').read_text(encoding='utf-8') + '</style>')
    stats_html = stats_html.replace('<script src="stats-3d.js"></script>',
                                    '<script>' + (ROOT / 'stats-3d.js').read_text(encoding='utf-8') + '</script>')
    stats_html = stats_html.replace('</style>', '''
body{background:#faf6eb}
section,#ring b{background:#fffcf5}
</style>''', 1)
    catalogue_json = (ROOT / "cases.json").read_text(encoding="utf-8")
    stats_html = stats_html.replace(
        "fetch('cases.json')",
        "Promise.resolve(new Response(" + json.dumps(catalogue_json, ensure_ascii=True).replace("<", r"\u003c") + "))",
        1,
    )
    stats_mount = """if (page === 'regions.html') {
      const toggle = doc.createElement('details');
      const label = doc.createElement('summary');
      label.textContent = '民俗样本统计 · 收起';
      label.style.cssText = 'cursor:pointer;color:#244d67;padding:8px 0;font-weight:600';
      toggle.append(label);
      doc.getElementById('records')?.after(toggle);
      toggle.open = true;
      toggle.addEventListener('toggle', () => {
        label.textContent = toggle.open ? '民俗样本统计 · 收起' : '展开民俗样本统计';
        if (!toggle.open || toggle.querySelector('iframe')) return;
        const chart = doc.createElement('iframe');
        chart.title = '民俗样本统计';
        chart.style.cssText = 'display:block;width:100%;height:min(80vh,820px);border:0;border-radius:10px';
        chart.srcdoc = """ + json.dumps(stats_html, ensure_ascii=False).replace("</", r"<\/") + """;
        chart.onload = () => {
          const body = chart.contentDocument.body;
          new ResizeObserver(() => { if (toggle.open && body.offsetHeight) chart.style.height = Math.ceil(body.getBoundingClientRect().height) + 'px'; }).observe(body);
        };
        toggle.append(chart);
      });
    }"""
    html = html.replace(hook, stats_mount + "\n" + hook, 1)
    html = html.replace(hook, qwen_demos + "\n" + hook, 1)
    html = html.replace(hook, "    if (isStory(page)) {\n" + notes_script + "\n}\n" + hook, 1)
    if story in {Path(name).stem for name in PAGES[3:]}:
        html = html.replace("\nnavigate('index.html');", "\nnavigate(" + json.dumps(story + ".html") + ");", 1)
    # Lift the desktop Macao photo and bow its guide above the entry button.
    html = html.replace("--cx:9%;--cy:76%", "--cx:9%;--cy:72%", 1)
    straight_guide = "  path.setAttribute('d','M '+x+' '+y+' L '+(cx+dx*edge)+' '+(cy+dy*edge));"
    curved_guide = """  const endX = cx + dx * edge, endY = cy + dy * edge;
  const guide = path.dataset.to === 'macao' && area.width > 680
    ? ' Q ' + (x + (endX - x) * 0.35) + ' ' + (Math.min(y, endY) - 34) + ' '
    : ' L ';
  path.setAttribute('d', 'M ' + x + ' ' + y + guide + endX + ' ' + endY);"""
    html = html.replace(straight_guide, curved_guide, 1)
    lookup_style += (ROOT / "featured-spacing.css").read_text(encoding="utf-8")
    lookup_style += (ROOT / "voice-assistant.css").read_text(encoding="utf-8")
    mobile_css = (ROOT / "mobile-home.css").read_text(encoding="utf-8")
    html = html.replace("'</style></head>'", json.dumps("</style><style>" + mobile_css + "</style></head>"))
    html = html.replace(
        "themeCSS+(storyArt[page]||'')",
        "themeCSS+(storyArt[page]||'').replaceAll('html body .page #form::after','html body .page #form + section::before')" + " + (storyArt[page] ? " + json.dumps(source_style + reading_style) + " : '')"
        + " + (page === 'regions.html' ? " + json.dumps(gallery_style + gallery_toolbar_style + (ROOT / 'regions-polish.css').read_text(encoding='utf-8')) + " : '')"
        + " + " + json.dumps(lookup_style),
        1,
    )


    # Remove the old control in the entrypoint so a hot reload cannot retain it.
    switch_block = re.compile(r"    if \(page === 'featured.html'\) \{\n      const button = doc.createElement\('button'\);[\s\S]*?      doc.querySelector\('main'\)\?\.prepend\(button\);\n    \}")
    html, removed = switch_block.subn('', html, count=1)
    if removed != 1:
        raise ValueError('Featured script switch hook changed')
    from release_quality import improve_release
    html = improve_release(html, ROOT)
    voice_script = (ROOT / 'voice-assistant.js').read_text(encoding='utf-8')
    from release_quality import replace_once
    html = replace_once(html, "function navigate(page, hash = '', tab = '') {",
                        voice_script + "\nfunction navigate(page, hash = '', tab = '') {")
    html = replace_once(html, '  const sequence = ++navigationSequence;',
                        '  ziliVoiceGuide?.destroy();\n  ziliVoiceGuide = null;\n  const sequence = ++navigationSequence;')
    return replace_once(html, '    bindShareLink(doc, page);',
                        '    bindShareLink(doc, page);\n    bindZiliVoiceGuide(doc);')


release_html = ROOT / "published-theme.html"
if release_html.is_file():
    assets = [release_html, *(ROOT / name for name in (
        "reading-edition.css", "reading-notes.js", "cover-lettering.css", "qwen-demos.js", "mobile-home.css", "folk-stats.html", "release_fixes.py", "opencc-full.gz.b64",
        "zili-lookup-results.js", "zili-lookup-results-original.js", "cases.json", "release_quality.py", "release_runtime.js", "dictionary-cache.json", "qwen-component/asset-manifest.json", "guide.html", "regions-polish.css", "stats-3d.js", "stats-3d.css", "featured-spacing.css", "voice-assistant.js", "voice-assistant.css"
    ))]
    assets.extend(path for path in (ROOT / "static" / "atlas").rglob("*") if path.is_file())
    assets.extend(path for path in ROOT.iterdir() if path.suffix.lower() in (".webp", ".png", ".jpg"))
    version = tuple((str(path.relative_to(ROOT)), path.stat().st_mtime_ns, path.stat().st_size) for path in sorted(set(assets)))
    story = st.query_params.get("story", "")
    site = declare_component("zili_site", path=str(ROOT / "qwen-component"))
    previous = st.session_state.get("qwen_response")
    request = site(
        html=published_story_theme(release_html, story, version),
        site_key=json.dumps([story, version]),
        response=previous, key="zili_site",
    )
    if isinstance(request, dict) and isinstance(request.get("id"), str):
        if not previous or request["id"] != previous["id"]:
            # Reuse successful answers to the same question in this browser session.
            catalogue_bytes = (ROOT / "cases.json").read_bytes()
            catalogue = json.loads(catalogue_bytes)
            signature = (hashlib.sha256(catalogue_bytes).hexdigest(), PROMPT_VERSION,
                         str(config(st.secrets, 'QWEN_MODEL', 'qwen-plus')),
                         str(config(st.secrets, 'QWEN_BASE_URL', ''))) + tuple(str(request.get(field, "")).strip() for field in (
                "mode", "story", "question", "character", "dictionary"
            ))
            answers = st.session_state.setdefault("qwen_recent_answers", {})
            cached = answers.get(signature)
            response = cached[1] if isinstance(cached, tuple) and time() - cached[0] < 600 else None
            invalid = validate_request(request)
            if invalid:
                response = {'error': invalid}
            if response is None:
                from request_limits import allow_request
                permitted = allow_request(st.session_state)
                try:
                    response = qwen_answer(request, catalogue, st.secrets) if permitted else {"error": "提问较频繁，请稍等片刻再试。仍可使用地区筛选和关键词搜索。"}
                except Exception:
                    logging.exception('Qwen service failed')
                    response = {'error': '问答暂时无法完成，请稍后重试。故事和关键词搜索仍可使用。'}
                if "error" not in response:
                    if len(answers) >= 24:
                        answers.pop(next(iter(answers)))
                    answers[signature] = (time(), response)
            st.session_state.qwen_response = {"id": request["id"], **response}
            st.rerun()
    st.stop()

site_payload = bundle_site(site_version())
render_html("""<!doctype html><meta charset="utf-8"><style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#e9decd}
*{box-sizing:border-box}
#layout{display:grid;grid-template-columns:clamp(244px,24vw,320px) minmax(0,1fr);height:100dvh}
#layout.home{grid-template-columns:minmax(0,1fr)}
#directory{overflow:auto;background:#f9f0de;border-right:1px solid #d7c2a4;padding:28px 20px;color:#473326;font:16px/1.65 system-ui,sans-serif}
#directory[hidden]{display:none}
.brand{font:700 32px KaiTi,serif;color:#84281e}.subtitle{font-size:14px;color:#705946;margin:4px 0 23px}
#directory nav{display:grid;gap:8px}
#directory button{width:100%;border:0;border-radius:9px;background:transparent;text-align:left;padding:11px 14px;color:inherit;font:inherit;cursor:pointer}
#directory button:hover:not([aria-current]){background:#f0e0c5}
#directory button[aria-current]{background:#8c291e;color:white}
#directory button:focus-visible{outline:2px solid #a35a23;outline-offset:2px}
#directory small{display:block;font-size:13px;opacity:.86}
iframe{display:block;width:100%;height:100%;min-height:0;border:0}
@media(max-width:660px){#layout{grid-template-columns:1fr;grid-template-rows:auto minmax(0,1fr)}#layout.home{grid-template-rows:minmax(0,1fr)}#directory{border-right:0;border-bottom:1px solid #d7c2a4;padding:10px 13px}.brand{font-size:24px}.subtitle,#directory small{display:none}#directory nav{grid-template-columns:repeat(3,minmax(0,1fr));gap:4px;margin-top:7px}#directory button{padding:7px 4px;min-height:40px;text-align:center;font-size:14px}}
</style><style>
#layout:not(:has(#directory[hidden])){background:#102c3c}
#directory{background:linear-gradient(155deg,#1b4154,#102b3b 70%);color:#edf7f7;border-right-color:#386173}
#directory :is(h1,h2,strong,.brand){color:#fff3dd}
#directory small{color:#b9d1d7}
#directory button:hover:not([aria-current]){background:#254b5e}
#directory button[aria-current]{background:#26586c;box-shadow:inset 3px 0 #7dd9df;color:#fff}
#directory button:focus-visible{outline-color:#8de4ee}
</style>
<div id="layout" class="home">
<aside id="directory" hidden><div class="brand">字里寻踪</div><p class="subtitle">文字里的故事</p><nav aria-label="功能目录">
<button type="button" data-tab="home">首页<small>回到封面入口</small></button>
<button type="button" data-tab="featured">精选寻踪<small>沿一个字读完整故事</small></button>
<button type="button" data-tab="regions">四海故事<small>按地区浏览生活记录</small></button>
<button type="button" data-tab="lookup">自由查字<small>输入或选择感兴趣的字</small></button>
<button type="button" data-tab="keepsake">我的寻踪卡<small>带走想记住的生活细节</small></button>
<button type="button" data-tab="sources">资料与来源<small>查看原文与素材说明</small></button>
<button type="button" data-tab="guide">使用说明<small>操作步骤与体验指南</small></button>
</nav></aside><iframe title="字里寻踪" id="site"></iframe></div>
<script>
(async () => {
const packed = '""" + site_payload + """';
const bytes = Uint8Array.from(atob(packed), character => character.charCodeAt(0));
const decompressed = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
const {pages, images, variants, strokes} = await new Response(decompressed).json();
window.ziliVariantPairs = variants.pairs;
window.ziliSameForms = new Set(variants.same);
window.ziliVariants = Object.fromEntries(Object.entries(variants.pairs).map(([char, [simple, traditional]]) =>
  [char, [...new Set([...simple, ...traditional])].filter(form => form !== char)]));
window.ziliStrokeData = strokes;
window.ziliImage = name => images[name] || name;
const frame = document.getElementById('site');
const directory = document.getElementById('directory');
const layout = document.getElementById('layout');
let current = 'index.html', lastStory = '';
let lookupScroll = 0;
const keepsakePage = 'keepsakes.html';
const keepsakeKey = 'zili-keepsakes-v1';
let savedKeepsakes = [];
try {
  const stored = JSON.parse(localStorage.getItem(keepsakeKey) || '[]');
  if (Array.isArray(stored)) savedKeepsakes = stored.filter(item =>
    item && typeof item.id === 'string' && Object.hasOwn(pages, item.page));
} catch {}
window.ziliSaveKeepsake = (record, image) => {
  const item = {
    id: record.id, page: current, character: frame.contentDocument.body.dataset.character || '年',
    place: record.place, title: record.title, detail: record.recorded_action || record.body, image
  };
  savedKeepsakes = [item, ...savedKeepsakes.filter(entry => entry.id !== item.id)];
  try {
    localStorage.setItem(keepsakeKey, JSON.stringify(savedKeepsakes));
    return true;
  } catch {
    return false;
  }
};
pages[keepsakePage] = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>已保存的寻踪卡</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3ebdd;color:#34271e;font:16px/1.65 system-ui,sans-serif}
main{margin:auto;padding:26px 0;max-width:1208px}h1{margin:0 0 8px;font:700 clamp(1.8rem,4vw,2.8rem) KaiTi,serif}
a{color:#79271a;font-weight:700}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:16px}
article{border:1px solid #d6b995;background:#fff9ee;border-radius:12px;overflow:hidden}
article div{padding:15px}article h2{margin:4px 0 8px;font-size:1.2rem}
article img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}small{color:#79271a;font-weight:700}
</style></head><body><main><h1>已保存的寻踪卡</h1><p id="saved-count"></p><div class="cards" id="saved-cards"></div></main></body></html>`;
pages["guide.html"] = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>使用说明</title><style>*{box-sizing:border-box}body{margin:0;color:#344e60;font:16px/1.85 system-ui,sans-serif;background:linear-gradient(145deg,#faf8f2,#eff4f5 52%,#dcebf3);min-height:100vh}main{margin:auto;padding:clamp(24px,4vw,60px);max-width:1100px}h1{font:700 clamp(32px,5vw,52px) KaiTi,serif;margin:0}h2{font-size:1.25rem;margin:0 0 8px}p{margin:0 0 12px}.guide-card{background:#ffffffa8;border:1px solid #cbdde4;border-radius:12px;padding:22px;margin:18px 0;box-shadow:0 5px 18px #344e600b}.num{color:#54778b;margin-right:12px}.flow{display:grid;gap:8px;text-align:center;max-width:650px;margin:auto}.node{border:1px solid #adc7d5;background:#edf5f8;border-radius:8px;padding:12px}.branches{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.arrow{color:#54778b;font-size:22px}pre{white-space:pre-wrap;background:#e7eff2;padding:14px;border-radius:8px}a{color:#315d77}</style></head><body><main><small>USER GUIDE · 体验指南</small><h1>使用说明</h1><p>从一个汉字出发，探索两岸四海的生活印记。本作品以汉字、字形演变与民俗故事为线索，帮助用户发现不同地域之间的文化联系。</p><section class="guide-card"><h2>用户交互流程图</h2><div class="flow" role="group" aria-label="用户交互流程"><div class="node">访问网页 · 进入首页</div><div class="arrow">↓</div><div class="node">选择地区或进入精选寻踪</div><div class="arrow">↓</div><div class="branches"><div class="node">精选寻踪</div><div class="node">四海故事</div><div class="node">自由查字</div></div><div class="arrow">↓</div><div class="node">阅读字形与文化资料 · 选择故事</div><div class="arrow">↓</div><div class="branches"><div class="node">继续探索</div><div class="node">保存寻踪卡</div><div class="node">查看资料来源</div></div></div></section><section class="guide-card"><h2><span class="num">01</span>快速开始</h2><p>打开线上网址，等待首页加载。选择你的地区，或点击「同一个字，也有不同写法」进入精选寻踪。进入后可通过左侧功能区切换页面。</p></section><section class="guide-card"><h2><span class="num">02</span>精选寻踪</h2><p>选择年、门、茶、船、灯、圆中的一个字。阅读字形观察与文化介绍，按页面提示观看字形演变、笔顺演示，再浏览不同地区的民俗案例。点击感兴趣的故事，阅读生活细节与文化联系。</p></section><section class="guide-card"><h2><span class="num">03</span>四海故事</h2><p>点击左侧「四海故事」，按地区浏览案例。选择感兴趣的记录进入故事页，对照不同地方的生活习俗，再通过汉字切换入口继续探索。</p></section><section class="guide-card"><h2><span class="num">04</span>自由查字</h2><p>点击「自由查字」，输入一个感兴趣的汉字并查询。查看字典释义、关联字形及可用的笔顺资料；六个精选汉字还可进入对应民俗故事。外部字典或在线查询服务可能受网络影响。</p></section><section class="guide-card"><h2><span class="num">05</span>我的寻踪卡</h2><p>在故事页找到寻踪卡区域，选择想记住的生活记录并按页面提示保存。进入「我的寻踪卡」查看已保存的内容，点击回到故事可继续阅读。收藏保存在当前浏览器，清除浏览器数据或更换设备可能无法找回。</p></section><section class="guide-card"><h2><span class="num">06</span>资料与来源</h2><p>进入故事后点击「资料与来源」，查看原文链接、文化资料及素材说明。建议结合原始出处阅读，区分史料、民俗记录与设计示意。</p></section><section class="guide-card"><h2><span class="num">07</span>简繁体与设备</h2><p>可在自由查字中查看汉字的简繁关联字形，也可在首页选择地区浏览故事。推荐使用最新版 Chrome、Edge 或 Safari 浏览器；电脑宽屏体验更完整。移动设备可滚动阅读，部分布局可能不同。</p></section><section class="guide-card"><h2><span class="num">08</span>线上访问与技术部署</h2><p>普通用户无需下载或安装软件，直接打开 https://zili-xunzong.streamlit.app/ 即可体验。项目通过 GitHub 托管源代码与素材，Streamlit Community Cloud 从 gh-pages 分支读取 streamlit_app.py 并运行。开发者可获取该分支代码，在项目目录执行下方命令；在线查询功能可能还需要服务配置。</p><pre>git clone -b gh-pages &lt;仓库地址&gt;<br>cd huacan-award<br>python -m pip install -r requirements.txt<br>python -m streamlit run streamlit_app.py</pre><p><a href="https://zili-xunzong.streamlit.app/" target="_blank" rel="noopener">打开线上作品</a></p></section><section class="guide-card"><h2><span class="num">09</span>常见问题</h2><p>首次加载较慢时请等待云端启动；若页面异常，可刷新或稍后重试。查不到汉字时请确认只输入一个汉字，并尝试简繁体写法。收藏未显示时请确认使用同一浏览器，且未禁用本地存储。</p></section></main></body></html>`;
function renderKeepsakes(doc) {
  const add = (parent, tag, value = '') => {
    const node = doc.createElement(tag);
    node.textContent = value;
    parent.append(node);
    return node;
  };
  const count = doc.getElementById('saved-count');
  count.textContent = savedKeepsakes.length ? savedKeepsakes.length + ' 条已保存' : '还没有收藏。';
  if (!savedKeepsakes.length) add(count, 'a', ' 去看看故事 →').href = lastStory || 'featured.html';
  const cards = doc.getElementById('saved-cards');
  for (const item of savedKeepsakes) {
    const card = add(cards, 'article');
    if (images[item.image]) {
      const image = add(card, 'img');
      image.src = images[item.image];
      image.alt = '';
    }
    const body = add(card, 'div');
    add(body, 'small', item.character + ' · ' + item.place);
    add(body, 'h2', item.title);
    add(body, 'p', item.detail);
    add(body, 'a', '回到故事 →').href = item.page + '#' + item.id;
  }
}
const isStory = page => /^(nian|men|cha|chuan|deng|yuan)\\.html$/.test(page);
function selectTab(key) {
  for (const button of directory.querySelectorAll('[data-tab]')) {
    if (button.dataset.tab === key) button.setAttribute('aria-current','page');
    else button.removeAttribute('aria-current');
  }
}
function goToSection(doc, hash) {
  const node = doc.getElementById(hash === 'sources' && !doc.getElementById('sources') ? 'journey-sources' : hash);
  if (!node) return;
  if (node.tagName === 'DETAILS') node.open = true;
  const view = frame.contentWindow;
  const offset = Number.parseFloat(view.getComputedStyle(node).scrollMarginTop) || 0;
  view.scrollTo(0, view.scrollY + node.getBoundingClientRect().top - offset);
}
function activateLocal(doc, key) {
  if (key === 'lookup') {
    const trigger = doc.querySelector('[data-open-story-lookup]');
    if (trigger) {
      if (doc.body.classList.contains('lookup-only')) return;
      lookupScroll = frame.contentWindow.scrollY;
      const input = doc.getElementById('hanzi');
      input.value = '';
      input.dispatchEvent(new frame.contentWindow.Event('input', {bubbles:true}));
      trigger.click();
      doc.body.classList.add('lookup-only');
      frame.contentWindow.scrollTo(0, 0);
      return;
    }
    goToSection(doc, 'lookup');
    doc.getElementById('hanzi')?.focus({preventScroll:true});
    return;
  }
  goToSection(doc, key);
}
const traditionalRegions = new Set(['台湾', '香港', '澳门']);
const mainlandPlaces = /大陆|大陸|浙江|贵州|貴州|杭州|宁波|寧波|贵阳|貴陽|遵义|遵義|福建|泉州|厦门|廈門|北京|上海|广东|廣東|江苏|江蘇|山东|山東|四川|湖南|湖北|江西|安徽|云南|雲南|陕西|陝西|河南|河北|山西|甘肃|甘肅|青海|广西|廣西|海南|吉林|辽宁|遼寧|黑龙江|黑龍江|内蒙古|內蒙古|重庆|重慶|天津|新疆|宁夏|寧夏|西藏/;
const traditionalPlaces = /台湾|臺灣|台灣|臺北|台北|台中|臺中|台南|臺南|高雄|新北|桃園|桃园|宜蘭|宜兰|花蓮|花莲|金門|金门|香港|澳[門门]/;
let traditionalUI = false;
const standardTraditional = new Map(
  Object.entries(variants.pairs).filter(([, [simple, traditional]]) => !simple && [...traditional].length === 1)
    .map(([char, [, traditional]]) => [char, traditional])
);
standardTraditional.set('灯', '燈');
const originalDirectoryText = new WeakMap();
function traditionalText(text) {
  return [...text.replaceAll('字里寻踪', '字裡尋蹤').replaceAll('台湾', '臺灣').replaceAll('里面', '裡面')]
    .map(char => standardTraditional.get(char) || char).join('');
}
function applyDirectoryScript() {
  const walker = document.createTreeWalker(directory, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (!originalDirectoryText.has(node)) originalDirectoryText.set(node, node.nodeValue);
    const original = originalDirectoryText.get(node);
    node.nodeValue = traditionalUI ? traditionalText(original) : original;
  }
}
function localizeStory(doc) {
  const skip = 'script,style,code,textarea,blockquote,#sources,#journey-sources,#comparison,[data-source-notes],.story-evidence,#lookup-result,#lookup-status,#glyph-dialog,#record-quote';
  function convert(node) {
    if (node.nodeType !== 3 || !node.parentElement || node.parentElement.closest(skip)) return;
    const mapped = traditionalText(node.nodeValue);
    if (mapped !== node.nodeValue) node.nodeValue = mapped;
  }
  function walk(node) {
    if (node.nodeType === 3) { convert(node); return; }
    const walker = doc.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    for (let text = walker.nextNode(); text; text = walker.nextNode()) convert(text);
  }
  doc.documentElement.lang = 'zh-TW';
  doc.title = traditionalText(doc.title);
  walk(doc.body);
  const observer = new MutationObserver(changes => {
    for (const change of changes) {
      if (change.type === 'characterData') convert(change.target);
      else for (const node of change.addedNodes) walk(node);
    }
  });
  observer.observe(doc.body, {childList:true, subtree:true, characterData:true});
  doc.defaultView.addEventListener('pagehide', () => observer.disconnect(), {once:true});
}
function bindRegionEntry(doc) {
  const mapReader = doc.getElementById('map-reader');
  for (const mapButton of doc.querySelectorAll('button.map-zoom')) {
    mapButton.addEventListener('click', () => {
      const style = doc.defaultView.getComputedStyle(mapButton);
      const art = doc.getElementById('map-reader-art');
      const title = mapButton.getAttribute('aria-label');
      doc.getElementById('map-reader-title').textContent = title;
      art.setAttribute('aria-label', title);
      art.toggleAttribute('data-central', mapButton.classList.contains('zoom-3'));
    art.toggleAttribute('data-strait', mapButton.classList.contains('zoom-0'));
    art.replaceChildren();
    const markers = mapButton.querySelector('.region-markers');
    if (markers) art.append(markers.cloneNode(true));
      art.style.aspectRatio = mapButton.offsetWidth + ' / ' + mapButton.offsetHeight;
      art.style.backgroundImage = style.backgroundImage;
      art.style.backgroundBlendMode = style.backgroundBlendMode;
      art.style.backgroundColor = style.backgroundColor;
      art.style.backgroundRepeat = style.backgroundRepeat;
      art.style.backgroundSize = style.backgroundSize;
      art.style.backgroundPosition = style.backgroundPosition;
      mapReader.showModal();
    });
  }
  const picker = doc.getElementById('region-picker');
  const input = doc.getElementById('region-input');
  const enter = region => {
    traditionalUI = traditionalRegions.has(region);
    navigate('featured.html');
  };
  doc.querySelectorAll('[data-region]').forEach(button => {
    button.addEventListener('click', () => enter(button.dataset.region));
  });
  const enterTypedRegion = () => {
    const value = input.value.trim();
    if (/海外|華僑|华侨|新加坡|马来西亚|馬來西亞/.test(value)) enter('海外华侨');
    else if (/香港/.test(value)) enter('香港');
    else if (/澳[門门]/.test(value)) enter('澳门');
    else if (traditionalPlaces.test(value)) enter('台湾');
    else if (mainlandPlaces.test(value)) enter('大陆');
    else {
      const help = doc.getElementById('region-help');
      help.textContent = '暂未识别该地区，可在下拉框选择最符合的一项。';
      help.setAttribute('data-error', '');
    }
  };
  doc.getElementById('region-form').addEventListener('submit', event => {
    event.preventDefault();
    enterTypedRegion();
  });
  input.addEventListener('keydown', event => {
    if (event.key !== 'Enter' || event.isComposing || event.keyCode === 229) return;
    event.preventDefault();
    enterTypedRegion();
  });
  doc.getElementById('region-default-entry').addEventListener('click', event => {
    event.preventDefault();
    event.stopPropagation();
    enter('大陆');
  });
  doc.addEventListener('click', event => {
    if (!picker.contains(event.target)) picker.open = false;
  });
  picker.addEventListener('keydown', event => {
    if (event.key === 'Escape' && picker.open) {
      picker.open = false;
      picker.querySelector('summary').focus();
    }
  });
}
function navigate(page, hash = '', tab = '') {
  if (!Object.hasOwn(pages, page)) return;
  current = page;
  if (isStory(page)) lastStory = page;
  const cover = page === 'index.html' && tab !== 'lookup';
  const selected = tab || (page === keepsakePage ? 'keepsake' : page === 'regions.html' ? 'regions' : cover ? 'home' : 'featured');
  directory.hidden = cover;
  layout.classList.toggle('home', cover);
  selectTab(selected);
  applyDirectoryScript();
  frame.onload = () => {
    const doc = frame.contentDocument;
    if (page === keepsakePage) renderKeepsakes(doc);
    if (savedKeepsakes.length) {
      const collectionLink = doc.getElementById('keepsake-collection-link');
      if (collectionLink) collectionLink.hidden = false;
    }
    if (cover) bindRegionEntry(doc);
    if (!cover && traditionalUI) localizeStory(doc);

    if (hash) activateLocal(doc, hash);
    const close = doc.getElementById('close-story-lookup');
    const restoreStory = () => {
      if (!doc.body.classList.contains('lookup-only')) return;
      doc.body.classList.remove('lookup-only');
      frame.contentWindow.scrollTo(0, lookupScroll);
      selectTab('featured');
    };
    close?.addEventListener('click', restoreStory);
    doc.getElementById('story-lookup')?.addEventListener('keydown', event => {
      if (event.key === 'Escape') restoreStory();
    });
    doc.addEventListener('click', event => {
      const anchor = event.target.closest('a[href]');
      if (!anchor || anchor.hasAttribute('download')) return;
      const href = anchor.getAttribute('href');
      if (!href || /^(?:[a-z]+:|\\/\\/)/i.test(href)) return;
      if (href.startsWith('#')) {
        event.preventDefault();
        const id = href.slice(1);
        if (id === 'keepsake' || id === 'sources' || id === 'journey-sources') selectTab(id === 'journey-sources' ? 'sources' : id);
        goToSection(doc, id);
        return;
      }
      const [path, fragment] = href.split('#');
      const next = path === './' ? 'index.html' : path.replace(/^\\.\\//, '');
      if (!Object.hasOwn(pages, next)) return;
      event.preventDefault();
      if (next === 'index.html' && fragment === 'lookup') {
        openFunction('lookup');
        return;
      }
      navigate(next, fragment);
    });
  };
  const innerStyles = cover ? '' : '<style>.demo-shell,.journey-layout{display:block!important;width:100%;max-width:none;margin:0}.demo-shell>.page,.journey-layout>.page{width:100%;max-width:none;margin:0;min-height:100dvh;box-shadow:none}.demo-shell>.directory,.journey-layout>.journey-sidebar{display:none!important}body>main,.sheet>main{width:calc(100% - 2 * clamp(14px,3vw,44px));max-width:none}.lookup-only .page>header,.lookup-only main>:not(#story-lookup){display:none!important}.lookup-only .page{min-height:100dvh}</style>';
  const lookupLanding = page === 'index.html' && tab === 'lookup'
    ? '<style>.globe-cover{width:min(92%,620px);aspect-ratio:auto;padding:28px 12px;background:none;overflow:visible}.globe-cover .globe-art,.globe-cover .globe-start{display:none}.globe-cover .globe-search{position:static;width:100%;height:46px}</style>'
    : '';
  const lookupSizing = cover ? '' : '<style>.story-lookup .story-lookup-form,.globe-cover .globe-search{min-height:52px;grid-template-columns:minmax(0,1fr) 84px 64px}.story-lookup .story-lookup-form{max-width:700px}.story-lookup .story-lookup-form>*,.globe-cover .globe-search>*{font-size:16px}.story-lookup-form select,.globe-search select{padding-inline:10px}@media(max-width:420px){.story-lookup .story-lookup-form,.globe-cover .globe-search{grid-template-columns:minmax(0,1fr) 74px 56px}}</style>';
  const creditStyle = '<style>.lookup-credit{margin:7px 0 0;color:#695849;font:clamp(11px,2.4vw,14px)/1.3 system-ui,sans-serif}.cover-credit{max-width:650px;margin:0 auto;padding:0 16px 10px;text-align:center}.globe-cover .lookup-credit{position:absolute;top:146cqw;left:7.7%;width:84.8%;margin:0;text-align:center;font-size:clamp(10px,1.8cqw,12px)}.globe-cover:has(.globe-search) .lookup-credit a{color:inherit}.globe-cover.lookup-credit-flow .lookup-credit{position:static;width:auto;margin-top:7px}</style>';
  const credit = '<p class="lookup-credit">萌典提供读音、部首、笔画和释义；Unicode Unihan 识别简繁关联；Hanzi Writer 在精选字的字形弹窗里演示笔顺。</p>';
  const pageHtml = pages[page].replace(
    /(<form class="(?:globe-search|story-lookup-form)"[^>]*>[\\s\\S]*?<\\/form>)/,
    '$1' + (cover ? '' : credit)
  );
  const attributedPage = cover ? `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>字里寻踪：文字里的故事</title></head><body>
<div id="cover" class="terrain-cover">
 <div class="terrain-scene" role="group" aria-label="台湾、香港和澳门地标投影示意">
 <div class="terrain-photo" aria-hidden="true"></div><div class="terrain-repair repair-upper" aria-hidden="true"></div><div class="terrain-repair repair-lower" aria-hidden="true"></div><div class="terrain-repair repair-inset" aria-hidden="true"></div>
 <svg class="terrain-beams" aria-hidden="true"><defs><marker id="photo-tip" viewBox="0 0 12 12" markerUnits="userSpaceOnUse" markerWidth="17" markerHeight="17" refX="11" refY="6" orient="auto"><polygon points="0,0 12,6 0,12 3,6" fill="#b9ffff"/></marker></defs><g fill="none" stroke="#95faff" marker-end="url(#photo-tip)"><path data-to="macao"/><path data-to="hongkong"/><path data-to="taiwan"/></g></svg>
 <div class="projection macao" style="--x:65.6%;--y:76.4%;--cx:9%;--cy:76%">
 <i class="beacon" aria-hidden="true"></i><span class="terrain-place">澳门</span>
 <div class="landmark"><button type="button" class="peek" data-caption="观音莲花苑观音像" aria-label="放大查看澳门观音莲花苑" title="放大查看澳门观音莲花苑"><img class="full-scene" src="home-macao.webp" alt="澳门观音莲花苑"></button></div></div><div class="projection hongkong" style="--x:67.8%;--y:75.9%;--cx:94%;--cy:33%">
 <i class="beacon" aria-hidden="true"></i><span class="terrain-place">香港</span>
 <div class="landmark"><button type="button" class="peek" data-caption="金紫荆雕塑" aria-label="放大查看香港金紫荆" title="放大查看香港金紫荆"><img class="full-scene" src="home-hongkong.webp" alt="香港金紫荆"></button></div></div><div class="projection taiwan" style="--x:81%;--y:65.1%;--cx:92%;--cy:81%">
 <i class="beacon" aria-hidden="true"></i><span class="terrain-place">台湾</span>
 <div class="landmark"><button type="button" class="peek" data-caption="台北 101" aria-label="放大查看台北 101" title="放大查看台北 101"><img class="full-scene" src="home-taiwan.webp" alt="台北 101"></button></div></div></div>
 <header class="terrain-heading"><h1>字里寻踪</h1><p>文字里的故事</p></header>
 <div class="terrain-entry"><a class="cover-start" href="featured.html" id="region-default-entry">同一个字，也有不同写法</a>
  <form class="region-entry" id="region-form">
    <label for="region-input">你来自哪里？</label>
    <div class="region-field">
      <input id="region-input" placeholder="手动输入地区" autocomplete="off" enterkeyhint="go" aria-describedby="region-help">
      <details id="region-picker">
        <summary>选择地区 <span class="region-arrow" aria-hidden="true"></span></summary>
        <div class="region-options">
          <button type="button" data-region="大陆">大陆</button>
          <button type="button" data-region="台湾">台湾</button>
          <button type="button" data-region="香港">香港</button>
          <button type="button" data-region="澳门">澳门</button>
          <button type="button" data-region="海外华侨">海外华侨</button>
        </div>
      </details>
    </div>
    <p class="help" id="region-help" role="status">选择后直接进入。手动输入后，按回车进入。</p>
  </form></div></div><style>.terrain-cover[hidden]{display:none}
.terrain-cover{min-height:100svh;position:relative;isolation:isolate;background:#0b2436;color:#fffaf0;display:grid;grid-template-rows:1fr auto}
.terrain-scene{position:absolute;inset:0;overflow:hidden;container-type:size}
.terrain-photo{position:absolute;inset:0;background:linear-gradient(180deg,#07192287,transparent 30%,transparent 63%,#081a29e6),url(home-terrain-reference.webp) center/100% 100% no-repeat}
.terrain-beams{position:absolute;inset:0;width:100%;height:100%;filter:drop-shadow(0 0 5px #67efff)}
.terrain-heading{position:relative;text-align:center;align-self:start;justify-self:center;margin:.5vh 0 0;text-shadow:0 2px 12px #001520}
.terrain-heading h1{margin:0;font:700 clamp(42px,6vw,96px)/1.15 KaiTi,serif;letter-spacing:.12em}
.terrain-heading p{margin:8px 0;font-size:clamp(16px,2vw,24px);letter-spacing:.18em}
.beacon,.terrain-place,.landmark{position:absolute}
.beacon{left:var(--x);top:var(--y);width:25px;height:14px;border:2px solid #b5fbff;border-radius:50%;transform:translate(-50%,-50%);background:#8deefa77;box-shadow:0 0 0 5px #68e9f93b,0 0 19px #7df8ff}
.terrain-place{left:var(--x);top:var(--y);transform:translate(-50%,10px);padding:2px 7px;border-radius:5px;background:#052035df;color:#e5ffff;font-size:.83rem;white-space:nowrap}
.macao .terrain-place{transform:translate(-95%,10px)}.hongkong .terrain-place{transform:translate(8%,10px)}
.landmark{left:var(--cx);top:var(--cy);transform:translate(-50%,-100%);width:clamp(82px,11vw,158px);text-align:center;border:1px solid #87f2ff8c;border-radius:8px;background:linear-gradient(#0c4064a0,#074167dc);color:#edfeff;padding:8px;box-shadow:0 0 20px #53d9ff63;backdrop-filter:blur(2px)}
.landmark strong{font-size:clamp(11px,1.15vw,17px)}
.architecture{height:clamp(50px,10vh,110px);width:70%;margin:auto;background:repeating-linear-gradient(0deg,#b8fbffb0 0 1px,transparent 1px 7px),linear-gradient(90deg,#5fe3f599,#d7ffff);}
.taiwan .architecture{clip-path:polygon(48% 0,52% 0,52% 12%,64% 12%,64% 22%,68% 22%,68% 32%,72% 32%,72% 42%,76% 42%,76% 52%,79% 52%,79% 69%,84% 69%,84% 91%,92% 91%,92% 100%,8% 100%,8% 91%,16% 91%,16% 69%,21% 69%,21% 52%,24% 52%,24% 42%,28% 42%,28% 32%,32% 32%,32% 22%,36% 22%,36% 12%,48% 12%)}
.hongkong .architecture{background:repeating-linear-gradient(36deg,transparent 0 12px,#d9ffffb5 12px 14px),repeating-linear-gradient(-36deg,#2d97c570 0 12px,#d9ffffa0 12px 14px);clip-path:polygon(24% 100%,24% 48%,47% 22%,47% 0,50% 0,50% 21%,67% 35%,67% 8%,70% 8%,70% 38%,83% 54%,83% 100%)}
.macao .architecture{height:clamp(44px,7vh,82px);background:radial-gradient(ellipse at 50% 83%,#13465f 0 10%,transparent 11%),radial-gradient(ellipse at 22% 83%,#13465f 0 8%,transparent 9%),radial-gradient(ellipse at 78% 83%,#13465f 0 8%,transparent 9%),repeating-linear-gradient(0deg,#dcffff 0 1px,#73c5d8 1px 9px);clip-path:polygon(0 100%,0 55%,18% 55%,18% 35%,32% 35%,32% 18%,44% 18%,44% 9%,48% 9%,48% 0,52% 0,52% 9%,56% 9%,56% 18%,68% 18%,68% 35%,82% 35%,82% 55%,100% 55%,100% 100%)}
.terrain-entry{position:relative;justify-self:center;width:min(92%,535px);padding:0 0 5vh}
.terrain-entry .cover-start{position:static;min-height:44px;height:auto;width:fit-content;padding:9px 20px;margin:0 auto 9px;color:#fffaf2;background:#88291d;border-radius:999px;font:700 1rem system-ui,sans-serif;text-decoration:none}
.terrain-entry .region-entry{position:relative;inset:auto;width:100%;height:auto;margin:0}
.terrain-entry label,.terrain-entry .help{position:static;clip-path:none;width:auto;height:auto;color:#fff4df}
.terrain-entry .region-field input{position:static;width:100%;min-height:46px;background:#fff9ec;color:#34271e;font-size:16px}
.terrain-entry .region-field input::placeholder{color:#756455}
.terrain-entry .region-field details{width:auto}
.terrain-entry .region-field summary,.terrain-entry .region-field details[open] summary{min-width:100px;color:#702117;background:#f0e1cb;border-radius:0 999px 999px 0}
.terrain-entry .region-options{top:auto;bottom:calc(100% + 5px)}
@media(max-width:680px){.terrain-cover{min-height:680px}.terrain-photo{background-size:100% 100%}.terrain-heading{margin-top:2vh}.landmark{width:72px;padding:4px}.architecture{height:55px}.macao .landmark{transform:translate(-77%,-100%)}.taiwan .landmark{transform:translate(-42%,-100%)}.terrain-place{font-size:11px}.terrain-entry .region-field input{font-size:14px}}
</style><style>
.terrain-repair{position:absolute;inset:0;pointer-events:none;background:linear-gradient(180deg,#07192287,transparent 30%,transparent 63%,#081a29e6),url(home-terrain-corner-repair.webp) center/100% 100% no-repeat}
.repair-upper{mask-image:linear-gradient(to right,#000 18%,transparent 22%),linear-gradient(to bottom,#000 33%,transparent 37%);mask-composite:intersect}
.repair-lower{mask-image:linear-gradient(to right,#000 26%,transparent 31%),linear-gradient(to top,#000 19%,transparent 22%);mask-composite:intersect}
.repair-inset{mask-image:linear-gradient(to left,#000 12%,transparent 16%),linear-gradient(to top,#000 10%,transparent 14%);mask-composite:intersect}
</style><style>.landmark img{display:block;width:100%;height:clamp(75px,16vh,165px);object-fit:cover;border-radius:5px;margin-bottom:4px}.hongkong img{object-position:50% 65%}.macao img,.taiwan img{object-fit:contain}.landmark{width:clamp(80px,8vw,136px)}@media(max-width:680px){.landmark{width:64px}.landmark img{height:76px}}</style><style>.projection .landmark{width:clamp(68px,12vw,190px);height:clamp(115px,23vh,240px);transform:translate(-50%,-100%);padding:0;background:none;border:0;box-shadow:none;backdrop-filter:none}.holo-model{display:block;width:100%;height:100%;touch-action:none;cursor:grab;filter:drop-shadow(0 0 2px #e0ffff) drop-shadow(0 0 9px #57e4f6)}.holo-model:active{cursor:grabbing}.landmark:after{content:"";position:absolute;pointer-events:none;bottom:0;left:20%;width:60%;height:7%;border:1px solid #b6ffff;border-radius:50%;background:radial-gradient(ellipse,#baffff80,transparent 72%);box-shadow:0 0 10px #45f1ff}.terrain-beams path{stroke-dasharray:.1 9;stroke-width:3;stroke-linecap:round;animation:flow 1.2s linear infinite}@keyframes flow{to{stroke-dashoffset:-18.2}}@media(prefers-reduced-motion:reduce){.terrain-beams path{animation:none}}</style><style>.photo-cutout{display:block;width:100%;height:90%;overflow:visible;touch-action:none;cursor:grab;filter:drop-shadow(0 1px 2px #123940) drop-shadow(0 0 5px #72ecf4);transform:perspective(460px) rotateY(var(--turn,0deg)) rotateX(var(--tilt,0deg));transition:transform .16s ease-out}.photo-cutout:active{cursor:grabbing}</style><style>.projection .landmark::after{display:none}.projection .beacon{width:6px;height:6px;border:0;background:#c6ffff;box-shadow:0 0 7px #59daef}.photo-cutout{cursor:default;touch-action:auto;transform:none}</style><style>.projection .landmark{width:clamp(120px,18vw,340px);height:clamp(185px,33vh,420px)}.projection .photo-cutout{height:100%;filter:drop-shadow(2px 4px 2px #10212c99) drop-shadow(8px 15px 7px #0b202e85)}.taiwan .landmark{height:clamp(200px,38vh,465px)}.model-open{position:absolute;inset:0;background:transparent;border:0;cursor:grab}.tower-view{position:absolute;inset:0;width:100%;height:100%;border:0;background:transparent}.viewer-close{position:absolute;right:0;top:0;border:0;border-radius:50%;color:white;background:#153144;width:26px;height:26px;cursor:pointer}@media(max-width:680px){.projection .landmark{width:23vw;height:clamp(130px,23vh,190px)}.taiwan .landmark{height:26vh}}</style><style>.projection .landmark img.full-scene{display:block;width:100%;height:100%;object-fit:contain;object-position:bottom;margin:0;border-radius:0;filter:drop-shadow(3px 7px 8px #07152180)}</style><style>.projection .landmark{width:clamp(72px,9vw,152px);height:clamp(110px,20vh,193px);perspective:620px}.peek{display:block;width:100%;height:100%;padding:0;border:0;background:transparent;cursor:zoom-in;transform:rotateY(var(--yaw,-13deg)) rotateX(5deg);transition:transform .25s}.hongkong{--yaw:10deg}.peek:hover,.peek:focus-visible{transform:translateY(-4px) rotateY(0)}.projection .landmark img.full-scene{filter:drop-shadow(2px 2px 0 #718b8a) drop-shadow(3px 4px 0 #344a49) drop-shadow(6px 12px 6px #05212bad)}#photo-detail{padding:0;border:0;background:transparent;max-width:94vw;max-height:94dvh;overflow:visible}#photo-detail::backdrop{background:#04131cdb}#photo-detail img{display:block;max-height:86dvh;max-width:90vw;width:auto;height:auto}#photo-detail button{position:absolute;right:6px;top:6px;background:#16252bd9;color:white;border:0;border-radius:50%;width:38px;height:38px;font-size:23px;cursor:pointer}</style><style>.macao .peek,.taiwan .peek{transform:none}.projection.taiwan .landmark{width:clamp(88px,12vw,195px);height:clamp(140px,25vh,248px)}.terrain-beams{pointer-events:none}.terrain-beams path{stroke-width:4.5;stroke-dasharray:.1 13;animation-name:photo-flow}@keyframes photo-flow{to{stroke-dashoffset:-26.2}}</style><style>#landmark-caption{text-align:center;color:#fff8eb;background:#10212b;padding:6px 12px;font:600 17px/1.4 system-ui,sans-serif}#photo-detail img{max-height:calc(90dvh - 38px)}</style><dialog id="photo-detail" aria-label="地标实拍大图"><img alt=""><div id="landmark-caption"></div><button type="button" aria-label="关闭大图" autofocus>×</button></dialog>
<script>
const detail=document.getElementById('photo-detail');
for(const button of document.querySelectorAll('.peek')){
 button.onclick=()=>{const source=button.querySelector('img');const large=detail.querySelector('img');large.src=source.src;detail.querySelector('#landmark-caption').textContent=button.dataset.caption;large.alt=source.alt;detail.setAttribute('aria-label',source.alt);detail.showModal()};
}
detail.querySelector('button').onclick=()=>detail.close();
detail.onclick=e=>{if(e.target===detail)detail.close()};
<\\/script><script>
const scene=document.querySelector('.terrain-scene');
function alignPhotoArrows(){
 const area=scene.getBoundingClientRect();
 if(!area.width)return;
 for(const path of scene.querySelectorAll('[data-to]')){
  const panel=scene.querySelector('.projection.'+path.dataset.to);
  const photo=panel.querySelector('img');
  if(!photo.naturalWidth)continue;
  const box=photo.getBoundingClientRect(),pin=panel.querySelector('.beacon').getBoundingClientRect();
  const scale=Math.min(box.width/photo.naturalWidth,box.height/photo.naturalHeight);
  const w=photo.naturalWidth*scale,h=photo.naturalHeight*scale;
  const cx=box.left+box.width/2-area.left,cy=box.bottom-h/2-area.top;
  const x=pin.left+pin.width/2-area.left,y=pin.top+pin.height/2-area.top;
  const dx=x-cx,dy=y-cy;
  const edge=Math.min((w/2+5)/Math.abs(dx),(h/2+5)/Math.abs(dy));
  path.setAttribute('d','M '+x+' '+y+' L '+(cx+dx*edge)+' '+(cy+dy*edge));
 }
}
new ResizeObserver(alignPhotoArrows).observe(scene);
scene.querySelectorAll('.full-scene').forEach(img=>img.addEventListener('load',alignPhotoArrows));
alignPhotoArrows();
<\\/script></body></html>` : pageHtml;
  const lookupHtml = lookupLanding ? attributedPage.replace('class="globe-cover"', 'class="globe-cover lookup-credit-flow"') : attributedPage;
  const inlineImages = lookupHtml
    .replace(/(src=")([\\w.-]+\\.(?:webp|png|jpg))(")/g, (match, start, name, end) =>
      images[name] ? start + images[name] + end : match)
    .replace(/url\\((["']?)([\\w.-]+\\.(?:webp|png|jpg))\\1\\)/g, (match, quote, name) =>
      images[name] ? 'url("' + images[name] + '")' : match);
  const regionStyle = cover ? `<style>
*{box-sizing:border-box}body{margin:0;color:#34271e;background:#f6f2eb;font:16px/1.6 system-ui,sans-serif}
a{color:#83291e}button,input{font:inherit}button,summary{cursor:pointer}
.cover{width:min(100%,580px);margin:auto;container-type:inline-size}
@media(min-width:700px){.cover{width:min(580px, max(330px, calc((100svh - 150px) / 1.1)))}}
.cover-art{position:relative;overflow:hidden}
.cover-title{height:27cqw}
.cover-history-subtitle{position:absolute;z-index:1;top:19.5cqw;left:27%;width:46%;margin:0;text-align:center;background:#f6f2eb;font:500 clamp(14px,3.3cqw,25px)/1.45 "Songti SC","SimSun",serif}
@media(min-width:900px){.cover-history-subtitle{top:14.3%;left:38%;width:24%;font-size:1.32cqw;background:#f8f2e8}}
.cover-map{height:65cqw}
.cover-art img{position:absolute;width:100%;height:auto;display:block;mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent)}
.cover-title img{top:-20cqw}
.cover-map img{top:-50cqw}
.cover-start{display:grid;place-items:center;width:min(85%,max(205px,46.5%));min-height:44px;height:9.97cqw;margin:clamp(15px,4cqw,24px) auto 0;border-radius:999px;background:linear-gradient(110deg,#912819,#aa3828);box-shadow:0 4px 10px #8c291e40;color:#fffaf2;text-decoration:none;text-align:center;font:700 clamp(15px,3.75cqw,22px)/1.2 "Songti SC","SimSun",serif}
.cover-start:focus-visible{outline:2px solid #79281d;outline-offset:4px}
.region-entry{position:relative;margin:clamp(18px,4.5cqw,26px) auto 16px;width:85%}
.region-entry label{display:block;font-weight:700;color:#79281d;margin-bottom:8px}
.region-field{position:relative}.region-field input{width:100%;min-height:52px;border:1px solid #d2b99b;border-radius:999px;background:#fcf8ef;color:inherit;padding:10px 122px 10px 16px}
.region-field details{position:absolute;inset-block:0;inset-inline-end:0}
.region-field summary{display:flex;align-items:center;justify-content:center;gap:8px;min-width:112px;height:100%;padding:0 14px;border:1px solid #d2b99b;border-radius:0 999px 999px 0;background:#f0e1cb;list-style:none;color:#702117;font-weight:700;white-space:nowrap}
.region-field summary::-webkit-details-marker{display:none}
.region-field summary:hover,.region-field details[open] summary{background:#e9d4b8}
.region-field summary:focus-visible{outline:2px solid #79281d;outline-offset:2px}
.region-arrow{width:9px;height:9px;border:solid currentColor;border-width:0 2px 2px 0;transform:translateY(-2px) rotate(45deg)}
.region-field details[open] .region-arrow{transform:translateY(2px) rotate(225deg)}
@media(max-width:430px){.region-field input{padding-inline-end:110px;font-size:14px}.region-field summary{min-width:102px;padding-inline:10px;font-size:14px}}
.region-options{position:absolute;inset-inline-end:0;top:calc(100% + 4px);width:min(240px,70vw);background:#fff9ef;border:1px solid #d2b99b;border-radius:10px;padding:6px;z-index:1;box-shadow:0 5px 14px #34271e24}
.region-options button{display:block;width:100%;text-align:start;border:0;background:transparent;color:#5a2b21;padding:8px 12px;border-radius:6px;min-height:42px}
.region-options button:hover,.region-options button:focus-visible{background:#f2e2cb}
.help{font-size:.9rem;color:#6e5946;margin:7px 0}
.view-options{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
#script-switch{border:1px solid #cfaf89;border-radius:999px;background:#fff9ee;color:#79281d;padding:6px 14px;min-height:40px}

</style>` : '<style>#script-switch{display:block;margin:0 0 12px auto;border:1px solid #cfaf89;border-radius:999px;background:#fff9ee;color:#79281d;padding:6px 14px;min-height:40px;font:inherit;cursor:pointer}</style>';
  frame.srcdoc = inlineImages.replace('</head>', (cover ? '' : `<style>\n:root{--ink:#172e3c;--line:#b7ccce;--paper:#faf7ee}\nhtml body{color:#172e3c;background:#e6eeee}\nhtml body .sheet,html body .page,html body .globe-cover.lookup-credit-flow{\n background:radial-gradient(ellipse at 85% 0%,#f6f8f1 0%,transparent 65%),linear-gradient(150deg,#faf8f2,#eff4f5 48%,#dcebf3 100%);\n}\nhtml body .sheet::before,html body .sheet::after{opacity:.17}\nhtml body :is(.feature,.filters,.grid article,.lookup-tile,.card,.note,.keepsake){\n background:#faf7ee;border-color:#b7ccce;color:#172e3c;\n box-shadow:0 5px 16px #15394b12;\n}\nhtml body :is(.intro h1,main h1,main h2,.brand){color:#173747}\nhtml body :is(input,select,#script-switch){border-color:#9ebec3}\nhtml body :is(.lookup-credit,.note){color:#36525d}\n</style>`) + innerStyles + lookupLanding + lookupSizing + creditStyle + regionStyle + '</head>');
}
function openFunction(key) {
  if (key === 'guide') return navigate('guide.html', '', 'guide');
  if (key === 'home') return navigate('index.html');
  if (key === 'featured') return navigate('featured.html');
  if (key === 'regions') return navigate('regions.html');
  if (isStory(current)) {
    const doc = frame.contentDocument;
    if (key !== 'lookup' && doc.body.classList.contains('lookup-only')) {
      doc.getElementById('close-story-lookup').click();
    }
    selectTab(key);
    activateLocal(frame.contentDocument, key);
    return;
  }
  if (lastStory) return navigate(lastStory, key, key);
  if (key === 'lookup') return navigate('index.html', 'lookup', key);
  navigate('featured.html', '', key);
}
for (const button of directory.querySelectorAll('[data-tab]')) {
  button.addEventListener('click', () => openFunction(button.dataset.tab));
}
navigate('index.html');
})().catch(error => {
  console.error('Unable to load site', error);
  const notice = document.createElement('p');
  notice.setAttribute('role', 'alert');
  notice.style.cssText = 'margin:24px;font:16px system-ui';
  notice.textContent = '暂时无法载入《字里寻踪》，请刷新页面重试。';
  document.getElementById('layout').replaceWith(notice);
});
</script>""", height=860, scrolling=False)



