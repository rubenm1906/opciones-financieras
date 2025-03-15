import yfinance as yf
from datetime import datetime
import os
from tabulate import tabulate

# Configuración
TICKERS = list(set(["AAPL", "MSFT", "GOOGL", "EPAM"]))  # Aseguramos que no haya duplicados
MIN_RENTABILIDAD_ANUAL = 40
MAX_DIAS_VENCIMIENTO = 90  # Filtro máximo de 90 días
MIN_DIFERENCIA_PORCENTUAL = 5  # Filtro mínimo para la diferencia % (Subyacente - Break-even)
MIN_VOLUMEN = 50  # Filtro mínimo de volumen
MIN_VOLATILIDAD_IMPLÍCITA = 20  # Mínimo de volatilidad implícita en %
MAX_VOLATILIDAD_IMPLÍCITA = 50  # Máximo de volatilidad implícita en %
MIN_OPEN_INTEREST = 100  # Mínimo de interés abierto
TOP_CONTRATOS = 5  # Número de contratos a mostrar en la tabla de "Mejores Contratos"

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
                "openInterest": put.get("openInterest", 0)  # Añadimos interés abierto
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

def analizar_opciones(tickers):
    global SCRIPT_EJECUTADO
    if SCRIPT_EJECUTADO:
        print("El script ya ha sido ejecutado. Evitando repetición.")
        return
    SCRIPT_EJECUTADO = True

    resultado = ""
    todas_las_opciones = []  # Lista para almacenar todas las opciones filtradas de todos los tickers

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
                    precio_put = float(contrato["lastPrice"])
                    vencimiento_str = contrato["expirationDate"]
                    dias_vencimiento = (datetime.strptime(vencimiento_str, "%Y-%m-%d") - datetime.now()).days
                    volumen = contrato["volume"]
                    volatilidad_implícita = contrato["impliedVolatility"] * 100  # Convertir a %
                    open_interest = contrato["openInterest"]  # Obtener interés abierto

                    # Filtros
                    if dias_vencimiento <= 0 or dias_vencimiento > MAX_DIAS_VENCIMIENTO:
                        continue
                    if volumen < MIN_VOLUMEN:
                        continue
                    if volatilidad_implícita < MIN_VOLATILIDAD_IMPLÍCITA or volatilidad_implícita > MAX_VOLATILIDAD_IMPLÍCITA:
                        continue
                    if open_interest < MIN_OPEN_INTEREST:
                        continue

                    rent_diaria, rent_anual = calcular_rentabilidad(precio_put, precio_subyacente, dias_vencimiento)
                    break_even = calcular_break_even(strike, precio_put)
                    diferencia_porcentual = calcular_diferencia_porcentual(precio_subyacente, break_even)

                    # Filtrar por rentabilidad anual mínima y diferencia porcentual mínima
                    if rent_anual >= MIN_RENTABILIDAD_ANUAL and diferencia_porcentual >= MIN_DIFERENCIA_PORCENTUAL:
                        opcion = {
                            "ticker": ticker,
                            "strike": strike,
                            "precio_put": precio_put,
                            "vencimiento": vencimiento_str,
                            "dias_vencimiento": dias_vencimiento,
                            "rentabilidad_diaria": rent_diaria,
                            "rentabilidad_anual": rent_anual,
                            "break_even": break_even,
                            "diferencia_porcentual": diferencia_porcentual,
                            "volatilidad_implícita": volatilidad_implícita,
                            "volumen": volumen,
                            "open_interest": open_interest  # Añadimos interés abierto al diccionario
                        }
                        opciones_filtradas.append(opcion)
                        todas_las_opciones.append(opcion)

                if opciones_filtradas:
                    resultado += f"\nOpciones PUT con rentabilidad anual > {MIN_RENTABILIDAD_ANUAL}% y diferencia % > {MIN_DIFERENCIA_PORCENTUAL}% (máximo {MAX_DIAS_VENCIMIENTO} días, volumen > {MIN_VOLUMEN}, volatilidad entre {MIN_VOLATILIDAD_IMPLÍCITA}% y {MAX_VOLATILIDAD_IMPLÍCITA}%, interés abierto > {MIN_OPEN_INTEREST}):\n"
                    print(f"Se encontraron {len(opciones_filtradas)} opciones que cumplen los filtros para {ticker}")
                    
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
                            f"{opcion['diferencia_porcentual']:.2f}%",
                            f"{opcion['volatilidad_implícita']:.2f}%",
                            opcion['volumen'],
                            opcion['open_interest']
                        ])
                    
                    headers = [
                        "Strike",
                        "Precio PUT",
                        "Vencimiento",
                        "Días Venc.",
                        "Rent. Diaria",
                        "Rent. Anual",
                        "Break-even",
                        "Dif. % (Suby.-Break.)",
                        "Volatilidad Implícita",
                        "Volumen",
                        "Interés Abierto"
                    ]
                    
                    tabla = tabulate(tabla_datos, headers=headers, tablefmt="grid")
                    resultado += f"\n{tabla}\n"
                    print(tabla)
                else:
                    resultado += "\nNo se consiguieron resultados para este ticker.\n"
                    print("No se consiguieron resultados para este ticker.")

            except Exception as e:
                error_msg = f"Error al analizar {ticker}: {e}\n"
                resultado += error_msg
                print(error_msg)
                continue

        # Tabla adicional: Mejores contratos
        print(f"Total de opciones filtradas (todos los tickers): {len(todas_las_opciones)}")
        if todas_las_opciones:
            # Ordenar por mayor rentabilidad anual, menor tiempo de vencimiento, y mayor diferencia porcentual
            mejores_opciones = sorted(
                todas_las_opciones,
                key=lambda x: (-x['rentabilidad_anual'], x['dias_vencimiento'], -x['diferencia_porcentual'])
            )[:TOP_CONTRATOS]

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
                    f"{opcion['diferencia_porcentual']:.2f}%",
                    f"{opcion['volatilidad_implícita']:.2f}%",
                    opcion['volumen'],
                    opcion['open_interest']
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
                "Dif. % (Suby.-Break.)",
                "Volatilidad Implícita",
                "Volumen",
                "Interés Abierto"
            ]

            tabla = tabulate(tabla_mejores, headers=headers_mejores, tablefmt="grid")
            resultado += f"\n{tabla}\n"
            print(tabla)
        else:
            resultado += f"\nNo se encontraron opciones que cumplan los filtros en ningún ticker.\n"
            print("No se encontraron opciones que cumplan los filtros en ningún ticker.")

        # Guardar resultados en un archivo
        with open("resultados.txt", "w") as f:
            f.write(resultado)

    except Exception as e:
        error_msg = f"Error general: {e}\n"
        print(error_msg)
        with open("resultados.txt", "w") as f:
            f.write(error_msg)

if __name__ == "__main__":
    analizar_opciones(TICKERS)
