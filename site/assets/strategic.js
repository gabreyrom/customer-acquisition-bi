const get=id=>document.getElementById(id), months=[...new Set(data.map(r=>r.month))];
get('asof').textContent='Synthetic digital bank · Data as of '+new Date(snapshot.asOf+'T00:00Z').toLocaleString('en-US',{month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
const monS=m=>new Date(m+'-01T00:00Z').toLocaleString('en-US',{month:'short',year:'2-digit',timeZone:'UTC'});
const options=(items,initial)=>items.map(([k,v])=>`<option value="${k}" ${String(k)===String(initial)?'selected':''}>${esc(v)}</option>`).join('');
const START='#b8336a';
const shade=(k,n)=>{const f=n>1?k/(n-1):0,a=[127,182,199],b=[0,56,74];return `rgb(${a.map((v,i)=>Math.round(v+(b[i]-v)*f))})`;};
const usd=v=>(v<0?'−$':'$')+Math.abs(v).toLocaleString('en-US');
function niceTicks(lo,hi){
 const span=(hi-lo)/4||1, mag=10**Math.floor(Math.log10(span)), st=[1,2,2.5,5,10].map(f=>f*mag).find(s=>s>=span);
 const first=Math.floor(lo/st), last=Math.ceil(hi/st), out=[];
 for(let i=first;i<=last;i++)out.push(+(i*st).toFixed(6));
 return out;
}
const controls=[
 ['start','Start cohort',months.map(m=>[m,mon(m)]),'2025-01'],
 ['span','Compare with',[3,6,9,12].map(n=>[n,`Next ${n} months`]),6],
 ['channel','Acquisition channel',[['ALL','All signups'],['PAID','All paid channels'],...Object.entries(channels)],'ALL'],
 ['age','Customer age up to',ages.map(a=>[a,a+' days']),365],
 ['model','Expected-value assumptions',[['A_v0.3_BASELINE','Baseline (channel-specific)'],['A_v0.3_EQUAL_CHANNEL','Same for every channel']],'A_v0.3_BASELINE']];
get('filters').innerHTML=controls.map(([id,label,items,initial])=>`<label>${label}<select id="${id}">${options(items,initial)}</select></label>`).join('');
get('metric').innerHTML=options(Object.entries(metrics),'roas');

// withLegend draws the legend inside the SVG (used for slide extracts; the page shows an HTML legend instead).
function cohortChart(c,withLegend=false){
 const A=c.selected,start=c.groups[0],others=c.groups.slice(1),w=840,l=64,r=24,b=48,leg=[];
 let top=16;
 if(withLegend){
  const items=[[mon(start.month)+' realized',START,false],[mon(start.month)+' expected',START,true],...others.map((g,k)=>[mon(g.month),shade(k,others.length),false])];
  let lx=l,ly=14;
  for(const [label,color,dash] of items){
   const iw=label.length*7+42; if(lx+iw>w-r){lx=l;ly+=20;}
   leg.push(`<line x1="${lx}" x2="${lx+22}" y1="${ly}" y2="${ly}" stroke="${color}" stroke-width="3" ${dash?'stroke-dasharray="6 5"':''}/><text x="${lx+28}" y="${ly+4}" fill="#193847">${esc(label)}</text>`);
   lx+=iw;
  }
  top=ly+22;
 }
 const t=top,h=314+t,W=w-l-r,H=h-t-b;
 const vals=c.groups.flatMap(g=>g.points.map(p=>p.real)).concat(start.points.map(p=>p.expected)).filter(v=>v!=null);
 const ticks=niceTicks(Math.min(0,...vals),Math.max(1,...vals)),lo=ticks[0],hi=ticks.at(-1);
 const x=a=>A.length<2?l+W/2:l+24+(W-48)*(a-A[0])/(A.at(-1)-A[0]), y=v=>t+(hi-v)/(hi-lo)*H;
 const out=[`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="Cumulative contribution per customer by signup cohort"><g font-family="system-ui,sans-serif" font-size="12" fill="#395969">`,...leg];
 for(const v of ticks)out.push(`<line x1="${l}" x2="${w-r}" y1="${y(v)}" y2="${y(v)}" stroke="${v===0?'#9ab2bd':'#e3ecef'}"/><text x="${l-8}" y="${y(v)+4}" text-anchor="end">${esc(usd(v))}</text>`);
 for(const a of A)out.push(`<text x="${x(a)}" y="${t+H+20}" text-anchor="middle">${a} days</text>`);
 out.push(`<text x="${l+W/2}" y="${h-4}" text-anchor="middle">Days since signup</text>`);
 const line=(g,key,color,width,dash)=>{
  const pts=A.map((a,i)=>[a,g.points[i]]).filter(([,p])=>p[key]!=null);
  if(!pts.length)return '';
  const coords=pts.map(([a,p])=>x(a)+','+y(p[key])).join(' '), label=key==='real'?'realized':'expected at signup';
  return (pts.length>1?`<polyline fill="none" stroke="transparent" stroke-width="14" points="${coords}"/><polyline fill="none" stroke="${color}" stroke-width="${width}" ${dash?'stroke-dasharray="6 5"':''} points="${coords}"/>`:'')+
   pts.map(([a,p])=>`<circle cx="${x(a)}" cy="${y(p[key])}" r="${width+1.5}" fill="${dash?'#fff':color}" stroke="${color}" stroke-width="2"><title>${esc(`${mon(g.month)} · ${a} days · ${money(p[key])} per customer ${label} · ${p.n} customers`)}</title></circle>`).join('');
 };
 others.forEach((g,k)=>out.push(`<g data-m="${g.month}">${line(g,'real',shade(k,others.length),2,false)}</g>`));
 out.push(`<g data-m="${start.month}">${line(start,'expected',START,2.5,true)}${line(start,'real',START,3.5,false)}</g>`);
 if(!vals.length)out.push(`<text x="${l+W/2}" y="${t+H/2}" text-anchor="middle" font-size="16">No complete checkpoints yet</text>`);
 return out.join('')+'</g></svg>';
}
function legend(c){
 const s=c.groups[0],o=c.groups.slice(1);
 return `<span data-m="${s.month}"><i style="border-color:${START}"></i><b>${mon(s.month)}</b>&nbsp;realized</span><span data-m="${s.month}"><i class="dash" style="border-color:${START}"></i>${mon(s.month)} expected</span>`+
  o.map((g,k)=>`<span data-m="${g.month}"><i style="border-color:${shade(k,o.length)}"></i>${mon(g.month)}</span>`).join('');
}
function summary(c,ms,model){
 const n=c.groups.reduce((s,g)=>s+g.points[0].n,0);
 const [paid,all]=data.filter(r=>ms.includes(r.month)&&r.age===30&&r.model===model).reduce((a,r)=>[a[0]+r.paid,a[1]+r.n],[0,0]);
 const s=c.groups[0], k=s.points.map(p=>p.ok).lastIndexOf(true);
 const tile=([v,l,cls])=>`<div class="${cls||''}"><strong>${esc(v)}</strong>${esc(l)}</div>`;
 const a=[[`${ms.length} cohorts`,`${mon(ms[0])} – ${mon(ms.at(-1))} · ${n.toLocaleString('en-US')} customers`]];
 if(k>=0&&s.points[k].expected>0)a.push([`${(s.points[k].real/s.points[k].expected).toFixed(1)}×`,`${mon(s.month)} realized vs expected at ${c.selected[k]} days`,'key']);
 else a.push(['Pending',`${mon(s.month)} has not completed a checkpoint yet`,'key']);
 a.push([`${all?Math.round(paid/all*100):0}%`,`of signups have a known paid channel (${paid.toLocaleString('en-US')} of ${all.toLocaleString('en-US')}, all channels)`]);
 const b=c.selected.map((age,i)=>{
  const done=c.groups.filter(g=>g.points[i].ok), tot=done.reduce((t,g)=>t+g.points[i].n,0);
  return [tot?money(done.reduce((t,g)=>t+g.points[i].real*g.points[i].n,0)/tot):'Pending',`average contribution per customer at ${age} days · ${done.length} of ${ms.length} cohorts complete`];
 });
 get('tilesA').innerHTML=a.map(tile).join('');
 get('tilesB').innerHTML=b.map(tile).join('');
}
function triangle(c){
 const maxV=Math.max(1,...c.groups.flatMap(g=>g.points.map(p=>Math.abs(p.real??0))));
 const head=['Signup cohort','Customers',...c.selected.map(a=>a+' days')];
 const rows=c.groups.map((g,gi)=>`<tr${gi?'':' class="start"'}><td>${esc(mon(g.month))}${gi?'':'<span class="tag">start</span>'}</td><td>${g.points[0].n.toLocaleString('en-US')}</td>`+g.points.map(p=>{
  if(!p.ok)return `<td class="pending">${p.n?`Pending<small>${p.m} of ${p.n} reached</small>`:'No signups'}</td>`;
  const f=Math.min(1,Math.abs(p.real)/maxV), bg=p.real<0?`rgba(173,69,31,${(.12+.33*f).toFixed(2)})`:`rgba(0,103,128,${(.05+.35*f).toFixed(2)})`;
  return `<td style="background:${bg}">${esc(money(p.real))}<small>expected ${esc(money(p.expected))}</small></td>`;
 }).join('')+'</tr>').join('');
 return `<div class="scroll"><table><thead><tr>${head.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`;
}
get('byChAge').innerHTML=options(ages.map(a=>[a,a+' days']),90);
function drawByChannel(){
 const {ms,model}=state, age=+get('byChAge').value;
 const rows=(m,k)=>data.filter(r=>r.month===m&&r.age===age&&r.model===model&&(k==='ALL'||r.channel===k));
 const avg=(m,k)=>{const rs=rows(m,k),n=rs.reduce((s,r)=>s+r.n,0);return n&&rs.every(r=>r.n===r.mature)?rs.reduce((s,r)=>s+(r.real||0),0)/n/100:null;};
 const count=(m,k)=>rows(m,k).reduce((s,r)=>s+r.n,0)+' customers';
 const series=Object.keys(channels).map(k=>({name:channels[k],v:ms.map(m=>avg(m,k)),detail:ms.map(m=>count(m,k))}));
 series.push({name:'All signups',c:'#193847',d:true,v:ms.map(m=>avg(m,'ALL')),detail:ms.map(m=>count(m,'ALL'))});
 get('byChTitle').textContent=`Contribution per customer by channel at ${age} days`;
 get('byCh').innerHTML=plot('',ms.map(monS),series,'USD','line',ms.map((m,i)=>series.at(-1).v[i]==null?'Pending':''));
}
// Payback: each cohort's acquisition spend against what its customers returned by a chosen age.
const PAID=Object.keys(channels).filter(k=>k!=='UNKNOWN'), chColor={GOOGLE_ADS:colors[0],META_ADS:colors[1],PAID_AFFILIATES:colors[2]};
const inScope=(k,channel)=>channel==='ALL'||(channel==='PAID'?k!=='UNKNOWN':k===channel);
const measures={real:'Contribution',revenue:'Revenue'};
get('payAge').innerHTML=options(ages.map(a=>[a,a+' days']),365);
function payback(m,age,channel,model,measure){
 const rows=data.filter(r=>r.month===m&&r.age===age&&r.model===model&&inScope(r.channel,channel));
 const spend=Object.fromEntries(PAID.filter(k=>inScope(k,channel)).map(k=>[k,(rows.find(r=>r.channel===k)?.spend||0)/100]));
 const total=Object.values(spend).reduce((s,v)=>s+v,0), live=rows.filter(r=>r.n>0);
 const ok=live.length>0&&live.every(r=>r.status==='MATURE'&&r.mature===r.n);
 const value=ok?live.reduce((s,r)=>s+(r[measure]||0),0)/100:null;
 return {spend,total,value,ratio:value!=null&&total?value/total:null,n:rows.reduce((s,r)=>s+r.n,0)};
}
const ratioColor=r=>r>=1?'#1b7f4b':'#b3261e';
function paybackChart(ms,ps,label){
 const w=840,h=370,l=78,r=24,t=70,b=46,W=w-l-r,H=h-t-b;
 const vals=ps.flatMap(p=>[p.total,p.value]).filter(v=>v!=null);
 const ticks=niceTicks(Math.min(0,...vals),Math.max(1,...vals)),lo=ticks[0],hi=ticks.at(-1);
 const step=W/ms.length,x=i=>l+(i+.5)*step,y=v=>t+(hi-v)/(hi-lo)*H,bw=Math.min(48,step*.55);
 const out=[`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="Acquisition spend and ${esc(label)} by signup cohort"><rect width="${w}" height="${h}" fill="white"/><g font-family="system-ui,sans-serif" font-size="12" fill="#395969">`];
 let lx=l;
 for(const k of Object.keys(ps[0]?.spend||{})){out.push(`<rect x="${lx}" y="10" width="14" height="14" fill="${chColor[k]}"/><text x="${lx+20}" y="21" fill="#193847">${esc(channels[k])} spend</text>`);lx+=channels[k].length*7+64;}
 out.push(`<line x1="${lx}" x2="${lx+24}" y1="17" y2="17" stroke="#193847" stroke-width="3"/><circle cx="${lx+12}" cy="17" r="4" fill="#193847"/><text x="${lx+30}" y="21" fill="#193847">${esc(label)}</text><text x="${l-8}" y="52" text-anchor="end" font-size="12" font-weight="600">Payback</text>`);
 for(const v of ticks)out.push(`<line x1="${l}" x2="${w-r}" y1="${y(v)}" y2="${y(v)}" stroke="${v===0?'#9ab2bd':'#e3ecef'}"/><text x="${l-8}" y="${y(v)+4}" text-anchor="end">${esc(usd(v))}</text>`);
 ps.forEach((p,i)=>{
  let base=0;
  for(const [k,v] of Object.entries(p.spend)){if(!v)continue;out.push(`<rect x="${x(i)-bw/2}" y="${y(base+v)}" width="${bw}" height="${y(base)-y(base+v)}" fill="${chColor[k]}" fill-opacity=".85"><title>${esc(`${mon(ms[i])} · ${channels[k]} spend ${money(v)}`)}</title></rect>`);base+=v;}
  out.push(`<text x="${x(i)}" y="${t+H+18}" text-anchor="middle">${esc(monS(ms[i]))}</text>`);
  if(p.value==null)out.push(`<text x="${x(i)}" y="${t+H+34}" text-anchor="middle" fill="#955026" font-size="11">Pending</text>`);
  else if(p.ratio!=null)out.push(`<text x="${x(i)}" y="52" text-anchor="middle" font-size="14" font-weight="700" fill="${ratioColor(p.ratio)}">${p.ratio.toFixed(1)}×</text>`);
 });
 const pts=ps.map((p,i)=>p.value==null?null:[x(i),y(p.value)]);
 for(let i=1;i<pts.length;i++)if(pts[i]&&pts[i-1])out.push(`<line x1="${pts[i-1][0]}" y1="${pts[i-1][1]}" x2="${pts[i][0]}" y2="${pts[i][1]}" stroke="#193847" stroke-width="3"/>`);
 ps.forEach((p,i)=>{if(pts[i])out.push(`<circle cx="${pts[i][0]}" cy="${pts[i][1]}" r="5" fill="#193847"><title>${esc(`${mon(ms[i])} · ${label} ${money(p.value)} · spend ${money(p.total)}${p.ratio!=null?' · '+p.ratio.toFixed(2)+'×':''} · ${p.n} customers`)}</title></circle>`);});
 return out.join('')+'</g></svg>';
}
function paybackTable(ms,channel,model,measure){
 const keys=Object.keys(channels).filter(k=>inScope(k,channel));
 const scopes=keys.map(k=>[channels[k],k]).concat(keys.length>1?[[channel==='ALL'?'All signups':'All paid channels',channel]]:[]);
 const head=['Channel','Spend','Customers',...ages.map(a=>`${a} days`),'Pays back by'];
 const rows=scopes.map(([name,sc],ri)=>{
  const all=ms.map(m=>payback(m,30,sc,model,measure)), spend=all.reduce((s,p)=>s+p.total,0), n=all.reduce((s,p)=>s+p.n,0);
  const byAge=ages.map(a=>{const done=ms.map(m=>payback(m,a,sc,model,measure)).filter(p=>p.value!=null),sp=done.reduce((s,p)=>s+p.total,0);
   return {k:done.length,ratio:sp?done.reduce((s,p)=>s+p.value,0)/sp:null};});
  const first=byAge.findIndex(b=>b.ratio!=null&&b.ratio>=1);
  const cells=byAge.map(b=>b.ratio==null?`<td>${b.k?'No spend':'Pending'}</td>`:`<td class="${b.ratio>=1?'good':'bad'}">${b.ratio.toFixed(2)}×<small>${b.k} of ${ms.length} cohorts</small></td>`).join('');
  const by=!spend?'No spend':first>=0?`${ages[first]} days`:byAge.at(-1).k?'Not within 365 days':'Not yet';
  return `<tr${ri===scopes.length-1&&keys.length>1?' class="start"':''}><td>${esc(name)}</td><td>${esc(spend?money(spend):'—')}</td><td>${n.toLocaleString('en-US')}</td>${cells}<td>${esc(by)}</td></tr>`;
 }).join('');
 return `<table><thead><tr>${head.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
}
function drawPayback(){
 const {ms,model,channel,chName}=state, age=+get('payAge').value, measure=get('payMeasure').value, label=`${measures[measure]} by ${age} days`;
 get('payTitle').textContent=`Payback: spend vs ${measures[measure].toLowerCase()} returned`;
 get('paySub').textContent=`${mon(ms[0])} – ${mon(ms.at(-1))} · ${chName} · ${measures[measure].toLowerCase()} each cohort returned by ${age} days`;
 get('pay').innerHTML=paybackChart(ms,ms.map(m=>payback(m,age,channel,model,measure)),label);
 get('payTable').innerHTML=paybackTable(ms,channel,model,measure);
}
let state;
function drawEff(){
 const {ms,model,max}=state, metric=get('metric').value, age=metric==='roas'?90:max, keys=Object.keys(channels).filter(k=>k!=='UNKNOWN');
 get('effTitle').textContent=metrics[metric]+' by cohort';
 get('eff').innerHTML=plot('',ms.map(monS),keys.map(k=>({name:channels[k],v:ms.map(m=>data.find(r=>r.month===m&&r.channel===k&&r.age===age&&r.model===model)?.[metric]??null)})),metric==='cac'?'USD':'×','line');
}
function draw(){
 const i=months.indexOf(get('start').value), span=+get('span').value, model=get('model').value, max=+get('age').value, channel=get('channel').value;
 const ms=months.slice(i,i+span+1), c=cohortModel(data,ms,channel,model,max), chName=get('channel').selectedOptions[0].text;
 state={ms,model,max,channel,chName};
 const later=ms.length-1, pl=later===1?'':'s', note=later<span?` (only ${later} later cohort${pl} in the data)`:'';
 get('summarySub').textContent=(later?`${mon(ms[0])} and the ${later} cohort${pl} after it${note}`:`${mon(ms[0])} is the latest cohort in the data`)+` · ${chName}`;
 get('curveSub').textContent=(later?`${mon(ms[0])} compared with the next ${later} cohort${pl}${note}`:`${mon(ms[0])} only; no later cohorts to compare`)+` · ${chName}`;
 summary(c,ms,model);
 get('legend').innerHTML=legend(c);
 get('curve').innerHTML=cohortChart(c);
 get('triangle').innerHTML=triangle(c);
 get('mix').innerHTML=plot('',ms.map(monS),Object.keys(channels).map(k=>({name:channels[k],v:ms.map(m=>data.find(r=>r.month===m&&r.channel===k&&r.age===30&&r.model===model)?.n??0)})),'count','stack');
 drawPayback();
 drawByChannel();
 drawEff();
}
const wrap=get('curveWrap');
wrap.addEventListener('mouseover',e=>{const m=e.target.closest('[data-m]')?.dataset.m;wrap.classList.toggle('focus',!!m);wrap.querySelectorAll('[data-m]').forEach(el=>el.classList.toggle('on',el.dataset.m===m));});
wrap.addEventListener('mouseleave',()=>wrap.classList.remove('focus'));
get('filters').addEventListener('change',draw);
get('metric').addEventListener('change',drawEff);
get('byChAge').addEventListener('change',drawByChannel);
for(const id of ['payAge','payMeasure'])get(id).addEventListener('change',drawPayback);
draw();
