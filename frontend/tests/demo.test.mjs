import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {goalResult,generateReport,standings,sanctionsFor} from '../js/reports.js';

const seed = JSON.parse(fs.readFileSync(new URL('../js/seed.json',import.meta.url),'utf8'));
const reports = ['posiciones','goleadores','fair-play','promedio-goles','uso-espacios','jugadores-facultad','sin-participacion','sanciones','estados','local-visitante','disciplina','goles-tramos'];

test('datos de demostración coinciden con verificación SQL',()=>{
 assert.equal(seed.equipo.length,6);
 assert.equal(seed.jugador.length,42);
 assert.equal(seed.partido.length,13);
 assert.equal(seed.partido.filter(x=>x.estado==='jugado').length,10);
 assert.equal(seed.gol.length,30);
 assert.equal(seed.planilla_partido.length,100);
});

test('todos los reportes tienen resultados',()=>{
 assert.equal(reports.length,12);
 for(const slug of reports)assert.ok(generateReport(seed,slug,1).length>0,slug);
});

test('se computan correctamente goles, autogol y empate 0-0',()=>{
 const played=seed.partido.filter(p=>p.estado==='jugado');
 assert.equal(played.reduce((n,p)=>{const x=goalResult(seed,p);return n+x.local+x.visitante},0),30);
 const tie=played.find(p=>p.numero_fecha===4);
 assert.deepEqual(goalResult(seed,tie),{local:0,visitante:0});
 assert.equal(seed.gol.filter(g=>g.autogol).length,1);
});

test('puntos y criterios de desempate de la edición',()=>{
 const rows=standings(seed,1);
 assert.equal(rows.length,6);
 assert.equal(rows[0].equipo,'Halcones');
 assert.equal(rows[0].puntos,8);
 assert.equal(rows.find(x=>x.equipo==='Leones').empatados,2);
 assert.equal(rows.find(x=>x.equipo==='Leones').puntos,2);
});

test('fair play, sanciones y jugadores sin participación',()=>{
 assert.equal(generateReport(seed,'fair-play',1).reduce((n,x)=>n+x.puntos_fair_play,0),8);
 assert.equal(sanctionsFor(seed,1).length,3);
 assert.equal(generateReport(seed,'sin-participacion',1).length,10);
 assert.equal(generateReport(seed,'sanciones',1).reduce((n,x)=>n+x.cantidad_sanciones,0),3);
});

test('porcentaje de partidos clasifica jugados, postergados y cancelados',()=>{
 const rows=generateReport(seed,'estados',1);
 assert.deepEqual(Object.fromEntries(rows.map(x=>[x.estado,x.cantidad])),{jugado:10,postergado:1,cancelado:1,programado:1});
 assert.equal(rows.reduce((n,x)=>n+x.cantidad,0),13);
});
