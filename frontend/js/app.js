import {esc,ico,badge,fmtDate,fmtDay,timeHM,initials,normalize,emptyState,collator} from './utils.js';
import {isDemo,setMode,getSavedUser,demoUser,demoReset,login,logout,loadData,loadReport,mutate} from './repository.js';
import {standings,goalResult,sanctionsFor,isSuspended,reportDefs,reportFields} from './reports.js';
import {canModify} from './permissions.js';

const app=document.getElementById('app');
const navGroups=[
 {label:'GENERAL',links:[['dashboard','Resumen','dashboard'],['fixture','Fixture y partidos','fixture'],['equipos','Equipos y planteles','team'],['jugadores','Jugadores','players']]},
 {label:'ADMINISTRACIÓN',links:[['torneos','Ediciones del torneo','trophy'],['complejos','Complejos y canchas','venue'],['sanciones','Sanciones','shield']]},
 {label:'ESTADÍSTICAS',links:[['reportes','Reportes','chart']]}
];
const titles={dashboard:'Panel general',fixture:'Fixture y partidos',equipos:'Equipos y planteles',jugadores:'Jugadores',torneos:'Ediciones del torneo',complejos:'Complejos y canchas',sanciones:'Sanciones',reportes:'Centro de reportes'};
const state={db:null,user:null,page:'dashboard',modal:null,tournament:1,search:'',status:'todos',report:'posiciones',reportRows:[],reportLoading:false,menuOpen:false,theme:localStorage.getItem('ucu_theme')||'dark',error:'',toast:null,loading:true};
const admin=()=>state.user?.rol==='administrador';
const tId=()=>Number(state.tournament);
const getTournament=()=>state.db.torneo.find(t=>+t.id_torneo===tId());
const teams=()=>state.db.equipo.filter(e=>+e.id_torneo===tId());
const matches=()=>state.db.partido.filter(p=>+p.id_torneo===tId());
const players=()=>state.db.jugador;
const teamName=(id)=>state.db.equipo.find(x=>+x.id_equipo===+id)?.nombre||'Equipo no encontrado';
const playerName=(ci)=>{const p=state.db.jugador.find(x=>+x.ci===+ci);return p?`${p.nombre} ${p.apellido}`:`CI ${ci}`};
const facultyName=(id)=>state.db.facultad.find(x=>+x.id_facultad===+id)?.nombre||'Facultad';
const tournamentOptions=()=>state.db.torneo.map(t=>`<option value="${t.id_torneo}" ${tId()===+t.id_torneo?'selected':''}>${esc(t.anio)} · Semestre ${esc(t.semestre)}</option>`).join('');
const teamsOptions=(id,chosen)=>state.db.equipo.filter(e=>+e.id_torneo===+id).map(e=>`<option value="${e.id_equipo}" ${+chosen===+e.id_equipo?'selected':''}>${esc(e.nombre)}</option>`).join('');
const boolBadge=(v)=>v?'<span class="tiny-tag green">Techada</span>':'<span class="tiny-tag">Abierta</span>';
const permNote=()=>!admin()?'<div class="info-strip">'+ico('info',17)+' Cuenta planillero: consulta de información y registro de planillas, goles y tarjetas. Las acciones de administración están restringidas.</div>':'';
const statusColors={jugado:'green',programado:'blue',postergado:'orange',cancelado:'red'};
function jersey(id,size='normal'){
 const colors=['lime','sky','violet','amber','pink','teal'];
 return `<div class="team-emblem emblem-${colors[(Math.abs(Number(id))-1)%6]} ${size==='large'?'emblem-large':''}">${initials(teamName(id))}</div>`;
}
function actionBtn(text,action,id='',style='primary',iconName='plus'){
 return `<button type="button" class="btn btn-${style}" data-action="${action}" ${id!==''?`data-id="${esc(id)}"`:''}>${ico(iconName,17)}<span>${esc(text)}</span></button>`;
}
function iconBtn(action,id,iconName,label){return `<button type="button" class="icon-btn" data-action="${action}" data-id="${esc(id)}" aria-label="${esc(label)}" title="${esc(label)}">${ico(iconName,17)}</button>`}
function sectionHead(title,descr,action=''){return `<div class="section-head"><div><h2>${esc(title)}</h2>${descr?`<p>${esc(descr)}</p>`:''}</div>${action}</div>`}
function table(headers,body,empty='No se encontraron resultados'){
 return `<div class="table-scroll"><table class="data-table"><thead><tr>${headers.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${body||`<tr><td colspan="${headers.length}">${emptyState(empty)}</td></tr>`}</tbody></table></div>`;
}
function layout(){
 if(!state.db)return `<div class="initial-loading"><span>Preparando el tablero…</span></div>`;
 if(!state.user)return loginView();
 const tour=getTournament();
 return `<div class="shell theme-${state.theme}">
 <aside class="sidebar ${state.menuOpen?'mobile-open':''}">
  <div class="logo-box"><div class="logo-symbol">${ico('football',28)}</div><div><div class="logo-title">UCU <span>LEAGUE</span></div><div class="logo-subtitle">FÚTBOL 5 · INTERFACULTADES</div></div></div>
  <div class="edition-box"><span class="edition-kicker"><span class="live-dot"></span> TORNEO SELECCIONADO</span><strong>${esc(tour?.nombre||'Sin edición')}</strong><div>${badge(tour?.estado||'—')}</div></div>
  <nav class="sidebar-nav">${navGroups.map(g=>`<div class="nav-group"><div class="nav-caption">${g.label}</div>${g.links.map(([page,label,icon])=>`<button class="nav-link ${state.page===page?'active':''}" data-page="${page}">${ico(icon,19)}<span>${label}</span>${state.page===page?`<span class="nav-active-indicator"></span>`:''}</button>`).join('')}</div>`).join('')}</nav>
  <div class="sidebar-bottom"><div class="side-divider"></div><div class="user-profile"><div class="avatar">${state.user.rol==='administrador'?'AD':'PL'}</div><div class="profile-meta"><strong>${state.user.rol==='administrador'?'Administrador':'Planillero'}</strong><span title="${esc(state.user.correo)}">${esc(state.user.correo)}</span></div><button class="icon-btn" data-action="switch-user" title="Cambiar usuario">${ico('logout',17)}</button></div><div class="mode-line"><span class="mode-indicator"></span>${isDemo()?'Datos de demostración':'Conectado a la API'}</div></div>
 </aside><div class="scrim ${state.menuOpen?'visible':''}" data-action="close-menu"></div>
 <main class="workspace"><header class="topbar"><div class="topbar-left"><button class="menu-toggle icon-btn" data-action="menu">${ico('menu',22)}</button><span class="breadcrumb-root">COMPETICIÓN</span>${ico('chevron',15)}<span class="breadcrumb-current">${esc(titles[state.page])}</span></div><div class="topbar-right"><div class="search-wrap">${ico('search',17)}<input id="global-search" placeholder="Buscar equipo, jugador…" aria-label="Buscar" value="${esc(state.search)}"/></div><select id="tournament-picker" aria-label="Elegir torneo">${tournamentOptions()}</select><button class="icon-btn theme-btn" data-action="theme" aria-label="Alternar tema">${ico(state.theme==='dark'?'sun':'moon',19)}</button><span class="top-avatar">${state.user.rol==='administrador'?'AD':'PL'}</span></div></header>
 <div class="page-content" id="main-body">${content()}</div>
 <footer class="footer"><span>UCU League · Proyecto académico, Base de Datos 1 · 2026</span><span>${isDemo()?'Modo demostración · Datos del SQL de prueba':'API Python · MySQL'}</span></footer></main>
 ${renderModal()}<div id="toast-area" aria-live="polite">${state.toast?`<div class="toast toast-${state.toast.type}">${ico(state.toast.type==='error'?'alert':'check',18)}${esc(state.toast.msg)}<button class="toast-close" data-action="clear-toast">${ico('close',15)}</button></div>`:''}</div>
 </div>`;
}
function pageIntro(kicker,title,subtitle,actions=''){
 return `<div class="page-intro"><div><div class="eyebrow">${esc(kicker)}</div><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div>${actions?`<div class="intro-actions">${actions}</div>`:''}</div>`;
}
function content(){
 switch(state.page){case'dashboard':return dashboard();case'jugadores':return playersView();case'equipos':return teamsView();case'fixture':return fixtureView();case'torneos':return tournamentsView();case'complejos':return venuesView();case'sanciones':return sanctionsView();case'reportes':return reportsView();default:return dashboard()}
}
function dashboard(){
 const ms=matches(),played=ms.filter(p=>p.estado==='jugado'),pts=standings(state.db,tId());
 const goals=played.reduce((s,p)=>{const g=goalResult(state.db,p);return s+g.local+g.visitante},0);
 const next=ms.filter(p=>p.estado==='programado').sort((a,b)=>a.dia.localeCompare(b.dia));
 const recent=[...played].sort((a,b)=>b.dia.localeCompare(a.dia)||b.id_partido-a.id_partido).slice(0,4);
 const rounds=[...new Set(played.map(p=>p.numero_fecha))].sort((a,b)=>a-b);
 const roundData=rounds.map(r=>played.filter(p=>+p.numero_fecha===+r).reduce((n,p)=>{const x=goalResult(state.db,p);return n+x.local+x.visitante},0));
 const peak=Math.max(1,...roundData);
 const barChart=rounds.map((r,i)=>`<div class="bar-col"><div class="bar-top">${roundData[i]}</div><div class="bar-track"><div class="bar-fill" style="height:${Math.max(8,roundData[i]/peak*100)}%"></div></div><span>Fecha ${r}</span></div>`).join('');
 const playedPct=ms.length?played.length/ms.length*100:0;
 return `<div class="fade-in">${pageIntro('TEMPORADA '+(getTournament()?.anio||'2026')+' / S'+(getTournament()?.semestre||'2'),'El torneo, de un vistazo','Resultados, estadísticas y movimientos de la competición en tiempo real desde los datos disponibles.',admin()?actionBtn('Programar partido','new-partido','','primary','plus'):'')}
 <div class="hero"><div class="hero-inner"><div class="hero-top"><span class="hero-badge"><span class="live-dot"></span> EDICIÓN ${esc(getTournament()?.anio||'2026')} · SEMESTRE ${esc(getTournament()?.semestre||2)}</span></div><h2>La cancha está lista.<br/><em>El torneo también.</em></h2><p>Gestioná los encuentros y seguí el rendimiento de todas las facultades desde un solo lugar.</p><div class="hero-cta">${actionBtn('Explorar fixture','page-fixture','','hero-btn','arrow')}<button class="hero-link" data-action="page-reportes">Ver estadísticas ${ico('arrow',16)}</button></div></div><div class="pitch"><div class="pitch-outline"><div class="pitch-half"></div><div class="pitch-center"></div><div class="goal goal-l"></div><div class="goal goal-r"></div></div><div class="pitch-ball">${ico('football',50)}</div></div></div>
 <div class="stats-grid"><div class="stat-card"><div class="stat-icon green">${ico('fixture',22)}</div><div class="stat-trend">PARTIDOS JUGADOS</div><div class="stat-value">${played.length}<span> / ${ms.length}</span></div><div class="stat-note"><span class="muted-line">${Math.round(playedPct)}% de la programación</span><div class="mini-progress"><span style="width:${playedPct}%"></span></div></div></div>
 <div class="stat-card"><div class="stat-icon violet">${ico('team',22)}</div><div class="stat-trend">EQUIPOS INSCRIPTOS</div><div class="stat-value">${teams().length}<span> equipos</span></div><div class="stat-note">${new Set(teams().map(t=>t.id_facultad)).size} facultades representadas</div></div>
 <div class="stat-card"><div class="stat-icon blue">${ico('players',22)}</div><div class="stat-trend">JUGADORES EN PLANTELES</div><div class="stat-value">${state.db.equipo_jugador_torneo.filter(r=>+r.id_torneo===tId()).length}<span> jugadores</span></div><div class="stat-note">Listos para competir</div></div>
 <div class="stat-card"><div class="stat-icon orange">${ico('football',22)}</div><div class="stat-trend">GOLES CONVERTIDOS</div><div class="stat-value">${goals}<span> goles</span></div><div class="stat-note">${played.length?(goals/played.length).toFixed(1):'0'} de promedio por partido</div></div></div>
 <div class="dashboard-columns"><section class="panel panel-results">${sectionHead('Últimos resultados','Marcadores de los partidos disputados',`<button class="text-link" data-page="fixture">Ver todos ${ico('arrow',15)}</button>`)}${recent.length?recent.map(p=>resultRow(p)).join(''):emptyState('Todavía no hay partidos jugados')}</section><section class="panel panel-standings">${sectionHead('Tabla de posiciones','Clasificación actual',`<button class="text-link" data-action="page-reportes">Ver reporte ${ico('arrow',15)}</button>`)}<div class="standings-mini"><div class="standings-mini-header"><span>#</span><span>EQUIPO</span><span>PJ</span><span>DG</span><span>PTS</span></div>${pts.slice(0,6).map((r,i)=>`<div class="standings-mini-row"><span class="rank ${i<3?'rank-top':''}">${i+1}</span><span class="mini-team">${jersey(r.id_equipo)} <span>${esc(r.equipo)}</span></span><span>${r.partidos_jugados}</span><span>${r.diferencia_goles>0?'+':''}${r.diferencia_goles}</span><strong>${r.puntos}</strong></div>`).join('')}</div></section></div>
 <div class="dashboard-columns dashboard-bottom"><section class="panel">${sectionHead('Goles por fecha','Distribución durante el semestre')}<div class="bars">${barChart||emptyState('Sin goles registrados')}</div></section><section class="panel next-panel">${sectionHead('Próximos encuentros','Partidos programados')}${next.length?next.slice(0,2).map(p=>`<div class="upcoming-card"><div class="upcoming-head"><span>FECHA ${p.numero_fecha}</span>${badge(p.estado)}</div><div class="upcoming-teams">${jersey(p.id_equipo_local)}<strong>${esc(teamName(p.id_equipo_local))}</strong><span class="versus">VS</span><strong>${esc(teamName(p.id_equipo_visitante))}</strong>${jersey(p.id_equipo_visitante)}</div><div class="upcoming-foot">${ico('fixture',15)} ${fmtDate(p.dia)} <span>·</span> ${esc(state.db.complejo.find(c=>+c.id_complejo===+p.id_complejo)?.nombre||'')} · ${esc(p.nombre_cancha)}</div></div>`).join(''):emptyState('No hay próximos partidos programados')}${actionBtn('Ir al fixture','page-fixture','','outline','arrow')}</section></div>
 ${isDemo()?'<div class="demo-banner">'+ico('info',19)+' <span>Estás viendo una <strong>demostración local</strong> construida con los datos de <code>torneo_ucu_creacion.sql</code>. Los cambios se guardan solo en este navegador.</span>'+`<button data-action="reset-demo">Reiniciar datos</button></div>`:''}</div>`;
}
function resultRow(p){const g=goalResult(state.db,p);return `<div class="result-row"><div class="result-round">F${p.numero_fecha}<small>${fmtDay(p.dia)}</small></div><div class="result-teams"><div>${jersey(p.id_equipo_local)}<span>${esc(teamName(p.id_equipo_local))}</span></div><div>${jersey(p.id_equipo_visitante)}<span>${esc(teamName(p.id_equipo_visitante))}</span></div></div><div class="result-scores"><strong>${g.local}</strong><strong>${g.visitante}</strong></div><button class="icon-btn" data-action="view-planilla" data-id="${p.id_partido}" title="Ver planilla">${ico('chevron',18)}</button></div>`}
function playersView(){
 const q=normalize(state.search);const filtered=players().filter(p=>[p.ci,p.nombre,p.apellido,p.email,facultyName(p.id_facultad),p.tipo].some(x=>normalize(x).includes(q))).sort((a,b)=>collator.compare(a.apellido,b.apellido));
 const body=filtered.map(p=>{const roster=state.db.equipo_jugador_torneo.find(r=>+r.ci_jugador===+p.ci&&+r.id_torneo===tId());return `<tr><td><div class="name-cell"><div class="person-avatar">${initials(`${p.nombre} ${p.apellido}`)}</div><div><strong>${esc(p.nombre)} ${esc(p.apellido)}</strong><small>${esc(p.email)}</small></div></div></td><td class="mono">${p.ci}</td><td>${esc(facultyName(p.id_facultad))}</td><td><span class="type-chip">${esc(p.tipo)}</span></td><td>${roster?`<span class="team-pill">${esc(teamName(roster.id_equipo))}</span>`:'<span class="muted">Sin equipo</span>'}</td>${admin()?`<td class="actions-cell">${iconBtn('edit-jugador',p.ci,'pencil','Editar jugador')}${iconBtn('delete-jugador',p.ci,'trash','Eliminar jugador')}</td>`:''}</tr>`}).join('');
 return `<div class="fade-in">${pageIntro('PERSONAS','Gestión de jugadores','Registrá estudiantes, docentes y funcionarios de las diferentes facultades.',admin()?actionBtn('Nuevo jugador','new-jugador'):'')}${permNote()}<div class="info-metrics"><span>${ico('players',18)} <strong>${players().length}</strong> jugadores registrados</span><span>${ico('team',18)} <strong>${state.db.equipo_jugador_torneo.filter(r=>+r.id_torneo===tId()).length}</strong> inscripciones en esta edición</span></div><section class="panel panel-table">${sectionHead('Listado de jugadores',`${filtered.length} de ${players().length} registros`)}${table(['JUGADOR','CÉDULA','FACULTAD','TIPO','EQUIPO',...(admin()?['ACCIONES']:[])],body,'No hay jugadores que coincidan')}</section></div>`;
}
function teamsView(){
 const q=normalize(state.search);const arr=teams().filter(e=>[e.nombre,facultyName(e.id_facultad),playerName(e.ci_capitan)].some(x=>normalize(x).includes(q)));
 const canCreate=getTournament()?.estado==='inscripción';
 return `<div class="fade-in">${pageIntro('COMPETIDORES','Equipos y planteles','Consultá las nóminas, los capitanes y las facultades representadas.',admin()&&canCreate?actionBtn('Nuevo equipo','new-equipo'):'')}${permNote()}${admin()&&!canCreate?`<div class="info-strip">${ico('lock',17)} La edición está en estado «${esc(getTournament()?.estado)}»: los planteles solo pueden cambiarse durante inscripción.</div>`:''}<div class="team-grid">${arr.map(e=>{const roster=state.db.equipo_jugador_torneo.filter(r=>+r.id_equipo===+e.id_equipo&&+r.id_torneo===tId());const cap=playerName(e.ci_capitan);return `<div class="team-card"><div class="team-card-top"><div class="team-badge">${jersey(e.id_equipo,'large')}</div><span class="tiny-tag">${roster.length}/10 jugadores</span></div><h3>${esc(e.nombre)}</h3><p>${esc(facultyName(e.id_facultad))}</p><div class="team-card-detail"><div><span>CAPITÁN</span><strong>${esc(cap)}</strong></div><div><span>PLANTEL</span><strong>${roster.length} integrantes</strong></div></div><div class="team-card-actions">${actionBtn('Ver plantel','roster',e.id_equipo,'outline','players')}${admin()?iconBtn('edit-equipo',e.id_equipo,'pencil','Editar equipo')+iconBtn('delete-equipo',e.id_equipo,'trash','Eliminar equipo'):''}</div></div>`}).join('')}</div>${arr.length?'':emptyState('No se encontraron equipos')}</div>`;
}
function fixtureView(){
 const arr=matches().filter(p=>(state.status==='todos'||p.estado===state.status)&&[teamName(p.id_equipo_local),teamName(p.id_equipo_visitante),p.nombre_cancha,p.numero_fecha].some(x=>normalize(x).includes(normalize(state.search)))).sort((a,b)=>+a.numero_fecha-+b.numero_fecha||a.dia.localeCompare(b.dia)||+a.id_turno-+b.id_turno);
 const groups=[...new Set(arr.map(p=>p.numero_fecha))];
 return `<div class="fade-in">${pageIntro('CALENDARIO','Fixture y partidos','Programación, resultados y planillas de cada fecha de la liga.',admin()?actionBtn('Nuevo partido','new-partido'):'')}${permNote()}<div class="filter-strip">${['todos','programado','jugado','postergado','cancelado'].map(x=>`<button class="filter-pill ${state.status===x?'selected':''}" data-action="fixture-filter" data-id="${x}">${esc(x==='todos'?'Todos':x.charAt(0).toUpperCase()+x.slice(1))}<span>${x==='todos'?matches().length:matches().filter(p=>p.estado===x).length}</span></button>`).join('')}</div>${groups.map(round=>`<section class="fixture-group"><div class="fixture-round"><div><span class="round-icon">${ico('fixture',19)}</span><h2>Fecha ${round}</h2></div><span>${arr.filter(p=>p.numero_fecha===round).length} partido(s)</span></div><div class="fixture-list">${arr.filter(p=>p.numero_fecha===round).map(p=>matchCard(p)).join('')}</div></section>`).join('')||emptyState('No hay partidos con esos filtros')}</div>`;
}
function matchCard(p){
 const g=goalResult(state.db,p);const court=state.db.complejo.find(c=>+c.id_complejo===+p.id_complejo)?.nombre||'';const turn=state.db.turno.find(t=>+t.id_turno===+p.id_turno);
 return `<article class="match-card"><div class="match-meta"><div><span class="match-date">${fmtDate(p.dia,{weekday:'short',day:'numeric',month:'short'})}</span><span class="match-time">${ico('clock',14)} ${timeHM(turn?.hora_inicio)}</span></div>${badge(p.estado)}</div><div class="match-center"><div class="match-team home">${jersey(p.id_equipo_local)}<span>${esc(teamName(p.id_equipo_local))}</span></div><div class="match-score">${p.estado==='jugado'?`<strong>${g.local}</strong><span>:</span><strong>${g.visitante}</strong>`:'<span class="vs-chip">VS</span>'}</div><div class="match-team away"><span>${esc(teamName(p.id_equipo_visitante))}</span>${jersey(p.id_equipo_visitante)}</div></div><div class="match-bottom"><div>${ico('venue',15)} ${esc(court)} · ${esc(p.nombre_cancha)}</div><div class="match-actions">${actionBtn('Ver planilla','view-planilla',p.id_partido,'subtle','players')}${admin()&&p.estado!=='jugado'?iconBtn('edit-partido',p.id_partido,'pencil','Editar partido')+iconBtn('delete-partido',p.id_partido,'trash','Eliminar partido'):''}</div></div></article>`;
}
function tournamentsView(){
 return `<div class="fade-in">${pageIntro('EDICIONES','Torneos','Cada semestre constituye una nueva edición de la competición.',admin()?actionBtn('Nueva edición','new-torneo'):'')}${permNote()}<div class="tournament-list">${[...state.db.torneo].sort((a,b)=>b.anio-a.anio||b.semestre-a.semestre).map(t=>`<div class="tournament-item"><div class="tournament-icon">${ico('trophy',28)}</div><div class="tournament-info"><div class="tournament-title"><h3>${esc(t.nombre)}</h3>${badge(t.estado)}</div><p>Semestre ${t.semestre} · ${fmtDate(t.fecha_inicio)} — ${fmtDate(t.fecha_fin)}</p><span>${state.db.equipo.filter(e=>+e.id_torneo===+t.id_torneo).length} equipos en esta edición</span></div>${admin()?iconBtn('edit-torneo',t.id_torneo,'pencil','Editar edición'):''}<button class="btn btn-outline" data-action="select-torneo" data-id="${t.id_torneo}">Ver torneo ${ico('arrow',16)}</button></div>`).join('')}</div></div>`;
}
function venuesView(){
 return `<div class="fade-in">${pageIntro('INSTALACIONES','Complejos y canchas','Administrá las sedes deportivas y sus espacios habilitados.',admin()?actionBtn('Nuevo complejo','new-complejo'):'')}${permNote()}<div class="venue-grid">${state.db.complejo.map(c=>{const courts=state.db.cancha.filter(x=>+x.id_complejo===+c.id_complejo);return `<section class="panel venue-card"><div class="venue-head"><div class="venue-icon">${ico('venue',24)}</div><div><h3>${esc(c.nombre)}</h3><p>${esc(c.direccion)} · ${esc(c.departamento)}</p></div>${admin()?iconBtn('edit-complejo',c.id_complejo,'pencil','Editar complejo')+iconBtn('delete-complejo',c.id_complejo,'trash','Eliminar complejo'):''}</div><div class="venue-courts">${courts.map(k=>`<div class="court-line"><div><strong>${esc(k.nombre_cancha)}</strong><span>${esc(k.superficie)}</span></div>${boolBadge(k.techada)}${admin()?iconBtn('edit-cancha',`${k.id_complejo}|${k.nombre_cancha}`,'pencil','Editar cancha')+iconBtn('delete-cancha',`${k.id_complejo}|${k.nombre_cancha}`,'trash','Eliminar cancha'):''}</div>`).join('')}${admin()?`<button class="add-inline" data-action="new-cancha" data-id="${c.id_complejo}">${ico('plus',16)} Agregar cancha</button>`:''}</div></section>`}).join('')}</div><section class="panel shifts-panel">${sectionHead('Turnos habilitados','Franja horaria obligatoria: 18:00 a 23:00')}<div class="shift-grid">${state.db.turno.map(t=>`<div class="shift"><span>${ico('clock',18)}</span><strong>${timeHM(t.hora_inicio)}</strong><i>—</i><strong>${timeHM(t.hora_fin)}</strong></div>`).join('')}</div></section></div>`;
}
function sanctionsView(){
 const sanctions=sanctionsFor(state.db,tId());const q=normalize(state.search);
 const rows=sanctions.filter(s=>[playerName(s.ci_jugador),s.motivo,teamName(state.db.equipo_jugador_torneo.find(r=>+r.ci_jugador===+s.ci_jugador&&+r.id_torneo===tId())?.id_equipo)].some(x=>normalize(x).includes(q))).sort((a,b)=>+a.numero_fecha_inicio-+b.numero_fecha_inicio).map(s=>`<tr><td><div class="name-cell"><div class="person-avatar">${initials(playerName(s.ci_jugador))}</div><strong>${esc(playerName(s.ci_jugador))}</strong></div></td><td>${esc(teamName(state.db.equipo_jugador_torneo.find(r=>+r.ci_jugador===+s.ci_jugador&&+r.id_torneo===tId())?.id_equipo))}</td><td>${esc(s.motivo)}</td><td><span class="type-chip">Fecha ${s.numero_fecha_inicio}</span></td><td>${s.cantidad_fechas}</td><td>${s.origen==='automatica'?'<span class="tiny-tag violet-tag">Automática</span>':'<span class="tiny-tag">Disciplinaria</span>'}</td>${admin()?`<td>${s.origen==='manual'?iconBtn('edit-sancion_jugador',s.id_sancion,'pencil','Editar sanción')+iconBtn('delete-sancion',s.id_sancion,'trash','Eliminar sanción'):'<span class="muted">—</span>'}</td>`:''}</tr>`).join('');
 return `<div class="fade-in">${pageIntro('DISCIPLINA','Control de sanciones','Las tarjetas generan suspensiones automáticamente; las disciplinarias las administra la organización.',admin()?actionBtn('Nueva sanción','new-sancion_jugador'):'')}${permNote()}<div class="info-strip">${ico('shield',18)} Una roja o la tercera amarilla suspende al jugador por una fecha. Las sanciones automáticas provienen de los datos de tarjetas y no se editan manualmente.</div><div class="info-metrics"><span>${ico('shield',18)} <strong>${sanctions.length}</strong> sanciones totales</span><span><strong>${sanctions.filter(s=>s.origen==='automatica').length}</strong> automáticas</span><span><strong>${sanctions.filter(s=>s.origen==='manual').length}</strong> disciplinarias</span></div><section class="panel panel-table">${sectionHead('Historial de sanciones','Incluye sanciones automáticas y disciplinarias')}${table(['JUGADOR','EQUIPO','MOTIVO','DESDE','FECHAS','ORIGEN',...(admin()?['ACCIONES']:[])],rows,'No se encontraron sanciones')}</section></div>`;
}
function reportsView(){
 const def=reportDefs.find(r=>r[0]===state.report)||reportDefs[0],fields=reportFields[def[0]]||[];
 const trs=state.reportRows.map((r,i)=>`<tr>${fields.map(([key])=>`<td>${key==='equipo'?`<strong>${esc(r[key])}</strong>`:esc(r[key]??'—')}</td>`).join('')}</tr>`).join('');
 const vals=state.reportRows.filter(x=>x?.cantidad_goles!==undefined||x?.total_goles!==undefined);
 return `<div class="fade-in">${pageIntro('ANÁLISIS','Centro de reportes','Los 9 reportes obligatorios y 3 adicionales que pide la consigna.',actionBtn('Exportar CSV','export-report','','outline','download'))}${permNote()}<div class="reports-wrap"><div class="report-menu">${reportDefs.map(([slug,title],i)=>`<button class="report-option ${state.report===slug?'current':''}" data-action="report" data-id="${slug}"><span class="report-index">${String(i+1).padStart(2,'0')}</span><span>${esc(title)}</span>${ico('chevron',15)}</button>`).join('')}</div><section class="panel report-panel"><div class="report-title"><div><div class="eyebrow">REPORTE ${String(reportDefs.findIndex(r=>r[0]===state.report)+1).padStart(2,'0')} / 12</div><h2>${esc(def[1])}</h2><p>${esc(def[2])}</p></div><span class="type-chip">Edición ${esc(getTournament()?.anio)}</span></div>${state.reportLoading?`<div class="report-loading">${ico('refresh',23)} Consultando datos…</div>`:table(fields.map(f=>f[1]),trs,'No hay datos para esta consulta')}<div class="report-foot">${ico('info',15)} ${state.reportRows.length} registros · ${isDemo()?'Calculado con el conjunto SQL de demostración':'Consultado a la API Python / MySQL'}</div></section></div></div>`;
}
function inputField(label,name,value='',type='text',attrs='',hint=''){
 return `<label class="form-field"><span>${esc(label)}</span><input name="${esc(name)}" type="${type}" value="${esc(value)}" ${attrs}/>${hint?`<small>${esc(hint)}</small>`:''}</label>`;
}
function selectField(label,name,values,selected='',attrs=''){
 return `<label class="form-field"><span>${esc(label)}</span><select name="${esc(name)}" ${attrs}>${values.map(([v,text])=>`<option value="${esc(v)}" ${String(v)===String(selected)?'selected':''}>${esc(text)}</option>`).join('')}</select></label>`;
}
const facOptions=()=>state.db.facultad.map(f=>[f.id_facultad,f.nombre]);
const tourOptions=()=>state.db.torneo.map(t=>[t.id_torneo,`${t.anio} · Semestre ${t.semestre}`]);
const playerOptions=(restricted=false)=>state.db.jugador.filter(j=>!restricted||state.db.equipo_jugador_torneo.some(r=>+r.ci_jugador===+j.ci&&+r.id_torneo===tId())).map(j=>[j.ci,`${j.apellido}, ${j.nombre} (${facultyName(j.id_facultad)})`]);
function formModal(title,description,body,kind,submitText='Guardar cambios',aux=''){
 return `<div class="modal-backdrop" data-action="close-modal"><div class="dialog" role="dialog" aria-modal="true" aria-label="${esc(title)}"><div class="modal-head"><div><h2>${esc(title)}</h2><p>${esc(description)}</p></div><button class="icon-btn" data-action="close-modal" aria-label="Cerrar">${ico('close',20)}</button></div><form data-form="${esc(kind)}" ${aux}><div class="modal-body">${body}</div><div class="modal-foot"><button type="button" class="btn btn-outline" data-action="close-modal">Cancelar</button><button type="submit" class="btn btn-primary">${ico('check',17)} ${esc(submitText)}</button></div></form></div></div>`;
}
function customModal(title,description,body){return `<div class="modal-backdrop" data-action="close-modal"><div class="dialog" role="dialog" aria-modal="true" aria-label="${esc(title)}"><div class="modal-head"><div><h2>${esc(title)}</h2><p>${esc(description)}</p></div><button class="icon-btn" data-action="close-modal">${ico('close',20)}</button></div><div class="modal-body">${body}</div><div class="modal-foot"><button class="btn btn-primary" data-action="close-modal">Cerrar</button></div></div></div>`}
function renderModal(){
 const m=state.modal;if(!m||!state.db)return '';
 const {kind,id,extra}=m;
 if(kind==='jugador'){
  const p=state.db.jugador.find(x=>+x.ci===+id)||{};return formModal(id?'Editar jugador':'Nuevo jugador','Datos personales y vinculación académica.',`<div class="form-grid">${inputField('Cédula','ci',p.ci||'','number',`required min="1" ${id?'readonly':''}`)}${selectField('Facultad','id_facultad',facOptions(),p.id_facultad||1,'required')}${inputField('Nombre','nombre',p.nombre||'','text','required minlength="2" maxlength="100"')}${inputField('Apellido','apellido',p.apellido||'','text','required minlength="2" maxlength="100"')}${inputField('Correo electrónico','email',p.email||'','email','required maxlength="150"')}${inputField('Fecha de nacimiento','fecha_nacimiento',p.fecha_nacimiento||'','date','required max="'+new Date().toISOString().slice(0,10)+'"')}${selectField('Tipo de jugador','tipo',['grado','posgrado','docente','funcionario'].map(x=>[x,x]),p.tipo||'grado','required')}</div>`,kind,id?'Guardar cambios':'Crear jugador');
 }
 if(kind==='equipo'){
  const p=state.db.equipo.find(x=>+x.id_equipo===+id)||{};const t=p.id_torneo||tId();return formModal(id?'Editar equipo':'Nuevo equipo','El capitán debe pertenecer a la facultad y al plantel.',`<div class="form-grid">${inputField('Nombre del equipo','nombre',p.nombre||'','text','required maxlength="100"')}${selectField('Edición','id_torneo',tourOptions(),t,id?'disabled':'required')}${selectField('Facultad','id_facultad',facOptions(),p.id_facultad||1,id?'disabled':'required')}${selectField('Capitán','ci_capitan',playerOptions(),p.ci_capitan||state.db.jugador[0]?.ci,'required')}</div>${!id?'<div class="info-strip small">El capitán se agrega al plantel con camiseta 1 al crear el equipo. Después podés agregar el resto de jugadores desde «Ver plantel».</div>':''}`,kind,id?'Guardar cambios':'Crear equipo');
 }
 if(kind==='roster'){
  const eq=state.db.equipo.find(e=>+e.id_equipo===+id);if(!eq)return '';
  const roster=state.db.equipo_jugador_torneo.filter(x=>+x.id_equipo===+id&&+x.id_torneo===+eq.id_torneo).sort((a,b)=>a.numero_camiseta-b.numero_camiseta);
  const canEdit=admin()&&state.db.torneo.find(t=>+t.id_torneo===+eq.id_torneo)?.estado==='inscripción';
  const ids=state.db.equipo_jugador_torneo.filter(x=>+x.id_torneo===+eq.id_torneo).map(x=>+x.ci_jugador);
  const available=state.db.jugador.filter(j=>+j.id_facultad===+eq.id_facultad&&!ids.includes(+j.ci));
  return `<div class="modal-backdrop" data-action="close-modal"><div class="dialog" role="dialog" aria-modal="true"><div class="modal-head"><div><h2>Plantel · ${esc(eq.nombre)}</h2><p>${esc(facultyName(eq.id_facultad))} · ${roster.length} / 10 jugadores</p></div><button class="icon-btn" data-action="close-modal">${ico('close',20)}</button></div><div class="modal-body"><div class="roster-rows">${roster.map(r=>`<div class="roster-line"><span class="jersey-num">${r.numero_camiseta}</span><div><strong>${esc(playerName(r.ci_jugador))}</strong><span>${esc(state.db.jugador.find(j=>+j.ci===+r.ci_jugador)?.tipo||'')}</span></div>${+eq.ci_capitan===+r.ci_jugador?'<span class="tiny-tag green">Capitán</span>':''}${canEdit?iconBtn('edit-jersey',`${eq.id_equipo}|${r.ci_jugador}`,'pencil','Cambiar dorsal'):''}${canEdit&&+eq.ci_capitan!==+r.ci_jugador?iconBtn('remove-roster',`${eq.id_equipo}|${r.ci_jugador}`,'trash','Quitar del plantel'):''}</div>`).join('')}</div>${canEdit?`<form data-form="roster-add" class="roster-add-form"><h3>Agregar jugador</h3><div class="form-grid">${selectField('Jugador','ci_jugador',available.map(j=>[j.ci,`${j.nombre} ${j.apellido} (${j.tipo})`]),'', 'required')}${inputField('Número de camiseta','numero_camiseta','','number','required min="1" max="99"')}</div><button class="btn btn-primary" type="submit" ${available.length===0?'disabled':''}>${ico('plus',17)} Agregar al plantel</button></form>`:`<div class="info-strip small">${ico('lock',16)} Plantel solo editable durante inscripción por un administrador.</div>`}</div><div class="modal-foot"><button class="btn btn-primary" data-action="close-modal">Listo</button></div></div></div>`;
 }
 if(kind==='partido'){
  const p=state.db.partido.find(x=>+x.id_partido===+id)||{};const cs=state.db.cancha;
  return formModal(id?'Editar partido':'Programar partido','Las restricciones de rivales, fecha y cancha se validan antes de guardar.',`<div class="form-grid">${inputField('Número de fecha','numero_fecha',p.numero_fecha||'','number','required min="1"')}${inputField('Día del partido','dia',p.dia||'','date','required')}${selectField('Equipo local','id_equipo_local',teams().map(e=>[e.id_equipo,e.nombre]),p.id_equipo_local||teams()[0]?.id_equipo,'required')}${selectField('Equipo visitante','id_equipo_visitante',teams().map(e=>[e.id_equipo,e.nombre]),p.id_equipo_visitante||teams()[1]?.id_equipo,'required')}${selectField('Turno','id_turno',state.db.turno.map(t=>[t.id_turno,`${timeHM(t.hora_inicio)}–${timeHM(t.hora_fin)}`]),p.id_turno||1,'required')}${selectField('Cancha','cancha_compuesta',cs.map(c=>[`${c.id_complejo}|${c.nombre_cancha}`,`${c.nombre_cancha} · ${state.db.complejo.find(v=>+v.id_complejo===+c.id_complejo)?.nombre||''}`]),`${p.id_complejo||cs[0]?.id_complejo}|${p.nombre_cancha||cs[0]?.nombre_cancha}`,'required')}${selectField('Estado','estado',['programado','postergado','cancelado','jugado'].map(x=>[x,x]),p.estado||'programado','required')}</div><div class="info-strip small">${ico('info',16)} No se permiten encuentros repetidos, equipos con menos de 5 jugadores, ni reservas de cancha superpuestas.</div>`,kind,id?'Actualizar partido':'Crear partido');
 }
 if(kind==='planilla'){
  const match=state.db.partido.find(x=>+x.id_partido===+id);if(!match)return '';
  const turn=state.db.turno.find(t=>+t.id_turno===+match.id_turno);const ended=new Date(`${match.dia}T${turn?.hora_fin||'23:00'}`);
  const editing=match.estado==='jugado'&&new Date()>=ended&&new Date().getTime()-ended.getTime()<=48*3600e3;
  const selected=state.db.planilla_partido.filter(x=>+x.id_partido===+id);
  const scores=goalResult(state.db,match);
  const goals=state.db.gol.filter(x=>+x.id_partido===+id).sort((a,b)=>a.minuto-b.minuto);
  const cards=state.db.tarjeta.filter(x=>+x.id_partido===+id).sort((a,b)=>a.minuto-b.minuto);
  return `<div class="modal-backdrop" data-action="close-modal"><div class="dialog dialog-large" role="dialog" aria-modal="true"><div class="modal-head"><div><h2>Planilla del partido #${id}</h2><p>Fecha ${match.numero_fecha} · ${fmtDate(match.dia)} · ${esc(teamName(match.id_equipo_local))} vs. ${esc(teamName(match.id_equipo_visitante))}</p></div><button class="icon-btn" data-action="close-modal">${ico('close',20)}</button></div><div class="modal-body"><div class="sheet-score"><span>${esc(teamName(match.id_equipo_local))}</span><strong>${match.estado==='jugado'?scores.local:'–'} : ${match.estado==='jugado'?scores.visitante:'–'}</strong><span>${esc(teamName(match.id_equipo_visitante))}</span></div>${!editing?`<div class="info-strip small">${ico('lock',16)} ${match.estado!=='jugado'?'El registro de la planilla se habilita cuando el partido está jugado y el turno ha terminado.':'Se cerró la ventana de 48 horas para editar esta planilla.'} Podés consultar los datos existentes.</div>`:''}<form data-form="planilla" class="sheet-form"><div class="sheet-rosters">${[match.id_equipo_local,match.id_equipo_visitante].map(teamId=>`<div><h3>${esc(teamName(teamId))}</h3>${state.db.equipo_jugador_torneo.filter(x=>+x.id_equipo===+teamId&&+x.id_torneo===+match.id_torneo).map(r=>{const checked=selected.some(s=>+s.ci_jugador===+r.ci_jugador);const suspended=isSuspended(state.db,match.id_torneo,r.ci_jugador,match.numero_fecha);return `<label class="sheet-player"><input type="checkbox" name="participant" value="${r.ci_jugador}|${teamId}" ${checked?'checked':''} ${!editing||suspended?'disabled':''}/><span>${esc(playerName(r.ci_jugador))}</span>${suspended?'<small class="red-text">Suspendido</small>':`<small>#${r.numero_camiseta}</small>`}</label>`}).join('')}</div>`).join('')}</div>${editing?'<button type="submit" class="btn btn-primary">'+ico('check',17)+' Guardar planilla</button>':''}</form><div class="sheet-events"><div><div class="sheet-event-head"><h3>Goles (${goals.length})</h3>${editing?actionBtn('Agregar gol','new-goal',id,'outline','plus'):''}</div>${goals.map(g=>`<div class="event-item"><span class="event-icon">${ico('football',15)}</span><span>${esc(playerName(g.ci_jugador))} ${g.autogol?'<small>(autogol)</small>':''}</span><strong>${g.minuto}′</strong>${editing?iconBtn('edit-goal',`${id}|${g.id_gol}`,'pencil','Corregir gol')+iconBtn('delete-goal',`${id}|${g.id_gol}`,'trash','Eliminar gol'):''}</div>`).join('')||'<div class="small-muted">No se registraron goles.</div>'}</div><div><div class="sheet-event-head"><h3>Tarjetas (${cards.length})</h3>${editing?actionBtn('Agregar tarjeta','new-card',id,'outline','plus'):''}</div>${cards.map(c=>`<div class="event-item"><span class="card-indicator ${c.color}"></span><span>${esc(playerName(c.ci_jugador))}</span><strong>${c.minuto}′</strong>${editing?iconBtn('edit-card',`${id}|${c.id_tarjeta}`,'pencil','Corregir tarjeta')+iconBtn('delete-card',`${id}|${c.id_tarjeta}`,'trash','Eliminar tarjeta'):''}</div>`).join('')||'<div class="small-muted">No se registraron tarjetas.</div>'}</div></div></div><div class="modal-foot"><button class="btn btn-primary" data-action="close-modal">Cerrar</button></div></div></div>`;
 }
 if(kind==='goal'||kind==='card'){
  const record=extra?(kind==='goal'?state.db.gol:state.db.tarjeta).find(x=>+(kind==='goal'?x.id_gol:x.id_tarjeta)===+extra):null;
  const part=state.db.planilla_partido.filter(p=>+p.id_partido===+id);
  const common=`<div class="form-grid">${selectField('Jugador que figura en planilla','ci_jugador',part.map(p=>[p.ci_jugador,`${playerName(p.ci_jugador)} · ${teamName(p.id_equipo)}`]),record?.ci_jugador||'','required')}${inputField('Minuto de juego','minuto',record?.minuto??'','number','required min="0" max="60"')}`;
  const custom=kind==='goal'?selectField('Tipo de gol','autogol',[['false','Gol normal'],['true','Autogol']],String(Boolean(record?.autogol)),'required'):selectField('Color de tarjeta','color',[['amarilla','Amarilla'],['roja','Roja']],record?.color||'amarilla','required');
  return formModal(kind==='goal'?(record?'Corregir gol':'Registrar gol'):(record?'Corregir tarjeta':'Registrar tarjeta'),'El jugador debe haber participado en el partido.',common+custom+'</div>',kind,record?'Guardar corrección':(kind==='goal'?'Registrar gol':'Registrar tarjeta'));
 }
 if(kind==='jersey'){
  const row=state.db.equipo_jugador_torneo.find(x=>+x.id_equipo===+id&&+x.ci_jugador===+extra);if(!row)return '';
  return formModal('Cambiar número de camiseta',playerName(extra),inputField('Nuevo dorsal','numero_camiseta',row.numero_camiseta,'number','required min="1" max="99"'),kind,'Actualizar dorsal');
 }
 if(kind==='complejo'){
  const p=state.db.complejo.find(x=>+x.id_complejo===+id)||{};
  return formModal(id?'Editar complejo':'Nuevo complejo','Datos de ubicación del complejo deportivo.',`<div class="form-grid">${inputField('Nombre','nombre',p.nombre||'','text','required maxlength="100"')}${inputField('Departamento','departamento',p.departamento||'Montevideo','text','required maxlength="100"')}${inputField('Dirección','direccion',p.direccion||'','text','required maxlength="150"')}</div>`,kind,id?'Guardar cambios':'Crear complejo');
 }
 if(kind==='cancha'){
  const [cid,cname]=String(id||'').includes('|')?String(id).split('|'):[String(extra||state.db.complejo[0]?.id_complejo||''),''];
  const p=state.db.cancha.find(x=>+x.id_complejo===+cid&&x.nombre_cancha===cname)||{};
  return formModal(cname?'Editar cancha':'Nueva cancha','Superficie y techado de la cancha.',`<div class="form-grid">${selectField('Complejo','id_complejo',state.db.complejo.map(c=>[c.id_complejo,c.nombre]),cid,cname?'disabled':'required')}${inputField('Nombre de cancha','nombre_cancha',p.nombre_cancha||'','text',`required maxlength="100" ${cname?'readonly':''}`)}${selectField('Superficie','superficie',[['sintético','Sintético'],['parquet','Parquet']],p.superficie||'sintético')}${selectField('¿Es techada?','techada',[['true','Sí'],['false','No']],String(p.techada??false))}</div>`,kind,cname?'Guardar cambios':'Crear cancha');
 }
 if(kind==='torneo'){
  const p=state.db.torneo.find(x=>+x.id_torneo===+id)||{};
  return formModal(id?'Editar edición':'Nueva edición','Año, semestre y período de competición.',`<div class="form-grid">${inputField('Nombre de la edición','nombre',p.nombre||'','text','required maxlength="150"')}${inputField('Año','anio',p.anio||2027,'number','required min="2000" max="2100"')}${selectField('Semestre','semestre',[[1,'1'],[2,'2']],p.semestre||1)}${selectField('Estado','estado',[['inscripción','Inscripción'],['en curso','En curso'],['finalizado','Finalizado']],p.estado||'inscripción',id?'':'disabled')}${inputField('Fecha de inicio','fecha_inicio',p.fecha_inicio||'','date','required')}${inputField('Fecha de fin','fecha_fin',p.fecha_fin||'','date','required')}</div>`,kind,id?'Guardar cambios':'Crear edición');
 }
 if(kind==='sancion_jugador'){
  const p=state.db.sancion_jugador.find(x=>+x.id_sancion===+id)||{};
  return formModal(id?'Editar sanción disciplinaria':'Nueva sanción disciplinaria','Las sanciones por tarjetas se generan automáticamente.',`<div class="form-grid">${selectField('Jugador inscripto','ci_jugador',playerOptions(true),p.ci_jugador||'','required')}${inputField('Número de fecha inicial','numero_fecha_inicio',p.numero_fecha_inicio||'','number','required min="1"')}${inputField('Cantidad de fechas','cantidad_fechas',p.cantidad_fechas||1,'number','required min="1"')}</div><div class="info-strip small">${ico('shield',16)} No se puede sancionar a quien ya tiene una planilla registrada para esas fechas.</div>`,kind,id?'Guardar sanción':'Aplicar sanción');
 }
 return '';
}
function loginView(){
 return `<div class="login-screen theme-${state.theme}"><div class="login-art"><div class="login-logo">${ico('football',28)} <strong>UCU <span>LEAGUE</span></strong></div><div class="login-art-content"><span class="eyebrow">TORNEO INTERFACULTADES DE FÚTBOL 5</span><h1>Una liga.<br/>Todas las<br/><em>facultades.</em></h1><p>La plataforma de gestión de partidos, planteles, resultados y estadísticas.</p></div><div class="login-pitch"><div class="pitch-center"></div></div><span class="login-footnote">BASE DE DATOS 1 · SEGUNDO SEMESTRE 2026</span></div><div class="login-form-area"><div class="login-form-card"><div class="eyebrow">${isDemo()?'MODO DEMOSTRACIÓN':'CONEXIÓN CON API PYTHON'}</div><h2>Bienvenido al torneo</h2><p>${isDemo()?'Elegí un rol para probar la interfaz. No se solicitan credenciales reales en modo demostración.':'Ingresá con tu usuario de la aplicación para conectar con el backend.'}</p>${isDemo()?`<div class="demo-login-options"><button class="login-role" data-action="login-demo" data-id="administrador"><span class="role-icon">${ico('shield',22)}</span><span><strong>Entrar como administrador</strong><small>Gestionar toda la competición</small></span>${ico('arrow',20)}</button><button class="login-role" data-action="login-demo" data-id="planillero"><span class="role-icon alternate">${ico('fixture',22)}</span><span><strong>Entrar como planillero</strong><small>Consultar y registrar partidos</small></span>${ico('arrow',20)}</button></div>`:`<form id="login-form"><label class="form-field"><span>Correo electrónico</span><input type="email" name="correo" placeholder="usuario@ucu.edu.uy" autocomplete="username" required/></label><label class="form-field"><span>Contraseña</span><input type="password" name="contrasena" placeholder="Contraseña" autocomplete="current-password" required/></label><button class="btn btn-primary login-submit" type="submit">${ico('arrow',18)} Iniciar sesión</button></form>`}${state.error?`<div class="login-error">${ico('alert',18)} ${esc(state.error)}</div>`:''}<div class="login-switch"><span>${isDemo()?'¿Ya tienen el backend funcionando?':'¿Todavía están desarrollando la API?'}</span><button data-action="toggle-mode">${isDemo()?'Usar backend Python':'Volver a la demostración'}</button></div></div></div></div>`;
}
function clearFieldErrors(form){
 if(!form)return;
 form.querySelectorAll('[aria-invalid="true"]').forEach(el=>el.removeAttribute('aria-invalid'));
 form.querySelectorAll('.field-error,.validation-summary').forEach(el=>el.remove());
}
function showFieldErrors(form,issues){
 if(!form||!issues?.length)return;
 clearFieldErrors(form);
 const summary=document.createElement('div');summary.className='validation-summary';summary.setAttribute('role','alert');
 summary.textContent='Revisá los campos señalados antes de guardar. ' + issues.map(x=>x.message).join(' ');
 const body=form.querySelector('.modal-body')||form;
 body.prepend(summary);
 for(const issue of issues){
  if(!issue.field)continue;
  const input=[...form.elements].find(el=>el.name===issue.field);
  if(!input)continue;
  input.setAttribute('aria-invalid','true');
  const label=input.closest('.form-field');
  if(label){const text=document.createElement('small');text.className='field-error';text.textContent=issue.message;label.append(text);}
 }
 const first=form.querySelector('[aria-invalid="true"]');
 (first||summary).focus?.();
}
function notify(msg,type='success'){
 state.toast={msg,type};const area=document.getElementById('toast-area');if(area)area.innerHTML=`<div class="toast toast-${type}">${ico(type==='error'?'alert':'check',18)}${esc(msg)}<button data-action="clear-toast" class="toast-close">${ico('close',15)}</button></div>`;
}
const rerender=()=>{app.innerHTML=layout();document.documentElement.dataset.theme=state.theme};
const rerenderContent=()=>{const el=document.getElementById('main-body');if(el)el.innerHTML=content()};
const rerenderModal=()=>{const old=document.querySelector('.modal-backdrop');if(old)old.outerHTML=renderModal()};
async function refreshReport(){if(state.page!=='reportes'||!state.db)return;state.reportLoading=true;rerenderContent();try{state.reportRows=await loadReport(state.report,tId(),state.db)}catch(e){state.reportRows=[];notify(e.message,'error')}finally{state.reportLoading=false;rerenderContent()}}
function navigate(page){state.page=page;state.menuOpen=false;state.search='';window.location.hash=page;rerender();if(page==='reportes')refreshReport();window.scrollTo({top:0,behavior:'smooth'})}
function open(kind,id='',extra=''){state.modal={kind,id,extra};rerenderModalOrFull()}
function rerenderModalOrFull(){const existing=document.querySelector('.modal-backdrop');if(existing)existing.remove();if(state.modal)document.querySelector('.shell')?.insertAdjacentHTML('beforeend',renderModal())}
async function commit(kind,action,body,options={}){
 try{
  if(!canModify(state.user?.rol,kind,action))throw Error('Esta operación no está permitida para tu rol.');
  state.db=await mutate(state.db,kind,action,body);
  if(!options.keepModal)state.modal=null;
  rerender();if(state.page==='reportes')refreshReport();notify(options.message||'Cambios guardados correctamente.');
  return true;
 }catch(e){
  if(e.issues)showFieldErrors(document.querySelector('.modal-backdrop form[data-form]'),e.issues);
  notify(e.message,'error');
  return false;
 }
}
async function handleAction(a,id){
 if(a.startsWith('page-')){navigate(a.slice(5));return}
 if(a==='menu'){state.menuOpen=!state.menuOpen;rerender();return}
 if(a==='close-menu'){state.menuOpen=false;rerender();return}
 if(a==='theme'){state.theme=state.theme==='dark'?'light':'dark';localStorage.setItem('ucu_theme',state.theme);rerender();return}
 if(a==='clear-toast'){state.toast=null;document.getElementById('toast-area').innerHTML='';return}
 if(a==='close-modal'){state.modal=null;rerenderModalOrFull();return}
 if(a==='switch-user'){logout();state.user=null;state.modal=null;rerender();return}
 if(a==='toggle-mode'){
  setMode(isDemo()?'api':'demo');state.error='';state.user=isDemo()?demoUser():null;state.db=null;
  if(state.user)try{state.db=await loadData()}catch(e){state.error=e.message}
  rerender();return;
 }
 if(a==='login-demo') {state.user=demoUser(id==='planillero'?'planillero':'administrador');state.error='';if(!state.db)state.db=await loadData();rerender();return}
 if(!state.user)return;
 if(a==='reset-demo') {if(window.confirm('¿Reiniciar todos los cambios de demostración realizados en este navegador?')){demoReset();state.db=await loadData();rerender();notify('Datos del SQL restaurados.')}return}
 if(a==='fixture-filter'){state.status=id;rerenderContent();return}
 if(a==='report'){state.report=id;state.reportRows=[];refreshReport();return}
 if(a==='export-report'){
  const fields=reportFields[state.report]||[];const cell=(v)=>{let s=String(v??'');if(typeof v!=='number'&&/^[=+@\-\t\r]/.test(s))s="'"+s;return `"${s.replaceAll('\"','\"\"')}"`};const csv=[fields.map(f=>f[1]).join(';'),...state.reportRows.map(row=>fields.map(([key])=>cell(row[key])).join(';'))].join('\r\n');
  const url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=`ucu_${state.report}_${tId()}.csv`;document.body.append(link);link.click();link.remove();URL.revokeObjectURL(url);notify('Reporte CSV generado.');return;
 }
 if(a==='select-torneo'){state.tournament=+id;navigate('dashboard');return}
 if(a==='view-planilla'){open('planilla',id);return}
 if(a==='roster'){open('roster',id);return}
 if(a==='new-goal'){open('goal',id);return}
 if(a==='new-card'){open('card',id);return}
 if(a==='edit-goal'||a==='edit-card'){const [match,record]=id.split('|');open(a==='edit-goal'?'goal':'card',match,record);return}
 if(a==='edit-jersey'){if(!admin())return notify('No tenés permisos.','error');const [team,ci]=id.split('|');open('jersey',team,ci);return}
 if(a==='delete-goal'||a==='delete-card'){
  const [matchId,recordId]=id.split('|').map(Number);if(!window.confirm(`¿Eliminar ${a==='delete-goal'?'este gol':'esta tarjeta'}?`))return;
  const action=a==='delete-goal'?'goal-delete':'card-delete';await commit('',action,{id_partido:matchId,...(a==='delete-goal'?{id_gol:recordId}:{id_tarjeta:recordId})},{keepModal:true});state.modal={kind:'planilla',id:matchId};rerenderModalOrFull();return;
 }
 if(a==='remove-roster'){
  if(!admin())return notify('No tenés permisos.','error');const [team,ci]=id.split('|').map(Number);if(!window.confirm('¿Quitar a este jugador del plantel?'))return;
  await commit('', 'roster-remove',{id_equipo:team,ci_jugador:ci},{keepModal:true});state.modal={kind:'roster',id:team};rerenderModalOrFull();return;
 }
 if(a.startsWith('delete-')){
  if(!admin())return notify('No tenés permisos.','error');const kind=a.slice(7);const key={jugador:'ci',partido:'id_partido',sancion:'id_sancion',equipo:'id_equipo',complejo:'id_complejo'}[kind];const resource=kind==='sancion'?'sancion_jugador':kind;
  if(kind==='cancha'){const [cid,name]=id.split('|');if(window.confirm('¿Eliminar esta cancha?'))await commit('cancha','remove',{id_complejo:Number(cid),nombre_cancha:name});return;}
  if(!key)return;
  if(window.confirm('¿Eliminar este registro? Esta acción no puede deshacerse.'))await commit(resource,'remove',{[key]:Number(id)});return;
 }
 if(a.startsWith('new-')||a.startsWith('edit-')){
  if(!admin())return notify('Esta acción requiere permisos de administrador.','error');
  const editing=a.startsWith('edit-'),kind=a.slice(editing?5:4);
  if(kind==='cancha'&&a==='new-cancha'){open(kind,'',id);return}
  open(kind,editing?id:'');return;
 }
}
function formNumbers(body,fields){for(const f of fields)if(body[f]!==undefined&&body[f]!=='')body[f]=Number(body[f]);return body}
async function handleForm(form){
 const kind=form.dataset.form;const data=Object.fromEntries(new FormData(form).entries());
 if(kind==='roster-add'){
  const team=Number(state.modal?.id);formNumbers(data,['ci_jugador','numero_camiseta']);if(await commit('', 'roster-add',{id_equipo:team,...data},{keepModal:true})){state.modal={kind:'roster',id:team};rerenderModalOrFull();}return;
 }
 if(kind==='planilla'){
  const id=Number(state.modal.id);const participantes=[...form.querySelectorAll('input[name=participant]:checked')].map(i=>{const [ci_jugador,id_equipo]=i.value.split('|').map(Number);return {ci_jugador,id_equipo}});
  if(await commit('','planilla-save',{id_partido:id,participantes},{keepModal:true})){state.modal={kind:'planilla',id};rerenderModalOrFull();}return;
 }
 if(kind==='goal'||kind==='card'){
  const id=Number(state.modal.id);const editing=Boolean(state.modal.extra);formNumbers(data,['ci_jugador','minuto']);const action=kind==='goal'?(editing?'goal-update':'goal-create'):(editing?'card-update':'card-create');if(kind==='goal')data.autogol=data.autogol==='true';
  const current={...data,id_partido:id,...(editing?{[kind==='goal'?'id_gol':'id_tarjeta']:Number(state.modal.extra)}:{})};if(await commit('',action,current,{keepModal:true})){state.modal={kind:'planilla',id};rerenderModalOrFull();}return;
 }
 if(kind==='jersey'){const team=Number(state.modal.id),ci=Number(state.modal.extra);formNumbers(data,['numero_camiseta']);if(await commit('','roster-update',{id_equipo:team,ci_jugador:ci,...data},{keepModal:true})){state.modal={kind:'roster',id:team};rerenderModalOrFull();}return;}
 const id=state.modal?.id;const editing=id!==''&&id!==null&&id!==undefined;let current={};
 const keys={jugador:'ci',equipo:'id_equipo',partido:'id_partido',torneo:'id_torneo',complejo:'id_complejo',cancha:'nombre_cancha',sancion_jugador:'id_sancion'};
 if(editing&&kind==='cancha'){
  const [cid,cname]=String(id).split('|');current=state.db.cancha.find(x=>+x.id_complejo===+cid&&x.nombre_cancha===cname)||{};
 }else if(editing)current=state.db[kind]?.find(x=>String(x[keys[kind]])===String(id))||{};
 const disabled={};if(kind==='equipo'&&editing){disabled.id_facultad=current.id_facultad;disabled.id_torneo=current.id_torneo}
 if(kind==='cancha'&&editing)disabled.id_complejo=current.id_complejo;
 if(kind==='torneo'&&!editing)data.estado='inscripción';
 if(kind==='partido'){
  const [id_complejo,nombre_cancha]=(data.cancha_compuesta||'').split('|');data.id_complejo=Number(id_complejo);data.nombre_cancha=nombre_cancha;delete data.cancha_compuesta;data.id_torneo=tId();
 }
 if(kind==='cancha')data.techada=data.techada==='true';
 if(kind==='sancion_jugador'){data.id_torneo=tId();data.motivo='disciplinaria';data.origen='manual'}
 Object.assign(data,disabled);
 formNumbers(data,{jugador:['ci','id_facultad'],equipo:['id_torneo','id_facultad','ci_capitan'],partido:['numero_fecha','id_equipo_local','id_equipo_visitante','id_turno','id_complejo'],torneo:['anio','semestre'],complejo:[],cancha:['id_complejo'],sancion_jugador:['ci_jugador','id_torneo','numero_fecha_inicio','cantidad_fechas']}[kind]||[]);
 if(editing){Object.assign(data,{[keys[kind]]:current[keys[kind]]});if(kind==='cancha')data.original_nombre_cancha=current.nombre_cancha}
 await commit(kind,editing?'update':'create',data);
}
app.addEventListener('click',async e=>{
 const page=e.target.closest('[data-page]');if(page){navigate(page.dataset.page);return}
 const target=e.target.closest('[data-action]');if(!target)return;
 if(target.classList.contains('modal-backdrop')&&target!==e.target)return;
 e.preventDefault();try{await handleAction(target.dataset.action,target.dataset.id||'')}catch(err){notify(err.message,'error')}
});
app.addEventListener('submit',async e=>{
 e.preventDefault();const form=e.target;
 if(form.id==='login-form'){
  const f=Object.fromEntries(new FormData(form));state.error='';const button=form.querySelector('button[type=submit]');button.disabled=true;try{state.user=await login(f.correo,f.contrasena);state.db=await loadData();state.tournament=state.db.torneo[0]?.id_torneo||1;rerender()}catch(err){logout();state.user=null;state.db=null;state.error=err.message;rerender()}return;
 }
 if(!state.user||!form.dataset.form)return;
 const allowed=['planilla','goal','card'];if(!admin()&&!allowed.includes(form.dataset.form)){notify('Acción restringida al administrador.','error');return}
 const submit=form.querySelector('[type=submit]');if(submit)submit.disabled=true;
 try{await handleForm(form)}catch(err){notify(err.message,'error')}finally{if(submit?.isConnected)submit.disabled=false}
});
app.addEventListener('input',e=>{
 if(e.target.id==='global-search'){state.search=e.target.value;rerenderContent();return;}
 if(e.target.closest('.modal-backdrop form[data-form]')){
  const form=e.target.closest('form');
  e.target.removeAttribute('aria-invalid');
  e.target.closest('.form-field')?.querySelector('.field-error')?.remove();
  form.querySelector('.validation-summary')?.remove();
 }
});
app.addEventListener('change',e=>{
 if(e.target.closest('.modal-backdrop form[data-form]')){
  e.target.removeAttribute('aria-invalid');
  e.target.closest('.form-field')?.querySelector('.field-error')?.remove();
  e.target.closest('form')?.querySelector('.validation-summary')?.remove();
 }
});
app.addEventListener('change',e=>{if(e.target.id==='tournament-picker'){state.tournament=Number(e.target.value);state.search='';rerender();if(state.page==='reportes')refreshReport()}});
window.addEventListener('hashchange',()=>{const page=window.location.hash.slice(1);if(titles[page]&&state.page!==page)navigate(page)});

async function init(){
 state.user=isDemo()?demoUser():getSavedUser();const page=window.location.hash.slice(1);state.page=titles[page]?page:'dashboard';
 if(state.user){try{state.db=await loadData();state.tournament=state.db.torneo[0]?.id_torneo||1;}catch(err){state.error=err.message;if(!isDemo())state.user=null;else app.innerHTML=`<div class="initial-loading">${esc(err.message)}</div>`}}
 state.loading=false;rerender();if(state.db&&state.page==='reportes')refreshReport();
}
init();
