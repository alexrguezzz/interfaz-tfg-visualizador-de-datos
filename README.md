# Interfaz Ejemplos Ampliada

Interfaz Flask conectada exclusivamente a GraphDB para visualizar datos del TFG.

## Requisitos
- Python 3.10+
- GraphDB levantado y repositorio `TFG_SoccerData`

## Configuracion opcional
Variable de entorno para endpoint:

- `GRAPHDB_ENDPOINT` (por defecto `http://localhost:7200/repositories/TFG_SoccerData`)

## Ejecucion
1. Abrir terminal en esta carpeta.
2. Ejecutar `run.bat`.
3. Abrir `http://127.0.0.1:5000`.

## Funcionalidad implementada
- Navbar con secciones finales: Inicio, Competicion, Partidos, Equipos, Jugadores, Comparador.
- Toggle dark/light persistente en `localStorage`.
- Subbarra de filtros globales: Competicion, Temporada, Jornadas (multi o Todas), Fecha desde/hasta.
- Todo consultado en GraphDB mediante SPARQL.
- Mensaje `Informacion no disponible` en vistas sin datos.

## Flujo inicial
- Al abrir la app por primera vez en una sesión, aparece una pantalla de carga y despues un onboarding de dos pasos.
- Primero se seleccionan ligas y luego temporadas.
- La seleccion se guarda solo durante la sesion del navegador.
- En la barra superior hay un boton para volver a abrir la seleccion en cualquier momento.

## Logos de ligas
- Carpeta esperada: `static/images/leagues/`
- Nombres esperados: `la-liga.svg`, `premier-league.svg`, `bundesliga.svg`, `ligue-1.svg`, `serie-a.svg`
