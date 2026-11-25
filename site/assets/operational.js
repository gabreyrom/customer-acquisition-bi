const get=id=>document.getElementById(id);
get('asof').textContent='Synthetic digital bank · Data as of '+new Date(snapshot.asOf+'T00:00Z').toLocaleString('en-US',{month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
const byCamp={};for(const r of data)(byCamp[r.campaign]??=[]).push(r);
for(const k in byCamp)byCamp[k].sort((a,b)=>a.day<b.day?-1:1);
const campaigns=Object.keys(byCamp).sort(), campChannel={G:'Google Ads',M:'Meta Ads',F:'Paid affiliates'};
const channelOf=c=>campChannel[c[0]]||'Other', channelList=[...new Set(campaigns.map(channelOf))].sort();
const campsOf=ch=>campaigns.filter(c=>ch==='ALL'||channelOf(c)===ch);
const days=data.map(r=>r.day).sort(), first=days[0], last=days.at(-1);
const addDays=(d,k)=>new Date(Date.parse(d+'T00:00Z')+k*864e5).toISOString().slice(0,10);
const fmtD=(d,o)=>new Date(d+'T00:00Z').toLocaleString('en-US',{...o,timeZone:'UTC'});
const fmtDay=d=>fmtD(d,{month:'short',day:'numeric'}), fmtDayY=d=>fmtD(d,{month:'short',day:'numeric',year:'numeric'}), fmtDow=d=>fmtD(d,{weekday:'short',month:'short',day:'numeric'});
const sum=(r,k)=>r.length&&r.every(x=>x[k]!=null)?r.reduce((s,x)=>s+x[k],0):null;
const rowsFor=(c,from,to)=>byCamp[c].filter(x=>x.day>=from&&x.day<=to);
// Daily rows for several campaigns added together. A day's plan (or plan to date) is unavailable if any campaign lacks it.
function combine(list,from,to){
 if(list.length===1)return rowsFor(list[0],from,to);
 const byDay=new Map();
 for(const c of list)for(const x of rowsFor(c,from,to)){
  const r=byDay.get(x.day)||{day:x.day,parts:0};
  for(const k of ['actual','eligible','plan','atd','ptd','n','m','a','forecast'])r[k]=r.parts&&r[k]==null||x[k]==null?null:(r[k]||0)+x[k];
  r.parts++; byDay.set(x.day,r);
 }
 return [...byDay.values()].sort((a,b)=>a.day<b.day?-1:1).map(r=>({...r,cac:r.eligible!=null&&r.n?r.eligible/r.n/100:null}));
}
const pct=v=>v==null?'—':Math.round(v*100)+'%';
const cents=v=>money(v==null?null:v/100);
function stats(r){
 const s={actual:sum(r,'actual'),eligible:sum(r,'eligible'),plan:sum(r,'plan'),n:sum(r,'n')??0,m:sum(r,'m')??0,a:sum(r,'a')??0,forecast:sum(r,'forecast')};
 s.cac=s.eligible!=null&&s.n?s.eligible/s.n/100:null; s.act=s.m?s.a/s.m:null; s.pace=s.plan?s.actual/s.plan:null; s.perDollar=s.eligible?s.forecast/s.eligible:null;
 s.noPlan=r.filter(x=>x.plan==null); return s;
}
get('channel').innerHTML=`<option value="ALL">All channels</option>`+channelList.map(ch=>`<option value="${esc(ch)}">${esc(ch)}</option>`).join('');
function fillCampaigns(selected='ALL'){
 const ch=get('channel').value, list=campsOf(ch);
 get('campaign').innerHTML=`<option value="ALL">All campaigns (${list.length})</option>`+list.map(c=>`<option value="${esc(c)}">${esc(c)}${ch==='ALL'?' · '+esc(channelOf(c)):''}</option>`).join('');
 get('campaign').value=list.includes(selected)?selected:'ALL';
}
fillCampaigns();
get('start').min=first; get('start').max=last;
function selection(){
 const ch=get('channel').value, cp=get('campaign').value;
 if(cp!=='ALL')return {list:[cp],label:`${cp} · ${channelOf(cp)}`,ch,cp};
 const list=campsOf(ch);
 return {list,label:`${ch==='ALL'?'All channels':ch} · ${list.length} campaign${list.length===1?'':'s'}`,ch,cp};
}

function delta(cur,prev,goodUp,label){
 if(cur==null||prev==null||!prev)return '<span class="delta">No prior period to compare</span>';
 const ch=(cur-prev)/Math.abs(prev);
 if(Math.abs(ch)<.005)return `<span class="delta">No change vs prior ${label}</span>`;
 const cls=goodUp==null?'':(ch>0)===goodUp?'good':'bad';
 return `<span class="delta ${cls}">${ch>0?'▲':'▼'} ${Math.round(Math.abs(ch)*100)}% vs prior ${label}</span>`;
}
function tiles(s,p,label,n){
 const t=[];
 t.push(['Actual spend',cents(s.actual),s.plan!=null?`Plan ${cents(s.plan)} · ${pct(s.pace)} of plan`:`Plan incomplete on ${s.noPlan.length} of ${n} days`,delta(s.actual,p?.actual,null,label)]);
 t.push(['Signups',s.n.toLocaleString('en-US'),'Attributed to the selection',delta(s.n,p?.n,true,label)]);
 t.push(['Cost per signup (CAC)',s.cac==null?'No signups':money(s.cac),'Spend ÷ signups',delta(s.cac,p?.cac,false,label)]);
 const young=s.n-s.m;
 t.push(['Activated within 30 days',s.m?pct(s.act):'Too early to tell',s.m?`${s.a} of ${s.m} signups old enough to judge`+(young?` · ${young} still under 30 days`:''):(s.n?`None of the ${s.n} signups is 30 days old yet`:'No signups'),
  s.m&&p?.m?(()=>{const d=Math.round((s.act-p.act)*100);return d?`<span class="delta ${d>0?'good':'bad'}">${d>0?'▲':'▼'} ${Math.abs(d)} pts vs prior ${label}</span>`:`<span class="delta">No change vs prior ${label}</span>`})():'']);
 t.push(['Expected first-year contribution',cents(s.forecast),s.n?`${money(s.forecast/s.n/100)} per signup · $${s.perDollar==null?'—':s.perDollar.toFixed(2)} per $1 spent`:'No signups',delta(s.forecast,p?.forecast,true,label)]);
 get('tiles').innerHTML=t.map(([k,v,sub,d])=>`<div><span class="k">${esc(k)}</span><strong>${esc(v)}</strong>${esc(sub)}${d}</div>`).join('');
}
function checks(r,s,n,span,list,start,end){
 const items=[], dates=a=>a.map(x=>fmtDay(x.day)).join(', ');
 const missing=list.map(c=>[c,rowsFor(c,start,end).filter(x=>x.plan==null)]).filter(([,d])=>d.length);
 items.push(missing.length?['warn',`No spending plan: ${missing.map(([c,d])=>`${c} on ${dates(d)}`).join('; ')}. Planned spend and pacing cannot be calculated for this period; confirm the plan with the campaign owner.`]:['ok','A spending plan exists for every day in the period.']);
 const zero=r.filter(x=>x.n===0&&x.actual>0);
 if(zero.length)items.push(['info',`Spend but no signups on ${dates(zero)}. Signups can arrive a few days after the spend, so read daily cost per signup with care.`]);
 const young=s.n-s.m;
 items.push(!s.n?['info','No signups in this period.']:young?['info',`${young} of ${s.n} signups are under 30 days old, so their activation is not known yet. Wait before judging activation.`]:['ok','Every signup is old enough to judge 30-day activation.']);
 if(n<span)items.push(['info',`Data ends ${fmtDayY(last)}, so only ${n} of ${span} days are shown.`]);
 get('checks').innerHTML=items.map(([k,t])=>`<li class="${k}">${esc(t)}</li>`).join('');
}
function compare(start,end,sel){
 const head=['Channel / campaign','Actual spend','% of plan','Signups','Cost per signup','Activated (30 days)','Expected per $1'];
 const row=(cls,attrs,name,list,isSel)=>{const s=stats(combine(list,start,end));
  return `<tr class="${cls}${isSel?' sel':''}" ${attrs} tabindex="0"${isSel?' aria-current="true"':''}>`+[name,cents(s.actual),s.pace==null?'Plan incomplete':pct(s.pace),s.n,s.cac==null?'No signups':money(s.cac),s.m?`${pct(s.act)} (${s.a} of ${s.m})`:'Too early',s.perDollar==null?'—':'$'+s.perDollar.toFixed(2)].map(v=>`<td>${esc(v)}</td>`).join('')+'</tr>';};
 const body=channelList.map(ch=>row('ch',`data-ch="${esc(ch)}"`,ch,campsOf(ch),sel.cp==='ALL'&&sel.ch===ch)+
  campsOf(ch).map(c=>row('camp',`data-ch="${esc(ch)}" data-c="${esc(c)}"`,c,[c],sel.cp===c)).join('')).join('')+
  row('total','data-ch="ALL"','All channels',campaigns,sel.cp==='ALL'&&sel.ch==='ALL');
 get('compare').innerHTML=`<table><thead><tr>${head.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table>`;
}
function charts(r){
 const day=r.map(x=>fmtDay(x.day)), d=v=>v==null?null:v/100;
 get('chSpend').innerHTML=plot('',day,[{name:'Actual spend',v:r.map(x=>d(x.actual))},{name:'Plan',v:r.map(x=>d(x.plan)),c:'#9ab2bd'}],'USD','bar',r.map(x=>x.plan==null?'No plan':''));
 get('chPace').innerHTML=plot('',day,[{name:'Actual to date',v:r.map(x=>d(x.atd))},{name:'Plan to date',v:r.map(x=>d(x.ptd)),d:true,c:'#67798a'}],'USD','line',r.map(x=>x.ptd==null?'Plan incomplete':''));
 get('chSignups').innerHTML=plot('',day,[{name:'Signups',v:r.map(x=>x.n)}],'count','bar',r.map(x=>x.n===0&&x.actual>0?'No signups':''));
 get('chCac').innerHTML=plot('',day,[{name:'Cost per signup',v:r.map(x=>x.cac)}],'USD','line',r.map(x=>x.cac==null?'No signups':''));
 get('chAct').innerHTML=plot('',day,[{name:'Activated',v:r.map(x=>x.a),c:'#1b7f4b'},{name:'Not activated',v:r.map(x=>x.m-x.a),c:'#ad451f'},{name:'Under 30 days old',v:r.map(x=>x.n-x.m),c:'#b9cbd3'}],'count','stack');
}
function detail(r,s,multi){
 const head=['Date','Actual spend','Planned spend','Signups','Cost per signup','Activated','Not activated','Under 30 days old','Expected contribution','Plan status'];
 const td=(v,flag)=>`<td${flag?' class="flag"':''}>${esc(v)}</td>`;
 const noPlan=multi?'Plan missing for a campaign':'No plan for this day';
 const body=r.map(x=>{const zero=x.n===0&&x.actual>0;return '<tr>'+td(fmtDow(x.day))+td(cents(x.actual))+td(x.plan==null?'No plan':cents(x.plan),x.plan==null)+td(x.n,zero)+td(x.cac==null?'No signups':money(x.cac),zero)+td(x.a)+td(x.m-x.a)+td(x.n-x.m)+td(cents(x.forecast))+td(x.plan==null?noPlan:x.ptd==null?'Month-to-date plan incomplete':'Plan available',x.plan==null)+'</tr>';}).join('');
 const foot='<tr>'+['Total',cents(s.actual),s.plan==null?'Incomplete':cents(s.plan),s.n,s.cac==null?'—':money(s.cac),s.a,s.m-s.a,s.n-s.m,cents(s.forecast),s.noPlan.length?`${s.noPlan.length} day${s.noPlan.length>1?'s':''} without full plan`:'Complete'].map(v=>`<td>${esc(v)}</td>`).join('')+'</tr>';
 get('detail').innerHTML=`<table><thead><tr>${head.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${body}</tbody><tfoot>${foot}</tfoot></table>`;
}
function draw(){
 const sel=selection(), span=+get('span').value;
 let start=get('start').value||'2026-05-01'; if(start<first)start=first; if(start>last)start=last;
 const end=addDays(start,span-1)<last?addDays(start,span-1):last, r=combine(sel.list,start,end), n=r.length, label=`${span} days`;
 const prevStart=addDays(start,-span), p=prevStart>=first?stats(combine(sel.list,prevStart,addDays(start,-1))):null;
 const s=stats(r);
 get('range').innerHTML=`<strong>${esc(fmtDay(start))} – ${esc(fmtDayY(end))}</strong>${n<span?`Data ends here · ${n} of ${span} days`:`${span} days`}`;
 get('sumSub').textContent=`${sel.label} · ${fmtDay(start)} – ${fmtDayY(end)}`+(p?` · changes compared with the prior ${span} days`:'');
 tiles(s,p,label,n); checks(r,s,n,span,sel.list,start,end); compare(start,end,sel); charts(r); detail(r,s,sel.list.length>1);
}
function pick(tr){
 get('channel').value=tr.dataset.ch; fillCampaigns(tr.dataset.c||'ALL'); draw();
 get('compare').querySelector('tr.sel')?.focus();
}
get('compare').addEventListener('click',e=>{const tr=e.target.closest('tr[data-ch]');if(tr)pick(tr);});
get('compare').addEventListener('keydown',e=>{const tr=e.target.closest('tr[data-ch]');if(tr&&(e.key==='Enter'||e.key===' ')){e.preventDefault();pick(tr);}});
get('channel').addEventListener('change',()=>{fillCampaigns();draw();});
get('campaign').addEventListener('change',()=>{const c=get('campaign').value;if(c!=='ALL'&&get('channel').value==='ALL'){get('channel').value=channelOf(c);fillCampaigns(c);}draw();});
for(const id of ['start','span'])get(id).addEventListener('change',draw);
draw();
