/**
 * Validaciones de entrada para la interfaz del Torneo Interfacultades.
 * No reemplazan la autorización, los triggers ni las validaciones del backend.
 * Función pura para reutilizarla en modo demostración y en modo API.
 */
const text = value => String(value ?? '').trim();
const num = value => Number(value);
const positiveInt = value => text(value) !== '' && Number.isSafeInteger(num(value)) && num(value) > 0;
const isDate = value => {
  const s=text(value);
  if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;
  const d=new Date(`${s}T12:00:00Z`);
  return !Number.isNaN(d.valueOf()) && d.toISOString().slice(0,10)===s;
};
const inRange = (value,min,max) => text(value)!=='' && Number.isInteger(num(value)) && num(value)>=min && num(value)<=max;
const same = (a,b) => String(a)===String(b);
const personTypes=['grado','posgrado','docente','funcionario'];
const matchStates=['programado','jugado','postergado','cancelado'];
const tourStates=['inscripción','en curso','finalizado'];
const oneOf = (value,allowed) => allowed.includes(value);
const matchesId = (obj,key,value) => same(obj?.[key],value);
const teamOf = (db,id) => db.equipo.find(x=>matchesId(x,'id_equipo',id));
const editionOf = (db,id) => db.torneo.find(x=>matchesId(x,'id_torneo',id));
const matchOf = (db,id) => db.partido.find(x=>matchesId(x,'id_partido',id));
const enrollment = (db,id,edition) => db.equipo_jugador_torneo.filter(x=>same(x.id_equipo,id)&&same(x.id_torneo,edition));
const displayedName = x => text(x).replace(/\s+/g,' ');
const eventEnd = (db,m) => {
  const turn=db.turno.find(t=>same(t.id_turno,m?.id_turno));
  if(!m||!turn||!isDate(m.dia))return null;
  const value = new Date(`${m.dia}T${String(turn.hora_fin).slice(0,8)}`);
  return Number.isNaN(value.valueOf())?null:value;
};
function sanctionCovers(s,torneo,ci,fecha){
  return same(s.id_torneo,torneo)&&same(s.ci_jugador,ci)&&num(fecha)>=num(s.numero_fecha_inicio)&&num(fecha)<num(s.numero_fecha_inicio)+num(s.cantidad_fechas);
}
function suspended(db,match,ci){
  const sanctions=db.sancion_jugador||[];
  if(sanctions.some(s=>sanctionCovers(s,match.id_torneo,ci,match.numero_fecha)))return true;
  // Sanciones automáticas derivadas de las tarjetas de partidos jugados.
  const cards=(db.tarjeta||[]).filter(t=>same(t.ci_jugador,ci)).map(c=>({
    ...c, match:matchOf(db,c.id_partido)
  })).filter(c=>c.match?.estado==='jugado'&&same(c.match?.id_torneo,match.id_torneo))
    .sort((a,b)=>num(a.match.numero_fecha)-num(b.match.numero_fecha)||a.match.dia.localeCompare(b.match.dia)||num(a.minuto)-num(b.minuto)||num(a.id_tarjeta)-num(b.id_tarjeta));
  let yellows=0;
  for(const card of cards){
    if(card.color==='amarilla')yellows++;
    if(card.color==='roja'||(card.color==='amarilla'&&yellows%3===0)){
      if(num(match.numero_fecha)===num(card.match.numero_fecha)+1)return true;
    }
  }
  return false;
}
/** Returns [{field, message}], never mutates the payload or bootstrap data. */
export function validateCommand(db,kind,action,p,now=new Date()){
  const issues=[];
  const add=(field,message)=>{if(!issues.some(x=>x.field===field&&x.message===message))issues.push({field,message})};
  const required=(field,label,max=100)=>{
    if(!displayedName(p[field]))add(field,`Ingresá ${label}.`);
    else if(displayedName(p[field]).length>max)add(field,`${label} admite hasta ${max} caracteres.`);
  };
  const validRef=(list,key,id,field,msg)=>{if(!list.some(x=>matchesId(x,key,id)))add(field,msg)};
  const editableMatch=(id)=>{
    const m=matchOf(db,id);
    if(!m){add('id_partido','No existe ese partido.');return null;}
    const end=eventEnd(db,m);
    if(m.estado!=='jugado')add('id_partido','La planilla solo se edita para un partido jugado.');
    else if(!end)add('id_partido','El turno del partido no es válido.');
    else if(now.getTime()<end.getTime())add('id_partido','El turno todavía no finalizó.');
    else if(now.getTime()-end.getTime()>48*60*60*1000)add('id_partido','Pasaron más de 48 horas desde el partido.');
    return m;
  };
  if(!db||!p||typeof p!=='object')return [{field:'',message:'No hay datos para validar la operación.'}];

  if(['goal-create','goal-update','goal-delete','card-create','card-update','card-delete','planilla-save'].includes(action)){
    const match=editableMatch(p.id_partido);
    if(action==='planilla-save'){
      if(!Array.isArray(p.participantes))add('participant','Seleccioná participantes válidos.');
      else if(match){
        const seen=new Set();
        for(const r of p.participantes){
          const ci=String(r.ci_jugador),id=String(r.id_equipo);
          if(seen.has(ci))add('participant','El mismo jugador no puede figurar dos veces.');
          seen.add(ci);
          if(![String(match.id_equipo_local),String(match.id_equipo_visitante)].includes(id))add('participant','Hay participantes de un equipo ajeno al partido.');
          if(!enrollment(db,id,match.id_torneo).some(x=>same(x.ci_jugador,ci)))add('participant','Hay jugadores que no integran el plantel correspondiente.');
          if(suspended(db,match,ci))add('participant','Hay jugadores suspendidos para esta fecha.');
        }
        if(db.gol.some(g=>same(g.id_partido,match.id_partido)&&!seen.has(String(g.ci_jugador)))||db.tarjeta.some(t=>same(t.id_partido,match.id_partido)&&!seen.has(String(t.ci_jugador))))add('participant','No se puede retirar un jugador que tiene goles o tarjetas.');
      }
    }else if(!action.endsWith('delete')){
      if(!inRange(p.minuto,0,60))add('minuto','El minuto debe estar entre 0 y 60.');
      if(match&&!db.planilla_partido.some(x=>same(x.id_partido,p.id_partido)&&same(x.ci_jugador,p.ci_jugador)))add('ci_jugador','Elegí un jugador incluido en la planilla del partido.');
      if(action.startsWith('card')&&!oneOf(p.color,['amarilla','roja']))add('color','Elegí una tarjeta amarilla o roja.');
      if(action.startsWith('goal')&&typeof p.autogol!=='boolean')add('autogol','Indicá si fue un autogol.');
    }
    return issues;
  }
  if(['roster-add','roster-remove','roster-update'].includes(action)){
    const eq=teamOf(db,p.id_equipo),edition=eq&&editionOf(db,eq.id_torneo);
    if(!eq){add('id_equipo','El equipo seleccionado no existe.');return issues;}
    if(edition?.estado!=='inscripción')add('id_equipo','Los planteles solo pueden modificarse durante inscripción.');
    const roster=enrollment(db,eq.id_equipo,eq.id_torneo), j=db.jugador.find(x=>same(x.ci,p.ci_jugador));
    if(!j)add('ci_jugador','Elegí un jugador existente.');
    if(action==='roster-add'){
      if(j&&!same(j.id_facultad,eq.id_facultad))add('ci_jugador','El jugador debe pertenecer a la facultad del equipo.');
      if(db.equipo_jugador_torneo.some(x=>same(x.ci_jugador,p.ci_jugador)&&same(x.id_torneo,eq.id_torneo)))add('ci_jugador','El jugador ya está inscripto en un equipo de esta edición.');
      if(roster.length>=10)add('ci_jugador','El plantel no admite más de 10 jugadores.');
      if(j&&['docente','funcionario'].includes(j.tipo)&&roster.filter(r=>['docente','funcionario'].includes(db.jugador.find(x=>same(x.ci,r.ci_jugador))?.tipo)).length>=2)add('ci_jugador','Ya hay dos docentes o funcionarios en el equipo.');
    }else if(!roster.some(r=>same(r.ci_jugador,p.ci_jugador)))add('ci_jugador','El jugador no pertenece a este plantel.');
    if(action!=='roster-remove'){
      if(!inRange(p.numero_camiseta,1,99))add('numero_camiseta','La camiseta debe estar entre 1 y 99.');
      else if(roster.some(r=>same(r.numero_camiseta,p.numero_camiseta)&&(!same(r.ci_jugador,p.ci_jugador)||action==='roster-add')))add('numero_camiseta','Esa camiseta ya se usa en el equipo.');
    }else{
      if(same(eq.ci_capitan,p.ci_jugador))add('ci_jugador','Asigná otro capitán antes de eliminar este jugador.');
      if(roster.length<=5&&db.partido.some(m=>m.estado!=='cancelado'&&(same(m.id_equipo_local,eq.id_equipo)||same(m.id_equipo_visitante,eq.id_equipo))))add('ci_jugador','El equipo debe mantener 5 jugadores si tiene partidos.');
    }
    return issues;
  }
  if(action==='remove'){
    if(kind==='partido'&&matchOf(db,p.id_partido)?.estado==='jugado')add('','Un partido jugado no puede eliminarse.');
    if(kind==='sancion_jugador'&&db.sancion_jugador.find(x=>same(x.id_sancion,p.id_sancion))?.origen==='automatica')add('','No se pueden eliminar sanciones automáticas.');
    return issues;
  }

  if(kind==='jugador'){
    if(!/^\d{6,10}$/.test(text(p.ci))||!positiveInt(p.ci))add('ci','La cédula debe tener entre 6 y 10 dígitos.');
    required('nombre','un nombre');required('apellido','un apellido');
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text(p.email))||text(p.email).length>150)add('email','Ingresá un correo electrónico válido (máximo 150 caracteres).');
    if(!isDate(p.fecha_nacimiento)||new Date(`${p.fecha_nacimiento}T12:00:00Z`)>now)add('fecha_nacimiento','Ingresá una fecha de nacimiento válida y pasada.');
    validRef(db.facultad,'id_facultad',p.id_facultad,'id_facultad','Seleccioná una facultad válida.');
    if(!oneOf(p.tipo,personTypes))add('tipo','Seleccioná un tipo de jugador válido.');
    if(db.jugador.some(j=>same(j.ci,p.ci)&&action==='create'))add('ci','Ya existe un jugador con esa cédula.');
    if(db.jugador.some(j=>text(j.email).toLowerCase()===text(p.email).toLowerCase()&&!same(j.ci,p.ci)))add('email','Ese correo ya está registrado.');
    if(action==='update'){
      const old=db.jugador.find(j=>same(j.ci,p.ci));
      if(old&&(old.tipo!==p.tipo||!same(old.id_facultad,p.id_facultad))&&db.equipo_jugador_torneo.some(x=>same(x.ci_jugador,p.ci)))add('id_facultad','No se puede cambiar facultad o tipo de un jugador inscripto.');
    }
  }
  if(kind==='torneo'){
    required('nombre','el nombre de la edición',150);
    if(!inRange(p.anio,2000,2100))add('anio','Ingresá un año entre 2000 y 2100.');
    if(!oneOf(num(p.semestre),[1,2]))add('semestre','Elegí el semestre 1 o 2.');
    if(!isDate(p.fecha_inicio))add('fecha_inicio','Ingresá una fecha de inicio válida.');
    if(!isDate(p.fecha_fin)||isDate(p.fecha_inicio)&&p.fecha_fin<p.fecha_inicio)add('fecha_fin','La fecha de fin no puede ser anterior al inicio.');
    if(!oneOf(p.estado,tourStates))add('estado','El estado del torneo no es válido.');
    if(db.torneo.some(t=>same(t.anio,p.anio)&&same(t.semestre,p.semestre)&&(action==='create'||!same(t.id_torneo,p.id_torneo))))add('semestre','Ya existe un torneo para ese año y semestre.');
    const old=db.torneo.find(t=>same(t.id_torneo,p.id_torneo));
    if(action==='create'&&p.estado!=='inscripción')add('estado','Los torneos nuevos deben comenzar en inscripción.');
    if(action==='update'&&old){
      if(old.estado==='finalizado'&&old.estado!==p.estado||old.estado==='en curso'&&p.estado==='inscripción')add('estado','No se puede retroceder el estado del torneo.');
      if(old.estado==='inscripción'&&p.estado!=='inscripción'){
        const incomplete=db.equipo.filter(e=>same(e.id_torneo,old.id_torneo)).some(e=>{
          const list=enrollment(db,e.id_equipo,old.id_torneo);
          return list.length<5||list.length>10||!list.some(r=>same(r.ci_jugador,e.ci_capitan));
        });
        if(incomplete)add('estado','Todos los equipos deben tener entre 5 y 10 jugadores y capitán inscripto antes de iniciar.');
      }
    }
  }
  if(kind==='equipo'){
    required('nombre','el nombre del equipo');
    validRef(db.torneo,'id_torneo',p.id_torneo,'id_torneo','Seleccioná un torneo existente.');
    validRef(db.facultad,'id_facultad',p.id_facultad,'id_facultad','Seleccioná una facultad existente.');
    const captain=db.jugador.find(j=>same(j.ci,p.ci_capitan));
    if(!captain||!same(captain.id_facultad,p.id_facultad))add('ci_capitan','El capitán debe ser jugador de la facultad elegida.');
    if(db.equipo.some(e=>same(e.id_torneo,p.id_torneo)&&text(e.nombre).toLowerCase()===text(p.nombre).toLowerCase()&&(action==='create'||!same(e.id_equipo,p.id_equipo))))add('nombre','Ya existe un equipo con ese nombre en la edición.');
    const old=teamOf(db,p.id_equipo);
    if(action==='create'&&editionOf(db,p.id_torneo)?.estado!=='inscripción')add('id_torneo','Solo se crean equipos durante inscripción.');
    if(action==='update'&&old){
      if(!same(old.id_torneo,p.id_torneo)||!same(old.id_facultad,p.id_facultad))add('id_facultad','No se puede cambiar la edición o facultad de un equipo existente.');
      if(!enrollment(db,old.id_equipo,old.id_torneo).some(r=>same(r.ci_jugador,p.ci_capitan)))add('ci_capitan','El capitán nuevo debe formar parte del plantel.');
    }
  }
  if(kind==='complejo'){
    required('nombre','el nombre del complejo');required('direccion','la dirección',150);required('departamento','el departamento');
  }
  if(kind==='cancha'){
    required('nombre_cancha','el nombre de la cancha');
    validRef(db.complejo,'id_complejo',p.id_complejo,'id_complejo','Seleccioná un complejo existente.');
    if(!oneOf(p.superficie,['sintético','parquet']))add('superficie','La superficie debe ser sintético o parquet.');
    if(typeof p.techada!=='boolean')add('techada','Indicá si la cancha es techada.');
    if(action==='create'&&db.cancha.some(c=>same(c.id_complejo,p.id_complejo)&&text(c.nombre_cancha)===text(p.nombre_cancha)))add('nombre_cancha','Esta cancha ya existe en el complejo.');
  }
  if(kind==='partido'){
    const edition=editionOf(db,p.id_torneo),local=teamOf(db,p.id_equipo_local),away=teamOf(db,p.id_equipo_visitante);
    if(!edition||edition.estado==='finalizado')add('id_torneo','La edición debe existir y no estar finalizada.');
    if(!positiveInt(p.numero_fecha))add('numero_fecha','El número de fecha debe ser un entero positivo.');
    if(!isDate(p.dia))add('dia','Elegí un día válido.');
    else if(edition&&(p.dia<edition.fecha_inicio||p.dia>edition.fecha_fin))add('dia','El día debe estar dentro del período del torneo.');
    if(!local||!same(local.id_torneo,p.id_torneo))add('id_equipo_local','El local debe pertenecer a esta edición.');
    if(!away||!same(away.id_torneo,p.id_torneo))add('id_equipo_visitante','El visitante debe pertenecer a esta edición.');
    if(local&&away&&same(local.id_equipo,away.id_equipo))add('id_equipo_visitante','El equipo no puede jugar contra sí mismo.');
    validRef(db.turno,'id_turno',p.id_turno,'id_turno','Elegí un turno válido.');
    if(!db.cancha.some(c=>same(c.id_complejo,p.id_complejo)&&c.nombre_cancha===p.nombre_cancha))add('cancha_compuesta','Seleccioná una cancha existente.');
    if(!oneOf(p.estado,matchStates))add('estado','Elegí un estado válido.');
    const old=matchOf(db,p.id_partido);
    if(action==='update'&&old?.estado==='jugado')add('estado','No se puede modificar un partido jugado.');
    if(local&&away&&p.estado!=='cancelado'){
      for(const [team,field] of [[local,'id_equipo_local'],[away,'id_equipo_visitante']]){
        const list=enrollment(db,team.id_equipo,p.id_torneo);
        if(list.length<5)add(field,`${team.nombre} necesita al menos 5 jugadores.`);
        if(!list.some(r=>same(r.ci_jugador,team.ci_capitan)))add(field,`El capitán de ${team.nombre} no está en el plantel.`);
      }
    }
    if(p.estado==='jugado'&&isDate(p.dia)){
      const end=eventEnd(db,p);
      if(!end||now<=end)add('estado','Solo puede marcarse jugado después de finalizar el turno.');
    }
    if(local&&away){
      const nextTeams=[String(p.id_equipo_local),String(p.id_equipo_visitante)];
      for(const m of db.partido){
        if(action==='update'&&same(m.id_partido,p.id_partido))continue;
        if(!same(m.id_torneo,p.id_torneo))continue;
        const existing=[String(m.id_equipo_local),String(m.id_equipo_visitante)];
        if(p.estado!=='cancelado'&&m.estado!=='cancelado'){
          if(nextTeams.every(x=>existing.includes(x)))add('id_equipo_visitante','Estos equipos ya tienen un enfrentamiento en la edición.');
          if(same(m.numero_fecha,p.numero_fecha)&&nextTeams.some(x=>existing.includes(x)))add('numero_fecha','Un equipo no puede jugar dos veces en la misma fecha.');
        }
        if(!['postergado','cancelado'].includes(p.estado)&&!['postergado','cancelado'].includes(m.estado)&&same(m.dia,p.dia)&&same(m.id_turno,p.id_turno)&&same(m.id_complejo,p.id_complejo)&&m.nombre_cancha===p.nombre_cancha)add('cancha_compuesta','Esta cancha ya está reservada ese día y turno.');
      }
    }
  }
  if(kind==='sancion_jugador'){
    if(p.motivo!=='disciplinaria'||p.origen!=='manual')add('','Solo se ingresan manualmente sanciones disciplinarias.');
    if(!positiveInt(p.numero_fecha_inicio))add('numero_fecha_inicio','El inicio debe ser una fecha positiva.');
    if(!positiveInt(p.cantidad_fechas))add('cantidad_fechas','La duración debe ser de una fecha o más.');
    if(!db.equipo_jugador_torneo.some(r=>same(r.ci_jugador,p.ci_jugador)&&same(r.id_torneo,p.id_torneo)))add('ci_jugador','Solo se puede sancionar a jugadores inscriptos en esta edición.');
    if(positiveInt(p.numero_fecha_inicio)&&positiveInt(p.cantidad_fechas)){
      const conflict=db.planilla_partido.some(r=>same(r.ci_jugador,p.ci_jugador)&&db.partido.some(m=>same(m.id_partido,r.id_partido)&&same(m.id_torneo,p.id_torneo)&&num(m.numero_fecha)>=num(p.numero_fecha_inicio)&&num(m.numero_fecha)<num(p.numero_fecha_inicio)+num(p.cantidad_fechas)));
      if(conflict)add('numero_fecha_inicio','La sanción se superpone con una planilla ya registrada.');
    }
  }
  return issues;
}
export class ValidationError extends Error{
  constructor(issues){super(issues.map(x=>x.message).join(' '));this.name='ValidationError';this.issues=issues}
}
export function assertValid(db,kind,action,payload,now=new Date()){
  const issues=validateCommand(db,kind,action,payload,now);
  if(issues.length)throw new ValidationError(issues);
}
