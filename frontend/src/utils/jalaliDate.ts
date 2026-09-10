const div = (a:number,b:number)=>Math.floor(a/b);
const mod = (a:number,b:number)=>a-Math.floor(a/b)*b;

export function toJalali(gy:number,gm:number,gd:number){
  const gdm=[0,31,59,90,120,151,181,212,243,273,304,334];
  let gy2=gm>2?gy+1:gy;
  let days=355666+365*gy+div(gy2+3,4)-div(gy2+99,100)+div(gy2+399,400)+gd+gdm[gm-1];
  let jy=-1595+33*div(days,12053); days=mod(days,12053);
  jy+=4*div(days,1461); days=mod(days,1461);
  if(days>365){jy+=div(days-1,365);days=mod(days-1,365);}
  const jm=days<186?1+div(days,31):7+div(days-186,30);
  const jd=1+mod(days<186?days:days-186, days<186?31:30);
  return {jy,jm,jd};
}

export function toGregorian(jy:number,jm:number,jd:number){
  let jy2=jy+1595;
  let days=-355668+365*jy2+div(jy2,33)*8+div(mod(jy2,33)+3,4)+jd+(jm<7?(jm-1)*31:(jm-7)*30+186);
  let gy=400*div(days,146097); days=mod(days,146097);
  if(days>36524){gy+=100*div(--days,36524);days=mod(days,36524);if(days>=365)days++;}
  gy+=4*div(days,1461); days=mod(days,1461);
  if(days>365){gy+=div(days-1,365);days=mod(days-1,365);}
  let gd=days+1;
  const leap=(y:number)=>y%4===0&&(y%100!==0||y%400===0);
  const md=[31,leap(gy)?29:28,31,30,31,30,31,31,30,31,30,31];
  let gm=1;
  while(gd>md[gm-1]){gd-=md[gm-1];gm++;}
  return {gy,gm,gd};
}

export function isJalaliLeapYear(y:number){
  const a=toGregorian(y,12,1);
  const b=toGregorian(y+1,1,1);
  const da=new Date(a.gy,a.gm-1,a.gd).getTime();
  const db=new Date(b.gy,b.gm-1,b.gd).getTime();
  return Math.round((db-da)/86400000)===366;
}
export function jalaliMonthDays(y:number,m:number){return m<=6?31:m<=11?30:(isJalaliLeapYear(y)?30:29);}
export function formatJalali(y:number,m:number,d:number){return `${y}/${String(m).padStart(2,"0")}/${String(d).padStart(2,"0")}`;}
export function parseJalali(value:string){
  const clean=value.replace(/[۰-۹]/g,c=>String("۰۱۲۳۴۵۶۷۸۹".indexOf(c))).replace(/[٠-٩]/g,c=>String("٠١٢٣٤٥٦٧٨٩".indexOf(c))).replace(/-/g,"/");
  const match=/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/.exec(clean.trim());
  if(!match)return null;
  const y=Number(match[1]),m=Number(match[2]),d=Number(match[3]);
  if(m<1||m>12||d<1||d>jalaliMonthDays(y,m))return null;
  return {jy:y,jm:m,jd:d};
}
export function jalaliDateToLocalIso(value:string,endOfDay=false){
  const j=parseJalali(value); if(!j)return undefined;
  const g=toGregorian(j.jy,j.jm,j.jd);
  const dt=new Date(g.gy,g.gm-1,g.gd,endOfDay?23:0,endOfDay?59:0,endOfDay?59:0,endOfDay?999:0);
  const pad=(n:number)=>String(n).padStart(2,"0");
  return `${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
}
export function todayJalali(){const d=new Date();const j=toJalali(d.getFullYear(),d.getMonth()+1,d.getDate());return formatJalali(j.jy,j.jm,j.jd);}
export function shiftJalali(y:number,m:number,delta:number){
  let nm=m+delta, ny=y; while(nm<1){nm+=12;ny--;} while(nm>12){nm-=12;ny++;} return {y:ny,m:nm};
}
export function jalaliMonthFirstWeekday(y:number,m:number){const g=toGregorian(y,m,1);return new Date(g.gy,g.gm-1,g.gd).getDay();}
