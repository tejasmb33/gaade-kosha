import React,{useRef} from 'react';
import {X} from 'lucide-react';

export default function ClearableInput({onClear,clearLabel='Clear search',...props}){
  const input=useRef(null);
  return <span className="clearable-filter-input"><input {...props} ref={input}/>{props.value&&<button type="button" className="clear-filter-button" aria-label={clearLabel} title="ತೆರವುಗೊಳಿಸಿ · Clear" disabled={props.disabled} onClick={()=>{onClear();input.current?.focus();}}><X size={17}/></button>}</span>;
}
