#!/usr/bin/env python3
"""
generar_buscador_html.py
=========================
Ensambla `buscador_trenes.html` (fichero único, autocontenido) a partir del
payload de datos generado por build_buscador_data.py (`buscador_data.b64`).

No requiere red ni build steps adicionales: solo lee el .b64 y escribe el
HTML final con la plantilla (CSS+JS) embebida abajo.
"""
import datetime
import pathlib

B64_PATH = "buscador_data.b64"
OUT_HTML = "buscador_trenes.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>BuscaTrenes</title>
<style>
  :root{
    --bg:#0b1219; --panel:#151f2b; --panel2:#1e2b3a; --text:#e8edf2; --muted:#8fa1b3;
    --accent:#3b82f6; --accent2:#2563eb; --border:#263646;
    --av:#e5484d; --ld:#f0883e; --md:#2fbf71; --cer:#3a9bdc; --ouigo:#e6007e;
    --fgc:#2e7d32; --eus:#00838f; --sfm:#c77c02;
  }
  *{box-sizing:border-box}
  body{margin:0;color:var(--text);background:var(--bg);
       background-image:radial-gradient(900px 480px at 50% -10%, #16283c 0%, transparent 60%);
       background-repeat:no-repeat;
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
       -webkit-font-smoothing:antialiased;}
  .wrap{max-width:720px;margin:0 auto;padding:28px 14px 60px}
  h1{font-size:1.45rem;margin:34px 0 24px;letter-spacing:-.01em}
  .card{background:linear-gradient(180deg,var(--panel) 0%,#121b26 100%);
        border:1px solid var(--border);border-radius:16px;padding:18px 16px;
        margin-bottom:14px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
  label{display:block;font-size:.72rem;color:var(--muted);margin:12px 0 5px;
        text-transform:uppercase;letter-spacing:.08em}
  label:first-child{margin-top:0}
  .row{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
  .row > div{flex:1 1 130px;min-width:0}
  input[type=text],input[type=date],input[type=time],input[type=number],select{
    width:100%;padding:12px 13px;border-radius:11px;border:1px solid var(--border);
    background:var(--panel2);color:var(--text);font-size:16px;
    transition:border-color .15s, box-shadow .15s;
  }
  input:focus,select:focus{outline:none;border-color:var(--accent);
    box-shadow:0 0 0 3px rgba(59,130,246,.25)}
  .autocomplete{position:relative}
  .sugg{position:absolute;left:0;right:0;top:calc(100% + 4px);background:var(--panel2);
        border:1px solid var(--border);border-radius:12px;max-height:220px;overflow:auto;
        z-index:20;display:none;box-shadow:0 14px 32px rgba(0,0,0,.5)}
  .sugg div{padding:10px 12px;font-size:.92rem;cursor:pointer;border-bottom:1px solid var(--border)}
  .sugg div:last-child{border-bottom:none}
  .sugg div:hover, .sugg div.active{background:#2f4356}
  .sugg small{color:var(--muted)}
  .geobtn{margin-top:8px;background:rgba(59,130,246,.08);
          border:1px solid rgba(59,130,246,.4);color:var(--accent);
          padding:8px 14px;border-radius:999px;font-size:.8rem;cursor:pointer}
  .geobtn:active{background:rgba(59,130,246,.2)}
  .geostatus{font-size:.78rem;color:var(--muted);margin-top:4px;min-height:1em}
  .chk{display:flex;align-items:center;gap:8px;margin-top:14px;font-size:.85rem;color:var(--muted)}
  .chk input{width:16px;height:16px;accent-color:var(--accent)}
  .chk label{text-transform:none;letter-spacing:0;font-size:.85rem}
  button.buscar{width:100%;margin-top:18px;padding:14px;border:none;border-radius:12px;
    background:linear-gradient(180deg,var(--accent),var(--accent2));color:#fff;
    font-size:1.02rem;font-weight:700;letter-spacing:.02em;cursor:pointer;
    box-shadow:0 6px 18px rgba(37,99,235,.35)}
  button.buscar:active{transform:translateY(1px);box-shadow:0 3px 10px rgba(37,99,235,.3)}
  button.buscar:disabled{opacity:.5;box-shadow:none}
  #estado{color:var(--muted);font-size:.85rem;margin:14px 0}
  .resultado{background:linear-gradient(180deg,var(--panel) 0%,#121b26 100%);
    border:1px solid var(--border);border-radius:14px;
    padding:14px 15px;margin-bottom:12px;box-shadow:0 6px 18px rgba(0,0,0,.25)}
  .rescab{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px}
  .badge{font-size:.7rem;font-weight:800;color:#fff;padding:3px 10px;border-radius:999px;letter-spacing:.06em}
  .badge.AV{background:var(--av)} .badge.LD{background:var(--ld)}
  .badge.MD{background:var(--md)} .badge.CER{background:var(--cer)}
  .badge.OUIGO{background:var(--ouigo)}
  .badge.FGC{background:var(--fgc)} .badge.EUS{background:var(--eus)}
  .badge.SFM{background:var(--sfm)}
  .tren{font-weight:700}
  .linea{color:var(--muted);font-size:.85rem}
  .horas{display:flex;align-items:center;gap:12px;font-size:1.12rem;margin:8px 0}
  .horas .hh{font-weight:800;font-variant-numeric:tabular-nums}
  .horas .st{font-size:.76rem;color:var(--muted);font-weight:400;display:block;margin-top:1px}
  .flecha{color:var(--accent);font-weight:700}
  .meta{font-size:.78rem;color:var(--muted);margin-top:4px}
  details{margin-top:8px;font-size:.85rem}
  summary{cursor:pointer;color:var(--accent)}
  .parada{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px dashed var(--border);font-size:.83rem}
  .parada:last-child{border-bottom:none}
  .vacio{color:var(--muted);text-align:center;padding:24px 10px}
  .sharebtn{margin-left:auto;background:none;border:1px solid var(--border);
    color:var(--muted);border-radius:999px;padding:4px 11px;font-size:.72rem;cursor:pointer}
  .sharebtn:active{background:var(--panel2);color:var(--text)}
  .resfoot{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:8px}
  .resfoot .meta{margin-top:0}
  #toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);
    background:#2f4356;color:var(--text);padding:9px 16px;border-radius:999px;
    font-size:.82rem;box-shadow:0 8px 22px rgba(0,0,0,.45);opacity:0;
    pointer-events:none;transition:opacity .25s;z-index:50;white-space:nowrap}
  #toast.visible{opacity:1}
  .transbordo{margin:8px 0;padding:8px 12px;line-height:1.5;
    border-left:3px solid var(--accent);background:rgba(59,130,246,.07);
    border-radius:8px;font-size:.82rem;color:var(--muted)}
  .transbordo b{color:var(--text)}
  .tabs{display:flex;gap:5px;margin-bottom:16px;flex-wrap:wrap}
  .tab{flex:1 1 auto;padding:10px 4px;border-radius:10px;border:1px solid #2a4a6e;
    background:#16324f;color:#b9cde4;font-size:.75rem;font-weight:700;
    cursor:pointer;text-align:center;white-space:nowrap}
  .tab.active{background:rgba(59,130,246,.3);border-color:var(--accent);color:#fff}
  .tab[hidden]{display:none}
  .tabpanel{display:none}
  .tabpanel.active{display:block}
  .incidencia{margin:8px 0 0;padding:8px 12px;line-height:1.45;
    border-left:3px solid #f0b429;background:rgba(240,180,41,.08);
    border-radius:8px;font-size:.8rem;color:var(--muted)}
  .incidencia b{color:var(--text)}
  .leg{padding:4px 0}
  .leg + .leg{border-top:none}
  footer{color:var(--muted);font-size:.72rem;text-align:center;margin-top:28px;
    opacity:.75;line-height:1.5}
  .chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
  .chips:empty{display:none}
  .chip{display:inline-flex;align-items:center;gap:7px;background:var(--panel2);
    border:1px solid var(--border);border-radius:999px;padding:6px 11px;
    font-size:.78rem;color:var(--text);cursor:pointer;max-width:100%}
  .chip:active{background:#2f4356}
  .chip .t{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .chip.favorita{background:linear-gradient(180deg,var(--accent),var(--accent2));
    border-color:var(--accent2);color:#fff}
  .chip.favorita:active{background:var(--accent2)}
  .chip .del{color:rgba(255,255,255,.85);font-size:.95rem;line-height:1;font-weight:700;padding:0 1px}
  .filtros{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}
  .filtros:empty{display:none}
  .fchip{border:1px solid var(--border);background:var(--panel2);color:var(--text);
    border-radius:999px;padding:6px 12px;font-size:.75rem;font-weight:700;cursor:pointer}
  .fchip.off{opacity:.4}
  .salida{display:flex;align-items:center;gap:9px;cursor:pointer;
    border-bottom:1px dashed var(--border);padding:8px 0;font-size:.88rem}
  .salida:last-child{border-bottom:none}
  .salida:active{background:rgba(59,130,246,.08)}
  .salida .hh{font-weight:800;font-variant-numeric:tabular-nums}
  .salida .dest{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .salida .linea{font-size:.72rem;max-width:34%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .salida .badge{font-size:.62rem;padding:2px 8px}
  .salida .ret{font-size:.72rem;font-weight:700;color:#7fc98f;white-space:nowrap}
  .salida .ret.tarde{color:#f0b429}
  #aviso-datos{display:none;margin:0 0 14px;padding:9px 12px;line-height:1.45;
    border-left:3px solid #f0b429;background:rgba(240,180,41,.08);
    border-radius:8px;font-size:.8rem;color:var(--muted)}
  #seguimiento:empty{display:none}
  .segcard{background:linear-gradient(180deg,#152a42 0%,#121b26 100%);
    border:1px solid var(--accent2);border-radius:16px;padding:14px 15px;
    margin-bottom:16px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
  .segcab{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .segcab .ruta{font-weight:700;font-size:.88rem;flex:1;min-width:0}
  .stopseg{background:rgba(229,72,77,.15);border:1px solid var(--av);color:#ff9a9e;
    font-weight:700;font-size:.78rem;padding:6px 13px}
  .stopseg:active{background:rgba(229,72,77,.35);color:#fff}
  .segbar{height:6px;border-radius:999px;background:var(--panel2);margin:11px 0 9px;overflow:hidden}
  .segbar div{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:999px}
  .segbig{font-size:1.02rem;font-weight:700;margin:6px 0 2px}
  .seggps{font-size:.78rem;margin-top:6px;color:#7fc98f}
  .seggps.tarde{color:#f0b429}
  .croquis{display:block;width:100%;height:auto;margin-top:10px}
  .segpregunta{display:flex;gap:10px;margin-top:4px}
  .segpregunta .buscar{flex:1;margin-top:10px}
  .segpregunta .bno{background:linear-gradient(180deg,#e5484d,#c73a3f);
    box-shadow:0 6px 18px rgba(229,72,77,.3)}
  @media (min-width:600px){ .wrap{padding-top:26px} }
</style>
</head>
<body>
<div class="wrap">
  <h1>🚆 BuscaTrenes</h1>

  <div id="aviso-datos"></div>
  <div id="seguimiento"></div>

  <div class="tabs">
    <button type="button" class="tab active" id="tab-estacion" data-tab="estacion">Trayecto</button>
    <button type="button" class="tab" id="tab-salidas" data-tab="salidas">Salidas</button>
    <button type="button" class="tab" id="tab-numero" data-tab="numero">Nº tren</button>
    <button type="button" class="tab" id="tab-incidencias" data-tab="incidencias" hidden>⚠️ Incidencias</button>
  </div>

  <div class="card">
    <div class="tabpanel active" id="panel-estacion">
      <div class="chips" id="chips-trayectos"></div>
      <label for="origen">Origen</label>
      <div class="autocomplete">
        <input type="text" id="origen" placeholder="Escribe una estación..." autocomplete="off">
        <div class="sugg" id="sugg-origen"></div>
      </div>
      <button type="button" class="geobtn" id="btn-geo">📍 Usar mi ubicación</button>
      <div class="geostatus" id="geo-status"></div>

      <label for="destino">Destino</label>
      <div class="autocomplete">
        <input type="text" id="destino" placeholder="Escribe una estación..." autocomplete="off">
        <div class="sugg" id="sugg-destino"></div>
      </div>

      <div class="row">
        <div>
          <label for="fecha">Fecha</label>
          <input type="date" id="fecha">
        </div>
        <div>
          <label for="hora">Hora</label>
          <input type="time" id="hora">
        </div>
        <div>
          <label for="enlace-min">Enlace mín. (min)</label>
          <input type="number" id="enlace-min" value="10" min="0" max="120" inputmode="numeric">
        </div>
      </div>
      <div class="chk">
        <input type="checkbox" id="todo-el-dia">
        <label for="todo-el-dia" style="margin:0">Ver todo el día (ignorar la hora)</label>
      </div>
      <div class="chk">
        <input type="checkbox" id="guardar-fav">
        <label for="guardar-fav" style="margin:0">Guardar trayecto como favorito</label>
      </div>

      <button class="buscar" id="btn-buscar" disabled>Cargando datos…</button>
    </div>

    <div class="tabpanel" id="panel-salidas">
      <label for="sal-estacion">Estación</label>
      <div class="autocomplete">
        <input type="text" id="sal-estacion" placeholder="Escribe una estación..." autocomplete="off">
        <div class="sugg" id="sugg-sal"></div>
      </div>
      <button type="button" class="geobtn" id="btn-geo-sal">📍 Usar mi ubicación</button>
      <div class="geostatus" id="sal-geo-status"></div>
      <div class="row">
        <div>
          <label for="sal-fecha">Fecha</label>
          <input type="date" id="sal-fecha">
        </div>
        <div>
          <label for="sal-hora">Desde las</label>
          <input type="time" id="sal-hora">
        </div>
      </div>
      <button class="buscar" id="btn-salidas" disabled>Cargando datos…</button>
    </div>

    <div class="tabpanel" id="panel-numero">
      <label for="num-tren">Número de tren</label>
      <input type="text" id="num-tren" placeholder="Ej. 03045" inputmode="numeric" autocomplete="off">
      <button class="buscar" id="btn-buscar-numero" disabled>Cargando datos…</button>
    </div>

    <div class="tabpanel" id="panel-incidencias">
      <label for="inc-ambito">Ámbito</label>
      <select id="inc-ambito">
        <option value="zona" selected>Mi zona (50 km)</option>
        <option value="todas">Toda España</option>
      </select>
      <label for="inc-linea">Línea</label>
      <select id="inc-linea">
        <option value="">Todas las líneas</option>
      </select>
      <div class="geostatus" id="inc-status" style="margin-top:10px"></div>
      <div id="inc-lista"></div>
    </div>
  </div>

  <div id="estado"></div>
  <div class="filtros" id="filtros"></div>
  <div id="resultados"></div>
  <div id="toast"></div>

  <footer>Datos horarios públicos de los operadores ferroviarios españoles (alta velocidad, larga y media distancia, cercanías y regionales). Se muestran trenes directos; si no hay, se buscan automáticamente enlaces con 1 o 2 transbordos respetando el tiempo mínimo de enlace indicado (+10 min si el cambio es a pie entre estaciones próximas). Con el enlace mínimo por defecto (10 min), entre dos líneas de Cercanías también se ofrecen enlaces más ajustados (5 min en la misma estación, 7,5 min andando a otra estación cercana).<span id="fecha-datos"></span></footer>
</div>

<script>
const DATA_B64 = "__DATA_B64__";
const DATA_FECHA = "__DATA_FECHA__"; // YYYY-MM-DD, fecha de extracción de los horarios
let DB = null; // {estaciones, lineas, trips}
let estNombres = []; // nombres en minusculas sin acentos, paralelo a DB.estaciones

function normaliza(s){
  return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase().trim();
}

let grupoDe = null; // grupo de transbordo de cada estación (estaciones a <500 m = mismo nodo)

function agruparEstaciones(){
  const n = DB.estaciones.length;
  const parent = new Int32Array(n);
  for(let i=0;i<n;i++) parent[i]=i;
  const find = i => { while(parent[i]!==i){ parent[i]=parent[parent[i]]; i=parent[i]; } return i; };
  const KM = 0.5;
  for(let i=0;i<n;i++){
    const [_, la, lo] = DB.estaciones[i];
    if(la==null) continue;
    for(let j=i+1;j<n;j++){
      const [__, lb, lob] = DB.estaciones[j];
      if(lb==null) continue;
      if(Math.abs(la-lb) > 0.006) continue;              // ~0.66 km de latitud
      if(haversine(la, lo, lb, lob) <= KM){
        parent[find(i)] = find(j);
      }
    }
  }
  grupoDe = new Int32Array(n);
  for(let i=0;i<n;i++) grupoDe[i] = find(i);
}

async function cargarDatos(){
  const bin = atob(DATA_B64);
  const bytes = new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) bytes[i] = bin.charCodeAt(i);
  const ds = new DecompressionStream('gzip');
  const stream = new Blob([bytes]).stream().pipeThrough(ds);
  const text = await new Response(stream).text();
  DB = JSON.parse(text);
  estNombres = DB.estaciones.map(e => normaliza(e[0]));
  agruparEstaciones();
}

// ---------- Autocompletado ----------
function setupAutocomplete(inputId, suggId){
  const input = document.getElementById(inputId);
  const sugg = document.getElementById(suggId);
  let activeIdx = -1, items = [];

  function render(list){
    items = list;
    activeIdx = -1;
    if(!list.length){ sugg.style.display='none'; sugg.innerHTML=''; return; }
    sugg.innerHTML = list.map((idx,i) =>
      `<div data-idx="${idx}" data-i="${i}">${DB.estaciones[idx][0]}</div>`
    ).join('');
    sugg.style.display='block';
  }

  input.addEventListener('input', () => {
    const q = normaliza(input.value);
    input.dataset.selIdx = '';
    if(!DB || q.length < 2){ render([]); return; }
    const starts=[], contains=[];
    for(let i=0;i<estNombres.length;i++){
      const n = estNombres[i];
      if(n.startsWith(q)) starts.push(i);
      else if(n.includes(q)) contains.push(i);
      if(starts.length>=8) break;
    }
    render(starts.concat(contains).slice(0,8));
  });

  sugg.addEventListener('mousedown', (e) => {
    const div = e.target.closest('div[data-idx]');
    if(!div) return;
    const idx = div.dataset.idx;
    input.value = DB.estaciones[idx][0];
    input.dataset.selIdx = idx;
    render([]);
  });

  input.addEventListener('keydown', (e) => {
    if(sugg.style.display !== 'block') return;
    const divs = [...sugg.children];
    if(e.key === 'ArrowDown'){ e.preventDefault(); activeIdx = Math.min(activeIdx+1, divs.length-1); }
    else if(e.key === 'ArrowUp'){ e.preventDefault(); activeIdx = Math.max(activeIdx-1, 0); }
    else if(e.key === 'Enter'){
      if(activeIdx>=0){
        e.preventDefault();
        divs[activeIdx].dispatchEvent(new MouseEvent('mousedown'));
      }
      return;
    } else return;
    divs.forEach((d,i)=>d.classList.toggle('active', i===activeIdx));
  });

  input.addEventListener('blur', () => setTimeout(()=>{ sugg.style.display='none'; }, 150));
}

function resolverEstacion(inputId){
  const input = document.getElementById(inputId);
  if(input.dataset.selIdx) return parseInt(input.dataset.selIdx);
  const q = normaliza(input.value);
  const i = estNombres.indexOf(q);
  return i>=0 ? i : -1;
}

// ---------- Trayectos favoritos ----------
// Se guardan por NOMBRE de estación (no por índice): los índices cambian
// cuando se actualiza el payload de datos.
const LS_FAV = 'bt_favoritos';
function lsGet(k){ try{ return JSON.parse(localStorage.getItem(k)) || []; }catch(e){ return []; } }
function lsSet(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)); }catch(e){} }
const mismoPar = (a, b) => a[0] === b[0] && a[1] === b[1];

function guardarTrayecto(o, d){
  const chk = document.getElementById('guardar-fav');
  if(!chk.checked) return;
  const par = [o, d];
  const fav = lsGet(LS_FAV).filter(p => !mismoPar(p, par));
  fav.unshift(par);
  lsSet(LS_FAV, fav.slice(0, 8));
  chk.checked = false;
  renderChips();
}

function borrarFavorito(par){
  lsSet(LS_FAV, lsGet(LS_FAV).filter(p => !mismoPar(p, par)));
  renderChips();
}

function setEstacion(inputId, nombre){
  const input = document.getElementById(inputId);
  input.value = nombre;
  const i = estNombres.indexOf(normaliza(nombre));
  input.dataset.selIdx = i >= 0 ? String(i) : '';
}

function renderChips(){
  const cont = document.getElementById('chips-trayectos');
  cont.innerHTML = '';
  for(const par of lsGet(LS_FAV)){
    // solo trayectos cuyas estaciones sigan existiendo tras actualizar datos
    if(estNombres.indexOf(normaliza(par[0])) < 0 || estNombres.indexOf(normaliza(par[1])) < 0) continue;
    const chip = document.createElement('span');
    chip.className = 'chip favorita';
    const t = document.createElement('span');
    t.className = 't';
    t.textContent = par[0] + ' → ' + par[1];
    chip.appendChild(t);
    const del = document.createElement('span');
    del.className = 'del';
    del.textContent = '✕';
    del.title = 'Borrar favorito';
    del.addEventListener('click', (e) => { e.stopPropagation(); borrarFavorito(par); });
    chip.appendChild(del);
    chip.addEventListener('click', () => {
      setEstacion('origen', par[0]);
      setEstacion('destino', par[1]);
      buscar();
    });
    cont.appendChild(chip);
  }
}

// ---------- Geolocalización ----------
function haversine(lat1,lon1,lat2,lon2){
  const R=6371, toRad=x=>x*Math.PI/180;
  const dLat=toRad(lat2-lat1), dLon=toRad(lon2-lon1);
  const a=Math.sin(dLat/2)**2 + Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dLon/2)**2;
  return 2*R*Math.asin(Math.sqrt(a));
}

function configurarGeo(btnId, statusId, inputId){
  document.getElementById(btnId).addEventListener('click', () => {
    const st = document.getElementById(statusId);
    if(!navigator.geolocation){
      st.textContent = 'Tu navegador no soporta geolocalización.';
      return;
    }
    st.textContent = 'Localizando...';
    navigator.geolocation.getCurrentPosition((pos) => {
      const {latitude, longitude} = pos.coords;
      let mejor=-1, mejorD=Infinity;
      DB.estaciones.forEach((e,i) => {
        if(e[1]==null || e[2]==null) return;
        const d = haversine(latitude, longitude, e[1], e[2]);
        if(d<mejorD){ mejorD=d; mejor=i; }
      });
      if(mejor>=0){
        const input = document.getElementById(inputId);
        input.value = DB.estaciones[mejor][0];
        input.dataset.selIdx = mejor;
        st.textContent = `Estación más cercana: ${DB.estaciones[mejor][0]} (${mejorD.toFixed(1)} km)`;
      } else {
        st.textContent = 'No se pudo determinar la estación más cercana.';
      }
    }, (err) => {
      st.textContent = 'No se pudo obtener tu ubicación (' + err.message + ').';
    }, {enableHighAccuracy:true, timeout:10000});
  });
}
configurarGeo('btn-geo', 'geo-status', 'origen');
configurarGeo('btn-geo-sal', 'sal-geo-status', 'sal-estacion');

// ---------- Búsqueda ----------
const DIAS_ES = ['L','M','X','J','V','S','D'];
const CAT_LABEL = {AV:'Alta Velocidad', LD:'Larga Distancia', MD:'Media Distancia', CER:'Cercanías',
  OUIGO:'OUIGO', FGC:'FGC', EUS:'Euskotren', SFM:'SFM Mallorca'};

function diasTexto(bitmask){
  if(bitmask === 127) return 'Diario';
  const activos = DIAS_ES.filter((_,i) => (bitmask & (1<<i)) !== 0);
  return activos.length ? activos.join('-') : '—';
}

function fmtFecha(yyyymmdd){
  const s = String(yyyymmdd);
  return `${s.slice(6,8)}/${s.slice(4,6)}/${s.slice(0,4)}`;
}

function trenLabel(numero){
  return numero ? `Tren ${numero}` : 'Servicio';
}

function fmtHora(min){
  if(min == null || min < 0) return '--:--';
  const h = Math.floor(min/60) % 24, m = Math.round(min) % 60;
  return String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0');
}

function durTxt(min){
  if(min == null || min < 0) return '';
  return `${Math.floor(min/60)}h ${String(min%60).padStart(2,'0')}m`;
}

function buscarDirectos(activos, oIdx, dIdx, minSel){
  const resultados = [];
  for(const trip of activos){
    const [cat, lineaIdx, numero, dias, fIni, fFin, stops] = trip;
    let posO=-1, posD=-1;
    const n = stops.length/3;
    for(let p=0;p<n;p++){
      const st = stops[p*3];
      if(st===oIdx && posO===-1) posO=p;
      else if(st===dIdx && posO!==-1 && posD===-1){ posD=p; break; }
    }
    if(posO===-1 || posD===-1 || posD<=posO) continue;

    const depO = stops[posO*3+2];
    const arrD = stops[posD*3+1];
    if(depO < 0 || depO < minSel) continue;

    const intermedias = [];
    for(let p=posO+1; p<posD; p++){
      intermedias.push({nombre: DB.estaciones[stops[p*3]][0], llegada: stops[p*3+1], salida: stops[p*3+2]});
    }

    resultados.push({
      cat, linea: DB.lineas[lineaIdx], numero, dias, fIni, fFin, trip, posO, posD,
      depO, arrD, intermedias,
      origenNombre: DB.estaciones[oIdx][0], destinoNombre: DB.estaciones[dIdx][0],
      origenReal: DB.estaciones[stops[0]][0], destinoReal: DB.estaciones[stops[stops.length-3]][0],
    });
  }
  resultados.sort((a,b) => a.depO - b.depO);
  return resultados;
}

const ANDAR_MIN = 10; // minutos extra si el transbordo es entre estaciones distintas del mismo nodo

// Entre dos líneas de Cercanías, con el enlace mínimo en su valor por defecto
// (10 min), se ofrecen también enlaces más ajustados: 5 min si el cambio es en
// la misma estación, 7,5 min si es andando a otra estación del mismo nodo.
const CER_MISMA_PARADA = 5;
const CER_ANDANDO = 7.5;

function margenTransbordo(catPrev, catNext, minT, mismaParada){
  if(minT === 10 && catPrev === 'CER' && catNext === 'CER'){
    return mismaParada ? CER_MISMA_PARADA : CER_ANDANDO;
  }
  return minT + (mismaParada ? 0 : ANDAR_MIN);
}

// Cada "candidato" de llegada a un nodo lleva su itinerario acumulado:
// {arr, depO, stIdx, legs:[{trip, dep, arr, oSt, dSt}]}
// Los mapas de llegadas se indexan por grupo de transbordo: estaciones a <500 m
// cuentan como el mismo nodo (p. ej. Atocha Cercanías y Puerta de Atocha).

function paretoPorGrupo(map){
  // Dentro de cada nodo, descartar llegadas dominadas (otra que llega antes o
  // igual habiendo salido del origen igual o más tarde)
  for(const [g, lst] of map){
    lst.sort((a,b) => a.arr - b.arr || b.depO - a.depO);
    const out = [];
    let maxDep = -Infinity;
    for(const c of lst){
      if(c.depO > maxDep){ out.push(c); maxDep = c.depO; }
    }
    map.set(g, out);
  }
}

function llegadasIniciales(activos, oIdx, dIdx, minSel){
  const map = new Map();
  for(const trip of activos){
    const stops = trip[6], n = stops.length/3;
    let posO = -1;
    for(let p=0;p<n;p++) if(stops[p*3]===oIdx){ posO=p; break; }
    if(posO===-1) continue;
    const depO = stops[posO*3+2];
    if(depO < 0 || depO < minSel) continue;
    for(let p=posO+1;p<n;p++){
      const st = stops[p*3], arr = stops[p*3+1];
      if(arr < 0 || st===oIdx || st===dIdx) continue;
      const g = grupoDe[st];
      let lst = map.get(g);
      if(!lst){ lst = []; map.set(g, lst); }
      lst.push({arr, depO, stIdx: st, legs: [{trip, dep: depO, arr, oSt: oIdx, dSt: st}]});
    }
  }
  paretoPorGrupo(map);
  return map;
}

function expandirTransbordo(llegadas, activos, oIdx, dIdx, minT){
  // Añade un tramo intermedio: desde los nodos ya alcanzados, subir a otro tren
  // y registrar todas sus llegadas posteriores.
  const map = new Map();
  for(const trip of activos){
    const stops = trip[6], n = stops.length/3;
    let best = null, bestBoard = null;
    for(let p=0;p<n;p++){
      const st = stops[p*3], arr = stops[p*3+1], dep = stops[p*3+2];
      // registrar la llegada usando el mejor embarque en una parada anterior
      if(best && arr >= 0 && st!==oIdx && st!==dIdx){
        const g = grupoDe[st];
        let lst = map.get(g);
        if(!lst){ lst = []; map.set(g, lst); }
        lst.push({arr, depO: best.depO, stIdx: st,
          legs: [...best.legs, {trip, dep: bestBoard.dep, arr, oSt: bestBoard.st, dSt: st}]});
      }
      // considerar el embarque en esta parada
      if(dep < 0 || st===oIdx) continue;
      const cands = llegadas.get(grupoDe[st]);
      if(!cands) continue;
      for(const c of cands){
        if(c.legs.some(l => l.trip===trip)) continue;
        const catPrev = c.legs[c.legs.length-1].trip[0];
        const margen = margenTransbordo(catPrev, trip[0], minT, c.stIdx === st);
        if(c.arr + margen > dep) continue;
        if(!best || c.depO > best.depO){ best = c; bestBoard = {st, dep}; }
      }
    }
  }
  paretoPorGrupo(map);
  return map;
}

function cerrarEnDestino(llegadas, activos, oIdx, dIdx, minT){
  if(!llegadas.size) return [];
  // Trenes que llegan al destino: subir en una estación de un nodo ya alcanzado
  const conexiones = [];
  for(const trip of activos){
    const stops = trip[6], n = stops.length/3;
    let posD = -1;
    for(let p=0;p<n;p++) if(stops[p*3]===dIdx){ posD=p; break; }
    if(posD < 1) continue;
    const arrD = stops[posD*3+1];
    if(arrD < 0) continue;

    let mejor = null;
    for(let p=0;p<posD;p++){
      const st = stops[p*3], depB = stops[p*3+2];
      if(depB < 0 || st===oIdx) continue;
      const cands = llegadas.get(grupoDe[st]);
      if(!cands) continue;
      for(const c of cands){
        if(c.legs.some(l => l.trip===trip)) continue;
        const catPrev = c.legs[c.legs.length-1].trip[0];
        const margen = margenTransbordo(catPrev, trip[0], minT, c.stIdx === st);
        if(c.arr + margen > depB) continue;   // no da tiempo al cambio
        // preferir salir del origen lo más tarde posible; a igualdad, menor espera
        if(!mejor || c.depO > mejor.c.depO ||
           (c.depO === mejor.c.depO && (depB - c.arr) < mejor.espera)){
          mejor = {c, st, depB, espera: depB - c.arr};
        }
      }
    }
    if(mejor){
      conexiones.push({
        depO: mejor.c.depO, arrD,
        legs: [...mejor.c.legs, {trip, dep: mejor.depB, arr: arrD, oSt: mejor.st, dSt: dIdx}],
      });
    }
  }

  // Poda de dominados: solo opciones que llegan antes o salen más tarde que las demás
  conexiones.sort((a,b) => a.arrD - b.arrD || b.depO - a.depO);
  const res = [];
  let maxDep = -1;
  for(const c of conexiones){
    if(c.depO > maxDep){ res.push(c); maxDep = c.depO; }
  }
  res.sort((a,b) => a.depO - b.depO);
  return res.slice(0, 50);
}

// ---------- Incidencias en tiempo real ----------
// Feeds GTFS-RT de alertas: RENFE Cercanías (JSON, sin CORS: solo llega a
// través del puente nativo de la app Android) y FGC (.pb vía su portal de
// datos abiertos, con CORS). Si ningún feed responde, la pestaña no aparece.
const URL_ALERTAS_RENFE = 'https://gtfsrt.renfe.com/alerts.json';
const URL_CATALOGO_FGC = 'https://dadesobertes.fgc.cat/api/explore/v2.1/catalog/datasets/alerts-gtfs_realtime/records?limit=1';
const RADIO_INC_KM = 50; // radio de "mi zona" alrededor del dispositivo

let ALERTAS = [];        // [{op, texto, lineas:Set(idx), estaciones:Set(idx)}]
let alertasCargadas = 0; // timestamp de la última carga
const feedsEstado = {CER: null, FGC: null}; // null=pendiente, true=ok, false=fallo

function esc(s){ return String(s).replace(/[&<>]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[ch])); }

let netSeq = 0;
const netPend = {};
window.__netCb = function(id, b64){
  const cb = netPend[id]; delete netPend[id];
  if(cb) cb(b64);
};
function fetchBytes(url){
  if(window.AndroidNet && AndroidNet.fetch){
    return new Promise(res => {
      const id = String(++netSeq);
      netPend[id] = b64 => {
        if(b64 == null){ res(null); return; }
        const bin = atob(b64);
        const u = new Uint8Array(bin.length);
        for(let i=0;i<bin.length;i++) u[i] = bin.charCodeAt(i);
        res(u);
      };
      setTimeout(() => { if(netPend[id]){ delete netPend[id]; res(null); } }, 20000);
      AndroidNet.fetch(url, id);
    });
  }
  return fetch(url).then(r => r.ok ? r.arrayBuffer().then(b => new Uint8Array(b)) : null).catch(() => null);
}

// Decodificador mínimo de protobuf, suficiente para el feed de alertas GTFS-RT
function pbCampos(buf, ini, fin){
  const out = [];
  let i = ini;
  while(i < fin){
    let clave = 0, s = 0;
    while(true){ const b = buf[i++]; clave |= (b & 127) << s; if(b < 128) break; s += 7; }
    const num = clave >>> 3, wire = clave & 7;
    if(wire === 0){
      let v = 0, e = 1;
      while(true){ const b = buf[i++]; v += (b & 127) * e; if(b < 128) break; e *= 128; }
      out.push({num, val: v});
    } else if(wire === 2){
      let len = 0, s2 = 0;
      while(true){ const b = buf[i++]; len |= (b & 127) << s2; if(b < 128) break; s2 += 7; }
      out.push({num, ini: i, fin: i + len});
      i += len;
    } else if(wire === 5){ i += 4; }
    else if(wire === 1){ i += 8; }
    else break;
  }
  return out;
}
const utf8 = new TextDecoder();
function pbTexto(buf, c){ return utf8.decode(buf.subarray(c.ini, c.fin)); }

function pbTraduccion(buf, c){
  // TranslatedString: translation=1 {text=1, language=2}
  for(const t of pbCampos(buf, c.ini, c.fin)){
    if(t.num !== 1) continue;
    for(const f of pbCampos(buf, t.ini, t.fin)) if(f.num === 1) return pbTexto(buf, f);
  }
  return '';
}

function decodificarAlertasPb(buf){
  // FeedMessage.entity=2 > FeedEntity.alert=5 > Alert{active_period=1,
  // informed_entity=5, header_text=10, description_text=11};
  // EntitySelector{route_id=2, trip=4{route_id=5}, stop_id=5}; TimeRange{end=2}
  const alertas = [];
  for(const ent of pbCampos(buf, 0, buf.length)){
    if(ent.num !== 2 || ent.ini === undefined) continue;
    for(const c of pbCampos(buf, ent.ini, ent.fin)){
      if(c.num !== 5) continue;
      const a = {rutas: [], stops: [], fin: 0, texto: ''};
      let desc = '';
      for(const f of pbCampos(buf, c.ini, c.fin)){
        if(f.num === 1 && f.ini !== undefined){
          for(const p of pbCampos(buf, f.ini, f.fin)) if(p.num === 2) a.fin = Math.max(a.fin, p.val);
        } else if(f.num === 5 && f.ini !== undefined){
          for(const s of pbCampos(buf, f.ini, f.fin)){
            if(s.num === 2 && s.ini !== undefined) a.rutas.push(pbTexto(buf, s));
            else if(s.num === 5 && s.ini !== undefined) a.stops.push(pbTexto(buf, s));
            else if(s.num === 4 && s.ini !== undefined){
              for(const t of pbCampos(buf, s.ini, s.fin)) if(t.num === 5 && t.ini !== undefined) a.rutas.push(pbTexto(buf, t));
            }
          }
        } else if(f.num === 10 && f.ini !== undefined) a.texto = pbTraduccion(buf, f);
        else if(f.num === 11 && f.ini !== undefined) desc = pbTraduccion(buf, f);
      }
      if(!a.texto) a.texto = desc;
      alertas.push(a);
    }
  }
  return alertas;
}

function lineasDeRuta(rid){
  if(rid in DB.rutas) return [DB.rutas[rid]];
  // RENFE rota los route_id entre versiones del feed (10T0095C4 -> 10T0096C4):
  // probar la clave estable "núcleo|nombre corto". El route_id de Cercanías es
  // <núcleo:2><T><nnnn><línea>, así que la línea es lo que sigue al carácter 7.
  const resto = rid.length > 7 ? rid.slice(7).toUpperCase() : '';
  if(!resto) return [];
  const pref = rid.slice(0,2) + '|';
  const out = [];
  for(const k in DB.rutas){
    if(!k.startsWith(pref)) continue;
    const corto = k.slice(3).toUpperCase();
    // igual (C4A ~ C4a), o ramal de una alerta troncal (C8 -> C8a, C8b) pero
    // sin confundir líneas distintas (R1 no debe casar con R11)
    if(corto === resto ||
       (corto.startsWith(resto) && (corto.charAt(resto.length) < '0' || corto.charAt(resto.length) > '9'))){
      out.push(DB.rutas[k]);
    }
  }
  return out;
}

function afinarAlerta(texto, lineas, ests){
  // El feed de RENFE etiqueta algunas alertas con todas las líneas del núcleo;
  // el propio texto permite afinar el ámbito real.
  const soloEstacion = /inaccesible|accesibilidad|ascensor|escalera|aseo|vestibulo|pmr|permanecera cerrado|cerrado temporalmente/
    .test(normaliza(texto));
  // 1) Alertas de la propia estación ("...la estación de X se encuentra
  //    inaccesible..."): convertir en alerta de esa estación concreta. Las de
  //    circulación (demoras, obras...) conservan sus líneas aunque mencionen
  //    una estación: el retraso viaja con el tren más allá de esa estación.
  if(soloEstacion && !ests.length){
    const m = normaliza(texto).match(/estacion de ([a-z0-9. -]{2,45})/);
    if(m){
      const chunk = m[1].trim();
      let mejor = [], mejorLen = 0;
      for(let i=0;i<estNombres.length;i++){
        const n = estNombres[i];
        if(n.length < 3) continue;
        // nombre de estación al inicio del texto capturado (con límite de palabra)
        if(chunk === n || (chunk.startsWith(n) && chunk.charAt(n.length) === ' ')){
          if(n.length > mejorLen){ mejor = [i]; mejorLen = n.length; }
          else if(n.length === mejorLen) mejor.push(i);
        }
      }
      if(!mejor.length){
        // el feed suele omitir el prefijo de ciudad ("Nuevos Ministerios" por
        // "Madrid-Nuevos Ministerios"): probar como final del nombre
        const palabras = chunk.split(' ');
        for(let w = Math.min(5, palabras.length); w >= 1 && !mejor.length; w--){
          const cand = palabras.slice(0, w).join(' ');
          if(cand.length < 3) continue;
          const hits = [];
          for(let i=0;i<estNombres.length;i++){
            const n = estNombres[i];
            // el feed suele acortar el nombre por delante ("Nuevos Ministerios"
            // por "Madrid-Nuevos Ministerios") o por detrás ("La Serna" por
            // "La Serna-Fuenlabrada")
            if(n === cand || n.endsWith('-' + cand) || n.endsWith(' ' + cand) ||
               n.startsWith(cand + '-') || n.startsWith(cand + ' ')) hits.push(i);
          }
          if(hits.length >= 1 && hits.length <= 2) mejor = hits;
        }
      }
      if(mejor.length) return {lineas: [], ests: mejor, soloEst: true};
    }
  }
  // 2) Alertas con hashtags de línea (#MadC7 #MadC8...): quedarse solo con
  //    las líneas citadas (si ninguna casa, se conserva el etiquetado original)
  const tags = texto.match(/#[A-Za-z0-9]+/g);
  if(tags && lineas.length){
    const tagsU = tags.map(t => t.toUpperCase());
    const filtradas = lineas.filter(l => {
      const partes = DB.lineas[l].split(' ');
      const corto = partes[partes.length - 1].toUpperCase();
      const base = corto.replace(/[A-Z]+$/, ''); // C4a -> C4 (ramales)
      return tagsU.some(t => t.endsWith(corto) || (base && base !== corto && t.endsWith(base)));
    });
    if(filtradas.length) lineas = filtradas;
  }
  return {lineas, ests, soloEst: soloEstacion && ests.length > 0};
}

function registrarAlerta(mapa, op, texto, lineas, estaciones, soloEst){
  if(!texto || (!lineas.length && !estaciones.length)) return;
  const clave = op + '|' + texto;
  let a = mapa.get(clave);
  if(!a){ a = {op, texto, lineas: new Set(), estaciones: new Set(), soloEst: !!soloEst}; mapa.set(clave, a); }
  for(const l of lineas) a.lineas.add(l);
  for(const e of estaciones) a.estaciones.add(e);
}

async function cargarAlertasRenfe(mapa){
  feedsEstado.CER = false;
  const bytes = await fetchBytes(URL_ALERTAS_RENFE);
  if(!bytes) return;
  let d;
  try{ d = JSON.parse(utf8.decode(bytes)); }catch(e){ return; }
  const ahora = Date.now()/1000;
  for(const ent of (d.entity || [])){
    try{
      const al = ent.alert;
      if(!al) continue;
      const periodos = al.activePeriod || [];
      if(periodos.length && periodos.every(p => p.end && Number(p.end) < ahora)) continue;
      const tr = (al.descriptionText && al.descriptionText.translation) || [];
      const esTr = tr.find(t => t.language === 'es') || tr[0];
      const texto = esTr ? esTr.text : '';
      const lineas = [], ests = [];
      for(const ie of (al.informedEntity || [])){
        if(ie.routeId) lineas.push(...lineasDeRuta(ie.routeId));
        if(ie.stopId && ie.stopId in DB.codigos) ests.push(DB.codigos[ie.stopId]);
      }
      const fino = afinarAlerta(texto, lineas, ests);
      registrarAlerta(mapa, 'CER', texto, fino.lineas, fino.ests, fino.soloEst);
    }catch(e){ /* alerta malformada: se ignora sin perder el resto */ }
  }
  feedsEstado.CER = true;
}

async function cargarAlertasFgc(mapa){
  // La URL del .pb cambia en cada actualización: se resuelve vía el catálogo
  feedsEstado.FGC = false;
  const cat = await fetchBytes(URL_CATALOGO_FGC);
  if(!cat) return;
  let url = null;
  try{
    const d = JSON.parse(utf8.decode(cat));
    url = d.results && d.results[0] && d.results[0].file && d.results[0].file.url;
  }catch(e){ return; }
  if(!url) return;
  const bytes = await fetchBytes(url);
  if(!bytes) return;
  const ahora = Date.now()/1000;
  for(const a of decodificarAlertasPb(bytes)){
    try{
      if(a.fin && a.fin < ahora) continue;
      const lineas = [], ests = [];
      for(const rid of a.rutas) lineas.push(...lineasDeRuta(rid));
      for(const sid of a.stops){
        // el feed estático de FGC numera los andenes (PR1, PR2); las alertas
        // usan el código de estación pelado (PR)
        const k = sid in DB.codigos ? sid : ((sid + '1') in DB.codigos ? sid + '1' : null);
        if(k) ests.push(DB.codigos[k]);
      }
      registrarAlerta(mapa, 'FGC', a.texto, lineas, ests);
    }catch(e){ /* alerta malformada: se ignora sin perder el resto */ }
  }
  feedsEstado.FGC = true;
}

async function cargarIncidencias(){
  if(!DB || !DB.rutas || !DB.codigos) return;
  const mapa = new Map();
  // cada feed capturado por separado: el fallo de uno no pierde el otro
  await Promise.all([
    cargarAlertasRenfe(mapa).catch(() => { feedsEstado.CER = false; }),
    cargarAlertasFgc(mapa).catch(() => { feedsEstado.FGC = false; }),
  ]);
  ALERTAS = [...mapa.values()];
  alertasCargadas = Date.now();
  document.getElementById('tab-incidencias').hidden = ALERTAS.length === 0;
}

function avisoFeeds(){
  const fallidos = [];
  if(feedsEstado.CER === false) fallidos.push('RENFE Cercanías');
  if(feedsEstado.FGC === false) fallidos.push('FGC');
  if(!fallidos.length) return '';
  let msg = ` No se pudieron cargar las incidencias de ${fallidos.join(' y ')}.`;
  if(feedsEstado.CER === false && !(window.AndroidNet && AndroidNet.fetch)){
    msg += ' El feed de RENFE solo es accesible desde la app Android (el navegador lo bloquea).';
  }
  return msg;
}

function alertasDeTrip(trip, ini, fin){
  // ini/fin: posiciones (índices de parada) del tramo que se recorre; si no se
  // pasan, se considera el recorrido completo del tren
  if(!ALERTAS.length) return [];
  const lin = trip[1], stops = trip[6], n = stops.length/3;
  const p0 = (ini >= 0 && ini !== undefined) ? ini : 0;
  const p1 = (fin >= 0 && fin !== undefined) ? fin : n - 1;
  const out = [];
  for(const a of ALERTAS){
    // alertas de la propia estación (accesibilidad, cierres): solo si el tramo
    // recorrido pasa por ella; las de circulación casan por línea (el retraso
    // originado en cualquier estación de la línea viaja con el tren)
    let afecta = !a.soloEst && a.lineas.has(lin);
    if(!afecta && a.estaciones.size){
      for(let p=p0;p<=p1;p++){ if(a.estaciones.has(stops[p*3])){ afecta = true; break; } }
    }
    if(afecta) out.push(a);
  }
  return out;
}

function incidenciasListaHTML(als){
  if(!als.length) return '';
  const bloques = als.map(a => `<div class="incidencia">⚠️ ${esc(a.texto)}</div>`);
  if(bloques.length <= 2) return bloques.join('');
  return bloques[0] + bloques[1] +
    `<details><summary>⚠️ ${bloques.length - 2} incidencia(s) más</summary>${bloques.slice(2).join('')}</details>`;
}

function incidenciasHTML(trip, ini, fin){
  return incidenciasListaHTML(alertasDeTrip(trip, ini, fin));
}

let posDispositivo = null;
function obtenerPosicion(){
  return new Promise(res => {
    if(posDispositivo){ res(posDispositivo); return; }
    if(!navigator.geolocation){ res(null); return; }
    navigator.geolocation.getCurrentPosition(
      p => { posDispositivo = {lat: p.coords.latitude, lon: p.coords.longitude}; res(posDispositivo); },
      () => res(null), {enableHighAccuracy: false, timeout: 10000, maximumAge: 300000});
  });
}

function lineasDeEstaciones(ests){
  // De las líneas con alguna alerta, las que paran en alguna de esas estaciones
  const lineasAlerta = new Set();
  for(const a of ALERTAS) for(const l of a.lineas) lineasAlerta.add(l);
  const lineas = new Set();
  for(const trip of DB.trips){
    if(!lineasAlerta.has(trip[1]) || lineas.has(trip[1])) continue;
    const stops = trip[6];
    for(let p=0;p<stops.length;p+=3){ if(ests.has(stops[p])){ lineas.add(trip[1]); break; } }
  }
  return lineas;
}

function lineasCercaniasDe(ests){
  // Líneas de Cercanías/FGC que paran en alguna de las estaciones dadas
  // (ests = null: todas las líneas de Cercanías/FGC)
  const out = new Set();
  for(const trip of DB.trips){
    if(trip[0] !== 'CER' && trip[0] !== 'FGC') continue;
    if(out.has(trip[1])) continue;
    if(!ests){ out.add(trip[1]); continue; }
    const stops = trip[6];
    for(let p=0;p<stops.length;p+=3){ if(ests.has(stops[p])){ out.add(trip[1]); break; } }
  }
  return out;
}

const estacionesLineaCache = {};
function estacionesDeLinea(L){
  if(estacionesLineaCache[L]) return estacionesLineaCache[L];
  const s = new Set();
  for(const trip of DB.trips){
    if(trip[1] !== L) continue;
    const stops = trip[6];
    for(let p=0;p<stops.length;p+=3) s.add(stops[p]);
  }
  return estacionesLineaCache[L] = s;
}

function poblarLineas(ests){
  // Rellena el filtro de línea con las líneas de Cercanías/FGC del ámbito
  // actual, conservando la selección si sigue disponible
  const sel = document.getElementById('inc-linea');
  const previa = sel.value;
  const lineas = [...lineasCercaniasDe(ests)]
    .sort((a,b) => DB.lineas[a].localeCompare(DB.lineas[b]));
  sel.innerHTML = '<option value="">Todas las líneas</option>' +
    lineas.map(l => `<option value="${l}">${esc(DB.lineas[l])}</option>`).join('');
  if(previa && [...sel.options].some(o => o.value === previa)) sel.value = previa;
}

function poblarAmbitos(){
  // Rellena el selector con las CCAA y provincias que tienen estaciones
  if(!DB.provincias || !DB.provincias.length) return;
  const sel = document.getElementById('inc-ambito');
  const usadas = new Set();
  for(const e of DB.estaciones) if(e[3] >= 0) usadas.add(e[3]);
  const ccaas = [...new Set([...usadas].map(p => DB.provincias[p][1]))].sort((a,b) => a.localeCompare(b));
  const gC = document.createElement('optgroup');
  gC.label = 'Comunidad autónoma';
  for(const c of ccaas){
    const o = document.createElement('option');
    o.value = 'c:' + c; o.textContent = c;
    gC.appendChild(o);
  }
  sel.appendChild(gC);
  const gP = document.createElement('optgroup');
  gP.label = 'Provincia';
  const provs = [...usadas].sort((a,b) => DB.provincias[a][0].localeCompare(DB.provincias[b][0]));
  for(const p of provs){
    const o = document.createElement('option');
    o.value = 'p:' + p; o.textContent = DB.provincias[p][0];
    gP.appendChild(o);
  }
  sel.appendChild(gP);
}

async function renderIncidencias(){
  const st = document.getElementById('inc-status');
  const lista = document.getElementById('inc-lista');
  lista.innerHTML = '';
  if(Date.now() - alertasCargadas > 120000) await cargarIncidencias();
  const modo = document.getElementById('inc-ambito').value;
  let locales, ambito, estsAmbito = null;
  if(modo === 'todas'){
    locales = ALERTAS;
    ambito = 'en toda España';
  } else {
    let ests;
    if(modo === 'zona'){
      st.textContent = 'Obteniendo tu ubicación...';
      const pos = await obtenerPosicion();
      if(!pos){
        st.textContent = 'No se pudo obtener tu ubicación. Elige arriba otro ámbito para ver incidencias.';
        return;
      }
      ests = new Set();
      DB.estaciones.forEach((e, i) => {
        if(e[1] != null && haversine(pos.lat, pos.lon, e[1], e[2]) <= RADIO_INC_KM) ests.add(i);
      });
      ambito = 'en tu zona';
    } else if(modo.slice(0,2) === 'p:'){
      const p = parseInt(modo.slice(2), 10);
      ests = new Set();
      DB.estaciones.forEach((e, i) => { if(e[3] === p) ests.add(i); });
      ambito = 'en ' + DB.provincias[p][0];
    } else {
      const c = modo.slice(2);
      ests = new Set();
      DB.estaciones.forEach((e, i) => { if(e[3] >= 0 && DB.provincias[e[3]][1] === c) ests.add(i); });
      ambito = 'en ' + c;
    }
    const lineas = lineasDeEstaciones(ests);
    locales = ALERTAS.filter(a => {
      for(const l of a.lineas) if(lineas.has(l)) return true;
      for(const e of a.estaciones) if(ests.has(e)) return true;
      return false;
    });
    estsAmbito = ests;
  }
  poblarLineas(estsAmbito);
  const lsel = document.getElementById('inc-linea').value;
  if(lsel !== ''){
    const L = parseInt(lsel, 10);
    const estsL = estacionesDeLinea(L);
    locales = locales.filter(a => a.lineas.has(L) || [...a.estaciones].some(e => estsL.has(e)));
    ambito += ' · ' + DB.lineas[L];
  }
  if(!locales.length){
    st.textContent = 'Sin incidencias ' + ambito + '.' + avisoFeeds();
    return;
  }
  st.textContent = `${locales.length} incidencia(s) ${ambito}:` + avisoFeeds();
  for(const a of locales){
    const badge = a.op === 'FGC' ? 'FGC' : 'CER';
    const nombres = [...a.lineas].map(l => DB.lineas[l]).sort().join(' · ');
    const div = document.createElement('div');
    div.className = 'resultado';
    div.innerHTML = `
      <div class="rescab">
        <span class="badge ${badge}">${badge}</span>
        <span class="linea">${esc(nombres)}</span>
      </div>
      <div class="meta">${esc(a.texto)}</div>`;
    lista.appendChild(div);
  }
}

// ---------- Compartir ----------
let toastTimer = null;
function toast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('visible'), 2200);
}

function compartir(texto){
  if(window.AndroidShare && AndroidShare.share){          // app Android (WebView)
    AndroidShare.share(texto);
  } else if(navigator.share){                             // navegadores móviles
    navigator.share({text: texto}).catch(()=>{});
  } else if(navigator.clipboard){                         // escritorio
    navigator.clipboard.writeText(texto)
      .then(() => toast('Itinerario copiado al portapapeles'))
      .catch(() => toast('No se pudo copiar'));
  } else {
    toast('Compartir no disponible en este navegador');
  }
}

function fechaSeleccionada(){
  const f = document.getElementById('fecha').value;       // YYYY-MM-DD
  return f ? `${f.slice(8,10)}/${f.slice(5,7)}/${f.slice(0,4)}` : '';
}

// ---------- Añadir al calendario ----------
// En la app Android abre el editor de eventos del calendario (puente
// AndroidCal); en navegador descarga un .ics como alternativa.
function aCalendario(titulo, desc, depMin, arrMin){
  const fecha = (ultimaBusqueda && ultimaBusqueda.fechaISO) || document.getElementById('fecha').value;
  if(!fecha) return;
  const base = new Date(fecha + 'T00:00:00').getTime();
  const ini = base + depMin*60000;
  const fin = base + (arrMin >= 0 ? arrMin : depMin + 60)*60000;
  if(window.AndroidCal && AndroidCal.evento){
    AndroidCal.evento(titulo, desc, String(ini), String(fin));
    return;
  }
  const f = t => {
    const d = new Date(t), p = x => String(x).padStart(2,'0');
    return d.getFullYear() + p(d.getMonth()+1) + p(d.getDate()) + 'T' + p(d.getHours()) + p(d.getMinutes()) + '00';
  };
  const ics = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//BuscaTrenes//ES','BEGIN:VEVENT',
    'UID:' + Date.now() + '@buscatrenes',
    'DTSTART:' + f(ini),
    'DTEND:' + f(fin),
    'SUMMARY:' + titulo,
    'DESCRIPTION:' + desc.split('\\n').join('\\\\n'),
    'END:VEVENT','END:VCALENDAR'].join('\\r\\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([ics], {type:'text/calendar'}));
  a.download = 'tren.ics';
  document.body.appendChild(a);
  a.click();
  a.remove();
  toast('Evento de calendario descargado (.ics)');
}

// ---------- Seguimiento de un trayecto ----------
// SEG = {fechaISO, legs:[{cat, numero, linea, paradas:[[estIdx,arr,dep],...]}]}
// Vive solo en memoria: un arranque en frío de la app nunca retoma un
// seguimiento anterior (decisión de diseño).
let SEG = null;
let segTimer = null;
let segDelay = null;     // retraso estimado por GPS (min, suavizado)
let segLegActivo = null; // leg en curso (para el GPS), null si no estamos en marcha
let segWake = null;      // wake lock de pantalla durante el viaje
let segPregunta = false;  // mostrando "¿desea continuar el seguimiento?"
let segPreguntado = false;// ya confirmado que sí: no volver a preguntar
let segLejos = 0;         // posiciones GPS consecutivas lejos de la ruta
let segProg = null;       // {t0, s0}: ancla para detectar que no se avanza por la ruta

function segDesdeTrip(trip, ini, fin){
  // paradas: el tramo que se viaja; todas: el recorrido completo del tren,
  // necesario para deducir su retraso cuando aún no ha llegado a tu estación
  const stops = trip[6], paradas = [], todas = [];
  for(let p=0;p<stops.length/3;p++){
    const tr = [stops[p*3], stops[p*3+1], stops[p*3+2]];
    todas.push(tr);
    if(p >= ini && p <= fin) paradas.push(tr);
  }
  return {cat: trip[0], numero: trip[2], linea: DB.lineas[trip[1]], paradas, todas};
}

function iniciarSeguimiento(legs, fechaISO){
  if(!fechaISO) return;
  SEG = {fechaISO, legs};
  segDelay = null;
  segRT = null;
  segRTts = 0;
  segPosUsuario = null;
  segPregunta = false;
  segPreguntado = false;
  segLejos = 0;
  segProg = null;
  if(segTimer) clearInterval(segTimer);
  segTimer = setInterval(tickSeguimiento, 30000);
  tickSeguimiento();
  window.scrollTo({top: 0, behavior: 'smooth'});
  toast('Siguiendo el trayecto');
}

function pararSeguimiento(){
  SEG = null;
  segDelay = null;
  segRT = null;
  segRTts = 0;
  segPosUsuario = null;
  segPregunta = false;
  segPreguntado = false;
  segLejos = 0;
  segProg = null;
  segLegActivo = null;
  if(segTimer){ clearInterval(segTimer); segTimer = null; }
  document.getElementById('seguimiento').innerHTML = '';
  segWakeLock(false);
}

async function segWakeLock(on){
  try{
    if(on && !segWake && 'wakeLock' in navigator){
      segWake = await navigator.wakeLock.request('screen');
      segWake.addEventListener('release', () => { segWake = null; });
    } else if(!on && segWake){
      const w = segWake; segWake = null;
      await w.release();
    }
  }catch(e){ segWake = null; }
}

function fmtRestante(min){
  min = Math.max(0, Math.round(min));
  const d = Math.floor(min/1440), h = Math.floor((min%1440)/60), m = min%60;
  if(d) return `${d} d ${h} h`;
  if(h) return `${h} h ${m} min`;
  return `${m} min`;
}

// Estima el retraso comparando la posición GPS con el punto donde el tren
// debería estar según horario: proyecta la posición sobre el tramo más
// cercano entre estaciones consecutivas y convierte esa fracción en la hora
// teórica de paso; retraso = ahora - esa hora. Solo si estás a <5 km de la ruta.
function retrasoDesdePos(leg, lat, lon, nowMin){
  const P = leg.paradas;
  let best = null;
  const kx = 111.32*Math.cos(lat*Math.PI/180), ky = 110.57; // km por grado
  for(let i=0;i<P.length-1;i++){
    const a = DB.estaciones[P[i][0]], b = DB.estaciones[P[i+1][0]];
    if(a[1]==null || b[1]==null) continue;
    const ax=(a[2]-lon)*kx, ay=(a[1]-lat)*ky, bx=(b[2]-lon)*kx, by=(b[1]-lat)*ky;
    const dx=bx-ax, dy=by-ay, L2=dx*dx+dy*dy;
    let t = L2 > 0 ? (-(ax*dx+ay*dy))/L2 : 0;
    t = Math.max(0, Math.min(1, t));
    const px=ax+dx*t, py=ay+dy*t;
    const dist = Math.sqrt(px*px+py*py);
    if(!best || dist < best.dist){
      const dep = P[i][2] >= 0 ? P[i][2] : P[i][1];
      const arr = P[i+1][1] >= 0 ? P[i+1][1] : P[i+1][2];
      best = {dist, tSched: dep + (arr-dep)*t};
    }
  }
  if(!best || best.dist > 5) return null;
  return nowMin - best.tSched;
}

// ---------- Datos oficiales GTFS-RT del tren seguido (solo Cercanías) ----------
// Renfe publica en abierto los retrasos por tren (trip_updates) y la posición
// de cada tren en circulación (vehicle_positions). El número de tren va dentro
// del tripId (p. ej. 3095V23541C1) y casa con el campo `numero` del payload;
// el stopId casa con DB.codigos. AV/LD/MD no están en el feed: para esos
// trenes se usa solo la estimación GPS.
const URL_RT_TRIP = 'https://gtfsrt.renfe.com/trip_updates.json';
const URL_RT_VEH = 'https://gtfsrt.renfe.com/vehicle_positions.json';
let segRT = null;  // {delayMin, estIdx, status} del tren seguido, null si no hay dato
let segRTts = 0;   // instante de la última consulta (throttle de ~60 s)

function numeroDeTripId(tid){
  const m = /V0*(\d+)/.exec(tid || '');
  return m ? m[1] : null;
}

function segLegParaRT(){
  // Tramo relevante para el feed: el que está en curso o sale en <45 min,
  // y solo si es de Cercanías
  if(!SEG) return null;
  const base = new Date(SEG.fechaISO + 'T00:00:00').getTime();
  const nowMin = (Date.now() - base)/60000;
  for(const leg of SEG.legs){
    const P = leg.paradas;
    if(nowMin > P[P.length-1][1] + 5) continue; // tramo ya terminado
    if(P[0][2] - nowMin > 45) break;            // aún falta mucho
    return leg.cat === 'CER' ? leg : null;
  }
  return null;
}

async function actualizarRTSeguimiento(leg){
  const num = normalizaNumeroTren(leg.numero || '');
  if(!num) return;
  segRTts = Date.now();
  const [tu, vp] = await Promise.all([fetchBytes(URL_RT_TRIP), fetchBytes(URL_RT_VEH)]);
  if(!tu && !vp) return; // sin red: se conserva el último dato
  const rt = {delayMin: null, estIdx: -1, status: ''};
  let visto = false;
  try{
    if(tu){
      const d = JSON.parse(utf8.decode(tu));
      for(const e of (d.entity || [])){
        const t = e.tripUpdate;
        if(!t || numeroDeTripId(t.trip && t.trip.tripId) !== num) continue;
        let del = t.delay != null ? t.delay : null;
        const stu = t.stopTimeUpdate || [];
        for(let i=stu.length-1;i>=0;i--){
          const a = stu[i].arrival || stu[i].departure;
          if(a && a.delay != null){ del = a.delay; break; }
        }
        if(del != null){ rt.delayMin = Math.round(del/60); visto = true; }
        break;
      }
    }
  }catch(e){}
  try{
    if(vp){
      const d = JSON.parse(utf8.decode(vp));
      for(const e of (d.entity || [])){
        const v = e.vehicle;
        if(!v) continue;
        const porTrip = numeroDeTripId(v.trip && v.trip.tripId) === num;
        const porVeh = normalizaNumeroTren((v.vehicle && v.vehicle.id) || '') === num;
        if(!porTrip && !porVeh) continue;
        if(v.stopId && v.stopId in DB.codigos){ rt.estIdx = DB.codigos[v.stopId]; }
        if(v.position && v.position.latitude != null){
          rt.lat = v.position.latitude;
          rt.lon = v.position.longitude;
        }
        if(v.timestamp) rt.ts = Number(v.timestamp) || 0;
        rt.status = v.currentStatus || '';
        visto = true;
        break;
      }
    }
  }catch(e){}
  if(!SEG) return;
  // Validar la posición del feed antes de usarla: a veces llega obsoleta o
  // apunta a una estación del sentido contrario (p. ej. la unidad terminando
  // el recorrido inverso). Se descarta si el dato tiene >3 min o si, ya en
  // marcha, la estación anunciada queda POR DETRÁS de la última ya pasada.
  if(rt.estIdx >= 0 || rt.lat != null){
    let mala = rt.ts && (Date.now()/1000 - rt.ts) > 180;
    if(!mala && segLegActivo === leg && rt.estIdx >= 0){
      const retV = rt.delayMin != null && rt.delayMin > 0 ? rt.delayMin
        : (segDelay != null && segDelay > 0 ? Math.round(segDelay) : 0);
      mala = posicionIncoherente(leg, rt.estIdx, retV);
    }
    if(mala){ rt.estIdx = -1; delete rt.lat; delete rt.lon; }
  }
  // Renfe a veces publica la posición del tren pero no su retraso en
  // trip_updates: deducirlo comparando dónde está con dónde debería estar
  // según su horario completo (incluidas las paradas previas al embarque).
  if(visto && rt.delayMin == null){
    const base = new Date(SEG.fechaISO + 'T00:00:00').getTime();
    const nowMin = (Date.now() - base)/60000;
    const todas = leg.todas || leg.paradas;
    let est = null;
    if(rt.estIdx >= 0){
      const p = todas.find(x => x[0] === rt.estIdx);
      if(p){
        // parado en una estación pasada su hora de salida, o llegando a una
        // estación pasada su hora de llegada = retraso
        const ref = rt.status === 'STOPPED_AT' ? (p[2] >= 0 ? p[2] : p[1]) : (p[1] >= 0 ? p[1] : p[2]);
        if(ref >= 0) est = nowMin - ref;
      }
    }
    if(est == null && rt.lat != null){
      est = retrasoDesdePos({paradas: todas}, rt.lat, rt.lon, nowMin);
    }
    if(est != null && est > -30 && est < 180){
      rt.delayMin = Math.max(0, Math.round(est));
      rt.estimado = true;
    }
  }
  segRT = visto ? rt : null; // el tren dejó de aparecer en el feed: descartar
  renderSeguimiento();
}

// ---------- Croquis de la ruta ----------
let segPosUsuario = null; // última posición GPS del usuario durante el seguimiento

// En marcha, una estación anunciada por el feed que quede POR DETRÁS de la
// última de la que ya hemos salido (según horario + retraso) es un dato
// obsoleto o del recorrido inverso: no debe mostrarse.
function posicionIncoherente(leg, estIdx, retraso){
  const base = new Date(SEG.fechaISO + 'T00:00:00').getTime();
  const nowV = (Date.now() - base)/60000;
  const tEffV = nowV - (retraso != null && retraso > 0 ? retraso : 0);
  const T = leg.todas || leg.paradas;
  let iExp = 0; // última parada de la que ya hemos salido según horario+retraso
  for(let i=0;i<T.length;i++){
    const d = T[i][2] >= 0 ? T[i][2] : T[i][1];
    if(d >= 0 && d <= tEffV) iExp = i;
    else if(d > tEffV) break;
  }
  const iPos = T.findIndex(x => x[0] === estIdx);
  return iPos < 0 || iPos < iExp;
}

// La unidad aún no ha iniciado su recorrido y el feed la sitúa respecto a la
// cabecera de la línea (normalmente porque viene de hacer el sentido
// contrario): no debe mostrarse como "en camino a X", que parece el tren
// opuesto, sino como pendiente de posicionarse.
function trenPosicionandose(){
  if(!SEG || !segRT || segRT.estIdx < 0) return null;
  const base = new Date(SEG.fechaISO + 'T00:00:00').getTime();
  const nowMin = (Date.now() - base)/60000;
  for(const leg of SEG.legs){
    const P = leg.paradas;
    if(nowMin > P[P.length-1][1]) continue; // tramo terminado
    if(nowMin >= P[0][2]) break;            // ya en marcha: no aplica
    const T = leg.todas || P;
    if(segRT.estIdx === T[0][0]){
      return {cabIdx: T[0][0], cabecera: DB.estaciones[T[0][0]][0],
              enCabecera: segRT.status === 'STOPPED_AT'};
    }
    break; // solo el tramo próximo
  }
  return null;
}

// Posición estimada del tren: la oficial del feed si existe; si no, interpolando
// el horario (corregido con el retraso conocido) entre estaciones consecutivas.
function posTrenEstimada(){
  if(!SEG) return null;
  const posi = trenPosicionandose();
  if(posi){
    // posicionándose: pintarlo en la cabecera, no en su posición real (que
    // corresponde al recorrido inverso y confunde)
    const e = DB.estaciones[posi.cabIdx];
    return e[1] != null ? {lat: e[1], lon: e[2]} : null;
  }
  if(segRT && segRT.lat != null) return {lat: segRT.lat, lon: segRT.lon};
  const base = new Date(SEG.fechaISO + 'T00:00:00').getTime();
  const nowMin = (Date.now() - base)/60000;
  const oficial = segRT && segRT.delayMin != null ? segRT.delayMin : null;
  const retraso = oficial != null ? oficial : (segDelay != null ? Math.round(segDelay) : 0);
  const tEff = nowMin - Math.max(0, retraso);
  const coord = i => { const e = DB.estaciones[i]; return e[1] != null ? {lat: e[1], lon: e[2]} : null; };
  if(tEff <= SEG.legs[0].paradas[0][2]) return coord(SEG.legs[0].paradas[0][0]);
  for(const leg of SEG.legs){
    const P = leg.paradas;
    if(tEff > P[P.length-1][1]) continue;
    if(tEff < P[0][2]) return coord(P[0][0]); // esperando en el andén (transbordo)
    for(let i=0;i<P.length-1;i++){
      const dep = P[i][2], arr = P[i+1][1];
      if(tEff > arr) continue;
      if(tEff <= dep) return coord(P[i][0]); // parado en la estación
      const a = coord(P[i][0]), b = coord(P[i+1][0]);
      if(!a || !b) return null;
      const f = (tEff - dep)/Math.max(0.01, arr - dep);
      return {lat: a.lat + (b.lat - a.lat)*f, lon: a.lon + (b.lon - a.lon)*f};
    }
    return coord(P[P.length-1][0]);
  }
  const U = SEG.legs[SEG.legs.length-1].paradas;
  return coord(U[U.length-1][0]);
}

function croquisSVG(){
  if(!SEG || !DB) return '';
  // Mientras se espera al tren, el croquis arranca en su posición actual
  // (p. ej. Humanes) y no en la estación de embarque, que se marca aparte.
  const baseCk = new Date(SEG.fechaISO + 'T00:00:00').getTime();
  const nowCk = (Date.now() - baseCk)/60000;
  const ofiCk = segRT && segRT.delayMin != null ? segRT.delayMin
    : (segDelay != null ? Math.round(segDelay) : null);
  const tEffCk = nowCk - (ofiCk != null && ofiCk > 0 ? ofiCk : 0);
  let idxActivo = 0;
  while(idxActivo < SEG.legs.length - 1 &&
        nowCk > SEG.legs[idxActivo].paradas[SEG.legs[idxActivo].paradas.length-1][1]) idxActivo++;
  const legsPts = [];
  SEG.legs.forEach((leg, li) => {
    const P = leg.paradas;
    let fuente = P;
    const trenIniciado = segRT != null ||
      (leg.todas && leg.todas[0][2] >= 0 && tEffCk >= leg.todas[0][2]);
    if(li === idxActivo && nowCk < P[0][2] && trenIniciado &&
       leg.todas && leg.todas.length > P.length){
      const destino = P[P.length-1][0];
      const rec = [];
      let dentro = false;
      for(const p of leg.todas){
        const t = p[1] >= 0 ? p[1] : p[2];
        if(t >= 0 && t >= tEffCk) dentro = true;
        if(dentro){ rec.push(p); if(p[0] === destino) break; }
      }
      if(rec.length >= 2) fuente = rec;
    }
    const embarque = P[0][0];
    const pts = [];
    for(const p of fuente){
      const e = DB.estaciones[p[0]];
      if(e[1] != null) pts.push({lat: e[1], lon: e[2], nombre: e[0],
        emb: fuente !== P && p[0] === embarque});
    }
    if(pts.length >= 2) legsPts.push(pts);
  });
  if(!legsPts.length) return '';
  const tren = posTrenEstimada();
  const todos = legsPts.flat().slice();
  if(tren) todos.push(tren);
  if(segPosUsuario) todos.push(segPosUsuario);
  let minLat=Infinity, maxLat=-Infinity, minLon=Infinity, maxLon=-Infinity;
  for(const p of todos){
    minLat=Math.min(minLat,p.lat); maxLat=Math.max(maxLat,p.lat);
    minLon=Math.min(minLon,p.lon); maxLon=Math.max(maxLon,p.lon);
  }
  const kx = Math.cos(((minLat+maxLat)/2)*Math.PI/180);
  const W=320, H=170, M=20;
  const spanX = Math.max(1e-4,(maxLon-minLon)*kx), spanY = Math.max(1e-4, maxLat-minLat);
  const s = Math.min((W-2*M)/spanX, (H-2*M)/spanY);
  const ox = (W - spanX*s)/2, oy = (H - spanY*s)/2;
  const X = p => ox + (p.lon-minLon)*kx*s;
  const Y = p => oy + (maxLat-p.lat)*s;
  const xy = p => `${X(p).toFixed(1)},${Y(p).toFixed(1)}`;

  let lineas = '';
  legsPts.forEach((pts, i) => {
    lineas += `<polyline points="${pts.map(xy).join(' ')}" fill="none" stroke="#3a5372" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
    if(i > 0){
      const a = legsPts[i-1][legsPts[i-1].length-1], b = pts[0];
      lineas += `<line x1="${X(a).toFixed(1)}" y1="${Y(a).toFixed(1)}" x2="${X(b).toFixed(1)}" y2="${Y(b).toFixed(1)}" stroke="#8fa1b3" stroke-width="1.5" stroke-dasharray="4 4"/>`;
    }
  });

  // tramo ya recorrido: proyectar el tren sobre la cadena de estaciones
  const cadena = legsPts.flat();
  let best = null;
  if(tren){
    const tx0 = X(tren), ty0 = Y(tren);
    for(let i=0;i<cadena.length-1;i++){
      const ax=X(cadena[i]), ay=Y(cadena[i]), bx=X(cadena[i+1]), by=Y(cadena[i+1]);
      const dx=bx-ax, dy=by-ay, L2=dx*dx+dy*dy;
      let t = L2>0 ? ((tx0-ax)*dx+(ty0-ay)*dy)/L2 : 0;
      t = Math.max(0, Math.min(1, t));
      const px=ax+dx*t, py=ay+dy*t;
      const d2 = (px-tx0)*(px-tx0)+(py-ty0)*(py-ty0);
      if(!best || d2 < best.d2) best = {d2, i, px, py};
    }
    if(best){
      const rec = cadena.slice(0, best.i+1).map(xy);
      rec.push(`${best.px.toFixed(1)},${best.py.toFixed(1)}`);
      lineas += `<polyline points="${rec.join(' ')}" fill="none" stroke="var(--accent)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
    }
  }

  // estaciones: puntos pequeños; extremos y transbordos con etiqueta
  let marcas = '', etiquetas = '';
  const etiquetadas = new Set();
  legsPts.forEach((pts, i) => {
    pts.forEach((p, j) => {
      const esClave = j === 0 || j === pts.length-1 || p.emb;
      if(!esClave){
        marcas += `<circle cx="${X(p).toFixed(1)}" cy="${Y(p).toFixed(1)}" r="1.8" fill="#64809c"/>`;
        return;
      }
      marcas += `<circle cx="${X(p).toFixed(1)}" cy="${Y(p).toFixed(1)}" r="3.4" fill="#fff" stroke="var(--accent2)" stroke-width="1.5"/>`;
      if(etiquetadas.has(p.nombre)) return;
      etiquetadas.add(p.nombre);
      const nx = X(p), fin = nx > W - 130;
      etiquetas += `<text x="${(fin ? nx-6 : nx+6).toFixed(1)}" y="${(Y(p)+3).toFixed(1)}" font-size="9" fill="#8fa1b3"${fin ? ' text-anchor="end"' : ''}>${esc(p.nombre)}</text>`;
    });
  });

  let trenSvg = '';
  if(tren){
    const tx = best ? best.px.toFixed(1) : X(tren).toFixed(1);
    const ty = best ? best.py.toFixed(1) : Y(tren).toFixed(1);
    trenSvg = `<circle cx="${tx}" cy="${ty}" r="6" fill="none" stroke="var(--accent)" stroke-width="2" opacity=".8">
        <animate attributeName="r" values="6;13" dur="1.6s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values=".8;0" dur="1.6s" repeatCount="indefinite"/>
      </circle>
      <circle cx="${tx}" cy="${ty}" r="4.5" fill="var(--accent)" stroke="#fff" stroke-width="1.5"/>`;
  }
  let usuarioSvg = '';
  if(segPosUsuario){
    usuarioSvg = `<circle cx="${X(segPosUsuario).toFixed(1)}" cy="${Y(segPosUsuario).toFixed(1)}" r="3.2" fill="#34d399" stroke="#0b1219" stroke-width="1.2"/>`;
  }

  return `<svg class="croquis" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="${W}" height="${H}" rx="12" fill="rgba(30,43,58,.5)"/>
    ${lineas}${marcas}${usuarioSvg}${trenSvg}${etiquetas}
  </svg>`;
}

// Distancia (km) del punto a la polilínea de estaciones de un tramo
function distKmARuta(paradas, lat, lon){
  let best = Infinity;
  const kx = 111.32*Math.cos(lat*Math.PI/180), ky = 110.57;
  for(let i=0;i<paradas.length-1;i++){
    const a = DB.estaciones[paradas[i][0]], b = DB.estaciones[paradas[i+1][0]];
    if(a[1]==null || b[1]==null) continue;
    const ax=(a[2]-lon)*kx, ay=(a[1]-lat)*ky, bx=(b[2]-lon)*kx, by=(b[1]-lat)*ky;
    const dx=bx-ax, dy=by-ay, L2=dx*dx+dy*dy;
    let t = L2 > 0 ? (-(ax*dx+ay*dy))/L2 : 0;
    t = Math.max(0, Math.min(1, t));
    const px=ax+dx*t, py=ay+dy*t;
    best = Math.min(best, Math.sqrt(px*px+py*py));
  }
  return best;
}

// En trayectos con transbordo, en marcha solo interesan los hitos: hora de
// llegada a cada estación de transbordo pendiente y al destino. El retraso
// conocido solo se aplica al tren en curso (el siguiente sale de fábrica).
function hitosTransbordos(legs, desde, retraso){
  if(legs.length <= 1) return '';
  const filas = [];
  for(let k = desde; k < legs.length; k++){
    const Pk = legs[k].paradas;
    const arrK = Pk[Pk.length-1][1];
    const nomK = DB.estaciones[Pk[Pk.length-1][0]][0];
    const esDest = k === legs.length - 1;
    const prev = (k === desde && retraso != null && retraso > 0) ? ` · prevista ~${fmtHora(arrK + retraso)}` : '';
    filas.push(`<div class="parada"><span>${esDest ? '<b>' + nomK + '</b>' : 'Transbordo: ' + nomK}</span><span>${fmtHora(arrK)}${prev}</span></div>`);
  }
  return `<div class="meta" style="margin-top:8px">Llegadas:</div>` + filas.join('');
}

// Mientras se espera al tren (aún no ha llegado a la estación de embarque),
// lista sus próximas paradas hasta la tuya inclusive, con hora prevista si
// hay retraso conocido. Ej.: el tren está en Fuenlabrada y tú en Polvoranca.
function proximasHaciaEmbarque(leg, nowMin, oficial){
  const todas = leg.todas;
  if(!todas || todas.length <= leg.paradas.length) return '';
  const ret = oficial != null && oficial > 0 ? oficial : 0;
  const tEff = nowMin - ret;
  const salidaTren = todas[0][2];
  const iniciado = segRT != null || (salidaTren >= 0 && tEff >= salidaTren);
  if(!iniciado) return '';
  const embarque = leg.paradas[0][0];
  const destino = leg.paradas[leg.paradas.length-1][0];
  const filas = [];
  let dentro = false;
  for(const p of todas){
    const t = p[1] >= 0 ? p[1] : p[2];
    if(t >= 0 && t >= tEff) dentro = true;
    if(!dentro) continue;
    const esEmb = p[0] === embarque;
    const nom = DB.estaciones[p[0]][0];
    const prev = ret ? ` · prevista ~${fmtHora(t + ret)}` : '';
    filas.push(`<div class="parada"><span>${esEmb ? '<b>' + nom + '</b>' : nom}</span><span>${fmtHora(t)}${prev}</span></div>`);
    if(p[0] === destino) break;
  }
  if(!filas.length) return '';
  return `<div class="meta" style="margin-top:8px">Próximas paradas del tren:</div>` + filas.join('');
}

function renderSeguimiento(){
  const cont = document.getElementById('seguimiento');
  if(!SEG || !DB){ if(cont) cont.innerHTML=''; return; }
  const base = new Date(SEG.fechaISO + 'T00:00:00').getTime();
  const nowMin = (Date.now() - base)/60000;
  const legs = SEG.legs;
  const ultimaP = legs[legs.length-1].paradas;
  const salidaTotal = legs[0].paradas[0][2];
  const llegadaTotal = ultimaP[ultimaP.length-1][1];
  const oNombre = DB.estaciones[legs[0].paradas[0][0]][0];
  const dNombre = DB.estaciones[ultimaP[ultimaP.length-1][0]][0];

  if(nowMin > llegadaTotal + 120){ pararSeguimiento(); return; }

  if(segPregunta){
    cont.innerHTML = `<div class="segcard">
      <div class="segcab">
        <span class="badge ${legs[0].cat}">${legs[0].cat}</span>
        <span class="ruta">${oNombre} → ${dNombre}</span>
      </div>
      <div class="segbig" style="margin-top:8px">No se detecta viaje en el trayecto en seguimiento.</div>
      <div class="meta">¿Desea continuar realizando el seguimiento?</div>
      <div class="segpregunta">
        <button type="button" class="buscar bsi">Sí</button>
        <button type="button" class="buscar bno">No</button>
      </div>
    </div>`;
    cont.querySelector('.bsi').addEventListener('click', () => {
      segPregunta = false;
      segPreguntado = true;
      segLejos = 0;
      segProg = null;
      tickSeguimiento();
    });
    cont.querySelector('.bno').addEventListener('click', pararSeguimiento);
    segWakeLock(false);
    return;
  }

  segLegActivo = null;
  let cuerpo = '', gps = '', barra = '', enViaje = false, posRT = '';
  const oficial = segRT && segRT.delayMin != null ? segRT.delayMin : null;

  if(nowMin < salidaTotal){
    const fTxt = `${SEG.fechaISO.slice(8,10)}/${SEG.fechaISO.slice(5,7)}`;
    // con retraso conocido, lo que importa es la hora estimada a la que el
    // tren pasará de verdad por la estación de origen (donde nos montamos)
    const ret = oficial != null && oficial > 0 ? oficial : 0;
    const salidaPrev = salidaTotal + ret;
    cuerpo = `<div class="segbig">Sale a las ${fmtHora(salidaTotal)}${ret ? ` · prevista ~${fmtHora(salidaPrev)}` : ''} · faltan ${fmtRestante(salidaPrev - nowMin)}</div>
      <div class="meta">El ${fTxt} desde ${oNombre} · llegada a ${dNombre} a las ${fmtHora(llegadaTotal)}${ret ? ` (~${fmtHora(llegadaTotal + ret)} con el retraso)` : ''}</div>` +
      proximasHaciaEmbarque(legs[0], nowMin, oficial);
  } else if(nowMin >= llegadaTotal){
    cuerpo = `<div class="segbig">Llegada teórica: ${fmtHora(llegadaTotal)}</div>
      <div class="meta">Trayecto finalizado según horario. Esta tarjeta se cerrará sola.</div>`;
  } else {
    enViaje = true;
    const frac = Math.max(0, Math.min(1, (nowMin - salidaTotal)/(llegadaTotal - salidaTotal)));
    barra = `<div class="segbar"><div style="width:${(frac*100).toFixed(1)}%"></div></div>`;
    // primer leg aún no terminado
    let idx = 0;
    while(idx < legs.length - 1 && nowMin > legs[idx].paradas[legs[idx].paradas.length-1][1]) idx++;
    const leg = legs[idx], P = leg.paradas;
    const depLeg = P[0][2];
    if(nowMin < depLeg){
      // en el andén: espera o transbordo; con retraso conocido, contar hasta
      // la hora estimada real de salida
      const est = DB.estaciones[P[0][0]][0];
      const ret = oficial != null && oficial > 0 ? oficial : 0;
      const depPrev = depLeg + ret;
      cuerpo = `<div class="segbig">${idx === 0 ? 'En ' + est : 'Transbordo en ' + est}</div>
        <div class="meta">${leg.cat} ${trenLabel(leg.numero)} sale a las ${fmtHora(depLeg)}${ret ? ` · prevista ~${fmtHora(depPrev)}` : ''} · faltan ${fmtRestante(depPrev - nowMin)}</div>` +
        (idx === 0 ? proximasHaciaEmbarque(leg, nowMin, oficial) : hitosTransbordos(legs, idx, ret || null));
    } else {
      segLegActivo = leg;
      const retraso = oficial != null ? oficial : (segDelay != null ? Math.round(segDelay) : null);
      const tEff = nowMin - (retraso != null && retraso > 0 ? retraso : 0);
      let listado;
      if(legs.length > 1){
        // con transbordos: solo llegadas a los transbordos pendientes y al destino
        listado = hitosTransbordos(legs, idx, retraso);
      } else {
        const prox = [];
        for(let i=1;i<P.length;i++){
          const arr = P[i][1] >= 0 ? P[i][1] : P[i][2];
          if(arr >= tEff){
            const nom = DB.estaciones[P[i][0]][0];
            const est = retraso != null && retraso > 0 ? ` · prevista ~${fmtHora(arr + retraso)}` : '';
            prox.push(`<div class="parada"><span>${nom}</span><span>${fmtHora(arr)}${est}</span></div>`);
          }
        }
        listado = prox.length ? `<div class="meta" style="margin-top:8px">Próximas paradas:</div>` + prox.join('') : '';
      }
      const llegEst = legs.length === 1 && retraso != null && retraso > 0 ? ` · prevista ~${fmtHora(llegadaTotal + retraso)}` : '';
      cuerpo = `<div class="segbig">${leg.cat} ${trenLabel(leg.numero)} en marcha</div>
        <div class="meta">Llegada a ${dNombre}: ${fmtHora(llegadaTotal)}${llegEst}</div>
        ${listado}`;
      if(oficial != null){
        const fuente = segRT && segRT.estimado ? 'por la posición del tren' : 'dato oficial de Renfe';
        gps = Math.abs(oficial) < 2
          ? `<div class="seggps">📡 En hora (${fuente})</div>`
          : (oficial > 0
            ? `<div class="seggps tarde">📡 ~${oficial} min de retraso (${fuente})</div>`
            : `<div class="seggps">📡 ~${-oficial} min adelantado (${fuente})</div>`);
      } else if(retraso != null){
        gps = Math.abs(retraso) < 2
          ? `<div class="seggps">🛰 En hora según tu posición GPS</div>`
          : (retraso > 0
            ? `<div class="seggps tarde">🛰 ~${retraso} min de retraso según tu posición GPS</div>`
            : `<div class="seggps">🛰 ~${-retraso} min adelantado según tu posición GPS</div>`);
      } else {
        gps = `<div class="meta" style="margin-top:6px">🛰 Con permiso de ubicación se estima el retraso real.</div>`;
      }
    }
  }

  // línea 📍 construida DESPUÉS de conocer la fase: así una posición aceptada
  // durante la espera se revalida en cada repintado al pasar a "en marcha"
  const posi = trenPosicionandose();
  if(posi){
    posRT = `<div class="seggps">📍 Tu tren: ${posi.enCabecera
      ? `en ${posi.cabecera} (cabecera de la línea), pendiente de salir`
      : `pendiente de posicionarse en ${posi.cabecera}, estación origen de la línea`}</div>`;
  } else if(segRT && segRT.estIdx >= 0){
    const retP = oficial != null && oficial > 0 ? oficial
      : (segDelay != null && segDelay > 0 ? Math.round(segDelay) : 0);
    if(!(segLegActivo && posicionIncoherente(segLegActivo, segRT.estIdx, retP))){
      const nom = DB.estaciones[segRT.estIdx][0];
      const verbo = segRT.status === 'STOPPED_AT' ? 'parado en'
        : (segRT.status === 'INCOMING_AT' ? 'llegando a' : 'en camino a');
      posRT = `<div class="seggps">📍 Tu tren: ${verbo} ${nom}</div>`;
    }
  }

  // fuera de la fase en marcha (cuenta atrás, andén, transbordo) el retraso
  // oficial también es útil: el tren ya circula hacia ti
  if(!segLegActivo && oficial != null && Math.abs(oficial) >= 2){
    const fuente = segRT && segRT.estimado ? 'por su posición' : 'Renfe';
    gps = oficial > 0
      ? `<div class="seggps tarde">📡 El tren circula con ~${oficial} min de retraso (${fuente})</div>`
      : `<div class="seggps">📡 El tren circula ~${-oficial} min adelantado (${fuente})</div>`;
  }
  const croquis = croquisSVG();
  cont.innerHTML = `<div class="segcard">
    <div class="segcab">
      <span class="badge ${legs[0].cat}">${legs[0].cat}</span>
      <span class="ruta">${oNombre} → ${dNombre}</span>
      <button type="button" class="sharebtn stopseg">✕ Dejar de seguir</button>
    </div>
    ${barra}${cuerpo}${posRT}${gps}${croquis}
  </div>`;
  cont.querySelector('.stopseg').addEventListener('click', pararSeguimiento);
  segWakeLock(enViaje);
}

function tickSeguimiento(){
  if(!SEG) return;
  renderSeguimiento();
  // dato oficial GTFS-RT (Cercanías): consulta cada ~60 s
  const legRT = segLegParaRT();
  if(legRT && Date.now() - segRTts > 55000) actualizarRTSeguimiento(legRT);
  if(segLegActivo && navigator.geolocation){
    const base = new Date(SEG.fechaISO + 'T00:00:00').getTime();
    const leg = segLegActivo;
    navigator.geolocation.getCurrentPosition(p => {
      if(!SEG || segLegActivo !== leg) return;
      segPosUsuario = {lat: p.coords.latitude, lon: p.coords.longitude};
      // dispositivo lejos de la ruta varias veces seguidas: preguntar si
      // se quiere seguir con el seguimiento
      if(!segPreguntado && !segPregunta){
        if(distKmARuta(leg.paradas, p.coords.latitude, p.coords.longitude) > 5){
          segLejos++;
          if(segLejos >= 3){ segPregunta = true; renderSeguimiento(); return; }
        } else {
          segLejos = 0;
        }
      }
      const nowG = (Date.now() - base)/60000;
      const r = retrasoDesdePos(leg, p.coords.latitude, p.coords.longitude, nowG);
      if(r != null){
        // detección de "no vas montado": con el tren en marcha, la posición
        // del dispositivo proyectada sobre la ruta (nowG - r) debe avanzar;
        // si lleva ~3 min clavada (p. ej. viendo el tren desde el andén),
        // preguntar si se desea continuar el seguimiento
        if(!segPreguntado && !segPregunta){
          const s = nowG - r;
          if(segProg == null || s > segProg.s0 + 1.5){
            segProg = {t0: nowG, s0: s};
          } else if(nowG - segProg.t0 >= 3){
            segProg = null;
            segPregunta = true;
            renderSeguimiento();
            return;
          }
        }
        segDelay = segDelay == null ? r : (segDelay + r)/2;
        renderSeguimiento();
      }
    }, () => {}, {enableHighAccuracy: false, timeout: 8000, maximumAge: 20000});
  }
}

document.addEventListener('visibilitychange', () => {
  if(document.visibilityState === 'visible' && SEG) tickSeguimiento();
});

function textoDirecto(r){
  const dur = r.arrD >= 0 ? durTxt(r.arrD - r.depO) : '';
  return `🚆 ${fechaSeleccionada()}\\n` +
    `${r.cat} ${trenLabel(r.numero)} (${r.linea})\\n` +
    `${r.origenNombre} ${fmtHora(r.depO)} → ${r.destinoNombre} ${fmtHora(r.arrD)}` +
    (dur ? ` (${dur})` : '');
}

function textoConexion(c){
  const origenNombre = DB.estaciones[c.legs[0].oSt][0];
  const destinoNombre = DB.estaciones[c.legs[c.legs.length-1].dSt][0];
  const lineas = [`🚆 ${fechaSeleccionada()}  ${origenNombre} → ${destinoNombre}`];
  for(let i=0;i<c.legs.length;i++){
    const l = c.legs[i];
    if(i > 0){
      const prev = c.legs[i-1];
      const desde = DB.estaciones[prev.dSt][0], hacia = DB.estaciones[l.oSt][0];
      lineas.push(desde === hacia
        ? `  Transbordo en ${desde} (espera ${l.dep - prev.arr} min)`
        : `  Transbordo a pie ${desde} → ${hacia} (${l.dep - prev.arr} min entre trenes)`);
    }
    lineas.push(`${l.trip[0]} ${trenLabel(l.trip[2])} (${DB.lineas[l.trip[1]]}): ` +
      `${DB.estaciones[l.oSt][0]} ${fmtHora(l.dep)} → ${DB.estaciones[l.dSt][0]} ${fmtHora(l.arr)}`);
  }
  lineas.push(`Duración total: ${durTxt(c.arrD - c.depO)}`);
  return lineas.join('\\n');
}

function legHTML(trip, depMin, arrMin, desde, hasta){
  const cat = trip[0], linea = DB.lineas[trip[1]], numero = trip[2];
  return `
    <div class="leg">
      <div class="rescab">
        <span class="badge ${cat}">${cat}</span>
        <span class="tren">${trenLabel(numero)}</span>
        <span class="linea">${linea}</span>
      </div>
      <div class="horas">
        <div><span class="hh">${fmtHora(depMin)}</span><span class="st">${desde}</span></div>
        <span class="flecha">→</span>
        <div><span class="hh">${fmtHora(arrMin)}</span><span class="st">${hasta}</span></div>
      </div>
    </div>`;
}

function pintarDirecto(resEl, r){
  const dur = r.arrD >= 0 ? r.arrD - r.depO : null;
  const dtx = durTxt(dur);
  const div = document.createElement('div');
  div.className = 'resultado';
  div.innerHTML = `
    <div class="rescab">
      <span class="badge ${r.cat}">${r.cat}</span>
      <span class="tren">${trenLabel(r.numero)}</span>
      <span class="linea">${r.linea}</span>
    </div>
    <div class="horas">
      <div><span class="hh">${fmtHora(r.depO)}</span><span class="st">${r.origenNombre}</span></div>
      <span class="flecha">→</span>
      <div><span class="hh">${fmtHora(r.arrD)}</span><span class="st">${r.destinoNombre}</span></div>
      ${dtx ? `<span class="linea">(${dtx})</span>` : ''}
    </div>
    <div class="meta">
      Circula: ${diasTexto(r.dias)} · Vigencia: ${fmtFecha(r.fIni)} – ${fmtFecha(r.fFin)}<br>
      Trayecto completo del tren: ${r.origenReal} → ${r.destinoReal}
    </div>
    ${r.intermedias.length ? `<details><summary>${r.intermedias.length} parada(s) intermedia(s)</summary>
      ${r.intermedias.map(i => `<div class="parada"><span>${i.nombre}</span><span>${fmtHora(i.llegada)} / ${fmtHora(i.salida)}</span></div>`).join('')}
      </details>` : ''}
    ${incidenciasHTML(r.trip, r.posO, r.posD)}
    <div class="resfoot">
      <button type="button" class="sharebtn segbtn">🎯 Seguir</button>
      <button type="button" class="sharebtn calbtn" style="margin-left:0">🗓</button>
      <button type="button" class="sharebtn compbtn" style="margin-left:0">📤 Compartir</button>
    </div>
  `;
  div.querySelector('.segbtn').addEventListener('click', () =>
    iniciarSeguimiento([segDesdeTrip(r.trip, r.posO, r.posD)],
      (ultimaBusqueda && ultimaBusqueda.fechaISO) || document.getElementById('fecha').value));
  div.querySelector('.calbtn').addEventListener('click', () =>
    aCalendario(`Tren ${r.origenNombre} → ${r.destinoNombre}`, textoDirecto(r), r.depO, r.arrD));
  div.querySelector('.compbtn').addEventListener('click', () => compartir(textoDirecto(r)));
  resEl.appendChild(div);
}

function normalizaNumeroTren(s){
  return String(s).trim().replace(/^0+(?=\d)/, '');
}

function pintarTren(resEl, trip){
  const [cat, lineaIdx, numero, dias, fIni, fFin, stops] = trip;
  const n = stops.length/3;
  const origenNombre = DB.estaciones[stops[0]][0];
  const destinoNombre = DB.estaciones[stops[(n-1)*3]][0];
  const salida = stops[2];
  const llegada = stops[(n-1)*3+1];
  const intermedias = [];
  for(let p=1;p<n-1;p++){
    intermedias.push({nombre: DB.estaciones[stops[p*3]][0], llegada: stops[p*3+1], salida: stops[p*3+2]});
  }
  const dur = (llegada>=0 && salida>=0) ? llegada - salida : null;
  const dtx = durTxt(dur);
  const div = document.createElement('div');
  div.className = 'resultado';
  div.innerHTML = `
    <div class="rescab">
      <span class="badge ${cat}">${cat}</span>
      <span class="tren">${trenLabel(numero)}</span>
      <span class="linea">${DB.lineas[lineaIdx]}</span>
    </div>
    <div class="horas">
      <div><span class="hh">${fmtHora(salida)}</span><span class="st">${origenNombre}</span></div>
      <span class="flecha">→</span>
      <div><span class="hh">${fmtHora(llegada)}</span><span class="st">${destinoNombre}</span></div>
      ${dtx ? `<span class="linea">(${dtx})</span>` : ''}
    </div>
    <div class="meta">
      Circula: ${diasTexto(dias)} · Vigencia: ${fmtFecha(fIni)} – ${fmtFecha(fFin)}
    </div>
    ${intermedias.length ? `<details open><summary>${intermedias.length} parada(s) intermedia(s)</summary>
      ${intermedias.map(i => `<div class="parada"><span>${i.nombre}</span><span>${fmtHora(i.llegada)} / ${fmtHora(i.salida)}</span></div>`).join('')}
      </details>` : ''}
    ${incidenciasHTML(trip)}
  `;
  resEl.appendChild(div);
}

function buscarPorNumero(){
  const estadoEl = document.getElementById('estado');
  const resEl = document.getElementById('resultados');
  limpiarResultados();

  const q = normalizaNumeroTren(document.getElementById('num-tren').value);
  if(!q){
    estadoEl.textContent = 'Indica un número de tren.';
    return;
  }

  const encontrados = DB.trips.filter(trip => trip[2] && normalizaNumeroTren(trip[2]) === q);
  encontrados.sort((a,b) => a[4] - b[4]);

  if(!encontrados.length){
    estadoEl.textContent = `No se ha encontrado ningún tren con el número ${q}.`;
    return;
  }

  estadoEl.textContent = `${encontrados.length} circulación(es) encontrada(s) para el tren ${q}.`;
  for(const trip of encontrados) pintarTren(resEl, trip);
}

function pintarConexion(resEl, c){
  const partes = [];
  for(let i=0;i<c.legs.length;i++){
    const l = c.legs[i];
    if(i > 0){
      const prev = c.legs[i-1];
      const espera = l.dep - prev.arr;
      const desde = DB.estaciones[prev.dSt][0], hacia = DB.estaciones[l.oSt][0];
      partes.push(desde === hacia
        ? `<div class="transbordo">🔁 Transbordo en <b>${desde}</b> · espera ${espera} min</div>`
        : `<div class="transbordo">🚶 Transbordo a pie: <b>${desde}</b> → <b>${hacia}</b> · ${espera} min entre trenes</div>`);
    }
    partes.push(legHTML(l.trip, l.dep, l.arr, DB.estaciones[l.oSt][0], DB.estaciones[l.dSt][0]));
  }
  // incidencias de todos los tramos (cada uno limitado a su recorrido), sin duplicados
  const alSet = new Set();
  for(const l of c.legs){
    const stops = l.trip[6];
    let ini = -1, fin = -1;
    for(let p=0;p<stops.length/3;p++){
      const st = stops[p*3];
      if(st === l.oSt && ini === -1) ini = p;
      else if(st === l.dSt && ini !== -1){ fin = p; break; }
    }
    for(const a of alertasDeTrip(l.trip, ini, fin)) alSet.add(a);
  }
  partes.push(incidenciasListaHTML([...alSet]));
  partes.push(`<div class="resfoot"><span class="meta">Duración total: ${durTxt(c.arrD - c.depO)}</span></div>`);
  const div = document.createElement('div');
  div.className = 'resultado';
  div.innerHTML = partes.join('');
  const btnSeg = document.createElement('button');
  btnSeg.type = 'button';
  btnSeg.className = 'sharebtn';
  btnSeg.style.marginLeft = '0';
  btnSeg.textContent = '🎯 Seguir';
  btnSeg.addEventListener('click', () => {
    const legs = c.legs.map(l => {
      const stops = l.trip[6];
      let ini = -1, fin = -1;
      for(let p=0;p<stops.length/3;p++){
        const st = stops[p*3];
        if(st === l.oSt && ini === -1) ini = p;
        else if(st === l.dSt && ini !== -1){ fin = p; break; }
      }
      return segDesdeTrip(l.trip, ini, fin);
    });
    iniciarSeguimiento(legs, (ultimaBusqueda && ultimaBusqueda.fechaISO) || document.getElementById('fecha').value);
  });
  div.querySelector('.resfoot').appendChild(btnSeg);
  const btnCal = document.createElement('button');
  btnCal.type = 'button';
  btnCal.className = 'sharebtn';
  btnCal.style.marginLeft = '0';
  btnCal.textContent = '🗓';
  btnCal.addEventListener('click', () => {
    const o = DB.estaciones[c.legs[0].oSt][0], d = DB.estaciones[c.legs[c.legs.length-1].dSt][0];
    aCalendario(`Tren ${o} → ${d} (con transbordo)`, textoConexion(c), c.depO, c.arrD);
  });
  div.querySelector('.resfoot').appendChild(btnCal);
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'sharebtn';
  btn.style.marginLeft = '0';
  btn.textContent = '📤 Compartir';
  btn.addEventListener('click', () => compartir(textoConexion(c)));
  div.querySelector('.resfoot').appendChild(btn);
  resEl.appendChild(div);
}

// ---------- Filtros de resultados por categoría ----------
let ultimaBusqueda = null; // {tipo:'directos'|'con1'|'con2', items, minT, fechaISO}
let catsActivas = null;    // Set de categorías visibles; null = todas

function limpiarResultados(){
  ultimaBusqueda = null;
  catsActivas = null;
  document.getElementById('filtros').innerHTML = '';
  document.getElementById('resultados').innerHTML = '';
}

function catsDeItem(it, tipo){
  return tipo === 'directos' ? [it.cat] : it.legs.map(l => l.trip[0]);
}

function renderResultados(){
  const estadoEl = document.getElementById('estado');
  const resEl = document.getElementById('resultados');
  const filtEl = document.getElementById('filtros');
  resEl.innerHTML = '';
  filtEl.innerHTML = '';
  if(!ultimaBusqueda) return;
  const {tipo, items, minT} = ultimaBusqueda;
  const cats = [...new Set(items.flatMap(it => catsDeItem(it, tipo)))];
  if(!catsActivas) catsActivas = new Set(cats);
  if(cats.length > 1){
    for(const c of cats){
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'fchip' + (catsActivas.has(c) ? '' : ' off');
      b.textContent = CAT_LABEL[c] || c;
      b.addEventListener('click', () => {
        if(catsActivas.has(c)){ if(catsActivas.size > 1) catsActivas.delete(c); }
        else catsActivas.add(c);
        renderResultados();
      });
      filtEl.appendChild(b);
    }
  }
  const visibles = items.filter(it => catsDeItem(it, tipo).every(x => catsActivas.has(x)));
  const ocultos = items.length - visibles.length;
  const sufijo = ocultos > 0 ? ` (${ocultos} más oculto(s) por el filtro)` : '';
  if(tipo === 'directos'){
    estadoEl.textContent = `${visibles.length} tren(es) directo(s) encontrado(s).` + sufijo;
    for(const r of visibles) pintarDirecto(resEl, r);
  } else if(tipo === 'con1'){
    estadoEl.textContent = `Sin trenes directos. ${visibles.length} opción(es) con 1 transbordo ` +
      `(enlace mínimo ${minT} min):` + sufijo;
    for(const c of visibles) pintarConexion(resEl, c);
  } else {
    estadoEl.textContent = `Sin trenes directos ni enlaces con 1 transbordo. ` +
      `${visibles.length} opción(es) con 2 transbordos (enlace mínimo ${minT} min):` + sufijo;
    for(const c of visibles) pintarConexion(resEl, c);
  }
}

function buscar(){
  const oIdx = resolverEstacion('origen');
  const dIdx = resolverEstacion('destino');
  const estadoEl = document.getElementById('estado');
  limpiarResultados();

  if(oIdx < 0 || dIdx < 0){
    estadoEl.textContent = 'Selecciona un origen y un destino válidos de la lista de sugerencias.';
    return;
  }
  if(oIdx === dIdx){
    estadoEl.textContent = 'El origen y el destino deben ser distintos.';
    return;
  }

  const fecha = document.getElementById('fecha').value; // YYYY-MM-DD
  const hora = document.getElementById('hora').value;   // HH:MM
  const todoElDia = document.getElementById('todo-el-dia').checked;
  if(!fecha){ estadoEl.textContent = 'Indica una fecha.'; return; }

  guardarTrayecto(DB.estaciones[oIdx][0], DB.estaciones[dIdx][0]);

  const dateInt = parseInt(fecha.replace(/-/g,''), 10);
  const jsDate = new Date(fecha + 'T00:00:00');
  const weekdayBit = (jsDate.getDay() + 6) % 7; // 0=lunes
  const [hh, mm] = (hora || '00:00').split(':').map(Number);
  const minSel = todoElDia ? 0 : (hh*60 + mm);
  const minT = Math.max(0, parseInt(document.getElementById('enlace-min').value, 10) || 10);

  // Circulaciones activas en la fecha seleccionada
  const activos = [];
  for(const trip of DB.trips){
    if(dateInt < trip[4] || dateInt > trip[5]) continue;
    if((trip[3] & (1<<weekdayBit)) === 0) continue;
    activos.push(trip);
  }

  const directos = buscarDirectos(activos, oIdx, dIdx, minSel);
  if(directos.length){
    ultimaBusqueda = {tipo: 'directos', items: directos, minT, fechaISO: fecha};
    renderResultados();
    return;
  }

  // Sin directos: buscar enlaces con 1 transbordo y, si tampoco hay, con 2
  const llegadas1 = llegadasIniciales(activos, oIdx, dIdx, minSel);
  const enlaces1 = cerrarEnDestino(llegadas1, activos, oIdx, dIdx, minT);
  if(enlaces1.length){
    ultimaBusqueda = {tipo: 'con1', items: enlaces1, minT, fechaISO: fecha};
    renderResultados();
    return;
  }

  const llegadas2 = expandirTransbordo(llegadas1, activos, oIdx, dIdx, minT);
  const enlaces2 = cerrarEnDestino(llegadas2, activos, oIdx, dIdx, minT);
  if(enlaces2.length){
    ultimaBusqueda = {tipo: 'con2', items: enlaces2, minT, fechaISO: fecha};
    renderResultados();
    return;
  }

  estadoEl.textContent = `Sin trenes directos ni enlaces con 1 o 2 transbordos (mínimo ${minT} min) de ` +
    `${DB.estaciones[oIdx][0]} a ${DB.estaciones[dIdx][0]} ese día` +
    (todoElDia ? '.' : ' a partir de esa hora.');
}

// ---------- Salidas desde una estación ----------
function buscarSalidas(){
  const estadoEl = document.getElementById('estado');
  const resEl = document.getElementById('resultados');
  limpiarResultados();

  const stIdx = resolverEstacion('sal-estacion');
  if(stIdx < 0){
    estadoEl.textContent = 'Selecciona una estación válida de la lista de sugerencias.';
    return;
  }
  const fecha = document.getElementById('sal-fecha').value;
  if(!fecha){ estadoEl.textContent = 'Indica una fecha.'; return; }
  const hora = document.getElementById('sal-hora').value;
  const dateInt = parseInt(fecha.replace(/-/g,''), 10);
  const weekdayBit = (new Date(fecha + 'T00:00:00').getDay() + 6) % 7;
  const [hh, mm] = (hora || '00:00').split(':').map(Number);
  const minSel = hh*60 + mm;

  const salidas = [];
  for(const trip of DB.trips){
    if(dateInt < trip[4] || dateInt > trip[5]) continue;
    if((trip[3] & (1<<weekdayBit)) === 0) continue;
    const stops = trip[6], n = stops.length/3;
    for(let p=0;p<n-1;p++){  // la última parada no es una salida
      if(stops[p*3] !== stIdx) continue;
      const dep = stops[p*3+2];
      if(dep >= minSel) salidas.push({dep, trip, pos: p});
      break;
    }
  }
  salidas.sort((a,b) => a.dep - b.dep);

  const MAX = 40;
  const nombre = DB.estaciones[stIdx][0];
  if(!salidas.length){
    estadoEl.textContent = `Sin salidas desde ${nombre} ese día a partir de esa hora.`;
    return;
  }
  estadoEl.textContent = `${salidas.length} salida(s) desde ${nombre}` +
    (salidas.length > MAX ? ` (se muestran las ${MAX} primeras).` : '.') +
    ' Toca una salida para abrirla en Trayecto.';
  const lista = salidas.slice(0, MAX);
  const card = document.createElement('div');
  card.className = 'resultado';
  card.innerHTML = lista.map((s, i) => {
    const stops = s.trip[6], n = stops.length/3;
    const destino = DB.estaciones[stops[(n-1)*3]][0];
    return `<div class="salida" data-i="${i}">
      <span class="hh">${fmtHora(s.dep)}</span>
      <span class="badge ${s.trip[0]}">${s.trip[0]}</span>
      <span class="dest">${destino}</span>
      <span class="linea">${DB.lineas[s.trip[1]]}</span>
    </div>`;
  }).join('');
  // al tocar una salida: cargarla en la pestaña Trayecto, buscar allí y
  // arrancar automáticamente el seguimiento de ese tren
  card.addEventListener('click', (e) => {
    const fila = e.target.closest('.salida');
    if(!fila) return;
    const s = lista[parseInt(fila.dataset.i, 10)];
    const stops = s.trip[6], n = stops.length/3;
    setEstacion('origen', DB.estaciones[stIdx][0]);
    setEstacion('destino', DB.estaciones[stops[(n-1)*3]][0]);
    document.getElementById('fecha').value = fecha;
    document.getElementById('hora').value = fmtHora(s.dep);
    document.getElementById('todo-el-dia').checked = false;
    document.getElementById('tab-estacion').click();
    buscar();
    iniciarSeguimiento([segDesdeTrip(s.trip, s.pos, n - 1)], fecha);
  });
  resEl.appendChild(card);
  anotarRetrasosSalidas(card, lista, fecha);
}

// Anota en la lista de salidas el retraso y la hora prevista de los trenes
// presentes en el feed GTFS-RT de Renfe (Cercanías, solo para el día de hoy).
async function anotarRetrasosSalidas(card, lista, fecha){
  if(fecha !== hoyLocal()) return;
  const bytes = await fetchBytes(URL_RT_TRIP);
  if(!bytes || !card.isConnected) return;
  let d;
  try{ d = JSON.parse(utf8.decode(bytes)); }catch(e){ return; }
  const retrasos = {};
  for(const e of (d.entity || [])){
    const t = e.tripUpdate;
    if(!t) continue;
    const num = numeroDeTripId(t.trip && t.trip.tripId);
    if(!num) continue;
    let del = t.delay != null ? t.delay : null;
    const stu = t.stopTimeUpdate || [];
    for(let i=stu.length-1;i>=0;i--){
      const a = stu[i].arrival || stu[i].departure;
      if(a && a.delay != null){ del = a.delay; break; }
    }
    if(del != null) retrasos[num] = Math.round(del/60);
  }
  lista.forEach((s, i) => {
    const num = normalizaNumeroTren(s.trip[2] || '');
    if(!num || !(num in retrasos)) return;
    const fila = card.querySelector(`.salida[data-i="${i}"]`);
    if(!fila) return;
    const r = retrasos[num];
    const span = document.createElement('span');
    span.className = 'ret' + (r >= 1 ? ' tarde' : '');
    span.textContent = Math.abs(r) < 1 ? 'en hora'
      : `~${fmtHora(s.dep + r)} (${r > 0 ? '+' + r : r} min)`;
    fila.querySelector('.hh').after(span);
  });
}

document.getElementById('btn-buscar').addEventListener('click', buscar);
document.getElementById('btn-buscar-numero').addEventListener('click', buscarPorNumero);
document.getElementById('btn-salidas').addEventListener('click', buscarSalidas);
document.getElementById('inc-ambito').addEventListener('change', renderIncidencias);
document.getElementById('inc-linea').addEventListener('change', renderIncidencias);
document.getElementById('num-tren').addEventListener('keydown', (e) => {
  if(e.key === 'Enter') buscarPorNumero();
});

// ---------- Pestañas ----------
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t===tab));
    document.querySelectorAll('.tabpanel').forEach(p =>
      p.classList.toggle('active', p.id === 'panel-' + tab.dataset.tab));
    document.getElementById('estado').textContent = '';
    limpiarResultados();
    if(tab.dataset.tab === 'incidencias') renderIncidencias();
  });
});

// ---------- Inicialización ----------
function hoyLocal(){
  const d = new Date();
  const off = d.getTimezoneOffset();
  return new Date(d.getTime() - off*60000).toISOString().slice(0,10);
}
function ahoraLocal(){
  const d = new Date();
  return String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0');
}

function avisoDatos(){
  const fechaTxt = `${DATA_FECHA.slice(8,10)}/${DATA_FECHA.slice(5,7)}/${DATA_FECHA.slice(0,4)}`;
  document.getElementById('fecha-datos').textContent =
    ` Horarios extraídos de los operadores el ${fechaTxt}.`;
  const dias = Math.floor((Date.now() - new Date(DATA_FECHA + 'T00:00:00').getTime())/86400000);
  if(dias > 60){
    const el = document.getElementById('aviso-datos');
    el.textContent = `⚠️ Los horarios de esta app se extrajeron hace ${Math.round(dias/30)} meses ` +
      `(${fechaTxt}) y pueden haber cambiado. Si hay una versión más reciente de la app, actualízala.`;
    el.style.display = 'block';
  }
}

(async function init(){
  try{ // restos de versiones anteriores
    localStorage.removeItem('bt_recientes');
    localStorage.removeItem('bt_seguimiento');
  }catch(e){}
  document.getElementById('fecha').value = hoyLocal();
  document.getElementById('hora').value = ahoraLocal();
  document.getElementById('sal-fecha').value = hoyLocal();
  document.getElementById('sal-hora').value = ahoraLocal();
  setupAutocomplete('origen','sugg-origen');
  setupAutocomplete('destino','sugg-destino');
  setupAutocomplete('sal-estacion','sugg-sal');
  avisoDatos();
  try{
    await cargarDatos();
    const btn = document.getElementById('btn-buscar');
    btn.disabled = false;
    btn.textContent = 'Buscar trenes';
    const btnNum = document.getElementById('btn-buscar-numero');
    btnNum.disabled = false;
    btnNum.textContent = 'Buscar tren';
    const btnSal = document.getElementById('btn-salidas');
    btnSal.disabled = false;
    btnSal.textContent = 'Ver salidas';
    renderChips();
    poblarAmbitos();
    cargarIncidencias(); // en segundo plano; si no hay red, la pestaña no aparece
  }catch(e){
    document.getElementById('estado').textContent = 'Error al cargar los datos: ' + e.message;
    console.error(e);
  }
})();
</script>
</body>
</html>
"""


def main():
    path = pathlib.Path(B64_PATH)
    b64 = path.read_text().strip()
    # Fecha de extracción de los horarios: la de generación del payload
    fecha = datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()
    html = TEMPLATE.replace("__DATA_B64__", b64).replace("__DATA_FECHA__", fecha)
    pathlib.Path(OUT_HTML).write_text(html, encoding="utf-8")
    print(f"Generado: {OUT_HTML} ({len(html)/1e6:.1f} MB, horarios del {fecha})")


if __name__ == "__main__":
    main()
