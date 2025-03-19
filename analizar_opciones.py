import yfinance as yf
from datetime import datetime
import os
from tabulate import tabulate
import pandas as pd
import requests
import time

# Configuración para Discord - Forzado directamente
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1350463523196768356/ePmWnO2XWnfD582oMAr2WzqSFs7ZxU1ApRYi1bz8PiSbZE5zAcR7ZoOD8SPVofxA9UUW"
print(f"[DEBUG] Valor inicial de DISCORD_WEBHOOK_URL: {DISCORD_WEBHOOK_URL}")  # Depuración inicial

# Variable para evitar ejecuciones múltiples
SCRIPT_EJECUTADO = False
ENVIAR_NOTIFICACION_MANUAL = False  # Cambia a True/false para forzar la notificación manualmente

# Configuraciones por defecto (ajustables manualmente)
DEFAULT_CONFIG = {
    "TICKERS": "WBD,UNFI,GOOGL,EPAM,NFE,GLNG,GLOB,NVDA",
    "MIN_RENTABILIDAD_ANUAL": 45.0,
    "MAX_DIAS_VENCIMIENTO": 45,
    "MIN_DIFERENCIA_PORCENTUAL": 5.0,
    "MIN_VOLUMEN": 1,
    "MIN_VOLATILIDAD_IMPLICITA": 35.0,
    "MIN_OPEN_INTEREST": 1,
    "FILTRO_TIPO_OPCION": "OTM",
    "TOP_CONTRATOS": 5,
    "ALERTA_RENTABILIDAD_ANUAL": 50.0,
    "ALERTA_VOLATILIDAD_MINIMA": 50.0,
    "MIN_BID": 0.99
}

# Clave API de Finnhub
FINNHUB_API_KEY = "cvbfudhr01qob7udcs1gcvbfudhr01qob7udcs20"

def obtener_configuracion():
    """Obtiene la configuración desde variables de entorno con valores por defecto del script."""
    print(f"[DEBUG] Configuración inicial - DISCORD_WEBHOOK_URL: {DISCORD_WEBHOOK_URL}")  # Depuración
    # TICKERS
    TICKERS = os.getenv("TICKERS", DEFAULT_CONFIG["TICKERS"])
    print(f"Valor de TICKERS desde os.getenv: {TICKERS}")
    if not TICKERS:
        raise ValueError("No se especificaron tickers válidos. Define TICKERS en las variables de entorno.")
    TICKERS = [t.strip() for t in TICKERS.split(",") if t.strip()]  # Eliminar espacios y elementos vacíos
    TICKERS = list(set(TICKERS))  # Eliminar duplicados
    if not TICKERS:
        raise ValueError("La lista de tickers está vacía después de procesar.")
    print(f"Tickers procesados: {TICKERS}")

    # MIN_RENTABILIDAD_ANUAL
    min_rentabilidad_env = os.getenv("MIN_RENTABILIDAD_ANUAL", str(DEFAULT_CONFIG["MIN_RENTABILIDAD_ANUAL"]))
    MIN_RENTABILIDAD_ANUAL = float(min_rentabilidad_env) if min_rentabilidad_env else DEFAULT_CONFIG["MIN_RENTABILIDAD_ANUAL"]
    print(f"MIN_RENTABILIDAD_ANUAL: {MIN_RENTABILIDAD_ANUAL}")

    # MAX_DIAS_VENCIMIENTO
    max_dias_env = os.getenv("MAX_DIAS_VENCIMIENTO", str(DEFAULT_CONFIG["MAX_DIAS_VENCIMIENTO"]))
    MAX_DIAS_VENCIMIENTO = int(max_dias_env) if max_dias_env else DEFAULT_CONFIG["MAX_DIAS_VENCIMIENTO"]
    print(f"MAX_DIAS_VENCIMIENTO: {MAX_DIAS_VENCIMIENTO}")

    # MIN_DIFERENCIA_PORCENTUAL
    min_dif_env = os.getenv("MIN_DIFERENCIA_PORCENTUAL", str(DEFAULT_CONFIG["MIN_DIFERENCIA_PORCENTUAL"]))
    MIN_DIFERENCIA_PORCENTUAL = float(min_dif_env) if min_dif_env else DEFAULT_CONFIG["MIN_DIFERENCIA_PORCENTUAL"]
    print(f"MIN_DIFERENCIA_PORCENTUAL: {MIN_DIFERENCIA_PORCENTUAL}")

    # MIN_VOLUMEN (hardcodeado)
    MIN_VOLUMEN = DEFAULT_CONFIG["MIN_VOLUMEN"]
    print(f"MIN_VOLUMEN: {MIN_VOLUMEN}")

    # MIN_VOLATILIDAD_IMPLICITA
    min_vol_env = os.getenv("MIN_VOLATILIDAD_IMPLICITA", str(DEFAULT_CONFIG["MIN_VOLATILIDAD_IMPLICITA"]))
    MIN_VOLATILIDAD_IMPLICITA = float(min_vol_env) if min_vol_env else DEFAULT_CONFIG["MIN_VOLATILIDAD_IMPLICITA"]
    print(f"MIN_VOLATILIDAD_IMPLICITA: {MIN_VOLATILIDAD_IMPLICITA}")

    # MIN_OPEN_INTEREST (hardcodeado)
    MIN_OPEN_INTEREST = DEFAULT_CONFIG["MIN_OPEN_INTEREST"]
    print(f"MIN_OPEN_INTEREST: {MIN_OPEN_INTEREST}")

    # FILTRO_TIPO_OPCION
    FILTRO_TIPO_OPCION = os.getenv("FILTRO_TIPO_OPCION", DEFAULT_CONFIG["FILTRO_TIPO_OPCION"]).upper()
    if FILTRO_TIPO_OPCION not in ["OTM", "ITM", "TODAS"]:
        print(f"Valor inválido para FILTRO_TIPO_OPCION: {FILTRO_TIPO_OPCION}. Usando valor por defecto: {DEFAULT_CONFIG['FILTRO_TIPO_OPCION']}")
        FILTRO_TIPO_OPCION = DEFAULT_CONFIG["FILTRO_TIPO_OPCION"]
    print(f"FILTRO_TIPO_OPCION: {FILTRO_TIPO_OPCION}")

    # TOP_CONTRATOS
    top_contratos_env = os.getenv("TOP_CONTRATOS", str(DEFAULT_CONFIG["TOP_CONTRATOS"]))
    TOP_CONTRATOS = int(top_contratos_env) if top_contratos_env else DEFAULT_CONFIG["TOP_CONTRATOS"]
    print(f"TOP_CONTRATOS: {TOP_CONTRATOS}")

    # ALERTA_RENTABILIDAD_ANUAL (hardcodeado)
    ALERTA_RENTABILIDAD_ANUAL = DEFAULT_CONFIG["ALERTA_RENTABILIDAD_ANUAL"]
    print(f"ALERTA_RENTABILIDAD_ANUAL: {ALERTA_RENTABILIDAD_ANUAL}")

    # ALERTA_VOLATILIDAD_MINIMA (hardcodeado)
    ALERTA_VOLATILIDAD_MINIMA = DEFAULT_CONFIG["ALERTA_VOLATILIDAD_MINIMA"]
    print(f"ALERTA_VOLATILIDAD_MINIMA: {ALERTA_VOLATILIDAD_MINIMA}")

    # MIN_BID (nueva variable)
    min_bid_env = os.getenv("MIN_BID", str(DEFAULT_CONFIG["MIN_BID"]))
    MIN_BID = float(min_bid_env) if min_bid_env else DEFAULT_CONFIG["MIN_BID"]
    print(f"MIN_BID: {MIN_BID}")

    return (TICKERS, MIN_RENTABILIDAD_ANUAL, MAX_DIAS_VENCIMIENTO, MIN_DIFERENCIA_PORCENTUAL,
            MIN_VOLUMEN, MIN_VOLATILIDAD_IMPLICITA, MIN_OPEN_INTEREST,
            FILTRO_TIPO_OPCION, TOP_CONTRATOS, ALERTA_RENTABILIDAD_ANUAL, ALERTA_VOLATILIDAD_MINIMA, MIN_BID)

def obtener_datos_subyacente(ticker):
    """Obtiene el precio del subyacente, mínimo y máximo de 52 semanas."""
    if not ticker:
        raise ValueError("El ticker no puede estar vacío.")
    stock = yf.Ticker(ticker)
    precio = stock.info.get('regularMarketPrice', None)
    minimo_52_semanas = stock.info.get('fiftyTwoWeekLow', None)
    maximo_52_semanas = stock.info.get('fiftyTwoWeekHigh', None)
    if precio is None or minimo_52_semanas is None or maximo_52_semanas is None:
        raise ValueError(f"No se encontraron datos válidos para el subyacente {ticker}")
    return stock, precio, minimo_52_semanas, maximo_52_semanas

def obtener_opciones_yahoo(stock):
    """Obtiene las opciones PUT desde Yahoo Finance."""
    try:
        fechas_vencimiento = stock.options
        opciones_put = []
        for fecha in fechas_vencimiento:
            opcion = stock.option_chain(fecha)
            puts = opcion.puts
            for _, put in puts.iterrows():
                opciones_put.append({
                    "strike": float(put["strike"]),
                    "lastPrice": float(put["lastPrice"]),
                    "bid": float(put.get("bid", 0) or 0),
                    "expirationDate": fecha,
                    "volume": put.get("volume", 0) or 0,
                    "impliedVolatility": (put.get("impliedVolatility", 0) or 0) * 100,
                    "openInterest": put.get("openInterest", 0) or 0,
                    "source": "Yahoo Finance"
                })
        print(f"Se obtuvieron {len(opciones_put)} opciones PUT de Yahoo Finance para {stock.ticker}")
        return opciones_put, "Yahoo Finance", None
    except Exception as e:
        print(f"Error al obtener opciones de Yahoo Finance para {stock.ticker}: {e}")
        return [], "Yahoo Finance", str(e)

def obtener_opciones_finnhub(ticker):
    """Obtiene las opciones PUT desde Finnhub como respaldo."""
    url = f"https://finnhub.io/api/v1/stock/option-chain?symbol={ticker}&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        opciones_put = []
        for expiration in data.get("data", []):
            fecha = expiration["expirationDate"]
            for option in expiration["options"]["PUT"]:
                opciones_put.append({
                    "strike": float(option["strike"]),
                    "lastPrice": float(option.get("last", 0) or 0),
                    "bid": float(option.get("bid", 0) or 0),
                    "expirationDate": fecha,
                    "volume": option.get("volume", 0) or 0,
                    "impliedVolatility": (option.get("impliedVolatility", 0) or 0) * 100,
                    "openInterest": option.get("openInterest", 0) or 0,
                    "source": "Finnhub"
                })
        print(f"Se obtuvieron {len(opciones_put)} opciones PUT de Finnhub para {ticker}")
        return opciones_put, "Finnhub", None
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de Finnhub para {ticker}: {e}")
        return [], "Finnhub", str(e)

def combinar_opciones(opciones_yahoo, opciones_finnhub):
    """Combina opciones de Yahoo Finance y Finnhub, usando Finnhub como respaldo para campos faltantes."""
    opciones_combinadas = []
    opciones_dict = {}  # Diccionario para manejar duplicados (clave: strike + expirationDate)

    # Primero agregar todas las opciones de Yahoo Finance
    for opcion in opciones_yahoo:
        key = (opcion["strike"], opcion["expirationDate"])
        opciones_dict[key] = opcion

    # Luego complementar o reemplazar con datos de Finnhub si hay campos faltantes
    for opcion in opciones_finnhub:
        key = (opcion["strike"], opcion["expirationDate"])
        if key not in opciones_dict:  # Si no existe, agregar directamente
            opciones_dict[key] = opcion
        else:  # Si existe, complementar si faltan datos (por ejemplo, bid es nan)
            opcion_existente = opciones_dict[key]
            updated = False
            if pd.isna(opcion_existente["bid"]) or opcion_existente["bid"] == 0:  # Si bid está ausente o es 0
                opcion_existente["bid"] = opcion["bid"]  # Actualizar bid desde Finnhub
                updated = True
            if pd.isna(opcion_existente["lastPrice"]) or opcion_existente["lastPrice"] == 0:  # Si lastPrice está ausente o es 0
                opcion_existente["lastPrice"] = opcion["lastPrice"]  # Actualizar lastPrice desde Finnhub
                updated = True
            if pd.isna(opcion_existente["volume"]) or opcion_existente["volume"] == 0:  # Si volume está ausente o es 0
                opcion_existente["volume"] = opcion["volume"]  # Actualizar volume desde Finnhub
                updated = True
            if pd.isna(opcion_existente["openInterest"]) or opcion_existente["openInterest"] == 0:  # Si openInterest está ausente o es 0
                opcion_existente["openInterest"] = opcion["openInterest"]  # Actualizar openInterest desde Finnhub
                updated = True
            if pd.isna(opcion_existente["impliedVolatility"]) or opcion_existente["impliedVolatility"] == 0:  # Si impliedVolatility está ausente o es 0
                opcion_existente["impliedVolatility"] = opcion["impliedVolatility"]  # Actualizar impliedVolatility desde Finnhub
                updated = True
            # Si se actualizó algún campo, cambiar la fuente a "Yahoo + Finnhub"
            if updated:
                opcion_existente["source"] = "Yahoo + Finnhub"

    opciones_combinadas = list(opciones_dict.values())
    return opciones_combinadas

def obtener_opciones_put(ticker, stock):
    """Obtiene las opciones PUT del ticker combinando Yahoo Finance y Finnhub como respaldo."""
    opciones_yahoo, source_yahoo, error_yahoo = obtener_opciones_yahoo(stock)
    opciones_finnhub, source_finnhub, error_finnhub = obtener_opciones_finnhub(ticker)

    opciones_combinadas = combinar_opciones(opciones_yahoo, opciones_finnhub)
    print(f"Se combinaron {len(opciones_combinadas)} opciones PUT para {ticker}")

    fuentes_usadas = []
    if opciones_yahoo:
        fuentes_usadas.append("Yahoo Finance")
    if opciones_finnhub:
        fuentes_usadas.append("Finnhub")
    fuentes_texto = " y ".join(fuentes_usadas) if fuentes_usadas else "Ninguna fuente disponible"

    errores = []
    if error_yahoo:
        errores.append(f"Yahoo Finance: {error_yahoo}")
    if error_finnhub:
        errores.append(f"Finnhub: {error_finnhub}")
    errores_texto = "; ".join(errores) if errores else "Ninguno"

    return opciones_combinadas, fuentes_texto, errores_texto

def calcular_rentabilidad(precio_put, precio_subyacente, dias_vencimiento):
    """Calcula la rentabilidad diaria y anualizada."""
    rentabilidad_diaria = (precio_put * 100) / precio_subyacente
    factor_anual = 365 / dias_vencimiento
    rentabilidad_anualizada = (rentabilidad_diaria * factor_anual)
    return rentabilidad_diaria, rentabilidad_anualizada

def calcular_break_even(strike, precio_put):
    """Calcula el break-even para un Short Put."""
    return strike - precio_put

def calcular_diferencia_porcentual(precio_subyacente, break_even):
    """Calcula la diferencia porcentual entre el subyacente y el break-even."""
    return ((precio_subyacente - break_even) / precio_subyacente) * 100

def enviar_notificacion_discord(tipo_opcion_texto, top_contratos, tickers_identificados, alerta_rentabilidad_anual, alerta_volatilidad_minima):
    """Envía el archivo Mejores_Contratos.txt a Discord como un adjunto y menciona los tickers identificados."""
    print(f"[DEBUG] Dentro de enviar_notificacion_discord - DISCORD_WEBHOOK_URL: {DISCORD_WEBHOOK_URL}")  # Depuración
    ticker_list = ", ".join(tickers_identificados) if tickers_identificados else "Ninguno"
    mensaje = f"Se encontraron contratos que cumplen los filtros de alerta para los siguientes tickers: {ticker_list}"

    # Verificar si la URL de Discord es válida
    print(f"[DEBUG] Intentando enviar notificación con URL: {DISCORD_WEBHOOK_URL}")  # Depuración
    if not DISCORD_WEBHOOK_URL or not DISCORD_WEBHOOK_URL.startswith(('http://', 'https://')):
        print(f"Error: URL de Discord inválida o no configurada: {DISCORD_WEBHOOK_URL}. Notificación no enviada.")
        return

    # Verificar el tamaño del archivo Mejores_Contratos.txt
    try:
        file_size = os.path.getsize("Mejores_Contratos.txt")
        max_size_mb = 8  # Límite de 8 MB para Discord (ajusta según el nivel de boost de tu servidor)
        if file_size > max_size_mb * 1024 * 1024:
            print(f"Error: El archivo Mejores_Contratos.txt ({file_size / (1024 * 1024):.2f} MB) excede el límite de {max_size_mb} MB para Discord.")
            mensaje = f"Se encontraron contratos que cumplen los filtros de alerta para los siguientes tickers: {ticker_list}\nEl archivo Mejores_Contratos.txt es demasiado grande ({file_size / (1024 * 1024):.2f} MB) para enviarse a Discord.\nRevisa los artifacts en GitHub Actions para descargar el archivo."
            payload = {"content": mensaje}
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            print("Notificación de error enviada a Discord.")
            return
    except FileNotFoundError:
        print("Error: No se encontró el archivo Mejores_Contratos.txt.")
        mensaje = f"Se encontraron contratos que cumplen los filtros de alerta para los siguientes tickers: {ticker_list}\nNo se encontró el archivo Mejores_Contratos.txt para enviar a Discord.\nRevisa los logs para más detalles."
        payload = {"content": mensaje}
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Notificación de error enviada a Discord.")
        return

    # Enviar el archivo Mejores_Contratos.txt como adjunto
    try:
        with open("Mejores_Contratos.txt", "rb") as f:
            files = {
                "file": ("Mejores_Contratos.txt", f, "text/plain")
            }
            payload = {
                "content": mensaje
            }
            response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
            response.raise_for_status()
            print("Archivo Mejores_Contratos.txt enviado a Discord exitosamente.")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el archivo a Discord: {e}")
        if 'response' in locals() and response.text:
            print(f"Detalles del error: {response.text}")

def analizar_opciones():
    global SCRIPT_EJECUTADO

    print(f"[DEBUG] Iniciando ejecución del script a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    if SCRIPT_EJECUTADO:
        print("El script ya ha sido ejecutado. Evitando repetición.")
        return
    SCRIPT_EJECUTADO = True

    # Obtener configuración desde variables de entorno con valores por defecto del script
    try:
        (TICKERS, MIN_RENTABILIDAD_ANUAL, MAX_DIAS_VENCIMIENTO, MIN_DIFERENCIA_PORCENTUAL,
         MIN_VOLUMEN, MIN_VOLATILIDAD_IMPLICITA, MIN_OPEN_INTEREST,
         FILTRO_TIPO_OPCION, TOP_CONTRATOS, ALERTA_RENTABILIDAD_ANUAL, ALERTA_VOLATILIDAD_MINIMA, MIN_BID) = obtener_configuracion()
    except Exception as e:
        error_msg = f"Error al obtener la configuración: {e}\n"
        print(error_msg)
        with open("resultados.txt", "w") as f:
            f.write(error_msg)
        return  # Terminar ejecución si falla la configuración

    # Detectar si es una ejecución manual o automática
    es_ejecucion_manual = os.getenv("GITHUB_EVENT_NAME", "schedule") == "workflow_dispatch"
    force_discord = os.getenv("FORCE_DISCORD_NOTIFICATION", "false").lower() == "true"
    print(f"Es ejecución manual: {es_ejecucion_manual}, Forzar notificación Discord: {force_discord}")

    # Resumen de condiciones para el archivo .txt
    resumen_condiciones = (
        f"Resumen de condiciones de ejecución - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n"
        f"Tickers analizados: {', '.join(TICKERS)}\n"
        f"Filtro tipo opción: {FILTRO_TIPO_OPCION}\n"
        f"Mínima rentabilidad anual: {MIN_RENTABILIDAD_ANUAL}%\n"
        f"Máximo días al vencimiento: {MAX_DIAS_VENCIMIENTO}\n"
        f"Mínima diferencia porcentual: {MIN_DIFERENCIA_PORCENTUAL}%\n"
        f"Mínimo volumen: {MIN_VOLUMEN}\n"
        f"Volatilidad implícita mínima: {MIN_VOLATILIDAD_IMPLICITA}%\n"
        f"Mínimo interés abierto: {MIN_OPEN_INTEREST}\n"
        f"Mínimo bid: ${MIN_BID}\n"
        f"{'='*50}\n\n"
    )

    resultado = resumen_condiciones
    todas_las_opciones = []
    todas_las_opciones_df = []

    try:
        print(f"[DEBUG] Analizando {len(TICKERS)} tickers: {TICKERS}")
        for ticker in TICKERS:
            resultado += f"\n{'='*50}\nAnalizando ticker: {ticker}\n{'='*50}\n"
            print(f"\n{'='*50}\nAnalizando ticker: {ticker}\n{'='*50}\n")

            try:
                stock, precio_subyacente, minimo_52_semanas, maximo_52_semanas = obtener_datos_subyacente(ticker)
                resultado += f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}\n"
                resultado += f"Mínimo de las últimas 52 semanas: ${minimo_52_semanas:.2f}\n"
                resultado += f"Máximo de las últimas 52 semanas: ${maximo_52_semanas:.2f}\n"
                print(f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}")
                print(f"Mínimo de las últimas 52 semanas: ${minimo_52_semanas:.2f}")
                print(f"Máximo de las últimas 52 semanas: ${maximo_52_semanas:.2f}")

                opciones_put, fuentes_texto, errores_texto = obtener_opciones_put(ticker, stock)
                resultado += f"Datos de opciones para {ticker} obtenidos de: {fuentes_texto}\n"
                resultado += f"Errores al obtener datos: {errores_texto}\n"
                print(f"Datos de opciones para {ticker} obtenidos de: {fuentes_texto}")
                print(f"Errores al obtener datos: {errores_texto}")

                print(f"Se encontraron {len(opciones_put)} opciones PUT para {ticker}")
                opciones_filtradas = []
                for contrato in opciones_put:
                    strike = float(contrato["strike"])
                    precio_put = float(contrato["lastPrice"])
                    vencimiento_str = contrato["expirationDate"]
                    dias_vencimiento = (datetime.strptime(vencimiento_str, "%Y-%m-%d") - datetime.now()).days
                    volumen = contrato["volume"]
                    volatilidad_implícita = contrato["impliedVolatility"]
                    open_interest = contrato["openInterest"]
                    bid = contrato["bid"]
                    source = contrato["source"]

                    if FILTRO_TIPO_OPCION == "OTM":
                        if strike >= precio_subyacente:
                            continue
                    elif FILTRO_TIPO_OPCION == "ITM":
                        if strike < precio_subyacente:
                            continue

                    if dias_vencimiento <= 0 or dias_vencimiento > MAX_DIAS_VENCIMIENTO:
                        continue
                    if volumen < MIN_VOLUMEN:
                        continue
                    if volatilidad_implícita < MIN_VOLATILIDAD_IMPLICITA:
                        continue
                    if open_interest < MIN_OPEN_INTEREST:
                        continue
                    if bid < MIN_BID:
                        continue

                    rent_diaria, rent_anual = calcular_rentabilidad(precio_put, precio_subyacente, dias_vencimiento)
                    break_even = calcular_break_even(strike, precio_put)
                    diferencia_porcentual = calcular_diferencia_porcentual(precio_subyacente, break_even)

                    if rent_anual >= MIN_RENTABILIDAD_ANUAL and diferencia_porcentual >= MIN_DIFERENCIA_PORCENTUAL:
                        opcion = {
                            "ticker": ticker,
                            "strike": strike,
                            "lastPrice": precio_put,
                            "bid": bid,
                            "vencimiento": vencimiento_str,
                            "dias_vencimiento": dias_vencimiento,
                            "rentabilidad_diaria": rent_diaria,
                            "rentabilidad_anual": rent_anual,
                            "break_even": break_even,
                            "diferencia_porcentual": diferencia_porcentual,
                            "volatilidad_implícita": volatilidad_implícita,
                            "volumen": volumen,
                            "open_interest": open_interest,
                            "source": source
                        }
                        opciones_filtradas.append(opcion)
                        todas_las_opciones.append(opcion)

                        todas_las_opciones_df.append([
                            ticker,
                            f"${strike:.2f}",
                            f"${precio_put:.2f}",
                            f"${bid:.2f}",
                            vencimiento_str,
                            dias_vencimiento,
                            f"{rent_diaria:.2f}%",
                            f"{rent_anual:.2f}%",
                            f"${break_even:.2f}",
                            f"{diferencia_porcentual:.2f}%",
                            f"{volatilidad_implícita:.2f}%",
                            volumen,
                            open_interest,
                            source
                        ])

                if opciones_filtradas:
                    tipo_opcion_texto = "Out of the Money" if FILTRO_TIPO_OPCION == "OTM" else "In the Money" if FILTRO_TIPO_OPCION == "ITM" else "Todas"
                    resultado += f"\nOpciones PUT {tipo_opcion_texto} con rentabilidad anual > {MIN_RENTABILIDAD_ANUAL}% y diferencia % > {MIN_DIFERENCIA_PORCENTUAL}% (máximo {MAX_DIAS_VENCIMIENTO} días, volumen > {MIN_VOLUMEN}, volatilidad >= {MIN_VOLATILIDAD_IMPLICITA}%, interés abierto > {MIN_OPEN_INTEREST}, bid >= ${MIN_BID}):\n"
                    print(f"Se encontraron {len(opciones_filtradas)} opciones que cumplen los filtros para {ticker}")
                    
                    tabla_datos = []
                    for opcion in opciones_filtradas:
                        tabla_datos.append([
                            f"${opcion['strike']:.2f}",
                            f"${opcion['lastPrice']:.2f}",
                            f"${opcion['bid']:.2f}",
                            opcion['vencimiento'],
                            opcion['dias_vencimiento'],
                            f"{opcion['rentabilidad_diaria']:.2f}%",
                            f"{opcion['rentabilidad_anual']:.2f}%",
                            f"${opcion['break_even']:.2f}",
                            f"{opcion['diferencia_porcentual']:.2f}%",
                            f"{opcion['volatilidad_implícita']:.2f}%",
                            opcion['volumen'],
                            opcion['open_interest'],
                            opcion['source']
                        ])
                    
                    headers = [
                        "Strike",
                        "Last Closed",
                        "Bid",
                        "Vencimiento",
                        "Días Venc.",
                        "Rent. Diaria",
                        "Rent. Anual",
                        "Break-even",
                        "Dif. % (Suby.-Break.)",
                        "Volatilidad Implícita",
                        "Volumen",
                        "Interés Abierto",
                        "Fuente"
                    ]
                    
                    tabla = tabulate(tabla_datos, headers=headers, tablefmt="grid")
                    resultado += f"\n{tabla}\n"
                    print(tabla)

                    for opcion in opciones_filtradas:
                        if (opcion['rentabilidad_anual'] >= ALERTA_RENTABILIDAD_ANUAL and 
                            opcion['volatilidad_implícita'] >= ALERTA_VOLATILIDAD_MINIMA):
                            alerta_msg = f"¡Oportunidad destacada! {ticker}: Rentabilidad anual: {opcion['rentabilidad_anual']:.2f}%, Volatilidad: {opcion['volatilidad_implícita']:.2f}% (Strike: ${opcion['strike']:.2f}, Vencimiento: {opcion['vencimiento']})\n"
                            resultado += alerta_msg
                            print(alerta_msg)

                else:
                    resultado += "\nNo se consiguieron resultados para este ticker.\n"
                    print("No se consiguieron resultados para este ticker.")

            except Exception as e:
                error_msg = f"Error al analizar {ticker}: {e}\n"
                resultado += error_msg
                print(error_msg)
                continue

        # Guardar resultados.txt antes de procesar más datos
        with open("resultados.txt", "w") as f:
            f.write(resultado)
        print("Archivo resultados.txt generado.")

        # Generar todas_las_opciones.csv (incluso si está vacío)
        headers_csv = [
            "Ticker",
            "Strike",
            "Last Closed",
            "Bid",
            "Vencimiento",
            "Días Venc.",
            "Rent. Diaria",
            "Rent. Anual",
            "Break-even",
            "Dif. % (Suby.-Break.)",
            "Volatilidad Implícita",
            "Volumen",
            "Interés Abierto",
            "Fuente"
        ]
        if todas_las_opciones_df:
            print(f"Total de opciones filtradas (todos los tickers): {len(todas_las_opciones)}")
            df_todas = pd.DataFrame(todas_las_opciones_df, columns=headers_csv)
            df_todas.to_csv("todas_las_opciones.csv", index=False)
            print("Todas las opciones exportadas a 'todas_las_opciones.csv'.")
        else:
            print("No se encontraron opciones que cumplan los filtros. Generando todas_las_opciones.csv vacío.")
            df_todas = pd.DataFrame(columns=headers_csv)
            df_todas.to_csv("todas_las_opciones.csv", index=False)
            print("Archivo todas_las_opciones.csv generado (vacío).")

        # Seleccionar los mejores contratos por ticker y aplicar reglas de alerta
        mejores_contratos_df = []

        # Diccionario para almacenar opciones filtradas por ticker
        opciones_por_ticker = {}
        for ticker in TICKERS:
            opciones_por_ticker[ticker] = []

        # Llenar opciones_por_ticker con las opciones filtradas
        for opcion in todas_las_opciones:
            opciones_por_ticker[opcion['ticker']].append(opcion)

        # Seleccionar los mejores contratos por ticker
        mejores_contratos_por_ticker = []
        for ticker, opciones in opciones_por_ticker.items():
            if opciones:
                # Ordenar opciones por rentabilidad anual (descendente), días al vencimiento (ascendente), diferencia porcentual (descendente)
                opciones_ordenadas = sorted(
                    opciones,
                    key=lambda x: (-x['rentabilidad_anual'], x['dias_vencimiento'], -x['diferencia_porcentual'])
                )
                # Filtrar por reglas de alerta
                opciones_filtradas_alerta = [
                    opcion for opcion in opciones_ordenadas
                    if (opcion['rentabilidad_anual'] >= ALERTA_RENTABILIDAD_ANUAL and 
                        opcion['volatilidad_implícita'] >= ALERTA_VOLATILIDAD_MINIMA)
                ]
                # Tomar los mejores contratos según TOP_CONTRATOS (o menos si no hay suficientes que cumplan las alertas)
                mejores_n = opciones_filtradas_alerta[:TOP_CONTRATOS]
                mejores_contratos_por_ticker.extend(mejores_n)

                # Preparar datos para la tabla y el CSV
                for opcion in mejores_n:
                    mejores_contratos_df.append([
                        opcion['ticker'],
                        f"${opcion['strike']:.2f}",
                        f"${opcion['lastPrice']:.2f}",
                        f"${opcion['bid']:.2f}",
                        opcion['vencimiento'],
                        opcion['dias_vencimiento'],
                        f"{opcion['rentabilidad_diaria']:.2f}%",
                        f"{opcion['rentabilidad_anual']:.2f}%",
                        f"${opcion['break_even']:.2f}",
                        f"{opcion['diferencia_porcentual']:.2f}%",
                        f"{opcion['volatilidad_implícita']:.2f}%",
                        opcion['volumen'],
                        opcion['open_interest'],
                        opcion['source']
                    ])

        # Generar Mejores_Contratos.txt y mejores_contratos.csv
        headers_mejores = [
            "Ticker",
            "Strike",
            "Last Closed",
            "Bid",
            "Vencimiento",
            "Días Venc.",
            "Rent. Diaria",
            "Rent. Anual",
            "Break-even",
            "Dif. % (Suby.-Break.)",
            "Volatilidad Implícita",
            "Volumen",
            "Interés Abierto",
            "Fuente"
        ]
        if mejores_contratos_por_ticker:
            # Extraer tickers únicos de los contratos seleccionados
            tickers_identificados = sorted(list(set([opcion['ticker'] for opcion in mejores_contratos_por_ticker])))
            ticker_list = ", ".join(tickers_identificados)
            print(f"Tickers identificados como oportunidades: {ticker_list}")

            tipo_opcion_texto = "Out of the Money" if FILTRO_TIPO_OPCION == "OTM" else "In the Money" if FILTRO_TIPO_OPCION == "ITM" else "Todas"
            contenido_mejores = f"Mejores Contratos por Ticker (Mayor Rentabilidad Anual, Menor Tiempo, Mayor Diferencia %):\n{'='*50}\n"

            # Agrupar contratos por ticker para una mejor presentación
            contratos_por_ticker = {}
            for opcion in mejores_contratos_por_ticker:
                ticker = opcion['ticker']
                if ticker not in contratos_por_ticker:
                    contratos_por_ticker[ticker] = []
                contratos_por_ticker[ticker].append(opcion)

            # Generar tabla por ticker
            for ticker, contratos in contratos_por_ticker.items():
                contenido_mejores += f"\nTicker: {ticker}\n{'-'*30}\n"
                tabla_mejores = []
                for opcion in contratos:
                    tabla_mejores.append([
                        opcion['ticker'],
                        f"${opcion['strike']:.2f}",
                        f"${opcion['lastPrice']:.2f}",
                        f"${opcion['bid']:.2f}",
                        opcion['vencimiento'],
                        opcion['dias_vencimiento'],
                        f"{opcion['rentabilidad_diaria']:.2f}%",
                        f"{opcion['rentabilidad_anual']:.2f}%",
                        f"${opcion['break_even']:.2f}",
                        f"{opcion['diferencia_porcentual']:.2f}%",
                        f"{opcion['volatilidad_implícita']:.2f}%",
                        opcion['volumen'],
                        opcion['open_interest'],
                        opcion['source']
                    ])
                tabla = tabulate(tabla_mejores, headers=headers_mejores, tablefmt="grid")
                contenido_mejores += f"{tabla}\n"

            # Guardar en Mejores_Contratos.txt
            with open("Mejores_Contratos.txt", "w") as f:
                f.write(contenido_mejores)
            print("Mejores contratos por ticker exportados a 'Mejores_Contratos.txt'.")

            # Guardar en mejores_contratos.csv
            df_mejores = pd.DataFrame(mejores_contratos_df, columns=headers_mejores)
            df_mejores.to_csv("mejores_contratos.csv", index=False)
            print("Mejores contratos exportados a 'mejores_contratos.csv'.")

            # Verificar y depurar antes de enviar a Discord
            print(f"[DEBUG] Valor de DISCORD_WEBHOOK_URL antes de enviar: {DISCORD_WEBHOOK_URL}")
            if not es_ejecucion_manual or force_discord or ENVIAR_NOTIFICACION_MANUAL:
                enviar_notificacion_discord(tipo_opcion_texto, TOP_CONTRATOS, tickers_identificados, ALERTA_RENTABILIDAD_ANUAL, ALERTA_VOLATILIDAD_MINIMA)

        else:
            print("No se encontraron contratos que cumplan las reglas de alerta en ningún ticker.")
            # Generar mejores_contratos.csv vacío
            df_mejores = pd.DataFrame(columns=headers_mejores)
            df_mejores.to_csv("mejores_contratos.csv", index=False)
            print("Archivo mejores_contratos.csv generado (vacío).")

    except Exception as e:
        error_msg = f"Error general: {e}\n"
        print(error_msg)
        resultado += error_msg
        with open("resultados.txt", "w") as f:
            f.write(resultado)

        # Generar archivos vacíos para evitar problemas con los artefactos
        headers_csv = [
            "Ticker",
            "Strike",
            "Last Closed",
            "Bid",
            "Vencimiento",
            "Días Venc.",
            "Rent. Diaria",
            "Rent. Anual",
            "Break-even",
            "Dif. % (Suby.-Break.)",
            "Volatilidad Implícita",
            "Volumen",
            "Interés Abierto",
            "Fuente"
        ]
        df_todas = pd.DataFrame(columns=headers_csv)
        df_todas.to_csv("todas_las_opciones.csv", index=False)
        print("Archivo todas_las_opciones.csv generado (vacío debido a error).")

        df_mejores = pd.DataFrame(columns=headers_csv)
        df_mejores.to_csv("mejores_contratos.csv", index=False)
        print("Archivo mejores_contratos.csv generado (vacío debido a error).")

if __name__ == "__main__":
    analizar_opciones()
