const API = window.MATERA_API || `${location.protocol}//${location.hostname}:5000/api`;
const INTERVALO_MS = 5000;
const $ = (id) => document.getElementById(id);
let token = null;
let plantaActual = null;
let temporizador = null;

function guardar(clave, valor) { try { valor === null ? sessionStorage.removeItem(clave) : sessionStorage.setItem(clave, valor); } catch (e) { /* sin almacenamiento */ } }
function leer(clave) { try { return sessionStorage.getItem(clave); } catch (e) { return null; } }

async function pedir(ruta, { metodo = "GET", cuerpo, conToken = true } = {}) {
  const cabeceras = { "Content-Type": "application/json" };
  if (conToken && token) cabeceras.Authorization = `Bearer ${token}`;
  const r = await fetch(API + ruta, { method: metodo, headers: cabeceras, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  const datos = r.status === 202 || r.status === 204 ? {} : await r.json().catch(() => ({}));
  if (!r.ok) {
    if (r.status === 401 && conToken) cerrarSesion();
    throw new Error(datos.mensaje || `Error ${r.status}`);
  }
  return datos;
}

function celda(texto, clase) { const td = document.createElement("td"); td.textContent = texto; if (clase) td.className = clase; return td; }
function fila(...celdas) { const tr = document.createElement("tr"); celdas.forEach((c) => tr.append(c)); return tr; }
function mostrarMensaje(id, texto, error = true) { const m = $(id); m.textContent = texto; m.className = error ? "mensaje error" : "mensaje"; }

function iniciarSesion(nuevoToken, correo) {
  token = nuevoToken;
  guardar("token", token);
  guardar("correo", correo);
  $("acceso").hidden = true;
  $("panel").hidden = false;
  $("sesion-barra").hidden = false;
  $("usuario").textContent = correo || "";
  cargarPlantas();
}

function cerrarSesion() {
  token = null; plantaActual = null;
  guardar("token", null); guardar("correo", null);
  clearInterval(temporizador);
  $("acceso").hidden = false; $("panel").hidden = true; $("sesion-barra").hidden = true; $("detalle").hidden = true;
}

$("form-acceso").addEventListener("submit", async (e) => {
  e.preventDefault();
  const accion = e.submitter.dataset.accion;
  const datos = Object.fromEntries(new FormData(e.target));
  try {
    if (accion === "usuarios") await pedir("/usuarios", { metodo: "POST", cuerpo: datos, conToken: false });
    const { token: t } = await pedir("/sesion", { metodo: "POST", cuerpo: datos, conToken: false });
    mostrarMensaje("msg-acceso", "");
    iniciarSesion(t, datos.correo);
  } catch (err) { mostrarMensaje("msg-acceso", err.message); }
});

$("salir").addEventListener("click", cerrarSesion);

async function cargarPlantas() {
  try {
    const plantas = await pedir("/plantas");
    const lista = $("lista-plantas");
    lista.replaceChildren();
    if (!plantas.length) { const li = document.createElement("li"); li.textContent = "Aún no tienes materas."; lista.append(li); }
    plantas.forEach((p) => {
      const li = document.createElement("li");
      const texto = document.createElement("span");
      texto.textContent = `${p.nombre} · ${p.especie} · ${p.dispositivo || "sin dispositivo"}`;
      const ver = document.createElement("button");
      ver.textContent = "Ver"; ver.className = "secundario";
      ver.addEventListener("click", () => abrirPlanta(p));
      li.append(texto, ver);
      lista.append(li);
    });
  } catch (err) { mostrarMensaje("msg-planta", err.message); }
}

$("form-planta").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await pedir("/plantas", { metodo: "POST", cuerpo: Object.fromEntries(new FormData(e.target)) });
    e.target.reset();
    mostrarMensaje("msg-planta", "Matera agregada. Enciende el dispositivo en los próximos 10 minutos.", false);
    cargarPlantas();
  } catch (err) { mostrarMensaje("msg-planta", err.message); }
});

function abrirPlanta(planta) {
  plantaActual = planta;
  $("detalle").hidden = false;
  $("detalle-nombre").textContent = planta.nombre;
  clearInterval(temporizador);
  actualizarDetalle();
  temporizador = setInterval(actualizarDetalle, INTERVALO_MS);
}

async function actualizarDetalle() {
  if (!plantaActual) return;
  try {
    const [estado, historial] = await Promise.all([
      pedir(`/plantas/${plantaActual.id}/estado`),
      pedir(`/plantas/${plantaActual.id}/lecturas?limite=10`),
    ]);
    const d = estado.diagnostico;
    $("badge").textContent = d ? d.estado : "Sin lecturas";
    $("badge").className = "badge " + (d ? d.estado : "");
    $("detalle-puntos").textContent = `${estado.puntos} puntos`;
    $("detalle-actualizado").textContent = estado.ultimaLectura ? `Última lectura: ${new Date(estado.ultimaLectura.momento).toLocaleString()}` : "El dispositivo todavía no ha enviado lecturas.";
    const cuerpo = $("tabla-parametros").tBodies[0];
    cuerpo.replaceChildren(...(d ? d.parametros.map((p) => fila(
      celda(p.nombre), celda(`${p.valor} ${p.unidad}`), celda(`${p.rango.minimo} – ${p.rango.maximo}`), celda(p.clasificacion, p.clasificacion))) : []));
    $("recomendaciones").replaceChildren(...(d ? d.recomendaciones.map((r) => { const li = document.createElement("li"); li.textContent = r; return li; }) : []));
    $("tabla-historial").tBodies[0].replaceChildren(...historial.map((l) => fila(
      celda(new Date(l.momento).toLocaleTimeString()), celda(l.humedad), celda(l.luz), celda(l.temperatura), celda(l.estado))));
  } catch (err) { $("detalle-actualizado").textContent = err.message; }
}

$("reemparejar").addEventListener("click", async () => {
  if (!plantaActual) return;
  try {
    await pedir(`/plantas/${plantaActual.id}/reemparejar`, { metodo: "POST" });
    $("detalle-actualizado").textContent = "Listo: el dispositivo pedirá un token nuevo en los próximos 10 minutos.";
  } catch (err) { $("detalle-actualizado").textContent = err.message; }
});

$("form-diagnostico").addEventListener("submit", async (e) => {
  e.preventDefault();
  const datos = Object.fromEntries(new FormData(e.target));
  ["humedad", "luz", "temperatura"].forEach((c) => { datos[c] = datos[c] === "" ? null : Number(datos[c]); });
  try {
    const d = await pedir("/diagnostico", { metodo: "POST", cuerpo: datos, conToken: false });
    const partes = d.recomendaciones.length ? ` ${d.recomendaciones.join(" ")}` : "";
    mostrarMensaje("resultado-manual", `${d.estado}.${partes}`, d.estado !== "SALUDABLE");
  } catch (err) { mostrarMensaje("resultado-manual", err.message); }
});

async function cargarEspecies() {
  try {
    const especies = await pedir("/especies", { conToken: false });
    ["especies", "especies-manual"].forEach((id) => {
      $(id).replaceChildren(...especies.map((e) => { const o = document.createElement("option"); o.value = e.especie; o.textContent = `${e.nombreComun} (${e.especie})`; return o; }));
    });
  } catch (err) { mostrarMensaje("resultado-manual", "No se pudo cargar la lista de especies."); }
}

cargarEspecies();
const guardado = leer("token");
if (guardado) iniciarSesion(guardado, leer("correo"));
