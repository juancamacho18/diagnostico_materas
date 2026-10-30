// Front de la matera: solo habla con la API por fetch. Ningun dato se
// genera aqui; el estado de la planta se pide cada pocos segundos.

const API_BASE = `${location.protocol === "file:" ? "http:" : location.protocol}//${location.hostname || "127.0.0.1"}:5000/api/v1`;
const INTERVALO_MS = 5000;

let token = localStorage.getItem("matera_token");
let plantaSeleccionada = null;
let temporizador = null;

const $ = (id) => document.getElementById(id);

function mostrarMensaje(texto, ok = false) {
  const caja = $("mensaje");
  caja.textContent = texto;
  caja.classList.toggle("ok", ok);
  caja.classList.remove("oculto");
}

function limpiarMensaje() {
  $("mensaje").classList.add("oculto");
}

function crear(etiqueta, texto, clase) {
  const nodo = document.createElement(etiqueta);
  if (texto !== undefined) nodo.textContent = texto;
  if (clase) nodo.className = clase;
  return nodo;
}

async function api(ruta, { metodo = "GET", cuerpo, conToken = true } = {}) {
  const cabeceras = { "Content-Type": "application/json" };
  if (conToken && token) cabeceras["Authorization"] = `Bearer ${token}`;

  let respuesta;
  try {
    respuesta = await fetch(API_BASE + ruta, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    });
  } catch (e) {
    throw new Error("No se pudo conectar con el servidor.");
  }

  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    if (respuesta.status === 401 && conToken) cerrarSesion();
    throw new Error(datos.mensaje || "Ocurrió un error.");
  }
  return datos;
}

// ---------- sesión ----------

function correoDelToken() {
  return localStorage.getItem("matera_correo") || "";
}

function mostrarVista() {
  const conSesion = Boolean(token);
  $("vista-auth").classList.toggle("oculto", conSesion);
  $("vista-app").classList.toggle("oculto", !conSesion);
  $("sesion").classList.toggle("oculto", !conSesion);
  $("usuario-correo").textContent = correoDelToken();
}

function cerrarSesion() {
  token = null;
  localStorage.removeItem("matera_token");
  localStorage.removeItem("matera_correo");
  detenerSeguimiento();
  mostrarVista();
}

async function entrar(evento) {
  evento.preventDefault();
  limpiarMensaje();
  const correo = $("correo").value.trim();
  try {
    const datos = await api("/auth/login", {
      metodo: "POST", conToken: false,
      cuerpo: { correo, clave: $("clave").value },
    });
    token = datos.token;
    localStorage.setItem("matera_token", token);
    localStorage.setItem("matera_correo", correo);
    $("clave").value = "";
    mostrarVista();
    await iniciarApp();
  } catch (e) {
    mostrarMensaje(e.message);
  }
}

async function crearCuenta() {
  limpiarMensaje();
  try {
    await api("/auth/registro", {
      metodo: "POST", conToken: false,
      cuerpo: { correo: $("correo").value.trim(), clave: $("clave").value },
    });
    mostrarMensaje("Cuenta creada. Ya puedes entrar.", true);
  } catch (e) {
    mostrarMensaje(e.message);
  }
}

// ---------- plantas ----------

async function cargarEspecies() {
  const especies = await api("/especies", { conToken: false });
  for (const id of ["planta-especie", "manual-especie"]) {
    const select = $(id);
    select.replaceChildren();
    for (const e of especies) {
      const opcion = crear("option", e.nombreComun ? `${e.nombre} (${e.nombreComun})` : e.nombre);
      opcion.value = e.nombre;
      select.appendChild(opcion);
    }
  }
}

async function cargarPlantas() {
  const plantas = await api("/plantas");
  const cuerpo = $("plantas-tbody");
  cuerpo.replaceChildren();
  $("sin-plantas").classList.toggle("oculto", plantas.length > 0);

  for (const p of plantas) {
    const fila = crear("tr");
    for (const texto of [p.nombre, p.id, p.especie, p.dispositivoId]) {
      fila.appendChild(crear("td", texto));
    }
    const celda = crear("td");
    const boton = crear("button", "Ver", "tabla");
    boton.type = "button";
    boton.addEventListener("click", () => seguir(p));
    celda.appendChild(boton);
    fila.appendChild(celda);
    cuerpo.appendChild(fila);
  }
}

async function registrarPlanta(evento) {
  evento.preventDefault();
  limpiarMensaje();
  try {
    const datos = await api("/plantas", {
      metodo: "POST",
      cuerpo: {
        nombre: $("planta-nombre").value,
        especie: $("planta-especie").value,
        dispositivo: $("planta-dispositivo").value,
      },
    });
    $("token-valor").textContent = datos.tokenDispositivo;
    $("token-box").classList.remove("oculto");
    $("planta-form").reset();
    mostrarMensaje(`Matera ${datos.planta.id} registrada.`, true);
    await cargarPlantas();
  } catch (e) {
    mostrarMensaje(e.message);
  }
}

// ---------- seguimiento (consulta periódica) ----------

function detenerSeguimiento() {
  if (temporizador) clearInterval(temporizador);
  temporizador = null;
  plantaSeleccionada = null;
  $("detalle").classList.add("oculto");
}

function seguir(planta) {
  detenerSeguimiento();
  plantaSeleccionada = planta;
  $("detalle-nombre").textContent = planta.nombre;
  $("detalle-especie").textContent = planta.especie;
  $("intervalo-texto").textContent = INTERVALO_MS / 1000;
  $("detalle").classList.remove("oculto");
  actualizar();
  temporizador = setInterval(actualizar, INTERVALO_MS);
}

async function actualizar() {
  if (!plantaSeleccionada) return;
  const id = plantaSeleccionada.id;
  try {
    const [estado, historial] = await Promise.all([
      api(`/plantas/${id}/estado`),
      api(`/plantas/${id}/historial?limite=10`),
    ]);
    if (!plantaSeleccionada || plantaSeleccionada.id !== id) return;
    pintarEstado(estado);
    pintarHistorial(historial);
    $("detalle-consulta").textContent = new Date().toLocaleTimeString();
    limpiarMensaje();
  } catch (e) {
    mostrarMensaje(e.message);
  }
}

function pintarEstado(actual) {
  const etiqueta = $("detalle-estado");
  const lista = $("detalle-parametros");
  const recomendaciones = $("detalle-recomendaciones");
  lista.replaceChildren();
  recomendaciones.replaceChildren();

  $("sin-lecturas").classList.toggle("oculto", Boolean(actual.diagnostico));
  $("detalle-recomendaciones-wrap").classList.add("oculto");

  if (!actual.diagnostico) {
    etiqueta.textContent = "";
    etiqueta.className = "etiqueta";
    return;
  }

  etiqueta.textContent = actual.diagnostico.estado.replace("_", " ");
  etiqueta.className = `etiqueta ${actual.diagnostico.estado}`;

  for (const p of actual.diagnostico.parametros) {
    const item = crear("li");
    item.appendChild(crear("strong", `${p.nombre}: ${p.valor} ${p.unidad}`));
    item.appendChild(crear("div", `${p.estado} · ideal ${p.rangoOptimo[0]} a ${p.rangoOptimo[1]}`, "suave"));
    lista.appendChild(item);
  }

  if (actual.diagnostico.recomendaciones.length > 0) {
    for (const texto of actual.diagnostico.recomendaciones) {
      recomendaciones.appendChild(crear("li", texto));
    }
    $("detalle-recomendaciones-wrap").classList.remove("oculto");
  }
}

function pintarHistorial(registros) {
  const cuerpo = $("historial-tbody");
  cuerpo.replaceChildren();
  for (const r of registros) {
    const fila = crear("tr");
    fila.appendChild(crear("td", new Date(r.momento).toLocaleTimeString()));
    fila.appendChild(crear("td", `${r.humedad} %`));
    fila.appendChild(crear("td", `${r.luz} lx`));
    fila.appendChild(crear("td", `${r.temperatura} °C`));
    const celda = crear("td");
    celda.appendChild(crear("span", r.estado.replace("_", " "), `etiqueta ${r.estado}`));
    fila.appendChild(celda);
    cuerpo.appendChild(fila);
  }
}

// ---------- diagnóstico manual (el de la fase anterior) ----------

async function diagnosticarManual(evento) {
  evento.preventDefault();
  limpiarMensaje();
  try {
    const d = await api("/diagnosticos", {
      metodo: "POST", conToken: false,
      cuerpo: {
        especie: $("manual-especie").value,
        humedad: $("manual-humedad").value,
        luz: $("manual-luz").value,
        temperatura: $("manual-temperatura").value,
      },
    });
    const extra = d.recomendaciones.length ? " " + d.recomendaciones.join(" ") : "";
    $("manual-resultado").textContent = `Estado: ${d.estado.replace("_", " ")}.${extra}`;
  } catch (e) {
    $("manual-resultado").textContent = "";
    mostrarMensaje(e.message);
  }
}

// ---------- arranque ----------

async function iniciarApp() {
  try {
    await cargarEspecies();
    await cargarPlantas();
  } catch (e) {
    mostrarMensaje(e.message);
  }
}

$("auth-form").addEventListener("submit", entrar);
$("crear-cuenta-btn").addEventListener("click", crearCuenta);
$("salir-btn").addEventListener("click", cerrarSesion);
$("planta-form").addEventListener("submit", registrarPlanta);
$("manual-form").addEventListener("submit", diagnosticarManual);

mostrarVista();
if (token) iniciarApp();
