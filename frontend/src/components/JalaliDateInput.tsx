import {useEffect,useMemo,useState} from "react";
import {Box,Button,IconButton,Popover,Stack,TextField,Typography} from "@mui/material";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import {formatJalali,jalaliMonthDays,jalaliMonthFirstWeekday,parseJalali,shiftJalali,todayJalali} from "../utils/jalaliDate";

const months=["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"];
const weekdays=["ی","د","س","چ","پ","ج","ش"];

export default function JalaliDateInput({label,value,onChange,required=false,allowClear=false}:{label:string;value:string;onChange:(value:string)=>void;required?:boolean;allowClear?:boolean}){
 const initial=parseJalali(value)||parseJalali(todayJalali())!;
 const [view,setView]=useState({y:initial.jy,m:initial.jm});
 const [anchor,setAnchor]=useState<HTMLElement|null>(null);
 const parsed=useMemo(()=>parseJalali(value),[value]);
 useEffect(()=>{if(parsed)setView({y:parsed.jy,m:parsed.jm});},[value]);
 const days=jalaliMonthDays(view.y,view.m), first=jalaliMonthFirstWeekday(view.y,view.m);
 const cells=Array.from({length:first+days},(_,i)=>i<first?null:i-first+1);
 const select=(d:number)=>{const v=formatJalali(view.y,view.m,d);onChange(v);setAnchor(null);};
 const setToday=()=>{const v=todayJalali();onChange(v);const p=parseJalali(v)!;setView({y:p.jy,m:p.jm});setAnchor(null);};
 const onText=(v:string)=>onChange(v.replace(/[^0-9۰-۹\/]/g,""));
 return <>
  <TextField fullWidth label={label} value={value} onChange={e=>onText(e.target.value)} onClick={e=>setAnchor(e.currentTarget)} placeholder="۱۴۰۵/۰۶/۱۵" required={required} error={Boolean(value)&&!parsed} helperText={value&&!parsed?"تاریخ شمسی نامعتبر است؛ قالب ۱۴۰۵/۰۶/۱۵":"فرمت: سال/ماه/روز شمسی"} slotProps={{inputLabel:{shrink:true}}}/>
  <Popover open={Boolean(anchor)} anchorEl={anchor} onClose={()=>setAnchor(null)} anchorOrigin={{vertical:"bottom",horizontal:"right"}}>
   <Box sx={{p:2,width:320,dir:"rtl"}} dir="rtl"><Stack direction="row" sx={{alignItems:"center",justifyContent:"space-between"}}><IconButton onClick={()=>setView(v=>shiftJalali(v.y,v.m,-1))}><ChevronRightIcon/></IconButton><Typography sx={{fontWeight:700}}>{months[view.m-1]} {view.y}</Typography><IconButton onClick={()=>setView(v=>shiftJalali(v.y,v.m,1))}><ChevronLeftIcon/></IconButton></Stack>
    <Box sx={{display:"grid",gridTemplateColumns:"repeat(7,1fr)",gap:.5,mt:1}}>{weekdays.map(w=><Typography key={w} align="center" variant="caption" sx={{fontWeight:700}}>{w}</Typography>)}{cells.map((d,i)=>d===null?<Box key={`e${i}`}/>:<Button key={d} size="small" onClick={()=>select(d)} variant={parsed?.jy===view.y&&parsed?.jm===view.m&&parsed?.jd===d?"contained":"text"}>{d.toLocaleString("fa-IR")}</Button>)}</Box>
    <Stack direction="row" sx={{mt:1,justifyContent:"space-between"}}><Button size="small" onClick={setToday}>امروز</Button>{allowClear&&<Button size="small" color="inherit" onClick={()=>{onChange("");setAnchor(null)}}>پاک کردن</Button>}</Stack>
   </Box>
  </Popover>
 </>;
}
