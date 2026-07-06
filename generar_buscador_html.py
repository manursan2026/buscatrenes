#!/usr/bin/env python3
"""
generar_buscador_html.py
=========================
Ensambla `buscador_trenes.html` (fichero único, autocontenido) a partir del
payload de datos generado por build_buscador_data.py (`buscador_data.b64`).

No requiere red ni build steps adicionales: solo lee el .b64 y escribe el
HTML final con la plantilla (CSS+JS) embebida abajo.
"""
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
  input[type=text],input[type=date],input[type=time],input[type=number]{
    width:100%;padding:12px 13px;border-radius:11px;border:1px solid var(--border);
    background:var(--panel2);color:var(--text);font-size:16px;
    transition:border-color .15s, box-shadow .15s;
  }
  input:focus{outline:none;border-color:var(--accent);
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
  .leg{padding:4px 0}
  .leg + .leg{border-top:none}
  footer{color:var(--muted);font-size:.72rem;text-align:center;margin-top:28px;
    opacity:.75;line-height:1.5}
  @media (min-width:600px){ .wrap{padding-top:26px} }
</style>
</head>
<body>
<div class="wrap">
  <h1>🚆 BuscaTrenes</h1>

  <div class="card">
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

    <button class="buscar" id="btn-buscar" disabled>Cargando datos…</button>
  </div>

  <div id="estado"></div>
  <div id="resultados"></div>
  <div id="toast"></div>

  <footer>Datos horarios públicos de los operadores ferroviarios españoles (alta velocidad, larga y media distancia, cercanías y regionales). Se muestran trenes directos; si no hay, se buscan automáticamente enlaces con 1 o 2 transbordos respetando el tiempo mínimo de enlace indicado (+10 min si el cambio es a pie entre estaciones próximas).</footer>
</div>

<script>
const DATA_B64 = "__DATA_B64__";
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

// ---------- Geolocalización ----------
function haversine(lat1,lon1,lat2,lon2){
  const R=6371, toRad=x=>x*Math.PI/180;
  const dLat=toRad(lat2-lat1), dLon=toRad(lon2-lon1);
  const a=Math.sin(dLat/2)**2 + Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dLon/2)**2;
  return 2*R*Math.asin(Math.sqrt(a));
}

document.getElementById('btn-geo').addEventListener('click', () => {
  const st = document.getElementById('geo-status');
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
      const input = document.getElementById('origen');
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
      cat, linea: DB.lineas[lineaIdx], numero, dias, fIni, fFin,
      depO, arrD, intermedias,
      origenNombre: DB.estaciones[oIdx][0], destinoNombre: DB.estaciones[dIdx][0],
      origenReal: DB.estaciones[stops[0]][0], destinoReal: DB.estaciones[stops[stops.length-3]][0],
    });
  }
  resultados.sort((a,b) => a.depO - b.depO);
  return resultados;
}

const ANDAR_MIN = 10; // minutos extra si el transbordo es entre estaciones distintas del mismo nodo

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
        const margen = minT + (c.stIdx !== st ? ANDAR_MIN : 0);
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
        const margen = minT + (c.stIdx !== st ? ANDAR_MIN : 0);
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
      <button type="button" class="sharebtn">📤 Compartir</button>
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
  `;
  div.querySelector('.sharebtn').addEventListener('click', () => compartir(textoDirecto(r)));
  resEl.appendChild(div);
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
  partes.push(`<div class="resfoot"><span class="meta">Duración total: ${durTxt(c.arrD - c.depO)}</span></div>`);
  const div = document.createElement('div');
  div.className = 'resultado';
  div.innerHTML = partes.join('');
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'sharebtn';
  btn.textContent = '📤 Compartir';
  btn.addEventListener('click', () => compartir(textoConexion(c)));
  div.querySelector('.resfoot').appendChild(btn);
  resEl.appendChild(div);
}

function buscar(){
  const oIdx = resolverEstacion('origen');
  const dIdx = resolverEstacion('destino');
  const estadoEl = document.getElementById('estado');
  const resEl = document.getElementById('resultados');
  resEl.innerHTML = '';

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
    estadoEl.textContent = `${directos.length} tren(es) directo(s) encontrado(s).`;
    for(const r of directos) pintarDirecto(resEl, r);
    return;
  }

  // Sin directos: buscar enlaces con 1 transbordo y, si tampoco hay, con 2
  const llegadas1 = llegadasIniciales(activos, oIdx, dIdx, minSel);
  const enlaces1 = cerrarEnDestino(llegadas1, activos, oIdx, dIdx, minT);
  if(enlaces1.length){
    estadoEl.textContent = `Sin trenes directos. ${enlaces1.length} opción(es) con 1 transbordo ` +
      `(enlace mínimo ${minT} min):`;
    for(const c of enlaces1) pintarConexion(resEl, c);
    return;
  }

  const llegadas2 = expandirTransbordo(llegadas1, activos, oIdx, dIdx, minT);
  const enlaces2 = cerrarEnDestino(llegadas2, activos, oIdx, dIdx, minT);
  if(enlaces2.length){
    estadoEl.textContent = `Sin trenes directos ni enlaces con 1 transbordo. ` +
      `${enlaces2.length} opción(es) con 2 transbordos (enlace mínimo ${minT} min):`;
    for(const c of enlaces2) pintarConexion(resEl, c);
    return;
  }

  estadoEl.textContent = `Sin trenes directos ni enlaces con 1 o 2 transbordos (mínimo ${minT} min) de ` +
    `${DB.estaciones[oIdx][0]} a ${DB.estaciones[dIdx][0]} ese día` +
    (todoElDia ? '.' : ' a partir de esa hora.');
}

document.getElementById('btn-buscar').addEventListener('click', buscar);

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

(async function init(){
  document.getElementById('fecha').value = hoyLocal();
  document.getElementById('hora').value = ahoraLocal();
  setupAutocomplete('origen','sugg-origen');
  setupAutocomplete('destino','sugg-destino');
  try{
    await cargarDatos();
    const btn = document.getElementById('btn-buscar');
    btn.disabled = false;
    btn.textContent = 'Buscar trenes';
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
    b64 = pathlib.Path(B64_PATH).read_text().strip()
    html = TEMPLATE.replace("__DATA_B64__", b64)
    pathlib.Path(OUT_HTML).write_text(html, encoding="utf-8")
    print(f"Generado: {OUT_HTML} ({len(html)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
