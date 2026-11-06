import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const seed=JSON.parse(fs.readFileSync(new URL('../js/seed.json',import.meta.url),'utf8'));
const storage=entries=>{
 const values=new Map(entries);
 return {getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,String(value)),removeItem:key=>values.delete(key)};
};
const response=data=>({ok:true,status:200,json:async()=>data});
const settle=()=>new Promise(resolve=>setImmediate(resolve));
let instance=0;
async function start({signedIn=true,hash='',reportFetch=async()=>response([])}={}){
 const originals=Object.fromEntries(['localStorage','sessionStorage','document','window','fetch','FormData'].map(key=>[key,globalThis[key]]));
 const db=structuredClone(seed),handlers={},body={innerHTML:''},toast={innerHTML:''};
 let modal='';
 const app={innerHTML:'',addEventListener:(type,handler)=>(handlers[type]??=[]).push(handler)};
 const calls=[];
 globalThis.localStorage=storage([['ucu_league_mode_v1','api']]);
 globalThis.sessionStorage=storage(signedIn?[
  ['ucu_league_token_v1','token-de-prueba'],
  ['ucu_league_user_v1',JSON.stringify({correo:'admin@test.uy',rol:'administrador'})]
 ]:[]);
 globalThis.document={
  getElementById:id=>({app,'main-body':body,'toast-area':toast})[id]??null,
  documentElement:{dataset:{}},
  querySelector:selector=>selector==='.shell'?{insertAdjacentHTML:(position,html)=>{modal=html}}:null,
 };
 globalThis.window={location:{hash},addEventListener(){},scrollTo(){}};
 globalThis.FormData=class{
  constructor(form){this.values=form.values}
  [Symbol.iterator](){return this.values[Symbol.iterator]()}
 };
 globalThis.fetch=async url=>{
  calls.push(url);
  if(url.endsWith('/bootstrap'))return response(db);
  if(url.endsWith('/auth/login'))return response({token:'token-de-prueba',user:{correo:'admin@test.uy',rol:'administrador'}});
  return reportFetch(url);
 };
 const url=new URL('../js/app.js',import.meta.url);url.searchParams.set('regression',++instance);
 await import(url.href);
 await settle();
 return {
  db,app,body,calls,get modal(){return modal},
  async click(action,id=''){
   const target={dataset:{action,id},classList:{contains:()=>false}};
   await handlers.click[0]({target:{closest:selector=>selector==='[data-action]'?target:null},preventDefault(){}});
   await settle();
  },
  async login(){
   const button={disabled:false};
   await handlers.submit[0]({preventDefault(){},target:{id:'login-form',values:[['correo','admin@test.uy'],['contrasena','clave-de-prueba']],querySelector:()=>button}});
   await settle();
  },
  restore(){for(const [key,value] of Object.entries(originals)){if(value===undefined)delete globalThis[key];else globalThis[key]=value}},
 };
}

test('editar una cancha abierta conserva No cuando MySQL devuelve techada=0',async()=>{
 const ui=await start();
 try{
  const court=ui.db.cancha.find(c=>!c.techada);court.techada=0;
  await ui.click('edit-cancha',`${court.id_complejo}|${court.nombre_cancha}`);
  const select=ui.modal.match(/<select name="techada"[^>]*>.*?<\/select>/s)?.[0];
  assert.match(select,/<option value="false" selected>No<\/option>/);
 }finally{ui.restore()}
});

test('una respuesta atrasada no reemplaza el reporte seleccionado',async()=>{
 const pending=[];
 const ui=await start({hash:'#reportes',reportFetch:url=>new Promise(resolve=>pending.push({url,resolve}))});
 try{
  assert.equal(pending.length,1);
  await ui.click('report','goleadores');
  assert.equal(pending.length,2);
  pending[1].resolve(response([{nombre_completo:'GOLEADOR_ACTUAL',equipo:'Actual',goles:8,posicion:1}]));
  await settle();
  assert.match(ui.body.innerHTML,/GOLEADOR_ACTUAL/);
  pending[0].resolve(response([{nombre_completo:'FILA_ANTIGUA',equipo:'Anterior',puntos:20}]));
  await settle();
  assert.match(ui.body.innerHTML,/GOLEADOR_ACTUAL/);
  assert.doesNotMatch(ui.body.innerHTML,/FILA_ANTIGUA/);
 }finally{ui.restore()}
});

test('una solicitud anterior no oculta la carga del reporte actual',async()=>{
 const pending=[];
 const ui=await start({hash:'#reportes',reportFetch:url=>new Promise(resolve=>pending.push({url,resolve}))});
 try{
  await ui.click('report','goleadores');
  pending[0].resolve(response([]));
  await settle();
  assert.match(ui.body.innerHTML,/Consultando datos/);
  pending[1].resolve(response([]));
  await settle();
  assert.doesNotMatch(ui.body.innerHTML,/Consultando datos/);
 }finally{ui.restore()}
});

test('iniciar sesión desde #reportes consulta inmediatamente el reporte',async()=>{
 const ui=await start({signedIn:false,hash:'#reportes'});
 try{
  await ui.login();
  assert.ok(ui.calls.some(url=>url.endsWith('/reportes/posiciones?id_torneo=1')));
 }finally{ui.restore()}
});
