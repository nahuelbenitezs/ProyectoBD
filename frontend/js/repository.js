import {API_BASE_URL, DEMO_STORAGE_KEY,MODE_STORAGE_KEY,TOKEN_STORAGE_KEY,USER_STORAGE_KEY} from './config.js';
import {nextId} from './utils.js';
import {generateReport,goalResult,isSuspended,sanctionsFor} from './reports.js';
import {assertValid} from './validation.js';

export const isDemo = () => localStorage.getItem(MODE_STORAGE_KEY)!=='api';
export const setMode = (mode) => {localStorage.setItem(MODE_STORAGE_KEY,mode==='api'?'api':'demo');sessionStorage.removeItem(TOKEN_STORAGE_KEY);sessionStorage.removeItem(USER_STORAGE_KEY)};
export const getSavedUser = () => {
 // No mostrar la interfaz de una sesión anterior si ya no hay token.
 if(!sessionStorage.getItem(TOKEN_STORAGE_KEY))return null;
 try{
  const user=JSON.parse(sessionStorage.getItem(USER_STORAGE_KEY)||'null');
  return user?.correo && ['administrador','planillero'].includes(user.rol)?user:null;
 }catch{return null}
};
export const demoUser = (role='administrador') => ({correo:role==='administrador'?'admin@demo.ucu.edu.uy':'planillero@demo.ucu.edu.uy',rol:role});
export const demoReset = () => localStorage.removeItem(DEMO_STORAGE_KEY);
const fail = (msg) => {throw Error(msg)};

async function request(path,{method='GET',body}={}) {
 const token=sessionStorage.getItem(TOKEN_STORAGE_KEY);
 let res;
 try {res=await fetch(`${API_BASE_URL}${path}`,{method,headers:{'Accept':'application/json',...(body!==undefined?{'Content-Type':'application/json'}:{}),...(token?{'Authorization':`Bearer ${token}`}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{})})}
 catch {throw Error('No se pudo conectar con el backend. Revisá que la API Python esté levantada y que CORS esté configurado.');}
 if(res.status===401){
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  sessionStorage.removeItem(USER_STORAGE_KEY);
  if(typeof window!=='undefined' && typeof Event!=='undefined')window.dispatchEvent(new Event('ucu:session-expired'));
  throw Error('Sesión vencida. Volvé a iniciar sesión.');
 }
 let data=null;try{data=await res.json()}catch{}
 if(!res.ok)throw Error(data?.error||data?.message||`La API respondió ${res.status}`);
 return data;
}
export async function login(correo,contrasena){
 const data=await request('/auth/login',{method:'POST',body:{correo,contrasena}});
 if(!data?.token||!['administrador','planillero'].includes(data?.user?.rol))fail('La API no devolvió token y rol válidos.');
 sessionStorage.setItem(TOKEN_STORAGE_KEY,data.token);sessionStorage.setItem(USER_STORAGE_KEY,JSON.stringify(data.user));return data.user;
}
export function logout(){sessionStorage.removeItem(TOKEN_STORAGE_KEY);sessionStorage.removeItem(USER_STORAGE_KEY)}
export async function loadData(){
 if(!isDemo()){
  const data=await request('/bootstrap');
  const keys=['facultad','torneo','jugador','equipo','equipo_jugador_torneo','complejo','cancha','turno','partido','planilla_partido','gol','tarjeta','sancion_jugador'];
  for(const k of keys)if(!Array.isArray(data?.[k]))fail(`El backend no devolvió el arreglo requerido «${k}». Consultá el contrato de integración acordado con el backend.`);
  return data;
 }
 const raw=localStorage.getItem(DEMO_STORAGE_KEY);
 if(raw){try{return JSON.parse(raw)}catch{localStorage.removeItem(DEMO_STORAGE_KEY)}}
 const resp=await fetch('./js/seed.json');if(!resp.ok)fail('No se pudo cargar seed.json: usá un servidor local, no abras el HTML con file://.');
 const data=await resp.json();localStorage.setItem(DEMO_STORAGE_KEY,JSON.stringify(data));return data;
}
export async function loadReport(slug,tournament,db){
 if(isDemo())return generateReport(db,slug,tournament);
 const data=await request(`/reportes/${slug}?id_torneo=${encodeURIComponent(tournament)}`);
 return Array.isArray(data)?data:(Array.isArray(data?.items)?data.items:fail('El reporte debe devolver un arreglo JSON o { items: [...] }.'));
}
export async function mutate(db,kind,action,payload={}){
 assertValid(db,kind,action,payload);
 if(!isDemo()){
  const endpoint={jugador:'jugadores',equipo:'equipos',torneo:'torneos',complejo:'complejos',cancha:'canchas',partido:'partidos',sancion_jugador:'sanciones'};
  const method=action==='create'?'POST':(['update','goal-update','card-update','roster-update'].includes(action)?'PATCH':action==='remove'?'DELETE':'POST');
  let path='',body=payload;
  if(['roster-add','roster-remove','roster-update'].includes(action)){path=`/equipos/${payload.id_equipo}/plantel${action==='roster-remove'||action==='roster-update'?`/${payload.ci_jugador}`:''}`;}
  else if(action==='planilla-save'){path=`/partidos/${payload.id_partido}/planilla`;}
  else if(['goal-create','goal-delete','goal-update'].includes(action)){path=`/partidos/${payload.id_partido}/goles${action==='goal-delete'||action==='goal-update'?`/${payload.id_gol}`:''}`;}
  else if(['card-create','card-delete','card-update'].includes(action)){path=`/partidos/${payload.id_partido}/tarjetas${action==='card-delete'||action==='card-update'?`/${payload.id_tarjeta}`:''}`;}
  else if(kind==='cancha'){path=`/complejos/${payload.id_complejo}/canchas${action==='create'?'':`/${encodeURIComponent(payload.original_nombre_cancha||payload.nombre_cancha)}`}`;}
  else {const idKey={jugador:'ci',equipo:'id_equipo',torneo:'id_torneo',complejo:'id_complejo',partido:'id_partido',sancion_jugador:'id_sancion'}[kind];path=`/${endpoint[kind]}${action==='create'?'':`/${encodeURIComponent(payload[idKey])}`}`;}
  await request(path,{method:action==='planilla-save'?'PUT':['roster-remove','goal-delete','card-delete'].includes(action)?'DELETE':method,...(method==='DELETE'||['roster-remove','goal-delete','card-delete'].includes(action)?{}:{body})});
  return await loadData();
 }
 const next=structuredClone(db);
 demoMutation(next,kind,action,payload);
 localStorage.setItem(DEMO_STORAGE_KEY,JSON.stringify(next));
 return next;
}
function demoMutation(db,kind,action,p){
 const keys={jugador:'ci',equipo:'id_equipo',torneo:'id_torneo',complejo:'id_complejo',cancha:'nombre_cancha',partido:'id_partido',sancion_jugador:'id_sancion'};
 if(action==='roster-add'){
  const eq=db.equipo.find(x=>+x.id_equipo===+p.id_equipo);if(!eq)fail('No existe ese equipo.');
  const tor=db.torneo.find(t=>+t.id_torneo===+eq.id_torneo);if(tor?.estado!=='inscripción')fail('Solo podés modificar un plantel durante inscripción.');
  const j=db.jugador.find(x=>+x.ci===+p.ci_jugador);if(!j||+j.id_facultad!==+eq.id_facultad)fail('El jugador debe ser de la misma facultad.');
  const roster=db.equipo_jugador_torneo.filter(x=>+x.id_equipo===+eq.id_equipo&&+x.id_torneo===+eq.id_torneo);
  if(roster.length>=10)fail('El plantel no puede tener más de 10 jugadores.');
  if(db.equipo_jugador_torneo.some(x=>+x.ci_jugador===+p.ci_jugador&&+x.id_torneo===+eq.id_torneo))fail('El jugador ya pertenece a un equipo en esta edición.');
  if(roster.some(x=>+x.numero_camiseta===+p.numero_camiseta))fail('Ese número de camiseta ya está utilizado.');
  if(!Number.isInteger(+p.numero_camiseta)||+p.numero_camiseta<1||+p.numero_camiseta>99)fail('El número de camiseta debe ser de 1 a 99.');
  if(['docente','funcionario'].includes(j.tipo)&&roster.filter(x=>['docente','funcionario'].includes(db.jugador.find(j=>+j.ci===+x.ci_jugador)?.tipo)).length>=2)fail('Máximo dos docentes o funcionarios por plantel.');
  db.equipo_jugador_torneo.push({id_equipo:+eq.id_equipo,ci_jugador:+p.ci_jugador,id_torneo:+eq.id_torneo,numero_camiseta:+p.numero_camiseta});return;
 }
 if(action==='roster-update'){
  const eq=db.equipo.find(x=>+x.id_equipo===+p.id_equipo);const tor=db.torneo.find(t=>+t.id_torneo===+eq?.id_torneo);if(tor?.estado!=='inscripción')fail('El dorsal solo puede cambiarse durante inscripción.');
  const own=db.equipo_jugador_torneo.find(x=>+x.id_equipo===+p.id_equipo&&+x.ci_jugador===+p.ci_jugador);if(!own)fail('El jugador no pertenece al equipo.');
  if(!Number.isInteger(+p.numero_camiseta)||+p.numero_camiseta<1||+p.numero_camiseta>99)fail('Camiseta inválida.');
  if(db.equipo_jugador_torneo.some(x=>+x.id_equipo===+p.id_equipo&&+x.ci_jugador!==+p.ci_jugador&&+x.numero_camiseta===+p.numero_camiseta))fail('Este dorsal ya está utilizado.');
  own.numero_camiseta=+p.numero_camiseta;return;
 }
 if(action==='roster-remove'){
  const eq=db.equipo.find(x=>+x.id_equipo===+p.id_equipo);const tor=db.torneo.find(t=>+t.id_torneo===+eq?.id_torneo);
  if(tor?.estado!=='inscripción')fail('No se puede quitar jugadores fuera de inscripción.');
  if(+eq.ci_capitan===+p.ci_jugador)fail('Primero asigná otro capitán.');
  const roster=db.equipo_jugador_torneo.filter(x=>+x.id_equipo===+eq.id_equipo);
  if(roster.length<=5&&db.partido.some(x=>x.estado!=='cancelado'&&(+x.id_equipo_local===+eq.id_equipo||+x.id_equipo_visitante===+eq.id_equipo)))fail('El equipo debe conservar al menos cinco jugadores si tiene partidos.');
  db.equipo_jugador_torneo=db.equipo_jugador_torneo.filter(x=>!(+x.id_equipo===+p.id_equipo&&+x.ci_jugador===+p.ci_jugador));return;
 }
 if(action==='planilla-save'){
  const match=db.partido.find(x=>+x.id_partido===+p.id_partido);validateEditable(db,match);
  const uniques=new Set();for(const x of p.participantes){
   if(uniques.has(+x.ci_jugador))fail('Un jugador no puede figurar dos veces en la planilla.');uniques.add(+x.ci_jugador);
   if(![+match.id_equipo_local,+match.id_equipo_visitante].includes(+x.id_equipo))fail('El jugador no pertenece a estos equipos.');
   if(!db.equipo_jugador_torneo.some(r=>+r.ci_jugador===+x.ci_jugador&&+r.id_equipo===+x.id_equipo&&+r.id_torneo===+match.id_torneo))fail('Solo pueden participar jugadores inscritos en los planteles.');
   if(isSuspended(db,match.id_torneo,x.ci_jugador,match.numero_fecha))fail('Hay un jugador suspendido para esta fecha.');
  }
  if(db.gol.some(g=>+g.id_partido===+match.id_partido&&!uniques.has(+g.ci_jugador))||db.tarjeta.some(t=>+t.id_partido===+match.id_partido&&!uniques.has(+t.ci_jugador)))fail('No se puede quitar un jugador con goles o tarjetas.');
  db.planilla_partido=db.planilla_partido.filter(x=>+x.id_partido!==+p.id_partido).concat(p.participantes.map(x=>({id_partido:+p.id_partido,ci_jugador:+x.ci_jugador,id_equipo:+x.id_equipo})));return;
 }
 if(['goal-create','goal-delete','goal-update','card-create','card-delete','card-update'].includes(action)){
  const match=db.partido.find(x=>+x.id_partido===+p.id_partido);validateEditable(db,match);
  const resource=action.startsWith('goal')?'gol':'tarjeta';const key=resource==='gol'?'id_gol':'id_tarjeta';
  if(action.endsWith('delete')) {db[resource]=db[resource].filter(x=>+x[key]!==+p[key]);return;}
  if(!db.planilla_partido.some(x=>+x.id_partido===+p.id_partido&&+x.ci_jugador===+p.ci_jugador))fail('El jugador debe figurar en la planilla.');
  if(!Number.isInteger(+p.minuto)||p.minuto<0||p.minuto>60)fail('El minuto debe ser de 0 a 60.');
  if(resource==='tarjeta'&&!['amarilla','roja'].includes(p.color))fail('El color de tarjeta no es válido.');
  if(action.endsWith('update')) {const row=db[resource].find(x=>+x[key]===+p[key]&&+x.id_partido===+p.id_partido);if(!row)fail('Registro no encontrado.');Object.assign(row,p,{minuto:+p.minuto,ci_jugador:+p.ci_jugador});return;}
  db[resource].push({...p,[key]:nextId(db[resource],key),id_partido:+p.id_partido,ci_jugador:+p.ci_jugador,minuto:+p.minuto});return;
 }
 if(!db[kind]||!keys[kind])fail('Operación no disponible.');
 const key=keys[kind];const id=kind==='cancha'?p.original_nombre_cancha||p.nombre_cancha:p[key];
 const idx=db[kind].findIndex(row=>String(row[key])===String(id)&&(kind!=='cancha'||+row.id_complejo===+p.id_complejo));
 if(action==='create'){
  if(kind==='jugador'){
   if(!/^[1-9]\d{5,9}$/.test(String(p.ci)))fail('Ingresá una cédula numérica válida (6 a 10 dígitos).');
   if(db.jugador.some(x=>+x.ci===+p.ci))fail('Ya existe un jugador con esa cédula.');
   if(!db.facultad.some(x=>+x.id_facultad===+p.id_facultad))fail('Seleccioná una facultad válida.');
   if(db.jugador.some(x=>x.email.toLowerCase()===p.email.toLowerCase()))fail('El correo ya está registrado.');
  }
  if(kind==='equipo'){
   const t=db.torneo.find(t=>+t.id_torneo===+p.id_torneo);if(t?.estado!=='inscripción')fail('Solo podés crear equipos durante inscripción.');
   if(!db.jugador.some(j=>+j.ci===+p.ci_capitan&&+j.id_facultad===+p.id_facultad))fail('El capitán debe pertenecer a la facultad.');
   if(db.equipo.some(e=>+e.id_torneo===+p.id_torneo&&e.nombre.toLowerCase()===p.nombre.toLowerCase()))fail('Ya existe un equipo con ese nombre en la edición.');
  }
  if(kind==='torneo'){
   if(db.torneo.some(t=>+t.anio===+p.anio&&+t.semestre===+p.semestre))fail('Ya existe una edición con ese año y semestre.');
   if(p.fecha_fin<p.fecha_inicio)fail('La fecha de finalización no puede ser anterior al inicio.');
   p.estado='inscripción';
  }
  if(kind==='partido')validateMatch(db,p);
  if(kind==='sancion_jugador')validateSanction(db,p);
  if(kind==='cancha'&&!db.complejo.some(x=>+x.id_complejo===+p.id_complejo))fail('Complejo inexistente.');
  if(kind==='cancha'&&db.cancha.some(x=>+x.id_complejo===+p.id_complejo&&x.nombre_cancha===p.nombre_cancha))fail('Ya existe una cancha con ese nombre en el complejo.');
  const data={...p};if(kind!=='jugador'&&kind!=='cancha')data[key]=nextId(db[kind],key);
  if(kind==='sancion_jugador'){data.motivo='disciplinaria';data.origen='manual'}
  db[kind].push(data);
  if(kind==='equipo')db.equipo_jugador_torneo.push({id_equipo:data.id_equipo,id_torneo:+data.id_torneo,ci_jugador:+data.ci_capitan,numero_camiseta:1});
  return;
 }
 if(idx<0)fail('El registro ya no existe.');
 const old=db[kind][idx];
 if(action==='update'){
  if(kind==='partido'){if(old.estado==='jugado')fail('No se puede modificar un partido jugado.');validateMatch(db,p,old.id_partido)}
  if(kind==='equipo'){
   if(+p.id_facultad!==+old.id_facultad||+p.id_torneo!==+old.id_torneo)fail('No se puede cambiar el torneo o la facultad de un equipo.');
   if(!db.equipo_jugador_torneo.some(r=>+r.id_equipo===+old.id_equipo&&+r.ci_jugador===+p.ci_capitan))fail('El capitán debe integrar el plantel.');
  }
  if(kind==='jugador'){
   if(db.jugador.some(j=>+j.ci!==+old.ci&&j.email.toLowerCase()===p.email.toLowerCase()))fail('Ya existe ese correo.');
   if((+old.id_facultad!==+p.id_facultad||old.tipo!==p.tipo)&&db.equipo_jugador_torneo.some(x=>+x.ci_jugador===+old.ci))fail('No se puede modificar facultad o tipo si pertenece a un plantel.');
  }
  if(kind==='torneo'){
   if(old.estado==='finalizado'&&p.estado!=='finalizado'||old.estado==='en curso'&&p.estado==='inscripción')fail('No se permite volver a un estado anterior.');
   if(old.estado==='inscripción'&&p.estado!=='inscripción'&&db.equipo.filter(e=>+e.id_torneo===+p.id_torneo).some(e=>db.equipo_jugador_torneo.filter(r=>+r.id_equipo===+e.id_equipo).length<5))fail('Antes de iniciar, todos los equipos deben tener al menos 5 jugadores.');
  }
  if(kind==='sancion_jugador'){if(old.origen!=='manual')fail('Las sanciones automáticas no se editan.');validateSanction(db,p,old.id_sancion);}
  if(kind==='cancha'&&p.nombre_cancha!==old.nombre_cancha)fail('No se puede renombrar una cancha con clave compuesta en esta operación.');
  db[kind][idx]={...old,...p,[key]:old[key]};return;
 }
 if(action==='remove'){
  if(kind==='partido'&&old.estado==='jugado')fail('No se puede eliminar un partido jugado.');
  if(kind==='jugador'&&(db.equipo_jugador_torneo.some(r=>+r.ci_jugador===+old.ci)||db.planilla_partido.some(r=>+r.ci_jugador===+old.ci)))fail('No se puede eliminar: el jugador tiene referencias en el torneo.');
  if(kind==='equipo'&&(db.partido.some(m=>+m.id_equipo_local===+old.id_equipo||+m.id_equipo_visitante===+old.id_equipo)||db.equipo_jugador_torneo.some(r=>+r.id_equipo===+old.id_equipo)))fail('No se puede eliminar: primero debe quitarse el plantel y los partidos asociados.');
  if(kind==='complejo'&&db.cancha.some(c=>+c.id_complejo===+old.id_complejo))fail('El complejo todavía tiene canchas asociadas.');
  if(kind==='cancha'&&db.partido.some(m=>m.nombre_cancha===old.nombre_cancha&&+m.id_complejo===+old.id_complejo))fail('La cancha se usa en partidos registrados.');
  if(kind==='torneo'&&db.equipo.some(e=>+e.id_torneo===+old.id_torneo))fail('La edición tiene equipos asociados.');
  if(kind==='sancion_jugador'&&old.origen!=='manual')fail('Las sanciones automáticas no se eliminan.');
  db[kind].splice(idx,1);return;
 }
 fail('Operación no reconocida.');
}
function validateEditable(db,m){
 if(!m||m.estado!=='jugado')fail('Solo podés registrar información de partidos jugados.');
 const turn=db.turno.find(t=>+t.id_turno===+m.id_turno);const end=new Date(`${m.dia}T${turn?.hora_fin||'23:00'}`);const now=new Date();
 if(now<end)fail('El turno del partido todavía no terminó.');
 if(now.getTime()-end.getTime()>48*3600e3)fail('Ya vencieron las 48 horas para corregir la planilla.');
}
function validateMatch(db,p,exclude=null){
 const t=db.torneo.find(t=>+t.id_torneo===+p.id_torneo);if(!t||t.estado==='finalizado')fail('No se pueden programar partidos en esa edición.');
 if(p.dia<t.fecha_inicio||p.dia>t.fecha_fin)fail('La fecha del partido debe estar dentro del torneo.');
 if(+p.id_equipo_local===+p.id_equipo_visitante)fail('Un equipo no puede jugar contra sí mismo.');
 for(const id of [p.id_equipo_local,p.id_equipo_visitante]){
  if(!db.equipo.some(e=>+e.id_equipo===+id&&+e.id_torneo===+p.id_torneo))fail('Ambos equipos deben pertenecer a la edición.');
  if(p.estado!=='cancelado'&&db.equipo_jugador_torneo.filter(r=>+r.id_equipo===+id&&+r.id_torneo===+p.id_torneo).length<5)fail('Ambos equipos deben tener por lo menos 5 jugadores.');
 }
 if(p.estado==='jugado'){
  const turn=db.turno.find(t=>+t.id_turno===+p.id_turno);if(new Date()<=new Date(`${p.dia}T${turn?.hora_fin||'23:00'}`))fail('Un partido solo puede marcarse jugado después del turno.');
 }
 for(const m of db.partido.filter(x=>+x.id_torneo===+p.id_torneo&&+x.id_partido!==+exclude)){
  const teams=[+p.id_equipo_local,+p.id_equipo_visitante],others=[+m.id_equipo_local,+m.id_equipo_visitante];
  if(p.estado!=='cancelado'&&m.estado!=='cancelado'){
   if(teams.every(x=>others.includes(x)))fail('Estos equipos ya tienen un enfrentamiento en la edición.');
   if(+m.numero_fecha===+p.numero_fecha&&teams.some(x=>others.includes(x)))fail('Un equipo no puede jugar dos partidos en la misma fecha.');
  }
  if(!['cancelado','postergado'].includes(p.estado)&&!['cancelado','postergado'].includes(m.estado)&&m.dia===p.dia&&+m.id_turno===+p.id_turno&&+m.id_complejo===+p.id_complejo&&m.nombre_cancha===p.nombre_cancha)fail('Esta cancha ya tiene un partido en ese día y turno.');
 }
}
function validateSanction(db,p,exclude=null){
 if(!db.equipo_jugador_torneo.some(r=>+r.ci_jugador===+p.ci_jugador&&+r.id_torneo===+p.id_torneo))fail('Solo se puede sancionar a jugadores inscriptos en la edición.');
 if(+p.numero_fecha_inicio<1||+p.cantidad_fechas<1)fail('Las fechas de sanción deben ser mayores que cero.');
 if(db.planilla_partido.some(x=>+x.ci_jugador===+p.ci_jugador&&db.partido.some(m=>+m.id_partido===+x.id_partido&&+m.id_torneo===+p.id_torneo&&+m.numero_fecha>=+p.numero_fecha_inicio&&+m.numero_fecha<+p.numero_fecha_inicio + +p.cantidad_fechas)))fail('La sanción se superpone con una planilla existente.');
 if(db.sancion_jugador.some(x=>+x.id_sancion!==+exclude&&+x.ci_jugador===+p.ci_jugador&&+x.id_torneo===+p.id_torneo&&+x.numero_fecha_inicio===+p.numero_fecha_inicio))fail('Ya hay una sanción de ese jugador desde la misma fecha.');
}
