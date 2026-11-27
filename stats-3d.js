async function init() {
  const response = await fetch('cases.json');
  if (!response.ok) throw Error('无法加载故事数据');
  const catalogue = await response.json();
  const rows = Object.entries(catalogue.regions).flatMap(([region, stories]) => stories.map(story => ({...story, region})));
  const groups=['中国大陆','台湾与金门','香港','澳门','东南亚'];
  const letters=[...new Set(rows.map(story=>story.character))];
  const names=['饮食与团聚','节庆装饰','传统工艺','祭祀仪式','节庆活动'];
  const colors=['#35675f','#aa503a','#ba904c','#476c86','#83718a'];
  if(rows.some(story=>!names.includes(story.theme))) names.push('未归类');
  const get=id=>document.getElementById(id);
  const region=get('region'),word=get('word'),count=get('count');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const group=(p,r)=>/^(台湾|金门)/.test(p)?1:p.startsWith('香港')?2:p.startsWith('澳门')?3:r==='海外'?4:0;
  for(const [el,values] of [[region,groups],[word,letters]]) for(const value of ['全部',...values]) el.add(new Option(value,value));
  const ns='http://www.w3.org/2000/svg';
  function svgNode(tag,attrs={}) {const el=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,v);return el;}
  const ring=get('ring');
  ring.replaceChildren();
  const svg=svgNode('svg',{viewBox:'0 0 340 250',role:'group','aria-label':'各地区故事收录量立体环形图'});
  const shadow=svgNode('ellipse',{cx:170,cy:165,rx:132,ry:48,fill:'#203b3220'});
  svg.append(shadow);
  const slices=groups.map((label,i)=>{
    const g=svgNode('g',{class:'pie-slice',role:'button',tabindex:0});
    const title=svgNode('title');g.append(title);
    const layers=[];
    for(let depth=20;depth>=0;depth-=2){
      const path=svgNode('path',{transform:'translate(0 '+depth+')',fill:colors[i]});
      path.style.filter=depth?'brightness(.68)':'none';
      layers.push(path);g.append(path);
    }
    const choose=()=>{region.value=region.value===label?'全部':label;draw();};
    g.addEventListener('click',choose);
    g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});
    g.append(svgNode('path',{class:'pie-highlight',fill:'#ffffff14','pointer-events':'none'}));
    svg.append(g);return {g,layers,title,highlight:g.lastChild};
  });
  const center=svgNode('text',{x:170,y:111,'text-anchor':'middle',class:'pie-total'});
  const unit=svgNode('text',{x:170,y:134,'text-anchor':'middle',class:'pie-unit'});unit.textContent='条故事';
  svg.append(center,unit);ring.append(svg);
  const legend=get('legend');
  const legends=groups.map((label,i)=>{
    const button=document.createElement('button');button.type='button';button.className='legend';
    const dot=document.createElement('i');dot.className='dot';dot.style.background=colors[i];dot.setAttribute('aria-hidden','true');
    const text=document.createElement('span');button.append(dot,text);
    button.onclick=()=>{region.value=region.value===label?'全部':label;draw();};
    legend.append(button);return {button,text};
  });
  function point(radius,angle){return [170+radius*Math.cos(angle),116+radius*.64*Math.sin(angle)];}
  function arc(radius,a,b,reverse=false){const points=[];const steps=Math.max(2,Math.ceil(Math.abs(b-a)/.055));for(let j=0;j<=steps;j++){const t=reverse?b+(a-b)*j/steps:a+(b-a)*j/steps;points.push(point(radius,t).join(','));}return points;}
  function sector(a,b){return 'M'+arc(136,a,b).join(' L')+' L'+arc(80,a,b,true).join(' L')+' Z';}
  let displayed=groups.map(()=>0),animation;
  function paint(values){
    displayed=values;const total=values.reduce((a,b)=>a+b,0);let a=-Math.PI/2;
    values.forEach((value,i)=>{
      const slice=slices[i];const b=a+(total?value/total*Math.PI*2:0);
      slice.g.style.display=value>.0001?'':'none';
      if(value>.0001){const path=sector(a,b);slice.layers.forEach(el=>el.setAttribute('d',path));slice.highlight.setAttribute('d',path);
        slice.g.style.setProperty('--lift-x',Math.cos((a+b)/2)*6+'px');slice.g.style.setProperty('--lift-y',(Math.sin((a+b)/2)*4-7)+'px');}
      a=b;
    });
    shadow.style.opacity=total?'1':'0';
  }
  function animatePie(values){
    cancelAnimationFrame(animation);const from=[...displayed];
    if(reduced.matches){paint(values);return;}
    const started=performance.now();
    function tick(now){const progress=Math.min(1,(now-started)/650),eased=1-Math.pow(1-progress,3);paint(values.map((v,i)=>from[i]+(v-from[i])*eased));if(progress<1)animation=requestAnimationFrame(tick);}
    animation=requestAnimationFrame(tick);
  }
  function makeBars(container,labels){
    return labels.map(label=>{
      const row=document.createElement('div');row.className='row';
      const caption=document.createElement('span');caption.textContent=label;
      const track=document.createElement('div');track.className='track';track.setAttribute('role','meter');track.setAttribute('aria-label',label+'故事数');track.setAttribute('aria-valuemin','0');
      const fill=document.createElement('div');fill.className='fill';track.append(fill);
      const value=document.createElement('b');row.append(caption,track,value);container.append(row);
      return {track,fill,value};
    });
  }
  const themeBars=makeBars(get('themes'),names);
  const columnMaximum=Math.max(5,...letters.map(letter=>rows.filter(row=>row.character===letter).length));
  const columnsSvg=svgNode('svg',{viewBox:'0 0 440 330',class:'word-chart',role:'group','aria-label':'各汉字故事数竖向柱状图，纵轴从零起点，单位条'});
  const defs=svgNode('defs'),gradient=svgNode('linearGradient',{id:'word-column-blue',x1:0,y1:0,x2:0,y2:1});
  gradient.append(svgNode('stop',{offset:'0%','stop-color':'#5086a2'}),svgNode('stop',{offset:'100%','stop-color':'#315e79'}));defs.append(gradient);columnsSvg.append(defs);
  const baseline=265,plotHeight=220;
  const step=columnMaximum<=8?1:Math.ceil(columnMaximum/5);
  for(let value=0;value<=columnMaximum;value+=step){
    const y=baseline-value/columnMaximum*plotHeight;
    columnsSvg.append(svgNode('line',{x1:40,y1:y,x2:424,y2:y,class:value?'column-grid':'column-baseline'}));
    const tick=svgNode('text',{x:30,y:y+6,'text-anchor':'end',class:'column-tick'});tick.textContent=value;columnsSvg.append(tick);
  }
  const units=svgNode('text',{x:14,y:25,class:'column-unit'});units.textContent='条';columnsSvg.append(units);
  const columns=letters.map((letter,i)=>{
    const x=56+i*61,width=32,depth=5;
    const group=svgNode('g',{role:'meter','aria-label':letter+'故事数','aria-valuemin':0,'aria-valuemax':columnMaximum});
    const title=svgNode('title');
    const shadow=svgNode('ellipse',{cx:x+width/2+2,cy:baseline+4,rx:23,ry:3,fill:'#315e7915'});
    const front=svgNode('rect',{x,width,fill:'url(#word-column-blue)'});
    const side=svgNode('path',{fill:'#274f69'}),top=svgNode('path',{fill:'#8aaec3'});
    const number=svgNode('text',{x:x+width/2+2,'text-anchor':'middle',class:'column-value'});
    const label=svgNode('text',{x:x+width/2+2,y:300,'text-anchor':'middle',class:'column-word'});label.textContent=letter;
    group.append(title,shadow,side,front,top,number,label);columnsSvg.append(group);
    return {x,width,depth,group,title,front,side,top,number,shadow};
  });
  get('bars').replaceChildren(columnsSvg);
  let displayedColumns=letters.map(()=>0),columnAnimation,columnsInitialized=false;
  function paintColumns(values){
    displayedColumns=values;
    values.forEach((value,i)=>{
      const {x,width:w,depth:d,front,side,top,number,shadow}=columns[i];
      const height=value/columnMaximum*plotHeight,y=baseline-height;
      front.setAttribute('y',y);front.setAttribute('height',height);
      side.setAttribute('d',`M${x+w},${y} l${d},${-d} V${baseline-d} l${-d},${d} Z`);
      top.setAttribute('d',`M${x},${y} l${d},${-d} h${w} l${-d},${d} Z`);
      for(const face of [side,top,shadow])face.style.display=value>.001?'':'none';
      number.setAttribute('y',y-(value>.001?13:9));
    });
  }
  function updateColumns(values){
    columns.forEach((column,i)=>{column.number.textContent=values[i];column.title.textContent=letters[i]+'：'+values[i]+' 条';column.group.setAttribute('aria-valuenow',values[i]);});
    cancelAnimationFrame(columnAnimation);
    if(reduced.matches||!columnsInitialized){paintColumns(values);columnsInitialized=true;return;}
    const from=[...displayedColumns],started=performance.now();
    function tick(now){const progress=Math.min(1,(now-started)/650),eased=1-Math.pow(1-progress,3);paintColumns(values.map((value,i)=>from[i]+(value-from[i])*eased));if(progress<1)columnAnimation=requestAnimationFrame(tick);}
    columnAnimation=requestAnimationFrame(tick);
  }
  function updateBars(bars,values){
    const maximum=Math.max(1,...values);
    bars.forEach((bar,i)=>{bar.fill.style.width=values[i]/maximum*100+'%';bar.fill.classList.toggle('empty',values[i]===0);bar.value.textContent=values[i];bar.track.setAttribute('aria-valuemax',maximum);bar.track.setAttribute('aria-valuenow',values[i]);});
  }
  function draw(){
    const g=groups.map(()=>0),w=letters.map(()=>0),t=names.map(()=>0);let n=0;
    const records=get('records');records.replaceChildren();
    rows.forEach(({character:c,place:p,title,theme,region:sourceRegion})=>{
      const j=group(p,sourceRegion);
      if((region.value!=='全部'&&region.value!==groups[j])||(word.value!=='全部'&&word.value!==c))return;
      n++;g[j]++;w[letters.indexOf(c)]++;const category=names.includes(theme)?theme:'未归类';t[names.indexOf(category)]++;
      const li=document.createElement('li');li.textContent=[p,c,title,category].join(' · ');records.append(li);
    });
    count.textContent=(region.value==='全部'&&word.value==='全部'?'全站收录 · '+rows.length:'当前筛选 · '+n+' / '+rows.length)+' 条';
    center.textContent=n;
    g.forEach((value,i)=>{
      const label=groups[i]+' '+value+' 条 · '+(n?Math.round(value/n*100):0)+'%';
      slices[i].g.setAttribute('aria-label',label+'，点击筛选');slices[i].title.textContent=label;
      legends[i].text.textContent=label;legends[i].button.setAttribute('aria-pressed',String(region.value===groups[i]));
    });
    animatePie(g);updateColumns(w);updateBars(themeBars,t);
    get('regionNote').textContent=!n?'当前筛选没有匹配的故事。':g.every(v=>v===g[0])?'当前五个地区分组各收录 '+g[0]+' 条。百分比按当前故事总数计算。':'图例列出各地区的收录量，百分比按当前故事总数计算。';
    get('wordNote').textContent='当前涵盖 '+w.filter(Boolean).length+' 个汉字，每根立柱对应一个字的故事数；筛选前后使用相同刻度。';
    const peak=Math.max(...t);get('themeNote').textContent=!n?'当前筛选没有可统计的主题。':'当前收录最多的主题为'+names.filter((_,i)=>t[i]===peak).join('、')+'（'+peak+' 条）。';
  }
  region.onchange=word.onchange=draw;
  reduced.addEventListener('change',()=>{cancelAnimationFrame(animation);draw();});
  draw();
}
init().catch(()=>{document.getElementById('count').textContent='统计暂时无法加载，请刷新页面重试。';});
