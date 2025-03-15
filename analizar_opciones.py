import yfinance as yf
from datetime import datetime
import os
from tabulate import tabulate
import pandas as pd  # Para exportar a CSV
import requests  # Para enviar notificaciones a Discord

# Configuración
TICKERS = list(set(["NA9.DE","TEP.PA", "GOOGL","EPAM" ,"NFE" ,"GLNG","GLOB","NVDA"]))  # Aseguramos que no haya duplicados
MIN_RENTABILIDAD_ANUAL = 40
MAX_DIAS_VENCIMIENTO = 90  # Filtro máximo de 90 días
MIN_DIFERENCIA_PORCENTUAL = 5  # Filtro mínimo para la diferencia % (Subyacente - Break-even)
MIN_VOLUMEN = 50  # Filtro mínimo de volumen
MIN_VOLATILIDAD_IMPLÍCITA = 20  # Mínimo de volatilidad implícita en %
MAX_VOLATILIDAD_IMPLÍCITA = 50  # Máximo de volatilidad implícita en %
MIN_OPEN_INTEREST = 100  # Mínimo de interés abierto
FILTRO_TIPO_OPCION = "OTM"  # Opciones: "OTM", "ITM", "TODAS"
TOP_CONTRATOS = 5  # Número de contratos a mostrar en la tabla de "Mejores Contratos"

# Nuevos umbrales para alertas personalizadas (Idea 7)
ALERTA_RENTABILIDAD_ANUAL = 50  # Rentabilidad anual mínima para alerta
ALERTA_MAX_VOLATILIDAD = 30  # Volatilidad implícita máxima para alerta

# Configuración para Discord (Idea 2)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1350463523196768356/ePmWnO2XWnfD582oMAr2WzqSFs7ZxU1ApRYi1bz8PiSbZE5zAcR7ZoOD8SPVofxA9UUW"

# Variable para evitar ejecuciones múltiples
SCRIPT_EJECUTADO = False

def obtener_datos_subyacente(ticker):
    """Obtiene el precio del subyacente, mínimo y máximo de 52 semanas."""
    stock = yf.Ticker(ticker)
    precio = stock.info.get('regularMarketPrice', None)
    minimo_52_semanas = stock.info.get('fiftyTwoWeekLow', None)
    maximo_52_semanas = stock.info.get('fiftyTwoWeekHigh', None)
    if precio is None or minimo_52_semanas is None or maximo_52_semanas is None:
        raise ValueError(f"No se encontraron datos válidos para el subyacente {ticker}")
    return stock, precio, minimo_52_semanas, maximo_52_semanas

def obtener_opciones_put(stock):
    """Obtiene las opciones PUT del ticker, incluyendo interés abierto."""
    fechas_vencimiento = stock.options
    opciones_put = []
    for fecha in fechas_vencimiento:
        opcion = stock.option_chain(fecha)
        puts = opcion.puts
        for _, put in puts.iterrows():
            opciones_put.append({
                "strike": put["strike"],
                "lastPrice": put["lastPrice"],
                "expirationDate": fecha,
                "volume": put.get("volume", 0),
                "impliedVolatility": put.get("impliedVolatility", 0),
                "openInterest": put.get("openInterest", 0)
            })
    return opciones_put

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

def enviar_notificacion_discord(mejores_opciones, tipo_opcion_texto):
    """Envía una notificación a Discord con un resumen de los mejores contratos."""
    # Crear un mensaje simplificado con menos columnas para evitar exceder el límite de caracteres
    tabla_resumen = []
    headers_resumen = ["Ticker", "Strike", "Rent. Anual", "Vencimiento"]
    for opcion in mejores_opciones:
        tabla_resumen.append([
            opcion['ticker'],
            f"${opcion['strike']:.2f}",
            f"{opcion['rentabilidad_anual']:.2f}%",
            opcion['vencimiento']
        ])
    
    tabla = tabulate(tabla_resumen, headers=headers_resumen, tablefmt="grid")
    mensaje = (f"Se encontraron opciones que cumplen los filtros.\n\n"
               f"Mejores {TOP_CONTRATOS} Contratos {tipo_opcion_texto}:\n\n"
               f"```plaintext\n{tabla}\n```")

    # Verificar si el mensaje excede el límite de 2000 caracteres
    if len(mensaje) > 2000:
        mensaje = (f"Se encontraron opciones que cumplen los filtros.\n\n"
                   f"Mejores {TOP_CONTRATOS} Contratos {tipo_opcion_texto}:\n\n"
                   f"Demasiados datos para mostrar. Revisa los archivos CSV para más detalles.\n")

    payload = {"content": mensaje}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Notificación enviada a Discord exitosamente.")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar notificación a Discord: {e}")
        if response.text:
            print(f"Detalles del error: {response.text}")

def analizar_opciones(tickers):
    global SCRIPT_EJECUTADO
    if SCRIPT_EJECUTADO:
        print("El script ya ha sido ejecutado. Evitando repetición.")
        return
    SCRIPT_EJECUTADO = True

    resultado = ""
    todas_las_opciones = []  # Lista para almacenar todas las opciones filtradas de todos los tickers
    todas_las_opciones_df = []  # Lista para exportar a CSV

    try:
        print(f"Analizando {len(tickers)} tickers: {tickers}")
        for ticker in tickers:
            # Separador para cada ticker
            resultado += f"\n{'='*50}\nAnalizando ticker: {ticker}\n{'='*50}\n"
            print(f"\n{'='*50}\nAnalizando ticker: {ticker}\n{'='*50}\n")

            try:
                # Obtener datos del subyacente
                stock, precio_subyacente, minimo_52_semanas, maximo_52_semanas = obtener_datos_subyacente(ticker)
                resultado += f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}\n"
                resultado += f"Mínimo de las últimas 52 semanas: ${minimo_52_semanas:.2f}\n"
                resultado += f"Máximo de las últimas 52 semanas: ${maximo_52_semanas:.2f}\n"
                print(f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}")
                print(f"Mínimo de las últimas 52 semanas: ${minimo_52_semanas:.2f}")
                print(f"Máximo de las últimas 52 semanas: ${maximo_52_semanas:.2f}")

                # Obtener opciones PUT
                opciones_put = obtener_opciones_put(stock)
                print(f"Se encontraron {len(opciones_put)} opciones PUT para {ticker}")
                opciones_filtradas = []
                for contrato in opciones_put:
                    strike = float(contrato["strike"])
                    precio_put = float
