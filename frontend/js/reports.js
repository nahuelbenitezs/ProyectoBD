import {collator} from './utils.js';

export const reportDefs = [
 ['posiciones','Tabla de posiciones','Clasificación de todos los equipos'],
 ['goleadores','Máximos goleadores','Top 10 de la edición'],
 ['fair-play','Fair play','Tarjetas y comportamiento deportivo'],
 ['promedio-goles','Promedio de goles','Evolución por fecha y edición'],
 ['uso-espacios','Uso de canchas y turnos','Ocupación de instalaciones'],
 ['jugadores-facultad','Jugadores por facultad','Distribución por tipo'],
 ['sin-participacion','Sin participación','Inscriptos que nunca jugaron'],
 ['sanciones','Sanciones por equipo','Motivos y cantidad de suspensiones'],
 ['estados','Estado de partidos','Jugados, cancelados y postergados'],
 ['local-visitante','Local vs. visitante','Rendimiento por condición'],
 ['disciplina','Disciplina individual','Tarjetas y suspensiones por jugador'],
 ['goles-tramos','Goles por tramo','Minutos con más goles']
];
export const reportFields = {
  posiciones:[['equipo','Equipo'],['partidos_jugados','PJ'],['ganados','PG'],['empatados','PE'],['perdidos','PP'],['goles_favor','GF'],['goles_contra','GC'],['diferencia_goles','DG'],['puntos','PTS']],
  goleadores:[['posicion','#'],['nombre_completo','Jugador'],['equipo','Equipo'],['goles','Goles']],
  'fair-play':[['equipo','Equipo'],['amarillas','Amarillas'],['rojas','Rojas'],['puntos_fair_play','Puntos fair play']],
  'promedio-goles':[['fecha','Fecha'],['partidos_jugados','Partidos'],['total_goles','Goles'],['promedio_goles','Promedio']],
  'uso-espacios':[['tipo_recurso','Tipo'],['recurso','Recurso'],['partidos_jugados','Usos']],
  'jugadores-facultad':[['facultad','Facultad'],['tipo','Tipo'],['cantidad_jugadores','Jugadores']],
  'sin-participacion':[['nombre_completo','Jugador'],['equipo','Equipo'],['tipo','Tipo']],
  sanciones:[['equipo','Equipo'],['motivo','Motivo'],['cantidad_sanciones','Cantidad']],
  estados:[['estado','Estado'],['cantidad','Partidos'],['porcentaje','Porcentaje %']],
  'local-visitante':[['equipo','Equipo'],['partidos_local','PJ local'],['partidos_visitante','PJ visita'],['gf_local','GF local'],['gf_visitante','GF visita'],['puntos_local','PTS local'],['puntos_visitante','PTS visita']],
  disciplina:[['nombre_completo','Jugador'],['equipo','Equipo'],['amarillas','Amarillas'],['rojas','Rojas'],['sanciones','Sanciones'],['fechas_suspension','Fechas']],
  'goles-tramos':[['tramo','Minutos'],['cantidad_goles','Goles'],['porcentaje_goles','Porcentaje %']]
};

export function goalResult(db, match) {
  let local=0, visitante=0;
  for(const g of db.gol.filter(g=>+g.id_partido===+match.id_partido)) {
    const registered = db.planilla_partido.find(p=>+p.id_partido===+match.id_partido && +p.ci_jugador===+g.ci_jugador);
    if(!registered) continue;
    const side=+registered.id_equipo===+match.id_equipo_local?'local':'visitante';
    const winner=g.autogol?(side==='local'?'visitante':'local'):side;
    if(winner==='local')local++; else visitante++;
  }
  return {local,visitante};
}
export function automaticSanctions(db,id) {
  const matches=db.partido.filter(p=>p.estado==='jugado' && +p.id_torneo===+id);
  const rows=[];const byPlayer={};
  for(const t of db.tarjeta){
    const p=matches.find(m=>+m.id_partido===+t.id_partido);
    if(!p)continue;
    const key=`${t.ci_jugador}/${t.color}`;
    (byPlayer[key]??=[]).push({...t,numero_fecha:p.numero_fecha,dia:p.dia});
  }
  for(const [key,items] of Object.entries(byPlayer)){
    items.sort((a,b)=>(+a.numero_fecha- +b.numero_fecha)||String(a.dia).localeCompare(String(b.dia))||(+a.minuto- +b.minuto)||(+a.id_tarjeta- +b.id_tarjeta));
    items.forEach((t,i)=>{
      if(t.color==='roja' || (t.color==='amarilla' && (i+1)%3===0)) rows.push({id_sancion:-Number(t.id_tarjeta),ci_jugador:t.ci_jugador,id_torneo:+id,motivo:t.color==='roja'?'roja':'acumulación de amarillas',numero_fecha_inicio:+t.numero_fecha+1,cantidad_fechas:1,origen:'automatica'});
    });
  }
  return rows;
}
export const sanctionsFor = (db,id) => [...db.sancion_jugador.filter(s=>+s.id_torneo===+id),...automaticSanctions(db,id)];
export const isSuspended = (db,id,ci,round) => sanctionsFor(db,id).some(s=>+s.ci_jugador===+ci && round>=s.numero_fecha_inicio && round<s.numero_fecha_inicio+s.cantidad_fechas);

export function standings(db,id){
  const base=db.equipo.filter(e=>+e.id_torneo===+id).map(e=>({id_torneo:+id,id_equipo:e.id_equipo,equipo:e.nombre,partidos_jugados:0,ganados:0,empatados:0,perdidos:0,goles_favor:0,goles_contra:0,diferencia_goles:0,puntos:0}));
  const map=new Map(base.map(x=>[+x.id_equipo,x]));
  for(const p of db.partido.filter(m=>+m.id_torneo===+id&&m.estado==='jugado')) {
    const {local,visitante}=goalResult(db,p);
    for(const [team,GF,GC] of [[p.id_equipo_local,local,visitante],[p.id_equipo_visitante,visitante,local]]){
      const row=map.get(+team);if(!row)continue;
      row.partidos_jugados++;row.goles_favor+=GF;row.goles_contra+=GC;row.diferencia_goles+=GF-GC;
      if(GF>GC){row.ganados++;row.puntos+=3;}else if(GF===GC){row.empatados++;row.puntos++;}else row.perdidos++;
    }
  }
  return [...base].sort((a,b)=>b.puntos-a.puntos||b.diferencia_goles-a.diferencia_goles||b.goles_favor-a.goles_favor||collator.compare(a.equipo,b.equipo));
}
export function generateReport(db,slug,id){
 const teams=db.equipo.filter(e=>+e.id_torneo===+id);
 const matches=db.partido.filter(p=>+p.id_torneo===+id);
 const played=matches.filter(p=>p.estado==='jugado');
 const results=played.map(p=>({...p,...goalResult(db,p)}));
 const getTeam=k=>teams.find(t=>+t.id_equipo===+k)?.nombre||`Equipo ${k}`;
 const getPlayer=ci=>db.jugador.find(j=>+j.ci===+ci);
 const getPlayerName=ci=>{const j=getPlayer(ci);return j?`${j.nombre} ${j.apellido}`:`CI ${ci}`};
 const getPlayerTeam=ci=>db.equipo_jugador_torneo.find(r=>+r.ci_jugador===+ci && +r.id_torneo===+id)?.id_equipo;
 const goals=db.gol.filter(g=>played.some(p=>+p.id_partido===+g.id_partido));
 const cards=db.tarjeta.filter(t=>played.some(p=>+p.id_partido===+t.id_partido));
 const sanc=sanctionsFor(db,id);
 if(slug==='posiciones') return standings(db,id);
 if(slug==='goleadores'){
  const map=new Map();for(const g of goals.filter(g=>!g.autogol))map.set(+g.ci_jugador,(map.get(+g.ci_jugador)||0)+1);
  return [...map.entries()].map(([ci,goles])=>({ci_jugador:ci,nombre_completo:getPlayerName(ci),equipo:getTeam(getPlayerTeam(ci)),goles})).sort((a,b)=>b.goles-a.goles||collator.compare(a.nombre_completo,b.nombre_completo)).slice(0,10).map((x,i)=>({...x,posicion:i+1}));
 }
 if(slug==='fair-play')return teams.map(e=>{const cc=cards.filter(t=>+getPlayerTeam(t.ci_jugador)===+e.id_equipo);const amarillas=cc.filter(t=>t.color==='amarilla').length;const rojas=cc.length-amarillas;return {equipo:e.nombre,amarillas,rojas,puntos_fair_play:amarillas+rojas*3}}).sort((a,b)=>a.puntos_fair_play-b.puntos_fair_play||collator.compare(a.equipo,b.equipo));
 if(slug==='promedio-goles'){
  const dates=[...new Set(results.map(r=>+r.numero_fecha))].sort((a,b)=>a-b);
  const rows=dates.map(fecha=>{const arr=results.filter(r=>+r.numero_fecha===fecha);const total_goles=arr.reduce((s,x)=>s+x.local+x.visitante,0);return {fecha:`Fecha ${fecha}`,numero_fecha:fecha,partidos_jugados:arr.length,total_goles,promedio_goles:Number((total_goles/arr.length).toFixed(2))}});
  const total=results.reduce((s,x)=>s+x.local+x.visitante,0);
  return [...rows,{fecha:'Toda la edición',numero_fecha:null,partidos_jugados:results.length,total_goles:total,promedio_goles:results.length?Number((total/results.length).toFixed(2)):0}];
 }
 if(slug==='uso-espacios'){
  const map=new Map();for(const p of played){const c=db.complejo.find(c=>+c.id_complejo===+p.id_complejo);const turn=db.turno.find(t=>+t.id_turno===+p.id_turno);const names=[['Cancha',`${p.nombre_cancha} / ${c?.nombre||''}`],['Turno',`${turn?.hora_inicio?.slice(0,5)||''}–${turn?.hora_fin?.slice(0,5)||''}`]];for(const [tipo,recurso] of names){const key=`${tipo}:${recurso}`;const row=map.get(key)||{tipo_recurso:tipo,recurso,partidos_jugados:0};row.partidos_jugados++;map.set(key,row)}}
  return [...map.values()].sort((a,b)=>collator.compare(a.tipo_recurso,b.tipo_recurso)||b.partidos_jugados-a.partidos_jugados);
 }
 if(slug==='jugadores-facultad')return db.facultad.flatMap(f=>['grado','posgrado','docente','funcionario'].map(tipo=>({facultad:f.nombre,tipo,cantidad_jugadores:db.jugador.filter(j=>+j.id_facultad===+f.id_facultad&&j.tipo===tipo).length})));
 if(slug==='sin-participacion')return db.equipo_jugador_torneo.filter(p=>+p.id_torneo===+id && !db.planilla_partido.some(pp=>+pp.ci_jugador===+p.ci_jugador&&+pp.id_equipo===+p.id_equipo&&matches.some(m=>+m.id_partido===+pp.id_partido))).map(x=>({nombre_completo:getPlayerName(x.ci_jugador),equipo:getTeam(x.id_equipo),tipo:getPlayer(x.ci_jugador)?.tipo||''})).sort((a,b)=>collator.compare(a.equipo,b.equipo)||collator.compare(a.nombre_completo,b.nombre_completo));
 if(slug==='sanciones')return teams.flatMap(e=>['roja','acumulación de amarillas','disciplinaria'].map(motivo=>({equipo:e.nombre,motivo,cantidad_sanciones:sanc.filter(s=>s.motivo===motivo&&+getPlayerTeam(s.ci_jugador)===+e.id_equipo).length})));
 if(slug==='estados')return ['jugado','postergado','cancelado','programado'].map(estado=>{const cantidad=matches.filter(m=>m.estado===estado).length;return {estado,cantidad,porcentaje:matches.length?Number((cantidad/matches.length*100).toFixed(2)):0}});
 if(slug==='local-visitante')return teams.map(e=>{const home=results.filter(m=>+m.id_equipo_local===+e.id_equipo),away=results.filter(m=>+m.id_equipo_visitante===+e.id_equipo);return {equipo:e.nombre,partidos_local:home.length,partidos_visitante:away.length,gf_local:home.reduce((s,x)=>s+x.local,0),gf_visitante:away.reduce((s,x)=>s+x.visitante,0),puntos_local:home.reduce((s,x)=>s+(x.local>x.visitante?3:x.local===x.visitante?1:0),0),puntos_visitante:away.reduce((s,x)=>s+(x.visitante>x.local?3:x.visitante===x.local?1:0),0)}}).sort((a,b)=>collator.compare(a.equipo,b.equipo));
 if(slug==='disciplina')return db.equipo_jugador_torneo.filter(p=>+p.id_torneo===+id).map(p=>{const cc=cards.filter(t=>+t.ci_jugador===+p.ci_jugador),ss=sanc.filter(s=>+s.ci_jugador===+p.ci_jugador),amarillas=cc.filter(t=>t.color==='amarilla').length,rojas=cc.filter(t=>t.color==='roja').length;return {nombre_completo:getPlayerName(p.ci_jugador),equipo:getTeam(p.id_equipo),amarillas,rojas,sanciones:ss.length,fechas_suspension:ss.reduce((acc,s)=>acc+Number(s.cantidad_fechas),0),indice_disciplina:amarillas+3*rojas}}).filter(r=>r.amarillas+r.rojas+r.sanciones>0).sort((a,b)=>b.indice_disciplina-a.indice_disciplina||b.fechas_suspension-a.fechas_suspension);
 if(slug==='goles-tramos')return [[0,15],[16,30],[31,45],[46,60]].map(([lo,hi])=>{const cnt=goals.filter(g=>+g.minuto>=lo&&+g.minuto<=hi).length;return {tramo:`${String(lo).padStart(2,'0')}–${hi}`,cantidad_goles:cnt,porcentaje_goles:goals.length?Number((cnt/goals.length*100).toFixed(2)):0}});
 return [];
}
