# Dashboard Monitoreo 43

Dashboard de control para el servidor 43 (192.168.0.43, Windows).

## Datos
- `data/estado_43.json` — Estado general (KNIME, OneDrive, disco)
- `data/analisis_temp.json` — Análisis forense de E:\\Temp

## Actualización
Los datos se actualizan cada 1h via cron desde el servidor 95.

## Deploy
Vercel: conectar repo y deploy.

## Estructura
```
index.html          # Dashboard
style.css           # Estilos (inline en HTML)
data/               # JSON generados por cron
README.md           # Este archivo
```

## Autor
Grupo EPEM BI Team


Ultima actualizacion automatica: 2026-07-11 10:05
