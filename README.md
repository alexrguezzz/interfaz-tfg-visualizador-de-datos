# Interfaz TFG - Visualizador de datos

Aplicacion web en Flask para explorar datos de futbol almacenados en GraphDB mediante consultas SPARQL. La interfaz permite filtrar competiciones, temporadas, jornadas y rangos de fecha, y ofrece vistas de resumen, clasificacion, partidos, equipos, jugadores y comparacion de equipos.

## Tecnologias

- Python 3.10 o superior
- Flask
- Requests
- GraphDB como fuente de datos RDF
- SPARQL para todas las consultas

## Requisitos

- Tener Python disponible en `PATH`
- Tener GraphDB en ejecucion
- Disponer del repositorio `TFG_SoccerData` cargado en GraphDB
- Endpoint accesible, por defecto: `http://localhost:7200/repositories/TFG_SoccerData`

## Configuracion

La aplicacion usa estas variables de entorno opcionales:

- `GRAPHDB_ENDPOINT`: endpoint del repositorio en GraphDB
- `SECRET_KEY`: clave de sesion de Flask

Valores por defecto definidos en [config.py](/c:/Users/Usuario/Desktop/ALEX/GCED/8º%20cuatri/Trabajo%20Fin%20de%20Grado%20(TFG)/Interfaz/config.py:1).

## Ejecucion

### Opcion 1: script incluido

1. Abre una terminal en esta carpeta.
2. Ejecuta `run.bat`.
3. Abre `http://127.0.0.1:5000`.

El script actualiza `pip`, instala dependencias de [requirements.txt](/c:/Users/Usuario/Desktop/ALEX/GCED/8º%20cuatri/Trabajo%20Fin%20de%20Grado%20(TFG)/Interfaz/requirements.txt:1) y arranca la aplicacion.

### Opcion 2: arranque manual

```bash
python -m pip install -r requirements.txt
python app.py
```

## Flujo de uso

Al entrar por primera vez, la aplicacion fuerza una seleccion inicial de ligas y temporadas. Esa seleccion se guarda en la sesion del navegador y limita las consultas posteriores.

Ligas disponibles en el onboarding:

- La Liga
- Premier League
- Bundesliga
- Ligue 1
- Serie A

Temporadas disponibles:

- 2020-2021
- 2021-2022
- 2022-2023
- 2023-2024
- 2024-2025

## Funcionalidad implementada

- Navbar con vistas: Inicio, Competicion, Partidos, Equipos, Jugadores y Comparador
- Filtros globales por competicion, temporada, jornadas y fechas
- Busqueda textual en las vistas que lo soportan
- Persistencia visual del tema claro/oscuro en navegador
- Onboarding inicial para acotar ligas y temporadas
- Mensajes explicitos cuando no hay datos disponibles o falla la conexion

### Vistas

#### Inicio

- KPIs de partidos jugados, equipos, jugadores, goles, tarjetas y ultimo partido
- Resumen global calculado directamente desde GraphDB

#### Competicion

- Tabla de clasificacion por competicion y temporada
- Muestra posicion, puntos, partidos jugados, victorias, empates, derrotas y balance goleador
- La vista trabaja a nivel de temporada completa

#### Partidos

- Listado filtrado de partidos con fecha, jornada, equipos y marcador
- Enlace a detalle de partido

#### Detalle de partido

- Resumen del encuentro con jornada, fecha, local, visitante, marcador y asistencia
- Visualizacion de eventos sobre el terreno de juego a partir de coordenadas almacenadas

#### Equipos

- Resumen por equipo con partidos, goles a favor y goles en contra
- Panel adicional con tendencia Elo para los equipos destacados

#### Jugadores

- Listado de jugadores ajustado al alcance de filtros cuando corresponde

#### Comparador

- Comparacion basica entre dos equipos
- Muestra partidos y puntos acumulados dentro del contexto filtrado

## Estructura del proyecto

```text
Interfaz/
|-- app.py
|-- config.py
|-- requirements.txt
|-- run.bat
|-- routes/
|-- services/
|-- static/
`-- templates/
```

### Carpetas principales

- [routes](/c:/Users/Usuario/Desktop/ALEX/GCED/8º%20cuatri/Trabajo%20Fin%20de%20Grado%20(TFG)/Interfaz/routes): registro de rutas y vistas principales
- [services](/c:/Users/Usuario/Desktop/ALEX/GCED/8º%20cuatri/Trabajo%20Fin%20de%20Grado%20(TFG)/Interfaz/services): logica de filtros, consultas, onboarding y componentes UI
- [templates](/c:/Users/Usuario/Desktop/ALEX/GCED/8º%20cuatri/Trabajo%20Fin%20de%20Grado%20(TFG)/Interfaz/templates): plantillas HTML y parciales
- [static](/c:/Users/Usuario/Desktop/ALEX/GCED/8º%20cuatri/Trabajo%20Fin%20de%20Grado%20(TFG)/Interfaz/static): recursos visuales como logos e imagen de marca

## Recursos graficos

La aplicacion espera estos assets para las ligas:

- `static/images/leagues/la-liga.svg`
- `static/images/leagues/premier-league.svg`
- `static/images/leagues/bundesliga.svg`
- `static/images/leagues/ligue-1.svg`
- `static/images/leagues/serie-a.svg`

Logo de marca actual:

- `static/images/brand/datagol-logo.png`

## Notas

- La aplicacion consulta GraphDB en tiempo real; si el endpoint no responde, las vistas muestran un estado de error o sin datos.
- El servidor Flask arranca en `127.0.0.1:5000`.
- `app.py` abre automaticamente el navegador al iniciar la aplicacion en ejecucion local.
