import yfinance as yf
from datetime import datetime
import os
from tabulate import tabulate
import pandas as pd  # Para exportar a CSV
import requests  # Para enviar notificaciones a Discord
import time  # Para agregar retrasos entre solicitudes

# Configuración para Discord (Idea 2)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1350463523196768356/ePmWnO2XWnfD582oMAr2WzqSFs7ZxU1ApRYi1bz8PiSbZE5zAcR7ZoOD8SPVofxA9UUW"

# Variable para evitar ejecuciones múltiples
SCRIPT_EJECUTADO = False

def obtener_configuracion():
    """Obtiene la configuración desde variables de entorno con valores por defecto."""
    # TICKERS
    TICKERS = os.getenv("TICKERS", "AAPL,MSFT,GOOGL,EPAM,TEP.PA")
    TICKERS = list(set(TICKERS.split(",")))  # Convertir a lista y eliminar duplicados

    # MIN_RENTABILIDAD_ANUAL
    MIN_RENTABILIDAD_ANUAL = float(os.getenv("MIN_RENTABILIDAD_ANUAL", 40))

    # MAX_DIAS_VENCIMIENTO
    MAX_DIAS_VENCIMIENTO = int(os.getenv("MAX_DIAS_VENCIMIENTO", 90))

    # MIN_DIFERENCIA_PORCENTUAL
    MIN_DIFERENCIA_PORCENTUAL = float(os.getenv("MIN_DIFERENCIA_PORCENTUAL", 5))

    # MIN_VOLUMEN
    MIN_VOLUMEN = int(os.getenv("MIN_VOLUMEN", 50))

    # MIN_VOLATILIDAD_IMPLÍCITA
    MIN_VOLATILIDAD_IMPLÍCITA = float(os.getenv("MIN_VOLATILIDAD_IMPLÍCITA", 20))

    # MAX_VOLATILIDAD_IMPLÍCITA
    MAX_VOLATILIDAD_IMPLÍCITA = float(os.getenv("MAX_VOLATILIDAD_IMPLÍCITA", 50))

    # MIN_OPEN_INTEREST
    MIN_OPEN_INTEREST = int(os.getenv("MIN_OPEN_INTEREST", 100))

    # FILTRO_TIPO_OPCION
    FILTRO_TIPO_OPCION = os.getenv("FILTRO_TIPO_OPCION", "OTM").upper()
    if FILTRO_TIPO_OPCION not in ["OTM", "ITM", "TODAS"]:
        print(f"Valor inválido para FILTRO_TIPO_OPCION: {FILTRO_TIPO_OPCION}. Usando valor por defecto: OTM")
        FILTRO_TIPO_OPCION = "OTM"

    # TOP_CONTRATOS
    TOP_CONTRATOS = int(os.getenv("TOP_CONTRATOS", 5))

    # ALERTA_RENTABILIDAD_ANUAL
    ALERTA_RENTABILIDAD_ANUAL = float(os.getenv("ALERTA_RENTABILIDAD_ANUAL", 50))

    # ALERTA_MAX_VOLATILIDAD
    ALERTA_MAX_VOLATILIDAD = float(os.getenv("ALERTA_MAX_VOLATILIDAD", 30))

    return (TICKERS, MIN_RENTABILIDAD_ANUAL, MAX_DIAS_VENCIMIENTO, MIN_DIFERENCIA_PORCENTUAL,
            MIN_VOLUMEN, MIN_VOLATILIDAD_IMPLÍCITA, MAX_VOLATILIDAD_IMPLÍCITA, MIN_OPEN_INTEREST,
            FILTRO_TIPO_OPCION, TOP_CONTRATOS, ALERTA_RENTABILIDAD_ANUAL, ALERTA_MAX_VOLATILIDAD)

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

def enviar_notificacion_discord(mejores_opciones, tipo_opcion_texto, top_contratos):
    """Envía notificaciones a Discord dividiendo los contratos en grupos de 5 con retraso."""
    headers_resumen = ["Ticker", "Strike", "Precio PUT", "Días al Venc.", "Rent. Diaria", "Rent. Anual", "Volatilidad", "Vencimiento"]
    grupo_tamano = 5
    for i in range(0, len(mejores_opciones), grupo_tamano):
        grupo_opciones = mejores_opciones[i:i + grupo_tamano]
        inicio = i + 1
        fin = min(i + grupo_tamano, len(mejores_opciones))
        
        tabla_resumen = []
        for opcion in grupo_opciones:
            tabla_resumen.append([
                opcion['ticker'],
                f"${opcion['strike']:.2f}",
                f"${opcion['precio_put']:.2f}",
                opcion['dias_vencimiento'],
                f"{opcion['rentabilidad_diaria']:.2f}%",
                f"{opcion['rentabilidad_anual']:.2f}%",
                f"{opcion['volatilidad_implícita']:.2f}%",
                opcion['vencimiento']
            ])
        
        tabla = tabulate(tabla_resumen, headers=headers_resumen, tablefmt="grid")
        mensaje = (f"Se encontraron opciones que cumplen los filtros.\n\n"
                   f"Mejores {top_contratos} Contratos {tipo_opcion_texto} - Contratos {inicio}-{fin}:\n\n"
                   f"```plaintext\n{tabla}\n```")

        if len(mensaje) > 2000:
            mensaje = (f"Se encontraron opciones que cumplen los filtros.\n\n"
                       f"Mejores {top_contratos} Contratos {tipo_opcion_texto} - Contratos {inicio}-{fin}:\n\n"
                       f"Demasiados datos para mostrar. Revisa los archivos CSV para más detalles.\n")

        payload = {"content": mensaje}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            print(f"Notificación enviada a Discord exitosamente para contratos {inicio}-{fin}.")
        except requests.exceptions.RequestException as e:
            print(f"Error al enviar notificación a Discord para contratos {inicio}-{fin}: {e}")
            if response.text:
                print(f"Detalles del error: {response.text}")
            break

        time.sleep(1)

def analizar_opciones():
    global SCRIPT_EJECUTADO

    if SCRIPT_EJECUTADO:
        print("El script ya ha sido ejecutado. Evitando repetición.")
        return
    SCRIPT_EJECUTADO = True

    # Obtener configuración desde variables de entorno
    (TICKERS, MIN_RENTABILIDAD_ANUAL, MAX_DIAS_VENCIMIENTO, MIN_DIFERENCIA_PORCENTUAL,
     MIN_VOLUMEN, MIN_VOLATILIDAD_IMPLÍCITA, MAX_VOLATILIDAD_IMPLÍCITA, MIN_OPEN_INTEREST,
     FILTRO_TIPO_OPCION, TOP_CONTRATOS, ALERTA_RENTABILIDAD_ANUAL, ALERTA_MAX_VOLATILIDAD) = obtener_configuracion()

    # Resumen de condiciones para el archivo .txt
    resumen_condiciones = (
        f"Resumen de condiciones de ejecución - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n"
        f"Tickers analizados: {', '.join(TICKERS)}\n"
        f"Filtro tipo opción: {FILTRO_TIPO_OPCION}\n"
        f"Mínima rentabilidad anual: {MIN_RENTABILIDAD_ANUAL}%\n"
        f"Máximo días al vencimiento: {MAX_DIAS_VENCIMIENTO}\n"
        f"Mínima diferencia porcentual: {MIN_DIFERENCIA_PORCENTUAL}%\n"
        f"Mínimo volumen: {MIN_VOLUMEN}\n"
        f"Volatilidad implícita (mínima-máxima): {MIN_VOLATILIDAD_IMPLÍCITA}% - {MAX_VOLATILIDAD_IMPLÍCITA}%\n"
        f"Mínimo interés abierto: {MIN_OPEN_INTEREST}\n"
        f"{'='*50}\n\n"
    )

    resultado = resumen_condiciones
    todas_las_opciones = []
    todas_las_opciones_df = []

    try:
        print(f"Analizando {len(TICKERS)} tickers: {TICKERS}")
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

                opciones_put = obtener_opciones_put(stock)
                print(f"Se encontraron {len(opciones_put)} opciones PUT para {ticker}")
                opciones_filtradas = []
                for contrato in opciones_put:
                    strike = float(contrato["strike"])
                    precio_put = float(contrato["lastPrice"])
                    vencimiento_str = contrato["expirationDate"]
                    dias_vencimiento = (datetime.strptime(vencimiento_str, "%Y-%m-%d") - datetime.now()).days
                    volumen = contrato["volume"]
                    volatilidad_implícita = contrato["impliedVolatility"] * 100
                    open_interest = contrato["openInterest"]

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
                    if volatilidad_implícita < MIN_VOLATILIDAD_IMPLÍCITA or volatilidad_implícita > MAX_VOLATILIDAD_IMPLÍCITA:
                        continue
                    if open_interest < MIN_OPEN_INTEREST:
                        continue

                    rent_diaria, rent_anual = calcular_rentabilidad(precio_put, precio_subyacente, dias_vencimiento)
                    break_even = calcular_break_even(strike, precio_put)
                    diferencia_porcentual = calcular_diferencia_porcentual(precio_subyacente, break_even)

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
                            "open_interest": open_interest
                        }
                        opciones_filtradas.append(opcion)
                        todas_las_opciones.append(opcion)

                        todas_las_opciones_df.append([
                            ticker,
                            f"${strike:.2f}",
                            f"${precio_put:.2f}",
                            vencimiento_str,
                            dias_vencimiento,
                            f"{rent_diaria:.2f}%",
                            f"{rent_anual:.2f}%",
                            f"${break_even:.2f}",
                            f"{diferencia_porcentual:.2f}%",
                            f"{volatilidad_implícita:.2f}%",
                            volumen,
                            open_interest
                        ])

                if opciones_filtradas:
                    tipo_opcion_texto = "Out of the Money" if FILTRO_TIPO_OPCION == "OTM" else "In the Money" if FILTRO_TIPO_OPCION == "ITM" else "Todas"
                    resultado += f"\nOpciones PUT {tipo_opcion_texto} con rentabilidad anual > {MIN_RENTABILIDAD_ANUAL}% y diferencia % > {MIN_DIFERENCIA_PORCENTUAL}% (máximo {MAX_DIAS_VENCIMIENTO} días, volumen > {MIN_VOLUMEN}, volatilidad entre {MIN_VOLATILIDAD_IMPLÍCITA}% y {MAX_VOLATILIDAD_IMPLÍCITA}%, interés abierto > {MIN_OPEN_INTEREST}):\n"
                    print(f"Se encontraron {len(opciones_filtradas)} opciones que cumplen los filtros para {ticker}")
                    
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

                    for opcion in opciones_filtradas:
                        if (opcion['rentabilidad_anual'] >= ALERTA_RENTABILIDAD_ANUAL and 
                            opcion['volatilidad_implícita'] <= ALERTA_MAX_VOLATILIDAD):
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

        if todas_las_opciones_df:
            headers_csv = [
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
            df_todas = pd.DataFrame(todas_las_opciones_df, columns=headers_csv)
            df_todas.to_csv("todas_las_opciones.csv", index=False)
            print("Todas las opciones exportadas a 'todas_las_opciones.csv'.")

        print(f"Total de opciones filtradas (todos los tickers): {len(todas_las_opciones)}")
        mejores_opciones_df = []
        if todas_las_opciones:
            mejores_opciones = sorted(
                todas_las_opciones,
                key=lambda x: (-x['rentabilidad_anual'], x['dias_vencimiento'], -x['diferencia_porcentual'])
            )[:TOP_CONTRATOS]

            tipo_opcion_texto = "Out of the Money" if FILTRO_TIPO_OPCION == "OTM" else "In the Money" if FILTRO_TIPO_OPCION == "ITM" else "Todas"
            resultado += f"\n{'='*50}\nMejores {TOP_CONTRATOS} Contratos {tipo_opcion_texto} (Mayor Rentabilidad Anual, Menor Tiempo, Mayor Diferencia %):\n{'='*50}\n"
            print(f"\n{'='*50}\nMejores {TOP_CONTRATOS} Contratos {tipo_opcion_texto} (Mayor Rentabilidad Anual, Menor Tiempo, Mayor Diferencia %):\n{'='*50}\n")

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

                mejores_opciones_df.append([
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

            df_mejores = pd.DataFrame(mejores_opciones_df, columns=headers_mejores)
            df_mejores.to_csv("mejores_contratos.csv", index=False)
            print("Mejores contratos exportados a 'mejores_contratos.csv'.")

            enviar_notificacion_discord(mejores_opciones, tipo_opcion_texto, TOP_CONTRATOS)

        else:
            resultado += f"\nNo se encontraron opciones que cumplan los filtros en ningún ticker.\n"
            print("No se encontraron opciones que cumplan los filtros en ningún ticker.")

        with open("resultados.txt", "w") as f:
            f.write(resultado)

    except Exception as e:
        error_msg = f"Error general: {e}\n"
        print(error_msg)
        with open("resultados.txt", "w") as f:
            f.write(error_msg)

if __name__ == "__main__":
    analizar_opciones()
