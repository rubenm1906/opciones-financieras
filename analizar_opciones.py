import yfinance as yf
from datetime import datetime
import os

# Configuración
TICKER = "AAPL"
MIN_RENTABILIDAD_ANUAL = 60

def obtener_precio_subyacente(ticker):
    stock = yf.Ticker(ticker)
    precio = stock.info['regularMarketPrice']
    return precio

def obtener_opciones_put(ticker):
    stock = yf.Ticker(ticker)
    # Obtener fechas de vencimiento disponibles
    fechas_vencimiento = stock.options
    opciones_put = []
    for fecha in fechas_vencimiento:
        # Obtener datos de opciones para esa fecha
        opcion = stock.option_chain(fecha)
        puts = opcion.puts
        for _, put in puts.iterrows():
            opciones_put.append({
                "strike": put["strike"],
                "lastPrice": put["lastPrice"],
                "expirationDate": fecha
            })
    return opciones_put

def calcular_rentabilidad(precio_put, precio_subyacente, dias_vencimiento):
    rentabilidad_diaria = (precio_put * 100) / precio_subyacente
    factor_anual = 365 / dias_vencimiento
    rentabilidad_anualizada = (rentabilidad_diaria * factor_anual)
    return rentabilidad_diaria, rentabilidad_anualizada

def analizar_opciones(ticker):
    try:
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
