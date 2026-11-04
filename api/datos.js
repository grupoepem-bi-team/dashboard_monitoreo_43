/**
 * api/datos.js — Entrega los datos del tablero del 43.
 *
 * Los archivos viven en un almacen PRIVADO de Vercel Blob: no tienen direccion
 * publica. Esta funcion es la unica que los lee, y solo se los da a quien
 * presente la clave correcta.
 *
 * Variables de entorno que usa:
 *   BLOB_READ_WRITE_TOKEN  -> la crea Vercel al conectar el almacen (ya existe)
 *   DATOS_CLAVE            -> la clave que pedimos en la pantalla (hay que crearla)
 *
 * Sin DATOS_CLAVE configurada la funcion NO entrega nada: falla cerrada a
 * proposito, para que un olvido no deje los datos al aire.
 */

// Almacen privado del proyecto monitoreo43 (region Sao Paulo).
const HOST = 'https://nktzf2jyptmxdqwm.private.blob.vercel-storage.com';
const RUTA = '/monitoreo43/datos.json';

module.exports = async function handler(req, res) {
  // Nunca cachear: el dato cambia cada hora y una copia vieja en el borde
  // haria que el panel muestre informacion vencida sin saberlo.
  res.setHeader('Cache-Control', 'no-store, max-age=0, must-revalidate');
  res.setHeader('X-Content-Type-Options', 'nosniff');

  const esperada = process.env.DATOS_CLAVE || '';
  if (!esperada) {
    res.status(500).json({ error: 'falta configurar la clave (DATOS_CLAVE)' });
    return;
  }

  // La clave viaja en un encabezado propio; tambien se acepta por query
  // para poder probar desde la terminal con curl.
  const recibida = String(req.headers['x-clave'] || req.query.clave || '');
  if (recibida !== esperada) {
    res.status(401).json({ error: 'clave incorrecta' });
    return;
  }

  try {
    const respuesta = await fetch(HOST + RUTA, {
      headers: { Authorization: 'Bearer ' + process.env.BLOB_READ_WRITE_TOKEN },
    });

    if (!respuesta.ok) {
      res.status(502).json({ error: 'el almacen no respondio', codigo: respuesta.status });
      return;
    }

    const texto = await respuesta.text();
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.status(200).send(texto);
  } catch (error) {
    res.status(500).json({ error: 'fallo la lectura del almacen',
                           detalle: String(error).slice(0, 120) });
  }
};
