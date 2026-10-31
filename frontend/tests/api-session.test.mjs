import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  isDemo, setMode, getSavedUser, login, logout, loadData,
} from '../js/repository.js';
import {API_BASE_URL,TOKEN_STORAGE_KEY,USER_STORAGE_KEY} from '../js/config.js';

function fakeStorage(){
  const values=new Map();
  return {
    getItem:key=>values.has(key)?values.get(key):null,
    setItem:(key,value)=>values.set(key,String(value)),
    removeItem:key=>values.delete(key),
    clear:()=>values.clear(),
  };
}
function jsonResponse(data,status=200){
  return {ok:status>=200&&status<300,status,async json(){return data}};
}
const seed=JSON.parse(fs.readFileSync(new URL('../js/seed.json',import.meta.url),'utf8'));
const original={localStorage:globalThis.localStorage,sessionStorage:globalThis.sessionStorage,fetch:globalThis.fetch,window:globalThis.window};
function prepare(){
  globalThis.localStorage=fakeStorage();
  globalThis.sessionStorage=fakeStorage();
  globalThis.window={events:[],dispatchEvent(event){this.events.push(event.type)}};
  setMode('api');
}
function restore(){for(const [key,value] of Object.entries(original)){if(value===undefined)delete globalThis[key];else globalThis[key]=value}}

test('modo API no utiliza los datos de demostración ni crea una sesión',()=>{
  prepare();
  try{assert.equal(isDemo(),false);assert.equal(getSavedUser(),null)}finally{restore()}
});

test('usuario guardado sin token no mantiene una sesión aparente',()=>{
  prepare();
  try{
    sessionStorage.setItem(USER_STORAGE_KEY,JSON.stringify({correo:'admin@test.uy',rol:'administrador'}));
    assert.equal(getSavedUser(),null);
  }finally{restore()}
});

test('iniciar sesión envía credenciales y guarda token y rol válidos',async()=>{
  prepare();
  try{
    let sent;
    globalThis.fetch=async(url,options)=>{sent={url,options};return jsonResponse({token:'token-temporal',user:{correo:'admin@test.uy',rol:'administrador'}})};
    const user=await login('admin@test.uy','contraseña-de-prueba');
    assert.equal(user.rol,'administrador');
    assert.equal(sent.url,`${API_BASE_URL}/auth/login`);
    assert.equal(sent.options.method,'POST');
    assert.deepEqual(JSON.parse(sent.options.body),{correo:'admin@test.uy',contrasena:'contraseña-de-prueba'});
    assert.equal(sessionStorage.getItem(TOKEN_STORAGE_KEY),'token-temporal');
    assert.deepEqual(getSavedUser(),user);
  }finally{restore()}
});

test('rechaza autenticaciones sin token o sin un rol reconocido',async()=>{
  prepare();
  try{
    globalThis.fetch=async()=>jsonResponse({token:'token',user:{correo:'x@test.uy',rol:'invitado'}});
    await assert.rejects(login('x@test.uy','clave'),/token y rol válidos/);
    assert.equal(getSavedUser(),null);
  }finally{restore()}
});

test('carga /bootstrap usando Bearer y exige los arreglos del contrato',async()=>{
  prepare();
  try{
    sessionStorage.setItem(TOKEN_STORAGE_KEY,'token-ok');
    let sent;
    globalThis.fetch=async(url,options)=>{sent={url,options};return jsonResponse(seed)};
    const db=await loadData();
    assert.equal(db.partido.length,13);
    assert.equal(sent.url,`${API_BASE_URL}/bootstrap`);
    assert.equal(sent.options.headers.Authorization,'Bearer token-ok');
  }finally{restore()}
});

test('reporta respuestas /bootstrap incompletas sin usar datos demo',async()=>{
  prepare();
  try{
    globalThis.fetch=async()=>jsonResponse({equipo:[]});
    await assert.rejects(loadData(),/arreglo requerido/);
  }finally{restore()}
});

test('un 401 borra credenciales y emite aviso de sesión expirada',async()=>{
  prepare();
  try{
    sessionStorage.setItem(TOKEN_STORAGE_KEY,'token-vencido');
    sessionStorage.setItem(USER_STORAGE_KEY,JSON.stringify({correo:'test@ucu.uy',rol:'administrador'}));
    globalThis.fetch=async()=>jsonResponse({error:'No autorizado'},401);
    await assert.rejects(loadData(),/Sesión vencida/);
    assert.equal(getSavedUser(),null);
    assert.equal(sessionStorage.getItem(TOKEN_STORAGE_KEY),null);
    assert.deepEqual(window.events,['ucu:session-expired']);
  }finally{restore()}
});

test('un 403 muestra el mensaje del backend pero no borra una sesión válida',async()=>{
  prepare();
  try{
    sessionStorage.setItem(TOKEN_STORAGE_KEY,'token-ok');
    globalThis.fetch=async()=>jsonResponse({error:'No tenés permisos para esta operación'},403);
    await assert.rejects(loadData(),/No tenés permisos/);
    assert.equal(sessionStorage.getItem(TOKEN_STORAGE_KEY),'token-ok');
  }finally{restore()}
});

test('ante fallo de red informa cómo solucionar la conexión',async()=>{
  prepare();
  try{
    globalThis.fetch=async()=>{throw new Error('ECONNREFUSED')};
    await assert.rejects(loadData(),/No se pudo conectar con el backend/);
  }finally{restore()}
});

test('cerrar sesión elimina los datos sensibles guardados',()=>{
  prepare();
  try{
    sessionStorage.setItem(TOKEN_STORAGE_KEY,'token-ok');
    sessionStorage.setItem(USER_STORAGE_KEY,'{}');
    logout();
    assert.equal(sessionStorage.getItem(TOKEN_STORAGE_KEY),null);
    assert.equal(sessionStorage.getItem(USER_STORAGE_KEY),null);
  }finally{restore()}
});

test('la interfaz API muestra login sin requerir primero /bootstrap',async()=>{
  prepare();
  const oldDocument=globalThis.document;
  try{
    const app={innerHTML:'',addEventListener(){}};
    globalThis.document={getElementById:id=>id==='app'?app:null,documentElement:{dataset:{}}};
    window.location={hash:''};
    window.addEventListener=()=>{};
    await import('../js/app.js');
    assert.match(app.innerHTML,/id="login-form"/);
    assert.match(app.innerHTML,/CONEXIÓN CON API PYTHON/);
    assert.doesNotMatch(app.innerHTML,/Preparando el tablero/);
  }finally{
    if(oldDocument===undefined)delete globalThis.document;else globalThis.document=oldDocument;
    restore();
  }
});


test('login incorrecto muestra el error del backend y no dispara sesión vencida',async()=>{
  prepare();
  try{
    globalThis.fetch=async()=>jsonResponse({error:'Correo o contraseña incorrectos.'},401);
    await assert.rejects(login('x@test.uy','clave-erronea'),/Correo o contraseña incorrectos/);
    assert.deepEqual(window.events,[]);
  }finally{restore()}
});

test('logout en modo API revoca el token con Bearer y limpia la sesión local',async()=>{
  prepare();
  try{
    sessionStorage.setItem(TOKEN_STORAGE_KEY,'token-ok');
    sessionStorage.setItem(USER_STORAGE_KEY,JSON.stringify({correo:'x@test.uy',rol:'administrador'}));
    let sent;
    globalThis.fetch=async(url,options)=>{sent={url,options};return jsonResponse({ok:true})};
    logout();
    assert.equal(sessionStorage.getItem(TOKEN_STORAGE_KEY),null);
    assert.equal(sent.url,`${API_BASE_URL}/auth/logout`);
    assert.equal(sent.options.headers.Authorization,'Bearer token-ok');
    assert.equal(sent.options.method,'POST');
  }finally{restore()}
});
