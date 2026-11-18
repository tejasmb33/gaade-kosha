import React,{useEffect,useState} from 'react';
const key='gaadamruta:intro:v1';
function shouldPlay(){
 if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)return false;
 try{return !sessionStorage.getItem(key);}catch{return true;}
}
export default function LaunchExperience({children}){
 const [active,setActive]=useState(shouldPlay),[reveal,setReveal]=useState(false);
 function finish(){try{sessionStorage.setItem(key,'seen');}catch{}setActive(false);setReveal(true);}
 useEffect(()=>{
  if(!active)return;
  const previous=document.body.style.overflow;document.body.style.overflow='hidden';
  const timer=setTimeout(finish,1800);
  const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
  const changed=()=>{if(motion.matches)finish();};motion.addEventListener('change',changed);
  return()=>{clearTimeout(timer);document.body.style.overflow=previous;motion.removeEventListener('change',changed);};
 },[active]);
 return <><div className={reveal?'site-stage site-reveal':'site-stage'} inert={active?true:undefined} aria-hidden={active?true:undefined}>{children}</div>{active&&<div className="launch-screen" aria-label="ಗಾದಾಮೃತಕ್ಕೆ ಸ್ವಾಗತ" role="region"><div className="launch-map"><img src="/images/karnataka-intro.svg" alt="ಕರ್ನಾಟಕ"/><span lang="kn">ಗಾದಾಮೃತ</span></div><button className="launch-skip" onClick={finish}>ಮುಂದುವರಿಸಿ (Skip) →</button></div>}</>;
}
