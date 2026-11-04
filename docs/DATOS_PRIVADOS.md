# Datos privados del tablero del 43

Desde el 4 de noviembre de 2026 el tablero **no lee sus datos del repositorio**.
Los datos viajan por un almacen privado y la pagina los pide a una funcion que
valida una clave. El repositorio dejo de recibir commits cada hora y dejo de
exponer los datos del castillo en internet.

## Antes y despues

| | Antes | Ahora |
|---|---|---|
| Los datos viven en | `public/data/*.json`, en el repo publico | un almacen privado de Vercel Blob |
| Como llegan | `git push` cada hora con un token de GitHub en el 95 | una subida por HTTPS, con un token solo de almacenamiento |
| Quien los lee | cualquiera, por la URL del sitio | solo quien tenga la clave |
| Cada cuanto se publica | 4 archivos por hora | 1 paquete por hora |

## Las tres piezas

1. **El publicador** — `~/.hermes/scripts/publicar-blob.py` en el 95.
   Arma un solo paquete (para no gastar cuota) con `estado_43`, `analisis_temp`,
   `comparativa` y `errores_knime`, y lo sube a `monitoreo43/datos.json`.
   Conserva la regla de honestidad: si la recoleccion esta vieja, el dato se
   publica marcado como viejo y se avisa por Telegram.

   Lo llama `actualizar-dashboard-completo.sh` (cron de Hermes, cada hora en
   punto) con el interprete del venv `~/.vercel-blob/venv/bin/python`.

2. **La funcion** — `api/datos.js`.
   Lee el paquete del almacen privado y lo entrega solo si recibe la clave
   correcta en el encabezado `x-clave`. Sin clave configurada falla cerrada
   (500), a proposito: un olvido no debe dejar los datos al aire.

3. **La pagina** — `public/index.html`.
   Pide todo a `/api/datos`. La clave se pide una sola vez y queda en el
   navegador (`localStorage`, clave `clave_datos`). Si la persona cancela, no se
   le vuelve a preguntar en cada refresco.

## El almacen

- Nombre: `monitoreo43-blob`
- Acceso: **privado**
- Region: Sao Paulo (`gru1`)
- Ruta del paquete: `monitoreo43/datos.json`
- Cuota gratuita: 1 GB de almacenamiento, 10.000 lecturas y **2.000 escrituras**
  por mes. Con un paquete por hora se usan unas 720 escrituras al mes.

## La clave

- Variable `DATOS_CLAVE` en Vercel (Production, Preview y Development).
- Valor guardado en el Vault del 95: `~/.hermes/vault/vercel_blob_monitoreo43.json`
- Para cambiarla: se edita la variable en Vercel, se espera el redespliegue y se
  avisa a quien corresponda. Nada mas: la pagina vuelve a pedirla sola.

## Como verificarlo

```bash
# sin clave: tiene que dar 401
curl -s -o /dev/null -w '%{http_code}\n' https://monitoreo43.vercel.app/api/datos

# con la clave: tiene que dar 200 y el paquete
curl -s -H "x-clave: LA_CLAVE" https://monitoreo43.vercel.app/api/datos | head -c 200
```

En el servidor: `tail -6 /tmp/dashboard-catedral.log` muestra cada publicacion.

## Lo que se retiro

- `actualizar-y-push.py` (el publicador con `git push`), reemplazado.
- Los JSON de `public/data/` salieron del control de versiones: siguen en el
  disco del 95 porque el publicador los lee, pero ya no se publican.
- El token de GitHub deja de ser necesario para publicar datos. Solo se usa si
  alguien cambia el codigo a mano.
