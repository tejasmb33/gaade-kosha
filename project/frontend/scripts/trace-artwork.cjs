// Authoring utility: trace the white separators in the supplied PNG into SVG.
// Does not edit the raster image, download models, or run during production builds.
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');

// Minimum-cost one-to-one assignment of existing district positions to artwork
// regions. These are illustrative identities, not surveyed administrative areas.
function assign(cost){
 const n=cost.length,u=Array(n+1).fill(0),v=Array(n+1).fill(0),p=Array(n+1).fill(0),way=Array(n+1).fill(0);
 for(let i=1;i<=n;i++){
  p[0]=i;let j0=0;const min=Array(n+1).fill(Infinity),used=Array(n+1).fill(false);
  do{
   used[j0]=true;const i0=p[j0];let delta=Infinity,j1=0;
   for(let j=1;j<=n;j++)if(!used[j]){const cur=cost[i0-1][j-1]-u[i0]-v[j];if(cur<min[j]){min[j]=cur;way[j]=j0;}if(min[j]<delta){delta=min[j];j1=j;}}
   for(let j=0;j<=n;j++)if(used[j]){u[p[j]]+=delta;v[j]-=delta;}else min[j]-=delta;
   j0=j1;
  }while(p[j0]!==0);
  do{const j1=way[j0];p[j0]=p[j1];j0=j1;}while(j0!==0);
 }
 const result=Array(n);for(let j=1;j<=n;j++)result[p[j]-1]=j-1;return result;
}

(async()=>{
 const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||undefined});
 try{
  const page=await browser.newPage();
  const image=fs.readFileSync(path.join(root,'public/images/karnataka-art-map.png')).toString('base64');
  const result=await page.evaluate(async image=>{
   const img=new Image();img.src='data:image/png;base64,'+image;await img.decode();
   const w=img.naturalWidth,h=img.naturalHeight,canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
   const context=canvas.getContext('2d');context.drawImage(img,0,0);
   const rgba=context.getImageData(0,0,w,h).data,white=new Uint8Array(w*h),barrier=new Uint8Array(w*h),radius=7;
   for(let i=0;i<w*h;i++){
    const r=rgba[i*4],g=rgba[i*4+1],b=rgba[i*4+2];
    white[i]=r>235&&g>235&&b>220&&Math.max(r,g,b)-Math.min(r,g,b)<35?1:0;
   }
   // Close small gaps in the illustrated white separators before flood filling.
   for(let y=radius;y<h-radius;y++)for(let x=radius;x<w-radius;x++)if(white[y*w+x])
    for(let dy=-radius;dy<=radius;dy++)for(let dx=-radius;dx<=radius;dx++)barrier[(y+dy)*w+x+dx]=1;
   const labels=new Int32Array(w*h),queue=new Int32Array(w*h),regions=[];let id=0;
   function distance(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1];const t=dx||dy?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))):0;return Math.hypot(p[0]-a[0]-dx*t,p[1]-a[1]-dy*t);}
   function simplify(points,tolerance=1.15){
    if(points.length<3)return points;
    let best=0,index=0;for(let i=1;i<points.length-1;i++){const d=distance(points[i],points[0],points.at(-1));if(d>best){best=d;index=i;}}
    return best>tolerance?[...simplify(points.slice(0,index+1),tolerance).slice(0,-1),...simplify(points.slice(index),tolerance)]:[points[0],points.at(-1)];
   }
   for(let start=0;start<w*h;start++){
    if(barrier[start]||labels[start])continue;
    id++;let head=0,tail=1;queue[0]=start;labels[start]=id;
    let minx=w,miny=h,maxx=0,maxy=0,sx=0,sy=0;
    while(head<tail){
     const q=queue[head++],x=q%w,y=Math.floor(q/w);minx=Math.min(minx,x);maxx=Math.max(maxx,x);miny=Math.min(miny,y);maxy=Math.max(maxy,y);sx+=x;sy+=y;
     for(const n of [x>0?q-1:-1,x<w-1?q+1:-1,y>0?q-w:-1,y<h-1?q+w:-1])if(n>=0&&!barrier[n]&&!labels[n]){labels[n]=id;queue[tail++]=n;}
    }
    if(tail<3000||tail>150000)continue;
    // Restore the separator thickness so outlines sit on the artwork's borders,
    // not on the shrunken flood-fill interior. Work entirely in image pixels.
    const pad=10,bw=maxx-minx+1+pad*2,bh=maxy-miny+1+pad*2,mask=new Uint8Array(bw*bh),ox=minx-pad,oy=miny-pad;
    for(let i=0;i<tail;i++){
     const x=queue[i]%w-ox,y=Math.floor(queue[i]/w)-oy;
     for(let dy=-9;dy<=9;dy++)for(let dx=-9;dx<=9;dx++)if(dx*dx+dy*dy<=81)mask[(y+dy)*bw+x+dx]=1;
    }
    const edges=new Map();
    function edge(ax,ay,bx,by){const key=ay*(bw+1)+ax;if(!edges.has(key))edges.set(key,[]);edges.get(key).push(by*(bw+1)+bx);}
    for(let y=1;y<bh-1;y++)for(let x=1;x<bw-1;x++)if(mask[y*bw+x]){
     if(!mask[(y-1)*bw+x])edge(x,y,x+1,y);
     if(!mask[y*bw+x+1])edge(x+1,y,x+1,y+1);
     if(!mask[(y+1)*bw+x])edge(x+1,y+1,x,y+1);
     if(!mask[y*bw+x-1])edge(x,y+1,x,y);
    }
    const loops=[];
    while(edges.size){
     const first=edges.keys().next().value;let key=first,points=[],limit=0;
     do{
      points.push([key%(bw+1)+ox,Math.floor(key/(bw+1))+oy]);
      const next=edges.get(key);if(!next?.length)break;
      const previous=key;key=next.pop();if(!next.length)edges.delete(previous);
      if(++limit>100000)throw Error('Contour did not close');
     }while(key!==first);
     if(points.length>3){const area=Math.abs(points.reduce((a,p,i)=>{const q=points[(i+1)%points.length];return a+p[0]*q[1]-q[0]*p[1];},0));loops.push({points,area});}
    }
    const loop=loops.sort((a,b)=>b.area-a.area)[0].points;
    // Simplify two halves of a closed contour without collapsing its endpoints.
    let opposite=1;for(let i=2;i<loop.length;i++)if(Math.hypot(loop[i][0]-loop[0][0],loop[i][1]-loop[0][1])>Math.hypot(loop[opposite][0]-loop[0][0],loop[opposite][1]-loop[0][1]))opposite=i;
    const points=[...simplify(loop.slice(0,opposite+1)).slice(0,-1),...simplify([...loop.slice(opposite),loop[0]]).slice(0,-1)];
    regions.push({regionId:id,center:[Math.round(sx/tail),Math.round(sy/tail)],d:'M'+points.map(p=>p.join(',')).join('L')+'Z',points});
   }
   return{w,h,regions};
  },image);
  const geometry=JSON.parse(fs.readFileSync(path.join(root,'src/data/karnataka-boundaries.json'),'utf8'));
  if(result.regions.length!==geometry.paths.length)throw Error('Expected 31 distinct artwork regions, found '+result.regions.length);
  const assignment=assign(geometry.paths.map(shape=>result.regions.map(region=>Math.pow((shape.center[0]*1.02-20-region.center[0])/result.w,2)+Math.pow((shape.center[1]*1.06-region.center[1])/result.h,2))));
  const output={viewBox:`0 0 ${result.w} ${result.h}`,width:result.w,height:result.h,sourceImage:'/images/karnataka-art-map.png',description:'Image-space contours traced from the supplied illustration. Decorative regions, not geographic boundaries.',paths:geometry.paths.map((shape,i)=>{const r=result.regions[assignment[i]];return{code:shape.code,regionId:r.regionId,center:r.center,d:r.d};})};
  fs.writeFileSync(path.join(root,'src/data/karnataka-artwork-boundaries.json'),JSON.stringify(output)+'\n');
  console.log('Traced '+output.paths.length+' artwork outlines in native '+result.w+' × '+result.h+' image coordinates.');
  console.log(output.paths.map(s=>s.code+': '+s.center.join(',')).join('\n'));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
