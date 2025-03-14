import requests
import json
from datetime import datetime
import os

# Configuración
API_KEY = os.getenv("API_KEY")
TICKER = "AAPL"
MIN_RENTABILIDAD_ANUAL = 8

def obtener_precio_subyacente(ticker):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}"
    respuesta = requests.get(url)
    datos = respuesta.json()
    if "Time Series (Daily)" in datos:
        latest_date = list(datos["Time Series (Daily)"].keys())[0]
        precio = float(datos["Time Series (Daily)"][latest_date]["4. close"])
        return precio
    else:
        raise Exception("No se pudo obtener el precio del subyacente.")

def obtener_opciones_put(ticker):
    url = f"https://www.alphavantage.co/query?function=OPTION_PRICES&symbol={ticker}&apikey={API_KEY}"
    respuesta = requests.get(url)
    datos = respuesta.json()
    if "putOptionContracts" in datos:
        return datos["putOptionContracts"]
    else:
        raise Exception("No se encontraron datos de opciones PUT.")

def calcular_rentabilidad(precio_put, precio_subyacente, dias_vencimiento):
    rentabilidad_diaria = (precio_put * 100) / precio_subyacente
    factor_anual = 365 / dias_vencimiento
    rentabilidad_anualizada = (rentabilidad_diaria * factor_anual)
    return rentabilidad_diaria, rentabilidad_anualizada

def analizar_opciones(ticker):
    try:
        if not API_KEY:
            raise Exception("La clave API no está definida. Configura la variable de entorno API_KEY.")

        precio_subyacente = obtener_precio_subyacente(ticker)
        print(f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}")

        opciones_put = obtener_opciones_put(ticker)
        opciones_filtradas = []
        for contrato in opciones_put:
            strike = float(contrato["strike"])
            precio_put = float(contrato["lastPrice"])
            vencimiento_str = contrato["expirationDate"]
            dias_vencimiento = (datetime.strptime(vencimiento_str, "%Y-%m-%d") - datetime.now()).days

            if dias_vencimiento <= 0:
                continue

            rent_diaria, rent_anual = calcular_rentabilidad(precio_put, precio_subyacente, dias_vencimiento)

            if rent_anual >= MIN_RENTABILIDAD_ANUAL:
                opciones_filtradas.append({
                    "strike": strike,
                    "precio_put": precio_put,
                    "vencimiento": vencimiento_str,
                    "dias_vencimiento": dias_vencimiento,
                    "rentabilidad_diaria": rent_diaria,
                    "rentabilidad_anual": rent_anual
                })

        if opciones_filtradas:
            print(f"\nOpciones PUT con rentabilidad anual > {MIN_RENTABILIDAD_ANUAL}%:")
            for opcion in opciones_filtradas:
                print(f"- Strike: ${opcion['strike']:.2f}")
                print(f"  Precio PUT: ${opcion['precio_put']:.2f}")
                print(f"  Vencimiento: {opcion['vencimiento']} ({opcion['dias_vencimiento']} días)")
                print(f"  Rentabilidad Diaria: {opcion['rentabilidad_diaria']:.2f}%")
                print(f"  Rentabilidad Anual: {opcion['rentabilidad_anual']:.2f}%")
                print("---")
        else:
            print(f"\nNo se encontraron opciones PUT con rentabilidad anual > {MIN_RENTABILIDAD_ANUAL}%.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analizar_opciones(TICKER)
