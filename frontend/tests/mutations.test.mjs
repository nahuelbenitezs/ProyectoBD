import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {mutate} from '../js/repository.js';

// In the Node test environment, the demonstration repository needs a small localStorage stub.
const storage = new Map();
globalThis.localStorage = {getItem:key=>storage.get(key)??null,setItem:(key,value)=>storage.set(key,String(value)),removeItem:key=>storage.delete(key)};
const source=JSON.parse(fs.readFileSync(new URL('../js/seed.json',import.meta.url),'utf8'));
const fresh=()=>structuredClone(source);

test('ABM de jugador permite crear un registro no duplicado',async()=>{
 const row={ci:65432198,nombre:'Test',apellido:'Frontend',email:'testfrontend@example.edu.uy',fecha_nacimiento:'2000-01-01',id_facultad:1,tipo:'grado'};
 const updated=await mutate(fresh(),'jugador','create',row);
 assert.equal(updated.jugador.length,43);
 assert.equal(updated.jugador.at(-1).email,row.email);
});

test('ABM de jugador rechaza cédula duplicada',async()=>{
 const row={...source.jugador[0],email:'otro@example.edu.uy'};
 await assert.rejects(mutate(fresh(),'jugador','create',row),/Ya existe un jugador/);
});

test('un partido jugado no se puede eliminar',async()=>{
 await assert.rejects(mutate(fresh(),'partido','remove',{id_partido:1}),/partido jugado/);
});

test('fixture rechaza un enfrentamiento ya realizado',async()=>{
 const row={id_torneo:1,numero_fecha:6,id_equipo_local:1,id_equipo_visitante:6,dia:'2026-11-16',id_turno:1,nombre_cancha:'Cancha A',id_complejo:1,estado:'programado'};
 await assert.rejects(mutate(fresh(),'partido','create',row),/ya tienen un enfrentamiento/);
});

test('plantel no se puede cambiar fuera de inscripción',async()=>{
 await assert.rejects(mutate(fresh(),'','roster-add',{id_equipo:1,ci_jugador:50000107,numero_camiseta:9}),/durante inscripción/);
});

test('no se permite crear sanciones sobre fechas con planilla',async()=>{
 await assert.rejects(mutate(fresh(),'sancion_jugador','create',{ci_jugador:50000101,id_torneo:1,motivo:'disciplinaria',origen:'manual',numero_fecha_inicio:1,cantidad_fechas:1}),/se superpone con una planilla/);
});
