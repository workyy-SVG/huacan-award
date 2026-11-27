(async()=>{
const response=await fetch('cases.json');
if(!response.ok)throw Error('无法加载故事数据');
const catalogue=await response.json();
const rows=Object.entries(catalogue.regions).flatMap(([region,stories])=>stories.map(story=>({...story,region})));
const group=r=>/^(台湾|金门)/.test(r.place)?'台湾与金门':r.place.startsWith('香港')?'香港':r.place.startsWith('澳门')?'澳门':r.region==='海外'?'东南亚':'中国大陆';
const $=s=>document.querySelector(s),words=[...'年门茶船灯圆'],areas=['中国大陆','台湾与金门','香港','澳门','东南亚'],colors=['#256661','#c37c43','#527c91','#a85043','#808451'];
const tally=Object.entries(rows.reduce((o,r)=>(o[r.theme]=(o[r.theme]||0)+1,o),{})).sort((a,b)=>b[1]-a[1]);
for(const [theme,n] of tally){$('#rank').insertAdjacentHTML('beforeend','<div class="rank"><span>'+theme+'</span><div><i style="width:'+n/tally[0][1]*100+'%"></i></div><b>'+n+' 则 · '+Math.round(n/rows.length*100)+'%</b></div>')}
let focusKey=null;
const tones=['#a65c42','#427b75','#b48843','#58748a','#79794f'];
function weave(){
const narrow=window.innerWidth<620,W=narrow?370:840,H=345,A=narrow?40:95,B=W-(narrow?100:168),unit=7;
const themes=tally.map(t=>t[0]),counts=words.map(w=>themes.map(t=>rows.filter(r=>r.character===w&&r.theme===t).length));
const start=(sizes)=>{let y=12;return sizes.map(n=>{let v=y;y+=n*unit+(H-24-rows.length*unit)/(sizes.length-1);return v})};
const ls=start(words.map(w=>rows.filter(r=>r.character===w).length)),rs=start(tally.map(t=>t[1])),lc=[...ls],rc=[...rs];
let shapes='',nodes='';
counts.forEach((line,i)=>line.forEach((n,j)=>{if(!n)return;const y=lc[i],z=rc[j],h=n*unit,mid=(A+B)/2;lc[i]+=h;rc[j]+=h;
shapes+='<path d="M '+A+' '+y+' C '+mid+' '+y+' '+mid+' '+z+' '+B+' '+z+' v '+h+' C '+mid+' '+(z+h)+' '+mid+' '+(y+h)+' '+A+' '+(y+h)+' Z" fill="'+tones[j]+'" opacity="'+(!focusKey?.length||[words[i],themes[j]].includes(focusKey)?'.73':'.09')+'"><title>'+words[i]+' → '+themes[j]+' · '+n+' 则</title></path>'}));
function label(key,x,y,h,right,j){const color=right?tones[j]:'#365b55',active=focusKey===key;nodes+='<g role="button" tabindex="0" aria-pressed="'+active+'" aria-label="'+key+'" data-key="'+key+'"><rect x="'+(right?x:0)+'" y="'+(y+h/2-13)+'" width="'+(right?W-B:A)+'" height="26" fill="'+(active?'#eadfc9':'transparent')+'"/><rect x="'+(right?x:x-5)+'" y="'+y+'" width="5" height="'+h+'" fill="'+color+'"/><text x="'+(right?x+10:x-12)+'" y="'+(y+h/2+5)+'" text-anchor="'+(right?'start':'end')+'" font-size="'+(right?(narrow?12:16):21)+'" fill="#254741">'+key+(right?' · '+tally[j][1]:'')+'</text></g>'}
words.forEach((w,i)=>label(w,A,ls[i],lc[i]-ls[i],false,i));themes.forEach((t,j)=>label(t,B,rs[j],rc[j]-rs[j],true,j));
$('#loom').innerHTML='<svg viewBox="0 0 '+W+' '+H+'" role="group" aria-label="汉字与习俗的故事流向">'+shapes+nodes+'</svg>';
$('#loom').querySelectorAll('g').forEach(g=>{g.onclick=()=>{focusKey=focusKey===g.dataset.key?null:g.dataset.key;weave();$('#loom [data-key="'+g.dataset.key+'"]').focus()};g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();g.onclick()}}});
const selected=rows.filter(r=>r.character===focusKey||r.theme===focusKey),by={};selected.forEach(r=>{let k=words.includes(focusKey)?r.theme:r.character;by[k]=(by[k]||0)+1});
$('#insight').textContent=focusKey?focusKey+'的 '+selected.length+' 则故事：'+Object.entries(by).map(([k,n])=>k+' '+n+' 则').join('、')+'。':'饮食与团聚连接了「'+[...new Set(rows.filter(r=>r.theme==='饮食与团聚').map(r=>r.character))].join('」「')+'」。';
}
weave();window.matchMedia('(max-width:619px)').addEventListener('change',weave);
})().catch(()=>{document.querySelector('#loom').textContent='故事数据暂时无法载入，请刷新重试。'});