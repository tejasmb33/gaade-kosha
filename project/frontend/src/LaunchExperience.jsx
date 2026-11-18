import React,{useEffect,useState,useRef} from 'react';
const key='gaadamruta:intro:v3';
function shouldPlay(){
 if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)return false;
 try{return !sessionStorage.getItem(key);}catch{return true;}
}
function HampiParticles(){
 const ref=useRef(null);
 useEffect(()=>{
  const canvas=ref.current,ctx=canvas.getContext('2d');if(!ctx)return;
  let frame,stopped=false;const start=performance.now();
  const width=innerWidth,height=innerHeight,ratio=Math.min(devicePixelRatio||1,2);
  canvas.width=width*ratio;canvas.height=height*ratio;ctx.scale(ratio,ratio);
  const particles=Array.from({length:Math.min(360,Math.round(width/3))},(_,i)=>({x:Math.random()*width,y:Math.random()*height,tx:Math.random()*width,ty:Math.random()*height,r:.6+Math.random()*1.3,phase:Math.random()*6.28,red:i%9===0}));
  const photo=new Image();photo.src='/images/hampi-chariot.jpg';
  photo.onload=()=>{if(stopped)return;const sample=document.createElement('canvas');sample.width=width;sample.height=height;const c=sample.getContext('2d');if(!c)return;const scale=Math.max(width/photo.width,height/photo.height);c.drawImage(photo,(width-photo.width*scale)/2,(height-photo.height*scale)*.58,photo.width*scale,photo.height*scale);const data=c.getImageData(0,0,width,height).data;
   particles.forEach(p=>{for(let n=0;n<35;n++){const x=Math.floor(Math.random()*width),y=Math.floor(height*(.2+Math.random()*.75)),i=(y*width+x)*4;if(data[i]+data[i+1]+data[i+2]<330){p.tx=x;p.ty=y;break;}}});
  };
  function draw(now){if(stopped)return;const t=(now-start)/1000;ctx.clearRect(0,0,width,height);if(t>=3.5){const progress=Math.min(1,(t-3.5)/1.1),ease=1-Math.pow(1-progress,3);ctx.globalAlpha=Math.min(1,(t-3.5)*4)*Math.max(0,1-(t-4.6)/.4);
   particles.forEach(p=>{const x=p.x+(p.tx-p.x)*ease+Math.sin(t*3+p.phase)*12*(1-ease),y=p.y+(p.ty-p.y)*ease+Math.cos(t*2+p.phase)*15*(1-ease);ctx.beginPath();ctx.fillStyle=p.red?'#ef6943':'#ffe6a0';ctx.shadowColor=p.red?'#d84120':'#ffbd35';ctx.shadowBlur=8;ctx.arc(x,y,p.r,0,Math.PI*2);ctx.fill();});}
   if(t<5)frame=requestAnimationFrame(draw);
  }frame=requestAnimationFrame(draw);
  return()=>{stopped=true;cancelAnimationFrame(frame);photo.onload=null;};
 },[]);
 return <canvas className="launch-particles" ref={ref} aria-hidden="true"/>;
}
export default function LaunchExperience({children}){
 const [active,setActive]=useState(shouldPlay),[reveal,setReveal]=useState(false);
 function finish(){try{sessionStorage.setItem(key,'seen');}catch{}setActive(false);setReveal(true);}
 useEffect(()=>{
  if(!active)return;
  const previous=document.body.style.overflow;document.body.style.overflow='hidden';
  const timer=setTimeout(finish,5000);
  const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
  const changed=()=>{if(motion.matches)finish();};motion.addEventListener('change',changed);
  return()=>{clearTimeout(timer);document.body.style.overflow=previous;motion.removeEventListener('change',changed);};
 },[active]);
 return <><div className={reveal?'site-stage site-reveal':'site-stage'} inert={active?true:undefined} aria-hidden={active?true:undefined}>{children}</div>{active&&<div className="launch-screen" aria-label="ಗಾದಾಮೃತಕ್ಕೆ ಸ್ವಾಗತ" role="region"><div className="launch-hampi" aria-hidden="true"/><HampiParticles/><div className="launch-map"><img src="/images/karnataka-intro.svg" alt="ಕರ್ನಾಟಕ"/><div className="launch-outline" aria-hidden="true"/><span lang="kn">ಗಾದಾಮೃತ</span></div><button className="launch-skip" onClick={finish}>ಮುಂದುವರಿಸಿ (Skip) →</button></div>}</>;
}
