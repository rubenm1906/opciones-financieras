import yfinance as yf
from datetime import datetime
import os
import csv
from tabulate import tabulate
import time

# Configuración
TICKERS = ["AAPL", "MSFT", "GOOGL"]
MIN_RENTABILIDAD_ANUAL = 40
MAX_DIAS_VENCIMIENTO = 90
MIN_DIFERENCIA_PORCENTUAL = 5
MIN_VOLUMEN = 100  # Filtro mínimo de volumen
TOP_CONTRATOS = 5

def obtener_datos_subyacente(ticker):
    """Obtiene el precio del subyacente y el mínimo de 52 semanas."""
    try:
        stock = yf.Ticker(ticker)
        precio = stock.info.get('regularMarketPrice', None)
        minimo_52_semanas = stock.info.get('fiftyTwoWeekLow', None)
        if precio is None or minimo_52_semanas is None:
            raise ValueError("No se encontraron datos válidos para el subyacente")
        return stock, precio, minimo_52_semanas
    except Exception as e:
        raise Exception(f"Error al obtener datos del subyacente para {ticker}: {e}")

def obtener_opciones_put(stock):
    """Obtiene las opciones PUT del ticker."""
    try:
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
                    "impliedVolatility": put.get("impliedVolatility", 0)
                })
        return opciones_put
    except Exception as e:
        raise Exception(f"Error al obtener opciones PUT: {e}")

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

def generar_tabla(opciones_filtradas, headers):
    """Genera una tabla con los datos de las opciones."""
    tabla_datos = []
    for opcion in opciones_filtradas:
        tabla_datos.append([
            opcion.get('ticker', ''),
            f"${opcion['strike']:.2f}",
            f"${opcion['precio_put']:.2f}",
            opcion['vencimiento'],
            opcion['dias_vencimiento'],
            f"{opcion['rentabilidad_diaria']:.2f}%",
            f"{opcion['rentabilidad_anual']:.2f}%",
            f"${opcion['break_even']:.2f}",
            f"{opcion['diferencia_porcentual']:.2f}%",
            f"{opcion['volatilidad_implícita']:.2f}%",
            opcion['volumen']
        ])
    return tabulate(tabla_datos, headers=headers, tablefmt="grid")

def exportar_a_csv(opciones, filename):
    """Exporta las opciones a un archivo CSV."""
    headers = [
        "Ticker", "Strike", "Precio PUT", "Vencimiento", "Días Vencimiento",
        "Rent. Diaria", "Rent. Anual", "Break-even", "Dif. % (Suby.-Break.)",
        "Volatilidad Implícita", "Volumen"
    ]
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for opcion in opciones:
            writer.writerow([
                opcion.get('ticker', ''),
                opcion['strike'],
                opcion['precio_put'],
                opcion['vencimiento'],
                opcion['dias_vencimiento'],
                opcion['rentabilidad_diaria'],
                opcion['rentabilidad_anual'],
                opcion['break_even'],
                opcion['diferencia_porcentual'],
                opcion['volatilidad_implícita'],
                opcion['volumen']
            ])

def analizar_opciones(tickers):
    resultado = ""
    todas_las_opciones = []

    try:
        for ticker in tickers:
            resultado += f"\n{'='*50}\nAnalizando ticker: {ticker}\n{'='*50}\n"
            print(f"\n{'='*50}\nAnalizando ticker: {ticker}\n{'='*50}\n")

            try:
                stock, precio_subyacente, minimo_52_semanas = obtener_datos_subyacente(ticker)
                resultado += f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}\n"
                resultado += f"Mínimo de las últimas 52 semanas: ${minimo_52_semanas:.2f}\n"
                print(f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}")
                print(f"Mínimo de las últimas 52 semanas: ${minimo_52_semanas:.2f}")

                opciones_put = obtener_opciones_put(stock)
                opciones_filtradas = []
                for contrato in opciones_put:
                    strike = float(contrato["strike"])
                    precio_put = float(contrato["lastPrice"])
                    vencimiento_str = contrato["expirationDate"]
                    dias_vencimiento = (datetime.strptime(vencimiento_str, "%Y-%m-%d") - datetime.now()).days
                    volumen = contrato["volume"]
                    volatilidad_implícita = contrato["impliedVolatility"] * 100  # Convertir a %

                    if dias_vencimiento <= 0 or dias_vencimiento > MAX_DIAS_VENCIMIENTO:
                        continue
                    if volumen < MIN_VOLUMEN:
                        continue

                    rent_diaria, rent_anual = calcular_rentabilidad(precio_put, precio_sub
