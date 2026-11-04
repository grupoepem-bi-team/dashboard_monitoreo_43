# Dashboard Monitoreo 43 — Documentacion Tecnica

> **URL:** `https://monitoreo43.vercel.app/`  
> **Repo:** `https://github.com/grupoepem-bi-team/dashboard_monitoreo_43`  
> **Servidor:** 192.168.0.43 (GRUPOEPEM467-VM, Windows Server)  
> **Ultima version:** v4 narrativo | Fecha: 2026-07-11

---

## Que es

Dashboard web auto-actualizado que muestra el estado del servidor 43 (Windows).  
No requiere backend — es HTML estatico con datos JSON.

**Filosofia:** Cuenta una historia de arriba hacia abajo:  
1. ¿Como esta todo? → 2. ¿Cuanto falta para llenarse? → 3. ¿Que tan rapido crece? → 4. ¿Quien lo genera? → 5. ¿Hay problemas? → 6. ¿Que hacer?

---

## Secciones del Dashboard (v4)

| # | Seccion | Pregunta | Datos |
|---|---------|----------|-------|
| 1 | Resumen del Sistema | ¿Como esta todo? | Estado, disco %, RAM KNIME, temp GB |
| 2 | Disco Temporales | ¿Cuanto falta? | Barra, prediccion dias al 90%, ultima limpieza |
| 3 | Velocidad | ¿Que tan rapido? | 2h, 6h, 24h en GB |
| 4 | Quien Genera | ¿Causa? | Barras horizontales: Snapshot Temp, DuplicateChecker, etc. |
| 5 | Archivos Grandes | ¿Que archivos? | Top 10 con workflow, nombre, MB |
| 6 | Errores KNIME | ¿Problemas? | Total errores, dia peor, workflow, muestras |
| 7 | Distribucion Temporal | ¿Cuando se crearon? | <1h, 1-6h, 6-24h, 1-7d, >7d |
| 8 | Historial Mensual | ¿Evolucion? | Tabla por mes: dias, disco% prom, temp, max files |

---

## Pipeline de Datos

```
Servidor 43 (Windows, 192.168.0.43)
    ↓
WinRM (puerto 5985, credenciales en vault/windows_43.json)
    ↓
Scripts en ~/catedral/scripts/ (monitoreo-43.py)
    ↓
JSON local: ~/catedral/data/estado_43.json
    ↓
Historizador: ~/logs-central/scripts/historizar-43.py
    ↓
JSON comparativa: ~/catedral/dashboard_43/public/data/comparativa.json
    ↓
publicar-blob.py arma UN paquete y lo sube por HTTPS
    ↓
Almacen PRIVADO de Vercel Blob: monitoreo43/datos.json
    ↓
api/datos.js lo entrega solo con la clave correcta
    ↓
https://monitoreo43.vercel.app/  (la pagina pide /api/datos)
```

---

## Cronjobs Activos

| Nombre | Job ID | Frecuencia | Script | Que hace |
|--------|--------|-----------|--------|----------|
| monitoreo-43-catedral | ef51862dd831 | 0 * * * * | monitoreo-43.sh | Recolecta estado via WinRM |
| analisis-temp-43 | 55a69aab88f6 | 0 * * * * | analisis-temp-43.sh | Analisis forense de E:\Temp |
| recolectar-knime-43 | d8f8edc8a925 | 0 * * * * | recolectar-knime-43.sh | Trae el knime.log |
| actualizar-dashboard-43 | 541613363b1c | 5 * * * * | actualizar-dashboard-completo.sh | Arma el paquete y lo sube a Vercel Blob |
| historizar-43-diario | e61aaba38ff7 | 0 0 * * * | historizar-y-push.sh | Snapshot historico + publicacion |

Los tres recolectores corren en punto; la publicacion a las :05 para no leer un archivo a medio escribir.

**Ubicacion cron local:** `~/.hermes/cron/`  
**Scripts:** `~/.hermes/scripts/`  
**Venv:** `~/.venvs/logs-central/bin/python3`

---

## Archivos Clave

### Dashboard (repo)
```
public/
  index.html           # Dashboard v4 narrativo (pide los datos a /api/datos)
api/
  datos.js             # Funcion: lee el almacen privado y valida la clave
docs/
  DATOS_PRIVADOS.md    # Como funciona la publicacion privada
vercel.json            # Headers no-cache
README.md              # Este archivo

Los JSON de public/data/ ya NO se versionan: siguen en el disco del servidor porque el
publicador los lee, pero no se publican (salen 404 en el sitio).
```

### Scripts recolectores
```
~/catedral/scripts/
  monitoreo-43.py               # Recolector principal (WinRM)

~/logs-central/scripts/
  historizar-43.py                # Snapshot diario + comparativa
  analisis-temporales-43.py       # Analisis forense E:\Temp
  recolectar-knime-log.py         # Obtiene knime.log via WinRM

~/.hermes/scripts/
  monitoreo-43.sh                  # Wrapper cron horario (recoleccion)
  publicar-blob.py                 # Arma el paquete y lo sube a Vercel Blob
  actualizar-dashboard-completo.sh # Wrapper de publicacion (cron :05)
  historizar-y-push.sh             # Wrapper historizacion (00:00)
```

### Credenciales (vault)
```
~/.hermes/vault/
  windows_43.json                  # Credenciales WinRM (user, password)
  vercel_blob_monitoreo43.json     # Token del almacen + clave de la pagina (600)
```

---

## Alertas y Umbrales

| Metrica | Warning | Critico | Accion |
|---------|---------|---------|--------|
| Disco E:\ | 75% | 90% | Banner rojo/naranja en dashboard + Telegram |
| Temp files | 50.000 | 100.000 | Aviso Telegram |
| KNIME detenido | — | PID no existe | Alerta critica Telegram |

**Destino alertas:** Telegram grupo -1003771914699

---

## Problemas Conocidos / Quirks

1. **Datos privados:** el token del almacen y la clave de la pagina viven en `~/.hermes/vault/vercel_blob_monitoreo43.json` (600). El token de GitHub ya no se usa para publicar datos.

2. **.NET Date format:** PowerShell devuelve fechas como `/Date(1783516607551)/`. El dashboard las parsea con regex: `d.match(/Date\((\d+)\)/)`.

3. **Vercel cache:** Sin `vercel.json` con `Cache-Control: no-cache`, los JSON se cachean. Siempre incluir `vercel.json`.

4. **WinRM timeout:** Scripts WinRM pueden tardar >30s. El cron usa timeout generoso.

5. **Comparativa vacia al inicio:** Solo genera datos cuando `historizar-43.py` corre (medianoche). Los primeros dias mostraran 1 sola fila.

6. **Cuota del almacen:** el plan gratuito da 2.000 escrituras por mes. Un paquete por hora son ~720. No partir el paquete en varios archivos sin revisar la cuota.

7. **Preview protegido:** las URLs de preview piden sesion de Vercel. Pedirlas con curl devuelve la pantalla de login (un HTML de ~330 KB), no un error de la funcion. Probar en un navegador con sesion, o desplegar en dos tiempos a produccion.

---

## Como Recuperar / Restaurar

1. **Clonar repo:** `git clone https://github.com/grupoepem-bi-team/dashboard_monitoreo_43.git`
2. **Token del almacen:** Verificar `~/.hermes/vault/vercel_blob_monitoreo43.json`
3. **Credenciales 43:** Verificar `~/.hermes/vault/windows_43.json`
4. **Venv:** `~/.venvs/logs-central/bin/python3` debe tener `pywinrm`
5. **Cronjobs:** `hermes cron list` para verificar 3 jobs activos
6. **Vercel:** Conectar repo en panel Vercel, deploy automatico

---

## Versiones del Dashboard

| Version | Descripcion | Commit |
|---------|-------------|--------|
| v1 | Cards oscuras basicas | 8a395d5 |
| v2 | Public/data, grid 3x3 | b77b8e9 |
| v3 | Compacto con sparklines, heatmap, CSV, modo claro | 1a0aa6d |
| v4 | **Narrativo, scroll natural, barras horizontales, jerarquico** | 5ecbcfa |

---

*Documentacion mantenida automaticamente por el pipeline.  
Ultima actualizacion: 2026-11-04*
