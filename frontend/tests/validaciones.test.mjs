import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateCommand,assertValid,ValidationError} from '../js/validation.js';
import {canModify} from '../js/permissions.js';
const fixture=JSON.parse(fs.readFileSync(new URL('../js/seed.json', import.meta.url),'utf8'));
const copy=()=>structuredClone(fixture);
const messages=(db,kind,action,p,now)=>validateCommand(db,kind,action,p,now).map(x=>x.message).join(' ');
const player=()=>({ci:65432189,nombre:'Ana',apellido:'Prueba',email:'ana.prueba@ucu.edu.uy',fecha_nacimiento:'2000-01-01',id_facultad:1,tipo:'grado'});
const future=()=>({id_torneo:1,numero_fecha:6,id_equipo_local:2,id_equipo_visitante:4,dia:'2026-11-10',id_turno:2,id_complejo:1,nombre_cancha:'Cancha A',estado:'programado'});

test('valida datos correctos de un jugador nuevo',()=>assert.equal(messages(copy(),'jugador','create',player()),''));
test('rechaza un correo repetido sin distinguir mayúsculas',()=>assert.match(messages(copy(),'jugador','create',{...player(),email:'SPEREIRA@example.edu.uy'}),/correo ya está registrado/));
test('rechaza cédulas, nombres y correos inválidos',()=>{
 const msg=messages(copy(),'jugador','create',{...player(),ci:34,nombre:'',apellido:'',email:'mal-correo'});
 assert.match(msg,/6 y 10 dígitos/);assert.match(msg,/nombre/);assert.match(msg,/apellido/);assert.match(msg,/correo electrónico/);
});
test('rechaza fechas inexistentes y nacimiento futuro',()=>{
 assert.match(messages(copy(),'jugador','create',{...player(),fecha_nacimiento:'2026-02-30'}),/fecha de nacimiento/);
 assert.match(messages(copy(),'jugador','create',{...player(),fecha_nacimiento:'2099-02-01'}),/fecha de nacimiento/);
});
test('no cambia facultad de un jugador que pertenece a un plantel',()=>{
 const db=copy();const existing=db.jugador[0];
 assert.match(messages(db,'jugador','update',{...existing,id_facultad:2}),/inscripto/);
});
test('torneo nuevo exige inscripción, fechas coherentes y semestre válido',()=>{
 const db=copy();const t={nombre:'Nueva edición',anio:2027,semestre:3,fecha_inicio:'2027-05-01',fecha_fin:'2027-04-01',estado:'finalizado'};
 const msg=messages(db,'torneo','create',t);assert.match(msg,/semestre/);assert.match(msg,/anterior al inicio/);assert.match(msg,/inscripción/);
});
test('no se puede reabrir una edición finalizada',()=>{
 const db=copy();db.torneo[0].estado='finalizado';
 assert.match(messages(db,'torneo','update',{...db.torneo[0],estado:'en curso'}),/retroceder/);
});
test('capitán debe ser de la facultad representada',()=>{
 const db=copy();db.torneo[0].estado='inscripción';
 assert.match(messages(db,'equipo','create',{nombre:'Otro',id_torneo:1,id_facultad:1,ci_capitan:50000201}),/capitán/);
});
test('no permite partidos entre un equipo y sí mismo',()=>assert.match(messages(copy(),'partido','create',{...future(),id_equipo_visitante:2}),/sí mismo/));
test('no repite rivales en la misma edición',()=>assert.match(messages(copy(),'partido','create',{...future(),id_equipo_local:1,id_equipo_visitante:6}),/ya tienen un enfrentamiento/));
test('no permite que un equipo dispute dos partidos de una misma fecha',()=>assert.match(messages(copy(),'partido','create',{...future(),numero_fecha:3}),/dos veces en la misma fecha/));
test('no permite doble reserva de cancha en día y turno',()=>assert.match(messages(copy(),'partido','create',{...future(),numero_fecha:4,dia:'2026-10-26',id_turno:1}),/cancha ya está reservada/));
test('exige al menos cinco jugadores y capitán en el plantel',()=>{
 const db=copy();db.equipo_jugador_torneo=db.equipo_jugador_torneo.filter(r=>r.id_equipo!==2||r.numero_camiseta<=4);
 assert.match(messages(db,'partido','create',future()),/al menos 5 jugadores/);
});
test('admite un fixture futuro válido',()=>assert.equal(messages(copy(),'partido','create',future()),''));
test('bloquea un partido jugado antes de terminar su turno',()=>{
 const m={...future(),dia:'2026-11-05',estado:'jugado'};
 assert.match(messages(copy(),'partido','create',m,new Date('2026-11-05T18:30:00')),/después de finalizar/);
});
test('rechaza cargar goles de partidos jugados hace más de 48 horas',()=>assert.match(messages(copy(),'','goal-create',{id_partido:1,ci_jugador:50000101,minuto:30,autogol:false},new Date('2026-10-31T12:00:00')),/48 horas/));
test('minuto de un gol debe estar entre 0 y 60',()=>assert.match(messages(copy(),'','goal-create',{id_partido:1,ci_jugador:50000101,minuto:61,autogol:false},new Date('2026-10-05T20:00:00')),/0 y 60/));
test('los goles exigen que el jugador haya figurado en la planilla',()=>assert.match(messages(copy(),'','goal-create',{id_partido:1,ci_jugador:50000107,minuto:32,autogol:false},new Date('2026-10-05T20:00:00')),/incluido en la planilla/));
test('solo admite tarjetas amarillas o rojas',()=>assert.match(messages(copy(),'','card-create',{id_partido:1,ci_jugador:50000101,minuto:22,color:'azul'},new Date('2026-10-05T20:00:00')),/amarilla o roja/));
test('la planilla rechaza jugadores suspendidos por una tarjeta roja',()=>{
 const db=copy();const p={id_partido:4,participantes:[{ci_jugador:50000103,id_equipo:1}]};
 assert.match(messages(db,'','planilla-save',p,new Date('2026-10-12T20:00:00')),/suspendidos/);
});
test('bloquea sanciones que coincidan con planillas históricas',()=>assert.match(messages(copy(),'sancion_jugador','create',{id_torneo:1,ci_jugador:50000101,motivo:'disciplinaria',origen:'manual',numero_fecha_inicio:1,cantidad_fechas:2}),/superpone/));
test('prohíbe usar una camiseta duplicada en el plantel',()=>{
 const db=copy();db.torneo[0].estado='inscripción';
 assert.match(messages(db,'','roster-add',{id_equipo:1,ci_jugador:50000108,numero_camiseta:1}),/camiseta ya se usa/);
});
test('limita a diez el tamaño del plantel',()=>{
 const db=copy();db.torneo[0].estado='inscripción';
 for(let i=8;i<=10;i++)db.equipo_jugador_torneo.push({id_equipo:1,ci_jugador:50000900+i,id_torneo:1,numero_camiseta:i});
 db.jugador.push({ci:50000111,nombre:'Prueba',apellido:'Plantel',email:'p@prueba.uy',fecha_nacimiento:'2000-01-01',id_facultad:1,tipo:'grado'});
 assert.match(messages(db,'','roster-add',{id_equipo:1,ci_jugador:50000111,numero_camiseta:11}),/más de 10/);
});
test('protege operaciones específicas según rol de presentación',()=>{
 assert.equal(canModify('administrador','jugador','create'),true);
 assert.equal(canModify('planillero','jugador','create'),false);
 assert.equal(canModify('planillero','','roster-add'),false);
 assert.equal(canModify('planillero','partido','remove'),false);
 assert.equal(canModify('planillero','','planilla-save'),true);
 assert.equal(canModify('planillero','','goal-create'),true);
 assert.equal(canModify('planillero','','card-delete'),true);
 assert.equal(canModify(undefined,'jugador','create'),false);
});
test('assertValid genera un error con detalles por campo',()=>{
 assert.throws(()=>assertValid(copy(),'jugador','create',{...player(),email:'invalido'}),err=>err instanceof ValidationError&&err.issues.some(x=>x.field==='email'));
});
