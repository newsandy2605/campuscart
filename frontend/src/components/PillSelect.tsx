'use client';
import { useState } from 'react';
export default function PillSelect({ label, options, value, onChange }: { label: string; options: string[]; value?: string; onChange?: (value: string) => void }) {
  const [open,setOpen]=useState(false); const current=value||label;
  return <div className="pill-wrap"><button type="button" className="pill-select" onClick={()=>setOpen(!open)}>{current} <span>⌄</span></button>{open&&<div className="pill-menu">{options.map(option=><button type="button" key={option} onClick={()=>{onChange?.(option);setOpen(false)}}>{option}</button>)}</div>}</div>;
}
