# Análisis Automático de Opciones Financieras

Este repositorio contiene un script Python que analiza opciones financieras (PUTs) de manera automatizada, utilizando la biblioteca `yfinance` para obtener datos de mercado. El script filtra opciones basadas en criterios como rentabilidad anual, volatilidad implícita, días al vencimiento y más, y envía notificaciones a Discord con las mejores oportunidades detectadas.

## Descripción

El script `analizar_opciones.py` realiza las siguientes tareas:
- Obtiene datos de precios y opciones para una lista de tickers especificados.
- Filtra opciones PUT (Out of the Money por defecto) según parámetros configurables (rentabilidad mínima, días al vencimiento, etc.).
- Identifica las mejores oportunidades basadas en rentabilidad anual y envía alertas automáticas a un canal de Discord cuando se cumplen ciertos umbrales predefinidos.
- Exporta los resultados a archivos CSV y un archivo de texto con detalles.

Las ejecuciones se programan automáticamente a través de GitHub Actions y también pueden realizarse manualmente.

## Requisitos

- Python 3.x
- Las siguientes bibliotecas de Python:
  - `yfinance`
  - `pandas`
  - `tabulate`
  - `requests`

## Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/tu-repositorio.git
   cd tu-repositorio

## Configuración
Variables de Entorno
Puedes configurar el script usando variables de entorno o modificando los valores por defecto en analizar_opciones.py. Las variables disponibles son:

TICKERS: Lista de tickers a analizar (separados por comas, ej: NA9.DE,TEP.PA,GOOGL).
MIN_RENTABILIDAD_ANUAL: Mínima rentabilidad anual en porcentaje (por defecto: 45.0%).
MAX_DIAS_VENCIMIENTO: Máximo número de días al vencimiento (por defecto: 45).
MIN_DIFERENCIA_PORCENTUAL: Mínima diferencia porcentual entre precio del subyacente y break-even (por defecto: 5.0%).
MIN_VOLATILIDAD_IMPLÍCITA: Mínima volatilidad implícita en porcentaje (por defecto: 35.0%).
FILTRO_TIPO_OPCION: Tipo de opción a filtrar (OTM, ITM, o TODAS, por defecto: OTM).
TOP_CONTRATOS: Número de contratos a mostrar en los mejores resultados (por defecto: 10).

## Configuración de Discord
Para recibir notificaciones en Discord:

Crea un webhook en tu servidor de Discord (en la configuración del canal, selecciona "Integraciones" > "Webhooks" > "Nuevo Webhook").
Copia la URL del webhook y reemplázala en la variable DISCORD_WEBHOOK_URL en analizar_opciones.py.
##  Valores Hardcodeados
Algunos parámetros están fijados en el script y no son configurables a través de variables de entorno:

MIN_VOLUMEN: 1 (volumen mínimo de las opciones).
MIN_OPEN_INTEREST: 1 (interés abierto mínimo).
ALERTA_RENTABILIDAD_ANUAL: 50.0% (umbral para alertas automáticas).
ALERTA_VOLATILIDAD_MINIMA: 50.0% (umbral de volatilidad para alertas automáticas).
Si necesitas cambiar estos valores, modifícalos directamente en el diccionario DEFAULT_CONFIG en analizar_opciones.py.

## Ejecución Automática
El script se ejecuta automáticamente a través de GitHub Actions en los siguientes horarios (CET):

9:00
13:00
17:00
21:00
Los resultados y notificaciones se envían a Discord si se detectan oportunidades destacadas.

## Ejecución desde GitHub Actions (Manual)
Ve a la pestaña Actions en tu repositorio.
Selecciona el workflow "Ejecutar Script de Opciones".
Haz clic en "Run workflow" y configura los parámetros en la UI si lo deseas.
Descarga los artifacts generados tras la ejecución.
## Contribución
Si deseas contribuir:

Haz un fork del repositorio.
Crea una nueva rama (git checkout -b feature/nueva-caracteristica).
Realiza tus cambios y haz commit (git commit -m "Descripción del cambio").
Envía un pull request.
Licencia
[Agrega tu licencia aquí, por ejemplo: MIT, GPL, etc. Si no tienes una, puedes omitir esta sección o especificar "Sin licencia" por ahora.]

## Notas
Asegúrate de que la API de Yahoo Finance (usada por yfinance) esté disponible y no bloquee solicitudes excesivas.
Las notificaciones de Discord solo se envían en ejecuciones automáticas, no manuales.
Si encuentras errores, revisa los logs en GitHub Actions o el archivo resultados.txt.
