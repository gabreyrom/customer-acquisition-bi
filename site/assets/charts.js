// Shared chart and formatting helpers for both dashboards.
const colors=['#006780','#ad451f','#5b56a0','#67798a'];
const esc=v=>String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const money=v=>v==null?'Unavailable':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(v);
const fmt=(v,u)=>v==null?'Unavailable':u==='USD'?money(v):u==='×'?v.toFixed(2)+'×':String(v);
function plot(title,labels,series,unit,kind='line',notes=[],positions=null,xTitle=''){
 const w=840,h=300,l=77,r=30,t=title?66:36,b=53, width=w-l-r,height=h-t-b;
 const all=kind==='stack'?labels.map((_,i)=>series.reduce((s,x)=>s+(x.v[i]||0),0)):series.flatMap(s=>s.v).filter(v=>v!=null);
 const base=labels.map(()=>0);
 let low=Math.min(0,...all),high=Math.max(1,...all);
 const y=v=>t+(high-v)/(high-low)*height;
 const step=width/Math.max(1,labels.length);
 const x=i=>positions?l+32+(width-64)*(positions[i]-positions[0])/((positions.at(-1)-positions[0])||1):l+(i+.5)*step;
 let a=[`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${esc(title)}"><rect width="${w}" height="${h}" fill="white"/><g font-family="Arial,sans-serif" fill="#193847">${title?`<text x="15" y="25" font-size="19" font-weight="bold">${esc(title)}</text>`:''}`];
 let lx=15;
 for(let k=0;k<series.length;k++){
  const s=series[k],c=s.c||colors[k];
  a.push(`<line x1="${lx}" x2="${lx+20}" y1="${t-21}" y2="${t-21}" stroke="${c}" stroke-width="3" ${s.d?'stroke-dasharray="5 4"':''}/><text x="${lx+25}" y="${t-17}" font-size="12">${esc(s.name)}</text>`);
  lx+=Math.max(117,s.name.length*7+34);
 }
 const span=(high-low)/4, mag=10**Math.floor(Math.log10(span));
 const stepY=Math.max(unit==='count'?1:0,(unit==='count'?[1,2,5,10]:[1,2,2.5,5,10]).map(f=>f*mag).find(s=>s>=span));
 low=Math.floor(low/stepY)*stepY; high=Math.ceil(high/stepY)*stepY;
 for(let i=0;i<=Math.round((high-low)/stepY);i++){
  const v=+(low+i*stepY).toFixed(6), u=y(v);
  const label=unit==='USD'?(v<0?'−$':'$')+Math.abs(v).toLocaleString('en-US'):unit==='×'?v+'×':v;
  a.push(`<line x1="${l}" x2="${w-r}" y1="${u}" y2="${u}" stroke="#dbe5e9"/><text x="${l-7}" y="${u+4}" text-anchor="end" font-size="11">${esc(label)}</text>`);
 }
 for(let i=0;i<labels.length;i++){
  if(notes[i])a.push(`<rect x="${x(i)-step/2}" y="${t}" width="${step}" height="${height}" fill="#f6d9cc" fill-opacity=".55"><title>${esc(labels[i]+': '+notes[i])}</title></rect>`);
  if(labels.length>16&&i%2)continue;
  a.push(`<text x="${x(i)}" y="266" text-anchor="middle" font-size="12">${esc(labels[i])}</text>`);
  if(notes[i]&&labels.length<=14)a.push(`<text x="${x(i)}" y="282" text-anchor="middle" fill="#955026" font-size="11">${esc(notes[i])}</text>`);
 }
 if(xTitle)a.push(`<text x="420" y="291" text-anchor="middle" font-size="12">${esc(xTitle)}</text>`);
 if(!all.length)a.push('<text x="430" y="150" text-anchor="middle" font-size="16">No available observations</text>');
 for(let k=0;k<series.length;k++){
  const s=series[k],c=s.c||colors[k];
  s.v.forEach((v,i)=>{
   if(v==null)return;
   const tip=esc(s.name+' · '+labels[i]+': '+fmt(v,unit)+(s.detail?.[i]?' · '+s.detail[i]:''));
   if(kind==='stack'){
    if(!v)return;
    const bw=Math.min(56,step*.6);
    a.push(`<rect x="${x(i)-bw/2}" y="${y(base[i]+v)}" width="${bw}" height="${y(base[i])-y(base[i]+v)}" fill="${c}"><title>${tip}</title></rect>`);
    base[i]+=v;
   }else if(kind==='bar'){
    const bw=Math.min(56,step*.72/series.length), xx=x(i)+(k-(series.length-1)/2)*bw-bw*.44;
    a.push(`<rect x="${xx}" y="${Math.min(y(v),y(0))}" width="${bw*.88}" height="${Math.max(1,Math.abs(y(v)-y(0)))}" fill="${c}"><title>${tip}</title></rect>`);
   }else{
    if(i>0&&s.v[i-1]!=null)a.push(`<line x1="${x(i-1)}" y1="${y(s.v[i-1])}" x2="${x(i)}" y2="${y(v)}" stroke="${c}" stroke-width="2.5" ${s.d?'stroke-dasharray="5 4"':''}/>`);
    a.push(`<circle cx="${x(i)}" cy="${y(v)}" r="4" fill="${c}"><title>${tip}</title></circle>`);
   }
  });
 }
 return a.join('')+'</g></svg>';
}
const ages=[30,90,180,365], channels={GOOGLE_ADS:'Google Ads',META_ADS:'Meta Ads',PAID_AFFILIATES:'Paid affiliates',UNKNOWN:'Unknown channel'};
const mon=m=>new Date(m+'-01T00:00Z').toLocaleString('en-US',{month:'short',year:'numeric',timeZone:'UTC'});
const metrics={cac:'Acquisition cost per customer (CAC)',roas:'90-day revenue ROAS',eff:'Realized contribution per $1 of spend'};
function cohortModel(data,months,channel,model,maxAge){
 const selected=ages.filter(a=>a<=maxAge);
 const point=(month,a)=>{
  const rows=data.filter(r=>r.month===month&&r.age===a&&r.model===model&&(channel==='ALL'||(channel==='PAID'?r.channel!=='UNKNOWN':r.channel===channel)));
  const sum=k=>rows.reduce((s,r)=>s+(r[k]||0),0);
  const n=sum('n'),m=sum('mature');
  const ok=n>0&&rows.filter(r=>r.n>0).every(r=>r.status==='MATURE')&&n===m;
  return {n,m,ok,real:ok?sum('real')/n/100:null,expected:ok?sum('expected')/n/100:null};
 };
 return {selected,groups:months.map(month=>({month,points:selected.map(a=>point(month,a))}))};
}
