/* Gaadamrutha adapter for Udgam Labs Shruti Kannada, Apache-2.0.
 * C API integration adapted from udgamlabs/shruti/examples/browser/shruti-worker.js.
 * Changes: fixed first-party model, checksum, Kannada language and bounded audio;
 * no remote model registry, telemetry, audio upload or transcript persistence.
 */
'use strict';
importScripts('needle/needle.js');
const MODEL_BYTES=29742447;
const MODEL_SHA='492cdfdea934061edfefd14f2bd1e0255468adc8d0f0e3e9c2847cee69d5d5d8';
const MODEL_URL=new URL('shruti-kannada.cact?sha='+MODEL_SHA,self.location.href).href;
const CACHE='gaadamrutha-shruti-kn-v1';
let engine=null,ready=false;
async function valid(bytes){
 if(bytes.byteLength!==MODEL_BYTES)return false;
 const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
 return Array.from(digest,b=>b.toString(16).padStart(2,'0')).join('')===MODEL_SHA;
}
async function modelBytes(){
 let cache;try{cache=await caches.open(CACHE);}catch{}
 if(cache){const hit=await cache.match(MODEL_URL);if(hit){const bytes=await hit.arrayBuffer();if(await valid(bytes))return new Uint8Array(bytes);await cache.delete(MODEL_URL);}}
 const response=await fetch(MODEL_URL,{credentials:'omit'});if(!response.ok)throw Error('Kannada model could not load.');
 const reader=response.body.getReader(),parts=[];let count=0;
 for(;;){const {done,value}=await reader.read();if(done)break;parts.push(value);count+=value.length;if(count>MODEL_BYTES){await reader.cancel();throw Error('Invalid Kannada model size.');}self.postMessage({type:'progress',loaded:count,total:MODEL_BYTES});}
 const bytes=new Uint8Array(count);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
 if(!await valid(bytes))throw Error('Kannada model checksum failed.');
 if(cache)try{await cache.put(MODEL_URL,new Response(bytes,{headers:{'Content-Type':'application/octet-stream'}}));}catch{}
 return bytes;
}
function alloc(size){const ptr=engine._malloc(size);if(!ptr)throw Error('Not enough memory for Kannada speech.');return ptr;}
function copy(bytes){const ptr=alloc(Math.max(4,bytes.length));engine.HEAPU8.set(bytes,ptr);return ptr;}
function lastError(){return engine.UTF8ToString(engine._needle_last_error())||'Kannada speech engine failed.';}
async function init(){
 const [weights,wasm]=await Promise.all([modelBytes(),fetch(new URL('needle/needle.wasm',self.location.href)).then(r=>{if(!r.ok)throw Error('Kannada engine could not load.');return r.arrayBuffer();})]);
 engine=await createNeedle({wasmBinary:wasm,print:()=>{},printErr:()=>{}});
 const ptr=copy(weights);let status;try{status=engine._needle_load(ptr,BigInt(weights.length));}finally{engine._free(ptr);}
 if(status<0)throw Error(lastError());if(!(engine._needle_models()&2))throw Error('Kannada speech model unavailable.');ready=true;
}
function transcribe(pcm){
 if(!ready||!(pcm instanceof Float32Array)||!pcm.length||pcm.length>16000*90)throw Error('Invalid Kannada recording.');
 const p=copy(new Uint8Array(pcm.buffer,pcm.byteOffset,pcm.byteLength)),language=copy(new TextEncoder().encode('kn\0'));
 const cap=Math.max(65536,Math.ceil(pcm.length/16000)*4096+16384),out=alloc(cap);
 try{if(engine._needle_transcribe(p,pcm.length,language,0,0,out,cap)<0)throw Error(lastError());const result=JSON.parse(engine.UTF8ToString(out));if(typeof result.text!=='string')throw Error('Invalid Kannada transcript.');return result.text.trim();}
 finally{engine._free(out);engine._free(language);engine._free(p);}
}
self.onmessage=async({data})=>{
 try{if(data.type==='init'){if(!ready)await init();self.postMessage({type:'ready'});}else if(data.type==='transcribe')self.postMessage({type:'result',text:transcribe(data.pcm)});}
 catch(error){self.postMessage({type:'error',message:error.message||'Kannada speech failed.'});}
};
