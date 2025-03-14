import yfinance as yf
from datetime import datetime
import os
from tabulate import tabulate

# Configuración
TICKERS = ["AAPL", "MSFT", "GOOGL"]  # Lista de tickers a analizar
MIN_RENTABILIDAD_ANUAL = 20
MAX_DIAS_VENCIMIENTO = 90  # Filtro máximo de 90 días
MIN_DIFERENCIA_PORCENTUAL = 5  # Filtro mínimo para la diferencia % (Subyacente - Break-even)
TOP_CONTRATOS = 5  # Número de contratos a mostrar en la tabla de "Mejores Contratos"

def obtener_precio_subyacente(ticker):
    stock = yf.Ticker(ticker)
    precio = stock.info['regularMarketPrice']
    minimo_52_semanas = stock.info['fiftyTwoWeekLow']  # Mínimo de las últimas 52 semanas
    return precio, minimo_52_semanas

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

def calcular_break_even(strike, precio_put):
    # Break-even para un Short Put: Strike - Premium recibido
    return strike - precio_put

def calcular_diferencia_porcentual(precio_subyacente, break_even):
    # Diferencia en % entre el precio del subyacente y el break-even
    return ((precio_subyacente - break_even) / precio_subyacente) * 100

def analizar_opciones(tickers):
    resultado = ""
    todas_las_opciones = []  # Lista para almacenar todas las opciones filtradas de todos los tickers

    try:
        for ticker in tickers:
            # Separador para cada ticker
            resultado += f"\n{'='*50}\nAnalizando ticker: {ticker}\n{'='*50}\n"
            print(f"\n{'='*50}\nAnalizando ticker: {ticker}\n{'='*50}\n")

            precio_subyacente, minimo_52_semanas = obtener_precio_subyacente(ticker)
            resultado += f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}\n"
            resultado += f"Mínimo de las últimas 52 semanas: ${minimo_52_semanas:.2f}\n"
            print(f"Precio del subyacente ({ticker}): ${precio_subyacente:.2f}")
            print(f"Mínimo de las últimas 52 semanas: ${minimo_52_semanas:.2f}")

            opciones_put = obtener_opciones_put(ticker)
            opciones_filtradas = []
            for contrato in opciones_put:
                strike = float(contrato["strike"])
                precio_put = float(contrato["lastPrice"])
                vencimiento_str = contrato["expirationDate"]
                dias_vencimiento = (datetime.strptime(vencimiento_str, "%Y-%m-%d") - datetime.now()).days

                # Filtrar por máximo de 90 días
                if dias_vencimiento <= 0 or dias_vencimiento > MAX_DIAS_VENCIMIENTO:
                    continue

                rent_diaria, rent_anual = calcular_rentabilidad(precio_put, precio_subyacente, dias_vencimiento)
                break_even = calcular_break_even(strike, precio_put)
                diferencia_porcentual = calcular_diferencia_porcentual(precio_subyacente, break_even)

                # Filtrar por rentabilidad anual mínima y diferencia porcentual mínima
                if rent_anual >= MIN_RENTABILIDAD_ANUAL and diferencia_porcentual >= MIN_DIFERENCIA_PORCENTUAL:
                    opcion = {
                        "ticker": ticker,  # Añadimos el ticker para la tabla final
                        "strike": strike,
                        "precio_put": precio_put,
                        "vencimiento": vencimiento_str,
                        "dias_vencimiento": dias_vencimiento,
                        "rentabilidad_diaria": rent_diaria,
                        "rentabilidad_anual": rent_anual,
                        "break_even": break_even,
                        "diferencia_porcentual": diferencia_porcentual
                    }
                    opciones_filtradas.append(opcion)
                    todas_las_opciones.append(opcion)  # Añadimos a la lista global

            if opciones_filtradas:
                resultado += f"\nOpciones PUT con rentabilidad anual > {MIN_RENTABILIDAD_ANUAL}% y diferencia % > {MIN_DIFERENCIA_PORCENTUAL}% (máximo {MAX_DIAS_VENCIMIENTO} días):\n"
                
                # Crear una tabla con los datos para este ticker
                tabla_datos = []
                for opcion in opciones_filtradas:
                    tabla_datos.append([
                        f"${opcion['strike']:.2f}",
                        f"${opcion['precio_put']:.2f}",
                        opcion['vencimiento'],
                        opcion['dias_vencimiento'],
                        f"{opcion['rentabilidad_diaria']:.2f}%",
                        f"{opcion['rentabilidad_anual']:.2f}%",
                        f"${opcion['break_even']:.2f}",
                        f"{opcion['diferencia_porcentual']:.2f}%"
                    ])
                
                headers = [
                    "Strike",
                    "Precio PUT",
                    "Vencimiento",
                    "Días Venc.",
                    "Rent. Diaria",
                    "Rent. Anual",
                    "Break-even",
                    "Dif. % (Suby.-Break.)"
                ]
                
                tabla = tabulate(tabla_datos, headers=headers, tablefmt="grid")
                resultado += f"\n{tabla}\n"
                print(tabla)  # Mostrar en consola también
            else:
                resultado += f"\nNo se encontraron opciones PUT con rentabilidad anual > {MIN_RENTABILIDAD_ANUAL}% y diferencia % > {MIN_DIFERENCIA_PORCENTUAL}% dentro de {MAX_DIAS_VENCIMIENTO} días.\n"
                print(resultado)

        # Tabla adicional: Mejores contratos
        if todas_las_opciones:
            # Ordenar por mayor rentabilidad anual, menor tiempo de vencimiento, y mayor diferencia porcentual
            mejores_opciones = sorted(
                todas_las_opciones,
                key=lambda x: (-x['rentabilidad_anual'], x['dias_vencimiento'], -x['diferencia_porcentual'])
            )[:TOP_CONTRATOS]  # Tomar los mejores según el criterio

            resultado += f"\n{'='*50}\nMejores {TOP_CONTRATOS} Contratos (Mayor Rentabilidad Anual, Menor Tiempo, Mayor Diferencia %):\n{'='*50}\n"
            print(f"\n{'='*50}\nMejores {TOP_CONTRATOS} Contratos (Mayor Rentabilidad Anual, Menor Tiempo, Mayor Diferencia %):\n{'='*50}\n")

            tabla_mejores = []
            for opcion in mejores_opciones:
                tabla_mejores.append([
                    opcion['ticker'],
                    f"${opcion['strike']:.2f}",
                    f"${opcion['precio_put']:.2f}",
                    opcion['vencimiento'],
                    opcion['dias_vencimiento'],
                    f"{opcion['rentabilidad_diaria']:.2f}%",
                    f"{opcion['rentabilidad_anual']:.2f}%",
                    f"${opcion['break_even']:.2f}",
                    f"{opcion['diferencia_porcentual']:.2f}%"
                ])

            headers_mejores = [
                "Ticker",
                "Strike",
                "Precio PUT",
                "Vencimiento",
                "Días Venc.",
                "Rent. Diaria",
                "Rent. Anual",
                "Break-even",
                "Dif. % (Suby.-Break.)"
            ]

            tabla = tabulate(tabla_mejores, headers=headers_mejores, tablefmt="grid")
            resultado += f"\n{tabla}\n"
            print(tabla)

        # Guardar resultados en un archivo
        with open("resultados.txt", "w") as f:
            f.write(resultado)

    except Exception as e:
        error_msg = f"Error: {e}\n"
        print(error_msg)
        with open("resultados.txt", "w") as f:
            f.write(error_msg)

if __name__ == "__main__":
    analizar_opciones(TICKERS)
